def merge_channels(r_path, g_path, b_path, output_path):
    """
    Recombine three single-channel grayscale images into one RGB image.

    Args:
        r_path (str | Path): red channel image
        g_path (str | Path): green channel image
        b_path (str | Path): blue channel image
        output_path (str | Path): where to save the merged RGB image

    Raises:
        ValueError: if the three channel images do not share identical
                    width and height.
    """
    r_path = Path(r_path)
    g_path = Path(g_path)
    b_path = Path(b_path)
    output_path = Path(output_path)

    with Image.open(r_path) as r_img, \
         Image.open(g_path) as g_img, \
         Image.open(b_path) as b_img:

        r = r_img.convert("L")
        g = g_img.convert("L")
        b = b_img.convert("L")

        # --- Early, explicit dimension validation -------------------
        if not (r.size == g.size == b.size):
            raise ValueError(
                "Cannot merge channels: image dimensions do not match. "
                f"R={r_path.name} {r.size}, "
                f"G={g_path.name} {g.size}, "
                f"B={b_path.name} {b.size}."
            )
        # ------------------------------------------------------------

        merged = Image.merge("RGB", (r, g, b))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path)
    print(f"Merged channels -> {output_path}")