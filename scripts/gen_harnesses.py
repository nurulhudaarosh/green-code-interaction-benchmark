#!/usr/bin/env python3
"""Auto-generate per-task harness files from dataset reference signatures.

For every task in dataset/<category>/dataset.json that has no harness yet,
parse the reference solution's top-level functions and emit
tests/harness/<category>/<TASK_ID>.py implementing the harness protocol:

    SCALES, make_input(scale, rng), run(module, inp)

Inputs are generated deterministically from parameter NAMES of the
reference (docs/records/names/queries/pairs/points/...). A builder
function (``build_*``) is executed first and its output is fed to the
query function(s) that take it.

Every generated harness is SELF-TESTED against the reference before it is
kept. If the reference cannot run it cleanly, the file is discarded and
the task stays ``skipped (no_harness)``.

Usage:
    python3 scripts/gen_harnesses.py
    python3 scripts/gen_harnesses.py search_retrieval
    python3 scripts/gen_harnesses.py --force
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

HARNESS_DIR = REPO / "tests" / "harness"

DATA_NAMES = {
    "docs", "texts", "corpus", "lines", "names", "dictionary", "vocab",
    "dictionary_set", "freq", "pairs", "emails", "records", "rows", "entries",
    "items", "products", "readings", "points", "contacts", "papers", "users",
    "employees", "list",
}
BUILD_NAMES = {
    "index", "idx", "root", "lookup", "doc_vecs", "idf", "universe",
    "dept_index", "salary_sorted", "salary_values", "sorted_readings",
    "sorted_entries", "sorted_ts", "level_index", "name_index", "category_index",
    "price_sorted", "price_values", "grid", "table", "structure", "tree",
}
QBATCH_NAMES = {"ids", "tags", "queries", "groups", "words", "raw_numbers",
                "levels", "patterns"}
QSCALAR_NAMES = {
    "query_tokens", "tokens", "prefix", "department", "min_salary", "query",
    "max_dist", "e", "p", "line", "level", "start", "end", "text", "pattern",
    "word", "keyword", "category", "min_price", "max_price", "domain", "k",
    "threshold", "query_point", "citation_text", "a", "b", "tag", "s", "t",
    "wiki",
}

HELPERS = '''import random

SCALES = ["small", "medium", "large"]
_Q = 40

_VOCAB = [f"w{i}" for i in range(400)]
_NAMES = ["alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi",
          "ivan", "judy", "mallory", "oscar", "peggy", "trent", "victor"]
_DEPTS = ["eng", "ops", "sales", "fin", "hr"]
_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]


def _word(rng):
    return rng.choice(_VOCAB)


def _sentence(rng, k=None):
    return " ".join(_word(rng) for _ in range(k or rng.randint(2, 6)))


def _tokens(rng, k=None):
    return rng.sample(_VOCAB, k or rng.randint(1, 3))


def _docs(n, rng):
    return [_sentence(rng, rng.randint(5, 30)) for _ in range(n)]


def _lines(n, rng):
    return [f"2026-09-14T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d} "
            f"{rng.choice(_LEVELS)} [{rng.choice(_DEPTS)}] {_sentence(rng)} "
            f"id={i}" for i in range(n)]


def _logline(rng):
    return (f"2026-09-14T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d} "
            f"{rng.choice(_LEVELS)} [{rng.choice(_DEPTS)}] {_sentence(rng)} "
            f"id={rng.randint(0, 9999)}")


def _names(n, rng):
    return [rng.choice(_NAMES) + str(rng.randint(0, n // 3 + 1)) for _ in range(n)]


def _words(n, rng):
    return list({rng.choice(_VOCAB) for _ in range(n)})


def _freq(rng):
    return {w: rng.randint(1, 500) for w in _words(120, rng)}


def _pairs(n, rng):
    return [(rng.choice(_NAMES), rng.randint(0, n)) for _ in range(n)]


def _emails(n, rng):
    return [rng.choice(_NAMES) + str(rng.randint(0, 90)) + "@" +
            rng.choice(["ex.com", "mail.org", "corp.net"]) for _ in range(n)]


def _email(rng):
    return rng.choice(_NAMES) + "@" + rng.choice(["ex.com", "mail.org"])


def _phone(rng):
    return f"+1-555-{rng.randint(1000, 9999)}"


def _domain(rng):
    return rng.choice(["ex.com", "mail.org", "corp.net"])


def _dept(rng):
    return rng.choice(_DEPTS)


def _level(rng):
    return rng.choice(_LEVELS)


def _readings(n, rng):
    return [rng.randint(0, 10 ** 6) for _ in range(n)]


def _points(n, rng):
    return [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]


def _records(n, rng):
    out = []
    for i in range(n):
        out.append({
            "id": i, "doc_id": i, "name": rng.choice(_NAMES),
            "department": rng.choice(_DEPTS), "dept": rng.choice(_DEPTS),
            "salary": rng.randint(30000, 150000),
            "value": rng.randint(0, 10000), "category": rng.choice(_DEPTS),
            "amount": rng.randint(1, 500), "quantity": rng.randint(1, 20),
            "price": rng.randint(1, 999), "count": rng.randint(0, 100),
            "score": rng.random(), "text": _sentence(rng),
            "title": _sentence(rng, 4), "word": _word(rng),
            "email": _email(rng), "phone": _phone(rng),
            "domain": _domain(rng), "level": _level(rng),
            "timestamp": rng.randint(0, 10 ** 6), "ts": rng.randint(0, 10 ** 6),
            "tags": rng.sample(_VOCAB, rng.randint(1, 4)),
            "x": rng.uniform(0, 100), "y": rng.uniform(0, 100),
        })
    return out


def _ids(n, rng):
    return [rng.randint(0, max(1, n - 1)) for _ in range(_Q)]
'''

RUNTIME = '''

def _get(module, name):
    if isinstance(module, dict):
        return module.get(name)
    return getattr(module, name, None)


def _jsonable(v):
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted(_jsonable(x) for x in v)
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return repr(v)


def _module_items(module):
    return module.items() if isinstance(module, dict) else vars(module).items()


_CLASS_HINTS = ("index", "trie", "lookup", "grid", "engine", "search", "invert",
                "auto", "bm25", "tfidf", "tag", "freq", "domain", "title",
                "sort", "reverse", "level", "cache", "store")


def _find_class(module):
    classes = [(n, o) for n, o in _module_items(module)
               if isinstance(o, type) and not n.startswith("_")]
    for n, o in classes:
        if any(t in n.lower() for t in _CLASS_HINTS):
            return o
    return classes[0][1] if classes else None


_ALIASES = ["query", "search", "lookup", "find", "get", "match", "process",
            "evaluate", "rank", "nearest", "completions", "top_k", "correct",
            "duplicates", "substring", "range", "filter", "batch", "run"]


def _instantiate(cls, data):
    import inspect
    try:
        ip = [p for p in inspect.signature(cls.__init__).parameters.values()
              if p.name != "self"]
    except (TypeError, ValueError):
        ip = []
    cands = []
    if data is not None:
        adapted = data
        if ip and isinstance(data, list) and data and isinstance(data[0], str):
            nm = ip[0].name.lower()
            if any(t in nm for t in ("document", "doc", "mapping", "corpus", "map")):
                adapted = dict(enumerate(data))
        cands.append((adapted,))
    cands.append(())
    if data is not None:
        cands.append((data,))
    last = None
    for a in cands:
        try:
            return cls(*a)
        except Exception as e:
            last = e
    raise RuntimeError(f"cannot instantiate {cls.__name__}: {last}")


def _adapt(v):
    if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
        return " ".join(v)
    return v


SPEC = __SPEC__


def run(module, inp):
    env = {}
    out = {}
    for fname, params in SPEC:
        fn = _get(module, fname)
        obj = env.get("__obj__")
        if fn is None and obj is None and fname.startswith("build_"):
            cls = _find_class(module)
            if cls is not None:
                data = None
                for p, k in params:
                    if k == "data":
                        data = inp[p]
                        break
                try:
                    obj = _instantiate(cls, data)
                except Exception as e:
                    out[fname] = {"__error__": str(e)}
                    continue
                env["__obj__"] = obj
                env["__builder__"] = obj
                out[fname] = [cls.__name__]
                continue
        method = False
        if fn is None:
            if obj is None:
                out[fname] = None
                continue
            fn = None
            for cand in [fname] + _ALIASES:
                if hasattr(obj, cand):
                    fn = getattr(obj, cand)
                    break
            if fn is None:
                out[fname] = None
                continue
            params = [(p, k) for p, k in params if k in ("qscalar", "qbatch")]
            method = True
        qpos = [i for i, (_p, k) in enumerate(params) if k == "qscalar"]
        bpos = [i for i, (_p, k) in enumerate(params) if k == "build"]
        loops = _Q if qpos else 1
        res = []
        raws = []
        for j in range(loops):
            call = []
            bi = 0
            for p, k in params:
                if k == "build":
                    bv = env.get("__builder__")
                    if isinstance(bv, (list, tuple)) and len(bpos) > 1:
                        call.append(bv[bi])
                    else:
                        call.append(bv)
                    bi += 1
                elif k == "qscalar":
                    call.append(inp[p + "__q"][j])
                elif k == "qbatch":
                    call.append(inp[p + "__q"])
                else:
                    call.append(inp[p])
            try:
                raw = fn(*call)
                raws.append(raw)
                res.append(_jsonable(raw))
            except Exception as e:
                if method:
                    try:
                        raw = fn(*[_adapt(a) for a in call])
                        raws.append(raw)
                        res.append(_jsonable(raw))
                        continue
                    except Exception as e2:
                        e = e2
                res.append({"__error__": f"{type(e).__name__}: {e}"})
        if fname.startswith("build_") and raws:
            env["__builder__"] = raws[0]
        out[fname] = res[0] if len(res) == 1 else res
    if any(not f.startswith("build_") for f, _ in SPEC):
        out = {k: v for k, v in out.items() if not k.startswith("build_")}
    return out
'''


def sigs_of(code):
    return re.findall(r"^def (\w+)\(([^)]*)\)", code, re.M)


def params_of(raw):
    """Return [(name, default_repr_or_None), ...]."""
    out = []
    for p in raw.split(","):
        p = p.strip()
        default = None
        if "=" in p:
            p, default = p.split("=", 1)
            default = default.strip()
        p = p.split(":")[0].strip()
        if p and p != "self":
            out.append((p, default))
    return out


def string_elements(code, p):
    """True if a loop variable over param p is used as a string (.lower/.split)."""
    loop_vars = []
    for m in re.finditer(r"for\s+([^:]+?)\s+in\s+(?:enumerate\()?\s*"
                         + re.escape(p) + r"\b", code):
        for v in re.findall(r"\w+", m.group(1)):
            if v not in ("enumerate",):
                loop_vars.append(v)
    return any(re.search(rf"\b{re.escape(v)}\.lower\(\)", code)
               or re.search(rf"\b{re.escape(v)}\.split\(", code)
               for v in loop_vars)


def kind_of(fname, p, default):
    if default is not None:
        return "config"
    if p in BUILD_NAMES:
        return "build"
    if p in DATA_NAMES:
        return "data"
    if p in QBATCH_NAMES:
        return "qbatch"
    if p in QSCALAR_NAMES:
        return "qscalar"
    if fname.startswith("build_"):
        return "config"
    return "qscalar"


def data_expr(name, string_params):
    if name in string_params:
        return "_docs(n, rng)"
    if name in ("docs", "texts", "corpus"):
        return "_docs(n, rng)"
    if name == "lines":
        return "_lines(n, rng)"
    if name == "names":
        return "_names(n, rng)"
    if name in ("dictionary", "vocab"):
        return "_words(max(10, n // 2), rng)"
    if name == "dictionary_set":
        return "set(_words(max(10, n // 2), rng))"
    if name == "freq":
        return "_freq(rng)"
    if name == "pairs":
        return "_pairs(n, rng)"
    if name == "emails":
        return "_emails(n, rng)"
    if name == "points":
        return "_points(n, rng)"
    if name == "readings":
        return "_records(n, rng)"
    return "_records(n, rng)"


def config_expr(name, default):
    if default is not None:
        return default
    if name == "k1":
        return "1.5"
    if name == "b":
        return "0.75"
    if name == "cell_size":
        return "rng.randint(5, 50)"
    return "rng.randint(1, 10)"


def qscalar_expr(name):
    return {
        "query_tokens": "_tokens(rng)", "tokens": "_tokens(rng)",
        "query": "_sentence(rng)", "word": "_word(rng)",
        "pattern": "_word(rng)", "prefix": "_word(rng)[:3]",
        "text": "_sentence(rng)", "line": "_logline(rng)",
        "citation_text": "_sentence(rng)", "s": "_sentence(rng)",
        "t": "_sentence(rng)", "a": "_word(rng)", "b": "_word(rng)",
        "department": "_dept(rng)", "category": "_dept(rng)",
        "tag": "_word(rng)", "domain": "_domain(rng)",
        "level": "_level(rng)", "keyword": "_word(rng)",
        "e": "_email(rng)", "p": "_phone(rng)",
        "min_salary": "rng.randint(10000, 90000)",
        "min_price": "rng.randint(1, 300)",
        "max_price": "rng.randint(300, 999)",
        "k": "rng.randint(1, 20)", "max_dist": "rng.randint(1, 3)",
        "threshold": "round(rng.uniform(0.1, 0.9), 2)",
        "query_point": "(rng.uniform(0, 100), rng.uniform(0, 100))",
        "start": "rng.randint(0, max(1, n // 3))",
    }.get(name, "_word(rng)")


def qbatch_expr(name):
    return {
        "ids": "_ids(n, rng)",
        "tags": "[_word(rng) for _ in range(_Q)]",
        "groups": "[_tokens(rng) for _ in range(_Q)]",
        "words": "[_word(rng) for _ in range(_Q)]",
        "raw_numbers": "[_phone(rng) for _ in range(_Q)]",
        "queries": "[_sentence(rng) for _ in range(_Q)]",
    }.get(name, "[_word(rng) for _ in range(_Q)]")


def build_source(task):
    tid = task["task_id"]
    code = (task.get("reference_solution") or {}).get("code") or ""
    sigs = sigs_of(code)
    if not sigs:
        return None
    parsed = [(f, params_of(ps)) for f, ps in sigs]
    parsed = [(f, ps) for f, ps in parsed if ps]

    string_params = {p for _f, ps in parsed for p, _d in ps
                     if string_elements(code, p)}

    spec = []
    need = {}   # key -> (kind, name, default)
    for fname, params in parsed:
        plist = []
        for p, default in params:
            k = kind_of(fname, p, default)
            plist.append((p, k))
            key = p + "__q" if k in ("qscalar", "qbatch") else p
            if key not in need:
                need[key] = (k, p, default)
        spec.append((fname, plist))
    if not spec:
        return None

    lines = ["def make_input(scale, rng):",
             "    n = {'small': 300, 'medium': 4000, 'large': 15000}.get(scale, 300)",
             "    inp = {}"]
    for key, (kind, name, default) in need.items():
        if kind == "data":
            expr = data_expr(name, string_params)
        elif kind == "config":
            expr = config_expr(name, default)
        elif kind == "qbatch":
            expr = qbatch_expr(name)
        else:
            expr = f"[{qscalar_expr(name)} for _ in range(_Q)]"
        lines.append(f"    inp[{key!r}] = {expr}")
    if "end__q" in need:
        lines.append("    inp['end__q'] = [inp.get('start__q', [0] * _Q)[j] + "
                     "rng.randint(1, max(2, n // 3)) for j in range(_Q)]")
    if "tags__q" in need and "items" in need:
        lines.append("    try:")
        lines.append("        inp['tags__q'] = list(inp['items'][0]['tags'])")
        lines.append("    except Exception:")
        lines.append("        pass")
    if "groups__q" in need and "items" in need:
        lines.append("    try:")
        lines.append("        first = inp['items'][0]")
        lines.append("        toks = first.split() if isinstance(first, str) "
                     "else first.get('tags', ['w0'])")
        lines.append("        inp['groups__q'] = [toks[:2], toks[:3]]")
        lines.append("    except Exception:")
        lines.append("        pass")
    lines.append("    return inp")
    make_input_src = "\n".join(lines) + "\n"

    header = (f'"""AUTO-GENERATED harness for {tid} '
              f'(see scripts/gen_harnesses.py).\n\n'
              f'Reference signatures: {sigs}\n"""\n')
    body = (header + HELPERS + "\n" + make_input_src + "\n"
            + RUNTIME.replace("__SPEC__", repr(spec)))
    return body


def selftest(task, src):
    ns = {"__name__": "harness"}
    try:
        exec(compile(src, "<harness>", "exec"), ns)
        ref = {}
        exec(compile(task["reference_solution"]["code"], "<ref>", "exec"), ref)
        inp = ns["make_input"]("small", random.Random(1234))
        out = ns["run"](ref, inp)
        json.dumps(out, default=str)
        vals = list(out.values())
        errs = [v for v in vals if isinstance(v, dict) and "__error__" in v]
        if errs:
            return False, f"reference error {errs[0]['__error__']}"
        if all(v is None for v in vals):
            return False, "no non-None outputs"
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category", nargs="?")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cats = [args.category] if args.category else \
        sorted(p.parent.name for p in (REPO / "dataset").glob("*/dataset.json"))
    stats = {"written": 0, "exists": 0, "failed": []}
    for cat in cats:
        dfile = REPO / "dataset" / cat / "dataset.json"
        try:
            data = json.loads(dfile.read_text(encoding="utf-8"))
        except Exception as e:
            stats["failed"].append((cat, "-", f"dataset_unreadable: {e}"))
            continue
        hdir = HARNESS_DIR / cat
        for task in data.get("tasks", []):
            tid = task["task_id"]
            hp = hdir / f"{tid}.py"
            if hp.is_file() and not args.force:
                stats["exists"] += 1
                continue
            src = build_source(task)
            if src is None:
                stats["failed"].append((tid, cat, "no_reference_signatures"))
                continue
            ok, err = selftest(task, src)
            if not ok:
                stats["failed"].append((tid, cat, f"selftest: {err}"))
                continue
            hdir.mkdir(parents=True, exist_ok=True)
            hp.write_text(src, encoding="utf-8")
            stats["written"] += 1

    print(f"[gen_harnesses] written={stats['written']} existing={stats['exists']}")
    for tid, cat, why in stats["failed"]:
        print(f"  FAILED {tid} ({cat}): {why}")


if __name__ == "__main__":
    main()
