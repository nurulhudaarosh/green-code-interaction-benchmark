#!/usr/bin/env python3
"""
Offline customer record matcher with deterministic best-candidate selection.

Pipeline:
  1. Normalize fields (email, phone, surname, postal code).
  2. Block on (surname initial, postal prefix).
  3. For each LEFT record, collect RIGHT candidates in the same block that share
     an exact normalized email or phone.
  4. Pick one winner per left record:
        a) email match beats phone-only match
        b) then the lowest right-side ID (natural order: "2" < "10", "A2" < "A10")

Usage:
  python matcher.py left.csv right.csv [-o matches.csv] [--postal-prefix-len 3]
  python matcher.py customers.csv            # one file: matched against itself (self excluded)
  python matcher.py --demo

Expected CSV columns (case-insensitive): id, first_name, last_name, email, phone, postal_code
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict


# ----------------------------- Normalization -----------------------------

def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize_surname(s: str) -> str:
    s = strip_accents((s or "").strip().lower())
    return re.sub(r"[^a-z]", "", s)


def normalize_postal(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def normalize_email(s: str) -> str:
    s = (s or "").strip().lower()
    if "@" not in s:
        return ""
    local, _, domain = s.rpartition("@")
    if not local or not domain or "." not in domain:
        return ""
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        domain = "gmail.com"
        local = local.replace(".", "")
    return f"{local}@{domain}" if local else ""


def normalize_phone(s: str, min_digits: int = 7) -> str:
    digits = re.sub(r"\D", "", s or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) < min_digits or len(set(digits)) == 1:
        return ""
    return digits


def natural_key(id_value: str):
    """Sort key giving natural order: 'A2' < 'A10', '2' < '10'."""
    return [
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in re.split(r"(\d+)", str(id_value))
        if part != ""
    ]


# ----------------------------- Matching -----------------------------

def prepare(record: dict, prefix_len: int) -> dict:
    surname = normalize_surname(record.get("last_name", ""))
    postal = normalize_postal(record.get("postal_code", ""))
    return {
        **record,
        "_email": normalize_email(record.get("email", "")),
        "_phone": normalize_phone(record.get("phone", "")),
        "_block": (surname[:1], postal[:prefix_len]) if surname and postal else None,
    }


def check_unique_ids(records: list, side: str):
    seen = set()
    for r in records:
        if r["id"] in seen:
            raise ValueError(f"Duplicate {side} id: {r['id']!r}")
        seen.add(r["id"])


def build_indexes(records: list):
    """(block, value) -> [records], separately for email and phone."""
    email_idx, phone_idx = defaultdict(list), defaultdict(list)
    for r in records:
        if r["_block"] is None:
            continue
        if r["_email"]:
            email_idx[(r["_block"], r["_email"])].append(r)
        if r["_phone"]:
            phone_idx[(r["_block"], r["_phone"])].append(r)
    return email_idx, phone_idx


def rank_key(candidate: dict):
    """Lower sorts first: email-matched candidates, then lowest right id."""
    return (0 if "email" in candidate["kinds"] else 1, natural_key(candidate["id"]))


def find_best_matches(left: list, right: list, same_source: bool = False):
    email_idx, phone_idx = build_indexes(right)
    results = []

    for l in left:
        candidates = {}                     # right id -> {"id", "kinds"}
        if l["_block"] is not None:
            for kind, idx, value in (
                ("email", email_idx, l["_email"]),
                ("phone", phone_idx, l["_phone"]),
            ):
                if not value:
                    continue
                for r in idx.get((l["_block"], value), []):
                    if same_source and r["id"] == l["id"]:
                        continue
                    candidates.setdefault(r["id"], {"id": r["id"], "kinds": set()})
                    candidates[r["id"]]["kinds"].add(kind)

        ranked = sorted(candidates.values(), key=rank_key)
        best = ranked[0] if ranked else None
        results.append({
            "left_id": l["id"],
            "right_id": best["id"] if best else "",
            "matched_on": "+".join(sorted(best["kinds"])) if best else "",
            "candidate_count": len(ranked),
            "other_candidates": ";".join(c["id"] for c in ranked[1:]),
        })
    return results


def run_matcher(left_rows: list, right_rows=None, prefix_len: int = 3):
    same_source = right_rows is None
    left = [prepare(r, prefix_len) for r in left_rows]
    right = left if same_source else [prepare(r, prefix_len) for r in right_rows]

    check_unique_ids(left, "left")
    if not same_source:
        check_unique_ids(right, "right")

    results = find_best_matches(left, right, same_source)
    stats = {
        "left_records": len(left),
        "right_records": len(right),
        "unblocked_left": sum(1 for r in left if r["_block"] is None),
        "matched": sum(1 for r in results if r["right_id"]),
        "ambiguous (>1 candidate)": sum(1 for r in results if r["candidate_count"] > 1),
        "unmatched": sum(1 for r in results if not r["right_id"]),
    }
    return results, stats


# ----------------------------- I/O -----------------------------

def read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV has no header row")
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        if "id" not in reader.fieldnames:
            raise ValueError(f"{path}: CSV must contain an 'id' column")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def write_output(path: str, results: list):
    out = sys.stdout if path == "-" else open(path, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(out, fieldnames=[
            "left_id", "right_id", "matched_on", "candidate_count", "other_candidates"])
        w.writeheader()
        w.writerows(sorted(results, key=lambda r: natural_key(r["left_id"])))
    finally:
        if out is not sys.stdout:
            out.close()


DEMO_LEFT = [
    {"id": "L1", "first_name": "Ana",  "last_name": "García", "email": "ana.garcia@gmail.com", "phone": "(555) 123-4567", "postal_code": "90210"},
    {"id": "L2", "first_name": "Bob",  "last_name": "Smith",  "email": "bob@example.com",      "phone": "555-000-1111",    "postal_code": "10001"},
    {"id": "L3", "first_name": "Cara", "last_name": "Lee",    "email": "cara@example.com",     "phone": "",                "postal_code": "30301"},
    {"id": "L4", "first_name": "Dan",  "last_name": "Moore",  "email": "",                     "phone": "",                "postal_code": ""},
]

DEMO_RIGHT = [
    # L1: R10 matches by phone only, R9 by email -> email wins even though R10... both candidates; R9 is email
    {"id": "R10", "first_name": "A.",   "last_name": "Garcia", "email": "other@example.com",   "phone": "+1 555 123 4567", "postal_code": "90211"},
    {"id": "R9",  "first_name": "Anna", "last_name": "Garcia", "email": "anagarcia+x@gmail.com", "phone": "",              "postal_code": "902-10"},
    # L2: two email matches -> lowest right id (R2, not R11)
    {"id": "R11", "first_name": "Rob",  "last_name": "Smith",  "email": "BOB@example.com",     "phone": "",                "postal_code": "10002"},
    {"id": "R2",  "first_name": "Bob",  "last_name": "Smith",  "email": "bob@example.com",     "phone": "",                "postal_code": "10001"},
    # L3: two phone-only candidates would tie on tier; no phone on left, so only email matters here
    {"id": "R5",  "first_name": "Cara", "last_name": "Lee",    "email": "cara@example.com",    "phone": "555-777-8888",    "postal_code": "30305"},
]


def main():
    p = argparse.ArgumentParser(description="Offline customer record matcher")
    p.add_argument("left", nargs="?", help="Left CSV (or the only CSV for self-matching)")
    p.add_argument("right", nargs="?", help="Right CSV (optional)")
    p.add_argument("-o", "--output", default="-", help="Output CSV path (default: stdout)")
    p.add_argument("--postal-prefix-len", type=int, default=3)
    p.add_argument("--demo", action="store_true", help="Run on built-in sample data")
    args = p.parse_args()

    if args.demo:
        left_rows, right_rows = DEMO_LEFT, DEMO_RIGHT
    elif args.left:
        left_rows = read_csv(args.left)
        right_rows = read_csv(args.right) if args.right else None
    else:
        p.error("provide a left CSV (and optionally a right CSV) or use --demo")

    results, stats = run_matcher(left_rows, right_rows, args.postal_prefix_len)
    write_output(args.output, results)

    print("\n--- stats ---", file=sys.stderr)
    for k, v in stats.items():
        print(f"{k}: {v}", file=sys.stderr)


if __name__ == "__main__":
    main()