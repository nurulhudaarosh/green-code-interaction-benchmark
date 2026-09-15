import csv
import re
import sys
from typing import Dict, List, Optional

def normalize_email(email: str) -> str:
    """Canonicalize email by trimming whitespace and lowercasing."""
    return email.strip().lower()

def normalize_phone(phone: str) -> str:
    """Canonicalize phone by stripping non-digit characters."""
    return re.sub(r'\D', '', phone)

def record_completeness(row: Dict[str, str]) -> int:
    """Count non-empty, non-whitespace fields in a row."""
    return sum(1 for val in row.values() if val and val.strip())

def normalize_customer_csv(input_filepath: str, output_filepath: str) -> None:
    """
    Reads a customer CSV, normalizes email and phone, groups by normalized email,
    selects the most complete record (earliest row breaks ties), and writes sorted output.
    """
    grouped_records: Dict[str, Dict[str, str]] = {}
    grouped_completeness: Dict[str, int] = {}
    fieldnames: List[str] = []

    with open(input_filepath, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            return
        fieldnames = list(reader.fieldnames)

        for row in reader:
            raw_email = row.get('email', '')
            norm_email = normalize_email(raw_email)
            if not norm_email:
                continue

            # Update record fields with normalized values
            row['email'] = norm_email
            if 'phone' in row:
                row['phone'] = normalize_phone(row.get('phone', ''))

            completeness = record_completeness(row)

            # Keep existing record if it has higher or equal completeness to preserve earliest row tie-breaking
            if norm_email not in grouped_records or completeness > grouped_completeness[norm_email]:
                grouped_records[norm_email] = row
                grouped_completeness[norm_email] = completeness

    # Sort deterministically by normalized email
    sorted_emails = sorted(grouped_records.keys())

    with open(output_filepath, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for email in sorted_emails:
            writer.writerow(grouped_records[email])

if __name__ == '__main__':
    if len(sys.argv) == 3:
        normalize_customer_csv(sys.argv[1], sys.argv[2])