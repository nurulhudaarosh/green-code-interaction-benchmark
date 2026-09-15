"""Shared helpers for auto-generated task harnesses.

Imported by the generated harness files (tests/harness/<cat>/<TASK>.py)
so that name resolution, input adaptation and output normalization behave
identically across the templated / manual / file harness runtimes.
"""

_EXCLUDE = ("main", "self_test", "run_test", "demo", "setup", "teardown")


def _items(module):
    return module.items() if isinstance(module, dict) else [
        (n, getattr(module, n)) for n in dir(module)]


def get(module, name):
    if isinstance(module, dict):
        return module.get(name)
    return getattr(module, name, None)


def _sig_of(fn):
    import inspect
    try:
        return list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return None


def _callable_with(ps, nargs, skip_first=False):
    if ps is None:
        return False
    if skip_first and ps:
        ps = ps[1:]
    pos = [p for p in ps if p.kind in (p.POSITIONAL_ONLY,
                                       p.POSITIONAL_OR_KEYWORD)]
    req = sum(1 for p in pos if p.default is p.empty)
    var = any(p.kind == p.VAR_POSITIONAL for p in ps)
    return var or req <= nargs <= len(pos) or (var and nargs >= req)


def _class_entry(cls, nargs):
    """Wrap a class into an entry callable: instantiate (with the leading
    args if the constructor wants data) and call the best matching public
    method with the rest."""
    ps = _sig_of(cls.__init__ or cls.__new__)
    creq = 0
    if ps:
        cpos = [p for p in ps[1:] if p.kind in (p.POSITIONAL_ONLY,
                                                p.POSITIONAL_OR_KEYWORD)]
        creq = sum(1 for p in cpos if p.default is p.empty)
    methods = []
    for n in dir(cls):
        if n.startswith("_") or n in _EXCLUDE:
            continue
        o = getattr(cls, n)
        if not callable(o) or isinstance(o, type):
            continue
        mps = _sig_of(o)
        if mps is None:
            continue
        mpos = [p for p in mps[1:] if p.kind in (p.POSITIONAL_ONLY,
                                                 p.POSITIONAL_OR_KEYWORD)]
        mreq = sum(1 for p in mpos if p.default is p.empty)
        mvar = any(p.kind == p.VAR_POSITIONAL for p in mps)
        if mvar or mreq <= nargs:
            methods.append((mreq, n))
    if not methods:
        return None
    methods.sort(key=lambda m: (-m[0], m[1]))

    def entry(*args):
        if creq <= 0:
            obj = cls()
            rest = args
        elif creq <= len(args):
            obj = cls(*args[:creq])
            rest = args[creq:]
        else:
            obj = cls(*args)
            rest = ()
        # try preferred method, then the others
        for _, mname in methods:
            try:
                return getattr(obj, mname)(*rest)
            except TypeError:
                continue
        raise TypeError(f"no method of {cls.__name__} accepts the input")
    return entry


def _is_typing_artifact(o):
    """typing generics (Dict, List, ...), decorators (dataclass) and other
    imported machinery are callable but must never be picked as the task
    entry point. Functions exec'd from source have __module__ None and
    are NOT artifacts."""
    mod = getattr(o, "__module__", None)
    return bool(mod) and mod in ("typing", "dataclasses", "abc",
                                 "collections.abc", "importlib", "functools",
                                 "itertools", "operator")


def _req_of(fn):
    ps = _sig_of(fn)
    if ps is None:
        return 0
    pos = [p for p in ps if p.kind in (p.POSITIONAL_ONLY,
                                       p.POSITIONAL_OR_KEYWORD)]
    return sum(1 for p in pos if p.default is p.empty)


def _tier_of(ps, nargs):
    """1 = directly callable with nargs; 2 = needs more args than nargs
    (input adaptation may split a wrapper dict into them); None = no."""
    if ps is None:
        return None
    pos = [p for p in ps if p.kind in (p.POSITIONAL_ONLY,
                                       p.POSITIONAL_OR_KEYWORD)]
    req = sum(1 for p in pos if p.default is p.empty)
    var = any(p.kind == p.VAR_POSITIONAL for p in ps)
    if var or req <= nargs <= len(pos):
        return 1
    if nargs < req <= nargs + 8:
        return 2
    return None


def resolve_entry(module, fname, nargs):
    """Find the task entry point in a module (candidate or reference
    namespace), tolerant to naming and structure:

    1. the exact function name from the reference
    2. any public function callable with nargs arguments (tier 1), or
       needing a few more args that input adaptation can supply by
       splitting the wrapper dict (tier 2); own-module functions first
    3. a public class instantiated and called via its best method
    """
    fn = get(module, fname)
    if callable(fn) and not isinstance(fn, type) \
            and not _is_typing_artifact(fn):
        return fn
    modname = getattr(module, "__name__", None)
    own, foreign, classes = [], [], []
    for n, o in _items(module):
        if n.startswith("_") or n in _EXCLUDE or n.startswith("test_"):
            continue
        if isinstance(o, type):
            classes.append((n, o))
            continue
        if not callable(o) or _is_typing_artifact(o):
            continue
        tier = _tier_of(_sig_of(o), nargs)
        if tier:
            om = getattr(o, "__module__", None)
            (own if om in (modname, None) else foreign).append((tier, n, o))
    for cands in (own, foreign):
        if cands:
            cands.sort(key=lambda c: (c[0], _req_of(c[2]) if c[0] == 2
                                      else -_req_of(c[2]), c[1]))
            return cands[0][2]
    for _, cls in sorted(classes):
        if _is_typing_artifact(cls):
            continue
        e = _class_entry(cls, nargs)
        if e is not None:
            return e
    return None


def adapt_call(fn, args):
    """Call fn with the canonical args; when the member's implementation
    expects a different shape (raw values instead of a wrapper dict),
    retry with keyword-unwrap and positional-unwrap. Raises the first
    error if nothing works."""
    first = None
    try:
        return fn(*args)
    except Exception as e:  # noqa: BLE001
        first = e
    dicts = [a for a in args if isinstance(a, dict)]
    if dicts:
        kw = {}
        for a in dicts:
            kw.update(a)
        try:
            return fn(**kw)
        except Exception:  # noqa: BLE001
            pass
        flat = []
        for a in args:
            if isinstance(a, dict):
                flat.extend(a.values())
            else:
                flat.append(a)
        try:
            return fn(*flat)
        except Exception:  # noqa: BLE001
            pass
    raise first


def jsonable(v):
    """Make any return value JSON-comparable (sets sorted, tuples listed,
    dataclasses/namedtypes dictified)."""
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted(jsonable(x) for x in v)
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    try:
        import dataclasses
        if dataclasses.is_dataclass(v) and not isinstance(v, type):
            return jsonable(dataclasses.asdict(v))
    except Exception:  # noqa: BLE001
        pass
    if hasattr(v, "_asdict"):
        try:
            return jsonable(v._asdict())
        except Exception:  # noqa: BLE001
            pass
    if hasattr(v, "__dict__") and not isinstance(v, type):
        try:
            return jsonable(vars(v))
        except Exception:  # noqa: BLE001
            pass
    return repr(v)
