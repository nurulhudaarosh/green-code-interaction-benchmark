import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Optional dependency: pip install rapidfuzz
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


def normalize_string(text: str) -> str:
    """Removes special characters and normalizes string to lowercase ASCII."""
    if not text:
        return ""
    text = text.strip().lower()
    return re.sub(r"[^a-z0-9]", "", text)


def normalize_phone(phone: str) -> str:
    """Extracts trailing digits from phone numbers to handle country codes/formatting."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_postcode(postcode: str) -> str:
    """Normalizes postal codes to alphanumeric uppercase."""
    if not postcode:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", postcode).upper()


def extract_blocking_keys(record: Dict[str, str]) -> Set[str]:
    """Generates blocking keys based on surname initial and postal code prefix, plus fallback identity keys."""
    keys = set()
    surname = normalize_string(record.get("surname", ""))
    postcode = normalize_postcode(record.get("postcode", ""))

    surname_initial = surname[0] if surname else ""
    postcode_prefix = postcode[:3] if len(postcode) >= 3 else postcode

    if surname_initial and postcode_prefix:
        keys.add(f"SP_{surname_initial}_{postcode_prefix}")

    email = normalize_string(record.get("email", ""))
    phone = normalize_phone(record.get("phone", ""))

    if email:
        keys.add(f"EMAIL_{email}")
    if phone:
        keys.add(f"PHONE_{phone}")

    return keys


def fuzzy_name_match(
    rec1: Dict[str, str], rec2: Dict[str, str], threshold: float = 85.0
) -> bool:
    """Compares names using RapidFuzz ratio if available, else exact normalized match."""
    first1, last1 = normalize_string(rec1.get("first_name", "")), normalize_string(
        rec1.get("surname", "")
    )
    first2, last2 = normalize_string(rec2.get("first_name", "")), normalize_string(
        rec2.get("surname", "")
    )

    full1 = f"{first1}{last1}"
    full2 = f"{first2}{last2}"

    if not full1 or not full2:
        return False

    if HAS_RAPIDFUZZ:
        return fuzz.ratio(full1, full2) >= threshold
    return full1 == full2


def evaluate_match(rec1: Dict[str, str], rec2: Dict[str, str]) -> Tuple[bool, str, int]:
    """
    Evaluates match candidate and assigns a match priority level:
    Priority 1: Exact Email Match (Highest)
    Priority 2: Exact Phone Match
    Priority 3: Blocked Match (Surname Initial + Postcode Prefix + Fuzzy Name)
    """
    email1 = normalize_string(rec1.get("email", ""))
    email2 = normalize_string(rec2.get("email", ""))
    if email1 and email2 and email1 == email2:
        return True, "EXACT_EMAIL", 1

    phone1 = normalize_phone(rec1.get("phone", ""))
    phone2 = normalize_phone(rec2.get("phone", ""))
    if phone1 and phone2 and phone1 == phone2:
        return True, "EXACT_PHONE", 2

    post1 = normalize_postcode(rec1.get("postcode", ""))
    post2 = normalize_postcode(rec2.get("postcode", ""))

    if post1 and post2 and post1[:3] == post2[:3]:
        if fuzzy_name_match(rec1, rec2):
            return True, "BLOCK_NAME_AND_POSTCODE", 3

    return False, "NO_MATCH", 999


class RecordMatcher:
    def __init__(self):
        self.blocks = defaultdict(set)
        self.records = {}

    def add_records(self, records: List[Dict[str, str]]):
        """Indexes customer records into blocks."""
        for rec in records:
            rec_id = str(rec["id"])
            self.records[rec_id] = rec
            keys = extract_blocking_keys(rec)
            for k in keys:
                self.blocks[k].add(rec_id)

    def find_matches(self) -> List[Dict[str, str]]:
        """
        Performs candidate pair extraction within blocks and selects the best candidate for each left-side ID.
        Tie-breaking rule:
          1. Highest match quality (Email > Phone > Blocking/Fuzzy Name)
          2. Lowest right-side ID (sorted numerically/lexicographically)
        """
        candidate_pairs = set()

        # Generate unique candidate pairs within the same blocks
        for block_id, rec_ids in self.blocks.items():
            ids_list = list(rec_ids)
            for i in range(len(ids_list)):
                for j in range(i + 1, len(ids_list)):
                    id1, id2 = ids_list[i], ids_list[j]
                    if id1 != id2:
                        # Order pair so id1 < id2 for consistency
                        if (
                            int(id1) > int(id2)
                            if id1.isdigit() and id2.isdigit()
                            else id1 > id2
                        ):
                            id1, id2 = id2, id1
                        candidate_pairs.add((id1, id2))

        # Map each target record to all its valid potential matches
        matches_by_left_id = defaultdict(list)

        for id1, id2 in candidate_pairs:
            is_match, reason, priority = evaluate_match(
                self.records[id1], self.records[id2]
            )
            if is_match:
                matches_by_left_id[id1].append(
                    {
                        "record_id_1": id1,
                        "record_id_2": id2,
                        "match_type": reason,
                        "priority": priority,
                    }
                )

        selected_matches = []

        # Select top match per left-side record based on rules
        for left_id, candidates in matches_by_left_id.items():
            # Sort rule:
            # 1. Primary: priority (1=Email > 2=Phone > 3=Block)
            # 2. Secondary: lowest right-side ID (numerical if possible, else string comparison)
            candidates.sort(
                key=lambda x: (
                    x["priority"],
                    int(x["record_id_2"])
                    if str(x["record_id_2"]).isdigit()
                    else str(x["record_id_2"]),
                )
            )

            # Pick top match for this record
            best_match = candidates[0]
            selected_matches.append(
                {
                    "record_id_1": best_match["record_id_1"],
                    "record_id_2": best_match["record_id_2"],
                    "match_type": best_match["match_type"],
                }
            )

        return selected_matches


# --- Example Usage ---
if __name__ == "__main__":
    sample_dataset = [
        {
            "id": "1",
            "first_name": "John",
            "surname": "Smith",
            "email": "john.smith@gmail.com",
            "phone": "+1 (555) 019-2834",
            "postcode": "SW1A 1AA",
        },
        {
            "id": "2",
            "first_name": "John",
            "surname": "Smith",
            "email": "different@gmail.com",
            "phone": "555-019-2834",  # Matches ID 1 on Phone
            "postcode": "SW1A 1AA",
        },
        {
            "id": "3",
            "first_name": "John",
            "surname": "Smith",
            "email": "john.smith@gmail.com",  # Matches ID 1 on Email (Lowest right-side ID choice between 3 and 4)
            "phone": "+1 (555) 019-2834",
            "postcode": "SW1A 1AA",
        },
        {
            "id": "4",
            "first_name": "John",
            "surname": "Smith",
            "email": "john.smith@gmail.com",  # Also matches ID 1 on Email
            "phone": "555-000-0000",
            "postcode": "SW1A 1AA",
        },
    ]

    matcher = RecordMatcher()
    matcher.add_records(sample_dataset)
    results = matcher.find_matches()

    for match in results:
        print(
            f"Matched Pair: Record {match['record_id_1']} <-> Record {match['record_id_2']} | Reason: {match['match_type']}"
        )