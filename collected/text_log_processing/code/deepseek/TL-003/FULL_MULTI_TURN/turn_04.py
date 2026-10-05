import re
import unicodedata
from collections import OrderedDict
from typing import Callable, Optional


# ----------------------------------------------------------------------
# Normalization helpers
# ----------------------------------------------------------------------
def make_normalizer(
    casefold: bool = False,
    collapse_whitespace: bool = False,
    strip_whitespace: bool = False,
    unicode_nfkc: bool = False,
    remove_punctuation: bool = False,
) -> Callable[[str], str]:
    """Build a normalization function mapping raw line -> comparison key."""
    punct_re = re.compile(r"[^\w\s]", re.UNICODE) if remove_punctuation else None
    ws_re = re.compile(r"\s+", re.UNICODE)

    def normalize(line: str) -> str:
        if unicode_nfkc:
            line = unicodedata.normalize("NFKC", line)
        if remove_punctuation:
            line = punct_re.sub("", line)          # type: ignore[union-attr]
        if strip_whitespace:
            line = line.strip()
        if collapse_whitespace:
            line = ws_re.sub(" ", line)
        if casefold:
            line = line.casefold()
        return line

    return normalize


# ----------------------------------------------------------------------
# Core function
# ----------------------------------------------------------------------
def remove_duplicate_lines(
    text: str,
    *,
    show_counts: bool = True,
    strip_whitespace: bool = False,
    ignore_empty: bool = False,
    preserve_trailing_newline: bool = True,
    normalize: Optional[Callable[[str], str]] = None,
    casefold: bool = False,
    collapse_whitespace: bool = False,
    unicode_nfkc: bool = False,
    remove_punctuation: bool = False,
    keep_original_form: bool = True,
) -> str:
    """
    Remove duplicate lines, preserving first-occurrence order, with optional
    normalized comparison and robust edge-case handling.

    Edge cases handled:
      * Empty input ("")                      -> ""
      * Input that is only a newline ("\\n")  -> "\\n"
      * Input that is only blank lines        -> preserved or collapsed per flags
      * All lines identical                   -> single line + (n)
      * No duplicates                         -> input unchanged (modulo flags)
      * Missing trailing newline              -> not added
      * Trailing newline present              -> preserved
    """
    # ---- 1. Truly empty input: nothing to do, nothing to add ----
    if text == "":
        return ""

    # ---- 2. Detect trailing newline BEFORE splitting ----
    ends_with_newline = text.endswith(("\n", "\r"))

    # ---- 3. Split (handles \n, \r\n, \r) ----
    lines = text.splitlines()

    # Special case: text was JUST a newline ("\n", "\r\n", "\r").
    # splitlines() returns [""], i.e. one empty line. That's correct:
    # the input is one empty line, and (unless ignore_empty) we keep it.
    if not lines:
        # Defensive: shouldn't happen for non-empty text, but be safe.
        return "\n" if (ends_with_newline and preserve_trailing_newline) else ""

    # ---- 4. Build normalizer ----
    if normalize is None:
        normalize = make_normalizer(
            casefold=casefold,
            collapse_whitespace=collapse_whitespace,
            strip_whitespace=strip_whitespace,
            unicode_nfkc=unicode_nfkc,
            remove_punctuation=remove_punctuation,
        )

    # ---- 5. First pass: build ordered counts + first-seen originals ----
    counts: "OrderedDict[str, int]" = OrderedDict()
    first_original: "OrderedDict[str, str]" = OrderedDict()

    for raw in lines:
        key = normalize(raw)

        if ignore_empty and key == "":
            # Skip blank lines entirely — don't count, don't output.
            continue

        if key not in counts:
            counts[key] = 1
            first_original[key] = raw
        else:
            counts[key] += 1

    # ---- 6. If everything was filtered out (e.g. all-empty + ignore_empty) ----
    if not counts:
        # We removed every line. Respect the trailing-newline flag:
        # if the input had a trailing newline, keep a single one so the
        # output is still "a text file with one blank line"; otherwise
        # return "" so the caller sees an empty result.
        if preserve_trailing_newline and ends_with_newline:
            return "\n"
        return ""

    # ---- 7. Build output ----
    out_lines = []
    for key, n in counts.items():
        line = first_original[key] if keep_original_form else key
        if show_counts and n > 1:
            out_lines.append(f"{line} ({n})")
        else:
            out_lines.append(line)

    result = "\n".join(out_lines)

    # ---- 8. Restore trailing newline ----
    if preserve_trailing_newline and ends_with_newline and result:
        result += "\n"

    return result


def remove_duplicate_lines_with_stats(text: str, **kwargs) -> dict:
    """Same as above but returns stats. Never raises on edge cases."""
    # Empty input short-circuit
    if text == "":
        return {
            "output": "",
            "total_lines": 0,
            "unique_lines": 0,
            "duplicates_removed": 0,
            "counts": {},
            "first_original": {},
            "had_trailing_newline": False,
            "is_empty": True,
        }

    ends_with_newline = text.endswith(("\n", "\r"))
    lines = text.splitlines()

    normalize = kwargs.pop("normalize", None)
    if normalize is None:
        normalize = make_normalizer(
            casefold=kwargs.get("casefold", False),
            collapse_whitespace=kwargs.get("collapse_whitespace", False),
            strip_whitespace=kwargs.get("strip_whitespace", False),
            unicode_nfkc=kwargs.get("unicode_nfkc", False),
            remove_punctuation=kwargs.get("remove_punctuation", False),
        )

    ignore_empty = kwargs.get("ignore_empty", False)
    show_counts = kwargs.get("show_counts", True)
    keep_original_form = kwargs.get("keep_original_form", True)
    preserve_trailing_newline = kwargs.get("preserve_trailing_newline", True)

    counts: "OrderedDict[str, int]" = OrderedDict()
    first_original: "OrderedDict[str, str]" = OrderedDict()

    for raw in lines:
        key = normalize(raw)
        if ignore_empty and key == "":
            continue
        if key not in counts:
            counts[key] = 1
            first_original[key] = raw
        else:
            counts[key] += 1

    out_lines = []
    for key, n in counts.items():
        line = first_original[key] if keep_original_form else key
        out_lines.append(f"{line} ({n})" if (show_counts and n > 1) else line)

    result = "\n".join(out_lines)
    if preserve_trailing_newline and ends_with_newline and result:
        result += "\n"
    elif not counts and preserve_trailing_newline and ends_with_newline:
        # Every line was filtered out but input had a trailing newline.
        result = "\n"

    total = sum(counts.values())
    return {
        "output": result,
        "total_lines": total,
        "unique_lines": len(counts),
        "duplicates_removed": total - len(counts),
        "counts": dict(counts),
        "first_original": dict(first_original),
        "had_trailing_newline": ends_with_newline,
        "is_empty": False,
    }


# ---------------- Edge case test suite ----------------
if __name__ == "__main__":
    def show(label, value):
        print(f"{label:<48} -> {value!r}")

    print("=== Empty input ===")
    show("''",                              remove_duplicate_lines(""))
    show("'' + preserve_trailing_newline",  remove_duplicate_lines("", preserve_trailing_newline=True))
    show("'\\n'",                           remove_duplicate_lines("\n"))
    show("'\\n\\n\\n'",                     remove_duplicate_lines("\n\n\n"))
    show("'\\n\\n\\n' + ignore_empty",      remove_duplicate_lines("\n\n\n", ignore_empty=True))

    print("\n=== All-duplicate input ===")
    show("'a\\na\\na\\n'",                  remove_duplicate_lines("a\na\na\n"))
    show("'a\\na\\na' (no trailing NL)",    remove_duplicate_lines("a\na\na"))
    show("'\\n\\n\\n' (3 blank lines)",     remove_duplicate_lines("\n\n\n"))
    show("'   \\n   \\n' + strip",          remove_duplicate_lines("   \n   \n", strip_whitespace=True))
    show("'   \\n   \\n' + strip+ignore",   remove_duplicate_lines("   \n   \n", strip_whitespace=True, ignore_empty=True))

    print("\n=== No duplicates (passthrough) ===")
    show("'a\\nb\\nc\\n'",                  remove_duplicate_lines("a\nb\nc\n"))
    show("'a\\nb\\nc'",                     remove_duplicate_lines("a\nb\nc"))

    print("\n=== Single line, with / without newline ===")
    show("'a'",                             remove_duplicate_lines("a"))
    show("'a\\n'",                          remove_duplicate_lines("a\n"))

    print("\n=== show_counts=False ===")
    show("'a\\na\\na\\n'",                  remove_duplicate_lines("a\na\na\n", show_counts=False))

    print("\n=== ignore_empty on mixed input ===")
    show("'a\\n\\nb\\n\\na\\n'",            remove_duplicate_lines("a\n\nb\n\na\n", ignore_empty=True))
    show("'a\\n\\nb\\n\\na\\n' (keep)",     remove_duplicate_lines("a\n\nb\n\na\n"))

    print("\n=== All whitespace variants folded together ===")
    show("'A\\n a \\nA\\n' + case+strip",   remove_duplicate_lines("A\n a \nA\n", casefold=True, strip_whitespace=True))

    print("\n=== Stats on empty input ===")
    import json
    print(json.dumps(remove_duplicate_lines_with_stats(""), indent=2))

    print("\n=== Stats on all-duplicates ===")
    print(json.dumps(remove_duplicate_lines_with_stats("a\na\na\n"), indent=2))