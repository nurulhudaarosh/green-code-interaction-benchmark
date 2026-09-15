#!/usr/bin/env python3
"""Heuristics that make candidate programs runnable without touching their
source: infer command-line arguments from the program's own argparse /
sys.argv / usage text, and serve already-materialised workload files under
the filenames a program expects to open.
"""
import ast
import re
import shutil
from pathlib import Path

INPUT_HINTS = ("input", "in", "src", "source", "data", "file", "path",
               "old", "new", "prev", "previous", "before", "after",
               "snapshot", "transactions", "events", "logs", "records",
               "sales", "inventory", "customer", "read")
OUTPUT_HINTS = ("output", "out", "dest", "destination", "report", "result",
                "target", "write", "save", "clean")


def _text(prog):
    return Path(prog).read_text(encoding="utf-8", errors="replace")


def add_argument_specs(src):
    """Parse parser.add_argument(...) calls -> [(names, kwargs)]."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    specs = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            names = [a.value for a in node.args
                     if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            if names:
                specs.append((names, kwargs))
    return specs


EXT_RE = re.compile(
    r"""['"]([A-Za-z0-9_][A-Za-z0-9_./-]*?\.
    (?:csv|tsv|json|ndjson|jsonl|txt|log|xml|yaml|yml|
    jpg|jpeg|png|bmp|tif|tiff|webp|gif|pdf))['"]""",
    re.VERBOSE | re.IGNORECASE)


def _literal_files(src):
    """Literal relative filenames the program opens or references."""
    names = set()
    for m in re.finditer(r"""open\s*\(\s*['"]([^'"]+)['"]""", src):
        names.add(m.group(1))
    for m in re.finditer(r"""Path\s*\(\s*['"]([^'"]+)['"]""", src):
        names.add(m.group(1))
    for m in re.finditer(r"""(?:default|dest)\s*=\s*['"]([^'"]+)['"]""", src):
        names.add(m.group(1))
    # any string literal that looks like a data filename (covers filenames
    # passed as function arguments, e.g. run("old_snapshot.csv", ...))
    for m in EXT_RE.finditer(src):
        names.add(m.group(1))
    out = set()
    for n in names:
        if n in ("r", "w", "a", "rb", "wb", "x", "ab", "utf-8", "utf8"):
            continue
        if n.startswith("/") or re.match(r"^[a-zA-Z]:[\\/]", n):
            continue
        out.add(n)
    return out


def literal_dirs(src):
    """Quoted strings that name a directory the program expects."""
    dirs = set()
    for m in re.finditer(r"""['"]([^'"\n]+)['"]""", src):
        n = m.group(1)
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", n):
            continue
        base = n.rstrip("/").split("/")[-1].lower()
        if base in ("photos", "images", "input_images", "imgs", "pics",
                    "input", "inputs", "data", "sample", "samples") \
                or base.endswith(("_dir", "dir", "folder", "images")):
            if n.startswith("/") or "." in base:
                continue
            dirs.add(n)
    return dirs



def _suffix_matches(name, cand):
    return Path(cand).suffix.lower() == Path(name).suffix.lower()


def _tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t}


def pick_source(work, wanted, used):
    """Choose the best existing workload file to serve as `wanted`."""
    files = [f for f in sorted(work.iterdir())
             if f.is_file() and f.name != "prog.py" and f.name not in used]
    if not files:
        return None
    wt = _tokens(wanted)
    best, best_score = None, None
    for f in files:
        score = len(wt & _tokens(f.name))
        if _suffix_matches(wanted, f.name):
            score += 0.5
        if best is None or score > best_score:
            best, best_score = f, score
    return best


def serve_aliases(work, prog_text):
    """Copy existing workload files to literal filenames the program opens."""
    work = Path(work)
    touched, used = [], set()
    for name in sorted(_literal_files(prog_text)):
        dst = work / name
        if dst.exists() or name.endswith("/"):
            continue
        src = pick_source(work, name, used=used | {dst.name})
        if src is None:
            continue
        shutil.copy2(src, dst)
        used.add(src.name)
        touched.append(name)
    return touched


def _is_inputish(name):
    n = name.lower()
    if any(h in n for h in OUTPUT_HINTS):
        return False
    return any(h in n for h in INPUT_HINTS)


def _is_outputish(name):
    n = name.lower()
    return any(h in n for h in OUTPUT_HINTS)


FORMAT_WORDS = ("format", "fmt", "extension", "ext")
NUMBER_WORDS = ("radius", "sigma", "threshold", "quality", "count", "limit",
                "top", "top_n", "n", "k", "size", "width", "height", "scale",
                "amount", "budget", "capacity", "alpha", "factor", "num",
                "iterations", "steps", "depth", "rounds", "seed", "workers")


def _value_for(name, inputs, kind):
    """Pick an argv value for an argument named `name`."""
    n = name.lower()
    if kind == "dir":
        if _is_outputish(n) or "cache" in n:
            return "outdir"
        return "inputdir"
    if any(w in n for w in FORMAT_WORDS):
        return "PNG"
    if n in NUMBER_WORDS or n.endswith(tuple("_" + w for w in NUMBER_WORDS)):
        return "2"
    if _is_outputish(n):
        if "csv" in n:
            return "out.csv"
        if "json" in n:
            return "out.json"
        if "ndjson" in n:
            return "out.ndjson"
        return "out.txt"
    # input-ish / unknown file: choose a plausible source file
    if inputs:
        for key, fname in (("old", "old"), ("prev", "old"), ("before", "old"),
                           ("new", "new"), ("after", "new")):
            if key in n:
                for f in inputs:
                    if fname in f.lower():
                        return f
        if "ndjson" in n:
            for f in inputs:
                if f.endswith(".ndjson"):
                    return f
        if "json" in n and "ndjson" not in n:
            for f in inputs:
                if f.endswith(".json"):
                    return f
        if "csv" in n:
            for f in inputs:
                if f.endswith(".csv"):
                    return f
        if "log" in n:
            for f in inputs:
                if "log" in f.lower():
                    return f
        if "image" in n or "img" in n:
            return "inputdir"
        return inputs[0]
    return "in"


def _build(specs, inputs, work):
    """Turn add_argument specs into an ordered argv (positional + required)."""
    positional, options = [], []
    for names, kwargs in specs:
        flag = names[0]
        is_pos = not flag.startswith("-")
        required = is_pos
        if not is_pos:
            d = kwargs.get("required")
            required = bool(d.value) if isinstance(d, ast.Constant) else False
        kind = "dir" if "dir" in flag.lower() else "file"
        dest = kwargs.get("dest")
        label = dest.value if isinstance(dest, ast.Constant) else flag.lstrip("-")
        if is_pos:
            positional.append((label, kind))
        elif required:
            options.append((flag, label, kind))
    argv = [_value_for(lbl, inputs, k) for lbl, k in positional]
    for flag, lbl, k in options:
        argv += [flag, _value_for(lbl, inputs, k)]
    return argv


def _usage_positionals(src):
    """Positional tokens from a `Usage: ... <a> <b>` line (angle tokens only)."""
    m = re.search(r"[Uu]sage:\s*(.+)", src)
    if not m:
        return []
    names = re.findall(r"<([^>]+)>", m.group(1))
    return [n for n in names if not n.startswith("-")]


def infer_arg_candidates(work, src):
    """Candidate argv lists (without stdin), most-specific first."""
    work = Path(work)
    inputs = sorted(f.name for f in work.iterdir()
                    if f.is_file() and f.name != "prog.py")
    cands = []
    specs = add_argument_specs(src)
    if specs:
        base = _build(specs, inputs, work)
        if base:
            cands.append(base)
        # flag-form fallback for positional specs
        flagform = []
        for names, kwargs in specs:
            flag = names[0]
            if flag.startswith("-"):
                continue
            dest = kwargs.get("dest")
            label = dest.value if isinstance(dest, ast.Constant) else flag
            flagform += [f"--{label}", _value_for(label, inputs,
                                                  "dir" if "dir" in label else "file")]
        if flagform and flagform not in cands:
            cands.append(flagform)
    # usage-string driven
    upos = _usage_positionals(src)
    if upos:
        cands.append([_value_for(u, inputs, "dir" if "dir" in u.lower() else "file")
                      for u in upos])
    # generic positional combos over the available input files
    for f in inputs:
        cands.append([f])
    for f in inputs:
        cands.append([f, "out.csv"])
    for i, a in enumerate(inputs):
        for b in inputs[i + 1:]:
            cands.append([a, b])
            cands.append([a, b, "out.csv"])
            cands.append([a, b, "report.csv"])
    # generic flag forms
    for f in inputs:
        cands.append(["--input", f, "--output", "out.csv"])
        cands.append(["-i", f, "-o", "out.csv"])
    # de-duplicate, preserve order
    seen, out = set(), []
    for c in cands:
        key = tuple(c)
        if c and key not in seen:
            seen.add(key)
            out.append(c)
    return out
