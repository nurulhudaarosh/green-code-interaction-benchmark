"""
Offline customer record matcher.

Pipeline:
  1. Normalize fields (email, phone, surname, postal code).
  2. Blocking: group records by (surname initial, postal prefix).
  3. Within each block, link records that share an exact normalized
     email or phone number.
  4. Merge linked records into clusters via union-find.

No network access or third-party packages required.
"""

import csv
import re
import sys
import unicodedata
from collections import defaultdict
from itertools import combinations


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def normalize_email(email: str) -> str:
    """Lowercase, trim, strip +tags; drop dots for gmail-style domains."""
    if not email:
        return ""
    email = email.strip().lower()
    if email.count("@") != 1:
        return ""
    local, domain = email.split("@")
    if not local or not domain or "." not in domain:
        return ""
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}" if local else ""


def normalize_phone(phone: str, default_country_code: str = "1") -> str:
    """Keep digits only; apply a default country code to 10-digit numbers.
    Returns '' for numbers too short to be meaningful."""
    if not phone:
        return ""
    phone = phone.strip()
    # Drop extensions like "x123" or "ext. 123"
    phone = re.split(r"(?i)\s*(?:ext\.?|x)\s*\d+$", phone)[0]
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("00"):          # international prefix
        digits = digits[2:]
    elif len(digits) == 10:
        digits = default_country_code + digits
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if len(digits) >= 7 else ""


def normalize_surname(name: str) -> str:
    if not name:
        return ""
    name = strip_accents(name).lower().strip()
    return re.sub(r"[^a-z]", "", name)


def normalize_postal(postal: str) -> str:
    if not postal:
        return ""
    return re.sub(r"[^A-Z0-9]", "", postal.upper())


def surname_initial(surname: str) -> str:
    s = normalize_surname(surname)
    return s[0] if s else ""


def postal_prefix(postal: str, length: int = 3) -> str:
    return normalize_postal(postal)[:length]


# --------------------------------------------------------------------------
# Union-Find
# --------------------------------------------------------------------------

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)  # keep lowest id as root


# --------------------------------------------------------------------------
# Matcher
# --------------------------------------------------------------------------

class CustomerMatcher:
    def __init__(self, postal_prefix_len: int = 3, default_country_code: str = "1"):
        self.postal_prefix_len = postal_prefix_len
        self.cc = default_country_code

    def prepare(self, records):
        """Attach normalized fields and blocking key to each record."""
        prepared = []
        for i, rec in enumerate(records):
            prepared.append({
                "_idx": i,
                "_raw": rec,
                "email": normalize_email(rec.get("email", "")),
                "phone": normalize_phone(rec.get("phone", ""), self.cc),
                "block": (
                    surname_initial(rec.get("surname", "")),
                    postal_prefix(rec.get("postal_code", ""), self.postal_prefix_len),
                ),
            })
        return prepared

    @staticmethod
    def build_blocks(prepared):
        blocks = defaultdict(list)
        for rec in prepared:
            initial, prefix = rec["block"]
            if not initial or not prefix:
                continue  # can't block -> unmatchable under this strategy
            blocks[rec["block"]].append(rec)
        return blocks

    @staticmethod
    def match_block(block_records):
        """Yield (idx_a, idx_b, reason) for pairs sharing email or phone."""
        by_email, by_phone = defaultdict(list), defaultdict(list)
        for rec in block_records:
            if rec["email"]:
                by_email[rec["email"]].append(rec["_idx"])
            if rec["phone"]:
                by_phone[rec["phone"]].append(rec["_idx"])

        pairs = {}
        for key, ids in by_email.items():
            for a, b in combinations(ids, 2):
                pairs.setdefault((a, b), set()).add("email")
        for key, ids in by_phone.items():
            for a, b in combinations(ids, 2):
                pairs.setdefault((a, b), set()).add("phone")

        for (a, b), reasons in pairs.items():
            yield a, b, sorted(reasons)

    def run(self, records):
        prepared = self.prepare(records)
        blocks = self.build_blocks(prepared)

        uf = UnionFind()
        for rec in prepared:
            uf.find(rec["_idx"])

        match_pairs = []
        for block_key, block_records in blocks.items():
            if len(block_records) < 2:
                continue
            for a, b, reasons in self.match_block(block_records):
                uf.union(a, b)
                match_pairs.append({"a": a, "b": b, "reasons": reasons,
                                    "block": block_key})

        clusters = defaultdict(list)
        for rec in prepared:
            clusters[uf.find(rec["_idx"])].append(rec["_idx"])

        return {
            "pairs": match_pairs,
            "clusters": [sorted(v) for v in clusters.values()],
            "stats": {
                "records": len(records),
                "blocks": len(blocks),
                "unblockable": sum(
                    1 for r in prepared if not all(r["block"])
                ),
                "match_pairs": len(match_pairs),
                "duplicate_clusters": sum(
                    1 for v in clusters.values() if len(v) > 1
                ),
            },
        }


# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------

def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_clusters_csv(path, records, result):
    """Write each record with a cluster_id; only the lowest idx is canonical."""
    cluster_of = {}
    for cluster in result["clusters"]:
        cid = cluster[0]
        for idx in cluster:
            cluster_of[idx] = cid

    fieldnames = list(records[0].keys()) + ["cluster_id", "is_duplicate"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for i, rec in enumerate(records):
            row = dict(rec)
            row["cluster_id"] = cluster_of[i]
            row["is_duplicate"] = cluster_of[i] != i
            w.writerow(row)


# --------------------------------------------------------------------------
# Demo / CLI
# --------------------------------------------------------------------------

def demo():
    records = [
        {"id": "1", "surname": "Smith",   "postal_code": "90210",   "email": "John.Smith@gmail.com", "phone": "(310) 555-0100"},
        {"id": "2", "surname": "Smythe",  "postal_code": "90211",   "email": "johnsmith+promo@gmail.com", "phone": ""},
        {"id": "3", "surname": "Smith",   "postal_code": "90210",   "email": "",                      "phone": "+1 310-555-0100 x22"},
        {"id": "4", "surname": "Jones",   "postal_code": "10001",   "email": "ajones@example.com",    "phone": "212 555 0199"},
        {"id": "5", "surname": "Jones",   "postal_code": "10001",   "email": "AJONES@EXAMPLE.COM",    "phone": ""},
        {"id": "6", "surname": "Jones",   "postal_code": "94105",   "email": "ajones@example.com",    "phone": ""},  # different block
        {"id": "7", "surname": "Müller",  "postal_code": "80331",   "email": "",                      "phone": ""},  # no contact data
    ]

    matcher = CustomerMatcher(postal_prefix_len=3)
    result = matcher.run(records)

    print("Stats:", result["stats"])
    print("\nMatched pairs:")
    for p in result["pairs"]:
        a, b = records[p["a"]]["id"], records[p["b"]]["id"]
        print(f"  id {a} <-> id {b}  via {p['reasons']}  block={p['block']}")

    print("\nDuplicate clusters:")
    for c in result["clusters"]:
        if len(c) > 1:
            print("  ", [records[i]["id"] for i in c])


if __name__ == "__main__":
    if len(sys.argv) == 3:
        recs = load_csv(sys.argv[1])
        res = CustomerMatcher().run(recs)
        write_clusters_csv(sys.argv[2], recs, res)
        print(res["stats"])
    else:
        demo()