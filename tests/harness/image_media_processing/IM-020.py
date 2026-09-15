"""AUTO-GENERATED file harness for IM-020 (see scripts/gen_harnesses.py).

Main function: analyze_brightness; input files are generated per scale.
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

import hashlib, os as _os, shutil as _sh
import tempfile as _tf

SCALES = ["small", "medium", "large"]
_N = {"small": 24, "medium": 120, "large": 400}
SPEC = ('analyze_brightness', [('in', None)])          # (fname, [(kind, value)]) kind: in|out|file|outpath|const
MODE = 'images'          # "images" | "txt"
_prev_dir = None


def _noise_img(rng, w=48, h=32):
    from PIL import Image
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (rng.randint(0, 255), rng.randint(0, 255),
                        rng.randint(0, 255))
    return img


def _fill_images(dirpath, n, rng):
    n_png = max(1, int(n * 0.8))
    n_jpg = max(1, n - n_png)
    for i in range(n_png):
        _noise_img(rng).save(_os.path.join(dirpath, f"img_{i:04d}.png"))
    for i in range(n_jpg):
        _noise_img(rng).save(_os.path.join(dirpath, f"photo_{i:04d}.jpg"),
                             quality=88)
    for name in ("r.png", "g.png", "b.png", "wm.png"):
        _noise_img(rng).save(_os.path.join(dirpath, name))
    with open(_os.path.join(dirpath, "notes.txt"), "w") as f:
        f.write("not an image\n")


def _fill_txt(dirpath, n, rng):
    pool = ["alpha beta gamma", "delta epsilon zeta", "eta theta iota",
            "kappa lambda mu"]
    for i in range(n):
        c = pool[i % len(pool)] + (" extra" if i % 3 == 0 else "")
        sub = _os.path.join(dirpath, f"d{i % 3}")
        _os.makedirs(sub, exist_ok=True)
        with open(_os.path.join(sub, f"f{i:04d}.txt"), "w") as f:
            f.write(c + "\n")
        if i % 5 == 0:
            with open(_os.path.join(sub, f"f{i:04d}.md"), "w") as f:
                f.write("markdown ignored\n")


def make_input(scale, rng):
    global _prev_dir
    if _prev_dir and _os.path.isdir(_prev_dir):
        _sh.rmtree(_prev_dir, ignore_errors=True)
    d = _tf.mkdtemp(prefix="gcb_in_")
    n = _N.get(scale, 24)
    if MODE == "txt":
        _fill_txt(d, n, rng)
    else:
        _fill_images(d, n, rng)
    _prev_dir = d
    return {"__indir__": d}


def run(module, inp):
    work = _tf.mkdtemp(prefix="gcb_run_")
    try:
        ind = _os.path.join(work, "in")
        _sh.copytree(inp["__indir__"], ind)
        out = _os.path.join(work, "out")
        _os.makedirs(out, exist_ok=True)
        fname = SPEC[0]
        fn = resolve_entry(module, fname, len(SPEC[1]))
        if fn is None:
            return {fname: None}
        args = []
        for kind, val in SPEC[1]:
            if kind == "in":
                args.append(ind)
            elif kind == "out":
                args.append(out)
            elif kind == "file":
                args.append(_os.path.join(ind, val))
            elif kind == "outpath":
                args.append(_os.path.join(out, val))
            else:
                args.append(val)
        try:
            ret = fn(*args)
        except Exception as e:
            return {fname: {"__error__": f"{type(e).__name__}: {e}"}}
        listing = []
        for root, _, fs in _os.walk(out):
            for f in sorted(fs):
                p = _os.path.join(root, f)
                rel = _os.path.relpath(p, out)
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
                listing.append([rel, h])
        return {fname: [jsonable(ret), sorted(listing)]}
    finally:
        _sh.rmtree(work, ignore_errors=True)
