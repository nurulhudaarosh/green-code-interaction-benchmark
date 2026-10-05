from PIL import Image
from pathlib import Path

def test_merge_1x1(tmp=Path("/tmp/ch_1x1")):
    tmp.mkdir(parents=True, exist_ok=True)

    # Three 1x1 single-channel images with distinct values
    r_src = Image.new("L", (1, 1), 10)
    g_src = Image.new("L", (1, 1), 20)
    b_src = Image.new("L", (1, 1), 30)

    r_p, g_p, b_p = (tmp / f"c_{n}.png" for n in "rgb")
    r_src.save(r_p); g_src.save(g_p); b_src.save(b_p)

    out = tmp / "merged_1x1.png"
    merge_channels(r_p, g_p, b_p, out)

    with Image.open(out) as merged:
        assert merged.size == (1, 1), f"expected (1,1), got {merged.size}"
        assert merged.mode == "RGB", f"expected RGB, got {merged.mode}"
        assert merged.getpixel((0, 0)) == (10, 20, 30), \
            f"wrong pixel: {merged.getpixel((0, 0))}"

    print("1x1 merge OK: size=(1,1), mode=RGB, pixel=(10,20,30)")
    return out

test_merge_1x1()