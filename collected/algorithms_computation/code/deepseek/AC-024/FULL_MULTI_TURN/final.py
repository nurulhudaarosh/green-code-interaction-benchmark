from heapq import heappush, heappop
from typing import List, Union, Dict, Any
import itertools
import time


# ============================================================
# Core solver (original semantics preserved)
# ============================================================

def assign_rooms(
    intervals: List[List[int]],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Minimum Room Assignment.

    Assign every interval to a room so overlapping intervals never share a
    room. A room is reusable iff prev_end <= next_start. Minimize rooms and
    return the room ID for every original interval.

    Determinism:
      - Sort by (start, end, original_index).
      - Min-heap keyed by (end_time, room_id); ties -> smallest room_id.

    Complexity: O(n log n) time, O(n) space.

    Returns:
      - include_summary=False (default): List[int] of room IDs in input order.
      - include_summary=True: dict with 'rooms' and 'operation_summary'.
    """
    n = len(intervals)
    if n == 0:
        if include_summary:
            return {
                "rooms": [],
                "operation_summary": {
                    "sort_operations": 0,
                    "reuse_decisions": 0,
                    "allocate_decisions": 0,
                    "total_decisions": 0,
                    "rooms_used": 0,
                },
            }
        return []

    indexed = [(s, e, i) for i, (s, e) in enumerate(intervals)]
    indexed.sort(key=lambda x: (x[0], x[1], x[2]))

    result = [0] * n
    heap = []              # min-heap of (end_time, room_id)
    next_room_id = 0
    reuse_decisions = 0
    allocate_decisions = 0

    for start, end, orig_idx in indexed:
        if heap and heap[0][0] <= start:
            _, room_id = heappop(heap)
            reuse_decisions += 1
        else:
            room_id = next_room_id
            next_room_id += 1
            allocate_decisions += 1
        result[orig_idx] = room_id
        heappush(heap, (end, room_id))

    if include_summary:
        return {
            "rooms": result,
            "operation_summary": {
                "sort_operations": 1,
                "reuse_decisions": reuse_decisions,
                "allocate_decisions": allocate_decisions,
                "total_decisions": reuse_decisions + allocate_decisions,
                "rooms_used": next_room_id,
            },
        }
    return result


# ============================================================
# Test helpers
# ============================================================

def max_overlap_depth(intervals: List[List[int]]) -> int:
    """Independent oracle: max simultaneous overlaps (touching = no overlap)."""
    events = []
    for s, e in intervals:
        events.append((s, +1))
        events.append((e, -1))
    events.sort()
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def assert_valid_assignment(intervals, rooms):
    """Length/alignment/no-intra-room-overlap invariants."""
    assert len(rooms) == len(intervals)
    by_room = {}
    for i, r in enumerate(rooms):
        by_room.setdefault(r, []).append(i)
    for r, idxs in by_room.items():
        idxs_sorted = sorted(idxs, key=lambda i: (intervals[i][0], intervals[i][1], i))
        for a, b in zip(idxs_sorted, idxs_sorted[1:]):
            assert intervals[a][1] <= intervals[b][0], (
                f"overlap in room {r}: {intervals[a]} vs {intervals[b]}"
            )


# ============================================================
# Tests — original regression
# ============================================================

def test_original_regression():
    assert assign_rooms([[0, 2], [0, 2], [2, 3]]) == [0, 1, 0]
    assert assign_rooms([[1, 3], [1, 3], [3, 5], [3, 5]]) == [0, 1, 0, 1]
    assert assign_rooms([[1, 3], [3, 5], [5, 7]]) == [0, 0, 0]
    assert assign_rooms([[1, 10], [2, 3], [4, 5]]) == [0, 1, 1]
    assert assign_rooms([]) == []
    print("Regression: original outputs unchanged -> OK")


# ============================================================
# Tests — worst-case structures
# ============================================================

def test_max_overlap_depth():
    n = 1000
    intervals = [[0, 10] for _ in range(n)]
    rooms = assign_rooms(intervals)
    assert_valid_assignment(intervals, rooms)
    assert len(set(rooms)) == n == max_overlap_depth(intervals)
    assert rooms == list(range(n))
    s = assign_rooms(intervals, include_summary=True)["operation_summary"]
    assert s["allocate_decisions"] == n and s["reuse_decisions"] == 0
    assert s["rooms_used"] == n and s["total_decisions"] == n
    print(f"Case 1 (max depth n={n}): OK, rooms={s['rooms_used']}")


def test_zero_overlap_depth():
    n = 1000
    intervals = [[i, i + 1] for i in range(n)]
    rooms = assign_rooms(intervals)
    assert_valid_assignment(intervals, rooms)
    assert set(rooms) == {0}
    s = assign_rooms(intervals, include_summary=True)["operation_summary"]
    assert s["allocate_decisions"] == 1 and s["reuse_decisions"] == n - 1
    assert s["rooms_used"] == 1 and s["total_decisions"] == n
    print(f"Case 2 (sequential n={n}): OK, rooms=1, reuses={n-1}")


def test_tie_storm():
    k = 500
    intervals = [[0, 2] for _ in range(k)] + [[2, 3]]
    rooms = assign_rooms(intervals)
    assert_valid_assignment(intervals, rooms)
    assert rooms[:k] == list(range(k))
    assert rooms[k] == 0, f"tie-break failed: got {rooms[k]}, expected 0"
    for _ in range(5):
        assert assign_rooms(intervals) == rooms
    s = assign_rooms(intervals, include_summary=True)["operation_summary"]
    assert s["allocate_decisions"] == k and s["reuse_decisions"] == 1
    assert s["rooms_used"] == k
    print(f"Case 3 (tie storm k={k}): OK, final reuse room=0")


def test_permutation_invariance():
    base = [[0, 2], [0, 2], [2, 3]]
    shapes = set()
    for perm in itertools.permutations(range(len(base))):
        permuted = [base[i] for i in perm]
        rooms = assign_rooms(permuted)
        assert_valid_assignment(permuted, rooms)
        assert len(set(rooms)) == 2
        for i, r in enumerate(rooms):
            if permuted[i] == [0, 2]:
                assert r in (0, 1)
            else:
                assert r == 0
        shapes.add(tuple(sorted(rooms)))
    print(f"Case 4 (permutations={len(shapes)} shapes): OK")


def test_scaling_sanity():
    for n in (1000, 5000, 20000):
        intervals = [[i, i + 1] for i in range(n)]
        t0 = time.perf_counter()
        rooms = assign_rooms(intervals)
        dt = time.perf_counter() - t0
        assert set(rooms) == {0}
        print(f"Case 5: n={n:>6} sequential -> {dt:.4f}s (1 room)")


def test_empty_and_singleton():
    assert assign_rooms([]) == []
    assert assign_rooms([], include_summary=True) == {
        "rooms": [],
        "operation_summary": {
            "sort_operations": 0, "reuse_decisions": 0,
            "allocate_decisions": 0, "total_decisions": 0, "rooms_used": 0,
        },
    }
    assert assign_rooms([[5, 7]]) == [0]
    print("Case 6 (empty/singleton): OK")


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    test_original_regression()
    test_max_overlap_depth()
    test_zero_overlap_depth()
    test_tie_storm()
    test_permutation_invariance()
    test_scaling_sanity()
    test_empty_and_singleton()
    print("\nAll worst-case tests passed.")