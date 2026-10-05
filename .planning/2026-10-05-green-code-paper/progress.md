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
