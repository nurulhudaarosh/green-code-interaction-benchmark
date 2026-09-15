"""AUTO-GENERATED templated harness for TL-007 (see scripts/gen_harnesses.py).

Inputs are the task public tests, tiled up per scale.
"""

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


SCALES = ["small", "medium", "large"]
TEMPLATE = {"records": [{"timestamp": 0, "level": "ERROR"}, {"timestamp": 1, "level": "ERROR"}, {"timestamp": 2, "level": "ERROR"}, {"timestamp": 3, "level": "ERROR"}, {"timestamp": 4, "level": "ERROR"}, {"timestamp": 5, "level": "ERROR"}, {"timestamp": 6, "level": "ERROR"}, {"timestamp": 7, "level": "ERROR"}, {"timestamp": 8, "level": "ERROR"}, {"timestamp": 9, "level": "ERROR"}, {"timestamp": 10, "level": "ERROR"}, {"timestamp": 11, "level": "ERROR"}, {"timestamp": 12, "level": "ERROR"}, {"timestamp": 13, "level": "ERROR"}, {"timestamp": 14, "level": "ERROR"}, {"timestamp": 15, "level": "ERROR"}, {"timestamp": 16, "level": "ERROR"}, {"timestamp": 17, "level": "ERROR"}, {"timestamp": 18, "level": "ERROR"}, {"timestamp": 19, "level": "ERROR"}, {"timestamp": 20, "level": "ERROR"}, {"timestamp": 21, "level": "ERROR"}, {"timestamp": 22, "level": "ERROR"}, {"timestamp": 23, "level": "ERROR"}, {"timestamp": 24, "level": "ERROR"}, {"timestamp": 25, "level": "ERROR"}, {"timestamp": 26, "level": "ERROR"}, {"timestamp": 27, "level": "ERROR"}, {"timestamp": 28, "level": "ERROR"}, {"timestamp": 29, "level": "ERROR"}, {"timestamp": 30, "level": "ERROR"}, {"timestamp": 31, "level": "ERROR"}, {"timestamp": 32, "level": "ERROR"}, {"timestamp": 33, "level": "ERROR"}, {"timestamp": 34, "level": "ERROR"}, {"timestamp": 35, "level": "ERROR"}, {"timestamp": 36, "level": "ERROR"}, {"timestamp": 37, "level": "ERROR"}, {"timestamp": 38, "level": "ERROR"}, {"timestamp": 39, "level": "ERROR"}, {"timestamp": 40, "level": "ERROR"}, {"timestamp": 41, "level": "ERROR"}, {"timestamp": 42, "level": "ERROR"}, {"timestamp": 43, "level": "ERROR"}, {"timestamp": 44, "level": "ERROR"}, {"timestamp": 45, "level": "ERROR"}, {"timestamp": 46, "level": "ERROR"}, {"timestamp": 47, "level": "ERROR"}, {"timestamp": 48, "level": "ERROR"}, {"timestamp": 49, "level": "ERROR"}, {"timestamp": 50, "level": "ERROR"}, {"timestamp": 51, "level": "ERROR"}, {"timestamp": 52, "level": "ERROR"}, {"timestamp": 53, "level": "ERROR"}, {"timestamp": 54, "level": "ERROR"}, {"timestamp": 55, "level": "ERROR"}, {"timestamp": 56, "level": "ERROR"}, {"timestamp": 57, "level": "ERROR"}, {"timestamp": 58, "level": "ERROR"}, {"timestamp": 59, "level": "ERROR"}, {"timestamp": 60, "level": "ERROR"}, {"timestamp": 61, "level": "ERROR"}, {"timestamp": 62, "level": "ERROR"}, {"timestamp": 63, "level": "ERROR"}, {"timestamp": 64, "level": "ERROR"}, {"timestamp": 65, "level": "ERROR"}, {"timestamp": 66, "level": "ERROR"}, {"timestamp": 67, "level": "ERROR"}, {"timestamp": 68, "level": "ERROR"}, {"timestamp": 69, "level": "ERROR"}, {"timestamp": 70, "level": "ERROR"}, {"timestamp": 71, "level": "ERROR"}, {"timestamp": 72, "level": "ERROR"}, {"timestamp": 73, "level": "ERROR"}, {"timestamp": 74, "level": "ERROR"}, {"timestamp": 75, "level": "ERROR"}, {"timestamp": 76, "level": "ERROR"}, {"timestamp": 77, "level": "ERROR"}, {"timestamp": 78, "level": "ERROR"}, {"timestamp": 79, "level": "ERROR"}, {"timestamp": 80, "level": "ERROR"}, {"timestamp": 81, "level": "ERROR"}, {"timestamp": 82, "level": "ERROR"}, {"timestamp": 83, "level": "ERROR"}, {"timestamp": 84, "level": "ERROR"}, {"timestamp": 85, "level": "ERROR"}, {"timestamp": 86, "level": "ERROR"}, {"timestamp": 87, "level": "ERROR"}, {"timestamp": 88, "level": "ERROR"}, {"timestamp": 89, "level": "ERROR"}, {"timestamp": 90, "level": "ERROR"}, {"timestamp": 91, "level": "ERROR"}, {"timestamp": 92, "level": "ERROR"}, {"timestamp": 93, "level": "ERROR"}, {"timestamp": 94, "level": "ERROR"}, {"timestamp": 95, "level": "ERROR"}, {"timestamp": 96, "level": "ERROR"}, {"timestamp": 97, "level": "ERROR"}, {"timestamp": 98, "level": "ERROR"}, {"timestamp": 99, "level": "ERROR"}], "window_size": 10, "threshold": 0.8}
PARAMS = ('detect_error_bursts', ['records', 'window_size', 'threshold'])


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
