"""Automatic input materialization for generated programs.

Harness-generated workloads live in memory (``make_input``), but some
generated programs read real inputs: files opened by relative path, or
``input()``/stdin. Before every measured call the executor calls
``stage()`` which:

1. writes the generated workload into the persistent folder
   ``inputs/<category>/<TASK_ID>/<scale>/`` (one JSON per key, CSV for
   table-shaped values, ``input.txt`` stdin text, ``manifest.json``);
2. exposes the files inside the sandboxed run directory (symlinks, copied
   as fallback) so relative-path opens resolve;
3. provides deterministic stdin text for ``input()``-based programs via
   ``stdin_text()`` (executor replaces ``sys.stdin`` with it).

Content is deterministic (rng seeded from task_id), so the folder is
regenerated only when the workload changes and is identical across all
interaction conditions — inputs never bias the energy comparison.
"""

import csv
import hashlib
import json
import shutil
from pathlib import Path

STDIN_KEY_PRIORITY = ("lines", "docs", "texts", "corpus", "input", "text",
                      "records", "names")


def _scalar_rows(value):
    """CSV rows for table-shaped values, else None."""
    if not isinstance(value, list) or not value:
        return None
    if all(isinstance(x, dict) for x in value):
        cols = sorted({k for row in value for k in row})
        return [cols] + [[row.get(c, "") for c in cols] for row in value]
    if all(isinstance(x, (list, tuple)) for x in value):
        return [list(row) for row in value]
    return None


def content_sha256(inp: dict) -> str:
    try:
        payload = json.dumps(inp, sort_keys=True, default=str)
    except (TypeError, ValueError):
        payload = repr(inp)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def materialize(directory: Path, inp: dict):
    """Write the workload dict into *directory* (idempotent)."""
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for key, val in inp.items():
        try:
            text = json.dumps(val, default=str)
        except (TypeError, ValueError):
            text = json.dumps(repr(val))
        (directory / f"{key}.json").write_text(text, encoding="utf-8")
        entry = {"type": type(val).__name__, "json": f"{key}.json"}
        rows = _scalar_rows(val)
        if rows is not None:
            csv_name = f"{key}.csv"
            with (directory / csv_name).open("w", newline="",
                                             encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            entry["csv"] = csv_name
        manifest[key] = entry
    (directory / "input.txt").write_text(stdin_text(inp), encoding="utf-8")
    manifest["__stdin__"] = "input.txt"
    manifest["__content_sha256__"] = content_sha256(inp)
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")


def stdin_text(inp: dict) -> str:
    """Deterministic stdin payload for stdin-driven programs."""
    for key in STDIN_KEY_PRIORITY:
        val = inp.get(key)
        if isinstance(val, list) and val and all(isinstance(x, str) for x in val):
            return "\n".join(val) + "\n"
    remaining = [v for v in inp.values() if isinstance(v, list) and v]
    if remaining:
        return "\n".join(json.dumps(x, default=str) for x in remaining[0]) + "\n"
    return json.dumps(inp, default=str)


def _fresh(persistent_dir: Path, inp: dict) -> bool:
    """True if the recorded inputs match the current workload exactly."""
    try:
        manifest = json.loads((persistent_dir / "manifest.json").read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("__content_sha256__") == content_sha256(inp)


def stage(persistent_dir: Path, workdir: Path, inp: dict):
    """Refresh persistent inputs, link them into *workdir*, return env dict.

    Files appear in *workdir* under their bare names so relative opens
    (``open("docs.json")``) resolve inside the run directory.
    """
    if not _fresh(persistent_dir, inp):
        materialize(persistent_dir, inp)
    for f in sorted(persistent_dir.iterdir()):
        if not f.is_file():
            continue
        link = workdir / f.name
        if link.is_symlink() or link.exists():
            continue
        try:
            link.symlink_to(f)
        except (OSError, NotImplementedError):
            shutil.copy2(f, link)
    return {
        "GCB_INPUT_DIR": str(persistent_dir),
        "GCB_INPUTS_ROOT": str(workdir),
    }
