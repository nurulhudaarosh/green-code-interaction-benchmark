import csv
import re
import sys
from typing import Optional

PHONE_DIGITS_RE = re.compile(r"\d")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: Optional[str]) -> str:
    """Lowercase, strip whitespace, and collapse internal whitespace around @ and ."""
    if value is None:
        return ""
    s = value.strip().lower()
    # Remove all whitespace inside the email (handles " foo @ bar . com ")
    s = re.sub(r"\s+", "", s)
    return s


def normalize_phone(value: Optional[str], default_region: str = "1") -> str:
    """Strip all non-digit characters, then format as E.164-ish."""
    if value is None:
        return ""
    raw = value.strip()
    if not raw:
        return ""

    # Cut off extensions: ext, x, #, or comma followed by digits
    raw = re.split(r"(?i)\b(?:ext\.?|extension|x|#)\b|,", raw)[0]

    has_plus = raw.lstrip().startswith("+")

    digits = "".join(PHONE_DIGITS_RE.findall(raw))
    if not digits:
        return ""

    if has_plus:
        return "+" + digits
    if len(digits) == 10:
        return "+" + default_region + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    if len(digits) > 11:
        return "+" + digits
    return digits


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def completeness_score(record: dict, fields: list) -> int:
    """Count non-empty fields, treating normalized email/phone as filled."""
    score = 0
    for f in fields:
        v = record.get(f)
        if v is None:
            continue
        if str(v).strip():
            score += 1
    return score


def _key_for(row: dict, idx: int) -> str:
    email = row.get("email", "")
    if is_valid_email(email):
        return email
    # Group all invalid/blank emails separately by row so they aren't merged
    return f"\uffff__invalid__::{idx:08d}"


def normalize_csv(input_path: str, output_path: str, default_region: str = "1") -> None:
    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]

    # Ensure required fields are present
    for f in ("email", "phone"):
        if f not in fields:
            fields.append(f)
            for r in rows:
                r.setdefault(f, "")

    # Normalize each record
    for row in rows:
        row["email"] = normalize_email(row.get("email"))
        row["phone"] = normalize_phone(row.get("phone"), default_region)

    # Group by normalized email (invalid/blank emails kept as distinct groups)
    groups: dict = {}
    for idx, row in enumerate(rows):
        key = _key_for(row, idx)
        groups.setdefault(key, []).append((idx, row))

    # Choose most complete record per group; tie-break by earliest row index
    chosen = []
    for key, items in groups.items():
        best = min(
            items,
            key=lambda t: (-completeness_score(t[1], fields), t[0]),
        )
        chosen.append((key, best[1]))

    # Deterministic sort by normalized email key (invalid groups sort last, by row)
    chosen.sort(key=lambda t: t[0])
    output_rows = [r for _, r in chosen]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({f: row.get(f, "") for f in fields})


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python normalizer.py <input.csv> <output.csv> [default_region]")
        sys.exit(1)

    region = sys.argv[3] if len(sys.argv) > 3 else "1"
    normalize_csv(sys.argv[1], sys.argv[2], region)