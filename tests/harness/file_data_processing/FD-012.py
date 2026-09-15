"""AUTO-GENERATED harness for FD-012 (see scripts/gen_harnesses.py).

Reference signatures: [('solve', 'data')]
"""
import random

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

def make_input(scale, rng):
    n = {'small': 300, 'medium': 4000, 'large': 15000}.get(scale, 300)
    inp = {}
    inp['data__q'] = [_word(rng) for _ in range(_Q)]
    return inp



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


SPEC = [('solve', [('data', 'qscalar')])]


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
