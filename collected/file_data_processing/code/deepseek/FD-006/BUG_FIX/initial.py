import csv
import re
import sys
from typing import Optional


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.strip().lower()


def normalize_phone(value: Optional[str], default_country: str = "1") -> str:
    if not value:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    has_plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    if has_plus:
        return "+" + digits
    if len(digits) == 10:
        return "+" + default_country + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return "+" + digits


def completeness_score(row: dict, fields: list) -> int:
    score = 0
    for f in fields:
        v = row.get(f)
        if v is not None and str(v).strip() != "":
            score += 1
    return score


def normalize_csv(
    input_path: str,
    output_path: str,
    email_field: str = "email",
    phone_field: str = "phone",
    default_country: str = "1",
) -> None:
    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if email_field not in fieldnames:
        raise ValueError(f"Missing email field: {email_field}")
    if phone_field not in fieldnames:
        raise ValueError(f"Missing phone field: {phone_field}")

    groups: dict = {}
    for idx, row in enumerate(rows):
        norm_email = normalize_email(row.get(email_field))
        norm_phone = normalize_phone(row.get(phone_field), default_country)

        clean_row = dict(row)
        clean_row[email_field] = norm_email
        clean_row[phone_field] = norm_phone

        key = norm_email
        entry = {
            "row": clean_row,
            "original_index": idx,
            "score": completeness_score(clean_row, fieldnames),
            "email": norm_email,
        }

        if key not in groups:
            groups[key] = entry
        else:
            current = groups[key]
            if (entry["score"], -entry["original_index"]) > (
                current["score"],
                -current["original_index"],
            ):
                groups[key] = entry

    selected = [groups[k] for k in sorted(groups.keys(), key=lambda x: (x,))]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in selected:
            writer.writerow(entry["row"])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python normalizer.py <input.csv> <output.csv>")
        sys.exit(1)
    normalize_csv(sys.argv[1], sys.argv[2])