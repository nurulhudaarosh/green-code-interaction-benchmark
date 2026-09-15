"""Load generated code, run the reference solution, compare outputs."""

import importlib.util
import json
import traceback


def load_module(path, name="candidate_under_test"):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_reference(task):
    """Execute the task's reference_solution.code into a fresh namespace."""
    code = (task.get("reference_solution") or {}).get("code")
    if not code:
        raise ValueError("task has no reference_solution.code")
    ns = {}
    exec(compile(code, "<reference>", "exec"), ns)
    return ns


def reference_names(ns):
    import types
    return [n for n, v in ns.items() if isinstance(v, types.FunctionType)]


def compare(a, b):
    """Deep-ish comparison of harness outputs (must be JSON-serializable).

    Shape-tolerant: the dataset references often return dicts
    ({"max_overlap": ..., "peak_times": ...}) while member code returns
    tuples/lists of the same values ((max, times)). When one side is a
    dict and the other a list, the dict's values (insertion order) are
    aligned with the list before comparing.
    """
    if _json_eq(a, b):
        return True
    return _shape_eq(a, b)


def _json_eq(a, b):
    try:
        return json.dumps(a, sort_keys=True, default=str) == json.dumps(
            b, sort_keys=True, default=str
        )
    except (TypeError, ValueError):
        return repr(a) == repr(b)


def _shape_eq(a, b):
    if isinstance(a, dict) and isinstance(b, (list, tuple)):
        return _shape_eq(list(a.values()), b)
    if isinstance(b, dict) and isinstance(a, (list, tuple)):
        return _shape_eq(a, list(b.values()))
    if isinstance(a, dict) and isinstance(b, dict):
        return (set(a.keys()) == set(b.keys())
                and all(_shape_eq(a[k], b[k]) for k in a))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return (len(a) == len(b)
                and all(_shape_eq(x, y) for x, y in zip(a, b)))
    return _json_eq(a, b)


def safe_call(fn, args, kwargs, errors):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        errors.append(f"{type(e).__name__}: {e}")
        return None
