import collections
import re
from typing import Any, Dict, List, Optional, Tuple


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Normalize email address by lowercasing and stripping whitespace."""
    if not email:
        return None
    email = email.strip().lower()
    return email if "@" in email and "." in email.split("@")[-1] else None


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize phone number by stripping all non-digit characters."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) > 10 and digits.startswith("1"):
        digits = digits[1:]  # Standardize US/NANP +1 country code
    return digits if len(digits) >= 7 else None


def generate_blocking_key(
    surname: Optional[str], postal_code: Optional[str]
) -> str:
    """Creates a blocking key: (Surname Initial : First 3 Postal Code Characters)."""
    sn_initial = (
        re.sub(r"[^a-zA-Z]", "", surname or "").upper()[:1] or "UNKNOWN"
    )
    post_prefix = (
        re.sub(r"[^a-zA-Z0-9]", "", postal_code or "").upper()[:3] or "UNKNOWN"
    )
    return f"{sn_initial}:{post_prefix}"


class UnionFind:
    """Disjoint-set structure to merge matching record IDs into clusters."""

    def __init__(self) -> None:
        self.parent: Dict[Any, Any] = {}

    def find(self, item: Any) -> Any:
        if item not in self.parent:
            self.parent[item] = item
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])  # Path compression
        return self.parent[item]

    def union(self, item1: Any, item2: Any) -> None:
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            self.parent[root2] = root1


def match_customer_records(
    records: List[Dict[str, Any]]
) -> List[List[Dict[str, Any]]]:
    """Matches offline customer records using:

    1. Surname-initial / postal-prefix candidate blocking.
    2. Strict candidate precedence: Email Match > Phone Match, tied on lowest target ID.
    """
    uf = UnionFind()
    blocks: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)

    # ------------------------------------------------------------------
    # STAGE 1: BLOCKING & PREPROCESSING
    # Group records by blocking key before doing candidate comparisons.
    # ------------------------------------------------------------------
    for record in records:
        rec_id = record["id"]
        uf.find(rec_id)  # Register node in Union-Find

        record["_norm_email"] = normalize_email(record.get("email"))
        record["_norm_phone"] = normalize_phone(record.get("phone"))

        block_key = generate_blocking_key(
            record.get("surname"), record.get("postal_code")
        )
        blocks[block_key].append(record)

    # ------------------------------------------------------------------
    # STAGE 2: CANDIDATE MATCHING WITH PREFERENCE RULES
    # Evaluate matches inside the block, selecting:
    #   - Email matches over Phone matches
    #   - Lowest target ID on ties
    # ------------------------------------------------------------------
    for block_key, block_records in blocks.items():
        if len(block_records) < 2:
            continue

        # In-block indexes mapping normalized channels to lists of record IDs
        email_map: Dict[str, List[Any]] = collections.defaultdict(list)
        phone_map: Dict[str, List[Any]] = collections.defaultdict(list)

        for rec in block_records:
            rec_id = rec["id"]
            if rec["_norm_email"]:
                email_map[rec["_norm_email"]].append(rec_id)
            if rec["_norm_phone"]:
                phone_map[rec["_norm_phone"]].append(rec_id)

        # For each record in block, evaluate candidate matches
        for rec in block_records:
            rec_id = rec["id"]
            email = rec["_norm_email"]
            phone = rec["_norm_phone"]

            candidate_email_ids = [
                target_id
                for target_id in email_map.get(email, [])
                if target_id != rec_id
            ]
            candidate_phone_ids = [
                target_id
                for target_id in phone_map.get(phone, [])
                if target_id != rec_id
            ]

            best_match_id = None

            # Priority 1: Email Match -> select lowest candidate ID
            if candidate_email_ids:
                best_match_id = min(candidate_email_ids)
            # Priority 2: Phone Match -> select lowest candidate ID (if no email match)
            elif candidate_phone_ids:
                best_match_id = min(candidate_phone_ids)

            # Perform merge with top-priority candidate match
            if best_match_id is not None:
                uf.union(rec_id, best_match_id)

    # ------------------------------------------------------------------
    # STAGE 3: AGGREGATE CLUSTERS
    # ------------------------------------------------------------------
    clusters: Dict[Any, List[Dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        clean_record = {
            k: v for k, v in record.items() if not k.startswith("_norm_")
        }
        root = uf.find(record["id"])
        clusters[root].append(clean_record)

    return list(clusters.values())


# Example Usage
if __name__ == "__main__":
    sample_records = [
        {
            "id": 20,
            "first_name": "Jane",
            "surname": "Doe",
            "postal_code": "90210",
            "email": "jane@example.com",
            "phone": "555-111-2222",
        },
        {
            "id": 10,
            "first_name": "Janet",
            "surname": "Doe",
            "postal_code": "90210",
            "email": "janet@example.com",
            "phone": "555-111-2222",  # Phone match with ID 20
        },
        {
            "id": 30,
            "first_name": "J.",
            "surname": "Doe",
            "postal_code": "90210",
            "email": "jane@example.com",  # Email match with ID 20, Phone match with ID 10 & 20
            "phone": "555-111-2222",
        },
    ]

    matched_groups = match_customer_records(sample_records)

    print(f"Total Unique Profiles Found: {len(matched_groups)}\n")
    for i, group in enumerate(matched_groups, 1):
        ids = [r["id"] for r in group]
        print(f"Cluster #{i} (IDs: {ids}):")
        for rec in group:
            print(
                f"  - [{rec['id']}] {rec['first_name']} {rec['surname']} | Email: {rec['email']} | Phone: {rec['phone']}"
            )