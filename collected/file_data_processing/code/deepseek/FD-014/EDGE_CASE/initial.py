"""
Offline Customer Record Matcher
Blocking: surname-initial + postal-prefix
Matching: exact normalized email OR phone
"""

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


# ---------- Normalization helpers ----------

def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower().strip()
    name = re.sub(r"[^a-z\s\-']", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_email(email: str) -> str:
    if not email:
        return ""
    email = email.strip().lower()
    # Strip dots in local part for gmail-style, but keep general: just lowercase + strip
    # Remove plus-tags (common for gmail)
    local, _, domain = email.partition("@")
    local = local.split("+", 1)[0]
    local = local.replace(".", "") if domain in ("gmail.com", "googlemail.com") else local
    return f"{local}@{domain}" if domain else email


def normalize_phone(phone: str, default_country: str = "1") -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return ""
    # Naive US-style: if 10 digits, prepend country code
    if len(digits) == 10:
        digits = default_country + digits
    # Strip leading 00
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def postal_prefix(postal: str, length: int = 3) -> str:
    if not postal:
        return ""
    p = re.sub(r"\s+", "", postal.upper())
    return p[:length]


def surname_initial(surname: str) -> str:
    s = normalize_name(surname)
    return s[:1] if s else ""


# ---------- Record ----------

@dataclass
class CustomerRecord:
    record_id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    postal: str = ""

    # Cached normalized values
    norm_email: str = field(init=False)
    norm_phone: str = field(init=False)
    block_key: str = field(init=False)

    def __post_init__(self):
        self.norm_email = normalize_email(self.email)
        self.norm_phone = normalize_phone(self.phone)
        self.block_key = f"{surname_initial(self.last_name)}|{postal_prefix(self.postal)}"


# ---------- Matcher ----------

class CustomerMatcher:
    def __init__(self, records: List[CustomerRecord]):
        self.records = records
        self.blocks: Dict[str, List[CustomerRecord]] = defaultdict(list)
        self._build_blocks()

    def _build_blocks(self):
        for rec in self.records:
            self.blocks[rec.block_key].append(rec)

    def match(self, query: CustomerRecord) -> List[Tuple[CustomerRecord, str]]:
        """
        Returns list of (matched_record, match_reason) within the same block.
        Match reason: 'email' or 'phone'.
        """
        candidates = self.blocks.get(query.block_key, [])
        results = []
        for cand in candidates:
            if cand.record_id == query.record_id:
                continue
            reasons = []
            if query.norm_email and cand.norm_email and query.norm_email == cand.norm_email:
                reasons.append("email")
            if query.norm_phone and cand.norm_phone and query.norm_phone == cand.norm_phone:
                reasons.append("phone")
            if reasons:
                results.append((cand, "+".join(reasons)))
        return results

    def match_all(self) -> List[Tuple[CustomerRecord, CustomerRecord, str]]:
        """
        Match every record against every other within its block.
        Returns unique pairs (a, b) with a.record_id < b.record_id.
        """
        seen = set()
        pairs = []
        for block in self.blocks.values():
            for i, a in enumerate(block):
                for b in block[i + 1:]:
                    key = tuple(sorted([a.record_id, b.record_id]))
                    if key in seen:
                        continue
                    reasons = []
                    if a.norm_email and a.norm_email == b.norm_email:
                        reasons.append("email")
                    if a.norm_phone and a.norm_phone == b.norm_phone:
                        reasons.append("phone")
                    if reasons:
                        seen.add(key)
                        pairs.append((a, b, "+".join(reasons)))
        return pairs


# ---------- Demo ----------

if __name__ == "__main__":
    records = [
        CustomerRecord("1", "John", "Smith", "john.smith@gmail.com", "555-123-4567", "90210"),
        CustomerRecord("2", "Jon", "Smith", "johnsmith@gmail.com", "5551234567", "90210-1234"),
        CustomerRecord("3", "Jane", "Smith", "jane@example.com", "555-999-8888", "90210"),
        CustomerRecord("4", "Bob", "Jones", "bob@example.com", "555-111-2222", "10001"),
        CustomerRecord("5", "Robert", "Jones", "bob@example.com", "555-333-4444", "10001"),
        CustomerRecord("6", "Alice", "Brown", "alice@x.com", "555-777-6666", "90211"),
        CustomerRecord("7", "Alicia", "Brown", "alice@x.com", "555-777-6666", "90211"),
    ]

    matcher = CustomerMatcher(records)

    print("=== All pairwise matches within blocks ===")
    for a, b, reason in matcher.match_all():
        print(f"{a.record_id} <-> {b.record_id}  ({reason})  block={a.block_key}")

    print("\n=== Query: single record match ===")
    query = CustomerRecord("Q", "Johnny", "Smith", "john.smith@gmail.com", "", "90210")
    for cand, reason in matcher.match(query):
        print(f"Q matched {cand.record_id} via {reason}")