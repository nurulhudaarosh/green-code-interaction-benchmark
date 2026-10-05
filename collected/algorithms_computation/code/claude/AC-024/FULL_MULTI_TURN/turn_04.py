import heapq
from typing import Dict, List, Tuple, Union


def assign_rooms(
    intervals: List[Tuple[int, int]],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, object]]:
    """Assign each interval a room ID using the minimum number of rooms.

    Default (include_summary=False): returns rooms, a list where rooms[i] is
    the 0-based room ID for intervals[i].

    include_summary=True: returns {"rooms": rooms, "operation_summary": {...}}.

    A room is reusable when its last interval's end <= the next start.
    Ties: earliest-available room, then lowest room ID (heap tuple ordering).
    """
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end must be >= start")

    n = len(intervals)
    result = [0] * n
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    heap: List[Tuple[int, int]] = []  # (available_at, room_id)
    room_count = 0
    reused = 0
    pops = 0
    pushes = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, rid = heapq.heappop(heap)
            pops += 1
            reused += 1
        else:
            rid = room_count
            room_count += 1
        result[i] = rid
        heapq.heappush(heap, (end, rid))
        pushes += 1

    if not include_summary:
        return result

    return {
        "rooms": result,
        "operation_summary": {
            "intervals_processed": n,
            "rooms_reused": reused,
            "rooms_opened": room_count,
            "heap_pops": pops,
            "heap_pushes": pushes,
            "total_major_operations": n + pops + pushes,
        },
    }


# ----------------------------- test helpers -----------------------------

def reference_assign(intervals):
    """O(n^2) reference using the same rule: among rooms with avail <= start,
    pick min (avail, id); otherwise open a new room."""
    n = len(intervals)
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))
    avail = []  # avail[room_id]
    out = [0] * n
    for i in order:
        s, e = intervals[i]
        best = None
        for rid, a in enumerate(avail):
            if a <= s and (best is None or (a, rid) < best):
                best = (a, rid)
        if best is None:
            rid = len(avail)
            avail.append(e)
        else:
            rid = best[1]
            avail[rid] = e
        out[i] = rid
    return out


def check_valid(intervals, rooms):
    """No two intervals in one room may violate end <= next start."""
    assert len(rooms) == len(intervals)
    by_room = {}
    for iv, r in zip(intervals, rooms):
        by_room.setdefault(r, []).append(iv)
    for lst in by_room.values():
        lst.sort()
        assert all(a[1] <= b[0] for a, b in zip(lst, lst[1:]))
    # IDs are dense 0..m-1
    assert set(rooms) == set(range(len(by_room)))


def max_overlap(intervals):
    """Max simultaneous intervals; valid for positive-length intervals only."""
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()  # at equal time, -1 (end) sorts before +1 (start)
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def lcg(seed):
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % (2 ** 31)
        yield state >> 8


def run_case(name, data, expected, rooms_opened=None, summary=None):
    got = assign_rooms(data)
    assert got == expected, name
    full = assign_rooms(data, include_summary=True)
    assert full["rooms"] == got, name                    # summary never alters result
    assert assign_rooms(data, include_summary=True) == full, name  # deterministic
    s = full["operation_summary"]
    opened = max(got) + 1 if got else 0
    assert s["rooms_opened"] == opened, name
    assert s["rooms_reused"] + s["rooms_opened"] == len(data), name
    assert s["heap_pops"] == s["rooms_reused"], name
    assert s["heap_pushes"] == len(data), name
    assert s["total_major_operations"] == len(data) + s["heap_pops"] + s["heap_pushes"], name
    if rooms_opened is not None:
        assert s["rooms_opened"] == rooms_opened, name
    if summary is not None:
        for k, v in summary.items():
            assert s[k] == v, (name, k)
    check_valid(data, got)
    if data and all(e > s_ for s_, e in data):
        assert opened == max_overlap(data), name          # minimality
    print(f"ok: {name}")


# --------------------------------- tests ---------------------------------

def test_original_cases():
    run_case("defect example", [(0, 5), (1, 3), (6, 8)], [0, 1, 1])
    run_case("empty", [], [])
    run_case("touching", [(1, 3), (3, 5), (5, 7)], [0, 0, 0])
    run_case("chain", [(1, 4), (2, 5), (3, 6), (4, 7)], [0, 1, 2, 0])
    run_case("nested", [(0, 30), (5, 10), (15, 20)], [0, 1, 1])
    run_case("zero-length pair", [(2, 2), (2, 2)], [0, 0])
    try:
        assign_rooms([(3, 2)])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    print("ok: validation")


def test_all_identical_max_heap():
    n = 100_000
    data = [(0, 1)] * n
    run_case("identical x100000", data, list(range(n)),
             rooms_opened=n,
             summary={"rooms_reused": 0, "heap_pops": 0, "heap_pushes": n})


def test_reversed_nested():
    n = 1000
    data = [(i, 2 * n - i) for i in reversed(range(n))]
    run_case("reversed nested", data, list(range(n - 1, -1, -1)), rooms_opened=n)


def test_touching_chain():
    n = 1000
    asc = [(i, i + 1) for i in range(n)]
    run_case("touching chain asc", asc, [0] * n, rooms_opened=1,
             summary={"rooms_reused": n - 1, "heap_pops": n - 1})
    run_case("touching chain desc", list(reversed(asc)), [0] * n, rooms_opened=1)


def test_equal_availability_ties():
    k = 300
    data = [(0, 5)] * k + [(5, 6)] * k
    run_case("equal availability ties", data, list(range(k)) * 2,
             rooms_opened=k,
             summary={"rooms_reused": k, "heap_pops": k, "heap_pushes": 2 * k,
                      "total_major_operations": 5 * k})


def test_earliest_available_not_lowest_id():
    k = 500
    data = [(j, 2000 - j) for j in range(k)] + [(2000, 2001 + m) for m in range(k)]
    expected = list(range(k)) + list(range(k - 1, -1, -1))
    run_case("reverse-ID availability", data, expected, rooms_opened=k)


def test_staggered_full_heap_reuse():
    k = 300
    data = [(0, 10 + j) for j in range(k)] + [(1000, 1001 + j) for j in range(k)]
    run_case("staggered availability", data, list(range(k)) * 2, rooms_opened=k,
             summary={"rooms_reused": k, "heap_pops": k, "heap_pushes": 2 * k,
                      "total_major_operations": 5 * k})


def test_extreme_values():
    big = 10 ** 18
    run_case("extreme values", [(-big, big), (-5, 5), (5, big)], [0, 1, 1])


def test_zero_length_boundaries():
    run_case("zero-length inside", [(1, 5), (3, 3)], [0, 1])
    run_case("zero-length at end", [(1, 5), (5, 5)], [0, 0])
    run_case("zero-length at start", [(5, 7), (5, 5), (1, 5)], [0, 0, 0])


def test_generated_against_reference():
    for seed, allow_zero in ((12345, False), (987, True)):
        g = lcg(seed)
        data = []
        for _ in range(2000):
            s = next(g) % 500
            length = next(g) % 40 if allow_zero else 1 + next(g) % 40
            data.append((s, s + length))
        got = assign_rooms(data)
        assert got == reference_assign(data), seed
        full = assign_rooms(data, include_summary=True)
        assert full["rooms"] == got
        check_valid(data, got)
        if not allow_zero:
            assert max(got) + 1 == max_overlap(data)
        print(f"ok: generated seed={seed} zero_length={allow_zero}")


if __name__ == "__main__":
    test_original_cases()
    test_all_identical_max_heap()
    test_reversed_nested()
    test_touching_chain()
    test_equal_availability_ties()
    test_earliest_available_not_lowest_id()
    test_staggered_full_heap_reuse()
    test_extreme_values()
    test_zero_length_boundaries()
    test_generated_against_reference()
    print("all tests passed")