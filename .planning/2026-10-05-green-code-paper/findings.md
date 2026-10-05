# Findings

## Data sources (authoritative)
| File | Contents |
|------|----------|
| `results/energy_runs.jsonl` | 1309 ok units: `energy_pkg_j`, `energy_core_j`, `runtime_s`, `peak_mem_mb`, `invocation`, `sha256`, status |
| `results/measurement_ledger.jsonl` | 48 harness-measured units with `candidate_runtime_ms`, `reference_runtime_ms`, per-scale correctness |
| `results/raw/<cat>/<unit>.json` | rich harness metrics (energy_j, runtime_ms, peak_memory_mb, cpu_percent_avg) for 48 units |
| `dataset/<cat>/dataset.json` | 25 candidate tasks/category: `computational_profile.complexity` (declared Big-O), `reference_solution.code`, `tests.public_tests` |
| `tests/harness/<cat>/<TASK>.py` | `SCALES`, `make_input(scale,rng)`, `run(module,inp)`; AC scales small=300, medium=4000, large=15000 (tiled) |
| `inputs/<cat>/<task>/<scale>/` | materialized workload (JSON/CSV/`input.txt`), deterministic |
| `results/final/energy_report.json` | per-condition energy/runtime medians + Wilcoxon |
| `results/final/carbon_report.json` | CO2eq per condition, intensity sensitivity |
| `results/final/energy_failures.csv` | 176 failing units with reason taxonomy |

## Measured coverage
| Category | Finals | Measured (energy ok) |
|----------|-------:|---------------------:|
| algorithms_computation | 500 | 407 |
| file_data_processing | 360 | 326 |
| image_media_processing | 400 | 367 |
| realistic_applications_utilities | 123 | 113 |
| search_retrieval | 2 | 2 |
| text_log_processing | 100 | 94 |
| **Total** | **1485** | **1309** |

## Static code metrics (n=1485, 1471 parseable)
- Complexity class distribution: O(n log n) 411, O(n) 297, O(n^2 log n) 286,
  O(n^2) 263, O(n^3) 94, O(2^n) 50, O(n^4) 45, O(1) 25.
- FULL_MULTI_TURN has the largest median SLOC (98.5 vs 58 ONE_SHOT),
  function count (3 vs 2) and cyclomatic complexity (18 vs 14).
- declared-target compliance = 71.6% (n=430 programs with a declared target).

## Dynamic energy (n=1309)
- Median package energy: ONE_SHOT 0.561 J, BUG_FIX 0.632 J, FEATURE 0.635 J,
  EDGE_CASE 0.669 J, FULL_MULTI_TURN 0.805 J (+43.4% vs ONE_SHOT).
- Wilcoxon C4 vs C0: p=0.006 (only significant condition).
- Total 1853.0 J = 247.1 mgCO2eq (global-average 480 g/kWh).
- runtime vs energy: Spearman 0.93, Pearson 0.995 (energy is runtime-dominated;
  power ~= energy/runtime).

## Complexity estimation approach
- Static Big-O heuristic from AST: recursion+loop -> O(2^n); nested loop depth
  1/2/3 -> O(n)/O(n^2)/O(n^3), `sort`/`sorted` promotes to O(n log n) / O(n^2 log n).
- Empirical: log-log slope of median runtime vs input bytes at 3 harness scales
  (`small`,`medium`,`large`); slope ~0 constant, ~1 linear, ~2 quadratic.
- Cross-check: Spearman(rank, slope) and precision/recall for "superlinear" class.

## Measurement environment
- Linux 6.19, Python 3.13, 8 CPUs, RAPL intel-rapl:0 (package) + :0:0 (core).
- RAPL read perms reset on reboot.
