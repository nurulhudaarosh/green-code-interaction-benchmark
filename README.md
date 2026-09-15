# Green Code Interaction Benchmark

Does the trajectory of human–AI coding interaction (one-shot vs. bug-fix /
feature-addition / edge-case / full multi-turn) systematically change the
**energy efficiency of the final executable program**?

Existing work studies LLM code energy, prompting strategies, and multi-turn
code generation separately. This benchmark isolates the effect of
*interaction trajectory* on final-code energy, across AI models and task
types, using Intel RAPL–based energy measurement.

## Research Questions

- **RQ1** — Does realistic multi-turn AI-assisted coding produce final programs with significantly different energy consumption compared with one-shot coding?
- **RQ2** — Does the effect of interaction style on final-code energy vary across AI models?
- **RQ3** — How do bug fixing, feature addition, and edge-case handling individually affect energy efficiency of final generated code?
- **RQ4** — What relationships exist among energy, execution time, CPU utilization, memory usage, and correctness?
- **RQ5** — What code-level characteristics explain energy-efficiency differences between one-shot and multi-turn programs?

## Experimental Design

5 interaction conditions (equivalent final requirements in all conditions):

| ID | Condition | Trajectory |
|----|-----------|------------|
| C0 | `ONE_SHOT` | full specification at once |
| C1 | `BUG_FIX` | initial task → bug report |
| C2 | `FEATURE_ADDITION` | initial task → feature request |
| C3 | `EDGE_CASE` | initial task → edge-case requirement |
| C4 | `FULL_MULTI_TURN` | initial → bug fix → feature → edge case |

Matrix: **6 categories × 20 tasks × 5 conditions × 4 models = 2400 final programs**

Categories: `file_data_processing` (FD), `text_log_processing` (TL),
`search_retrieval` (SR), `algorithms_computation` (AC),
`image_media_processing` (IM), `realistic_applications_utilities` (RA).

Models: GPT, Claude, Gemini, DeepSeek (manual chat-UI generation, same
prompts, fresh conversation per condition, no manual repair of code).

## Pipeline

```
150 candidate tasks → dataset audit → 120 final tasks (dataset_v1.0 freeze)
→ pilot study (~8 tasks × 2 models × 5 conditions)
→ AI code generation (2400 programs)
→ correctness testing
→ controlled execution (energy + runtime + CPU + memory)
→ static code analysis
→ statistical analysis → results
```

Energy metric: joules per successful program execution, with
ΔE = (E_MT − E_ST)/E_ST × 100; secondary metrics: runtime, peak memory,
CPU utilization, energy per unit runtime.

## Repository Layout

```
analysis/                  aggregation, statistics, energy/interaction analysis, plots
collection/                member collection notebook (Colab) + workflow docs
config/                    models.json, experiment.json, hardware.json, drive_sources.json
collected/<category>/      validated code/raw responses ingested from member ZIPs
dataset/<category>/        per-category task datasets (dataset.json)
docs/                      research proposal (green-proposal.docx)
inbox/                     incoming member ZIP submissions (gitignored)
inputs/<category>/<task>/  auto-materialized task workloads (generated, gitignored)
kits/                      per-category member kits (generated, gitignored)
measurement/               RAPL energy, memory, CPU/system probes
results/{raw,processed,final}/  experiment outputs
runner/                    executor driver, measure_unit, sandbox, tester, input staging
scripts/                   project-setup.sh, runway tools (see Runbook below)
tests/                     unit tests + per-task harnesses (tests/harness/)
```

## Usage

Code collection is manual — no bot. Each member runs
`collection/member_collection.ipynb` in Colab for one category and returns a
ZIP. Coordinator flow:

```bash
# 1. build kits for members (notebook + dataset per category)
python3 scripts/make_member_kit.py

# 2. drop the 6 returned ZIPs into inbox/, then ingest + validate:
python3 scripts/ingest_zips.py
#    -> collected/<category>/, collected/STATUS.md,
#       dataset/<category>/dataset.json updated from ZIP

# 3. check completeness
cat collected/STATUS.md
```

Measurement is slow and members finish at different times, so measurement
runs are tracked in an append-only ledger (`results/measurement_ledger.jsonl`)
keyed by code sha256 — a program is never measured twice unless its code
changed:

```bash
python3 scripts/measure_progress.py status          # progress table
python3 scripts/measure_progress.py queue -o q.jsonl  # pending programs only
python3 scripts/measure_progress.py record <file.py> --status measured --metrics results/raw/xxx.json
```

## Automated pipeline (CI/CD mode)

Put each member's shared Drive ZIP link in `config/drive_sources.json`, then:

```bash
pip install gdown
python3 scripts/run_pipeline.py              # sync -> ingest -> measure -> analyze
python3 scripts/run_pipeline.py --watch 900  # repeat every 15 min
```

One pass = download updated ZIPs (checksum-checked, unchanged skipped) →
ingest/validate → measure only units not measured before (or previously
`error`/`skipped`, so new harnesses auto-apply) → rebuild
`results/processed/*.csv`, ΔE tables, statistical tests and
`results/final/plots/*.png`. When one member completes one task, the next
pass measures exactly that one program.

Requirements for real measurement:

- **Harness per task**: `tests/harness/<category>/<TASK_ID>.py`
  (see `tests/harness/TEMPLATE.py`) — without one the unit is recorded
  `skipped (no_harness)` and retried automatically once written. Harnesses
  are auto-generated + self-tested by `scripts/gen_harnesses.py`.
- **Auto-input**: candidate programs that need real input (files opened by
  relative path, or `input()`/stdin) are served automatically: the harness
  workload is written to `inputs/<category>/<TASK_ID>/<scale>/` (JSON per
  key, CSV tables, `input.txt` stdin text), symlinked into the sandboxed
  run directory, exposed via `GCB_INPUT_DIR`, and fed on stdin — no manual
  input files, identical workload for every condition.
- **RAPL read permission** for your user on the measurement machine, e.g.
  `sudo chmod go+r /sys/class/powercap/intel-rapl:0/energy_uj` (or run the
  pipeline via sudo). Without it, energy is `null` but runtime/memory/CPU
  still work.

## Runbook — every command

```bash
# 1. Setup
bash scripts/project-setup.sh                  # scaffold/repair layout (idempotent)
pip install -r requirements.txt                # psutil, gdown, numpy, pandas, scipy, matplotlib, pytest

# 2. Dataset & member collection (per category)
python3 scripts/make_member_kit.py             # build kits/<category>/ for members
python3 scripts/sync_drive.py                  # pull member folders into inbox/ (gdown)
python3 scripts/ingest_zips.py                 # validate + merge inbox/ (ZIPs or folders)
cat collected/STATUS.md                        # completeness per category

# 3. Harnesses (missing ones auto-generated + self-tested from references)
python3 scripts/gen_harnesses.py [category] [--force]

# 4. Measurement (correctness + energy + runtime + memory + CPU)
python3 scripts/run_pipeline.py --no-sync      # one full pass, skip Drive sync
python3 scripts/run_pipeline.py                # full pass incl. Drive sync
python3 scripts/run_pipeline.py --limit 10     # at most 10 pending units/count
python3 scripts/run_pipeline.py --resilient    # log failures, keep going
python3 scripts/run_pipeline.py --watch 900    # CI/CD mode: repeat every 15 min
python3 scripts/measure_progress.py status     # ledger progress table
python3 scripts/measure_progress.py queue --redo-failed -o q.jsonl
python3 runner/measure_unit.py --unit-file q.json   # measure one unit by hand

# 4b. Fix a failing unit yourself (no re-download ever clobbers it):
#     1. edit collected/<category>/code/<model>/<task>/<INT>/*.py   (your fix)
#     2. re-run the pipeline — ingest prints "KEPT ... local modification(s)",
#        the sha256 change makes the queue re-measure it, the fix gets measured.
#     3. to go back to the member's version: delete your edited collected file.

# 5. Drive sync is add-only — each file is fetched from Drive AT MOST ONCE:
#     - Results/state are kept in results/file_ledger.jsonl and
#       inbox/.sync_state.json, so re-running never re-requests a file
#       already saved or measured.  Members only add NEW files.
#     - If a Drive file fails (Google "many accesses" quota), it is
#       scheduled with exponential backoff (15m → 30m → 1h … 24h) and
#       skipped on the next passes until the quota resets — no spam.
#     - Per pass at most 500 new files are fetched (--) so big folders
#       make progress in chunks with a natural gap between files.
#     - Inspect: python3 scripts/sync_drive.py --ledger [N]
#     - Optional: delete cookies.txt so the broken session is skipped
#       (the anonymous fallback is used automatically).

# 5. Analysis (also run automatically at the end of every pipeline pass)
python3 analysis/aggregate.py                  # -> results/processed/metrics.csv
python3 analysis/energy_analysis.py            # -> delta_energy.csv, energy_summary.json
python3 analysis/interaction_analysis.py       # -> interaction_breakdown.csv
python3 analysis/rq_statistics.py              # -> statistical_tests.json (Wilcoxon, Kruskal)
python3 analysis/plots.py                      # -> results/final/plots/*.png
python3 scripts/code_problems.py               # -> results/final/problems.{md,csv} to fix

# 6. Tests
python3 -m unittest discover -s tests -p 'test_*.py'   # or: pytest tests
```

## Measurement Environment

- Final energy experiments require a **controlled Linux machine with Intel
  RAPL** (`/sys/class/powercap/intel-rapl*`, root access may be needed).
- Colab / shared notebooks are acceptable for dataset validation, reference
  solutions, correctness testing, and development — **not** for final energy
  measurement.

## Dataset Status

| Category | Tasks |
|----------|-------|
| search_retrieval | 25 candidates (SR-001 … SR-025) |
| others | pending collection |
