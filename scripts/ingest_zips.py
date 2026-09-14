#!/usr/bin/env python3
"""Ingest member collection ZIPs (no bot).

Each ZIP comes from member_collection.ipynb and contains:
    <root>/dataset/dataset.json            category dataset (new schema)
    <root>/.collection/code/**             generated code
    <root>/.collection/raw/**              raw model responses + turn manifests
    <root>/.collection/logs/*.jsonl
    <root>/.collection/state.json
    <root>/.collection/submissions/manifest.json (optional)

Usage:
    python3 scripts/ingest_zips.py [zip ...]        # default: inbox/*.zip

Output per category:
    collected/<category>/code|raw|logs|state.json|manifest.json
    collected/<category>/ingest_report.json
    collected/STATUS.md
    dataset/<category>/dataset.json   (replaced; previous copy kept as dataset.prev.json)
"""

import argparse
import contextlib
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CATEGORY_BY_CODE = {
    "FD": "file_data_processing",
    "TL": "text_log_processing",
    "SR": "search_retrieval",
    "AC": "algorithms_computation",
    "IM": "image_media_processing",
    "RA": "realistic_applications_utilities",
}

EXPECTED_MODELS = ["gpt", "claude", "gemini", "deepseek"]

INTERACTION_DIRS = {
    "ONE_SHOT": "one_shot",
    "BUG_FIX": "bug_fix",
    "FEATURE_ADDITION": "feature_addition",
    "EDGE_CASE": "edge_case",
    "FULL_MULTI_TURN": "full_multi_turn",
}


def load_tasks(dataset):
    if isinstance(dataset, dict) and "tasks" in dataset:
        return dataset["tasks"]
    if isinstance(dataset, list):
        return dataset
    raise ValueError("dataset.json must be a list or an object with a 'tasks' list")


def interactions_of(task):
    ia = task.get("interactions") or task.get("interaction_design") or {}
    return list(ia.keys())


def turns_for(task, interaction):
    ia = (task.get("interactions") or task.get("interaction_design") or {})
    spec = ia.get(interaction)
    if isinstance(spec, dict) and isinstance(spec.get("turns"), list):
        return len(spec["turns"])
    return {"ONE_SHOT": 1}.get(interaction, 2 if interaction != "FULL_MULTI_TURN" else 4)


def expected_code_files(task, model):
    tid = str(task["task_id"])
    base = f"code/{model}/{tid}"
    out = []
    for interaction in interactions_of(task):
        n = turns_for(task, interaction)
        if interaction == "ONE_SHOT":
            out.append(f"{base}/ONE_SHOT/code.py")
        elif interaction == "FULL_MULTI_TURN":
            out += [f"{base}/FULL_MULTI_TURN/turn_{i:02d}.py" for i in range(1, n + 1)]
            out.append(f"{base}/FULL_MULTI_TURN/final.py")
        else:
            out.append(f"{base}/{interaction}/initial.py")
            out.append(f"{base}/{interaction}/final.py")
    return out


def find_roots(tmp: Path):
    """Locate collection workspaces inside the extracted zip."""
    roots = []
    for cand in [tmp] + [p for p in tmp.iterdir() if p.is_dir()]:
        if (cand / ".collection").is_dir() or (cand / "dataset" / "dataset.json").is_file():
            roots.append(cand)
        else:
            for sub in cand.iterdir():
                if sub.is_dir() and (sub / ".collection").is_dir():
                    roots.append(sub)
    return roots


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def syntax_ok(path: Path):
    import py_compile
    try:
        py_compile.compile(str(path), cfile=tempfile.mktemp(), doraise=True)
        return True
    except py_compile.PyCompileError:
        return False


def process_source(src: Path, dry_run: bool):
    report = {
        "source_zip": src.name,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "category": None,
        "dataset_version": None,
        "notebooks": [],
        "task_count": 0,
        "expected_files": 0,
        "present": 0,
        "missing": [],
        "empty": [],
        "syntax_errors": [],
        "manifest_mismatches": [],
        "extra_files": [],
        "units_done": 0,
        "units_total": 0,
    }

    ctx = contextlib.nullcontext(str(src)) if src.is_dir() \
        else tempfile.TemporaryDirectory()
    with ctx as td:
        tmp = Path(td)
        if src.is_file():
            with zipfile.ZipFile(src) as z:
                z.extractall(tmp)

        roots = find_roots(tmp)
        if not roots:
            report["error"] = "no .collection/ or dataset/dataset.json found in zip"
            return report
        root = roots[0]

        ds_file = root / "dataset" / "dataset.json"
        if not ds_file.is_file():
            report["error"] = "dataset/dataset.json missing from zip"
            return report
        dataset = json.loads(ds_file.read_text(encoding="utf-8"))
        tasks = load_tasks(dataset)
        meta = dataset.get("dataset_metadata", {}) if isinstance(dataset, dict) else {}
        code_dir_name = meta.get("category")
        category = code_dir_name if code_dir_name in CATEGORY_BY_CODE.values() \
            else CATEGORY_BY_CODE.get(meta.get("category_code", ""))
        if category is None and tasks:
            prefix = str(tasks[0].get("task_id", "")).split("-")[0].upper()
            category = CATEGORY_BY_CODE.get(prefix)
        if category is None:
            report["error"] = "cannot determine category from dataset"
            return report

        report["category"] = category
        report["dataset_version"] = meta.get("dataset_version")
        report["task_count"] = len(tasks)

        coll = root / ".collection"
        code_root = coll / "code"
        all_code = {
            str(p.relative_to(coll)).replace("\\", "/")
            for p in (code_root.rglob("*.py") if code_root.is_dir() else [])
        }

        expected = set()
        units_total = units_done = 0
        for task in tasks:
            for model in EXPECTED_MODELS:
                files = expected_code_files(task, model)
                expected.update(files)
                units_total += len(interactions_of(task))
                if files and all(
                    (coll / f).is_file() and (coll / f).read_text(encoding="utf-8").strip()
                    for f in files
                ):
                    units_done += 1
        report["units_total"] = units_total
        report["units_done"] = units_done
        report["expected_files"] = len(expected)
        report["missing"] = sorted(expected - all_code)
        report["extra_files"] = sorted(all_code - expected)

        for rel in sorted(expected & all_code):
            p = coll / rel
            if not p.read_text(encoding="utf-8").strip():
                report["empty"].append(rel)
            elif not syntax_ok(p):
                report["syntax_errors"].append(rel)

        manifest_file = coll / "submissions" / "manifest.json"
        if manifest_file.is_file():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            for entry in manifest.get("files", []):
                p = root / entry["path"]
                if not p.is_file() or sha256(p) != entry.get("sha256"):
                    report["manifest_mismatches"].append(entry["path"])

        report["present"] = len(expected & all_code)
        report["notebooks"] = sorted(p.name for p in root.glob("*.ipynb"))

        if not dry_run:
            dest = REPO / "collected" / category
            if dest.is_dir() and (dest / "ingest_report.json").is_file():
                prev = json.loads(
                    (dest / "ingest_report.json").read_text(encoding="utf-8")
                )
                if prev.get("source_zip") != src.name:
                    print(
                        f"  WARNING: {category} already ingested from "
                        f"'{prev.get('source_zip')}'; merging this ZIP on top. "
                        "If two members cover the same category, keep ZIPs separate."
                    )
            for sub in ("code", "raw"):
                src = coll / sub
                if src.is_dir():
                    shutil.copytree(src, dest / sub, dirs_exist_ok=True)
            for extra in ("logs", "state.json"):
                src = coll / extra
                if src.is_dir():
                    shutil.copytree(src, dest / extra, dirs_exist_ok=True)
                elif src.is_file():
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest / extra)
            if manifest_file.is_file():
                (dest / "submissions").mkdir(parents=True, exist_ok=True)
                shutil.copy2(manifest_file, dest / "submissions" / "manifest.json")
            for nb in sorted(root.glob("*.ipynb")):
                (dest / "notebook").mkdir(parents=True, exist_ok=True)
                shutil.copy2(nb, dest / "notebook" / nb.name)

            ds_dest = REPO / "dataset" / category / "dataset.json"
            ds_dest.parent.mkdir(parents=True, exist_ok=True)
            if ds_dest.is_file() and ds_dest.read_bytes() != ds_file.read_bytes():
                shutil.copy2(ds_dest, ds_dest.parent / "dataset.prev.json")
            if ds_dest.is_file() and ds_dest.read_bytes() == ds_file.read_bytes():
                report["dataset_updated"] = False
            else:
                ds_dest.write_bytes(ds_file.read_bytes())
                report["dataset_updated"] = True

            (dest / "ingest_report.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    return report


def write_status(reports):
    lines = [
        "# Collection Status",
        "",
        f"Updated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Category | Units done | Expected files | Present | Missing | Empty | Syntax errors |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        cat = r.get("category") or r["source_zip"]
        if r.get("error"):
            lines.append(f"| {cat} | ERROR: {r['error']} | | | | | |")
            continue
        lines.append(
            f"| {cat} | {r['units_done']}/{r['units_total']} | {r['expected_files']} "
            f"| {r['present']} | {len(r['missing'])} | {len(r['empty'])} "
            f"| {len(r['syntax_errors'])} |"
        )
    lines.append("")
    for r in reports:
        if r.get("missing") and not r.get("error"):
            lines.append(f"## Missing units — {r['category']}")
            units = sorted({"|".join(f.split("/")[:3]) for f in r["missing"]})
            lines += [f"- {u}" for u in units]
            lines.append("")
    out = REPO / "collected" / "STATUS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("zips", nargs="*", type=Path,
                    help="ZIP files or collection folders (default: inbox/*.zip + inbox/<category>/)")
    ap.add_argument("--dry-run", action="store_true", help="validate only, copy nothing")
    args = ap.parse_args()

    if args.zips:
        sources = list(args.zips)
    else:
        inbox = REPO / "inbox"
        sources = sorted(inbox.glob("*.zip")) + sorted(
            p for p in inbox.iterdir()
            if p.is_dir() and not p.name.startswith("."))
    if not sources:
        print("No sources found. Drop member ZIPs/folders into inbox/ or pass paths.")
        return 1

    reports = []
    for zp in sources:
        print(f"\n=== {zp.name} ===")
        r = process_source(zp, args.dry_run)
        reports.append(r)
        if r.get("error"):
            print(f"  ERROR: {r['error']}")
            continue
        ok = not (r["missing"] or r["empty"] or r["syntax_errors"] or r["manifest_mismatches"])
        print(f"  category        : {r['category']} (dataset {r['dataset_version']}, {r['task_count']} tasks)")
        if r.get("notebooks"):
            print(f"  notebook(s)     : {', '.join(r['notebooks'])}")
        print(f"  units complete  : {r['units_done']}/{r['units_total']}")
        print(f"  files present   : {r['present']}/{r['expected_files']}")
        for key in ("missing", "empty", "syntax_errors", "manifest_mismatches", "extra_files"):
            if r[key]:
                print(f"  {key:<15} : {len(r[key])}")
                for item in r[key][:15]:
                    print(f"      - {item}")
                if len(r[key]) > 15:
                    print(f"      ... +{len(r[key]) - 15} more")
        print(f"  status          : {'COMPLETE' if ok else 'INCOMPLETE'}")
        if r.get("dataset_updated"):
            print("  dataset         : updated dataset/<category>/dataset.json")

    if not args.dry_run:
        write_status(reports)
        print("\nWrote collected/STATUS.md and per-category ingest_report.json")

    return 0 if all(not r.get("error") for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
