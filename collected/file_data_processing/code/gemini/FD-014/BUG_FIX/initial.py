import re
from typing import List, Dict, Set, Any, Tuple

def normalize_phone(phone: str) -> str:
    """Extracts digits from phone string, keeping last 10 digits for normalization."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    return digits[-10:] if len(digits) >= 10 else digits

def normalize_email(email: str) -> str:
    """Trims whitespace and lowercases email."""
    if not email:
        return ""
    return str(email).strip().lower()

def extract_blocking_key(record: Dict[str, Any]) -> str:
    """
    Generates a blocking key using:
    - Surname initial (first letter of last name, or first letter of name if single string)
    - Postal prefix (first 3 alphanumeric characters of postal/zip code)
    """
    surname = str(record.get("last_name", "")).strip()
    if not surname:
        first_name = str(record.get("first_name", "")).strip()
        surname = first_name.split()[-1] if first_name else ""
    
    surname_initial = surname[0].upper() if surname else "?"
    
    postal = re.sub(r"[^A-Za-z0-9]", "", str(record.get("postal_code", record.get("zip_code", "")))).upper()
    postal_prefix = postal[:3] if postal else "000"
    
    return f"{surname_initial}_{postal_prefix}"

def match_customer_records(records: List[Dict[str, Any]]) -> List[Set[int]]:
    """
    Finds matching customer records using blocking followed by exact email/phone matching.
    
    Returns a list of sets, where each set contains the indices of matching records.
    """
    # Step 1: Group records into blocks
    blocks: Dict[str, List[int]] = {}
    for idx, record in enumerate(records):
        key = extract_blocking_key(record)
        blocks.setdefault(key, []).append(idx)

    # Union-Find data structure to group matching records
    parent = list(range(len(records)))

    def find(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_j] = root_i

    # Step 2: Perform matching within each block
    for key, indices in blocks.items():
        if len(indices) < 2:
            continue

        # Lookups for exact matches inside the block
        email_map: Dict[str, int] = {}
        phone_map: Dict[str, int] = {}

        for idx in indices:
            rec = records[idx]
            email = normalize_email(rec.get("email", ""))
            phone = normalize_phone(rec.get("phone", ""))

            # Match on Email
            if email:
                if email in email_map:
                    union(idx, email_map[email])
                else:
                    email_map[email] = idx

            # Match on Phone
            if phone:
                if phone in phone_map:
                    union(idx, phone_map[phone])
                else:
                    phone_map[phone] = idx

    # Step 3: Collect grouped indices
    groups: Dict[int, Set[int]] = {}
    for idx in range(len(records)):
        root = find(idx)
        groups.setdefault(root, set()).add(idx)

    return list(groups.values())


# Example Usage
if __name__ == "__main__":
    data = [
        {"id": 1, "first_name": "John", "last_name": "Doe", "postal_code": "90210", "email": "jdoe@example.com", "phone": "555-123-4567"},
        {"id": 2, "first_name": "Jonathan", "last_name": "Doe", "postal_code": "90210-1234", "email": "JDOE@example.com", "phone": "555-000-0000"}, # Matches #1 via Email + Block
        {"id": 3, "first_name": "Jane", "last_name": "Doe", "postal_code": "90210", "email": "jane@example.com", "phone": "(555) 123-4567"},    # Matches #1 via Phone + Block
        {"id": 4, "first_name": "Alice", "last_name": "Smith", "postal_code": "10001", "email": "alice@example.com", "phone": "555-987-6543"},
        {"id": 5, "first_name": "A.", "last_name": "Smith", "postal_code": "10002", "email": "alice@example.com", "phone": "555-987-6543"},     # Different block (different zip prefix)
    ]

    matched_groups = match_customer_records(data)
    
    print("Matched Record Index Groups:")
    for group in matched_groups:
        record_ids = [data[idx]["id"] for idx in group]
        print(f"Group: Indices {sorted(list(group))} -> IDs {record_ids}")