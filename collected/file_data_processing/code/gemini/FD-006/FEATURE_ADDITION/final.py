import csv
import re
import sys
from collections import defaultdict


def normalize_email(email: str) -> str:
    """Canonicalize email: strip whitespace, lowercase, return empty string if invalid."""
    if not email:
        return ""
    email = email.strip().lower()
    return email if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else ""


def normalize_phone(phone: str) -> str:
    """Canonicalize phone: extract digits; prepend +1 for 10-digit US/CA numbers."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 0:
        return f"+{digits}"
    return ""


def record_completeness(row: dict) -> int:
    """Count non-empty fields in a row."""
    return sum(1 for val in row.values() if val and str(val).strip())


def normalize_csv(input_path: str, output_path: str) -> None:
    """Reads input CSV, canonicalizes email/phone, selects the most complete record per

    normalized email (tie-breaking with earliest input row), and outputs sorted by email.
    """
    with open(input_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        grouped = defaultdict(list)
        for row_idx, row in enumerate(reader):
            norm_row = dict(row)
            norm_email = normalize_email(norm_row.get("email", ""))
            norm_phone = normalize_phone(norm_row.get("phone", ""))

            if "email" in norm_row:
                norm_row["email"] = norm_email
            if "phone" in norm_row:
                norm_row["phone"] = norm_phone

            # Key by normalized email or fallback unique key for invalid/missing emails
            group_key = norm_email if norm_email else f"__no_email_{row_idx}"
            grouped[group_key].append((row_idx, norm_row))

    selected_records = []

    for group_key, items in grouped.items():
        if group_key.startswith("__no_email_"):
            selected_records.append(items[0][1])
        else:
            # Pick highest completeness (-completeness), tie-break with earliest input row (+row_idx)
            best_idx, best_row = min(
                items, key=lambda item: (-record_completeness(item[1]), item[0])
            )
            selected_records.append(best_row)

    # Sort deterministically by canonical normalized email
    selected_records.sort(key=lambda row: row.get("email", ""))

    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_records)


if __name__ == "__main__":
    in_file = sys.argv[1] if len(sys.argv) > 1 else "input.csv"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "normalized_output.csv"
    normalize_csv(in_file, out_file)