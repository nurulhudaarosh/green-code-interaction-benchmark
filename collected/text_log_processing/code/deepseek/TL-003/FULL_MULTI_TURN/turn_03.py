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
    """
    Build a normalization function. The returned function maps a raw line
    to its *comparison key*. Two lines are considered duplicates iff their
    keys are equal.

    By default (all flags False) the key is the identity, so behavior is
    unchanged from the previous version.
    """
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
    *normalized comparison*.

    Comparison mode:
        Provide either `normalize` (a custom function) OR the individual flags
        (`casefold`, `collapse_whitespace`, `unicode_nfkc`, `remove_punctuation`,
        `strip_whitespace`). Two lines are duplicates iff normalize(a) ==
        normalize(b).

    Output mode:
        keep_original_form=True  -> emit the first-seen *original* text.
        keep_original_form=False -> emit the *normalized* text.
    """
    # ---- 1. Detect trailing newline before splitting ----
    ends_with_newline = text.endswith(("\n", "\r"))

    lines = text.splitlines()
    if not lines:
        return "\n" if (ends_with_newline and preserve_trailing_newline) else ""

    # ---- 2. Build the comparison key function ----
    if normalize is None:
        normalize = make_normalizer(
            casefold=casefold,
            collapse_whitespace=collapse_whitespace,
            strip_whitespace=strip_whitespace,
            unicode_nfkc=unicode_nfkc,
            remove_punctuation=remove_punctuation,
        )

    # ---- 3. Count with first-occurrence order preserved ----
    # key -> count, and key -> first-seen original
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

    # ---- 4. Build output ----
    out_lines = []
    for key, n in counts.items():
        line = first_original[key] if keep_original_form else key
        if show_counts and n > 1:
            out_lines.append(f"{line} ({n})")
        else:
            out_lines.append(line)

    result = "\n".join(out_lines)

    # ---- 5. Restore trailing newline ----
    if preserve_trailing_newline and ends_with_newline and result:
        result += "\n"

    return result


def remove_duplicate_lines_with_stats(text: str, **kwargs) -> dict:
    """Same as above but also returns stats + the normalized keys."""
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

    total = sum(counts.values())
    return {
        "output": result,
        "total_lines": total,
        "unique_lines": len(counts),
        "duplicates_removed": total - len(counts),
        "counts": dict(counts),
        "first_original": dict(first_original),
        "had_trailing_newline": ends_with_newline,
    }


# ---------------- Example usage ----------------
if __name__ == "__main__":
    sample = """Apple
apple
APPLE
  banana  
Banana
banana
café
cafe\u0301
hello, world!
hello world
"""

    print("=== Default (identity comparison) ===")
    print(remove_duplicate_lines(sample))
    # Apple
    # apple
    # APPLE
    #   banana  
    # Banana
    # banana
    # café
    # café
    # hello, world!
    # hello world

    print("\n=== Case-insensitive ===")
    print(remove_duplicate_lines(sample, casefold=True))
    # Apple (3)
    #   banana   (3)
    # café
    # café
    # hello, world!
    # hello world
    # NOTE: "  banana  " vs "Banana" vs "banana" — casefolded but not
    # whitespace-normalized, so first-seen original is "  banana  ".

    print("\n=== Case-insensitive + collapse whitespace + strip ===")
    print(remove_duplicate_lines(
        sample, casefold=True, collapse_whitespace=True, strip_whitespace=True
    ))
    # Apple (3)
    # banana (3)
    # café
    # café
    # hello, world!
    # hello world

    print("\n=== + Unicode NFKC (é == e + combining accent) ===")
    print(remove_duplicate_lines(
        sample,
        casefold=True,
        collapse_whitespace=True,
        strip_whitespace=True,
        unicode_nfkc=True,
    ))
    # Apple (3)
    # banana (3)
    # café (2)
    # hello, world!
    # hello world

    print("\n=== + remove punctuation ===")
    print(remove_duplicate_lines(
        sample,
        casefold=True,
        collapse_whitespace=True,
        strip_whitespace=True,
        unicode_nfkc=True,
        remove_punctuation=True,
    ))
    # Apple (3)
    # banana (3)
    # café (2)
    # hello world (2)

    print("\n=== Same, but emit normalized form ===")
    print(remove_duplicate_lines(
        sample,
        casefold=True,
        collapse_whitespace=True,
        strip_whitespace=True,
        unicode_nfkc=True,
        remove_punctuation=True,
        keep_original_form=False,
    ))
    # apple (3)
    # banana (3)
    # café (2)
    # hello world (2)

    print("\n=== Custom normalizer (first word only) ===")
    print(remove_duplicate_lines(
        sample,
        normalize=lambda l: l.strip().split()[0] if l.strip() else "",
    ))
    # Apple (3)
    #   banana   (3)
    # café
    # café
    # hello, (2)