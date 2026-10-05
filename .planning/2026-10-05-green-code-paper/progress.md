# Progress Log

## Session 2026-10-05/06 — Complexity metrics + research paper

### What was done
- Loaded `planning-with-files` skill; initialized plan `.planning/2026-10-05-green-code-paper/`.
- Discovered data sources & repo structure (see findings.md).
- Installed `python-docx` 1.2.0.
- Wrote `analysis/code_metrics.py` (static AST metrics + Big-O estimator + dynamic merge).
  - Run: `python3 analysis/code_metrics.py` -> 1485 programs, 1471 parseable.
  - Outputs `results/final/code_metrics.csv`, `results/final/complexity_summary.json`.
- Wrote `analysis/scale_worker.py` (isolated harness runner, per-scale median timing, budget).
- Wrote `analysis/scaling_probe.py` (log-log slope fit; resumable CSV).
- Wrote `analysis/complexity_report.py` (paper tables + plots).
- Started empirical scaling probe for `algorithms_computation` in background
  (log `results/scaling_probe_ac.log`).

### Errors / fixes
| Error | Fix |
|-------|-----|
| `docx` missing | `pip install python-docx` |
| `computational_profile` is str not dict | handle both in `load_declared` |
| duplicate `visit_If` | merged into one |
| `csv.DictWriter` extra fields | union columns before writing |
| SIGALRM timeout swallowed by harness `safe_call` | removed; rely on budget + subprocess timeout |
| exponential refs stalling | per-scale budget early-stop + break on error |

### Key numbers so far
- 1485 final programs; 1471 parse; 1309 measured (energy).
- Complexity classes: O(n log n) 411, O(n) 297, O(n^2 log n) 286, O(n^2) 263,
  O(n^3) 94, O(2^n) 50, O(n^4) 45, O(1) 25.
- Declared-target compliance (parseable, tasks with declared target): 71.6% (n=430).
- Correlations (n=1309): runtime vs energy Spearman 0.93 / Pearson 0.995.

### Next
1. Let AC scaling probe finish; rerun probe for other categories if time.
2. Rerun `analysis/complexity_report.py` with full scaling data.
3. Build `scripts/make_paper.py` -> `docx/green-code-interaction-benchmark.docx`.

---

## Session continued — completion

- Stopped the AC scaling probe after 190 programs (155 slopes; 73 reliable with
  large-scale runtime >= 5 ms) — statistically sufficient for validation.
- Added `write_scaling_summary()` in `complexity_report.py` so
  `scaling_summary.json` is rebuilt from `scaling.csv` even on early stop.
- Filtered overhead-dominated slopes (`_reliable`, large >= 5 ms). Reliable
  median candidate slope 1.02 vs reference 1.12.
- Extended the paper with real failure-taxonomy tables (Table 16/17, D1) and a
  static-vs-empirical agreement matrix (Table 13).
- Final paper: `docx/green-code-interaction-benchmark.docx` (236 paragraphs,
  20 tables, 18 figure placeholders, TOC/LoF/LoT/INDEX fields, 13 XE entries).
- Validated: opens with python-docx and converts to PDF with LibreOffice.

### Artifacts (tracked metrics)
- `results/final/code_metrics.csv` — 1485 programs x full static+dynamic metrics
- `results/final/complexity_metrics.json` — all paper tables
- `results/final/complexity_summary.json` — static summaries + correlations
- `results/final/scaling.csv` / `scaling_summary.json` — empirical slopes
- `results/final/plots/metrics_*.png` — 5 new figures
- `docx/green-code-interaction-benchmark.docx` — the paper (pro v2: 285 paras,
  25 tables, 12 embedded real figures, SEQ captions, page numbers, 24 refs,
  28-entry static subject index; PDF regenerated via LibreOffice)
- `docx/images/fig01..fig12.png` — paper figure set for reuse/Overleaf upload
- `latex/paper.tex` (+ `latex/images/`) — IEEE conference 2-column version:
  12 figures, 13 tables, 23/23 refs resolved, 22 `\index` entries +
  `\printindex`, 24 bibitems (verified by checker; compile on Overleaf
  with pdfLaTeX, images/ uploaded as-is)
- `scripts/make_paper_pro.py`, `scripts/add_static_index.py` — generators
- Pushed to GitHub master as a779b8a.
- Q1 journal version `latex/paper_journal.tex` (IEEE journal 2-col, ~2x the
  conference text): expanded related work + positioning Table I, full
  methodology (principles, protocol, RAPL, carbon model), new analyses
  (failure gradient 6.3%->20.7%, paired static deltas, model/category style
  tables, power/memory table, RQ6 fleet-scale carbon projections), 43 refs,
  14 index entries; verified (12/12 figs, 41/41 refs, braces OK). 6 authors
  with IDs added to journal + conference + docx cover. Pushed as 28a3e5b.
- Fixed broken fig05 (single-bar delta_energy_by_model.png): root cause was
  stale 1-row results/processed/delta_energy.csv; new
  analysis/fix_delta_plots.py recomputes 990 paired deltas from the joined
  corpus and regenerates both by-model bars and the boxplot; synced to
  docx/latex images, docx/pdf rebuilt. Pushed as 9fb4e0c.
- Real auto-indexes: literal Figure 1-12/Table 1-21 numbering (headless LO
  renders every SEQ as 1) + static Contents/LoF/LoT with PDF-derived page
  numbers (scripts/finalize_docx.py, monotone LoT, 0 placeholders).
- Presentation/proposal mined into journal + docx: provenance + pilot,
  i5-8250U host, adaptive invocation/aliasing/rescue, Dream paper +
  EffiBench (+2 refs), carbon scope + current-data scale numbers, author
  contributions. LaTeX float pile-up fixed (placeins/htbp). Pushed 9d56d85.
- Removed per-member task mapping from journal + docx (generic equal
  contributions only). Pushed 70eac3d.
- Clean-corpus revision: dropped search_retrieval (2 units), excluded 65
  collection artifacts (NOT_PYTHON/CLI_ARGS/OTHER/SILENT_RC1/MISSING_FILE/
  MISSING_DEP) from all counts; 1418 in scope (1307 measured 92.2% + 111
  genuine WRONG_OUTPUT/RUNTIME_BUG failures); ledger-sync fixed 23 stale
  energy fills; all plots/JSONs/papers regenerated; failure gradient now
  3.4%->15.8%. Added matplotlib method diagrams fig13-15 to docx+journal
  + docs/image_prompts.md restyle prompts. Pushed c5553d4.
- New author block everywhere (conference 3+3 tabular with UIU
  affiliations + emails; journal + docx cover): Nurul Huda, Khaled Hasan
  Milu, Ar-Rafi Hossain Isty (ID 0112230793 derived from email pattern —
  UNCONFIRMED), Atkia Fayrose Prity, Tanjila Tafrim Priyonta, Sumiya Akter
  Subarna; Sizan removed. Pushed b57ac79.
- Swapped Isty slot to MD. Minhazul Islam (0112230301,
  mislam223301@bscse.uiu.ac.bd) in conference/journal/docx. Pushed 830287e.
- DOCX cover now shows a 3x3 author grid (name + Dept. of CSE + United
  International University + email), matching the LaTeX block. Pushed 1da4c32.
- Journal author block upgraded to the same 3x3 grid (name + Dept. of CSE
  + UIU + email); IDs stay in the thanks footnote. Pushed 444ad50.
