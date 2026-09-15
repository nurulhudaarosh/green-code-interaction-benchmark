"""AUTO-GENERATED manual-template harness for RA-019 (scripts/manual_harness_templates.json)."""

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
SCALE_LENS = {'small': 30, 'medium': 200, 'large': 600}
FUNCS = [{'name': 'plan_routes', 'args': {'locations': ['depot', 'a', 'b', 'c'], 'distances': {'depot': {'depot': 0, 'a': 5, 'b': 7, 'c': 9}, 'a': {'depot': 5, 'a': 0, 'b': 3, 'c': 4}, 'b': {'depot': 7, 'a': 3, 'b': 0, 'c': 2}, 'c': {'depot': 9, 'a': 4, 'b': 2, 'c': 0}}, 'deliveries': [{'id': 'd1', 'destination': 'a', 'weight': 3}, {'id': 'd2', 'destination': 'b', 'weight': 4}, {'id': 'd3', 'destination': 'c', 'weight': 2}], 'capacity': 10, 'depot': 'depot'}, 'tile': ['deliveries']}]


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
