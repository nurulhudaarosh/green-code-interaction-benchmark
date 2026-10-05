"""
Offline Customer Record Matcher
--------------------------------
Blocks candidate pairs using:
  - surname-initial + postal-prefix (e.g. "S" + "M5V")
  - exact normalized email
  - exact normalized phone (digits only, last 10)

Then confirms matches by exact normalized email or phone.
Pure standard library, no network required.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Iterable, Iterator


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_NON_DIGIT = re.compile(r"\D+")
_WS = re.compile(r"\s+")


def normalize_email(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def normalize_phone(value: str | None) -> str:
    """Return the last 10 digits (handles +1, dashes, parens, extensions)."""
    if not value:
        return ""
    digits = _NON_DIGIT.sub("", value)
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_name(value: str | None) -> str:
    """Strip accents, lowercase, remove punctuation/extra whitespace."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z\s\-']", " ", value)
    return _WS.sub(" ", value).strip()


def surname_initial(surname: str | None) -> str:
    s = normalize_name(surname)
    return s[0] if s else ""


def postal_prefix(postal: str | None, length: int = 3) -> str:
    """Take first `length` alphanumeric characters of the postal code (uppercased)."""
    if not postal:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", postal).upper()
    return cleaned[:length]


# ---------------------------------------------------------------------------
# Record model
# ---------------------------------------------------------------------------

@dataclass
class Customer:
    id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    postal: str = ""

    # Derived / cached fields
    _n_email: str = field(default="", init=False, repr=False)
    _n_phone: str = field(default="", init=False, repr=False)
    _surname_initial: str = field(default="", init=False, repr=False)
    _postal_prefix: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        self._n_email = normalize_email(self.email)
        self._n_phone = normalize_phone(self.phone)
        self._surname_initial = surname_initial(self.last_name)
        self._postal_prefix = postal_prefix(self.postal)

    @property
    def n_email(self) -> str:
        return self._n_email

    @property
    def n_phone(self) -> str:
        return self._n_phone

    @property
    def surname_initial(self) -> str:
        return self._surname_initial

    @property
    def postal_prefix(self) -> str:
        return self._postal_prefix

    @property
    def block_key(self) -> tuple[str, str] | None:
        """Surname-initial + postal-prefix block key, or None if either missing."""
        if self._surname_initial and self._postal_prefix:
            return (self._surname_initial, self._postal_prefix)
        return None


# ---------------------------------------------------------------------------
# Matching engine
# ---------------------------------------------------------------------------

@dataclass
class Match:
    a: Customer
    b: Customer
    reason: str  # "email" | "phone" | "email+phone"


class CustomerMatcher:
    def __init__(self) -> None:
        self._by_email: dict[str, list[Customer]] = defaultdict(list)
        self._by_phone: dict[str, list[Customer]] = defaultdict(list)
        self._by_block: dict[tuple[str, str], list[Customer]] = defaultdict(list)

    # ----- indexing -----

    def add(self, customer: Customer) -> None:
        if customer.n_email:
            self._by_email[customer.n_email].append(customer)
        if customer.n_phone:
            self._by_phone[customer.n_phone].append(customer)
        if customer.block_key is not None:
            self._by_block[customer.block_key].append(customer)

    def extend(self, customers: Iterable[Customer]) -> None:
        for c in customers:
            self.add(c)

    # ----- candidate generation -----

    def _candidate_pairs(self) -> Iterator[tuple[Customer, Customer]]:
        """Yield unique unordered pairs that share a block key OR an exact email/phone."""
        seen: set[tuple[str, str]] = set()

        def emit(a: Customer, b: Customer) -> Iterator[tuple[Customer, Customer]]:
            if a.id == b.id:
                return
            key = (a.id, b.id) if a.id < b.id else (b.id, a.id)
            if key in seen:
                return
            seen.add(key)
            yield (a, b)

        # Block: surname-initial + postal-prefix
        for bucket in self._by_block.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    yield from emit(bucket[i], bucket[j])

        # Exact email
        for bucket in self._by_email.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    yield from emit(bucket[i], bucket[j])

        # Exact phone
        for bucket in self._by_phone.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    yield from emit(bucket[i], bucket[j])

    # ----- matching -----

    @staticmethod
    def _reason(a: Customer, b: Customer) -> str | None:
        email_hit = bool(a.n_email) and a.n_email == b.n_email
        phone_hit = bool(a.n_phone) and a.n_phone == b.n_phone
        if email_hit and phone_hit:
            return "email+phone"
        if email_hit:
            return "email"
        if phone_hit:
            return "phone"
        return None

    def find_matches(self) -> list[Match]:
        results: list[Match] = []
        for a, b in self._candidate_pairs():
            reason = self._reason(a, b)
            if reason:
                results.append(Match(a=a, b=b, reason=reason))
        return results


# ---------------------------------------------------------------------------
# CSV loader (adjust column names as needed)
# ---------------------------------------------------------------------------

def load_customers_from_csv(path: str) -> list[Customer]:
    customers: list[Customer] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            customers.append(
                Customer(
                    id=row.get("id") or f"row-{i}",
                    first_name=row.get("first_name", "") or "",
                    last_name=row.get("last_name", "") or "",
                    email=row.get("email", "") or "",
                    phone=row.get("phone", "") or "",
                    postal=row.get("postal", "") or "",
                )
            )
    return customers


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo() -> None:
    customers = [
        Customer("1", "Jane", "Smith", "jane.smith@example.com", "416-555-1234", "M5V 2T6"),
        Customer("2", "J.",   "Smith", "JANE.SMITH@example.com ", "(416) 555-1234", "M5V 3A1"),
        Customer("3", "Bob",  "Smith", "bob@example.com",       "647-555-9999", "M5V 1A1"),
        Customer("4", "Alice","Jones", "alice@example.com",     "+1 416 555 1234", "K1A 0B1"),
        Customer("5", "Jane", "Smyth", "jane.smith@example.com", "",             "M5V 9Z9"),
        Customer("6", "Carl", "Brown", "carl@example.com",      "4165551234",   "L5B 2C3"),
    ]

    matcher = CustomerMatcher()
    matcher.extend(customers)
    matches = matcher.find_matches()

    print(f"Found {len(matches)} match(es):\n")
    for m in matches:
        print(f"  [{m.reason}] {m.a.id} ({m.a.first_name} {m.a.last_name})"
              f"  <->  {m.b.id} ({m.b.first_name} {m.b.last_name})")


if __name__ == "__main__":
    _demo()