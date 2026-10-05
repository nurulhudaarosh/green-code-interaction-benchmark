def _test_edge_cases(tmpdir):
    """All edge cases must return [] without raising."""
    import tempfile, os
    from PIL import Image

    def _make(path, color=128, size=(32, 32)):
        Image.new('L', size, color=color).save(path)

    # --- Case 1: empty directory ---
    d = os.path.join(tmpdir, "empty")
    os.makedirs(d, exist_ok=True)
    assert find_near_duplicates(d, threshold=0.1) == [], "empty dir failed"

    # --- Case 2: exactly one image ---
    d = os.path.join(tmpdir, "single")
    os.makedirs(d, exist_ok=True)
    _make(os.path.join(d, "only.png"))
    assert find_near_duplicates(d, threshold=0.1) == [], "single image failed"
    # Even at a permissive threshold, one image must not form a cluster.
    assert find_near_duplicates(d, threshold=10.0) == [], "single image (loose thr) failed"

    # --- Case 3: one valid image + one unreadable file ---
    d = os.path.join(tmpdir, "mixed")
    os.makedirs(d, exist_ok=True)
    _make(os.path.join(d, "good.png"))
    with open(os.path.join(d, "broken.png"), "wb") as f:
        f.write(b"not a real png")
    assert find_near_duplicates(d, threshold=0.1) == [], "valid+broken failed"

    # --- Case 4: no image-like files at all ---
    d = os.path.join(tmpdir, "nofiles")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "readme.txt"), "w") as f:
        f.write("hello")
    assert find_near_duplicates(d, threshold=0.1) == [], "no image files failed"

    print("All edge-case tests passed.")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        _test_edge_cases(tmp)