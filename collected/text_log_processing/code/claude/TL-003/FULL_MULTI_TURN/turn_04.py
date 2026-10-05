import sys
import argparse
import unicodedata

def normalize_line(line):
    line = unicodedata.normalize("NFKC", line)
    return " ".join(line.casefold().split())

def remove_duplicates(lines, ignore_blank=True, normalized=False):
    """Returns (results, total_considered). results = [(first_line, count), ...]"""
    key_fn = normalize_line if normalized else (lambda l: l.strip())
    seen = {}  # key -> [first_original_line, count]
    total = 0
    for raw in lines or []:          # None / empty list -> no iterations
        line = raw.strip()
        if ignore_blank and not line:
            continue
        total += 1
        key = key_fn(raw)
        if key in seen:
            seen[key][1] += 1
        else:
            seen[key] = [line, 1]
    return [(first, n) for first, n in seen.values()], total

def main():
    ap = argparse.ArgumentParser(description="Remove duplicate lines, keep first-occurrence order, show counts.")
    ap.add_argument("file", nargs="?", help="input file (default: stdin)")
    ap.add_argument("-n", "--normalize", action="store_true",
                    help="case-insensitive, collapse internal whitespace, Unicode NFKC")
    ap.add_argument("--keep-blank", action="store_true", help="count blank lines too")
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress the summary on stderr")
    args = ap.parse_args()

    try:
        if args.file:
            with open(args.file, encoding="utf-8", errors="replace", newline="") as f:
                text = f.read()
        else:
            text = sys.stdin.read()
    except FileNotFoundError:
        sys.exit(f"error: file not found: {args.file}")
    except OSError as e:
        sys.exit(f"error: cannot read input: {e}")

    text = text.lstrip("\ufeff")  # drop BOM so it doesn't make line 1 unique

    results, total = remove_duplicates(text.splitlines(),
                                       ignore_blank=not args.keep_blank,
                                       normalized=args.normalize)

    try:
        for line, count in results:
            print(f"{count}\t{line}")
    except BrokenPipeError:  # e.g. piped into `head`
        sys.stderr.close()
        return

    if not args.quiet:
        if total == 0:
            print("note: no lines to process (input empty or only blank lines)", file=sys.stderr)
        elif len(results) == 1 and total > 1:
            print(f"note: all {total} lines are duplicates of one line", file=sys.stderr)
        else:
            print(f"{total} lines, {len(results)} unique, {total - len(results)} duplicates removed",
                  file=sys.stderr)

if __name__ == "__main__":
    main()