import sys
import argparse
import unicodedata

def normalize_line(line):
    # Unicode-normalize, case-fold, collapse all internal whitespace
    line = unicodedata.normalize("NFKC", line)
    return " ".join(line.casefold().split())

def remove_duplicates(lines, ignore_blank=True, normalized=False):
    key_fn = normalize_line if normalized else (lambda l: l.strip())
    counts = {}  # key -> [first_original_line, count], insertion-ordered
    for raw in lines:
        line = raw.strip()
        if ignore_blank and not line:
            continue
        key = key_fn(raw)
        if key in counts:
            counts[key][1] += 1
        else:
            counts[key] = [line, 1]
    return [(first, n) for first, n in counts.values()]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Remove duplicate lines, keep first-occurrence order, show counts.")
    ap.add_argument("file", nargs="?", help="input file (default: stdin)")
    ap.add_argument("-n", "--normalize", action="store_true",
                    help="case-insensitive, collapse internal whitespace, Unicode NFKC")
    ap.add_argument("--keep-blank", action="store_true", help="count blank lines too")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8", newline="") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    for line, count in remove_duplicates(text.splitlines(),
                                         ignore_blank=not args.keep_blank,
                                         normalized=args.normalize):
        print(f"{count}\t{line}")