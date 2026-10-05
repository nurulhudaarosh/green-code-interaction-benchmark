id="m7k2p4"
"""
Prime Range Analyzer

Problem restatement
-------------------
Given integers L and R, list all prime numbers in the inclusive interval
[L, R] and return the largest gap between consecutive primes.

Original output:
    {
        "primes": [...],
        "largest_gap": ...
    }

Optional feature already added:
    When include_operation_summary=True, also return:
        "operation_summary": <deterministic integer>

Original requirements preserved:
- Generate base primes through sqrt(R).
- Perform a segmented sieve over [L, R].
- Return primes in increasing order.
- largest_gap is the maximum difference between consecutive primes.
- If fewer than two primes exist, largest_gap is 0.
- Deterministic behavior.
- No randomness or external services.
- Standard library only.
- When operation_summary is disabled/not requested, return exactly the
  original two fields.

Difficult valid cases handled explicitly
-----------------------------------------
1. Smallest permitted input:
   - The smallest meaningful prime-search value is 2.
   - For [2, 2], the answer is exactly one prime and no consecutive pair:
         {"primes": [2], "largest_gap": 0}

2. Empty prime structures:
   - A valid interval can contain no primes, such as [0, 1] or [14, 16].
   - In that case:
         {"primes": [], "largest_gap": 0}

3. Disconnected prime occurrences:
   - Composite values between primes are correctly ignored.
   - For example, [24, 30] contains only 29.
   - For [20, 40], the primes are [23, 29, 31, 37], with the largest
     consecutive gap equal to 6.

4. The optional operation_summary remains deterministic and does not alter
   the original result when disabled.
"""

from math import isqrt


def _generate_base_primes(limit: int, counter: list[int]) -> list[int]:
    """Generate all primes from 2 through limit."""
    if limit < 2:
        return []

    composite = bytearray(limit + 1)
    primes = []

    for p in range(2, limit + 1):
        counter[0] += 1

        if composite[p] == 0:
            primes.append(p)

            if p * p <= limit:
                composite[p * p : limit + 1 : p] = b"\x01" * (
                    (limit - p * p) // p + 1
                )

    return primes


def prime_range_analyzer(
    L: int,
    R: int,
    include_operation_summary: bool = False,
) -> dict:
    """
    Analyze the inclusive interval [L, R].

    Original output:
        {
            "primes": [...],
            "largest_gap": ...
        }

    If include_operation_summary=True:
        {
            "primes": [...],
            "largest_gap": ...,
            "operation_summary": <deterministic integer>
        }
    """

    if L > R:
        raise ValueError("L must be less than or equal to R")

    counter = [0]

    # Empty prime domain: R is below the smallest prime, 2.
    if R < 2:
        result = {
            "primes": [],
            "largest_gap": 0,
        }

        if include_operation_summary:
            result["operation_summary"] = 0

        return result

    start = max(L, 2)
    width = R - start + 1

    # Required: generate base primes through sqrt(R).
    base_primes = _generate_base_primes(
        isqrt(R),
        counter,
    )

    # Segmented sieve for [start, R].
    is_prime = bytearray(b"\x01") * width

    for p in base_primes:
        # Count processing of this base prime.
        counter[0] += 1

        # First multiple of p in the segment.
        first = max(
            p * p,
            ((start + p - 1) // p) * p,
        )

        if first > R:
            continue

        first_index = first - start
        count = (width - 1 - first_index) // p + 1

        # Count composite markings.
        counter[0] += count
        is_prime[first_index::p] = b"\x00" * count

    primes = [
        start + i
        for i, value in enumerate(is_prime)
        if value
    ]

    largest_gap = 0

    for i in range(1, len(primes)):
        # Each consecutive-prime comparison is one major operation.
        counter[0] += 1

        gap = primes[i] - primes[i - 1]

        # Strict > preserves deterministic behavior without changing the
        # original largest-gap requirement.
        if gap > largest_gap:
            largest_gap = gap

    result = {
        "primes": primes,
        "largest_gap": largest_gap,
    }

    if include_operation_summary:
        result["operation_summary"] = counter[0]

    return result


# ============================================================
# Tests
# ============================================================

def _run_tests() -> None:
    # --------------------------------------------------------
    # 1. Smallest permitted input: [2, 2]
    # --------------------------------------------------------
    assert prime_range_analyzer(2, 2) == {
        "primes": [2],
        "largest_gap": 0,
    }

    # Same case with optional operation summary.
    result = prime_range_analyzer(
        2,
        2,
        include_operation_summary=True,
    )
    assert result["primes"] == [2]
    assert result["largest_gap"] == 0
    assert isinstance(result["operation_summary"], int)

    # --------------------------------------------------------
    # 2. Empty prime structure: interval [0, 1]
    # --------------------------------------------------------
    assert prime_range_analyzer(0, 1) == {
        "primes": [],
        "largest_gap": 0,
    }

    # --------------------------------------------------------
    # 3. Empty prime structure between composites: [14, 16]
    # --------------------------------------------------------
    assert prime_range_analyzer(14, 16) == {
        "primes": [],
        "largest_gap": 0,
    }

    # --------------------------------------------------------
    # 4. Disconnected structure: only one prime in the interval
    # --------------------------------------------------------
    assert prime_range_analyzer(24, 30) == {
        "primes": [29],
        "largest_gap": 0,
    }

    # --------------------------------------------------------
    # 5. Several separated primes with a deterministic largest gap
    # --------------------------------------------------------
    assert prime_range_analyzer(20, 40) == {
        "primes": [23, 29, 31, 37],
        "largest_gap": 6,
    }

    # --------------------------------------------------------
    # 6. Interval beginning below 2 but containing primes
    # --------------------------------------------------------
    assert prime_range_analyzer(-10, 10) == {
        "primes": [2, 3, 5, 7],
        "largest_gap": 2,
    }

    # --------------------------------------------------------
    # 7. Smallest prime followed by several primes
    # --------------------------------------------------------
    assert prime_range_analyzer(2, 20) == {
        "primes": [2, 3, 5, 7, 11, 13, 17, 19],
        "largest_gap": 4,
    }

    # --------------------------------------------------------
    # 8. Original behavior is unchanged when the new feature
    #    is not requested.
    # --------------------------------------------------------
    original = prime_range_analyzer(10, 30)
    assert original == {
        "primes": [11, 13, 17, 19, 23, 29],
        "largest_gap": 6,
    }
    assert set(original.keys()) == {"primes", "largest_gap"}

    # --------------------------------------------------------
    # 9. Operation summary is deterministic.
    # --------------------------------------------------------
    first = prime_range_analyzer(
        10,
        100,
        include_operation_summary=True,
    )
    second = prime_range_analyzer(
        10,
        100,
        include_operation_summary=True,
    )

    assert first == second

    # --------------------------------------------------------
    # 10. No-prime interval with operation summary.
    # --------------------------------------------------------
    empty_result = prime_range_analyzer(
        14,
        16,
        include_operation_summary=True,
    )

    assert empty_result["primes"] == []
    assert empty_result["largest_gap"] == 0
    assert "operation_summary" in empty_result

    # --------------------------------------------------------
    # 11. Invalid reversed interval remains invalid.
    # --------------------------------------------------------
    try:
        prime_range_analyzer(10, 2)
        assert False, "Expected ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    _run_tests()

    print(prime_range_analyzer(2, 2))
    print(prime_range_analyzer(0, 1))
    print(prime_range_analyzer(20, 40))
    print(prime_range_analyzer(20, 40, include_operation_summary=True))