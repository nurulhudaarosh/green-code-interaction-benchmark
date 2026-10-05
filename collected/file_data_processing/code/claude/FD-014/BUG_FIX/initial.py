#!/usr/bin/env python3
"""
Offline customer record matcher.

Strategy
--------
1. Normalize fields (email, phone, surname, postal code).
2. Blocking: group records by (surname initial, postal prefix) so that
   candidate comparisons only happen inside a block.
3. Within each block, two records match if they share an exact normalized
   email OR an exact normalized phone number.
4. Matches are merged transitively (union-find) into clusters.

Usage
-----
    python matcher.py customers.csv                 # prints clusters
    python matcher.py customers.csv -o matches.csv  # writes cluster assignments
    python matcher.py customers.csv --postal-prefix 3 --pairs pairs.csv

Expected CSV columns (case-insensitive; override with flags):
    id, first_name, last_name, email, phone, postal_code
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from itertools import combinations


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize_email(raw: str) -> str:
    """Lowercase, trim, drop +tags; strip dots for gmail-style domains."""
    if not raw:
        return ""
    email = raw.strip().lower()
    if email.count("@") != 1:
        return ""
    local, domain = email.split("@")
    if not local or not domain or "." not in domain:
        return ""
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    if not local:
        return ""
    return f"{local}@{domain}"


def normalize_phone(raw: str, default_country_code: str = "1") -> str:
    """
    Keep digits only. Strip extensions, international prefixes (00 / 011),
    and prepend a default country code for bare national numbers.
    Returns "" if the result is implausibly short.
    """
    if not raw:
        return ""
    text = raw.strip().lower()
    # Remove extensions like "x123", "ext. 45"
    text = re.split(r"(?:ext\.?|extension|x)\s*\d+\s*$", text)[0]
    has_plus = text.lstrip().startswith("+")
    digits = re.sub(r"\D", "", text)
    if not has_plus:
        for prefix in ("011", "00"):
            if digits.startswith(prefix):
                digits = digits[len(prefix):]
                has_plus = True
                break
    if not has_plus and len(digits) == 11 and digits.startswith(default_country_code):
        pass  # already has country code
    elif not has_plus and len(digits) == 10:
        digits = default_country_code + digits
    if len(digits) < 7:
        return ""
    return digits


def normalize_surname(raw: str) -> str:
    if not raw:
        return ""
    s = strip_accents(raw).lower().strip()
    s = re.sub(r"[^a-z\s'-]", "", s)
    # Drop common particles so "van der Berg" and "Berg" share an initial
    s = re.sub(r"^(?:van der|van den|van|von|de la|de|del|della|di|da|le|la|al|bin|ibn)\s+", "", s)
    s = re.sub(r"[^a-z]", "", s)
    return s


def normalize_postal(raw: str, prefix_len: int) -> str:
    if not raw:
        return ""
    s = re.sub(r"[^A-Za-z0-9]", "", strip_accents(raw)).upper()
    return s[:prefix_len]


# --------------------------------------------------------------------------
# Union-Find
# --------------------------------------------------------------------------

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


# --------------------------------------------------------------------------
# Matcher
# --------------------------------------------------------------------------

class CustomerMatcher:
    def __init__(self, postal_prefix_len=3, default_country_code="1"):
        self.postal_prefix_len = postal_prefix_len
        self.default_country_code = default_country_code

    def prepare(self, records):
        """Attach normalized fields and a blocking key to every record."""
        prepared = []
        for rec in records:
            surname = normalize_surname(rec.get("last_name", ""))
            postal = normalize_postal(rec.get("postal_code", ""), self.postal_prefix_len)
            prepared.append({
                "rec": rec,
                "email": normalize_email(rec.get("email", "")),
                "phone": normalize_phone(rec.get("phone", ""), self.default_country_code),
                "block": (surname[:1], postal) if surname and postal else None,
            })
        return prepared

    def build_blocks(self, prepared):
        blocks = defaultdict(list)
        unblocked = []
        for idx, p in enumerate(prepared):
            if p["block"] is None:
                unblocked.append(idx)
            else:
                blocks[p["block"]].append(idx)
        return blocks, unblocked

    @staticmethod
    def _match_reason(a, b):
        reasons = []
        if a["email"] and a["email"] == b["email"]:
            reasons.append("email")
        if a["phone"] and a["phone"] == b["phone"]:
            reasons.append("phone")
        return reasons

    def find_pairs(self, prepared):
        """
        Yield (i, j, reasons) for matching pairs inside each block.
        Uses inverted indexes per block, so cost is ~linear in block size
        rather than quadratic.
        """
        blocks, _unblocked = self.build_blocks(prepared)
        seen = set()
        for members in blocks.values():
            if len(members) < 2:
                continue
            by_email = defaultdict(list)
            by_phone = defaultdict(list)
            for i in members:
                if prepared[i]["email"]:
                    by_email[prepared[i]["email"]].append(i)
                if prepared[i]["phone"]:
                    by_phone[prepared[i]["phone"]].append(i)
            for group in list(by_email.values()) + list(by_phone.values()):
                for i, j in combinations(group, 2):
                    key = (min(i, j), max(i, j))
                    if key in seen:
                        continue
                    seen.add(key)
                    reasons = self._match_reason(prepared[i], prepared[j])
                    if reasons:
                        yield key[0], key[1], reasons

    def cluster(self, records):
        prepared = self.prepare(records)
        uf = UnionFind()
        for i in range(len(prepared)):
            uf.add(i)
        pairs = []
        for i, j, reasons in self.find_pairs(prepared):
            uf.union(i, j)
            pairs.append((i, j, reasons))

        groups = defaultdict(list)
        for i in range(len(prepared)):
            groups[uf.find(i)].append(i)

        clusters = [sorted(g) for g in groups.values()]
        clusters.sort(key=lambda g: g[0])
        return prepared, clusters, pairs


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------

def read_records(path, colmap):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            sys.exit("Input file has no header row.")
        lookup = {name.strip().lower(): name for name in reader.fieldnames}
        records = []
        for n, row in enumerate(reader, start=1):
            rec = {}
            for canon, src in colmap.items():
                actual = lookup.get(src.lower())
                rec[canon] = (row.get(actual, "") if actual else "") or ""
            if not rec["id"]:
                rec["id"] = str(n)
            records.append(rec)
        return records


def write_clusters(path, records, clusters):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id", "cluster_size", "id", "first_name", "last_name",
                    "email", "phone", "postal_code"])
        for cid, members in enumerate(clusters, start=1):
            for i in members:
                r = records[i]
                w.writerow([cid, len(members), r["id"], r["first_name"], r["last_name"],
                            r["email"], r["phone"], r["postal_code"]])


def write_pairs(path, records, pairs):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id_a", "id_b", "matched_on"])
        for i, j, reasons in pairs:
            w.writerow([records[i]["id"], records[j]["id"], "+".join(reasons)])


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Offline customer record matcher.")
    ap.add_argument("input", help="Input CSV file")
    ap.add_argument("-o", "--output", help="Write cluster assignments to this CSV")
    ap.add_argument("--pairs", help="Write matched pairs (with reasons) to this CSV")
    ap.add_argument("--postal-prefix", type=int, default=3,
                    help="Number of postal code characters in the blocking key (default 3)")
    ap.add_argument("--country-code", default="1",
                    help="Default country code for bare national phone numbers (default 1)")
    for field in ("id", "first_name", "last_name", "email", "phone", "postal_code"):
        ap.add_argument(f"--col-{field.replace('_', '-')}", default=field,
                        help=f"Column name for {field} (default '{field}')")
    args = ap.parse_args()

    colmap = {
        "id": args.col_id,
        "first_name": args.col_first_name,
        "last_name": args.col_last_name,
        "email": args.col_email,
        "phone": args.col_phone,
        "postal_code": args.col_postal_code,
    }

    records = read_records(args.input, colmap)
    matcher = CustomerMatcher(args.postal_prefix, args.country_code)
    prepared, clusters, pairs = matcher.cluster(records)

    dupes = [c for c in clusters if len(c) > 1]
    skipped = sum(1 for p in prepared if p["block"] is None)

    print(f"Records:                 {len(records)}")
    print(f"Skipped (no block key):  {skipped}")
    print(f"Matched pairs:           {len(pairs)}")
    print(f"Duplicate clusters:      {len(dupes)}")
    print(f"Unique customers:        {len(clusters)}")

    for n, members in enumerate(dupes, start=1):
        print(f"\nCluster {n}:")
        for i in members:
            r = records[i]
            print(f"  [{r['id']}] {r['first_name']} {r['last_name']} | "
                  f"{r['email']} | {r['phone']} | {r['postal_code']}")

    if args.output:
        write_clusters(args.output, records, clusters)
        print(f"\nClusters written to {args.output}")
    if args.pairs:
        write_pairs(args.pairs, records, pairs)
        print(f"Pairs written to {args.pairs}")


if __name__ == "__main__":
    main()