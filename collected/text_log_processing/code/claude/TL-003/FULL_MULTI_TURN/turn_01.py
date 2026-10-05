from collections import Counter

def remove_duplicates(lines):
    counts = Counter(lines)
    # dict preserves insertion order, so first occurrences stay in order
    return [(line, counts[line]) for line in dict.fromkeys(lines)]

if __name__ == "__main__":
    import sys

    # Read from file if given, otherwise from stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f]
    else:
        lines = [l.rstrip("\n") for l in sys.stdin]

    for line, count in remove_duplicates(lines):
        print(f"{count}\t{line}")