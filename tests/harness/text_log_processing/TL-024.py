"""AUTO-GENERATED templated harness for TL-024 (see scripts/gen_harnesses.py).

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
TEMPLATE = {"records": [{"timestamp": 0.0, "value": 0.0}, {"timestamp": 10.0, "value": 1.0}, {"timestamp": 20.0, "value": 2.0}, {"timestamp": 30.0, "value": 3.0}, {"timestamp": 40.0, "value": 4.0}, {"timestamp": 50.0, "value": 5.0}, {"timestamp": 60.0, "value": 6.0}, {"timestamp": 70.0, "value": 7.0}, {"timestamp": 80.0, "value": 8.0}, {"timestamp": 90.0, "value": 9.0}, {"timestamp": 100.0, "value": 10.0}, {"timestamp": 110.0, "value": 11.0}, {"timestamp": 120.0, "value": 12.0}, {"timestamp": 130.0, "value": 13.0}, {"timestamp": 140.0, "value": 14.0}, {"timestamp": 150.0, "value": 15.0}, {"timestamp": 160.0, "value": 16.0}, {"timestamp": 170.0, "value": 17.0}, {"timestamp": 180.0, "value": 18.0}, {"timestamp": 190.0, "value": 19.0}, {"timestamp": 200.0, "value": 20.0}, {"timestamp": 210.0, "value": 21.0}, {"timestamp": 220.0, "value": 22.0}, {"timestamp": 230.0, "value": 23.0}, {"timestamp": 240.0, "value": 24.0}, {"timestamp": 250.0, "value": 25.0}, {"timestamp": 260.0, "value": 26.0}, {"timestamp": 270.0, "value": 27.0}, {"timestamp": 280.0, "value": 28.0}, {"timestamp": 290.0, "value": 29.0}, {"timestamp": 300.0, "value": 30.0}, {"timestamp": 310.0, "value": 31.0}, {"timestamp": 320.0, "value": 32.0}, {"timestamp": 330.0, "value": 33.0}, {"timestamp": 340.0, "value": 34.0}, {"timestamp": 350.0, "value": 35.0}, {"timestamp": 360.0, "value": 36.0}, {"timestamp": 370.0, "value": 37.0}, {"timestamp": 380.0, "value": 38.0}, {"timestamp": 390.0, "value": 39.0}, {"timestamp": 400.0, "value": 40.0}, {"timestamp": 410.0, "value": 41.0}, {"timestamp": 420.0, "value": 42.0}, {"timestamp": 430.0, "value": 43.0}, {"timestamp": 440.0, "value": 44.0}, {"timestamp": 450.0, "value": 45.0}, {"timestamp": 460.0, "value": 46.0}, {"timestamp": 470.0, "value": 47.0}, {"timestamp": 480.0, "value": 48.0}, {"timestamp": 490.0, "value": 49.0}, {"timestamp": 500.0, "value": 50.0}, {"timestamp": 510.0, "value": 51.0}, {"timestamp": 520.0, "value": 52.0}, {"timestamp": 530.0, "value": 53.0}, {"timestamp": 540.0, "value": 54.0}, {"timestamp": 550.0, "value": 55.0}, {"timestamp": 560.0, "value": 56.0}, {"timestamp": 570.0, "value": 57.0}, {"timestamp": 580.0, "value": 58.0}, {"timestamp": 590.0, "value": 59.0}, {"timestamp": 600.0, "value": 60.0}, {"timestamp": 610.0, "value": 61.0}, {"timestamp": 620.0, "value": 62.0}, {"timestamp": 630.0, "value": 63.0}, {"timestamp": 640.0, "value": 64.0}, {"timestamp": 650.0, "value": 65.0}, {"timestamp": 660.0, "value": 66.0}, {"timestamp": 670.0, "value": 67.0}, {"timestamp": 680.0, "value": 68.0}, {"timestamp": 690.0, "value": 69.0}, {"timestamp": 700.0, "value": 70.0}, {"timestamp": 710.0, "value": 71.0}, {"timestamp": 720.0, "value": 72.0}, {"timestamp": 730.0, "value": 73.0}, {"timestamp": 740.0, "value": 74.0}, {"timestamp": 750.0, "value": 75.0}, {"timestamp": 760.0, "value": 76.0}, {"timestamp": 770.0, "value": 77.0}, {"timestamp": 780.0, "value": 78.0}, {"timestamp": 790.0, "value": 79.0}, {"timestamp": 800.0, "value": 80.0}, {"timestamp": 810.0, "value": 81.0}, {"timestamp": 820.0, "value": 82.0}, {"timestamp": 830.0, "value": 83.0}, {"timestamp": 840.0, "value": 84.0}, {"timestamp": 850.0, "value": 85.0}, {"timestamp": 860.0, "value": 86.0}, {"timestamp": 870.0, "value": 87.0}, {"timestamp": 880.0, "value": 88.0}, {"timestamp": 890.0, "value": 89.0}, {"timestamp": 900.0, "value": 90.0}, {"timestamp": 910.0, "value": 91.0}, {"timestamp": 920.0, "value": 92.0}, {"timestamp": 930.0, "value": 93.0}, {"timestamp": 940.0, "value": 94.0}, {"timestamp": 950.0, "value": 95.0}, {"timestamp": 960.0, "value": 96.0}, {"timestamp": 970.0, "value": 97.0}, {"timestamp": 980.0, "value": 98.0}, {"timestamp": 990.0, "value": 99.0}], "expected_interval": 5.0, "gap_multiplier": 1.5}
PARAMS = ('interpolate_time_series', ['records', 'expected_interval', 'gap_multiplier'])


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
