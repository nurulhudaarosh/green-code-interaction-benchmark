import csv
import re
import sys
from collections import defaultdict


def normalize_email(email: str) -> str:
    """Canonicalize email: strip whitespace, lowercase, return empty string if invalid."""
    if not email:
        return ""
    email = email.strip().lower()
    # Basic structural check for email validity
    return email if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else ""


def normalize_phone(phone: str) -> str:
    """Canonicalize phone: extract digits; prepend country code +1 for 10-digit US/CA numbers."""
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
    """Count the number of non-empty fields in a row."""
    return sum(1 for value in row.values() if value and str(value).strip())


def normalize_csv(input_path: str, output_path: str) -> None:
    """Reads input CSV, normalizes records, selects the best record per normalized email,

    and writes the deterministic output sorted by email.
    """
    with open(input_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        # Group rows by normalized email while tracking original row order
        grouped = defaultdict(list)
        for idx, row in enumerate(reader):
            # Create a copy with canonicalized key fields
            norm_row = dict(row)
            norm_email = normalize_email(norm_row.get("email", ""))
            norm_phone = normalize_phone(norm_row.get("phone", ""))

            if "email" in norm_row:
                norm_row["email"] = norm_email
            if "phone" in norm_row:
                norm_row["phone"] = norm_phone

            # Key by normalized email (or fallback key if email missing/invalid)
            key = norm_email if norm_email else f"__unmatched_{idx}"
            grouped[key].append((idx, norm_row))

    consolidated_records = []

    for key, items in grouped.items():
        if key.startswith("__unmatched_"):
            # If no valid email, keep the record as-is
            consolidated_records.append((items[0][0], items[0][1]))
        else:
            # Sort candidate rows by completeness (descending), then original index (ascending)
            best_idx, best_row = min(
                items, key=lambda x: (-record_completeness(x[1]), x[0])
            )
            consolidated_records.append((best_idx, best_row))

    # Deterministic final output: sorted primary by normalized email, secondary by original index
    consolidated_records.sort(key=lambda x: (x[1].get("email", ""), x[0]))

    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for _, row in consolidated_records:
            writer.writerow(row)


if __name__ == "__main__":
    in_file = sys.argv[1] if len(sys.argv) > 1 else "input.csv"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "normalized_output.csv"
    normalize_csv(in_file, out_file)