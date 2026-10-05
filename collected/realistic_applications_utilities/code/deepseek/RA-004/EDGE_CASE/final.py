import os

def analyze_filename(filename, max_len=255):
    """
    Handle: missing extensions, missing separators, empty names, exact size boundaries.
    Returns a dict describing the parsed filename.
    """
    # --- Size boundaries & empty checks (before anything else) ---
    if filename is None:
        return {"input": None, "status": "error", "reason": "None input",
                "name": None, "ext": None, "has_ext": False, "size": 0}

    if not isinstance(filename, str):
        return {"input": filename, "status": "error", "reason": "not a string",
                "name": None, "ext": None, "has_ext": False, "size": 0}

    size = len(filename)
    if size == 0:                                    # exact boundary: 0
        return {"input": filename, "status": "error", "reason": "empty name",
                "name": None, "ext": None, "has_ext": False, "size": 0}

    if size > max_len:                               # exact boundary: > 255
        return {"input": filename, "status": "error",
                "reason": f"exceeds {max_len} chars", "name": None,
                "ext": None, "has_ext": False, "size": size}

    # --- Separator handling ---
    # Normalize both POSIX and Windows separators
    has_separator = any(s in filename for s in ("/", "\\", os.sep, os.altsep or os.sep))
    base_name = filename.replace("\\", "/").rsplit("/", 1)[-1]

    if base_name == "":                              # e.g. "path/" or "/"
        return {"input": filename, "status": "error",
                "reason": "no filename after separator", "name": None,
                "ext": None, "has_ext": False, "size": size}

    # --- Extension handling ---
    # Dotfiles like ".bashrc" have no extension; "a.txt" and "a.tar.gz" do.
    if base_name.startswith(".") and base_name.count(".") == 1:
        name, ext, has_ext = base_name, None, False
    else:
        name, dot_ext = os.path.splitext(base_name)
        has_ext = dot_ext != ""
        ext = dot_ext[1:] if has_ext else None       # strip the dot

    # Extension-only edge case: ".txt"
    if name == "" and has_ext:
        return {"input": filename, "status": "error",
                "reason": "extension but no base name", "name": None,
                "ext": ext, "has_ext": True, "size": size}

    return {
        "input": filename,
        "status": "ok",
        "reason": None,
        "name": name,
        "ext": ext,
        "has_ext": has_ext,
        "has_separator": has_separator,
        "size": size,
        "size_at_limit": size == max_len,            # exact boundary: == 255
    }


# ---------------- Test / demo ----------------
if __name__ == "__main__":
    cases = [
        "document.txt",          # normal with ext
        "archive.tar.gz",        # multi-dot ext
        "README",                # missing extension
        ".gitignore",            # dotfile, no ext
        "no_sep.txt",            # missing separator
        "/path/to/file.txt",     # has separator
        "C:\\Users\\f.doc",      # windows separator
        "",                      # empty (boundary 0)
        None,                    # None
        123,                     # non-string
        "/",                     # separator only
        "folder/",               # trailing separator
        ".txt",                  # extension only
        "a" * 255,               # exact boundary == 255
        "a" * 256,               # boundary exceeded
    ]

    for c in cases:
        r = analyze_filename(c)
        label = repr(c) if not isinstance(c, str) or len(c) <= 20 else repr(c[:17] + "...")
        print(f"{label:<24} -> {r['status']:<5} "
              f"name={r['name']!r:<12} ext={r['ext']!r:<6} "
              f"has_ext={r['has_ext']!s:<5} size={r['size']} "
              f"{r['reason'] or ''}")