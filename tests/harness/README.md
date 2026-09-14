# Test harnesses (per task)

`tests/harness/<category_dir>/<TASK_ID>.py` implements `make_input(scale, rng)`
and `run(module, inp)` — see `TEMPLATE.py`. The runner executes the reference
solution and every candidate program through the SAME harness; a candidate is
correct iff its output equals the reference output on the generated workload.

Units without a harness are recorded as `skipped (no_harness)` and are
re-tried automatically once the harness file appears — the pipeline needs no
manual re-run bookkeeping.

Start from `TEMPLATE.py`. Keep inputs deterministic (seed `rng` from scale),
keep workloads ≥ a few hundred ms at `medium` so energy is measurable, and
never compare memory addresses or timestamps.
