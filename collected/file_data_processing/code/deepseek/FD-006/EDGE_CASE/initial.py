import csv
import re
from typing import Optional

PHONE_DIGITS_RE = re.compile(r"\d")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: Optional[str]) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def normalize_phone(value: Optional[str], default_region: str = "1") -> str:
    if value is None:
        return ""
    raw = value.strip()
    if not raw:
        return ""

    # Handle extensions: strip everything after 'ext', 'x', '#'
    raw = re.split(r"(?i)\b(?:ext\.?|x|#)\b", raw)[0]

    digits = "".join(PHONE_DIGITS_RE.findall(raw))
    if not digits:
        return ""

    has_plus = raw.strip().startswith("+")

    if has_plus:
        return "+" + digits
    if len(digits) == 10:
        return "+" + default_region + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return "+" + digits if len(digits) > 11 else digits


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def completeness_score(record: dict, fields: list) -> int:
    return sum(1 for f in fields if (record.get(f) or "").strip())


def normalize_records(rows: list, fields: list) -> list:
    for row in rows:
        row["email"] = normalize_email(row.get("email"))
        row["phone"] = normalize_phone(row.get("phone"))

    groups = {}
    for idx, row in enumerate(rows):
        key = row["email"]
        if not key:
            key = f"__invalid__::{idx}"
        groups.setdefault(key, []).append((idx, row))

    chosen = []
    for key, items in groups.items():
        # Sort by completeness desc, then original row index asc
        items_sorted = sorted(
            items,
            key=lambda t: (-completeness_score(t[1], fields), t[0]),
        )
        chosen.append((key, items_sorted[0][1]))

    chosen.sort(key=lambda t: t[0])
    return [r for _, r in chosen]


def normalize_csv(input_path: str, output_path: str, default_region: str = "1") -> None:
    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = [dict(r) for r in reader]

    # Ensure email/phone fields exist
    for f in ("email", "phone"):
        if f not in fields:
            fields.append(f)
            for r in rows:
                r.setdefault(f, "")

    for row in rows:
        row["email"] = normalize_email(row.get("email"))
        row["phone"] = normalize_phone(row.get("phone"), default_region)

    groups = {}
    for idx, row in enumerate(rows):
        key = row["email"] if is_valid_email(row["email"]) else f"__invalid__::{idx}"
        groups.setdefault(key, []).append((idx, row))

    chosen = []
    for key, items in groups.items():
        best = min(
            items,
            key=lambda t: (-completeness_score(t[1], fields), t[0]),
        )
        chosen.append((key, best[1]))

    chosen.sort(key=lambda t: t[0])
    output_rows = [r for _, r in chosen]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({f: row.get(f, "") for f in fields})


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python normalizer.py <input.csv> <output.csv> [default_region]")
        sys.exit(1)

    region = sys.argv[3] if len(sys.argv) > 3 else "1"
    normalize_csv(sys.argv[1], sys.argv[2], region)