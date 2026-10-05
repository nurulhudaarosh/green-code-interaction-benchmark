from itertools import permutations
from typing import Any, Dict, List, Tuple, Union

INF = float("inf")


def held_karp(
    dist: List[List[float]], with_summary: bool = False
) -> Union[Tuple[float, List[int]], Dict[str, Any]]:
    """Minimum Hamiltonian cycle from/to city 0 via Held-Karp.

    Tie rule: the smaller predecessor wins at every step, including the
    closing edge back to city 0 (smaller last city wins).

    with_summary=False -> returns (min_cost, tour)            [original behavior]
    with_summary=True  -> returns {"min_cost", "tour", "operation_summary"}
    """
    n = len(dist)
    ops = {
        "base_states_initialized": 0,
        "dp_states_computed": 0,
        "transition_candidates_examined": 0,
        "strict_improvements": 0,
        "ties_kept_smaller_predecessor": 0,
        "closing_candidates_examined": 0,
        "reconstruction_steps": 0,
    }

    def finish(cost, tour):
        if not with_summary:
            return cost, tour
        summary = dict(ops)
        summary["total_operations"] = sum(ops.values())
        return {"min_cost": cost, "tour": tour, "operation_summary": summary}

    if n == 0:
        return finish(0, [])
    if n == 1:
        return finish(0, [0, 0])

    m = n - 1                                   # cities 1..n-1 -> bits 0..m-1
    full = (1 << m) - 1
    dp = [[INF] * m for _ in range(1 << m)]
    parent = [[-1] * m for _ in range(1 << m)]  # -1 => predecessor is city 0

    for j in range(m):
        dp[1 << j][j] = dist[0][j + 1]
        ops["base_states_initialized"] += 1

    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1:
                continue
            prev = mask ^ (1 << j)
            if prev == 0:
                continue
            ops["dp_states_computed"] += 1
            best, best_i = INF, -1
            for i in range(m):                  # ascending, strict '<'
                if (prev >> i) & 1:
                    ops["transition_candidates_examined"] += 1
                    cand = dp[prev][i] + dist[i + 1][j + 1]
                    if cand < best:
                        best, best_i = cand, i
                        ops["strict_improvements"] += 1
                    elif cand == best:
                        ops["ties_kept_smaller_predecessor"] += 1
            dp[mask][j] = best
            parent[mask][j] = best_i

    best_cost, last = INF, -1
    for j in range(m):                          # smaller last city wins ties
        ops["closing_candidates_examined"] += 1
        cand = dp[full][j] + dist[j + 1][0]
        if cand < best_cost:
            best_cost, last = cand, j
            ops["strict_improvements"] += 1
        elif cand == best_cost:
            ops["ties_kept_smaller_predecessor"] += 1

    path, mask, j = [], full, last
    while j != -1:
        ops["reconstruction_steps"] += 1
        path.append(j + 1)
        p = parent[mask][j]
        mask ^= 1 << j
        j = p
    path.reverse()
    return finish(best_cost, [0] + path + [0])


def brute_force(dist):
    """Reference for small n: min cost, ties broken by smallest last city,
    then smallest earlier cities (tour read backwards is lexicographically smallest)."""
    n = len(dist)
    best = None
    for p in permutations(range(1, n)):
        t = [0, *p, 0]
        c = sum(dist[a][b] for a, b in zip(t, t[1:]))
        key = (c, t[::-1])
        if best is None or key < best:
            best = key
    return best[0], best[1][::-1]


def reference(dist):
    """Independent check usable at n = 14: DP over (mask, last) storing
    (cost, path read backwards from the last city), taking the lexicographic minimum."""
    n = len(dist)
    m = n - 1
    best = {}
    for j in range(m):
        best[(1 << j, j)] = (dist[0][j + 1], (j + 1,))
    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1 or mask == 1 << j:
                continue
            prev = mask ^ (1 << j)
            best[(mask, j)] = min(
                (best[(prev, i)][0] + dist[i + 1][j + 1], (j + 1,) + best[(prev, i)][1])
                for i in range(m) if (prev >> i) & 1
            )
    full = (1 << m) - 1
    cost, rev = min(
        (best[(full, j)][0] + dist[j + 1][0], best[(full, j)][1]) for j in range(m)
    )
    return cost, [0] + list(rev[::-1]) + [0]


def expected_counts(n):
    """Data-independent operation counts for the Held-Karp loops (m = n - 1)."""
    m = n - 1
    states = m * 2 ** (m - 1) - m
    cands = m * (m - 1) * 2 ** (m - 2)
    return {"base_states_initialized": m, "dp_states_computed": states,
            "transition_candidates_examined": cands,
            "closing_candidates_examined": m, "reconstruction_steps": m}


def run_tests():
    N = 14  # maximum size: 2^13 masks x 13 x 13 transitions

    # 1. All distances equal: every candidate ties, so the tie rule decides
    #    everything. Smaller predecessor wins -> tour read backwards is 1,2,..,13.
    equal = [[0 if i == j else 1 for j in range(N)] for i in range(N)]
    r = held_karp(equal, with_summary=True)
    assert r["min_cost"] == 14
    assert r["tour"] == [0] + list(range(N - 1, 0, -1)) + [0]
    assert (r["min_cost"], r["tour"]) == held_karp(equal) == reference(equal)
    s = r["operation_summary"]
    for k, v in expected_counts(N).items():
        assert s[k] == v, (k, s[k], v)
    # Every DP state (and the closing scan) keeps its first candidate as a
    # strict improvement; every other candidate is an equal-cost tie.
    assert s["strict_improvements"] == s["dp_states_computed"] + 1
    assert s["ties_kept_smaller_predecessor"] == (
        s["transition_candidates_examined"] - s["dp_states_computed"]
        + s["closing_candidates_examined"] - 1)

    # 2. Line metric d(i, j) = |i - j|: many distinct optimal tours (cost 26).
    line = [[abs(i - j) for j in range(N)] for i in range(N)]
    r = held_karp(line, with_summary=True)
    assert r["min_cost"] == 2 * (N - 1)
    assert (r["min_cost"], r["tour"]) == held_karp(line) == reference(line)
    for k, v in expected_counts(N).items():
        assert r["operation_summary"][k] == v

    # 3. Deterministic structured matrix with heavy but partial ties.
    mix = [[0 if i == j else 1 + (i * j + i + j) % 4 for j in range(N)] for i in range(N)]
    r = held_karp(mix, with_summary=True)
    assert (r["min_cost"], r["tour"]) == held_karp(mix) == reference(mix)
    for k, v in expected_counts(N).items():
        assert r["operation_summary"][k] == v

    # 4. Every case is a valid Hamiltonian cycle from and to city 0.
    for d in (equal, line, mix):
        _, t = held_karp(d)
        assert t[0] == t[-1] == 0 and sorted(t[:-1]) == list(range(N))

    # 5. Original sample and small sizes still behave as before.
    sample = [[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]
    assert held_karp(sample) == (80, [0, 2, 3, 1, 0])
    for n in range(2, 8):
        eq = [[0 if i == j else 1 for j in range(n)] for i in range(n)]
        mx = [[0 if i == j else 1 + (i + j) % 3 for j in range(n)] for i in range(n)]
        for d in (eq, mx):
            assert held_karp(d) == brute_force(d) == reference(d)
    assert held_karp([[0]]) == (0, [0, 0])
    assert held_karp([]) == (0, [])
    print("All tests passed.")


if __name__ == "__main__":
    print(held_karp([[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]))
    run_tests()