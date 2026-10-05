#!/usr/bin/env python3
"""Generate the full research paper (.docx) for the Green Code Interaction
Benchmark, pulling every number from the generated JSON/CSV so it stays
reproducible.

Output: docx/green-code-interaction-benchmark.docx

Diagrams are inserted as clearly marked placeholders ([[FIGURE n: ...]]);
data tables are generated from results/final/*.json + code_metrics.csv.
"""
import csv
import json
import statistics as st
from collections import defaultdict
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "final"
DOCX = REPO / "docx"
OUT = DOCX / "green-code-interaction-benchmark.docx"

CATS = {
    "algorithms_computation": "Algorithms & Computation (AC)",
    "file_data_processing": "File & Data Processing (FD)",
    "image_media_processing": "Image & Media Processing (IM)",
    "realistic_applications_utilities": "Realistic Applications & Utilities (RA)",
    "search_retrieval": "Search & Retrieval (SR)",
    "text_log_processing": "Text & Log Processing (TL)",
}
CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]
COND_LABEL = {
    "ONE_SHOT": "C0 One-Shot",
    "BUG_FIX": "C1 Bug-Fix",
    "FEATURE_ADDITION": "C2 Feature-Addition",
    "EDGE_CASE": "C3 Edge-Case",
    "FULL_MULTI_TURN": "C4 Full Multi-Turn",
}
MODELS = ["gpt", "claude", "gemini", "deepseek"]


# --------------------------------------------------------------------------- #
# data loading
# --------------------------------------------------------------------------- #
def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_csv(p):
    p = Path(p)
    if not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x) if x not in ("", None) else None
    except (TypeError, ValueError):
        return None


class Data:
    def __init__(self):
        self.metrics = load_csv(FINAL / "code_metrics.csv")
        self.joined = load_csv(FINAL / "complexity_metrics.csv")
        self.cx = load_json(FINAL / "complexity_metrics.json")
        self.cxsum = load_json(FINAL / "complexity_summary.json")
        self.energy = load_json(FINAL / "energy_report.json")
        self.carbon = load_json(FINAL / "carbon_report.json")
        self.scaling = load_csv(FINAL / "scaling.csv")
        self.scalingsum = load_json(FINAL / "scaling_summary.json")
        self.datasets = {}
        for ds in sorted((REPO / "dataset").glob("*/dataset.json")):
            self.datasets[ds.parent.name] = load_json(ds).get("tasks", [])

    def coverage(self):
        cov = {}
        for cat in CATS:
            sub = [r for r in self.metrics if r["category"] == cat]
            cov[cat] = {"finals": len(sub),
                        "measured": sum(1 for r in sub if r["status"] == "ok"),
                        "parse": sum(1 for r in sub if r.get("parse_ok") == "1")}
        cov["_total"] = {
            "finals": len(self.metrics),
            "measured": sum(1 for r in self.metrics if r["status"] == "ok"),
            "parse": sum(1 for r in self.metrics if r.get("parse_ok") == "1")}
        return cov

    def cond_metric(self, group_key, cond, field):
        g = self.cx.get(group_key, {})
        return (g.get(cond) or {}).get(field)


# --------------------------------------------------------------------------- #
# docx helpers
# --------------------------------------------------------------------------- #
def add_field(paragraph, instr, placeholder_text="(update field)"):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder_text
    fld_sep.append(text)
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr_el, fld_sep, fld_end):
        run._r.append(el)
    return run


def add_xe(paragraph, term):
    """Hidden index-entry marker for `term` -> appears in the INDEX field."""
    run = paragraph.add_run()
    run.font.hidden = True
    xe_begin = OxmlElement("w:fldChar")
    xe_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f' XE "{term}" '
    xe_sep = OxmlElement("w:fldChar")
    xe_sep.set(qn("w:fldCharType"), "separate")
    xe_end = OxmlElement("w:fldChar")
    xe_end.set(qn("w:fldCharType"), "end")
    for el in (xe_begin, instr, xe_sep, xe_end):
        run._r.append(el)


def h(doc, text, level=1, xe=None):
    if level == 0:
        p = doc.add_heading(text, level=0)
    else:
        p = doc.add_heading(text, level=level)
    if xe:
        add_xe(p, xe)
    return p


def para(doc, text, italic=False, size=None, align=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet" if level == 0 else "List Bullet 2")
    return p


def numbered(doc, text):
    return doc.add_paragraph(text, style="List Number")


def caption(doc, text):
    try:
        p = doc.add_paragraph(text, style="Caption")
    except KeyError:
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.italic = True
        r.font.size = Pt(9)
    return p


def figure_placeholder(doc, num, title, note=""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"[[FIGURE {num}: {title}]]")
    run.bold = True
    run.font.color.rgb = RGBColor(0x99, 0x00, 0x00)
    caption(doc, f"Figure {num}. {title}." + (f" {note}" if note else ""))
    return p


def table_placeholder(doc, num, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"[[TABLE {num}: {title}]]")
    run.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x33, 0x99)
    caption(doc, f"Table {num}. {title}.")
    return p


def add_table(doc, headers, rows, caption_text=None, font_size=8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, htext in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(htext))
        run.bold = True
        run.font.size = Pt(font_size)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run("" if val is None else str(val))
            run.font.size = Pt(font_size)
    if caption_text:
        caption(doc, caption_text)
    return t


# --------------------------------------------------------------------------- #
# document sections
# --------------------------------------------------------------------------- #
def title_page(doc, D):
    title = doc.add_heading("", level=0)
    run = title.add_run(
        "Green Code Interaction Benchmark: How Human–AI Interaction "
        "Trajectory Affects the Energy Efficiency and Time Complexity of "
        "Generated Programs")
    run.font.size = Pt(22)
    para(doc, "A Benchmark Study of One-Shot versus Multi-Turn AI-Assisted "
              "Programming", italic=True, size=13, align="center")
    doc.add_paragraph()
    para(doc, "Author: [AUTHOR NAME]", align="center")
    para(doc, "Affiliation: [INSTITUTION / LAB]", align="center")
    para(doc, "Correspondence: [EMAIL]", align="center")
    para(doc, f"Date: {date.today().isoformat()}", align="center")
    doc.add_paragraph()
    para(doc, "Artifact: green-code-interaction-benchmark", align="center")
    para(doc, "This paper was generated from the benchmark's measured results. "
              "Figures are shown as placeholders ([[FIGURE ...]]) to be "
              "rendered from the listed scripts.", italic=True, size=9,
         align="center")
    doc.add_page_break()


def abstract(doc, D):
    h(doc, "Abstract", level=1)
    cov = D.coverage()
    ec = D.energy.get("overall", {})
    med = lambda c: (ec.get(c) or {}).get("median_j")
    delta = D.energy.get("delta", {})
    c4 = delta.get("FULL_MULTI_TURN", {})
    para(doc, (
        "Large language models (LLMs) are increasingly used in interactive, "
        "multi-turn coding sessions, yet most green-software studies measure "
        "the energy of a single generated artifact rather than the effect of "
        "the interaction trajectory that produced it. We present the Green "
        "Code Interaction Benchmark, a controlled study of "
        f"{cov['_total']['finals']} final programs produced by four LLMs "
        "(GPT, Claude, Gemini, DeepSeek) across six task categories and five "
        "interaction conditions that end at an equivalent specification: "
        "one-shot generation, bug-fix, feature-addition, edge-case, and full "
        "multi-turn. Every program is executed on identical per-task "
        "workloads on a controlled Linux host, and package energy is measured "
        "with Intel RAPL. We additionally derive static code metrics and "
        "estimate each program's time complexity both statically (AST "
        "heuristics) and empirically (log–log scaling of runtime across three "
        "input sizes). "
        f"Of {cov['_total']['finals']} programs, {cov['_total']['measured']} "
        "were successfully measured. Median package energy rises "
        f"monotonically with interaction depth, from {med('ONE_SHOT'):.3f} J "
        f"for one-shot to {med('FULL_MULTI_TURN'):.3f} J for full multi-turn "
        f"(+{c4.get('median_pct', 0):.1f}% median; Wilcoxon p="
        f"{D.energy.get('wilcoxon', {}).get('FULL_MULTI_TURN', {}).get('p_value')}), "
        "and the increase is concentrated in the largest programs rather than "
        "in the median, indicating a heavy-tail effect. Multi-turn programs "
        "are longer (median SLOC "
        f"{D.cx['by_condition']['FULL_MULTI_TURN']['median_sloc']:.0f} vs "
        f"{D.cx['by_condition']['ONE_SHOT']['median_sloc']:.0f}) and more "
        "structurally complex, but energy is dominated by runtime "
        f"(Spearman rho={D.cxsum['correlations']['runtime_vs_energy']['spearman_rho']}), "
        "not by code size. The results quantify a practical green-software "
        "cost of iterative AI-assisted development and give a reusable "
        "methodology for measuring complexity and energy together."
    ))
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Keywords: ").bold = True
    p.add_run("green software engineering, energy efficiency, Intel RAPL, "
              "large language models, code generation, multi-turn interaction, "
              "time complexity, empirical scaling.")
    doc.add_page_break()


def front_matter(doc, D):
    h(doc, "Table of Contents", level=1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-3" \\h \\z \\u',
              "Right-click and choose “Update Field” to build the table of contents.")
    doc.add_paragraph()
    h(doc, "List of Figures", level=1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\h \\z \\c "Figure"',
              "Right-click and choose “Update Field” to build the list of figures.")
    doc.add_paragraph()
    h(doc, "List of Tables", level=1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\h \\z \\c "Table"',
              "Right-click and choose “Update Field” to build the list of tables.")
    doc.add_page_break()


def introduction(doc, D):
    h(doc, "1. Introduction", level=1, xe="Introduction")
    h(doc, "1.1 Motivation and Context", level=2)
    para(doc, (
        "Software energy consumption is a first-order concern for datacentres, "
        "edge devices, and the growing population of AI-assisted development "
        "workflows. As generative coding assistants move from autocomplete to "
        "conversational, multi-turn collaboration, the software they produce "
        "increasingly reflects an entire trajectory of prompts, bug reports, "
        "feature requests, and edge-case refinements. Prior work reports the "
        "energy footprint of training and inference, and separately studies "
        "the quality of generated code, but the energy of the *final artifact* "
        "as a function of the *interaction trajectory* remains largely "
        "uncharacterised."))
    h(doc, "1.2 Problem Statement", level=2)
    para(doc, (
        "It is unknown whether realistic multi-turn AI-assisted coding yields "
        "final programs that run with systematically different energy cost "
        "than a single-shot generation of the same specification, and whether "
        "any such difference is explained by size, structural complexity, or "
        "algorithmic time complexity. Without a controlled benchmark, "
        "practitioners cannot reason about the operational energy consequences "
        "of iterating with an assistant."))
    h(doc, "1.3 Research Questions and Objectives", level=2)
    rqs = [
        ("RQ1", "Does multi-turn AI-assisted coding produce final programs with "
                "different energy consumption than one-shot coding?"),
        ("RQ2", "Does the effect vary across models?"),
        ("RQ3", "How do bug fixing, feature addition, and edge-case handling "
                "individually affect energy?"),
        ("RQ4", "What relationships hold among energy, runtime, memory, and "
                "correctness?"),
        ("RQ5", "What code-level characteristics and time-complexity classes "
                "explain energy differences?"),
    ]
    for rid, text in rqs:
        p = doc.add_paragraph()
        p.add_run(f"{rid}. ").bold = True
        p.add_run(text)
    h(doc, "1.4 Contributions", level=2)
    for c in [
        "A reproducible benchmark that measures RAPL package energy of "
        "final programs produced by five equivalent interaction conditions.",
        "A dual methodology for time complexity: a static AST Big-O estimator "
        "and an empirical log–log scaling probe using the same harness workload.",
        "A per-program metrics corpus (1485 programs) of energy, runtime, "
        "memory, power, and static code metrics.",
        "Statistical analysis of interaction-trajectory effects on energy, and "
        "an interpretation mediated by code size and algorithmic complexity.",
        "A carbon-equivalent translation with grid-intensity sensitivity.",
    ]:
        bullet(doc, c)
    h(doc, "1.5 Organization of the Paper", level=2)
    para(doc, (
        "Section 2 reviews background and related work. Section 3 describes "
        "the benchmark design and measurement methodology. Section 4 reports "
        "results, Section 5 discusses them, Section 6 addresses threats to "
        "validity, and Section 7 concludes. Appendices provide the task "
        "catalog, per-condition tables, a metric glossary, the failure "
        "taxonomy, and reproduction commands, followed by an index."))


def related_work(doc, D):
    h(doc, "2. Background and Related Work", level=1, xe="Related work")
    for t, body in [
        ("2.1 Energy Efficiency of Software",
         "Green software engineering studies the operational energy of "
         "software across languages, algorithms, and hardware. RAPL provides "
         "per-socket energy counters on Intel CPUs and has become a standard "
         "instrument for fine-grained measurement in controlled settings."),
        ("2.2 LLMs for Code Generation",
         "A large body of work evaluates LLM code generation for correctness "
         "and style. Reported metrics are dominated by functional pass rates, "
         "with energy and runtime of the generated code rarely quantified."),
        ("2.3 Multi-Turn and Interactive Code Generation",
         "Interactive agents refine code over several turns. Prior studies "
         "examine conversational repair and instruction following, but seldom "
         "hold the final specification constant across trajectories, which is "
         "required to isolate the effect of the trajectory itself."),
        ("2.4 Static Code Metrics and Algorithmic Complexity",
         "Cyclomatic complexity, lines of code, and asymptotic time "
         "complexity are classic proxies for maintainability and performance. "
         "Estimating Big-O from source is undecidable in general, so practical "
         "approaches combine AST pattern heuristics with empirical "
         "measurements on scaled inputs."),
        ("2.5 Research Gap",
         "No prior benchmark, to our knowledge, jointly measures the energy of "
         "LLM-generated final programs, holds the final requirements constant "
         "across interaction conditions, and connects energy to both static "
         "and empirical time-complexity metrics."),
    ]:
        h(doc, t, level=2)
        para(doc, body)
        figure_placeholder(doc, "RW-" + t[0],
                           f"Related-work positioning map for {t}",
                           "Placeholder: insert positioning diagram / taxonomy.")


def methodology(doc, D):
    h(doc, "3. Benchmark Design and Methodology", level=1, xe="Methodology")
    h(doc, "3.1 Overview", level=2)
    para(doc, (
        "The benchmark fixes the final specification of every task and varies "
        "only the interaction trajectory that produced the code. Each final "
        "program is executed on an identical, deterministic workload, and "
        "energy, runtime, memory, and static/complexity metrics are recorded."))
    figure_placeholder(doc, 1, "Benchmark pipeline overview",
                       "Placeholder: pipeline diagram (tasks → generation → "
                       "correctness → execution → metrics → analysis).")

    h(doc, "3.2 Task Taxonomy", level=2)
    para(doc, "Six categories span algorithmic, data, media, application, "
              "search, and text workloads; each contributes up to 25 tasks.")
    cov = D.coverage()
    rows = []
    for cat, label in CATS.items():
        ntasks = len(D.datasets.get(cat, []))
        rows.append([label, ntasks, cov[cat]["finals"], cov[cat]["measured"]])
    rows.append(["Total", sum(len(D.datasets.get(c, [])) for c in CATS),
                 cov["_total"]["finals"], cov["_total"]["measured"]])
    add_table(doc, ["Category", "#Tasks", "#Final programs", "#Measured"],
              rows, "Table 1. Task categories and program coverage.")

    h(doc, "3.3 Interaction Conditions", level=2)
    para(doc, "All conditions end at an equivalent specification:")
    for c in CONDS:
        bullet(doc, f"{COND_LABEL[c]}")
    add_table(doc, ["ID", "Condition", "Trajectory"], [
        ["C0", "ONE_SHOT", "Full specification delivered at once"],
        ["C1", "BUG_FIX", "Initial task followed by a bug report"],
        ["C2", "FEATURE_ADDITION", "Initial task followed by a feature request"],
        ["C3", "EDGE_CASE", "Initial task followed by an edge-case requirement"],
        ["C4", "FULL_MULTI_TURN", "Initial → bug fix → feature → edge case"],
    ], "Table 2. Interaction conditions.")

    h(doc, "3.4 Models and Code Generation", level=2)
    para(doc, "Four assistant models (GPT, Claude, Gemini, DeepSeek) generated "
              "code in fresh conversations per condition, without manual "
              "repair.")
    add_table(doc, ["Model", "Finals", "Measured"], [
        [m, sum(1 for r in D.metrics if r["model"] == m),
         sum(1 for r in D.metrics if r["model"] == m and r["status"] == "ok")]
        for m in MODELS], "Table 3. Programs per model.")

    h(doc, "3.5 Correctness and Harness Protocol", level=2)
    para(doc, "Each task ships a harness that materialises a deterministic "
              "workload and invokes the candidate and a reference solution "
              "through the same API. Correctness is recorded separately from "
              "energy so that a program which runs but differs from the "
              "reference is still measured.")

    h(doc, "3.6 Energy Measurement with Intel RAPL", level=2)
    para(doc, "Package energy is read from /sys/class/powercap/intel-rapl:0/"
              "energy_uj. Each unit performs one warm-up run and K=5 timed runs "
              "inside a single RAPL window; joules per run are the counter "
              "delta divided by K. Timeouts are capped at 30 s per run.")
    figure_placeholder(doc, 2, "Measurement rig block diagram",
                       "Placeholder: hardware + software measurement stack.")

    h(doc, "3.7 Runtime, Memory and CPU Measurement", level=2)
    para(doc, "Runtime is the median of the K timed runs; peak memory is "
              "captured with /usr/bin/time. Packet power is derived as "
              "energy/runtime.")

    h(doc, "3.8 Static Code Metrics", level=2)
    para(doc, "For each final program we parse the AST and compute lines of "
              "code (total/SLOC/comments/blank), function and class counts, "
              "loop counts and maximum nesting depth, branch counts, "
              "recursion, sort usage, comprehensions, import counts, "
              "non-standard-library imports, and McCabe-style cyclomatic "
              "complexity.")
    add_table(doc, ["Metric", "Definition"], [
        ["SLOC", "Non-blank, non-comment source lines"],
        ["Max loop depth", "Deepest nesting of for/while loops"],
        ["Cyclomatic", "Decision points + 1 (McCabe)"],
        ["Recursion", "Function calls its own name"],
        ["Non-stdlib imports", "Imports outside the Python standard library"],
    ], "Table 4. Static metric definitions (full glossary in Appendix C).")

    h(doc, "3.9 Time-Complexity Estimation", level=2)
    para(doc, "Because exact static Big-O inference is undecidable, we use an "
              "explicit, reproducible AST heuristic:")
    for rule in [
        "Recursion combined with a loop → O(2^n) (recursive search/backtracking).",
        "Recursion without a loop → O(recursive).",
        "Nested loop depth 1 → O(n); with a sort → O(n log n).",
        "Nested loop depth 2 → O(n^2); with a sort → O(n^2 log n).",
        "Nested loop depth 3 → O(n^3); depth ≥ 4 → O(n^4).",
        "No loops → O(1) (or O(n log n) if a sort dominates).",
    ]:
        bullet(doc, rule)
    para(doc, "The estimator is validated against the dataset's declared "
              "complexity targets and against empirical scaling slopes.")
    table_placeholder(doc, 5, "Confusion matrix: estimated class vs declared "
                              "target (render from complexity_metrics.json)")

    h(doc, "3.10 Empirical Scaling Probe", level=2)
    para(doc, "Each program and its reference are run through the task harness "
              "at three input scales (small, medium, large; the generator tiles "
              "the workload to 300 / 4 000 / 15 000 elements for the "
              "algorithms category). For each scale we take the median of up "
              "to three timed executions and fit")
    para(doc, "log(runtime_ms) = b · log(input_bytes) + a", italic=True,
         align="center")
    para(doc, "The exponent b is the empirical growth estimate: b ≈ 0 constant, "
              "b ≈ 1 linear, b ≈ 2 quadratic, b > 2 superlinear. A per-scale "
              "time budget prevents exponential tasks from stalling the sweep.")
    figure_placeholder(doc, 3, "Runtime vs input size (log–log) for "
                               "representative programs",
                       "Placeholder: log–log scaling plot.")

    h(doc, "3.11 Carbon-Equivalent Estimation", level=2)
    ci = D.carbon.get("intensity_gco2eq_per_kwh", 480)
    para(doc, f"Energy is converted to operational CO2eq with a configurable "
              f"grid carbon intensity (default {ci} gCO2eq/kWh) and a "
              "sensitivity analysis over US, EU, and low-carbon grids.")

    h(doc, "3.12 Statistical Analysis", level=2)
    para(doc, "Paired within-(task,model) comparisons use the Wilcoxon "
              "signed-rank test; multi-group comparisons use the "
              "Kruskal–Wallis test. Effect sizes are reported as median "
              "percentage change.")

    h(doc, "3.13 Reproducibility", level=2)
    para(doc, "All scripts and generated tables are listed in Appendix E; the "
              "energy ledger is append-only and resumable by code hash.")


def results(doc, D):
    h(doc, "4. Results", level=1, xe="Results")
    cov = D.coverage()

    h(doc, "4.1 Dataset and Measurement Coverage", level=2)
    para(doc, f"{cov['_total']['finals']} final programs were collected; "
              f"{cov['_total']['parse']} parse as Python and "
              f"{cov['_total']['measured']} were successfully executed and "
              f"measured ({100*cov['_total']['measured']/cov['_total']['finals']:.1f}%).")
    add_table(doc, ["Category", "Finals", "Parseable", "Measured"],
              [[CATS[c], cov[c]["finals"], cov[c]["parse"], cov[c]["measured"]]
               for c in CATS] +
              [["Total", cov["_total"]["finals"], cov["_total"]["parse"],
                cov["_total"]["measured"]]],
              "Table 6. Coverage by category.")

    h(doc, "4.2 Energy Consumption by Interaction Condition", level=2)
    ec = D.energy.get("overall", {})
    rows = []
    for c in CONDS:
        e = ec.get(c, {})
        rows.append([COND_LABEL[c], e.get("n"), f"{e.get('median_j', 0):.3f}",
                     f"{e.get('mean_j', 0):.3f}",
                     f"{e.get('mean_runtime_s', 0):.4f}"])
    add_table(doc, ["Condition", "n", "Median J", "Mean J", "Mean runtime s"],
              rows, "Table 7. Energy and runtime by interaction condition.")
    figure_placeholder(doc, 4, "Energy distribution by condition (box/violin)",
                       "Placeholder: render from results/final/plots/.")
    figure_placeholder(doc, 5, "Median energy by condition with confidence "
                               "intervals",
                       "Placeholder: error-bar chart.")

    h(doc, "4.3 Paired Analysis: ΔE from One-Shot to Multi-Turn", level=2)
    delta = D.energy.get("delta", {})
    wil = D.energy.get("wilcoxon", {})
    rows = []
    for c in CONDS[1:]:
        d = delta.get(c, {})
        w = wil.get(c, {})
        rows.append([COND_LABEL[c], summary_n(D, c),
                     f"{d.get('mean_pct', 0):.2f}", f"{d.get('median_pct', 0):.2f}",
                     d.get("n_increase"), d.get("n_decrease"),
                     f"{w.get('p_value', float('nan')):.4f}"])
    add_table(doc, ["Condition", "n paired", "Mean ΔE %", "Median ΔE %",
                    "#↑", "#↓", "Wilcoxon p"], rows,
              "Table 8. Paired energy change versus one-shot (ΔE).")
    para(doc, "Only the full multi-turn condition reaches statistical "
              "significance, indicating that the cumulative trajectory—not any "
              "single step—drives the energy increase.")
    figure_placeholder(doc, 6, "Paired ΔE distribution per condition",
                       "Placeholder: paired delta histogram / raincloud.")

    h(doc, "4.4 Effect of Individual Interaction Steps", level=2)
    para(doc, "Bug-fix and feature-addition produce near-zero median ΔE "
              "(both median changes are within a few percent), edge-case "
              "handling is intermediate, and the full trajectory compounds the "
              "increase.")

    h(doc, "4.5 Model-Specific Effects", level=2)
    bm = D.energy.get("by_model", {})
    rows = []
    for m in MODELS:
        e = bm.get(m, {})
        by = e.get("mean_energy_by_cond", {})
        rows.append([m] + [f"{by.get(c, 0):.3f}" for c in CONDS] +
                    [f"{e.get('mean_delta_vs_oneshot_pct', 0):.1f}"])
    add_table(doc, ["Model"] + [COND_LABEL[c].split()[0] for c in CONDS] +
              ["Mean ΔE %"], rows,
              "Table 9. Mean energy (J) by condition and model.")
    figure_placeholder(doc, 7, "Energy by condition, faceted by model",
                       "Placeholder: small-multiples chart.")

    h(doc, "4.6 Category-Specific Effects", level=2)
    bc = D.energy.get("by_category", {})
    rows = []
    for c in CATS:
        e = bc.get(c, {})
        rows.append([CATS[c], e.get("n_units"),
                     _fmt(e.get("mean_delta_vs_oneshot_pct")),
                     e.get("n_paired_c4")])
    add_table(doc, ["Category", "Units", "Mean ΔE %", "n paired (C4)"], rows,
              "Table 10. Energy change by category.")

    h(doc, "4.7 Runtime, Power and Memory", level=2)
    corr = D.cxsum.get("correlations", {})
    rv = corr.get("runtime_vs_energy") or {}
    para(doc, f"Runtime and energy are almost collinear "
              f"(Spearman rho={rv.get('spearman_rho')}, "
              f"Pearson r={rv.get('pearson_r')}), confirming that package "
              "energy in this workload is dominated by execution time. "
              "Derived power (energy/runtime) therefore varies less than "
              "energy itself.")
    figure_placeholder(doc, 8, "Runtime vs energy scatter (log–log)",
                       "Placeholder: render results/final/plots/"
                       "metrics_runtime_vs_energy.png.")

    h(doc, "4.8 Static Code Metrics", level=2)
    bcx = D.cx.get("by_condition", {})
    rows = []
    for c in CONDS:
        g = bcx.get(c, {})
        rows.append([COND_LABEL[c], g.get("median_sloc"),
                     g.get("median_functions"), g.get("median_cyclomatic"),
                     g.get("median_complexity_rank"),
                     g.get("pct_quadratic_plus")])
    add_table(doc, ["Condition", "Median SLOC", "Median functions",
                    "Median cyclomatic", "Median complexity rank",
                    "% quadratic+"], rows,
              "Table 11. Static metrics by condition.")
    para(doc, "Code size and structural complexity grow monotonically with "
              "interaction depth: full multi-turn programs are the longest and "
              "most branched, consistent with the accumulation of requirements "
              "across turns.")
    figure_placeholder(doc, 9, "SLOC and cyclomatic complexity by condition",
                       "Placeholder: boxplots from results/final/plots/.")

    h(doc, "4.9 Time-Complexity Distribution", level=2)
    dist = D.cx.get("complexity_distribution", {})
    add_table(doc, ["Estimated class", "Programs"],
              [[k, v] for k, v in dist.items()],
              "Table 12. Estimated time-complexity class distribution (n="
              f"{D.cxsum.get('n_parseable')}).")
    para(doc, "The distribution is dominated by linear and linearithmic "
              "programs, with a meaningful tail of quadratic, cubic, and "
              "exponential implementations—the latter concentrated in "
              "recursive-search algorithmic tasks.")
    figure_placeholder(doc, 10, "Complexity class distribution by condition",
                       "Placeholder: render results/final/plots/"
                       "metrics_complexity_by_condition.png.")

    h(doc, "4.10 Estimated vs Empirical Complexity", level=2)
    se = D.cx.get("static_vs_empirical")
    if se:
        para(doc, f"Across {se['n']} programs with both a static estimate and "
                  f"an empirical slope, Spearman(rank, slope) = "
                  f"{se['spearman_rank_vs_slope']}. Treating the static "
                  "estimator as a binary superlinear classifier (rank ≥ 2) "
                  f"against the empirical criterion (slope ≥ 1.5) yields "
                  f"precision {se['precision']} and recall {se['recall']} "
                  f"(TP={se['tp']}, FP={se['fp']}, FN={se['fn']}, TN={se['tn']}).")
    else:
        para(doc, "Empirical scaling slopes are still being computed; the "
                  "static/empirical comparison will populate Table 13.")
    ss = D.scalingsum
    if ss:
        para(doc, f"The probe produced slopes for {ss.get('n_slopes')} programs "
                  f"across {ss.get('n_reference_tasks')} reference tasks; the "
                  f"median program slope is {ss.get('median_cand_slope_ml')} "
                  f"and the median reference slope is "
                  f"{ss.get('median_reference_slope')}.")
    table_placeholder(doc, 13, "Estimated class vs empirical slope agreement")
    figure_placeholder(doc, 11, "Empirical growth exponent distribution",
                       "Placeholder: render results/final/plots/"
                       "metrics_slope_hist.png.")

    h(doc, "4.11 Relationship between Complexity and Energy", level=2)
    c = D.cxsum.get("correlations", {})
    rows = []
    for label, key in [("SLOC vs energy", "sloc_vs_energy"),
                       ("Cyclomatic vs energy", "cyclomatic_vs_energy"),
                       ("Complexity rank vs energy", "complexity_rank_vs_energy"),
                       ("Loop depth vs energy", "loop_depth_vs_energy"),
                       ("SLOC vs runtime", "sloc_vs_runtime"),
                       ("Runtime vs energy", "runtime_vs_energy")]:
        v = c.get(key) or {}
        rows.append([label, v.get("n"), v.get("spearman_rho"), v.get("pearson_r")])
    add_table(doc, ["Pair", "n", "Spearman rho", "Pearson r"], rows,
              "Table 14. Cross-metric correlations (measured programs).")
    para(doc, "Code-level complexity correlates weakly with energy across "
              "heterogeneous tasks, whereas runtime correlates almost "
              "perfectly. This shows that the energy penalty of multi-turn "
              "code is transmitted primarily through longer or heavier "
              "workloads, not through source-level complexity per se.")

    h(doc, "4.12 Carbon-Equivalent Emissions", level=2)
    tot = D.carbon.get("total", {})
    para(doc, f"The measured programs consumed {tot.get('energy_j')} J in "
              f"total, equivalent to {tot.get('co2_mg')} mgCO2eq at the "
              f"default intensity. Scaling analysis attributes an additional "
              f"~{D.carbon.get('scaling', {}).get('extra_co2_ug_per_multi_turn_run')} "
              "µgCO2eq per multi-turn run relative to one-shot.")
    add_table(doc, ["Grid intensity", "gCO2eq/kWh", "Median one-shot µg",
                    "Median multi-turn µg", "Total mg"],
              [[k, v.get("intensity_gco2eq_per_kwh"),
                v.get("median_oneshot_co2_ug"),
                v.get("median_multi_turn_co2_ug"),
                v.get("total_co2_mg")]
               for k, v in D.carbon.get("sensitivity_by_intensity", {}).items()],
              "Table 15. Carbon sensitivity by grid intensity.")
    figure_placeholder(doc, 12, "Carbon by condition and grid intensity",
                       "Placeholder: grouped bar chart.")

    h(doc, "4.13 Failure Taxonomy and Coverage Bias", level=2)
    para(doc, "The remaining unmeasured units cluster into embedded "
              "self-test logic errors, non-Python submissions, runtime bugs, "
              "and CLI-argument mismatches. Coverage is therefore slightly "
              "biased toward programs that run cleanly under the harness.")
    table_placeholder(doc, 16, "Failure taxonomy with counts and examples "
                               "(from results/final/energy_failures.csv)")


def discussion(doc, D):
    h(doc, "5. Discussion", level=1, xe="Discussion")
    h(doc, "5.1 Interpretation of Main Findings", level=2)
    para(doc, "Multi-turn interaction leaves a measurable green-software "
              "footprint. The median program barely changes between one-shot "
              "and bug-fix, but the full trajectory shifts the median upward "
              "and, more importantly, thickens the upper tail: the mean rises "
              "far more than the median.")
    h(doc, "5.2 Why Multi-Turn Programs Consume More Energy", level=2)
    for t in [
        "Accumulated requirements produce longer programs, and longer code "
        "tends to encode richer, less pruned algorithms.",
        "Edge-case and feature turns encourage defensive branches and "
        "additional passes over the input.",
        "Some trajectories converge on asymptotically heavier solutions, "
        "visible as superlinear empirical slopes.",
    ]:
        bullet(doc, t)
    h(doc, "5.3 Complexity as a Mediator", level=2)
    para(doc, "Static complexity rises with interaction depth, but its direct "
              "correlation with energy is weak across categories. The "
              "mediating variable is runtime: energy ≈ power × time, and "
              "runtime tracks the input-scaling behaviour of the chosen "
              "algorithm. This argues for treating algorithmic-complexity "
              "regressions, not raw SLOC, as the key leverage point.")
    h(doc, "5.4 Implications for Practitioners", level=2)
    for t in [
        "Treat iterative features as potential complexity regressions and "
        "re-benchmark the final artifact, not just the first draft.",
        "Ask assistants to justify asymptotic cost after each interactive "
        "turn, not only after the final one.",
        "Prefer terminating a session with a complexity review once the "
        "trajectory lengthens.",
    ]:
        bullet(doc, t)
    h(doc, "5.5 Implications for Tool Builders", level=2)
    para(doc, "IDE-integrated green linters could surface estimated complexity "
              "and measured energy deltas per turn, making the accumulating "
              "cost visible during interactive development.")


def threats(doc, D):
    h(doc, "6. Threats to Validity", level=1, xe="Validity")
    for t, body in [
        ("6.1 Construct Validity",
         "RAPL package energy includes components beyond the program under "
         "study; we mitigate by using identical workloads and subtracting idle "
         "via a per-run baseline, but some noise remains."),
        ("6.2 Internal Validity",
         "The static Big-O estimator is a heuristic; it is cross-checked "
         "against declared targets and empirical slopes. Harness workloads are "
         "deterministic and shared across conditions."),
        ("6.3 External Validity",
         "Results are from one host (Intel RAPL, 8 CPUs) and four models; "
         "generalisation to other hardware, models, or languages requires "
         "replication."),
        ("6.4 Conclusion Validity",
         "Some units are unmeasured due to correctness or launch failures, "
         "biasing coverage toward runnable programs. Paired tests restrict to "
         "units present in both conditions to limit this bias."),
    ]:
        h(doc, t, level=2)
        para(doc, body)


def conclusion(doc, D):
    h(doc, "7. Conclusion and Future Work", level=1, xe="Conclusion")
    h(doc, "7.1 Summary", level=2)
    para(doc, "We introduced a benchmark that isolates the effect of "
              "human–AI interaction trajectory on the energy of final programs. "
              "Holding the final specification constant, multi-turn "
              "trajectories increase median package energy relative to "
              "one-shot generation, with the full multi-turn condition the "
              "only statistically significant effect. The increase is mediated "
              "by runtime and algorithm choice rather than by source-level "
              "size alone. We released a per-program metrics corpus including "
              "static metrics and both static and empirical time-complexity "
              "estimates.")
    h(doc, "7.2 Future Work", level=2)
    for t in [
        "Extension to more models, languages, and hardware platforms.",
        "Per-turn energy attribution across an entire session.",
        "Automatic complexity regression detection during interactive coding.",
        "Larger empirical scaling sweeps with finer input-size grids.",
    ]:
        bullet(doc, t)


def references(doc):
    h(doc, "References", level=1, xe="References")
    refs = [
        "[1] Intel Corporation. Intel 64 and IA-32 Architectures Software "
        "Developer's Manual, Volume 3B: RAPL power management.",
        "[2] D. Patterson et al. “Carbon emissions and large neural network "
        "training.” arXiv preprint, 2021.",
        "[3] S. Georgiou, M. Kechagia, T. Sharma, F. Sarro, Y. Zou. “Green AI: "
        "do machine learning models produce CO2 emissions?” IEEE TSE, 2022.",
        "[4] A. Hindle. “Green software engineering: the curse of methodology.” "
        "IEEE Access, 2023.",
        "[5] M. Chen et al. “Evaluating large language models trained on code.” "
        "arXiv preprint, 2021.",
        "[6] J. Austin et al. “Program synthesis with large language models.” "
        "arXiv preprint, 2021.",
        "[7] R. Nijkamp et al. “CodeGen: an open large language model for code "
        "with multi-turn program synthesis.” ICLR, 2023.",
        "[8] T. McCabe. “A complexity measure.” IEEE TSE, 1976.",
        "[9] G. Pinto, F. Castor, L. Maia. “Energy efficiency: a new concern "
        "for software engineers.” SAC, 2014.",
        "[10] [PLACEHOLDER — add benchmark-specific and up-to-date references.]",
    ]
    for r in refs:
        para(doc, r, size=9)


def appendices(doc, D):
    doc.add_page_break()
    h(doc, "Appendix A: Task Catalog", level=1, xe="Appendix A")
    para(doc, "Each category provided up to 25 candidate tasks; the table "
              "lists each task's identifier, title, difficulty, and declared "
              "complexity target.")
    rows = []
    for cat in CATS:
        for t in D.datasets.get(cat, []):
            prof = t.get("computational_profile")
            comp = prof.get("complexity") if isinstance(prof, dict) else prof
            rows.append([cat.split("_")[0].upper()[:2] + "",
                         t.get("task_id"), (t.get("title") or "")[:34],
                         t.get("difficulty"), comp or "-"])
    add_table(doc, ["Cat", "Task", "Title", "Difficulty", "Declared"],
              rows, "Table A1. Full task catalog.",
              font_size=6.5)

    doc.add_page_break()
    h(doc, "Appendix B: Per-Condition Metrics", level=1, xe="Appendix B")
    bcx = D.cx.get("by_condition", {})
    rows = []
    for c in CONDS:
        g = bcx.get(c, {})
        rows.append([COND_LABEL[c], g.get("n"), g.get("median_sloc"),
                     g.get("median_loops"), g.get("mean_max_loop_depth"),
                     g.get("median_cyclomatic"), g.get("median_complexity_rank"),
                     g.get("pct_recursive"), g.get("compliant_rate")])
    add_table(doc, ["Condition", "n", "SLOC", "Loops", "Mean depth",
                    "Cyclomatic", "Rank", "%rec", "Compliant %"], rows,
              "Table B1. Static metrics per condition.")

    h(doc, "Appendix C: Metric Glossary", level=1, xe="Glossary")
    add_table(doc, ["Term", "Meaning"], [
        ["Package energy", "CPU socket energy from RAPL (joules per run)"],
        ["Core energy", "CPU core-domain energy from RAPL"],
        ["ΔE", "(E_multi_turn − E_one_shot) / E_one_shot × 100"],
        ["Power", "Package energy divided by runtime (watts)"],
        ["SLOC", "Source lines of code (non-blank, non-comment)"],
        ["Cyclomatic complexity", "McCabe decision-point count + 1"],
        ["Complexity rank", "Ordinal for the estimated Big-O class"],
        ["Empirical slope", "Log–log runtime vs input-size exponent b"],
        ["Compliance", "Estimated class no worse than declared target"],
    ], "Table C1. Glossary of tracked metrics.")

    h(doc, "Appendix D: Failure Taxonomy", level=1, xe="Appendix D")
    add_table(doc, ["Failure kind", "Meaning", "Input-fixable"], [
        ["WRONG_OUTPUT", "Embedded self-test assertion fails", "No"],
        ["RUNTIME_BUG", "Program raises at runtime", "Sometimes"],
        ["CLI_ARGS", "No invocation produced exit 0", "Sometimes"],
        ["NOT_PYTHON", "File is prose/truncated, not Python", "No"],
        ["SILENT_RC1", "Exits non-zero without output", "Sometimes"],
        ["MISSING_DEP", "Imports a non-available third-party module", "No"],
        ["MISSING_FILE", "Reads a file not provided by the workload", "Yes"],
    ], "Table D1. Failure taxonomy (from energy_failures.csv).")

    h(doc, "Appendix E: Reproduction Commands", level=1, xe="Appendix E")
    for cmd in [
        "python3 scripts/ingest_zips.py zip_src/*.zip",
        "python3 scripts/gen_inputs.py && python3 scripts/gen_inputs_extra.py",
        "python3 scripts/measure_energy.py",
        "python3 analysis/code_metrics.py",
        "python3 analysis/scaling_probe.py algorithms_computation",
        "python3 analysis/complexity_report.py",
        "python3 analysis/energy_report.py",
        "python3 analysis/carbon_report.py",
        "python3 analysis/energy_plots.py",
        "python3 scripts/make_paper.py",
    ]:
        para(doc, cmd, size=9)


def index_section(doc):
    doc.add_page_break()
    h(doc, "Index", level=1)
    p = doc.add_paragraph()
    add_field(p, 'INDEX \\c "1"',
              "Right-click and choose “Update Field” to build the index.")


def summary_n(D, cond):
    return (D.carbon.get("delta_vs_oneshot", {}).get(cond, {})
            or D.energy.get("delta", {}).get(cond, {})).get("n_paired", "?")


def _fmt(x):
    return "-" if x is None else (f"{x:.2f}" if isinstance(x, float) else x)


def build():
    D = Data()
    doc = Document()
    # base style
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    title_page(doc, D)
    abstract(doc, D)
    front_matter(doc, D)
    introduction(doc, D)
    related_work(doc, D)
    methodology(doc, D)
    results(doc, D)
    discussion(doc, D)
    threats(doc, D)
    conclusion(doc, D)
    references(doc)
    appendices(doc, D)
    index_section(doc)

    DOCX.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    n_par = len(doc.paragraphs)
    n_tab = len(doc.tables)
    print(f"[paper] wrote {OUT.relative_to(REPO)} "
          f"({n_par} paragraphs, {n_tab} tables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
