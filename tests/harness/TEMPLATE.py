"""Harness template — copy to tests/harness/<category>/<TASK_ID>.py.

A harness knows how to (a) build a reproducible workload for one scale and
(b) drive ANY module implementing the task API. It is used for BOTH the
generated candidate module and the reference-solution namespace, so
different API shapes (functions vs class) are tolerated inside run() only
as far as the task description genuinely allows.

Correctness = candidate output == reference output on the same input.
Outputs must be JSON-serialisable (lists/dicts/primitives).

Auto-input: before run() is called, the executor also materializes `inp`
into files under `inputs/<category>/<TASK_ID>/<scale>/` (one JSON per key,
CSV for table values, `input.txt` stdin text) and symlinks them into the
run directory, sets GCB_INPUT_DIR, and feeds `input.txt` on stdin — so
candidate programs that read files or `input()` get the same deterministic
workload without any manual input step.
"""

SCALES = ["small", "medium"]  # measured scales; large is optional per task


def make_input(scale: str, rng) -> object:
    """rng is seeded deterministically from the task_id — same workload
    for candidate and reference, and across runs."""
    raise NotImplementedError


def run(module, inp) -> object:
    """Call the task API implemented by `module` and return results.

    `module` is either the candidate module (generated code) or the
    reference solution namespace (a dict of functions). Return a
    JSON-serialisable result of the query/workload in `inp`.
    """
    raise NotImplementedError
