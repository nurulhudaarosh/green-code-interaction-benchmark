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
    """Top-level function signatures with balanced-paren parameter lists
    (regex [^)]* breaks on tuple defaults like pad_color=(0, 0, 0))."""
    out = []
    for m in re.finditer(r"^def\s+(\w+)\s*\(", code, re.M):
        name = m.group(1)
        i = m.end()
        depth, j, n = 1, i, len(code)
        while j < n and depth:
            c = code[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            j += 1
        if depth == 0:
            out.append((name, code[i:j - 1]))
    return out


def params_of(raw):
    """Return [(name, default_repr_or_None), ...], splitting parameters on
    top-level commas only (defaults may contain tuples/calls)."""
    parts, buf, depth = [], "", 0
    for c in raw:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += c
    if buf.strip():
        parts.append(buf)
    out = []
    for p in parts:
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
    import signal

    def _timeout(signum, frame):
        raise TimeoutError("selftest exceeded 60s")

    ns = {"__name__": "harness"}
    old = None
    try:
        old = signal.signal(signal.SIGALRM, _timeout)
        signal.alarm(60)
        exec(compile(src, "<harness>", "exec"), ns)
        ref = {}
        exec(compile(task["reference_solution"]["code"], "<ref>", "exec"), ref)
        inp = ns["make_input"]("small", random.Random(1234))
        out = ns["run"](ref, inp)
        json.dumps(out, default=str)
        errs = _find_errors(out)
        if errs:
            return False, f"reference error {errs[0]}"
        if all(v is None for v in out.values()):
            return False, "no non-None outputs"
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        signal.alarm(0)
        if old is not None:
            signal.signal(signal.SIGALRM, old)


def _find_errors(v, depth=0):
    """Recursively collect {"__error__": ...} dicts (incl. inside lists)."""
    if depth > 5:
        return []
    if isinstance(v, dict):
        if "__error__" in v:
            return [v["__error__"]]
        out = []
        for x in v.values():
            out += _find_errors(x, depth + 1)
        return out
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            out += _find_errors(x, depth + 1)
        return out
    return []


# --------------------------------------------------------------------------
# public-test-templated harnesses (much more robust than heuristics)
# --------------------------------------------------------------------------

HARNESS_IMPORTS = '''
import sys as _sys
try:
    from runner.harness_utils import resolve_entry, adapt_call, jsonable
except ImportError:  # loaded as a standalone file
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(_sys.argv[0])) if _sys.argv else "."
    for _up in range(4):
        if _os.path.isdir(_os.path.join(_here, "runner")):
            _sys.path.insert(0, _here)
            break
        _here = _os.path.dirname(_here)
    from runner.harness_utils import resolve_entry, adapt_call, jsonable
'''

TEMPLATE_RUNTIME = HARNESS_IMPORTS + '''

SCALES = ["small", "medium", "large"]
TEMPLATE = __TEMPLATE__
PARAMS = __PARAMS__


def _scale(v, n, depth=0):
    """Tile the dominant list of the template up to length n so the
    workload grows with the scale; everything else is kept as-is."""
    if isinstance(v, list) and v:
        return [v[i % len(v)] for i in range(n)]
    if isinstance(v, dict) and depth < 4:
        lists = [k for k, x in v.items() if isinstance(x, list) and x]
        if lists:
            big = max(lists, key=lambda k: len(v[k]))
            return {k: (_scale(x, n, depth + 1) if k == big else x)
                    for k, x in v.items()}
        dicts = [k for k, x in v.items() if isinstance(x, dict)]
        if dicts:
            k = dicts[0]
            return {kk: (_scale(x, n, depth + 1) if kk == k else x)
                    for kk, x in v.items()}
    return v


def make_input(scale, rng):
    n = {"small": 300, "medium": 4000, "large": 15000}.get(scale, 300)
    return {p: _scale(v, n) for p, v in TEMPLATE.items()}


def run(module, inp):
    out = {}
    for fname, params in [(PARAMS[0], PARAMS[1])]:
        fn = resolve_entry(module, fname, len(params))
        if fn is None:
            out[fname] = None
            continue
        call = [inp[p] for p in params]
        try:
            out[fname] = jsonable(adapt_call(fn, call))
        except Exception as e:
            out[fname] = {"__error__": f"{type(e).__name__}: {e}"}
    return out
'''


def template_of(task):
    """Best public-test input (the intended input shape). Prefers the
    largest non-empty input — the most representative of a normal
    workload — over boundary/empty cases."""
    tests = (task.get("tests") or {}).get("public_tests") or []
    best, best_size = None, -1
    for t in tests:
        if not isinstance(t, dict):
            continue
        inp = t.get("input")
        if inp in (None, [], {}, ""):
            continue
        try:
            size = len(json.dumps(inp, default=str))
        except (TypeError, ValueError):
            size = 0
        if size > best_size:
            best, best_size = inp, size
    return best


def _default_type(default_repr):
    """Best-effort type of a default value given its repr string."""
    import ast as _ast
    try:
        v = _ast.literal_eval(default_repr)
    except (ValueError, SyntaxError):
        return None
    return type(v)


def _type_ok(value, default_repr):
    """True if value could sensibly sit in a parameter whose default is
    default_repr (str vs list etc.)."""
    dt = _default_type(default_repr)
    if dt is None:
        return True
    vt = type(value)
    if dt is float and vt is int:
        return True
    return vt is dt


def map_template(inp, param_names, param_defaults=None):
    """Map a public-test input onto the function parameters.

    Returns {param: value} or None. Handles: dict keyed by param names,
    whole-input for the single non-default param, list positional args
    (validated against the defaulted params' types), single scalar.
    """
    names = list(param_names)
    defaults = list(param_defaults) if param_defaults is not None \
        else [None] * len(names)
    non_default = [n for n, d in zip(names, defaults) if d is None]
    if isinstance(inp, dict):
        if set(inp.keys()) & set(names):
            if set(inp.keys()) <= set(names):
                return {n: inp[n] for n in names if n in inp}
            return None
        if len(non_default) == 1:
            return {non_default[0]: inp}
        if len(names) == 1:
            return {names[0]: inp}
        return None
    if isinstance(inp, list) and len(inp) == len(names) and len(names) > 1:
        # positional over ALL params only when every defaulted param's
        # value type matches its default (guards against a list-of-lists
        # that is really one aggregate argument)
        if all(_type_ok(v, d) for v, d in zip(inp, defaults) if d is not None):
            return dict(zip(names, inp))
        if len(non_default) == 1:
            return {non_default[0]: inp}
        return None
    if len(non_default) == 1:
        return {non_default[0]: inp}
    if isinstance(inp, list) and len(inp) == len(non_default):
        return dict(zip(non_default, inp))
    if len(names) == 1:
        return {names[0]: inp}
    return None


def build_templated_source(task, sigs):
    """Harness whose inputs come from the task's own public tests,
    scaled per size. Only for single-function references."""
    if len(sigs) != 1:
        return None
    tmpl = template_of(task)
    if tmpl is None:
        return None
    fname, raw = sigs[0]
    pairs = params_of(raw)
    params = [p for p, _ in pairs]
    defaults = [d for _, d in pairs]
    mapped = map_template(tmpl, params, defaults)
    if mapped is None:
        return None
    try:
        body = json.dumps(mapped, ensure_ascii=False)
    except (TypeError, ValueError):
        return None
    header = (f'"""AUTO-GENERATED templated harness for {task["task_id"]} '
              f'(see scripts/gen_harnesses.py).\n\n'
              f'Inputs are the task public tests, tiled up per scale.\n"""\n')
    src = (header
           + TEMPLATE_RUNTIME.replace("__TEMPLATE__", body)
           .replace("__PARAMS__", repr((fname, [p for p in mapped]))))
    return src


# --------------------------------------------------------------------------
# file-system harnesses (input_dir/output_dir style tasks, e.g. IM/FD)
# --------------------------------------------------------------------------

FILE_RUNTIME = HARNESS_IMPORTS + '''
import hashlib, os as _os, shutil as _sh
import tempfile as _tf

SCALES = ["small", "medium", "large"]
_N = {"small": 24, "medium": 120, "large": 400}
SPEC = __SPEC__          # (fname, [(kind, value)]) kind: in|out|file|outpath|const
MODE = __MODE__          # "images" | "txt"
_prev_dir = None


def _noise_img(rng, w=48, h=32):
    from PIL import Image
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (rng.randint(0, 255), rng.randint(0, 255),
                        rng.randint(0, 255))
    return img


def _fill_images(dirpath, n, rng):
    n_png = max(1, int(n * 0.8))
    n_jpg = max(1, n - n_png)
    for i in range(n_png):
        _noise_img(rng).save(_os.path.join(dirpath, f"img_{i:04d}.png"))
    for i in range(n_jpg):
        _noise_img(rng).save(_os.path.join(dirpath, f"photo_{i:04d}.jpg"),
                             quality=88)
    for name in ("r.png", "g.png", "b.png", "wm.png"):
        _noise_img(rng).save(_os.path.join(dirpath, name))
    with open(_os.path.join(dirpath, "notes.txt"), "w") as f:
        f.write("not an image\\n")


def _fill_txt(dirpath, n, rng):
    pool = ["alpha beta gamma", "delta epsilon zeta", "eta theta iota",
            "kappa lambda mu"]
    for i in range(n):
        c = pool[i % len(pool)] + (" extra" if i % 3 == 0 else "")
        sub = _os.path.join(dirpath, f"d{i % 3}")
        _os.makedirs(sub, exist_ok=True)
        with open(_os.path.join(sub, f"f{i:04d}.txt"), "w") as f:
            f.write(c + "\\n")
        if i % 5 == 0:
            with open(_os.path.join(sub, f"f{i:04d}.md"), "w") as f:
                f.write("markdown ignored\\n")


def make_input(scale, rng):
    global _prev_dir
    if _prev_dir and _os.path.isdir(_prev_dir):
        _sh.rmtree(_prev_dir, ignore_errors=True)
    d = _tf.mkdtemp(prefix="gcb_in_")
    n = _N.get(scale, 24)
    if MODE == "txt":
        _fill_txt(d, n, rng)
    else:
        _fill_images(d, n, rng)
    _prev_dir = d
    return {"__indir__": d}


def run(module, inp):
    work = _tf.mkdtemp(prefix="gcb_run_")
    try:
        ind = _os.path.join(work, "in")
        _sh.copytree(inp["__indir__"], ind)
        out = _os.path.join(work, "out")
        _os.makedirs(out, exist_ok=True)
        fname = SPEC[0]
        fn = resolve_entry(module, fname, len(SPEC[1]))
        if fn is None:
            return {fname: None}
        args = []
        for kind, val in SPEC[1]:
            if kind == "in":
                args.append(ind)
            elif kind == "out":
                args.append(out)
            elif kind == "file":
                args.append(_os.path.join(ind, val))
            elif kind == "outpath":
                args.append(_os.path.join(out, val))
            else:
                args.append(val)
        try:
            ret = fn(*args)
        except Exception as e:
            return {fname: {"__error__": f"{type(e).__name__}: {e}"}}
        listing = []
        for root, _, fs in _os.walk(out):
            for f in sorted(fs):
                p = _os.path.join(root, f)
                rel = _os.path.relpath(p, out)
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
                listing.append([rel, h])
        return {fname: [jsonable(ret), sorted(listing)]}
    finally:
        _sh.rmtree(work, ignore_errors=True)
'''

DIR_PARAMS = ("input_dir", "root", "cache_dir", "archive_dir")
OUT_PARAMS = ("output_dir",)
FILE_PARAMS = {"image_path": "img_0000.png", "input_path": "img_0000.png",
               "watermark_path": "wm.png", "r_path": "r.png",
               "g_path": "g.png", "b_path": "b.png"}
OUTPATH_DEFAULT = "result.png"

FILE_CONSTS = {
    "target_size": (64, 48), "crop_size": (32, 24), "thumb_size": (64, 48),
    "widths": [32, 64, 128], "radius": 2, "angle_degrees": 30, "quality": 85,
    "kernel_size": 3, "hash_size": 8, "max_hamming": 5, "threshold": 0.2,
    "opacity": 0.5, "position": "bottom-right", "margin": 10,
    "patch_size": (8, 8), "stride": (4, 4), "max_dim": 128,
    "target_format": "PNG", "columns": 4, "pad_color": (0, 0, 0),
    "chunk_size": 65536, "tags": {"title": "Test Image", "author": "bench"},
}


def build_file_source(task, sigs):
    """Auto harness for tasks whose main function reads files/dirs."""
    main = None
    for fname, raw in sigs:
        if fname.startswith("_"):
            continue
        params = params_of(raw)
        pnames = [p for p, _ in params]
        if (any(p in DIR_PARAMS for p in pnames)
                or any(p in FILE_PARAMS for p in pnames)
                or "output_path" in pnames):
            main = (fname, params)
            break
    if main is None:
        return None
    fname, params = main
    mode = "txt" if any(p == "root" for p, _ in params) else "images"
    spec_args = []
    for p, default in params:
        if p in DIR_PARAMS:
            spec_args.append(("in", None))
        elif p in OUT_PARAMS:
            spec_args.append(("out", None))
        elif p in FILE_PARAMS:
            spec_args.append(("file", FILE_PARAMS[p]))
        elif p == "output_path":
            spec_args.append(("outpath", OUTPATH_DEFAULT))
        elif default is not None:
            try:
                import ast as _ast
                spec_args.append(("const", _ast.literal_eval(default)))
            except (ValueError, SyntaxError):
                return None
        elif p in FILE_CONSTS:
            spec_args.append(("const", FILE_CONSTS[p]))
        else:
            return None
    header = (f'"""AUTO-GENERATED file harness for {task["task_id"]} '
              f'(see scripts/gen_harnesses.py).\n\n'
              f'Main function: {fname}; input files are generated per '
              f'scale.\n"""\n')
    return (header + FILE_RUNTIME
            .replace("__SPEC__", repr((fname, spec_args)))
            .replace("__MODE__", repr(mode)))


# --------------------------------------------------------------------------
# manual templates (tasks without usable public tests)
# --------------------------------------------------------------------------

MANUAL_RUNTIME = HARNESS_IMPORTS + '''

SCALES = ["small", "medium", "large"]
SCALE_LENS = __SCALE_LENS__
FUNCS = __FUNCS__


def make_input(scale, rng):
    return {"n": SCALE_LENS.get(scale, 300)}


def _resolve(av, n, tile, raws):
    """Resolve one arg value: chain refs, square matrices, tiling.
    Lists of plain numbers are config values and are never tiled."""
    if isinstance(av, dict):
        if "__out__" in av:
            base = raws.get(av["__out__"])
            return base[av["pick"]] if ("pick" in av and base is not None) else base
        if "__square__" in av:
            b = av["__square__"]
            k = len(b)
            return [[b[i % k][j % k] for j in range(n)] for i in range(n)]
        return {k: _resolve(x, n, False, raws) for k, x in av.items()}
    if isinstance(av, list) and av and tile and not isinstance(av[0], (int, float)):
        return [av[i % len(av)] for i in range(n)]
    return av


def run(module, inp):
    n = inp["n"]
    outs = {}
    raws = {}
    for spec in FUNCS:
        fname = spec["name"]
        fn = resolve_entry(module, fname, len(spec["args"]))
        if fn is None:
            outs[fname] = None
            continue
        tile_any = set(spec.get("tile", [])) or None
        args = []
        for pname, av in spec["args"].items():
            do_tile = (tile_any is None) or (pname in tile_any)
            args.append(_resolve(av, n, do_tile, raws))
        try:
            raw = adapt_call(fn, args)
            raws[fname] = raw
            outs[fname] = jsonable(raw)
        except Exception as e:
            raws[fname] = None
            outs[fname] = {"__error__": f"{type(e).__name__}: {e}"}
    return outs
'''

MANUAL_TEMPLATES = REPO / "scripts" / "manual_harness_templates.json"


def load_manual_templates():
    try:
        return json.loads(MANUAL_TEMPLATES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def build_manual_source(task, sigs):
    entry = load_manual_templates().get(task["task_id"])
    if not entry:
        return None
    scale_lens = entry.get("scale_lens", {"small": 300, "medium": 4000,
                                          "large": 15000})
    header = (f'"""AUTO-GENERATED manual-template harness for '
              f'{task["task_id"]} (scripts/manual_harness_templates.json)."""\n')
    return (header + MANUAL_RUNTIME
            .replace("__SCALE_LENS__", repr(scale_lens))
            .replace("__FUNCS__", repr(entry["funcs"])))


def candidates(task):
    """Harness sources in priority order: public-test template, manual
    template, file harness, then heuristics."""
    out = []
    code = task.get("reference_solution", {}).get("code") or ""
    sigs = sigs_of(code)
    if not sigs:
        return out
    t = build_templated_source(task, sigs)
    if t:
        out.append(t)
    m = build_manual_source(task, sigs)
    if m:
        out.append(m)
    f = build_file_source(task, sigs)
    if f:
        out.append(f)
    h = build_source(task)
    if h:
        out.append(h)
    return out


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
            srcs = candidates(task)
            if not srcs:
                stats["failed"].append((tid, cat, "no_reference_signatures"))
                continue
            kept = None
            why = "no candidates"
            for src in srcs:
                ok, err = selftest(task, src)
                if ok:
                    kept = src
                    break
                why = f"selftest: {err}"
            if kept is None:
                stats["failed"].append((tid, cat, why))
                continue
            hdir.mkdir(parents=True, exist_ok=True)
            hp.write_text(src, encoding="utf-8")
            stats["written"] += 1

    print(f"[gen_harnesses] written={stats['written']} existing={stats['exists']}")
    for tid, cat, why in stats["failed"]:
        print(f"  FAILED {tid} ({cat}): {why}")


if __name__ == "__main__":
    main()
