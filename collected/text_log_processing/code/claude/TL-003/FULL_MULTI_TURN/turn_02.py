import sys
from collections import Counter

def remove_duplicates(lines, ignore_blank=True):
    # Normalize: strip leading/trailing whitespace (also removes stray \r)
    cleaned = [l.strip() for l in lines]
    if ignore_blank:
        cleaned = [l for l in cleaned if l]
    counts = Counter(cleaned)
    return [(line, counts[line]) for line in dict.fromkeys(cleaned)]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8", newline="") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    # splitlines handles \n, \r\n, \r and a missing final newline
    for line, count in remove_duplicates(text.splitlines()):
        print(f"{count}\t{line}")