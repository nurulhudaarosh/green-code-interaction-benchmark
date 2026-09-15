import csv
import re
import sys
from typing import Dict, List, Tuple, Optional


def normalize_email(email: Optional[str]) -> str:
    if email is None:
        return ""
    email = email.strip().lower()
    if not email:
        return ""
    match = re.match(r"^([^@]+)@([^@]+)$", email)
    if not match:
        return email
    local, domain = match.group(1), match.group(2)
    if "+" in local:
        local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def normalize_phone(phone: Optional[str]) -> str:
    if phone is None:
        return ""
    # Digits only: strip all punctuation, spaces, and other non-digit characters
    return re.sub(r"\D", "", phone)


def completeness_score(record: Dict[str, str], fields: List[str]) -> int:
    return sum(1 for f in fields if record.get(f, "").strip())


def normalize_records(
    input_path: str,
    output_path: str,
    email_field: str = "email",
    phone_field: str = "phone",
) -> None:
    with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if email_field not in fieldnames:
        raise ValueError(f"Missing email field: {email_field}")

    # Normalize email (case + whitespace) and phone (digits only) per row
    for row in rows:
        row["_norm_email"] = normalize_email(row.get(email_field, ""))
        if phone_field in fieldnames:
            row["_norm_phone"] = normalize_phone(row.get(phone_field, ""))
        else:
            row["_norm_phone"] = ""

    # Group by normalized email (case-insensitive, whitespace-trimmed)
    groups: Dict[str, List[Tuple[int, Dict[str, str]]]] = {}
    for idx, row in enumerate(rows):
        key = row["_norm_email"]
        groups.setdefault(key, []).append((idx, row))

    # Pick most complete record; tie-break by earliest input row
    chosen: List[Dict[str, str]] = []
    for key, entries in groups.items():
        best_idx, best_row = None, None
        best_score = -1
        for idx, row in entries:
            score = completeness_score(row, fieldnames)
            if score > best_score or (score == best_score and (best_idx is None or idx < best_idx)):
                best_score = score
                best_idx = idx
                best_row = row
        out = dict(best_row)
        out[email_field] = key
        if phone_field in fieldnames:
            out[phone_field] = out.get("_norm_phone", "")
        out.pop("_norm_email", None)
        out.pop("_norm_phone", None)
        chosen.append(out)

    # Deterministic output sorted by normalized email
    chosen.sort(key=lambda r: r.get(email_field, ""))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in chosen:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python normalizer.py <input.csv> <output.csv> [email_field] [phone_field]")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    ef = sys.argv[3] if len(sys.argv) > 3 else "email"
    pf = sys.argv[4] if len(sys.argv) > 4 else "phone"
    normalize_records(in_path, out_path, ef, pf)