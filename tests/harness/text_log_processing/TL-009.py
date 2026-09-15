"""AUTO-GENERATED templated harness for TL-009 (see scripts/gen_harnesses.py).

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
TEMPLATE = {"header_blocks": ["Subject: Msg 0\nMessage-ID: <id0>", "Subject: Msg 1\nMessage-ID: <id1>", "Subject: Msg 2\nMessage-ID: <id2>", "Subject: Msg 3\nMessage-ID: <id3>", "Subject: Msg 4\nMessage-ID: <id4>", "Subject: Msg 5\nMessage-ID: <id5>", "Subject: Msg 6\nMessage-ID: <id6>", "Subject: Msg 7\nMessage-ID: <id7>", "Subject: Msg 8\nMessage-ID: <id8>", "Subject: Msg 9\nMessage-ID: <id9>", "Subject: Msg 10\nMessage-ID: <id10>", "Subject: Msg 11\nMessage-ID: <id11>", "Subject: Msg 12\nMessage-ID: <id12>", "Subject: Msg 13\nMessage-ID: <id13>", "Subject: Msg 14\nMessage-ID: <id14>", "Subject: Msg 15\nMessage-ID: <id15>", "Subject: Msg 16\nMessage-ID: <id16>", "Subject: Msg 17\nMessage-ID: <id17>", "Subject: Msg 18\nMessage-ID: <id18>", "Subject: Msg 19\nMessage-ID: <id19>", "Subject: Msg 20\nMessage-ID: <id20>", "Subject: Msg 21\nMessage-ID: <id21>", "Subject: Msg 22\nMessage-ID: <id22>", "Subject: Msg 23\nMessage-ID: <id23>", "Subject: Msg 24\nMessage-ID: <id24>", "Subject: Msg 25\nMessage-ID: <id25>", "Subject: Msg 26\nMessage-ID: <id26>", "Subject: Msg 27\nMessage-ID: <id27>", "Subject: Msg 28\nMessage-ID: <id28>", "Subject: Msg 29\nMessage-ID: <id29>", "Subject: Msg 30\nMessage-ID: <id30>", "Subject: Msg 31\nMessage-ID: <id31>", "Subject: Msg 32\nMessage-ID: <id32>", "Subject: Msg 33\nMessage-ID: <id33>", "Subject: Msg 34\nMessage-ID: <id34>", "Subject: Msg 35\nMessage-ID: <id35>", "Subject: Msg 36\nMessage-ID: <id36>", "Subject: Msg 37\nMessage-ID: <id37>", "Subject: Msg 38\nMessage-ID: <id38>", "Subject: Msg 39\nMessage-ID: <id39>", "Subject: Msg 40\nMessage-ID: <id40>", "Subject: Msg 41\nMessage-ID: <id41>", "Subject: Msg 42\nMessage-ID: <id42>", "Subject: Msg 43\nMessage-ID: <id43>", "Subject: Msg 44\nMessage-ID: <id44>", "Subject: Msg 45\nMessage-ID: <id45>", "Subject: Msg 46\nMessage-ID: <id46>", "Subject: Msg 47\nMessage-ID: <id47>", "Subject: Msg 48\nMessage-ID: <id48>", "Subject: Msg 49\nMessage-ID: <id49>", "Subject: Msg 50\nMessage-ID: <id50>", "Subject: Msg 51\nMessage-ID: <id51>", "Subject: Msg 52\nMessage-ID: <id52>", "Subject: Msg 53\nMessage-ID: <id53>", "Subject: Msg 54\nMessage-ID: <id54>", "Subject: Msg 55\nMessage-ID: <id55>", "Subject: Msg 56\nMessage-ID: <id56>", "Subject: Msg 57\nMessage-ID: <id57>", "Subject: Msg 58\nMessage-ID: <id58>", "Subject: Msg 59\nMessage-ID: <id59>", "Subject: Msg 60\nMessage-ID: <id60>", "Subject: Msg 61\nMessage-ID: <id61>", "Subject: Msg 62\nMessage-ID: <id62>", "Subject: Msg 63\nMessage-ID: <id63>", "Subject: Msg 64\nMessage-ID: <id64>", "Subject: Msg 65\nMessage-ID: <id65>", "Subject: Msg 66\nMessage-ID: <id66>", "Subject: Msg 67\nMessage-ID: <id67>", "Subject: Msg 68\nMessage-ID: <id68>", "Subject: Msg 69\nMessage-ID: <id69>", "Subject: Msg 70\nMessage-ID: <id70>", "Subject: Msg 71\nMessage-ID: <id71>", "Subject: Msg 72\nMessage-ID: <id72>", "Subject: Msg 73\nMessage-ID: <id73>", "Subject: Msg 74\nMessage-ID: <id74>", "Subject: Msg 75\nMessage-ID: <id75>", "Subject: Msg 76\nMessage-ID: <id76>", "Subject: Msg 77\nMessage-ID: <id77>", "Subject: Msg 78\nMessage-ID: <id78>", "Subject: Msg 79\nMessage-ID: <id79>", "Subject: Msg 80\nMessage-ID: <id80>", "Subject: Msg 81\nMessage-ID: <id81>", "Subject: Msg 82\nMessage-ID: <id82>", "Subject: Msg 83\nMessage-ID: <id83>", "Subject: Msg 84\nMessage-ID: <id84>", "Subject: Msg 85\nMessage-ID: <id85>", "Subject: Msg 86\nMessage-ID: <id86>", "Subject: Msg 87\nMessage-ID: <id87>", "Subject: Msg 88\nMessage-ID: <id88>", "Subject: Msg 89\nMessage-ID: <id89>", "Subject: Msg 90\nMessage-ID: <id90>", "Subject: Msg 91\nMessage-ID: <id91>", "Subject: Msg 92\nMessage-ID: <id92>", "Subject: Msg 93\nMessage-ID: <id93>", "Subject: Msg 94\nMessage-ID: <id94>", "Subject: Msg 95\nMessage-ID: <id95>", "Subject: Msg 96\nMessage-ID: <id96>", "Subject: Msg 97\nMessage-ID: <id97>", "Subject: Msg 98\nMessage-ID: <id98>", "Subject: Msg 99\nMessage-ID: <id99>"]}
PARAMS = ('parse_email_headers', ['header_blocks'])


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
