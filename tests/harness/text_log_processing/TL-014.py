"""AUTO-GENERATED templated harness for TL-014 (see scripts/gen_harnesses.py).

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
TEMPLATE = {"logs": [{"timestamp": 0, "ip": "2.2.2.2", "path": "/page0"}, {"timestamp": 5, "ip": "2.2.2.2", "path": "/page1"}, {"timestamp": 10, "ip": "2.2.2.2", "path": "/page2"}, {"timestamp": 15, "ip": "2.2.2.2", "path": "/page3"}, {"timestamp": 20, "ip": "2.2.2.2", "path": "/page4"}, {"timestamp": 25, "ip": "2.2.2.2", "path": "/page5"}, {"timestamp": 30, "ip": "2.2.2.2", "path": "/page6"}, {"timestamp": 35, "ip": "2.2.2.2", "path": "/page7"}, {"timestamp": 40, "ip": "2.2.2.2", "path": "/page8"}, {"timestamp": 45, "ip": "2.2.2.2", "path": "/page9"}, {"timestamp": 50, "ip": "2.2.2.2", "path": "/page10"}, {"timestamp": 55, "ip": "2.2.2.2", "path": "/page11"}, {"timestamp": 60, "ip": "2.2.2.2", "path": "/page12"}, {"timestamp": 65, "ip": "2.2.2.2", "path": "/page13"}, {"timestamp": 70, "ip": "2.2.2.2", "path": "/page14"}, {"timestamp": 75, "ip": "2.2.2.2", "path": "/page15"}, {"timestamp": 80, "ip": "2.2.2.2", "path": "/page16"}, {"timestamp": 85, "ip": "2.2.2.2", "path": "/page17"}, {"timestamp": 90, "ip": "2.2.2.2", "path": "/page18"}, {"timestamp": 95, "ip": "2.2.2.2", "path": "/page19"}, {"timestamp": 100, "ip": "2.2.2.2", "path": "/page20"}, {"timestamp": 105, "ip": "2.2.2.2", "path": "/page21"}, {"timestamp": 110, "ip": "2.2.2.2", "path": "/page22"}, {"timestamp": 115, "ip": "2.2.2.2", "path": "/page23"}, {"timestamp": 120, "ip": "2.2.2.2", "path": "/page24"}, {"timestamp": 125, "ip": "2.2.2.2", "path": "/page25"}, {"timestamp": 130, "ip": "2.2.2.2", "path": "/page26"}, {"timestamp": 135, "ip": "2.2.2.2", "path": "/page27"}, {"timestamp": 140, "ip": "2.2.2.2", "path": "/page28"}, {"timestamp": 145, "ip": "2.2.2.2", "path": "/page29"}, {"timestamp": 150, "ip": "2.2.2.2", "path": "/page30"}, {"timestamp": 155, "ip": "2.2.2.2", "path": "/page31"}, {"timestamp": 160, "ip": "2.2.2.2", "path": "/page32"}, {"timestamp": 165, "ip": "2.2.2.2", "path": "/page33"}, {"timestamp": 170, "ip": "2.2.2.2", "path": "/page34"}, {"timestamp": 175, "ip": "2.2.2.2", "path": "/page35"}, {"timestamp": 180, "ip": "2.2.2.2", "path": "/page36"}, {"timestamp": 185, "ip": "2.2.2.2", "path": "/page37"}, {"timestamp": 190, "ip": "2.2.2.2", "path": "/page38"}, {"timestamp": 195, "ip": "2.2.2.2", "path": "/page39"}, {"timestamp": 200, "ip": "2.2.2.2", "path": "/page40"}, {"timestamp": 205, "ip": "2.2.2.2", "path": "/page41"}, {"timestamp": 210, "ip": "2.2.2.2", "path": "/page42"}, {"timestamp": 215, "ip": "2.2.2.2", "path": "/page43"}, {"timestamp": 220, "ip": "2.2.2.2", "path": "/page44"}, {"timestamp": 225, "ip": "2.2.2.2", "path": "/page45"}, {"timestamp": 230, "ip": "2.2.2.2", "path": "/page46"}, {"timestamp": 235, "ip": "2.2.2.2", "path": "/page47"}, {"timestamp": 240, "ip": "2.2.2.2", "path": "/page48"}, {"timestamp": 245, "ip": "2.2.2.2", "path": "/page49"}, {"timestamp": 250, "ip": "2.2.2.2", "path": "/page50"}, {"timestamp": 255, "ip": "2.2.2.2", "path": "/page51"}, {"timestamp": 260, "ip": "2.2.2.2", "path": "/page52"}, {"timestamp": 265, "ip": "2.2.2.2", "path": "/page53"}, {"timestamp": 270, "ip": "2.2.2.2", "path": "/page54"}, {"timestamp": 275, "ip": "2.2.2.2", "path": "/page55"}, {"timestamp": 280, "ip": "2.2.2.2", "path": "/page56"}, {"timestamp": 285, "ip": "2.2.2.2", "path": "/page57"}, {"timestamp": 290, "ip": "2.2.2.2", "path": "/page58"}, {"timestamp": 295, "ip": "2.2.2.2", "path": "/page59"}, {"timestamp": 300, "ip": "2.2.2.2", "path": "/page60"}, {"timestamp": 305, "ip": "2.2.2.2", "path": "/page61"}, {"timestamp": 310, "ip": "2.2.2.2", "path": "/page62"}, {"timestamp": 315, "ip": "2.2.2.2", "path": "/page63"}, {"timestamp": 320, "ip": "2.2.2.2", "path": "/page64"}, {"timestamp": 325, "ip": "2.2.2.2", "path": "/page65"}, {"timestamp": 330, "ip": "2.2.2.2", "path": "/page66"}, {"timestamp": 335, "ip": "2.2.2.2", "path": "/page67"}, {"timestamp": 340, "ip": "2.2.2.2", "path": "/page68"}, {"timestamp": 345, "ip": "2.2.2.2", "path": "/page69"}, {"timestamp": 350, "ip": "2.2.2.2", "path": "/page70"}, {"timestamp": 355, "ip": "2.2.2.2", "path": "/page71"}, {"timestamp": 360, "ip": "2.2.2.2", "path": "/page72"}, {"timestamp": 365, "ip": "2.2.2.2", "path": "/page73"}, {"timestamp": 370, "ip": "2.2.2.2", "path": "/page74"}, {"timestamp": 375, "ip": "2.2.2.2", "path": "/page75"}, {"timestamp": 380, "ip": "2.2.2.2", "path": "/page76"}, {"timestamp": 385, "ip": "2.2.2.2", "path": "/page77"}, {"timestamp": 390, "ip": "2.2.2.2", "path": "/page78"}, {"timestamp": 395, "ip": "2.2.2.2", "path": "/page79"}, {"timestamp": 400, "ip": "2.2.2.2", "path": "/page80"}, {"timestamp": 405, "ip": "2.2.2.2", "path": "/page81"}, {"timestamp": 410, "ip": "2.2.2.2", "path": "/page82"}, {"timestamp": 415, "ip": "2.2.2.2", "path": "/page83"}, {"timestamp": 420, "ip": "2.2.2.2", "path": "/page84"}, {"timestamp": 425, "ip": "2.2.2.2", "path": "/page85"}, {"timestamp": 430, "ip": "2.2.2.2", "path": "/page86"}, {"timestamp": 435, "ip": "2.2.2.2", "path": "/page87"}, {"timestamp": 440, "ip": "2.2.2.2", "path": "/page88"}, {"timestamp": 445, "ip": "2.2.2.2", "path": "/page89"}, {"timestamp": 450, "ip": "2.2.2.2", "path": "/page90"}, {"timestamp": 455, "ip": "2.2.2.2", "path": "/page91"}, {"timestamp": 460, "ip": "2.2.2.2", "path": "/page92"}, {"timestamp": 465, "ip": "2.2.2.2", "path": "/page93"}, {"timestamp": 470, "ip": "2.2.2.2", "path": "/page94"}, {"timestamp": 475, "ip": "2.2.2.2", "path": "/page95"}, {"timestamp": 480, "ip": "2.2.2.2", "path": "/page96"}, {"timestamp": 485, "ip": "2.2.2.2", "path": "/page97"}, {"timestamp": 490, "ip": "2.2.2.2", "path": "/page98"}, {"timestamp": 495, "ip": "2.2.2.2", "path": "/page99"}], "gap_threshold": 30, "top_n": 5}
PARAMS = ('reconstruct_sessions', ['logs', 'gap_threshold', 'top_n'])


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
