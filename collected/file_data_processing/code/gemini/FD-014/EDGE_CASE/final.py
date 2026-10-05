import re
from collections import defaultdict
from typing import Dict, List, Set

# -----------------------------------------------------------------------------
# 1. Normalization Utility Functions
# -----------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Strip leading/trailing whitespace and convert to lower case."""
    if not text:
        return ""
    return str(text).strip().lower()

def normalize_name(name: str) -> str:
    """Normalize case, strip whitespace, and keep letters/numbers."""
    text = clean_text(name)
    return re.sub(r"[^\w]", "", text)

def normalize_postal_code(postal_code: str) -> str:
    """Normalize case, strip whitespace and non-alphanumeric punctuation."""
    text = clean_text(postal_code)
    return re.sub(r"[^a-z0-9]", "", text)

def normalize_email(email: str) -> str:
    """Normalize case and remove surrounding whitespace."""
    return clean_text(email)

def normalize_phone(phone: str) -> str:
    """
    Remove all non-digit punctuation (spaces, hyphens, parens, pluses).
    Returns the standard 10-digit number when national prefix is included.
    """
    text = clean_text(phone)
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 10:
        return digits[-10:]
    return digits

# -----------------------------------------------------------------------------
# 2. Matching Engine
# -----------------------------------------------------------------------------

class RecordMatcher:
    def __init__(self, records: List[Dict[str, str]], postal_prefix_len: int = 3):
        self.records = records
        self.postal_prefix_len = postal_prefix_len
        self.normalized_records = []
        self._prepare_records()

    def _prepare_records(self):
        """Precompute normalized fields and blocking keys."""
        for rec in self.records:
            surname = normalize_name(rec.get("last_name", ""))
            postal = normalize_postal_code(rec.get("postal_code", ""))
            
            # Blocking key: Surname initial + Postal Code Prefix
            surname_initial = surname[0] if surname else "?"
            postal_prefix = postal[:self.postal_prefix_len] if postal else "unk"
            block_key = f"{surname_initial}_{postal_prefix}"

            self.normalized_records.append({
                "id": rec.get("id"),
                "raw": rec,
                "block_key": block_key,
                "email": normalize_email(rec.get("email", "")),
                "phone": normalize_phone(rec.get("phone", ""))
            })

    def match_records(self) -> List[Set[str]]:
        """Group records into blocks and union records with matching email or phone."""
        # 1. Group records by block
        blocks: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(self.normalized_records):
            blocks[rec["block_key"]].append(idx)

        # Union-Find data structure for graph connectivity
        parent = list(range(len(self.normalized_records)))

        def find(i: int) -> int:
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i: int, j: int):
            root_i, root_j = find(i), find(j)
            if root_i != root_j:
                parent[root_j] = root_i

        # 2. Match within blocks using normalized fields
        for record_indices in blocks.values():
            email_map: Dict[str, List[int]] = defaultdict(list)
            phone_map: Dict[str, List[int]] = defaultdict(list)

            for idx in record_indices:
                rec = self.normalized_records[idx]
                if rec["email"]:
                    email_map[rec["email"]].append(idx)
                if rec["phone"]:
                    phone_map[rec["phone"]].append(idx)

            # Union records sharing matching email
            for indices in email_map.values():
                for idx in indices[1:]:
                    union(indices[0], idx)

            # Union records sharing matching phone
            for indices in phone_map.values():
                for idx in indices[1:]:
                    union(indices[0], idx)

        # 3. Collect cluster groups
        clusters: Dict[int, Set[str]] = defaultdict(set)
        for idx, rec in enumerate(self.normalized_records):
            root = find(idx)
            clusters[root].add(rec["id"])

        return list(clusters.values())

# -----------------------------------------------------------------------------
# 3. Example Run
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    sample_dataset = [
        {
            "id": "REC_001",
            "last_name": "  Smith  ",
            "postal_code": " 90210 ",
            "email": "  JOHN.SMITH@Domain.COM ",
            "phone": " +1 (555) 123-4567 "
        },
        {
            "id": "REC_002",
            "last_name": "smith",
            "postal_code": "90210-1111",
            "email": "john.smith@domain.com",
            "phone": "5551234567"
        },
        {
            "id": "REC_003",
            "last_name": "S M I T H",
            "postal_code": "90210",
            "email": "other@domain.com",
            "phone": " 555-123.4567 "
        }
    ]

    matcher = RecordMatcher(sample_dataset, postal_prefix_len=3)
    matched_groups = matcher.match_records()

    print("--- Duplicate Record Clusters ---")
    for group in matched_groups:
        print(f"Group: {sorted(list(group))}")