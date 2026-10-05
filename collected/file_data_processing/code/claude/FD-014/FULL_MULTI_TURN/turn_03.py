#!/usr/bin/env python3
"""
Offline customer record matcher (left/right linkage, blocking first,
deterministic best-match selection).

Pipeline
--------
1. Normalize email, phone, surname and postal code on every record.
2. Compute a blocking key (surname initial, postal-code prefix) per record.
3. Index the RIGHT file by blocking key.
4. For each LEFT record, look up only the right records in the same block
   (the candidates) and compare those. The full left x right cross product
   is never built.
5. A candidate matches when normalized emails are equal and non-empty, or
   normalized phones are equal and non-empty.
6. When several candidates match one left record, pick ONE winner:
       a) a candidate matching on email beats one matching on phone only
       b) among equals, the lowest right-side ID wins
   (IDs that are all digits compare numerically, so 9 < 10; other IDs
   compare as case-sensitive text, and numeric IDs sort before text IDs.)

Usage
-----
    python matcher.py left.csv right.csv
    python matcher.py customers.csv            # dedupe a single file
    python matcher.py left.csv right.csv --postal-prefix-len 2 --out-dir results

Required CSV columns (case-insensitive; extra columns are preserved):
    id, last_name, email, phone, postal_code

Standard library only, so it runs fully offline.
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REQUIRED = {"id", "last_name", "email", "phone", "postal_code"}


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

def strip_accents(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize_surname(value):
    """Lowercase, strip accents, keep letters only."""
    return re.sub(r"[^a-z]", "", strip_accents(value or "").lower())


def normalize_postal(value):
    """Uppercase, keep letters and digits only."""
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def normalize_email(value):
    """Trim, lowercase, drop mailto:/angle brackets. Invalid -> ''."""
    value = (value or "").strip().lower()
    value = value.replace("mailto:", "").strip("<> ")
    if value.count("@") != 1:
        return ""
    local, domain = value.split("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return ""
    return value


def normalize_phone(value, min_digits=7):
    """Digits only, extension removed, leading 00 dropped. Too short -> ''."""
    value = (value or "").lower()
    value = re.split(r"\s*(?:ext\.?|x)\s*\d+\s*$", value)[0]
    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        digits = digits[2:]
    return digits if len(digits) >= min_digits else ""


# --------------------------------------------------------------------------
# Loading and preparation
# --------------------------------------------------------------------------

def blocking_key(rec, prefix_len):
    """(surname initial, postal prefix), or None if either part is missing."""
    surname = normalize_surname(rec["last_name"])
    postal = normalize_postal(rec["postal_code"])
    if not surname or not postal:
        return None
    return surname[0], postal[:prefix_len]


def load_records(path, prefix_len):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            sys.exit(f"{path} is empty.")
        header_map = {h: h.strip().lower() for h in reader.fieldnames if h}
        missing = REQUIRED - set(header_map.values())
        if missing:
            sys.exit(f"{path}: missing column(s): {', '.join(sorted(missing))}")

        records, seen = [], set()
        for row in reader:
            rec = {header_map[k]: (v or "").strip() for k, v in row.items() if k in header_map}
            if rec["id"] in seen:
                sys.exit(f"{path}: duplicate id {rec['id']!r}")
            seen.add(rec["id"])
            rec["_email"] = normalize_email(rec["email"])
            rec["_phone"] = normalize_phone(rec["phone"])
            rec["_block"] = blocking_key(rec, prefix_len)
            records.append(rec)
    return records


# --------------------------------------------------------------------------
# Blocking index and candidate comparison
# --------------------------------------------------------------------------

def build_block_index(records):
    """Map blocking key -> list of records. Unblockable records are skipped."""
    index = defaultdict(list)
    for rec in records:
        if rec["_block"] is not None:
            index[rec["_block"]].append(rec)
    return index


def candidates_for(rec, block_index):
    """Only the records sharing this record's block; nothing outside it."""
    if rec["_block"] is None:
        return []
    return block_index.get(rec["_block"], [])


def compare(a, b):
    """Return 'email', 'phone', 'email+phone', or None."""
    reasons = []
    if a["_email"] and a["_email"] == b["_email"]:
        reasons.append("email")
    if a["_phone"] and a["_phone"] == b["_phone"]:
        reasons.append("phone")
    return "+".join(reasons) if reasons else None


def id_sort_key(value):
    """Numeric IDs compare as numbers (9 < 10) and sort before text IDs."""
    return (0, int(value), "") if value.isdigit() else (1, 0, value)


def rank(reason, right_id):
    """
    Lower tuple = better candidate.
      first  : 0 if the match involves email, 1 if phone only
      second : lowest right-side ID
    """
    email_tier = 0 if "email" in reason else 1
    return (email_tier, id_sort_key(right_id))


def link(left, right):
    """
    Link two files. Each left record is compared only against right records
    in its own block, then reduced to at most one best match.
    """
    block_index = build_block_index(right)
    best_matches = []
    comparisons = 0
    candidate_matches = 0

    for l in left:
        best = None  # (rank, right_id, reason)
        for r in candidates_for(l, block_index):
            comparisons += 1
            reason = compare(l, r)
            if not reason:
                continue
            candidate_matches += 1
            key = rank(reason, r["id"])
            if best is None or key < best[0]:
                best = (key, r["id"], reason)
        if best:
            best_matches.append((l["id"], best[1], best[2]))

    stats = {
        "left_records": len(left),
        "right_records": len(right),
        "right_blocks": len(block_index),
        "left_unblockable": sum(1 for r in left if r["_block"] is None),
        "right_unblockable": sum(1 for r in right if r["_block"] is None),
        "comparisons_made": comparisons,
        "full_cross_product": len(left) * len(right),
        "candidate_matches": candidate_matches,
        "left_records_matched": len(best_matches),
        "runner_ups_dropped": candidate_matches - len(best_matches),
    }
    return best_matches, stats


def dedupe(records):
    """
    Single-file mode: group by blocking key first, then compare each pair
    inside a block exactly once. There is no left/right side here, so all
    matching pairs are kept (no best-candidate reduction).
    """
    block_index = build_block_index(records)
    matches, comparisons = [], 0

    for block in block_index.values():
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                comparisons += 1
                reason = compare(block[i], block[j])
                if reason:
                    a, b = sorted((block[i]["id"], block[j]["id"]), key=id_sort_key)
                    matches.append((a, b, reason))

    n = len(records)
    stats = {
        "records": n,
        "blocks": len(block_index),
        "unblockable": sum(1 for r in records if r["_block"] is None),
        "comparisons_made": comparisons,
        "full_cross_product": n * (n - 1) // 2,
        "matches": len(matches),
    }
    return matches, stats


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_matches(matches, out_dir, left_name, right_name):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "matches.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([f"{left_name}_id", f"{right_name}_id", "reason"])
        for row in sorted(matches, key=lambda m: (id_sort_key(m[0]), id_sort_key(m[1]))):
            w.writerow(row)
    return path


def write_unmatched_left(left, matches, out_dir):
    matched = {m[0] for m in matches}
    fields = [k for k in left[0] if not k.startswith("_")]
    path = out_dir / "unmatched_left.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for rec in left:
            if rec["id"] not in matched:
                w.writerow([rec.get(f, "") for f in fields])
    return path


def print_stats(stats):
    for k, v in stats.items():
        print(f"  {k.replace('_', ' '):<22}{v}")
    full = stats["full_cross_product"]
    if full:
        saved = 100 * (1 - stats["comparisons_made"] / full)
        print(f"  {'comparisons avoided':<22}{saved:.2f}%")


def main():
    p = argparse.ArgumentParser(description="Offline customer record matcher with blocking")
    p.add_argument("left", type=Path, help="Left CSV (or the only CSV for dedupe mode)")
    p.add_argument("right", type=Path, nargs="?", help="Right CSV (omit to dedupe the left file)")
    p.add_argument("--postal-prefix-len", type=int, default=3,
                   help="Postal-code characters in the blocking key (default 3)")
    p.add_argument("--out-dir", type=Path, default=Path("match_output"))
    args = p.parse_args()

    if args.postal_prefix_len < 1:
        sys.exit("--postal-prefix-len must be at least 1")

    left = load_records(args.left, args.postal_prefix_len)
    if not left:
        sys.exit("Left file has no records.")

    if args.right:
        right = load_records(args.right, args.postal_prefix_len)
        if not right:
            sys.exit("Right file has no records.")
        matches, stats = link(left, right)
        path = write_matches(matches, args.out_dir, "left", "right")
        write_unmatched_left(left, matches, args.out_dir)
    else:
        matches, stats = dedupe(left)
        path = write_matches(matches, args.out_dir, "record_a", "record_b")

    print("Matching complete")
    print_stats(stats)
    print(f"Results written to: {path.parent.resolve()}")


if __name__ == "__main__":
    main()