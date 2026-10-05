#!/usr/bin/env python3
"""
customer_matcher.py - offline customer record matcher (standard library only).

Pipeline
  1. Normalize   surname, postal code, email, phone
  2. Block       key = <surname initial> + <postal prefix>   (e.g. "S|941")
  3. Match       inside each block, two records match if they share an exact
                 normalized email OR an exact normalized phone number
  4. Cluster     union-find over matched pairs -> one cluster per customer

Only records in the same block are compared, so a true duplicate with a
different surname initial or postal prefix will NOT be found.

Usage
  python customer_matcher.py customers.csv
  python customer_matcher.py a.csv b.csv --out-dir results --postal-prefix-len 3
  python customer_matcher.py customers.csv --surname-col last_name --postal-col zip
  python customer_matcher.py --demo

Outputs (in --out-dir): matches.csv, clusters.csv, flags.csv
"""

import argparse
import csv
import os
import re
import sys
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_EXT_RE = re.compile(r"(?i)\s*(?:x|ext\.?|extension)\s*\d+\s*$")
_FAKE_PHONES = {"1234567890", "0123456789", "9876543210", "1234567", "12345678"}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def surname_initial(raw: str) -> Optional[str]:
    """First letter of the surname, accent- and case-insensitive."""
    for ch in strip_accents(raw or "").upper():
        if ch.isalpha():
            return ch
    return None


def postal_prefix(raw: str, length: int) -> Optional[str]:
    """First `length` alphanumeric chars, uppercased ('M5V 2T6' -> 'M5V')."""
    cleaned = re.sub(r"[^A-Z0-9]", "", strip_accents(raw or "").upper())
    if len(cleaned) < length:
        return None
    return cleaned[:length]


def normalize_email(raw: str, gmail_canon: bool = False) -> Optional[str]:
    """Lowercase + trim. With gmail_canon, drop dots and +tags on Gmail."""
    if not raw:
        return None
    email = raw.strip().strip("<>").lower()
    if email.startswith("mailto:"):
        email = email[7:]
    if not _EMAIL_RE.match(email):
        return None
    local, _, domain = email.rpartition("@")
    if domain == "googlemail.com":
        domain = "gmail.com"
    if gmail_canon and domain == "gmail.com":
        local = local.split("+", 1)[0].replace(".", "")
        if not local:
            return None
    return f"{local}@{domain}"


def normalize_phone(raw: str, default_cc: str = "1") -> Optional[str]:
    """
    Digits only, extension removed. If the number is default_cc + 10 digits,
    the country code is dropped so '+1 (415) 555-0100' == '415-555-0100'.
    Returns None for too-short, too-long, repeated-digit or placeholder numbers.
    """
    if not raw:
        return None
    text = _EXT_RE.sub("", raw.strip())
    digits = re.sub(r"\D", "", text)
    if digits.startswith("00"):  # international dialing prefix
        digits = digits[2:]
    if default_cc and digits.startswith(default_cc) and len(digits) == len(default_cc) + 10:
        digits = digits[len(default_cc):]
    if not 7 <= len(digits) <= 15:
        return None
    if len(set(digits)) == 1 or digits in _FAKE_PHONES:
        return None
    return digits


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class Record:
    uid: str                       # unique across all input files ("file:id")
    source: str
    raw: Dict[str, str]
    block: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    order: int = 0


@dataclass
class Config:
    id_col: str = "id"
    surname_col: str = "surname"
    postal_col: str = "postal_code"
    email_col: str = "email"
    phone_col: str = "phone"
    postal_prefix_len: int = 3
    default_cc: str = "1"
    gmail_canon: bool = False
    max_group_size: int = 10       # a value shared by more records than this is ignored
    include_singletons: bool = False


@dataclass
class Result:
    records: List[Record] = field(default_factory=list)
    pairs: Dict[Tuple[int, int], set] = field(default_factory=dict)
    clusters: Dict[int, List[int]] = field(default_factory=dict)
    flags: List[Dict[str, str]] = field(default_factory=list)
    block_count: int = 0


# --------------------------------------------------------------------------
# Union-find
# --------------------------------------------------------------------------

class DisjointSet:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if ra < rb:
                self.parent[rb] = ra
            else:
                self.parent[ra] = rb


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_records(paths: List[str], cfg: Config) -> List[Record]:
    records: List[Record] = []
    for path in paths:
        source = os.path.basename(path)
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                continue
            missing = [c for c in (cfg.surname_col, cfg.postal_col) if c not in reader.fieldnames]
            if missing:
                raise SystemExit(
                    f"{path}: missing required column(s) {missing}. "
                    f"Found: {reader.fieldnames}. Use --surname-col / --postal-col."
                )
            if cfg.email_col not in reader.fieldnames and cfg.phone_col not in reader.fieldnames:
                raise SystemExit(f"{path}: needs at least one of '{cfg.email_col}' or '{cfg.phone_col}' columns.")
            for rownum, row in enumerate(reader, start=1):
                rid = (row.get(cfg.id_col) or "").strip() or f"row{rownum}"
                records.append(Record(uid=f"{source}:{rid}", source=source, raw=row, order=len(records)))
    return records


# --------------------------------------------------------------------------
# Core matching
# --------------------------------------------------------------------------

def match(records: List[Record], cfg: Config) -> Result:
    res = Result(records=records)

    # 1-2. normalize + block
    blocks: Dict[str, List[int]] = defaultdict(list)
    for idx, rec in enumerate(records):
        rec.email = normalize_email(rec.raw.get(cfg.email_col, ""), cfg.gmail_canon)
        rec.phone = normalize_phone(rec.raw.get(cfg.phone_col, ""), cfg.default_cc)
        initial = surname_initial(rec.raw.get(cfg.surname_col, ""))
        prefix = postal_prefix(rec.raw.get(cfg.postal_col, ""), cfg.postal_prefix_len)
        if initial is None or prefix is None:
            reason = "no usable surname initial" if initial is None else "no usable postal prefix"
            res.flags.append({"type": "unblockable", "record": rec.uid, "block": "", "detail": reason})
            continue
        rec.block = f"{initial}|{prefix}"
        blocks[rec.block].append(idx)
    res.block_count = len(blocks)

    # 3. exact email / phone matching inside each block (hash index, not O(n^2))
    dsu = DisjointSet(len(records))
    for block_key, members in blocks.items():
        if len(members) < 2:
            continue
        for kind in ("email", "phone"):
            index: Dict[str, List[int]] = defaultdict(list)
            for idx in members:
                value = getattr(records[idx], kind)
                if value:
                    index[value].append(idx)
            for value, group in index.items():
                if len(group) < 2:
                    continue
                if len(group) > cfg.max_group_size:
                    res.flags.append({
                        "type": "shared_value_ignored",
                        "record": "; ".join(records[i].uid for i in group[:5]) + (" ..." if len(group) > 5 else ""),
                        "block": block_key,
                        "detail": f"{kind} '{value}' shared by {len(group)} records (> {cfg.max_group_size})",
                    })
                    continue
                for a, b in combinations(group, 2):
                    res.pairs.setdefault((a, b), set()).add(kind)
                    dsu.union(a, b)

    # 4. clusters
    groups: Dict[int, List[int]] = defaultdict(list)
    for idx in range(len(records)):
        groups[dsu.find(idx)].append(idx)
    for root, members in groups.items():
        if len(members) > 1 or cfg.include_singletons:
            res.clusters[root] = members
    return res


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_outputs(res: Result, cfg: Config, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    recs = res.records

    with open(os.path.join(out_dir, "matches.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_a", "record_b", "block", "matched_on", "email_a", "email_b", "phone_a", "phone_b"])
        for (a, b), reasons in sorted(res.pairs.items()):
            ra, rb = recs[a], recs[b]
            w.writerow([ra.uid, rb.uid, ra.block, "+".join(sorted(reasons)),
                        ra.email or "", rb.email or "", ra.phone or "", rb.phone or ""])

    with open(os.path.join(out_dir, "clusters.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cluster_id", "cluster_size", "record", "block", "surname", "postal_code",
                    "email_norm", "phone_norm"])
        for n, root in enumerate(sorted(res.clusters), start=1):
            members = res.clusters[root]
            for idx in members:
                r = recs[idx]
                w.writerow([f"C{n:05d}", len(members), r.uid, r.block or "",
                            r.raw.get(cfg.surname_col, ""), r.raw.get(cfg.postal_col, ""),
                            r.email or "", r.phone or ""])

    with open(os.path.join(out_dir, "flags.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["type", "record", "block", "detail"])
        w.writeheader()
        w.writerows(res.flags)


def print_summary(res: Result, out_dir: str) -> None:
    multi = [m for m in res.clusters.values() if len(m) > 1]
    in_clusters = sum(len(m) for m in multi)
    unblockable = sum(1 for f in res.flags if f["type"] == "unblockable")
    shared = sum(1 for f in res.flags if f["type"] == "shared_value_ignored")
    print(f"Records loaded        : {len(res.records)}")
    print(f"Blocks formed         : {res.block_count}")
    print(f"Unblockable records   : {unblockable}")
    print(f"Matched pairs         : {len(res.pairs)}")
    print(f"Multi-record clusters : {len(multi)} ({in_clusters} records)")
    print(f"Shared values ignored : {shared}")
    print(f"Output written to     : {os.path.abspath(out_dir)}")


# --------------------------------------------------------------------------
# Demo data
# --------------------------------------------------------------------------

DEMO_CSV = """id,surname,first_name,postal_code,email,phone
1,Smith,Ann,94107-1234,Ann.Smith@Example.com,(415) 555-0142
2,SMITH,Anne,94107,ann.smith@example.com ,
3,Smyth,A.,94107,,+1 415 555 0142
4,Smith,Robert,94107,bob@example.com,415-555-0199 x22
5,Smith,Bob,94107,BOB@example.com,
6,Müller,Jens,10115,jens@example.de,+49 30 1234 5678
7,Muller,Jens,10115,,0049 30 1234 5678
8,Jones,Pat,M5V 2T6,info@shop.example,416-555-0111
9,Jones,Lee,M5V 2T6,info@shop.example,416-555-0222
10,Jones,Sam,M5V 2T6,info@shop.example,416-555-0333
11,Brown,Kim,60601,kim@example.com,
12,Brown,Kim,90210,kim@example.com,
13,,Nobody,60601,nobody@example.com,
"""


def run_demo(cfg: Config) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "demo_customers.csv")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(DEMO_CSV)
        cfg.max_group_size = 2  # shows the shared-mailbox guard on ids 8-10
        out_dir = "matcher_demo_out"
        res = match(load_records([src], cfg), cfg)
        write_outputs(res, cfg, out_dir)
        print_summary(res, out_dir)
        print("\nExpected: {1,2,3}, {4,5}, {6,7} cluster; 8-10 ignored (shared mailbox);")
        print("11/12 NOT matched (different postal prefix -> different block); 13 unblockable.")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline customer record matcher "
                                            "(surname-initial/postal-prefix blocking, exact email/phone match).")
    p.add_argument("inputs", nargs="*", help="one or more CSV files (UTF-8)")
    p.add_argument("--out-dir", default="matcher_out", help="output directory (default: matcher_out)")
    p.add_argument("--id-col", default="id")
    p.add_argument("--surname-col", default="surname")
    p.add_argument("--postal-col", default="postal_code")
    p.add_argument("--email-col", default="email")
    p.add_argument("--phone-col", default="phone")
    p.add_argument("--postal-prefix-len", type=int, default=3, help="postal chars in block key (default 3)")
    p.add_argument("--default-cc", default="1", help="country code stripped from phones (default 1; '' to disable)")
    p.add_argument("--gmail-canon", action="store_true", help="treat Gmail dots and +tags as insignificant")
    p.add_argument("--max-group-size", type=int, default=10,
                   help="ignore an email/phone shared by more records than this within a block (default 10)")
    p.add_argument("--include-singletons", action="store_true", help="also list unmatched records in clusters.csv")
    p.add_argument("--demo", action="store_true", help="run on built-in sample data")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    cfg = Config(
        id_col=args.id_col, surname_col=args.surname_col, postal_col=args.postal_col,
        email_col=args.email_col, phone_col=args.phone_col,
        postal_prefix_len=args.postal_prefix_len, default_cc=args.default_cc,
        gmail_canon=args.gmail_canon, max_group_size=args.max_group_size,
        include_singletons=args.include_singletons,
    )
    if args.demo:
        run_demo(cfg)
        return 0
    if not args.inputs:
        print("error: provide at least one CSV file, or use --demo", file=sys.stderr)
        return 2
    res = match(load_records(args.inputs, cfg), cfg)
    write_outputs(res, cfg, args.out_dir)
    print_summary(res, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())