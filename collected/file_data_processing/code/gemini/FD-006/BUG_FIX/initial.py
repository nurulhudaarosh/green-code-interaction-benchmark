import csv
import re
import sys
from typing import Dict, List, Optional


def normalize_email(email: str) -> str:
    """Canonicalize email: strip whitespace and lowercase."""
    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    """Canonicalize phone: strip all non-digit characters.

    If 11 digits starting with 1 (US/NANP), strips the leading 1.
    """
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def completeness_score(row: Dict[str, str]) -> int:
    """Count non-empty fields in a row."""
    return sum(1 for val in row.values() if val and val.strip())


def normalize_customer_csv(input_filepath: str, output_filepath: str) -> None:
    """Reads a customer CSV, normalizes email/phone, groups by email,

    deduplicates selecting the most complete record, and writes sorted results.
    """
    with open(input_filepath, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames or "email" not in fieldnames:
            raise ValueError("CSV must contain an 'email' column.")

        grouped_records: Dict[str, List[tuple[int, Dict[str, str]]]] = {}

        for index, row in enumerate(reader):
            email = row.get("email", "")
            if not email or not email.strip():
                continue

            norm_email = normalize_email(email)
            row["email"] = norm_email

            if "phone" in row and row["phone"]:
                row["phone"] = normalize_phone(row["phone"])

            if norm_email not in grouped_records:
                grouped_records[norm_email] = []

            # Store (original_row_index, row_dict) to enforce deterministic tie-breaking
            grouped_records[norm_email].append((index, row))

    best_records: List[Dict[str, str]] = []

    for norm_email in sorted(grouped_records.keys()):
        records = grouped_records[norm_email]
        # Sort by completeness score (descending), then by original row index (ascending)
        records.sort(key=lambda item: (-completeness_score(item[1]), item[0]))
        best_records.append(records[0][1])

    with open(output_filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(best_records)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        normalize_customer_csv(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python script.py <input_csv> <output_csv>")