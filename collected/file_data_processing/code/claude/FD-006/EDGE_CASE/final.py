import csv
import re
import sys


def normalize_email(email: str) -> str:
    """Normalize email: strip surrounding whitespace, lowercase. Empty/invalid -> ''."""
    if not email:
        return ""
    email = email.strip().lower()
    if "@" not in email or email.count("@") != 1:
        return ""
    local, domain = email.split("@")
    local, domain = local.strip(), domain.strip()
    if not local or not domain:
        return ""
    return f"{local}@{domain}"


def normalize_phone(phone: str) -> str:
    """Strip all punctuation/whitespace, keep only digits (and leading + if present)."""
    if not phone:
        return ""
    phone = phone.strip()
    has_plus = phone.startswith("+")
    digits = re.sub(r"\D", "", phone)  # removes spaces, dashes, parens, dots, etc.
    if not digits:
        return ""
    if len(digits) == 10:
        digits = "1" + digits  # assume missing US country code
    return f"+{digits}" if (has_plus or len(digits) == 11) else digits


def completeness_score(record: dict) -> int:
    score = 0
    for value in record.values():
        if value is not None and str(value).strip() != "":
            score += 1
    return score


def normalize_csv(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("Input CSV has no header row")

        email_field = next((c for c in fieldnames if c.lower() == "email"), None)
        phone_field = next((c for c in fieldnames if c.lower() == "phone"), None)
        if not email_field:
            raise ValueError("No 'email' column found in CSV")

        groups: dict[str, dict] = {}
        best_score: dict[str, int] = {}

        for row_index, row in enumerate(reader):
            norm_email = normalize_email(row.get(email_field, ""))
            if not norm_email:
                continue

            normalized_row = dict(row)
            normalized_row[email_field] = norm_email
            if phone_field:
                normalized_row[phone_field] = normalize_phone(row.get(phone_field, ""))

            score = completeness_score(normalized_row)

            if norm_email not in groups:
                groups[norm_email] = normalized_row
                best_score[norm_email] = score
            elif score > best_score[norm_email]:
                # Strictly greater completeness wins; ties keep the earlier row
                # since we never overwrite on equal score.
                groups[norm_email] = normalized_row
                best_score[norm_email] = score

    sorted_records = [groups[key] for key in sorted(groups.keys())]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in sorted_records:
            writer.writerow(record)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python normalizer.py <input.csv> <output.csv>")
        sys.exit(1)
    normalize_csv(sys.argv[1], sys.argv[2])