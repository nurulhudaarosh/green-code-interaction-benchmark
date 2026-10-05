# Prime Range Analyzer
#
# Original problem:
# Given an integer interval [L, R], list all prime numbers in that interval
# and return the largest gap between consecutive primes.
#
# Original required output:
# {
#     "primes": [...],
#     "largest_gap": ...
# }
#
# Added feature:
# When operation_summary is requested, return an additional deterministic
# "operation_summary" field. It reports the number of major computational
# decisions/operations made by the segmented-sieve algorithm.
#
# The original fields and behavior remain unchanged when the feature is
# disabled or not requested.
#
# Algorithm:
# 1. Generate base primes through sqrt(R).
# 2. Create a boolean segment for [L, R].
# 3. For each base prime, determine its first relevant multiple and mark
#    composite values in the segment.
# 4. Extract the primes.
# 5. Compare consecutive primes to find the largest gap.
#
# The operation summary counts these major deterministic operations:
# - Each base prime processed by the segmented sieve: 1 operation.
# - Each composite marking performed: 1 operation.
# - Each consecutive-prime gap comparison: 1 operation.
#
# This count is deterministic for the same input and does not affect the
# original prime/gap results.


from math import isqrt


def generate_base_primes(limit: int) -> list[int]:
    """Generate all primes from 2 through limit."""
    if limit < 2:
        return []

    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False

    for p in range(2, isqrt(limit) + 1):
        if is_prime[p]:
            start = p * p
            is_prime[start:limit + 1:p] = [False] * (
                ((limit - start) // p) + 1
            )

    return [n for n, prime in enumerate(is_prime) if prime]


def prime_range_analyzer(
    L: int,
    R: int,
    include_operation_summary: bool = False,
) -> dict:
    """
    Analyze primes in [L, R].

    Original output:
        {
            "primes": [...],
            "largest_gap": ...
        }

    If include_operation_summary=True, also returns:
        "operation_summary": {
            "base_primes_processed": ...,
            "composite_marks": ...,
            "gap_comparisons": ...,
            "total_operations": ...
        }
    """
    if L > R:
        raise ValueError("L must be less than or equal to R.")

    # Operation counters are only needed when the optional feature is enabled.
    base_primes_processed = 0
    composite_marks = 0
    gap_comparisons = 0

    segment_start = max(L, 2)

    if segment_start > R:
        result = {
            "primes": [],
            "largest_gap": 0,
        }

        if include_operation_summary:
            result["operation_summary"] = {
                "base_primes_processed": 0,
                "composite_marks": 0,
                "gap_comparisons": 0,
                "total_operations": 0,
            }

        return result

    # Generate base primes through sqrt(R).
    base_primes = generate_base_primes(isqrt(R))

    # Segmented sieve for [segment_start, R].
    size = R - segment_start + 1
    is_prime = [True] * size

    for p in base_primes:
        if include_operation_summary:
            base_primes_processed += 1

        first_multiple = max(
            p * p,
            ((segment_start + p - 1) // p) * p
        )

        for multiple in range(first_multiple, R + 1, p):
            is_prime[multiple - segment_start] = False

            if include_operation_summary:
                composite_marks += 1

    primes = [
        segment_start + i
        for i, prime in enumerate(is_prime)
        if prime
    ]

    largest_gap = 0

    for i in range(1, len(primes)):
        if include_operation_summary:
            gap_comparisons += 1

        largest_gap = max(
            largest_gap,
            primes[i] - primes[i - 1]
        )

    result = {
        "primes": primes,
        "largest_gap": largest_gap,
    }

    # Preserve the original output exactly when the feature is not requested.
    if include_operation_summary:
        total_operations = (
            base_primes_processed
            + composite_marks
            + gap_comparisons
        )

        result["operation_summary"] = {
            "base_primes_processed": base_primes_processed,
            "composite_marks": composite_marks,
            "gap_comparisons": gap_comparisons,
            "total_operations": total_operations,
        }

    return result


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

# Original behavior: no additional field.
assert prime_range_analyzer(10, 30) == {
    "primes": [11, 13, 17, 19, 23, 29],
    "largest_gap": 6,
}

# Single-prime interval.
assert prime_range_analyzer(2, 2) == {
    "primes": [2],
    "largest_gap": 0,
}

# No primes.
assert prime_range_analyzer(14, 16) == {
    "primes": [],
    "largest_gap": 0,
}

# Interval crossing values below 2.
assert prime_range_analyzer(1, 10) == {
    "primes": [2, 3, 5, 7],
    "largest_gap": 2,
}

# Optional operation summary.
result = prime_range_analyzer(
    10,
    30,
    include_operation_summary=True,
)

assert result["primes"] == [11, 13, 17, 19, 23, 29]
assert result["largest_gap"] == 6
assert "operation_summary" in result

summary = result["operation_summary"]

assert summary["base_primes_processed"] == 3
assert summary["composite_marks"] == 8
assert summary["gap_comparisons"] == 5
assert summary["total_operations"] == 16

# Determinism: identical input produces identical summary.
assert prime_range_analyzer(
    10, 30, include_operation_summary=True
) == prime_range_analyzer(
    10, 30, include_operation_summary=True
)

# Empty interval after excluding values below 2.
assert prime_range_analyzer(
    -10, 1,
    include_operation_summary=True
) == {
    "primes": [],
    "largest_gap": 0,
    "operation_summary": {
        "base_primes_processed": 0,
        "composite_marks": 0,
        "gap_comparisons": 0,
        "total_operations": 0,
    },
}