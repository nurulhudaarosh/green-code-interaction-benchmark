#!/usr/bin/env python3
"""Append a static (pre-built) subject index to the docx paper's Index section.

Word/LibreOffice INDEX fields only populate inside Word. This script adds a
real, readable subject index (term -> section references) so the document is
complete even before fields are updated. Idempotent: skips if already present.
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt

REPO = Path(__file__).resolve().parent.parent
DOCX = REPO / "docx" / "green-code-interaction-benchmark.docx"
MARKER = "Static subject index (generated; see scripts/add_static_index.py)"

ENTRIES = [
    ("Bug-fix condition (C1)", "§3.3, §4.3"),
    ("Carbon-equivalent emissions", "§3.11, §4.11"),
    ("Code metrics corpus (code_metrics.csv)", "§3.8, §4.1, App. B–C"),
    ("Complexity rank", "§3.8–3.9, §4.10, App. C"),
    ("Cyclomatic complexity", "§3.8, §4.7, §4.10"),
    ("Dataset coverage (1485 finals, 1309 measured)", "§4.1"),
    ("Edge-case condition (C3)", "§3.3, §4.3"),
    ("Empirical scaling probe (log–log slope b)", "§3.10, §4.9"),
    ("Energy measurement, Intel RAPL", "§3.6, §4.2"),
    ("Failure taxonomy (WRONG_OUTPUT, RUNTIME_BUG, …)", "§4.12, App. D"),
    ("Feature-addition condition (C2)", "§3.3, §4.3"),
    ("Full multi-turn condition (C4)", "§3.3, §4.2–4.5"),
    ("Harness protocol (correctness vs energy)", "§3.5"),
    ("Heavy-tail effect (mean vs median)", "§4.2–4.3, §5.1"),
    ("Interaction trajectory", "§1–§5"),
    ("Log–log slope, reliable (≥ 5 ms)", "§3.10, §3.12, §4.9, App. C"),
    ("Models (GPT, Claude, Gemini, DeepSeek)", "§3.4, §4.4"),
    ("One-shot condition (C0)", "§3.3, §4.2–4.3"),
    ("Package energy", "§3.6, App. C"),
    ("Paired analysis (ΔE), Wilcoxon signed-rank", "§3.12, §4.3"),
    ("Power (energy/runtime)", "§3.7, §4.6"),
    ("Reproduction commands", "App. E"),
    ("Runtime vs energy (Spearman ρ = 0.93)", "§4.6, §4.10"),
    ("SLOC (source lines of code)", "§3.8, §4.7, §4.10"),
    ("Static Big-O estimator (AST heuristic)", "§3.9, §4.8–4.9"),
    ("Task taxonomy (6 categories × 25 tasks)", "§3.2, App. A"),
    ("Threats to validity", "§6"),
    ("Time complexity, static vs empirical", "§3.9–3.10, §4.8–4.9"),
]


def main():
    doc = Document(DOCX)
    if any(MARKER in p.text for p in doc.paragraphs):
        print("[index] static index already present, skipping")
        return 0
    # find Index heading (last occurrence)
    idx = max(i for i, p in enumerate(doc.paragraphs)
              if p.style.name.startswith("Heading") and p.text.strip() == "Index")
    # insert after the INDEX-field paragraph that follows the heading
    body = doc.paragraphs[idx]._p
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def insert_after(ref, text, bold=False, size=None, italic=False):
        p_el = OxmlElement("w:p")
        r_el = OxmlElement("w:r")
        t_el = OxmlElement("w:t")
        t_el.set(qn("xml:space"), "preserve")
        t_el.text = text
        rPr = OxmlElement("w:rPr")
        if bold:
            b = OxmlElement("w:b"); rPr.append(b)
        if italic:
            it = OxmlElement("w:i"); rPr.append(it)
        if size is not None:
            sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2)))
            rPr.append(sz)
        r_el.append(rPr); r_el.append(t_el); p_el.append(r_el)
        ref.addnext(p_el)
        return p_el

    ref = body
    # add in reverse so final order is correct
    for term, loc in reversed(ENTRIES):
        ref = insert_after(body, f"{term} — {loc}", size=9.5)
    insert_after(body, MARKER, italic=True, size=8.5)
    doc.save(DOCX)
    print(f"[index] added {len(ENTRIES)} static entries to Index section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
