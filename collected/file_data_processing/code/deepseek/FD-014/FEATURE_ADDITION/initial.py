"""
Offline customer record matcher.

Blocking strategy:
  - Block key = (surname_initial, postal_prefix)
    where surname_initial = first letter of normalized surname (or '#' if empty)
    and postal_prefix   = first 3 alphanumeric chars of normalized postal code (or '#' if empty)

Match rule (within a block):
  - Exact match on normalized email, OR
  - Exact match on normalized phone (digits only, last 10 digits)

Records that lack both email and phone are still indexed but will never match
on those fields; they can still be blocked/grouped for downstream inspection.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ----------------------------- normalization -----------------------------

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_DIGITS = re.compile(r"\D+")


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize_name(s: Optional[str]) -> str:
    if not s:
        return ""
    s = _strip_accents(s).lower()
    s = _NON_ALNUM.sub(" ", s).strip()
    return s


def normalize_email(s: Optional[str]) -> str:
    if not s:
        return ""
    return s.strip().lower()


def normalize_phone(s: Optional[str]) -> str:
    """Return last 10 digits, or '' if fewer than 10 digits present."""
    if not s:
        return ""
    digits = _DIGITS.sub("", s)
    if len(digits) < 10:
        return ""
    return digits[-10:]


def normalize_postal(s: Optional[str]) -> str:
    if not s:
        return ""
    s = _strip_accents(s).lower()
    return _NON_ALNUM.sub("", s)


# ----------------------------- record model ------------------------------

@dataclass
class Customer:
    id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    postal_code: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    # derived
    _surname_initial: str = field(init=False, repr=False)
    _postal_prefix: str = field(init=False, repr=False)
    _email_norm: str = field(init=False, repr=False)
    _phone_norm: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        last = normalize_name(self.last_name)
        # Fall back to first token of first_name if no surname provided
        if not last and self.first_name:
            last = normalize_name(self.first_name).split(" ")[0]
        self._surname_initial = last[0] if last else "#"

        postal = normalize_postal(self.postal_code)
        self._postal_prefix = postal[:3] if postal else "#"

        self._email_norm = normalize_email(self.email)
        self._phone_norm = normalize_phone(self.phone)

    @property
    def block_key(self) -> Tuple[str, str]:
        return (self._surname_initial, self._postal_prefix)


# ----------------------------- match result ------------------------------

@dataclass
class MatchGroup:
    """A set of records considered to be the same customer."""
    records: List[Customer]

    @property
    def ids(self) -> List[str]:
        return [r.id for r in self.records]

    def evidence(self) -> List[str]:
        """Human-readable reasons the group is linked (email/phone exact match)."""
        emails = {r._email_norm for r in self.records if r._email_norm}
        phones = {r._phone_norm for r in self.records if r._phone_norm}
        ev: List[str] = []
        for e in emails:
            ev.append(f"email={e}")
        for p in phones:
            ev.append(f"phone={p}")
        return ev


# ----------------------------- matcher -----------------------------------

class CustomerMatcher:
    def __init__(self, records: Iterable[Customer]):
        self.records: List[Customer] = list(records)
        self._by_block: Dict[Tuple[str, str], List[Customer]] = defaultdict(list)
        for r in self.records:
            self._by_block[r.block_key].append(r)

    # --- public API ---
    def match_all(self) -> List[MatchGroup]:
        """Return all match groups (size >= 2) found across all blocks."""
        groups: List[MatchGroup] = []
        for key, block in self._by_block.items():
            if len(block) < 2:
                continue
            groups.extend(self._match_block(block))
        return groups

    def find_matches(self, query: Customer) -> List[Customer]:
        """Return records in the same block that share email or phone with query."""
        candidates = self._by_block.get(query.block_key, [])
        out: List[Customer] = []
        for c in candidates:
            if c.id == query.id:
                continue
            if self._pair_matches(query, c):
                out.append(c)
        return out

    # --- internals ---
    @staticmethod
    def _pair_matches(a: Customer, b: Customer) -> bool:
        if a._email_norm and a._email_norm == b._email_norm:
            return True
        if a._phone_norm and a._phone_norm == b._phone_norm:
            return True
        return False

    def _match_block(self, block: Sequence[Customer]) -> List[MatchGroup]:
        """Union-Find within a block using email/phone equality."""
        parent = list(range(len(block)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        # Index by email and phone to avoid O(n^2) when possible
        by_email: Dict[str, int] = {}
        by_phone: Dict[str, int] = {}
        for i, c in enumerate(block):
            if c._email_norm:
                if c._email_norm in by_email:
                    union(i, by_email[c._email_norm])
                else:
                    by_email[c._email_norm] = i
            if c._phone_norm:
                if c._phone_norm in by_phone:
                    union(i, by_phone[c._phone_norm])
                else:
                    by_phone[c._phone_norm] = i

        groups: Dict[int, List[Customer]] = defaultdict(list)
        for i, c in enumerate(block):
            groups[find(i)].append(c)

        return [MatchGroup(records=recs) for recs in groups.values() if len(recs) >= 2]


# ----------------------------- demo --------------------------------------

if __name__ == "__main__":
    records = [
        Customer("1", "John",  "Smith",   "J.Smith@Example.com", "1-555-123-4567", "94103"),
        Customer("2", "Jon",   "Smith",   "jsmith@example.com",  "5551234567",     "94103-1234"),
        Customer("3", "Jane",  "Smith",   "jane@example.com",    "555-999-0000",   "94105"),
        Customer("4", "Bob",   "Jones",   "bob@example.com",     "555-222-3333",   "10001"),
        Customer("5", "Rob",   "Jones",   "bob@example.com",     "555-222-3333",   "10001"),
        Customer("6", "Alice", "O'Brien", "alice@example.com",   "555-444-5555",   "SW1A 1AA"),
        Customer("7", "Alicia","OBrien",  "ALICE@example.com",   "5554445555",     "SW1A1AA"),
        Customer("8", "Carl",  "Nguyen",  "",                    "",               "94103"),
    ]

    matcher = CustomerMatcher(records)
    groups = matcher.match_all()

    print(f"Found {len(groups)} match group(s):\n")
    for i, g in enumerate(groups, 1):
        print(f"Group {i}: ids={g.ids}")
        for r in g.records:
            print(
                f"  - id={r.id:<3} name={r.first_name} {r.last_name:<8} "
                f"email={r.email:<22} phone={r.phone:<15} postal={r.postal_code}"
            )
        print(f"  evidence: {', '.join(g.evidence())}\n")

    # Ad-hoc query
    q = Customer("q", "J", "Smith", "jsmith@example.com", "", "94103")
    print(f"Query {q.id} matches: {[c.id for c in matcher.find_matches(q)]}")