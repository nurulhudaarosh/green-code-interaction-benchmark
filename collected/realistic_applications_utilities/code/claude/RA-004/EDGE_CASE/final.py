import os
import re
import sys
from bisect import bisect_right
from collections import defaultdict

# Upper bounds are EXCLUSIVE: exactly 1024 bytes is "small", not "tiny".
EDGES = [1_024, 100 * 1_024, 1_024**2, 10 * 1_024**2, 100 * 1_024**2, 1_024**3]
LABELS = ["tiny (<1 KB)", "small (<100 KB)", "medium (<1 MB)",
          "large (<10 MB)", "xlarge (<100 MB)", "huge (<1 GB)", "massive (>=1 GB)"]
UNKNOWN = "unknown (bad size)"
NO_EXT = "(none)"
NO_NAME = "(unnamed)"


def split_name(raw):
    # Last path component. Handles / and \, repeated or trailing separators, empty/blank/None.
    s = "" if raw is None else str(raw).strip()
    parts = [p for p in re.split(r"[\\/]+", s) if p.strip()]
    return parts[-1].strip() if parts else NO_NAME


def get_ext(name):
    # Lowercased last extension. No dot, dotfile (.bashrc), trailing dot, or empty name -> "(none)".
    if not name or name == NO_NAME:
        return NO_EXT
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem.strip() or not ext.strip():
        return NO_EXT
    return "." + ext.strip().lower()


def classify_size(size):
    # Boundary values go to the higher bucket (bisect_right).
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        return UNKNOWN
    return LABELS[bisect_right(EDGES, size)]


def build(root="."):
    records = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            try:
                size = os.lstat(full).st_size  # lstat tolerates broken symlinks
            except OSError:
                continue
            name = split_name(fname)
            records.append({
                "path": os.path.normpath(full),
                "name": name,
                "ext": get_ext(name),
                "size": size,
                "bucket": classify_size(size),
            })
    return records


def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024


def self_test():
    # exact size boundaries
    assert classify_size(0) == LABELS[0]
    assert classify_size(1_023) == LABELS[0]
    assert classify_size(1_024) == LABELS[1]
    for i, edge in enumerate(EDGES):
        assert classify_size(edge - 1) == LABELS[i], edge
        assert classify_size(edge) == LABELS[i + 1], edge
    assert classify_size(-1) == UNKNOWN and classify_size(None) == UNKNOWN
    assert classify_size(True) == UNKNOWN and classify_size(1.5) == UNKNOWN
    # missing extensions
    assert get_ext("README") == NO_EXT
    assert get_ext(".bashrc") == NO_EXT
    assert get_ext("file.") == NO_EXT
    assert get_ext("a.tar.GZ") == ".gz"
    assert get_ext("") == NO_EXT and get_ext(NO_NAME) == NO_EXT
    # separators and empty names
    assert split_name("a/b//c.txt") == "c.txt"
    assert split_name("a\\b\\c.txt") == "c.txt"
    assert split_name("dir/sub/") == "sub"
    assert split_name("") == NO_NAME
    assert split_name("   ") == NO_NAME
    assert split_name(None) == NO_NAME
    assert split_name("///") == NO_NAME


def main():
    self_test()
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    records = build(root)

    buckets = defaultdict(list)
    exts = defaultdict(lambda: [0, 0])
    for r in records:
        buckets[r["bucket"]].append(r)
        exts[r["ext"]][0] += 1
        exts[r["ext"]][1] += r["size"]

    print(f"Scanned: {os.path.abspath(root)} ({len(records)} files)\n")
    print(f"{'Bucket':<22}{'Files':>8}{'Total':>14}")
    print("-" * 44)
    for label in LABELS + [UNKNOWN]:
        items = buckets.get(label, [])
        if items or label != UNKNOWN:
            print(f"{label:<22}{len(items):>8}{human(sum(i['size'] for i in items)):>14}")

    print(f"\n{'Extension':<14}{'Files':>8}{'Total':>14}")
    print("-" * 36)
    for ext, (count, total) in sorted(exts.items(), key=lambda kv: kv[1][1], reverse=True)[:10]:
        print(f"{ext:<14}{count:>8}{human(total):>14}")

    print("\nTop 10 largest files:")
    for r in sorted(records, key=lambda r: r["size"], reverse=True)[:10]:
        print(f"{human(r['size']):>12}  {r['bucket']:<18}  {r['path']}")


if __name__ == "__main__":
    main()