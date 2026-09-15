"""AUTO-GENERATED manual-template harness for RA-007 (scripts/manual_harness_templates.json)."""

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
SCALE_LENS = {'small': 50, 'medium': 300, 'large': 1000}
FUNCS = [{'name': 'process_invoices', 'args': {'invoices': [{'invoice_id': 'INV-001', 'customer': 'Acme Corp', 'tax_rate': 10.0, 'lines': [{'quantity': 2, 'price': 5.0}, {'quantity': 1, 'price': 3.5}]}, {'invoice_id': 'INV-002', 'customer': 'Globex', 'tax_rate': 5.0, 'lines': [{'quantity': 10, 'price': 2.25}]}]}}]


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
