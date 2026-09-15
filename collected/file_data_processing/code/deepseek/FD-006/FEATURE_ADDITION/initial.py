import csv
import re
from typing import Any


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip().lower()
    if not s:
        return ""
    # Remove common display-name wrappers and internal spaces
    s = s.strip("<>").strip()
    s = re.sub(r"\s+", "", s)
    if not EMAIL_RE.match(s):
        return ""
    return s


def normalize_phone(value: Any, default_region: str = "US") -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    # Convert letters (e.g., 1-800-FLOWERS) to digits
    letter_map = {
        **{c: str((i // 3) + 2) for i, c in enumerate("ABC")},
        **{c: str((i // 3) + 2) for i, c in enumerate("DEF")},
        **{c: str((i // 3) + 2) for i, c in enumerate("GHI")},
        **{c: str((i // 3) + 2) for i, c in enumerate("JKL")},
        **{c: str((i // 3) + 2) for i, c in enumerate("MNO")},
        **{c: str((i // 3) + 2) for i, c in enumerate("PQRS")},
        **{c: str((i // 3) + 2) for i, c in enumerate("TUV")},
        **{c: str((i // 3) + 2) for i, c in enumerate("WXYZ")},
    }
    s = s.upper()
    converted = "".join(letter_map.get(c, c) for c in s)
    digits = re.sub(r"\D", "", converted)
    if not digits:
        return ""
    # Normalize US numbers to E.164
    if default_region.upper() == "US":
        if len(digits) == 10:
            return "+1" + digits
        if len(digits) == 11 and digits.startswith("1"):
            return "+" + digits
        if digits.startswith("1") and len(digits) > 11:
            return "+" + digits
        return "+" + digits
    # Generic E.164 fallback
    return "+" + digits


def completeness_score(record: dict, fields: list) -> int:
    score = 0
    for f in fields:
        v = record.get(f)
        if v is not None and str(v).strip() != "":
            score += 1
    return score


def normalize_csv(
    input_path: str,
    output_path: str,
    email_field: str = "email",
    phone_field: str = "phone",
    fields: list = None,
    default_region: str = "US",
) -> None:
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        original_fields = reader.fieldnames or []

    if fields is None:
        fields = original_fields

    # Ensure required fields are present
    for required in (email_field, phone_field):
        if required not in original_fields:
            raise ValueError(f"Missing required column: {required}")

    # Build canonical output field list
    out_fields = list(original_fields)
    for extra in ("normalized_email", "normalized_phone"):
        if extra not in out_fields:
            out_fields.append(extra)

    # Normalize each row and add row index for tie-breaking
    normalized_rows = []
    for idx, row in enumerate(rows):
        email = normalize_email(row.get(email_field, ""))
        phone = normalize_phone(row.get(phone_field, ""), default_region=default_region)
        rec = dict(row)
        rec["normalized_email"] = email
        rec["normalized_phone"] = phone
        rec["_row_index"] = idx
        normalized_rows.append(rec)

    # Group by normalized email (skip empty emails into their own bucket)
    groups: dict = {}
    for rec in normalized_rows:
        key = rec["normalized_email"]
        groups.setdefault(key, []).append(rec)

    # Choose best record per group
    selected = []
    for key, group in groups.items():
        # Sort by: completeness desc, row index asc
        best = sorted(
            group,
            key=lambda r: (-completeness_score(r, fields), r["_row_index"]),
        )[0]
        selected.append(best)

    # Deterministic output sorted by normalized email (empty last)
    selected.sort(key=lambda r: (r["normalized_email"] == "", r["normalized_email"]))

    # Write output
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        for rec in selected:
            writer.writerow(rec)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python normalizer.py <input.csv> <output.csv>")
        sys.exit(1)
    normalize_csv(sys.argv[1], sys.argv[2])