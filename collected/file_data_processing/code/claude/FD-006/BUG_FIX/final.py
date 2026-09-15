import csv
import re
import sys


def normalize_email(email: str) -> str:
    if not email:
        return ""
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    local = local.split("+", 1)[0]  # strip +tag aliasing
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)  # digits only, punctuation/spaces stripped


def completeness_score(row: dict) -> int:
    return sum(1 for v in row.values() if v and str(v).strip())


def normalize_records(rows: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    order: dict[str, int] = {}

    for idx, row in enumerate(rows):
        row = dict(row)
        row["email"] = normalize_email(row.get("email", ""))
        row["phone"] = normalize_phone(row.get("phone", ""))
        key = row["email"]
        if not key:
            continue

        if key not in groups:
            groups[key] = row
            order[key] = idx
            continue

        existing = groups[key]
        existing_score = completeness_score(existing)
        new_score = completeness_score(row)

        if new_score > existing_score:
            groups[key] = row
            order[key] = idx
        elif new_score == existing_score and idx < order[key]:
            groups[key] = row
            order[key] = idx

    return [groups[k] for k in sorted(groups.keys())]


def process_csv(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    normalized = normalize_records(rows)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized:
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python normalizer.py <input.csv> <output.csv>")
        sys.exit(1)
    process_csv(sys.argv[1], sys.argv[2])