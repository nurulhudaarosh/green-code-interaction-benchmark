"""AUTO-GENERATED templated harness for TL-012 (see scripts/gen_harnesses.py).

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
TEMPLATE = {"rows": [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}, {"id": 6}, {"id": 7}, {"id": 8}, {"id": 9}, {"id": 10}, {"id": 11}, {"id": 12}, {"id": 13}, {"id": 14}, {"id": 15}, {"id": 16}, {"id": 17}, {"id": 18}, {"id": 19}, {"id": 20}, {"id": 21}, {"id": 22}, {"id": 23}, {"id": 24}, {"id": 25}, {"id": 26}, {"id": 27}, {"id": 28}, {"id": 29}, {"id": 30}, {"id": 31}, {"id": 32}, {"id": 33}, {"id": 34}, {"id": 35}, {"id": 36}, {"id": 37}, {"id": 38}, {"id": 39}, {"id": 40}, {"id": 41}, {"id": 42}, {"id": 43}, {"id": 44}, {"id": 45}, {"id": 46}, {"id": 47}, {"id": 48}, {"id": 49}, {"id": 50}, {"id": 51}, {"id": 52}, {"id": 53}, {"id": 54}, {"id": 55}, {"id": 56}, {"id": 57}, {"id": 58}, {"id": 59}, {"id": 60}, {"id": 61}, {"id": 62}, {"id": 63}, {"id": 64}, {"id": 65}, {"id": 66}, {"id": 67}, {"id": 68}, {"id": 69}, {"id": 70}, {"id": 71}, {"id": 72}, {"id": 73}, {"id": 74}, {"id": 75}, {"id": 76}, {"id": 77}, {"id": 78}, {"id": 79}, {"id": 80}, {"id": 81}, {"id": 82}, {"id": 83}, {"id": 84}, {"id": 85}, {"id": 86}, {"id": 87}, {"id": 88}, {"id": 89}, {"id": 90}, {"id": 91}, {"id": 92}, {"id": 93}, {"id": 94}, {"id": 95}, {"id": 96}, {"id": 97}, {"id": 98}, {"id": 99}], "columns": ["id"]}
PARAMS = ('format_log_table', ['rows', 'columns'])


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
