"""AUTO-GENERATED templated harness for TL-006 (see scripts/gen_harnesses.py).

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
TEMPLATE = {"csv_str": "num\n0\nN/A\n2\nN/A\n4\nN/A\n6\nN/A\n8\nN/A\n10\nN/A\n12\nN/A\n14\nN/A\n16\nN/A\n18\nN/A\n20\nN/A\n22\nN/A\n24\nN/A\n26\nN/A\n28\nN/A\n30\nN/A\n32\nN/A\n34\nN/A\n36\nN/A\n38\nN/A\n40\nN/A\n42\nN/A\n44\nN/A\n46\nN/A\n48\nN/A\n50\nN/A\n52\nN/A\n54\nN/A\n56\nN/A\n58\nN/A\n60\nN/A\n62\nN/A\n64\nN/A\n66\nN/A\n68\nN/A\n70\nN/A\n72\nN/A\n74\nN/A\n76\nN/A\n78\nN/A\n80\nN/A\n82\nN/A\n84\nN/A\n86\nN/A\n88\nN/A\n90\nN/A\n92\nN/A\n94\nN/A\n96\nN/A\n98\nN/A"}
PARAMS = ('normalize_and_impute_csv', ['csv_str'])


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
