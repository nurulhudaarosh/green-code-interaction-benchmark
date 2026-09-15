#!/usr/bin/env python3
"""Measure energy (Intel RAPL), runtime, peak memory for all final programs
in collected/ using the per-task inputs in inputs/.

Design:
- Final program per (category, model, task, condition):
    ONE_SHOT -> code.py, other conditions -> final.py
- Same per-task input for every model/condition (fair comparison)
- Adaptive invocation: (stdin+args) -> (stdin) -> (stdin+flags) -> (self-contained)
- Energy: 1 warmup + K=5 timed runs inside ONE RAPL window (package + core),
  joules per run = delta/1e6/K
- Peak memory: /usr/bin/time -f %M on the warmup run
- Resumable ledger: results/energy_runs.jsonl (skip already-measured sha)
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autoargs import infer_arg_candidates, serve_aliases  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
COLLECTED = REPO / "collected"
INPUTS = REPO / "inputs"
LEDGER = REPO / "results" / "energy_runs.jsonl"

PKG = "/sys/class/powercap/intel-rapl:0/energy_uj"
CORE = "/sys/class/powercap/intel-rapl:0:0/energy_uj"
RANGE = "/sys/class/powercap/intel-rapl:0/max_energy_range_uj"

K = 5            # timed runs per RAPL window
TIMEOUT = 30     # seconds per single run

# candidate CLI arg lists per task (files must exist in the task's input dir);
# tried in order until one exits 0
TASK_INVOCATIONS = {
    "FD-001": [["events.csv"], ["--input", "events.csv"],
               ["--input", "events.csv", "--output-dir", "out"]],
    "FD-002": [["input.ndjson"], ["--input", "input.ndjson"], []],
    "FD-003": [["sales.csv", "out.csv"], ["sales.csv"],
               ["--input", "sales.csv", "--output", "out.csv"]],
    "FD-004": [["inventory_old.csv", "inventory_new.csv", "-o", "report.csv"],
               ["inventory_old.csv", "inventory_new.csv"],
               ["--old", "inventory_old.csv", "--new", "inventory_new.csv"]],
    "FD-005": [["logs.csv", "out.csv"], ["logs.csv"],
               ["--input", "logs.csv", "--output", "out.csv"]],
    "FD-006": [["data.csv", "out.csv"], ["data.csv"],
               ["--input", "data.csv", "--output", "out.csv"]],
    "FD-007": [["events.csv", "out.csv"], ["events.csv"],
               ["--input", "events.csv", "--output", "out.csv"]],
    "FD-008": [[], ["tree"]],
    "FD-009": [["transactions.csv", "out.csv"], ["transactions.csv"],
               ["--input", "transactions.csv", "--output", "out.csv"]],
    "FD-010": [["input.json", "output.json"], ["input.json"],
               ["--input", "input.json", "--output", "output.json"]],
}
# stdin filename override (model-specific variants)
STDIN_OVERRIDE = {
    ("realistic_applications_utilities", "RA-001", "gemini"): "input_gemini.txt",
}


def read_uj(path):
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


def max_range():
    try:
        return int(Path(RANGE).read_text().strip())
    except (OSError, ValueError):
        return 0


def delta_uj(after, before, mrange):
    if after is None or before is None:
        return 0
    d = after - before
    if d < 0 and mrange:
        d += mrange
    return d


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def final_program(cond_dir, cond):
    if cond == "ONE_SHOT":
        cand = cond_dir / "code.py"
        if cand.is_file():
            return cand
    else:
        cand = cond_dir / "final.py"
        if cand.is_file():
            return cand
    pys = sorted(f for f in cond_dir.glob("*.py") if f.name.startswith(("code", "final")))
    return pys[0] if pys else None


def run_once(workdir, stdin_name, args, timeout=TIMEOUT):
    memf = workdir / ".mem"
    cmd = ["/usr/bin/time", "-f", "%M", "-o", str(memf),
           sys.executable, "prog.py", *args]
    stdin = subprocess.DEVNULL
    sf = workdir / stdin_name if stdin_name else None
    if sf and sf.is_file():
        stdin = open(sf, "rb")
    try:
        t0 = time.perf_counter()
        r = subprocess.run(cmd, cwd=workdir, stdin=stdin,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=timeout)
        dt = time.perf_counter() - t0
        rc = r.returncode
    except subprocess.TimeoutExpired:
        return 124, timeout, None
    finally:
        if sf and sf.is_file():
            stdin.close()
    mem = None
    try:
        mem = int(memf.read_text().strip().splitlines()[-1]) / 1024.0  # MB
    except (OSError, ValueError, IndexError):
        pass
    return rc, dt, mem


def invocations(task_id, cat, model, work, prog_text=None):
    """Candidate (stdin_name, args) tuples, tried in order."""
    arglists = TASK_INVOCATIONS.get(task_id)
    stdin = STDIN_OVERRIDE.get((cat, task_id, model), "input.txt")
    sf = work / stdin if stdin else None
    cands = []
    if sf and sf.is_file():
        cands.append((stdin, []))
    if prog_text is not None:
        for args in infer_arg_candidates(work, prog_text):
            cands.append((None, args))
            if sf and sf.is_file():
                cands.append((stdin, args))
    if arglists:
        for args in arglists:
            cands.append((None, args))
            if sf and sf.is_file():
                cands.append((stdin, args))
    if not arglists and not (sf and sf.is_file()):
        cands.append((None, []))
    # always allow a bare self-contained run at the end
    cands.append((None, []))
    return cands


def ensure_input_dirs(work, cat, prog_text=None):
    """Create directories referenced by inferred argv values / literals."""
    (work / "outdir").mkdir(exist_ok=True)
    dirs = {work / "inputdir"}
    if prog_text is not None:
        from autoargs import literal_dirs
        for name in literal_dirs(prog_text):
            dirs.add(work / name)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        if any(d.iterdir()):
            continue
        # give dir-consuming programs something to read
        reserved = {"prog.py", "out.csv", "out.json", "out.txt", "out.ndjson"}
        for f in work.iterdir():
            if f.is_file() and f.name not in reserved:
                shutil.copy2(f, d / f.name)
        if cat == "image_media_processing":
            _make_images(d)
    if cat == "image_media_processing":
        # expose generated images at the run root too (some programs open
        # "image1.jpg" directly rather than scanning a directory)
        made = sorted((work / "inputdir").glob("*.jpg"))
        for i, src in enumerate(made[:2], 1):
            for name in (f"image{i}.jpg", f"img{i}.jpg"):
                if not (work / name).exists():
                    shutil.copy2(src, work / name)


def _make_images(d, n=4, size=256):
    try:
        from PIL import Image
    except ImportError:
        return
    import random
    rng = random.Random(7)
    for i in range(n):
        img = Image.new("RGB", (size, size))
        px = img.load()
        for y in range(size):
            for x in range(size):
                px[x, y] = (rng.randint(0, 255), rng.randint(0, 255),
                            rng.randint(0, 255))
        img.save(d / f"img{i}.png")
        img.save(d / f"img{i}.jpg")


def measure(cat, model, task_id, cond, prog):
    tid_dir = INPUTS / cat / task_id
    rec = {"category": cat, "model": model, "task_id": task_id,
           "condition": cond, "file": str(prog.relative_to(COLLECTED)),
           "sha256": sha256_file(prog)}
    prog_text = prog.read_text(encoding="utf-8", errors="replace")
    with tempfile.TemporaryDirectory(prefix="gcb-energy-") as td:
        work = Path(td)
        if tid_dir.is_dir():
            for f in tid_dir.iterdir():
                if f.is_file():
                    shutil.copy2(f, work / f.name)
                elif f.is_dir():
                    shutil.copytree(f, work / f.name)
        shutil.copy2(prog, work / "prog.py")
        ensure_input_dirs(work, cat, prog_text)
        serve_aliases(work, prog_text)

        # adaptive invocation
        chosen = None
        for stdin_name, args in invocations(task_id, cat, model, work, prog_text):
            rc, dt, mem = run_once(work, stdin_name, args)
            rec["invocation"] = {"stdin": stdin_name, "args": args}
            if rc == 0:
                chosen = (stdin_name, args, mem)
                break
            if rc == 124:
                rec["status"] = "timeout"
                return rec
        if chosen is None:
            rec["status"] = "failed"
            rec["last_exit"] = rc
            return rec

        stdin_name, args, mem = chosen
        rec["peak_mem_mb"] = mem

        # energy: warmup + K runs inside one RAPL window
        mrange = max_range()
        e0p, e0c = read_uj(PKG), read_uj(CORE)
        times = []
        for _ in range(K):
            rc, dt, _ = run_once(work, stdin_name, args)
            times.append(dt)
            if rc != 0:
                rec["status"] = "unstable"
                rec["last_exit"] = rc
                return rec
        e1p, e1c = read_uj(PKG), read_uj(CORE)
        rec["status"] = "ok"
        rec["energy_pkg_j"] = round(delta_uj(e1p, e0p, mrange) / 1e6 / K, 4)
        if e0c is not None and e1c is not None:
            rec["energy_core_j"] = round(delta_uj(e1c, e0c, mrange) / 1e6 / K, 4)
        rec["runtime_s"] = round(sorted(times)[len(times) // 2], 4)
        rec["reps"] = K
    return rec


def measured_shas():
    done = set()
    if LEDGER.is_file():
        for line in LEDGER.read_text().splitlines():
            try:
                r = json.loads(line)
                if r.get("status") == "ok":
                    done.add(r["sha256"])
            except json.JSONDecodeError:
                pass
    return done


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    done = measured_shas()
    n_ok = n_bad = n_skip = 0
    for cat_dir in sorted(COLLECTED.iterdir()):
        code_root = cat_dir / "code"
        if not code_root.is_dir():
            continue
        if only and only not in cat_dir.name:
            continue
        for model_dir in sorted(code_root.iterdir()):
            for task_dir in sorted(model_dir.iterdir()):
                for cond_dir in sorted(task_dir.iterdir()):
                    if not cond_dir.is_dir():
                        continue
                    prog = final_program(cond_dir, cond_dir.name)
                    if prog is None:
                        continue
                    sha = sha256_file(prog)
                    if sha in done:
                        n_skip += 1
                        continue
                    rec = measure(cat_dir.name, model_dir.name,
                                  task_dir.name, cond_dir.name, prog)
                    with LEDGER.open("a") as f:
                        f.write(json.dumps(rec) + "\n")
                    if rec["status"] == "ok":
                        n_ok += 1
                    else:
                        n_bad += 1
                        print(f"  !! {rec['status']}: {rec['file']}", flush=True)
                    print(f"[{n_ok} ok/{n_bad} bad/{n_skip} skip] "
                          f"{cat_dir.name}/{model_dir.name}/{task_dir.name}/"
                          f"{cond_dir.name}", flush=True)
    print(f"DONE ok={n_ok} bad={n_bad} skipped={n_skip}")


if __name__ == "__main__":
    main()
