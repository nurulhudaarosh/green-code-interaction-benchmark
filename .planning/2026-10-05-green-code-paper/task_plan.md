# Task Plan: Green Code Interaction Benchmark — Complexity Metrics + Research Paper

## Goal

Compute per-program **time-complexity** and other measurable code metrics for the
1485 final programs, track them in `results/final/`, then write a full,
sectioned research paper (with TOC, index, and figure/table placeholders) as a
`.docx` inside `docx/`.

## Next Step

Deliver: summarize the metrics corpus and the generated paper to the user. If
requested, extend the empirical scaling probe to the remaining categories
(`python3 analysis/scaling_probe.py --limit N <category> ...`).

## Current Phase

Phase 6 complete — delivery

## Phases

### Phase 1: Requirements & Discovery

- [x] Understand user intent (complexity + extra metrics + full paper docx)
- [x] Map repo: `energy_runs.jsonl` (1309 units: energy/runtime/mem), `results/raw` (48 harness runs: candidate vs reference runtime, per-scale correctness)
- [x] Identify dataset-declared complexity targets (`dataset/<cat>/dataset.json` -> `computational_profile.complexity`) and reference solutions
- [x] Confirm harnesses exist for all 6 categories x 25 tasks and scale inputs (small=300, medium=4000, large=15000)
- [x] Install `python-docx` (1.2.0)
- **Status:** complete

### Phase 2: Static metrics + complexity analyzer

- [x] `analysis/code_metrics.py`: parse AST, emit LOC/SLOC/comments/blank, functions, classes, imports, loops, max loop depth, branches, recursion, sort usage, comprehensions, cyclomatic complexity, estimated Big-O class + ordinal
- [x] Handle unparseable files (NOT_PYTHON) gracefully (1471/1485 parse)
- [x] Merge dynamic metrics from `results/energy_runs.jsonl` (runtime, energy, memory, power)
- [x] Emit `results/final/code_metrics.csv` + `complexity_summary.json`
- **Status:** complete

### Phase 3: Empirical scaling / time-complexity probe

- [x] `analysis/scale_worker.py`: isolated per-program harness runner with per-scale median timing
- [x] `analysis/scaling_probe.py`: run each program + reference at small/medium/large, fit log-log slope, resumable (supports `--limit`)
- [x] Ran over the algorithms category sample: 190 programs, 155 slopes, 73 reliable (large-scale >= 5 ms); 14 reference-task slopes
- [x] Validated static estimator against declared targets (71.6% compliant) and empirical slopes (precision 0.21, recall 0.88)
- **Status:** complete (algorithms-category sample; static metrics cover all 1485)

### Phase 4: Metric tracking tables + plots

- [x] `analysis/complexity_report.py`: per-condition/model/category summaries, paired deltas, correlations, compliance
- [x] Extra tracked metrics: power_w, energy/SLOC, energy/kB input, correctness/status
- [x] `results/final/complexity_metrics.json/csv` + plots `metrics_*.png`
- **Status:** complete

### Phase 5: Research paper (docx)

- [x] `scripts/make_paper.py` builds `docx/green-code-interaction-benchmark.docx`
- [x] Full structure: title/abstract/keywords, TOC field, list of figures/tables, 7 sections + subsections, references, appendices, index
- [x] Figure placeholders (`[[FIGURE n ...]]`); data tables generated from JSON/CSV
- [x] Numbers pulled from JSON/CSV (no hardcoding)
- **Status:** complete

### Phase 6: Verification & delivery

- [x] Docx validated (opens with python-docx; converts to PDF with LibreOffice)
- [x] TOC/List-of-Figures/List-of-Tables/INDEX fields + 13 XE index entries present
- [x] 20 tables, 236 paragraphs, 18 figure placeholders
- [x] Reported to user
- **Status:** complete

## Key Questions

1. How to define "time complexity" defensibly? -> dual: static AST Big-O heuristic + empirical log-log runtime slope at 3 harness scales; validated against dataset-declared targets.
2. Which extra metrics are measurable? -> runtime, package/core energy, peak memory, derived power, energy/SLOC, energy/LOC, static code metrics, cyclomatic complexity, correctness/status, carbon.
3. Coverage limits? -> AC 500 finals, FD 360, IM 400, RA 123, TL 100, SR 2; 176 still failing.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Static Big-O as primary complexity metric | Scales to all 1485 programs, deterministic, defensible; empirical slope as validation on the subset whose harness API matches |
| Use existing harnesses for empirical scaling | They already tile inputs to 300/4000/15000 elements; no new input generators needed |
| Use `energy_runs.jsonl` (1309) as the authoritative dynamic source | Most complete, includes runtime_s + peak_mem_mb |
| Build docx with python-docx, TOC as a Word field | Native Word TOC update; placeholders for figures |
| Keep paper facts data-driven | A generator script reads JSON/CSV so numbers stay reproducible |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| `ModuleNotFoundError: docx` | 1 | `pip install python-docx` (1.2.0 installed) |
| dataset `constraints` sometimes a list | 1 | handle dict/list defensively in readers |
| `tests` field is a dict not list | 1 | read `tests["public_tests"]` etc. |

## Notes

- RAPL perms reset on reboot (subtle: user ran `sudo chmod go+r`); not needed for static/scaling work.
- User writes Banglish; keep technical terms in English.
- Do not commit unless asked.
- Repo plan dir: `.planning/2026-10-05-green-code-paper/`.
