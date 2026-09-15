import csv
import re
import sys

def normalize_email(email: str) -> str:
    """Canonicalize email: lowercased and stripped of leading/trailing whitespace."""
    return email.strip().lower()

def normalize_phone(phone: str) -> str:
    """Canonicalize phone: strip all non-digit characters."""
    return re.sub(r'\D', '', phone)

def record_completeness(record: dict) -> int:
    """Count non-empty values in a record to determine completeness."""
    return sum(1 for v in record.values() if v is not None and str(v).strip() != '')

def normalize_customer_csv(input_filepath: str, output_filepath: str):
    """
    Normalizes a customer CSV:
    1. Canonicalizes 'email' (lowercased) and 'phone' (digits only).
    2. Groups records by normalized email.
    3. Selects the most complete record (earliest-row breaks ties).
    4. Writes deterministic output sorted by normalized email.
    """
    with open(input_filepath, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames or 'email' not in fieldnames:
            raise ValueError("Input CSV must contain an 'email' column.")

        grouped_records = {}

        for row_index, row in enumerate(reader):
            # Canonicalize key fields before evaluating completeness
            if 'email' in row and row['email']:
                row['email'] = normalize_email(row['email'])
            
            if 'phone' in row and row['phone']:
                row['phone'] = normalize_phone(row['phone'])

            email_key = row['email']
            if not email_key:
                continue  # Skip records without an email

            current_completeness = record_completeness(row)

            if email_key not in grouped_records:
                # Store record along with row index to maintain original order for tie-breaking
                grouped_records[email_key] = (row, current_completeness, row_index)
            else:
                existing_row, existing_completeness, existing_index = grouped_records[email_key]
                # Replace only if current record is strictly more complete than existing record
                if current_completeness > existing_completeness:
                    grouped_records[email_key] = (row, current_completeness, row_index)

    # Sort records deterministically by normalized email
    sorted_emails = sorted(grouped_records.keys())

    with open(output_filepath, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for email in sorted_emails:
            best_record = grouped_records[email][0]
            writer.writerow(best_record)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        normalize_customer_csv(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python normalizer.py <input_csv> <output_csv>")