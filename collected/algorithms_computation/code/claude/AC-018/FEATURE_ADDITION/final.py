from typing import Dict, List, Union


def multiply_polynomials(
    a: List[int],
    b: List[int],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, object]]:
    """Multiply two integer polynomials exactly (ascending-degree coefficients).

    Default (include_summary=False): returns the coefficient list, exactly as
    before. Length is len(a)+len(b)-1; empty input gives [0].

    include_summary=True: returns
        {"coefficients": <same list>, "operation_summary": {...}}
    """
    decisions = 1  # the empty-input check
    zero_rows_skipped = 0
    multiplications = 0
    additions = 0

    if not a or not b:
        result = [0]
    else:
        result = [0] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            decisions += 1  # zero-coefficient check
            if ai == 0:
                zero_rows_skipped += 1
                continue
            for j, bj in enumerate(b):
                result[i + j] += ai * bj
                multiplications += 1
                additions += 1

    if not include_summary:
        return result

    return {
        "coefficients": result,
        "operation_summary": {
            "decisions": decisions,
            "zero_rows_skipped": zero_rows_skipped,
            "multiplications": multiplications,
            "additions": additions,
            "total_operations": decisions + multiplications + additions,
        },
    }


if __name__ == "__main__":
    # Original behavior is unchanged when the feature is off.
    assert multiply_polynomials([1, 2], [3, -1]) == [3, 5, -2]
    assert multiply_polynomials([1, -1], [1, 1]) == [1, 0, -1]
    assert multiply_polynomials([0], [5, 7]) == [0, 0]
    assert multiply_polynomials([], [1, 2]) == [0]
    assert multiply_polynomials([10**30, -1], [10**30]) == [10**60, -(10**30)]

    # Feature enabled: same coefficients plus a deterministic summary.
    r = multiply_polynomials([1, 2], [3, -1], include_summary=True)
    assert r["coefficients"] == [3, 5, -2]
    assert r["operation_summary"] == {
        "decisions": 3, "zero_rows_skipped": 0,
        "multiplications": 4, "additions": 4, "total_operations": 11,
    }

    r = multiply_polynomials([0], [5, 7], include_summary=True)
    assert r["coefficients"] == [0, 0]
    assert r["operation_summary"]["zero_rows_skipped"] == 1
    assert r["operation_summary"]["total_operations"] == 2

    r = multiply_polynomials([], [1, 2], include_summary=True)
    assert r["coefficients"] == [0]
    assert r["operation_summary"]["total_operations"] == 1

    print("All tests passed.")