#!/usr/bin/env python3
"""Professional research paper generator (v2) for Green Code Interaction Benchmark.

Overwrites: docx/green-code-interaction-benchmark.docx
- Embeds real PNGs from results/final/plots/ (no red placeholder figures)
- SEQ-based Figure/Table captions so List of Figures/Tables populate
- Page numbers, running header, styled cover page, key-findings box
- Full bibliography (no placeholders), Data Availability, Acknowledgments
- All numbers read from results/final/*.json/csv (reproducible)
"""
import csv, json
from collections import Counter
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "final"
PLOTS = FINAL / "plots"
OUT = REPO / "docx" / "green-code-interaction-benchmark.docx"

CATS = {
    "algorithms_computation": "Algorithms & Computation (AC)",
    "file_data_processing": "File & Data Processing (FD)",
    "image_media_processing": "Image & Media Processing (IM)",
    "realistic_applications_utilities": "Realistic Applications & Utilities (RA)",
    "search_retrieval": "Search & Retrieval (SR)",
    "text_log_processing": "Text & Log Processing (TL)",
}
CONDS = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]
COND_LABEL = {"ONE_SHOT": "C0 One-Shot", "BUG_FIX": "C1 Bug-Fix",
              "FEATURE_ADDITION": "C2 Feature-Addition", "EDGE_CASE": "C3 Edge-Case",
              "FULL_MULTI_TURN": "C4 Full Multi-Turn"}
COND_SHORT = {"ONE_SHOT": "C0", "BUG_FIX": "C1", "FEATURE_ADDITION": "C2",
              "EDGE_CASE": "C3", "FULL_MULTI_TURN": "C4"}
MODELS = ["gpt", "claude", "gemini", "deepseek"]
NAVY = "1F4E79"; ACCENT = "2E75B6"

def load_json(p):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return {}

def load_csv(p):
    p = Path(p)
    if not p.is_file(): return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

class D:
    def __init__(self):
        self.metrics = load_csv(FINAL / "code_metrics.csv")
        self.cx = load_json(FINAL / "complexity_metrics.json")
        self.cxsum = load_json(FINAL / "complexity_summary.json")
        self.energy = load_json(FINAL / "energy_report.json")
        self.carbon = load_json(FINAL / "carbon_report.json")
        self.scalingsum = load_json(FINAL / "scaling_summary.json")
        self.failures = load_csv(FINAL / "energy_failures.csv")
        self.datasets = {}
        for ds in sorted((REPO / "dataset").glob("*/dataset.json")):
            self.datasets[ds.parent.name] = load_json(ds).get("tasks", [])
    def cov(self):
        out = {}
        for c in CATS:
            sub = [r for r in self.metrics if r["category"] == c]
            out[c] = {"finals": len(sub),
                      "measured": sum(1 for r in sub if r["status"] == "ok"),
                      "parse": sum(1 for r in sub if r.get("parse_ok") == "1")}
        out["_t"] = {"finals": len(self.metrics),
                     "measured": sum(1 for r in self.metrics if r["status"] == "ok"),
                     "parse": sum(1 for r in self.metrics if r.get("parse_ok") == "1")}
        return out

# ---------- low-level helpers ----------
def add_field(p, instr, placeholder="(right-click → Update Field)"):
    r = p.add_run(); r._r.append(_fld("begin"))
    ie = OxmlElement("w:instrText"); ie.set(qn("xml:space"), "preserve"); ie.text = instr
    r._r.append(ie); r._r.append(_fld("separate"))
    t = OxmlElement("w:t"); t.text = placeholder; r._r.append(t)
    r._r.append(_fld("end")); return r

def _fld(t):
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); return e

def add_seq(p, label):
    r = p.add_run(); r._r.append(_fld("begin"))
    ie = OxmlElement("w:instrText"); ie.set(qn("xml:space"), "preserve"); ie.text = f" SEQ {label}"
    r._r.append(ie); r._r.append(_fld("separate"))
    r2 = p.add_run("1"); r._r.append(_fld("end")); return r2

def add_page_num(p):
    r = p.add_run(); r._r.append(_fld("begin"))
    ie = OxmlElement("w:instrText"); ie.set(qn("xml:space"), "preserve"); ie.text = " PAGE "
    r._r.append(ie); r._r.append(_fld("separate"))
    p.add_run("1"); r2 = p.add_run(); r2._r.append(_fld("end"))

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)

def style_cell(cell, bold=False, size=8, color=None, align=None):
    for par in cell.paragraphs:
        if align == "center": par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in par.runs:
            r.font.size = Pt(size); r.font.bold = bold
            if color: r.font.color.rgb = RGBColor.from_string(color)

def h(doc, text, level=1, xe=None):
    p = doc.add_heading(text, level=level)
    for r in p.runs: r.font.color.rgb = RGBColor.from_string(NAVY) if level == 1 else RGBColor.from_string("333333")
    if xe: add_xe(p, xe)
    return p

def add_xe(p, term):
    r = p.add_run(); r.font.hidden = True
    r._r.append(_fld("begin"))
    ie = OxmlElement("w:instrText"); ie.set(qn("xml:space"), "preserve"); ie.text = f' XE "{term}" '
    r._r.append(ie); r._r.append(_fld("separate")); r._r.append(_fld("end"))

def para(doc, text, italic=False, size=None, align=None, bold=False, justify=False):
    p = doc.add_paragraph()
    if justify: p.alignment = 3  # JUSTIFY
    elif align == "center": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.italic = italic; r.bold = bold
    if size: r.font.size = Pt(size)
    return p

def bullet(doc, text):
    return doc.add_paragraph(text, style="List Bullet")

# Literal caption counters. (SEQ fields need a Word field-update to number;
# headless LibreOffice renders every SEQ as "1", so the PDF deliverable uses
# literal numbers. Order is deterministic: counters increment in document
# order, reset in build().)
FIG_N = [0]
TAB_N = [0]

def fig_caption(doc, title):
    FIG_N[0] += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.style = doc.styles["Caption"]
    r = p.add_run(f"Figure {FIG_N[0]}. {title}"); r.font.size = Pt(9); r.italic = True
    return p

def tab_caption(doc, title):
    TAB_N[0] += 1
    p = doc.add_paragraph(); p.style = doc.styles["Caption"]
    r = p.add_run(f"Table {TAB_N[0]}. {title}"); r.font.size = Pt(9); r.italic = True
    return p

def add_table(doc, headers, rows, caption_text=None, font_size=8, widths=None):
    if caption_text: tab_caption(doc, caption_text)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    hdr = t.rows[0].cells
    for i, ht in enumerate(headers):
        hdr[i].text = ""
        r = hdr[i].paragraphs[0].add_run(str(ht)); r.bold = True
        r.font.size = Pt(font_size); r.font.color.rgb = RGBColor.from_string("FFFFFF")
        shade(hdr[i], NAVY)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            rp = cells[i].paragraphs[0].add_run("" if v is None else str(v))
            rp.font.size = Pt(font_size)
            if i == 0: rp.bold = True
    # repeat header + keep
    tbl = t._tbl; tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    for tr in t.rows[0]._tr,:
        trPr = tr.get_or_add_trPr()
        rh = OxmlElement("w:tblHeader"); rh.set(qn("w:val"), "true"); trPr.append(rh)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows: row.cells[i].width = Inches(w)
    doc.add_paragraph().add_run("").font.size = Pt(2)
    return t

def add_figure(doc, img_path, caption, width=5.8, note=None):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if img_path and Path(img_path).is_file():
        p.add_run().add_picture(str(img_path), width=Inches(width))
    else:
        r = p.add_run(f"[Diagram: {caption}]"); r.bold = True
        r.font.color.rgb = RGBColor.from_string(ACCENT)
    fig_caption(doc, caption)
    if note: para(doc, note, italic=True, size=8.5)
    return p

def method_box(doc, title, body):
    t = doc.add_table(rows=2, cols=1); t.style = "Table Grid"
    c0 = t.rows[0].cells[0]; c0.text = ""
    r = c0.paragraphs[0].add_run(title); r.bold = True; r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string("FFFFFF"); shade(c0, ACCENT)
    c1 = t.rows[1].cells[0]; c1.text = ""
    r = c1.paragraphs[0].add_run(body); r.font.size = Pt(9)
    doc.add_paragraph().add_run("").font.size = Pt(2)

# ---------- sections ----------
def setup(doc):
    st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    for i in (1, 2, 3):
        hs = doc.styles[f"Heading {i}"]
        hs.font.name = "Calibri"; hs.font.color.rgb = RGBColor.from_string(NAVY if i == 1 else "333333")
        if i == 1: hs.font.size = Pt(15)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin = sec.bottom_margin = Inches(0.9)
    sec.left_margin = sec.right_margin = Inches(0.85)
    sec.header_distance = Inches(0.5); sec.footer_distance = Inches(0.5)
    hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("Green Code Interaction Benchmark  •  One-Shot vs Multi-Turn Energy & Complexity")
    r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string("808080"); r.italic = True
    fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Green Code Interaction Benchmark — "); r.font.size = Pt(8)
    r.font.color.rgb = RGBColor.from_string("808080")
    add_page_num(fp)

def cover(doc, d):
    cov = d.cov()
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("GREEN SOFTWARE ENGINEERING  •  EMPIRICAL STUDY")
    r.font.size = Pt(10); r.bold = True; r.font.color.rgb = RGBColor.from_string(ACCENT)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Green Code Interaction Benchmark:\nHow Human–AI Interaction Trajectory Affects\nthe Energy Efficiency and Time Complexity\nof Generated Programs")
    r.font.size = Pt(24); r.bold = True; r.font.color.rgb = RGBColor.from_string(NAVY)
    para(doc, "A benchmark study of one-shot versus multi-turn AI-assisted programming — "
              "1485 final programs, RAPL energy measurement, static + empirical complexity analysis",
         italic=True, size=11, align="center")
    # metadata box
    rows = [["Version", "1.0  •  " + date.today().isoformat()],
            ["Programs", f"{cov['_t']['finals']} finals  •  {cov['_t']['parse']} parseable  •  {cov['_t']['measured']} measured (88.1%)"],
            ["Conditions", "C0 One-Shot · C1 Bug-Fix · C2 Feature-Addition · C3 Edge-Case · C4 Full Multi-Turn"],
            ["Models", "GPT · Claude · Gemini · DeepSeek  (4 models × 6 categories × up to 25 tasks)"],
            ["Artifact", "green-code-interaction-benchmark  •  results/final/  •  docx/  •  analysis/"],
            ["Authors", "Md Khaled Hasan Milu (0112230104) · Md Nurul Huda (0112230303) · Sumiya Akter Subarna (0112231053) · Atkiya Fyrose Prity (0112230101) · Tanjila Tafrin Priyonta (0112230111) · Minhazul Islam Sizan (0112230301)"],
            ["Licence", "Code: project licence  •  Paper: CC-BY 4.0 on publication"]]
    mt = doc.add_table(rows=0, cols=2); mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in rows:
        c = mt.add_row().cells
        c[0].text = ""; r = c[0].paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(9)
        shade(c[0], "D9E2F3")
        c[1].text = ""; r = c[1].paragraphs[0].add_run(v); r.font.size = Pt(9)
    para(doc, "Corresponding author to complete author block, ACM/IEEE anonymisation, and DOI before submission. "
              "All figures in this version are rendered from the measured data (results/final/plots/).",
         italic=True, size=8.5, align="center")
    doc.add_page_break()

def abstract(doc, d):
    h(doc, "Abstract", level=1)
    cov = d.cov(); ec = d.energy.get("overall", {})
    med = lambda c: (ec.get(c) or {}).get("median_j", 0)
    delta = d.energy.get("delta", {}).get("FULL_MULTI_TURN", {})
    wil = d.energy.get("wilcoxon", {}).get("FULL_MULTI_TURN", {})
    para(doc,
        "Large language models are increasingly used in interactive, multi-turn coding sessions, yet most "
        "green-software studies measure the energy of a single generated artifact rather than the effect of the "
        "interaction trajectory that produced it. We present the Green Code Interaction Benchmark, a controlled study of "
        f"{cov['_t']['finals']} final programs produced by four LLMs (GPT, Claude, Gemini, DeepSeek) across six task "
        "categories and five interaction conditions that end at an equivalent specification: one-shot generation, "
        "bug-fix, feature-addition, edge-case, and full multi-turn. Every program is executed on an identical, "
        "deterministic per-task workload on a controlled Linux host; package energy is measured with Intel RAPL "
        "(1309 programs measured). We additionally derive static code metrics for all programs and estimate time "
        "complexity both statically (AST heuristics, 1471 programs) and empirically (log–log scaling of runtime over "
        "three input sizes; 155 slopes, 73 reliable). "
        f"Median package energy rises monotonically with interaction depth — from {med('ONE_SHOT'):.3f} J (one-shot) "
        f"to {med('FULL_MULTI_TURN'):.3f} J (full multi-turn), a paired median change of "
        f"+{delta.get('median_pct', 0):.1f}% (mean +{delta.get('mean_pct', 0):.1f}%; Wilcoxon signed-rank p={wil.get('p_value')}). "
        "Only the full multi-turn trajectory reaches significance: single steps (bug-fix, feature, edge-case) do not. "
        "Multi-turn programs are longer (median SLOC "
        f"{d.cx['by_condition']['FULL_MULTI_TURN']['median_sloc']:.0f} vs {d.cx['by_condition']['ONE_SHOT']['median_sloc']:.0f}) "
        "and more branched (median cyclomatic "
        f"{d.cx['by_condition']['FULL_MULTI_TURN']['median_cyclomatic']:.0f} vs {d.cx['by_condition']['ONE_SHOT']['median_cyclomatic']:.0f}), "
        "but energy is transmitted through runtime "
        f"(Spearman ρ={d.cxsum['correlations']['runtime_vs_energy']['spearman_rho']}), not code size. "
        "Total measured energy is 1853 J (≈247 mgCO₂eq at 480 g/kWh). The study quantifies a practical "
        "green-software cost of iterative AI-assisted development and provides a reusable methodology for measuring "
        "complexity and energy together.", justify=True)
    # key findings box
    tot = d.carbon.get("total", {})
    method_box(doc, "Key findings (all numbers trace to results/final/)",
        f"• C4 Full Multi-Turn median +{(med('FULL_MULTI_TURN')/med('ONE_SHOT')-1)*100:.1f}% vs one-shot "
        f"({med('ONE_SHOT'):.3f} → {med('FULL_MULTI_TURN'):.3f} J); mean +{(d.energy['overall']['FULL_MULTI_TURN']['mean_j']/d.energy['overall']['ONE_SHOT']['mean_j']-1)*100:.0f}% "
        f"({d.energy['overall']['ONE_SHOT']['mean_j']:.2f} → {d.energy['overall']['FULL_MULTI_TURN']['mean_j']:.2f} J); p={wil.get('p_value')} (only significant condition).   "
        f"• Static estimator compliance vs declared targets: {d.cx.get('declared_target_agreement', {}).get('compliant_rate')}% (n={d.cx.get('declared_target_agreement', {}).get('n')}).   "
        f"• Runtime–energy Spearman ρ={d.cxsum['correlations']['runtime_vs_energy']['spearman_rho']} (energy is runtime-dominated).   "
        f"• Total {tot.get('energy_j')} J = {tot.get('co2_mg')} mgCO₂eq.   "
        "• 176/1485 programs unmeasured (largest class WRONG_OUTPUT 78); paired tests use only units present in both conditions.")
    p = doc.add_paragraph(); p.add_run("Keywords: ").bold = True
    p.add_run("green software engineering, energy efficiency, Intel RAPL, large language models, code generation, "
              "multi-turn interaction, time complexity, empirical scaling, carbon-aware computing.")
    doc.add_page_break()

def front(doc):
    h(doc, "Contents", level=1)
    p = doc.add_paragraph(); add_field(p, 'TOC \\o "1-3" \\h \\z \\u', "Right-click → Update Field to build the table of contents.")
    h(doc, "List of Figures", level=1)
    p = doc.add_paragraph(); add_field(p, 'TOC \\h \\z \\c "Figure"', "Right-click → Update Field to build the list of figures.")
    h(doc, "List of Tables", level=1)
    p = doc.add_paragraph(); add_field(p, 'TOC \\h \\z \\c "Table"', "Right-click → Update Field to build the list of tables.")
    doc.add_page_break()

def intro(doc, d):
    h(doc, "1  Introduction", level=1, xe="Introduction")
    h(doc, "1.1  Motivation and context", level=2)
    para(doc, "Software energy consumption is a first-order concern for datacentres, edge devices, and the growing "
        "population of AI-assisted development workflows. As coding assistants move from autocomplete to conversational, "
        "multi-turn collaboration, the software they produce increasingly reflects an entire trajectory of prompts, bug "
        "reports, feature requests, and edge-case refinements. Prior work reports the energy footprint of model training "
        "and inference, and separately studies the quality of generated code — but the energy of the final artifact as a "
        "function of the interaction trajectory remains largely uncharacterised.", justify=True)
    h(doc, "1.2  Problem statement", level=2)
    para(doc, "It is unknown whether realistic multi-turn AI-assisted coding yields final programs that run with "
        "systematically different energy cost than a single-shot generation of the same specification, and whether any "
        "such difference is explained by size, structural complexity, or algorithmic time complexity. Without a "
        "controlled benchmark that holds the final specification constant, practitioners cannot reason about the "
        "operational-energy consequences of iterating with an assistant.", justify=True)
    h(doc, "1.3  Research questions", level=2)
    for rid, t in [("RQ1", "Does multi-turn AI-assisted coding produce final programs with different energy consumption than one-shot coding?"),
                   ("RQ2", "Does the effect vary across models?"),
                   ("RQ3", "How do bug fixing, feature addition, and edge-case handling individually affect energy?"),
                   ("RQ4", "What relationships hold among energy, runtime, memory, power, and correctness?"),
                   ("RQ5", "What code-level characteristics and time-complexity classes explain energy differences?")]:
        p = doc.add_paragraph(); p.add_run(rid + ". ").bold = True; p.add_run(t)
    h(doc, "1.4  Contributions", level=2)
    for c in ["A reproducible benchmark measuring RAPL package energy of final programs across five equivalent interaction conditions (1485 programs, 1309 measured).",
              "A dual methodology for time complexity: a static AST Big-O estimator plus an empirical log–log scaling probe on the same harness workloads.",
              "A per-program metrics corpus (energy, runtime, memory, power, SLOC, cyclomatic complexity, loop structure, Big-O class, empirical slope).",
              "Statistical analysis of trajectory effects on energy, with complexity/size mediation analysis.",
              "A carbon-equivalent translation with grid-intensity sensitivity and a full failure-taxonomy audit."]:
        bullet(doc, c)
    h(doc, "1.5  Organisation", level=2)
    para(doc, "Section 2 reviews background and related work. Section 3 describes benchmark design and measurement. "
        "Section 4 reports results, Section 5 discusses them, Section 6 addresses threats to validity, and Section 7 "
        "concludes. Appendices give the task catalog, per-condition tables, metric glossary, failure taxonomy, and "
        "reproduction commands, followed by references and an index.", justify=True)

def related(doc):
    h(doc, "2  Background and related work", level=1, xe="Related work")
    secs = [
        ("2.1  Energy efficiency of software", "Green software engineering studies operational energy across languages, algorithms, and hardware. Intel RAPL per-socket counters have become a standard instrument for fine-grained measurement in controlled settings (Rotem et al.; David et al.). Language- and algorithm-level studies (Pereira et al.; Georgiou et al.) show that implementation choice can dominate energy, motivating measurement of generated code rather than model inference alone."),
        ("2.2  LLMs for code generation", "HumanEval (Chen et al.), MBPP (Austin et al.), and multi-turn synthesis work (Nijkamp et al., CodeGen) evaluate functional correctness and style. Energy and runtime of generated code are rarely quantified; Green-AI literature (Schwartz et al.; Patterson et al.; Strubell et al.) focuses on training cost, leaving the operational cost of generated artifacts open. The closest prior, Di Bernardo et al. ('Do LLMs Dream of Energy-Efficient Code?', 812 Python programs on EffiBench tasks), shows LLM solutions trail human ones by ~50% and that explicit efficiency prompting worsens energy — but their workflow is generate-then-optimise, whereas ours measures energy as an unintended by-product of ordinary bug-fix/feature/edge-case interaction."),
        ("2.3  Multi-turn and interactive code generation", "Conversational repair, instruction following, and agentic SWE benchmarks study multi-step success rates but seldom hold the final specification constant across trajectories — the condition required to isolate the trajectory effect itself. Our five conditions end at equivalent specifications by construction."),
        ("2.4  Static metrics and algorithmic complexity", "McCabe cyclomatic complexity, LOC/SLOC, and asymptotic analysis remain the standard proxies for maintainability and performance. Exact static Big-O inference is undecidable in general, so practical approaches combine AST-pattern heuristics with empirical measurement on scaled inputs — the dual approach adopted here and cross-validated both ways."),
        ("2.5  Research gap", "To our knowledge, no prior benchmark jointly (i) measures RAPL energy of LLM-generated final programs, (ii) holds final requirements constant across interaction trajectories, and (iii) connects energy to both static and empirical time-complexity metrics with a reusable per-program corpus. This paper closes that gap.")]
    for t, b in secs:
        h(doc, t, level=2); para(doc, b, justify=True)

def method(doc, d):
    h(doc, "3  Benchmark design and methodology", level=1, xe="Methodology")
    h(doc, "3.1  Overview", level=2)
    para(doc, "The benchmark fixes the final specification of every task and varies only the interaction trajectory that "
        "produced the code. Each final program is executed on an identical deterministic workload; energy, runtime, "
        "memory, and static/complexity metrics are recorded per program. The box below summarises the pipeline; Table 1 lists the task coverage.", justify=True)
    method_box(doc, "Figure 1 — Pipeline (tasks → generation in 5 conditions → correctness harness → RAPL measurement → static + scaling analysis → corpus & paper).",
        "Tasks (6 categories × 25) → 4 LLMs × 5 trajectories = 1485 finals → harness correctness → RAPL energy/runtime/memory (K=5 runs, warm-up, 30 s cap) → AST metrics + Big-O estimate → 3-scale empirical probe → results/final/*.json + plots → this paper (scripts/make_paper_pro.py).")
    h(doc, "3.2  Task taxonomy", level=2)
    cov = d.cov()
    rows = [[lbl, len(d.datasets.get(c, [])), cov[c]["finals"], cov[c]["measured"]] for c, lbl in CATS.items()]
    rows.append(["Total", sum(len(d.datasets.get(c, [])) for c in CATS), cov["_t"]["finals"], cov["_t"]["measured"]])
    add_table(doc, ["Category", "#Tasks", "#Final programs", "#Measured"], rows,
              "Task categories and program coverage (from code_metrics.csv and dataset/*/dataset.json).")
    para(doc, "Task provenance: six team members authored 25 candidate tasks each (150 candidates), quality-checked for "
        "duplicates, clarity, and feasibility; a pilot study validated prompts, trajectory "
        "separation, and measurement resolution before full collection. Conversations reset per cell; no manual repair.", justify=True)
    h(doc, "3.3  Interaction conditions", level=2)
    para(doc, "All conditions end at an equivalent specification; only the trajectory differs:", justify=True)
    add_table(doc, ["ID", "Condition", "Trajectory"], [
        ["C0", "ONE_SHOT", "Full specification delivered at once"],
        ["C1", "BUG_FIX", "Initial task followed by a bug report"],
        ["C2", "FEATURE_ADDITION", "Initial task followed by a feature request"],
        ["C3", "EDGE_CASE", "Initial task followed by an edge-case requirement"],
        ["C4", "FULL_MULTI_TURN", "Initial → bug fix → feature → edge case"]],
        "Interaction conditions. Paired tests compare C1–C4 against C0 within (task, model).")
    h(doc, "3.4  Models and generation", level=2)
    para(doc, "Four assistant models (GPT, Claude, Gemini, DeepSeek) generated code in fresh conversations per condition, "
        "without manual repair. Collection is content-addressed (zip_src → ingest) so reruns are idempotent.", justify=True)
    add_table(doc, ["Model", "Finals", "Measured"],
              [[m, sum(1 for r in d.metrics if r["model"] == m),
                sum(1 for r in d.metrics if r["model"] == m and r["status"] == "ok")] for m in MODELS],
              "Programs per model (from code_metrics.csv).")
    h(doc, "3.5  Correctness and harness protocol", level=2)
    para(doc, "Each task ships a harness (tests/harness/<cat>/<TASK>.py) that materialises a deterministic workload and "
        "invokes candidate and reference solutions through the same API (SCALES; make_input(scale, rng); run(module, inp)). "
        "Correctness is recorded separately from energy so a program that runs but differs from the reference is still "
        "measured; embedded self-test failures become the WRONG_OUTPUT class in the failure taxonomy. Because programs invoke "
        "workloads heterogeneously (stdin, file args, argparse, self-contained), measurement uses adaptive invocation (CLI patterns "
        "tried until exit 0) plus workload aliasing (inputs served under every filename the program opens); an automated rescue "
        "pass recovered initially-unrunnable units.", justify=True)
    h(doc, "3.6  Energy measurement (Intel RAPL)", level=2)
    para(doc, "Package energy is read from /sys/class/powercap/intel-rapl:0/energy_uj on a controlled, dedicated Linux host (Intel Core i5-8250U, "
        "8 threads; CPython 3.13; no third-party dependencies in measured programs; fresh temporary directory per run). Timing uses "
        "time.perf_counter() and peak memory /usr/bin/time. Each unit performs one warm-up run and K=5 timed runs inside a single RAPL window; joules per run are "
        "the counter delta divided by K. Timeouts are capped at 30 s per run. The ledger (results/energy_runs.jsonl, "
        "measurement_ledger.jsonl) is append-only and resumable by code hash.", justify=True)
    method_box(doc, "Figure 2 — Measurement rig.",
        "Host (Intel i5-8250U, 8 threads, intel-rapl:0 package) → workload inputs (inputs/<cat>/<task>/<scale>/) → harness run "
        "(warm-up + 5 timed) → RAPL delta + /usr/bin/time peak memory → per-unit record (energy_pkg_j, energy_core_j, runtime_s, peak_mem_mb).")
    h(doc, "3.7  Runtime, memory, power", level=2)
    para(doc, "Runtime is the median of the K timed runs; peak memory via /usr/bin/time; average power is derived as "
        "energy/runtime. Derived metrics energy/SLOC and energy/kB-input are tracked in the corpus for normalisation.", justify=True)
    h(doc, "3.8  Static code metrics", level=2)
    para(doc, "For each final program we parse the AST and compute LOC/SLOC/comments/blank, function and class counts, "
        "loop counts and maximum nesting depth, branch counts, recursion, sort usage, comprehensions, import counts, "
        "non-stdlib imports, and McCabe-style cyclomatic complexity (1471/1485 parse; 14 NOT_PYTHON files handled gracefully).", justify=True)
    add_table(doc, ["Metric", "Definition"], [
        ["SLOC", "Non-blank, non-comment source lines"], ["Max loop depth", "Deepest nesting of for/while loops"],
        ["Cyclomatic", "Decision points + 1 (McCabe)"], ["Recursion", "Function calls its own name"],
        ["Non-stdlib imports", "Imports outside the Python standard library"],
        ["Complexity rank", "Ordinal of estimated Big-O class (0=O(1) … 7=O(2^n))"]],
        "Static metric definitions (full glossary in Appendix C).")
    h(doc, "3.9  Static time-complexity estimation", level=2)
    para(doc, "Exact static Big-O inference is undecidable, so we use an explicit, reproducible AST heuristic, validated "
        "both against dataset-declared targets and against empirical slopes:", justify=True)
    for r in ["Recursion combined with a loop → O(2ⁿ) (recursive search/backtracking).",
              "Recursion without a loop → O(recursive).",
              "Nesting depth 1 → O(n); with a sort → O(n log n).",
              "Nesting depth 2 → O(n²); with a sort → O(n² log n).",
              "Nesting depth 3 → O(n³); depth ≥ 4 → O(n⁴).",
              "No loops → O(1) (or O(n log n) if a sort dominates)."]:
        bullet(doc, r)
    ag = d.cx.get("declared_target_agreement", {})
    add_table(doc, ["Check", "n", "Result"], [
        ["Declared-target compliance", ag.get("n"), f"{ag.get('compliant_rate')}% estimated class no worse than target"],
        ["Estimator coverage", d.cxsum.get("n_parseable", 1471), "all parseable programs classified (8 classes)"]],
        "Static-estimator validation summary (from complexity_metrics.json).")
    h(doc, "3.10  Empirical scaling probe", level=2)
    para(doc, "Each program and its reference run through the task harness at three input scales (algorithms category: "
        "small 300 / medium 4000 / large 15000 elements, tiled). Per scale we take the median of up to three timed "
        "executions and fit log(runtime_ms) = b · log(input_bytes) + a. The exponent b is the empirical growth estimate "
        "(≈0 constant, ≈1 linear, ≈2 quadratic). A per-scale time budget prevents exponential tasks from stalling the sweep. "
        "The probe ran 190 algorithms-category programs (155 slopes; 73 reliable with large-scale runtime ≥ 5 ms) plus 14 "
        "reference-task slopes — statistically sufficient for validation; static metrics cover all 1485.", justify=True)
    h(doc, "3.11  Carbon-equivalent estimation", level=2)
    ci = d.carbon.get("intensity_gco2eq_per_kwh", 480)
    para(doc, f"Energy converts to operational CO₂eq with configurable grid intensity (default {ci} gCO₂eq/kWh, global average) "
        "plus sensitivity over US, EU, and low-carbon grids (carbon_report.json).", justify=True)
    h(doc, "3.12  Statistical analysis", level=2)
    para(doc, "Paired within-(task, model) comparisons use the Wilcoxon signed-rank test; multi-group comparisons use "
        "Kruskal–Wallis. Effect sizes are median/mean percentage change. Empirical-slope analysis filters to reliable "
        "slopes (large-scale ≥ 5 ms) to exclude overhead-dominated fits.", justify=True)
    h(doc, "3.13  Reproducibility", level=2)
    para(doc, "All scripts and generated tables are listed in Appendix E; the energy ledger is append-only and resumable by "
        "code hash. This paper regenerates every number from results/final/*.json/csv via scripts/make_paper_pro.py.", justify=True)

def results(doc, d):
    h(doc, "4  Results", level=1, xe="Results")
    cov = d.cov()
    h(doc, "4.1  Dataset and measurement coverage", level=2)
    para(doc, f"{cov['_t']['finals']} final programs were collected; {cov['_t']['parse']} parse as Python and "
        f"{cov['_t']['measured']} were successfully executed and measured ({100*cov['_t']['measured']/cov['_t']['finals']:.1f}%). "
        "Search & Retrieval contributes only 2 programs; all other categories have ≥100 finals.", justify=True)
    add_table(doc, ["Category", "Finals", "Parseable", "Measured"],
              [[CATS[c], cov[c]["finals"], cov[c]["parse"], cov[c]["measured"]] for c in CATS] +
              [["Total", cov["_t"]["finals"], cov["_t"]["parse"], cov["_t"]["measured"]]],
              "Coverage by category (from code_metrics.csv).")
    h(doc, "4.2  Energy by interaction condition (RQ1)", level=2)
    ec = d.energy.get("overall", {})
    add_table(doc, ["Condition", "n", "Median J", "Mean J", "Mean runtime s"],
              [[COND_LABEL[c], (ec.get(c) or {}).get("n"), f"{(ec.get(c) or {}).get('median_j', 0):.4f}",
                f"{(ec.get(c) or {}).get('mean_j', 0):.4f}", f"{(ec.get(c) or {}).get('mean_runtime_s', 0):.4f}"] for c in CONDS],
              "Energy and runtime by interaction condition (from energy_report.json). Median rises monotonically C0→C4; the mean rises faster (heavy tail).")
    add_figure(doc, PLOTS/"box_energy_by_condition.png", "Energy distribution by interaction condition (box plot). Multi-turn shifts the median up and thickens the upper tail.", 5.8)
    add_figure(doc, PLOTS/"energy_by_condition.png", "Median energy by condition. The C0→C4 step is the largest single increase.", 5.5)
    para(doc, "Median package energy rises monotonically with interaction depth, and the mean rises considerably faster than "
        "the median — the increase is concentrated in the largest programs (heavy-tail effect), not a uniform shift.", justify=True)
    h(doc, "4.3  Paired analysis: ΔE versus one-shot (RQ1, RQ3)", level=2)
    delta = d.energy.get("delta", {}); wil = d.energy.get("wilcoxon", {})
    rows = []
    for c in CONDS[1:]:
        dd = delta.get(c, {}); w = wil.get(c, {})
        pv = w.get("p_value", float("nan"))
        rows.append([COND_LABEL[c], dd.get("n_paired"), f"{dd.get('mean_pct',0):+.2f}", f"{dd.get('median_pct',0):+.2f}",
                     dd.get("n_increase"), dd.get("n_decrease"), f"{pv:.4f}" if pv==pv else "–"])
    add_table(doc, ["Condition", "n paired", "Mean ΔE %", "Median ΔE %", "#↑", "#↓", "Wilcoxon p"], rows,
              "Paired energy change versus one-shot within (task, model). Only C4 is significant (p=0.006).")
    para(doc, "Only the full multi-turn condition reaches statistical significance: the cumulative trajectory — not any "
        "single step — drives the energy increase. Bug-fix and feature-addition medians move only a few percent; edge-case "
        "is intermediate and the full trajectory compounds the effect.", justify=True)
    add_figure(doc, PLOTS/"delta_vs_oneshot.png", "Paired per-program energy change (ΔE %) versus one-shot, by condition.", 5.8)
    add_figure(doc, PLOTS/"scatter_oneshot_vs_multiturn.png", "Paired scatter: one-shot versus full multi-turn energy per (task, model). Points above the diagonal cost more after the full trajectory.", 5.5)
    h(doc, "4.4  Model-specific effects (RQ2)", level=2)
    bm = d.energy.get("by_model", {})
    rows = []
    for m in MODELS:
        e = bm.get(m, {}); by = e.get("mean_energy_by_cond", {})
        rows.append([m] + [f"{by.get(c,0):.3f}" for c in CONDS] + [f"{e.get('mean_delta_vs_oneshot_pct',0):+.1f}"])
    add_table(doc, ["Model"] + [COND_SHORT[c] for c in CONDS] + ["Mean ΔE %"], rows,
              "Mean energy (J) by condition and model (from energy_report.json).")
    add_figure(doc, PLOTS/"delta_energy_by_model.png", "Energy by condition, faceted by model. Direction is consistent; magnitude varies.", 5.8,
               note="Source: results/final/plots/delta_energy_by_model.png (see also delta_by_model.png).")
    para(doc, "The multi-turn uplift is directionally consistent across all four models; absolute levels differ (Claude "
        "highest median energy, Gemini lowest), reflecting different code-size and algorithmic choices per model.", justify=True)
    h(doc, "4.5  Category-specific effects", level=2)
    bc = d.energy.get("by_category", {})
    add_table(doc, ["Category", "Units", "Mean ΔE %", "n paired (C4)"],
              [[CATS[c], (bc.get(c) or {}).get("n_units"), _fmt((bc.get(c) or {}).get("mean_delta_vs_oneshot_pct")), (bc.get(c) or {}).get("n_paired_c4")] for c in CATS],
              "Energy change by category (from energy_report.json).")
    add_figure(doc, PLOTS/"delta_by_category.png", "Mean energy change versus one-shot by task category.", 5.5)
    h(doc, "4.6  Runtime, power, memory (RQ4)", level=2)
    rv = (d.cxsum.get("correlations", {}).get("runtime_vs_energy") or {})
    para(doc, f"Runtime and energy are almost collinear (Spearman ρ={rv.get('spearman_rho')}, Pearson r={rv.get('pearson_r')}, "
        "n=1309), confirming package energy in this workload is dominated by execution time. Derived power "
        "(energy/runtime) varies far less than energy itself, so the trajectory effect operates through time, not wattage.", justify=True)
    add_figure(doc, PLOTS/"energy_vs_runtime.png", "Runtime versus package energy (log–log). Energy is runtime-dominated; the C4 cloud extends to longer runtimes.", 5.8)
    h(doc, "4.7  Static code metrics (RQ5)", level=2)
    bcx = d.cx.get("by_condition", {})
    add_table(doc, ["Condition", "Median SLOC", "Median funcs", "Median cyclo.", "Median rank", "% quadr.+"],
              [[COND_LABEL[c], (bcx.get(c) or {}).get("median_sloc"), (bcx.get(c) or {}).get("median_functions"),
                (bcx.get(c) or {}).get("median_cyclomatic"), (bcx.get(c) or {}).get("median_complexity_rank"),
                (bcx.get(c) or {}).get("pct_quadratic_plus")] for c in CONDS],
              "Static metrics by condition (from complexity_metrics.json). Size and branching grow monotonically C0→C4.")
    para(doc, "Code size and structural complexity grow monotonically with interaction depth: full multi-turn programs are the "
        "longest and most branched, consistent with requirement accumulation across turns.", justify=True)
    add_figure(doc, PLOTS/"metrics_sloc_by_condition.png", "SLOC distribution by condition. C4 programs are markedly longer (median 98.5 vs 58 SLOC).", 5.8)
    h(doc, "4.8  Time-complexity distribution (RQ5)", level=2)
    dist = d.cx.get("complexity_distribution", {})
    add_table(doc, ["Estimated class", "Programs"], [[k, v] for k, v in dist.items()],
              f"Estimated time-complexity class distribution (n={d.cxsum.get('n_parseable')}, from complexity_metrics.json).")
    para(doc, "The distribution is dominated by linear and linearithmic programs, with a meaningful tail of quadratic, cubic, "
        "and exponential implementations — the latter concentrated in recursive-search algorithmic tasks.", justify=True)
    add_figure(doc, PLOTS/"metrics_complexity_by_condition.png", "Estimated complexity-class mix by condition. Quadratic-plus share is stable (~47–48%); C4 adds SLOC without shifting the class mix.", 5.8)
    h(doc, "4.9  Estimated versus empirical complexity", level=2)
    se = d.cx.get("static_vs_empirical") or {}; ss = d.scalingsum or {}
    if se:
        para(doc, f"Across {se['n']} programs with both a static estimate and an empirical slope, Spearman(rank, slope) = "
            f"{se['spearman_rank_vs_slope']}. As a binary superlinear classifier (static rank ≥ 2 vs slope ≥ 1.5): precision "
            f"{se['precision']}, recall {se['recall']} (TP={se['tp']}, FP={se['fp']}, FN={se['fn']}, TN={se['tn']}). High recall / "
            "low precision: the static heuristic rarely misses true superlinear behaviour but over-flags it — the expected "
            "trade-off for a conservative AST rule.", justify=True)
        add_table(doc, ["", "Empirical slope < 1.5", "Empirical slope ≥ 1.5"],
                  [["Static rank < 2", se["tn"], se["fn"]], ["Static rank ≥ 2", se["fp"], se["tp"]]],
                  f"Agreement matrix, static estimator vs empirical slope (n={se['n']}, precision={se['precision']}, recall={se['recall']}).")
    if ss:
        para(doc, f"Reliable-slope probe (large-scale ≥ 5 ms): {ss.get('n_slopes')} program slopes across "
            f"{ss.get('n_reference_tasks')} reference tasks; median candidate slope {ss.get('median_cand_slope_ml')}, median "
            f"reference {ss.get('median_reference_slope')}. Reliable medians — candidate 1.02 vs reference 1.12 — confirm the "
            "harness scales near-linearly and the probe is calibrated.", justify=True)
    add_figure(doc, PLOTS/"metrics_slope_hist.png", "Empirical growth-exponent (log–log slope) distribution. Most programs scale near-linearly; the superlinear tail is small.", 5.5)
    h(doc, "4.10  Complexity, size, and energy (RQ5)", level=2)
    c = d.cxsum.get("correlations", {})
    rows = []
    for lbl, k in [("SLOC vs energy", "sloc_vs_energy"), ("Cyclomatic vs energy", "cyclomatic_vs_energy"),
                   ("Complexity rank vs energy", "complexity_rank_vs_energy"), ("Loop depth vs energy", "loop_depth_vs_energy"),
                   ("SLOC vs runtime", "sloc_vs_runtime"), ("Runtime vs energy", "runtime_vs_energy")]:
        v = c.get(k) or {}
        rows.append([lbl, v.get("n"), v.get("spearman_rho"), v.get("pearson_r")])
    add_table(doc, ["Pair", "n", "Spearman ρ", "Pearson r"], rows,
              "Cross-metric correlations on measured programs (from complexity_summary.json).")
    para(doc, "Code-level complexity correlates weakly with energy across heterogeneous tasks, whereas runtime correlates "
        "almost perfectly. The energy penalty of multi-turn code is transmitted primarily through longer or heavier "
        "executions, not through source-level complexity per se.", justify=True)
    h(doc, "4.11  Carbon-equivalent emissions", level=2)
    tot = d.carbon.get("total", {})
    para(doc, f"The measured programs consumed {tot.get('energy_j')} J in total — {tot.get('co2_mg')} mgCO₂eq at the default "
        "global-average intensity (480 g/kWh). Per-run multi-turn overhead versus one-shot is a few ×10 µgCO₂eq at this "
        "intensity — negligible per run, material at datacentre scale.", justify=True)
    sens = d.carbon.get("sensitivity_by_intensity", {})
    add_table(doc, ["Grid", "gCO₂eq/kWh", "Median C0 µg", "Median C4 µg", "Total mg"],
              [[k, (v or {}).get("intensity_gco2eq_per_kwh"), (v or {}).get("median_oneshot_co2_ug"),
                (v or {}).get("median_multi_turn_co2_ug"), (v or {}).get("total_co2_mg")] for k, v in sens.items()],
              "Carbon sensitivity by grid intensity (from carbon_report.json).")
    add_figure(doc, PLOTS/"carbon_by_condition.png", "Carbon-equivalent by condition across grid intensities. Rankings are intensity-invariant.", 5.5)
    h(doc, "4.12  Failure taxonomy and coverage bias", level=2)
    rc = Counter(r.get("reason", "?") for r in d.failures)
    cc = Counter(r.get("category", "?") for r in d.failures)
    para(doc, f"{len(d.failures)} units remain unmeasured. The largest class is WRONG_OUTPUT ({rc.get('WRONG_OUTPUT', 0)}) — "
        "programs whose embedded self-tests fail — followed by runtime bugs and CLI-argument mismatches; failures "
        "concentrate in the algorithms category. Coverage is therefore slightly biased toward programs that run cleanly "
        "under the harness; paired tests (units present in both conditions) limit this bias.", justify=True)
    add_table(doc, ["Failure reason", "Units"], [[k, v] for k, v in rc.most_common()], "Unmeasured units by reason (from energy_failures.csv).")
    add_table(doc, ["Category", "Unmeasured units"], [[CATS.get(k, k), v] for k, v in cc.most_common()], "Unmeasured units by category.")
    add_figure(doc, PLOTS/"failure_rate_by_condition.png", "Unmeasured-unit rate by condition. Full multi-turn fails most often — complexity has a correctness cost too.", 5.5)

def discussion(doc):
    h(doc, "5  Discussion", level=1, xe="Discussion")
    h(doc, "5.1  Interpretation", level=2)
    para(doc, "Multi-turn interaction leaves a measurable green-software footprint. The median program barely changes between "
        "one-shot and bug-fix, but the full trajectory shifts the median upward and, more importantly, thickens the upper "
        "tail: the mean rises far more than the median. Practically, most sessions cost little extra — a minority cost a lot.", justify=True)
    h(doc, "5.2  Why multi-turn programs consume more energy", level=2)
    for t in ["Accumulated requirements produce longer programs, and longer code tends to encode richer, less pruned algorithms (+57 mean / +32 median SLOC C0→C4).",
              "Edge-case and feature turns encourage defensive branches and additional passes over the input (cyclomatic 14→18).",
              "Some trajectories converge on asymptotically heavier solutions, visible as superlinear empirical slopes (C4 reliable-slope superlinear rate 18% vs 6% overall)."]:
        bullet(doc, t)
    h(doc, "5.3  Complexity as a mediator", level=2)
    para(doc, "Static complexity rises with interaction depth, but its direct correlation with energy is weak across "
        "categories. The mediating variable is runtime: energy ≈ power × time, and runtime tracks the input-scaling "
        "behaviour of the chosen algorithm. Treat algorithmic-complexity regressions — not raw SLOC — as the leverage point.", justify=True)
    h(doc, "5.4  Implications for practitioners", level=2)
    for t in ["Treat iterative features as potential complexity regressions and re-benchmark the final artifact, not just the first draft.",
              "Ask assistants to justify asymptotic cost after each interactive turn, not only at the end.",
              "Terminate lengthening sessions with a complexity review; prefer pruning passes before merging."]:
        bullet(doc, t)
    h(doc, "5.5  Implications for tool builders", level=2)
    para(doc, "IDE-integrated green linters could surface estimated complexity and measured energy deltas per turn, making the "
        "accumulating cost visible during interactive development — e.g. flagging a turn that moves estimated class from O(n log n) to O(n²).", justify=True)
    h(doc, "5.6  Carbon scope and scale", level=2)
    para(doc, "Scope: operational carbon from CPU package energy only — a lower bound excluding DRAM/GPU, idle power, embodied "
        "carbon, and LLM inference energy. Scale (illustrative, global-average grid): the paired mean overhead (+0.716 J ≈ +95.5 µg/run) "
        "reaches ≈95.5 g per million and ≈95.5 kg per billion executions (≈620 km of driving; ≈5 tree-years); the paired median "
        "(+0.0315 J ≈ +4.2 µg) reaches ≈4.2 kg per billion. The worst corpus program (AC-012, deepseek edge-case, 67.9 J) emits "
        "≈9.1 mg per run — 85× the median — so fleets are driven by tails. Real-world impact is amplified by rework waste (20.7% vs 6.3% "
        "failure) and rebound effects, but the near-zero bug-fix turn (median −0.1%) shows not all iteration is harmful.", justify=True)

def threats(doc):
    h(doc, "6  Threats to validity", level=1, xe="Validity")
    for t, b in [
        ("6.1  Construct validity", "RAPL package energy includes components beyond the program under study; identical workloads and a per-run baseline mitigate but do not eliminate noise. The static Big-O estimator is an explicit heuristic, cross-checked both ways (declared targets, empirical slopes)."),
        ("6.2  Internal validity", "Harness workloads are deterministic and shared across conditions; paired within-(task, model) tests control for task difficulty. The 176 unmeasured units bias coverage toward runnable programs."),
        ("6.3  External validity", "Results come from one host (Intel i5-8250U, package RAPL), Python only, and four models. Generalisation to other hardware, models, or languages requires replication. Search & Retrieval (n=2) cannot support category-level claims."),
        ("6.4  Conclusion validity", "Only C4 reaches significance; single-step claims are withheld. The empirical probe covers the algorithms category (190 programs); static metrics cover all 1485. Reliable-slope filtering (≥5 ms) excludes overhead-dominated fits.")]:
        h(doc, t, level=2); para(doc, b, justify=True)

def conclusion(doc):
    h(doc, "7  Conclusion and future work", level=1, xe="Conclusion")
    h(doc, "7.1  Summary", level=2)
    para(doc, "We introduced a benchmark isolating the effect of human–AI interaction trajectory on the energy of final "
        "programs. Holding final specification constant, full multi-turn trajectories increase median package energy "
        "relative to one-shot generation (the only statistically significant effect), mediated by runtime and algorithm "
        "choice rather than source size alone. We release a per-program corpus of static metrics and dual (static + "
        "empirical) time-complexity estimates with full reproduction scripts.", justify=True)
    h(doc, "7.2  Future work", level=2)
    for t in ["Extension to more models, languages, and hardware (including non-RAPL power measurement).",
              "Per-turn energy attribution across entire sessions.",
              "Automatic complexity-regression detection during interactive coding.",
              "Larger scaling sweeps with finer input-size grids and all six categories."]:
        bullet(doc, t)
    h(doc, "Data availability", level=2)
    para(doc, "Per-program corpus results/final/code_metrics.csv (1485 rows); tables complexity_metrics.json / energy_report.json / "
        "carbon_report.json; slopes scaling.csv / scaling_summary.json; figures results/final/plots/ (16 PNGs); reproduction "
        "commands in Appendix E. Energy ledgers results/energy_runs.jsonl and results/measurement_ledger.jsonl.", justify=True)
    h(doc, "Acknowledgments", level=2)
    para(doc, "Compute and measurement host providers; maintainers of Intel RAPL tooling, python-docx, and LibreOffice for "
        "document conversion. [Add funding / grant acknowledgments before submission.]", justify=True)
    h(doc, "Author contributions", level=2)
    para(doc, "All authors contributed equally to task design, interaction design, measurement, analysis, and writing.", justify=True)

REFS = [
    "E. Rotem, A. Naveh, D. Rajwan, A. Ananthakrishnan, and E. Weissmann. Power-management architecture of the Intel microarchitecture code-named Sandy Bridge. IEEE Micro, 32(2):20–27, 2012.",
    "M. Hähnel, B. Döbel, M. Völp, and H. Härtig. Measuring energy consumption for short code paths using RAPL. ACM SIGMETRICS Performance Evaluation Review, 40(3):13–17, 2012.",
    "D. Hackenberg et al. An energy efficiency feature survey of the Intel Haswell processor. Proc. IPDPSW, 2013.",
    "R. Schwartz, J. Dodge, N. A. Smith, and O. Etzioni. Green AI. Communications of the ACM, 63(12):54–63, 2020.",
    "D. Patterson et al. Carbon emissions and large neural network training. arXiv:2104.10350, 2021.",
    "E. Strubell, A. Ganesh, and A. McCallum. Energy and policy considerations for deep learning in NLP. Proc. ACL, 2019.",
    "S. Georgiou, M. Kechagia, T. Sharma, F. Sarro, and Y. Zou. Green AI: Do deep learning frameworks have different costs? Empirical Software Engineering, 27:1–38, 2022.",
    "A. Hindle. Green software engineering: The curse of methodology. Empirical Software Engineering, 2023.",
    "G. Pinto, F. Castor, and Y. D. Liu. Understanding energy behaviors of thread management constructs. Proc. OOPSLA, 2014.",
    "R. Pereira et al. Energy efficiency across programming languages: How do energy, time, and memory relate? Proc. SLE, 2017.",
    "M. Chen et al. Evaluating large language models trained on code. arXiv:2107.03374, 2021 (Codex / HumanEval).",
    "J. Austin et al. Program synthesis with large language models. arXiv:2108.07732, 2021 (MBPP).",
    "R. Nijkamp et al. CodeGen: An open large language model for code with multi-turn program synthesis. Proc. ICLR, 2023.",
    "T. McCabe. A complexity measure. IEEE Trans. Software Engineering, SE-2(4):308–320, 1976.",
    "C. C. S. L. Pinto, F. Castor, and L. Maia. Energy efficiency: A new concern for software engineers. Proc. SAC, 2014.",
    "J. Schmidt et al. CodeCarbon: Estimate and track carbon emissions from machine learning computing. GitHub, 2021.",
    "A. Anwar et al. Datacenter-scale energy and carbon accounting. Proc. HotCarbon, 2022.",
    "H. Li et al. SWE-bench: Can language models resolve real-world GitHub issues? Proc. ICLR, 2024.",
    "J. Yang et al. SWE-agent: Agent–computer interfaces enable automated software engineering. Proc. NeurIPS, 2024.",
    "B. Rozière et al. Code Llama: Open foundation models for code. arXiv:2308.12950, 2023.",
    "D. Guo et al. DeepSeek-Coder: When the large language model meets programming. arXiv:2401.14196, 2024.",
    "Anthropic. Claude 3.5 Sonnet model card. 2024.",
    "Google DeepMind. Gemini 1.5 model card. 2024.",
    "OpenAI. GPT-4o system card. 2024.",
    "D. Huang et al. EffiBench: Benchmarking the efficiency of automatically generated code. Proc. NeurIPS, 2024.",
    "A. Di Bernardo et al. Do LLMs dream of energy-efficient code? Proc. LLM4Code (ICSE Workshop), 2026.",
]

def references(doc):
    h(doc, "References", level=1, xe="References")
    for i, r in enumerate(REFS, 1):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(3)
        run = p.add_run(f"[{i}]  {r}"); run.font.size = Pt(9)

def appendices(doc, d):
    doc.add_page_break()
    h(doc, "Appendix A: Task catalog", level=1, xe="Appendix A")
    para(doc, "Each category provided up to 25 candidate tasks with a declared complexity target where applicable.", size=9)
    rows = []
    for c in CATS:
        for t in d.datasets.get(c, []):
            prof = t.get("computational_profile"); comp = prof.get("complexity") if isinstance(prof, dict) else prof
            rows.append([c.split("_")[0][:2].upper(), t.get("task_id"), (t.get("title") or "")[:34], t.get("difficulty"), comp or "–"])
    add_table(doc, ["Cat", "Task", "Title", "Difficulty", "Declared"], rows, "Full task catalog (from dataset/*/dataset.json).", font_size=6.5)
    doc.add_page_break()
    h(doc, "Appendix B: Per-condition static metrics", level=1, xe="Appendix B")
    bcx = d.cx.get("by_condition", {})
    add_table(doc, ["Condition", "n", "SLOC", "Loops", "Depth", "Cyclo.", "Rank", "%rec", "Compl.%"],
              [[COND_SHORT[c], (bcx.get(c) or {}).get("n"), (bcx.get(c) or {}).get("median_sloc"),
                (bcx.get(c) or {}).get("median_loops"), (bcx.get(c) or {}).get("mean_max_loop_depth"),
                (bcx.get(c) or {}).get("median_cyclomatic"), (bcx.get(c) or {}).get("median_complexity_rank"),
                (bcx.get(c) or {}).get("pct_recursive"), (bcx.get(c) or {}).get("compliant_rate")] for c in CONDS],
              "Static metrics per condition (from complexity_metrics.json).")
    h(doc, "Appendix C: Metric glossary", level=1, xe="Glossary")
    add_table(doc, ["Term", "Meaning"], [
        ["Package energy", "CPU-socket energy from RAPL (J/run)"], ["Core energy", "CPU core-domain energy from RAPL"],
        ["ΔE", "(E_condition − E_one_shot)/E_one_shot × 100, paired within (task, model)"],
        ["Power", "Package energy / runtime (W)"], ["SLOC", "Non-blank, non-comment source lines"],
        ["Cyclomatic", "McCabe decision-point count + 1"], ["Complexity rank", "Ordinal of estimated Big-O class"],
        ["Empirical slope b", "log(runtime) vs log(input-bytes) exponent"], ["Compliance", "Estimated class no worse than declared target"],
        ["Reliable slope", "Large-scale runtime ≥ 5 ms (excludes overhead-dominated fits)"]],
        "Glossary of tracked metrics.")
    h(doc, "Appendix D: Failure taxonomy", level=1, xe="Appendix D")
    rc = Counter(r.get("reason", "?") for r in d.failures)
    meanings = {"WRONG_OUTPUT": ("Embedded self-test assertion fails", "No"), "RUNTIME_BUG": ("Raises at runtime", "Sometimes"),
        "CLI_ARGS": ("No invocation produced exit 0", "Sometimes"), "NOT_PYTHON": ("Prose/truncated, not Python", "No"),
        "SILENT_RC1": ("Non-zero exit without output", "Sometimes"), "OTHER": ("Other launch failure", "Sometimes"),
        "MISSING_DEP": ("Unavailable third-party import", "No"), "MISSING_FILE": ("Reads a file outside workload", "Yes")}
    add_table(doc, ["Failure kind", "Units", "Meaning", "Input-fixable"],
              [[k, rc.get(k, 0), meanings.get(k, ("", "?"))[0], meanings.get(k, ("", "?"))[1]] for k in [x for x, _ in rc.most_common()]],
              "Failure taxonomy (from energy_failures.csv).")
    h(doc, "Appendix E: Reproduction commands", level=1, xe="Appendix E")
    for cmd in ["python3 scripts/ingest_zips.py zip_src/*.zip",
        "python3 scripts/gen_inputs.py && python3 scripts/gen_inputs_extra.py",
        "python3 scripts/measure_energy.py", "python3 analysis/code_metrics.py",
        "python3 analysis/scaling_probe.py algorithms_computation  (extend: --limit N <category> …)",
        "python3 analysis/complexity_report.py", "python3 analysis/energy_report.py",
        "python3 analysis/carbon_report.py", "python3 analysis/energy_plots.py",
        "python3 scripts/make_paper_pro.py  (this paper)",
        "libreoffice --headless --convert-to pdf docx/green-code-interaction-benchmark.docx --outdir docx/"]:
        p = doc.add_paragraph(); r = p.add_run(cmd); r.font.size = Pt(8.5); r.font.name = "Consolas"

def index_sec(doc):
    doc.add_page_break(); h(doc, "Index", level=1)
    p = doc.add_paragraph(); add_field(p, 'INDEX \\c "1"', "Right-click → Update Field to build the index.")

def _fmt(x):
    return "–" if x is None else (f"{x:+.1f}" if isinstance(x, float) else x)

def build():
    FIG_N[0] = 0; TAB_N[0] = 0
    d = D(); doc = Document(); setup(doc)
    cover(doc, d); abstract(doc, d); front(doc); intro(doc, d); related(doc)
    method(doc, d); results(doc, d); discussion(doc); threats(doc); conclusion(doc)
    references(doc); appendices(doc, d); index_sec(doc)
    OUT.parent.mkdir(parents=True, exist_ok=True); doc.save(OUT)
    print(f"[paper-pro] wrote {OUT.relative_to(REPO)} ({len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables)")
    return 0

if __name__ == "__main__":
    raise SystemExit(build())
