from heapq import heappush, heappop


def simulate_queue(jobs, include_operation_summary=False):
    """
    Simulate a non-preemptive single-server priority queue.

    Rules:
      - Larger priority runs first.
      - Ties: earlier arrival first, then smaller job ID.
      - Non-preemptive: once started, a job runs to completion.
      - Single server: one job at a time; idle if none waiting.

    Parameters
    ----------
    jobs : list of tuples
        Each job is (job_id, arrival_time, service_time, priority).
    include_operation_summary : bool, default False
        If True, also return an `operation_summary` dict.

    Returns
    -------
    results : list of dict
        One entry per input job, in original input order.
    average_waiting_time : float
    operation_summary : dict, optional
        Only when include_operation_summary=True.
    """
    n = len(jobs)
    if n == 0:
        if include_operation_summary:
            return [], 0.0, {
                "arrival_loads": 0,
                "idle_jumps": 0,
                "dispatches": 0,
                "total_operations": 0,
            }
        return [], 0.0

    # Positional identity so duplicate job_ids cannot collide.
    indexed = [
        (job_id, arrival, service, priority, pos)
        for pos, (job_id, arrival, service, priority) in enumerate(jobs)
    ]
    indexed.sort(key=lambda x: (x[1], x[0], x[4]))

    time = 0
    completed = 0
    idx = 0
    ready_heap = []          # (-priority, arrival, job_id, service, pos)
    results = [None] * n

    arrival_loads = 0
    idle_jumps = 0
    dispatches = 0

    while completed < n:
        # Load every job that has arrived by the current time.
        while idx < n and indexed[idx][1] <= time:
            job_id, arrival, service, priority, pos = indexed[idx]
            heappush(ready_heap, (-priority, arrival, job_id, service, pos))
            idx += 1
            arrival_loads += 1

        if not ready_heap:
            # Idle until the next arrival.
            time = indexed[idx][1]
            idle_jumps += 1
            continue

        neg_priority, arrival, job_id, service, pos = heappop(ready_heap)

        start_time = time
        completion_time = start_time + service
        waiting_time = start_time - arrival

        results[pos] = {
            "job_id": job_id,
            "arrival_time": arrival,
            "service_time": service,
            "priority": -neg_priority,
            "start_time": start_time,
            "completion_time": completion_time,
            "waiting_time": waiting_time,
        }

        time = completion_time
        completed += 1
        dispatches += 1

    total_waiting = sum(r["waiting_time"] for r in results)
    average_waiting_time = total_waiting / n

    if include_operation_summary:
        operation_summary = {
            "arrival_loads": arrival_loads,
            "idle_jumps": idle_jumps,
            "dispatches": dispatches,
            "total_operations": arrival_loads + idle_jumps + dispatches,
        }
        return results, average_waiting_time, operation_summary

    return results, average_waiting_time


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _check_original_fields(results):
    for r in results:
        for key in (
            "job_id",
            "arrival_time",
            "service_time",
            "priority",
            "start_time",
            "completion_time",
            "waiting_time",
        ):
            assert key in r, f"missing field: {key}"
        assert r["completion_time"] == r["start_time"] + r["service_time"]
        assert r["waiting_time"] == r["start_time"] - r["arrival_time"]


def test_all_arrive_at_zero_mixed_priority():
    # Full heap before any dispatch; exercises priority then job_id tie-breaks.
    jobs = [
        (1, 0, 3, 1),
        (2, 0, 2, 3),
        (3, 0, 1, 2),
        (4, 0, 4, 3),
        (5, 0, 2, 1),
    ]
    results, avg = simulate_queue(jobs)
    _check_original_fields(results)
    # Order of dispatch by (priority desc, arrival asc, job_id asc):
    #   (2,0,2,3) and (4,0,4,3) tie on priority; job_id 2 first.
    #   Then (3,0,1,2). Then (1,0,3,1) and (5,0,2,1); job_id 1 first.
    order = [r["job_id"] for r in sorted(results, key=lambda r: r["start_time"])]
    assert order == [2, 4, 3, 1, 5], order

    expected_completions = {2: 2, 4: 6, 3: 7, 1: 10, 5: 12}
    for r in results:
        assert r["completion_time"] == expected_completions[r["job_id"]]

    expected_wait = {2: 0, 4: 2, 3: 6, 1: 7, 5: 10}
    for r in results:
        assert r["waiting_time"] == expected_wait[r["job_id"]]

    assert abs(avg - (0 + 2 + 6 + 7 + 10) / 5) < 1e-12


def test_strictly_increasing_no_queue():
    # Each job arrives exactly when the previous finishes: heap size 1, no idle.
    jobs = [
        (1, 0, 2, 5),
        (2, 2, 3, 5),
        (3, 5, 1, 5),
        (4, 6, 4, 5),
    ]
    results, avg, summary = simulate_queue(jobs, include_operation_summary=True)
    _check_original_fields(results)
    assert [r["start_time"] for r in results] == [0, 2, 5, 6]
    assert [r["completion_time"] for r in results] == [2, 5, 6, 10]
    assert all(r["waiting_time"] == 0 for r in results)
    assert abs(avg) < 1e-12
    assert summary["idle_jumps"] == 0
    assert summary["dispatches"] == 4
    assert summary["arrival_loads"] == 4


def test_identical_priority_and_arrival_distinct_ids():
    # Only the third tie-break (smaller job_id) decides dispatch order.
    jobs = [(jid, 0, 1, 7) for jid in [4, 2, 5, 1, 3]]
    results, avg = simulate_queue(jobs)
    _check_original_fields(results)
    dispatch = [r["job_id"] for r in sorted(results, key=lambda r: r["start_time"])]
    assert dispatch == [1, 2, 3, 4, 5], dispatch
    # Start times: 0,1,2,3,4; waiting: 0,1,2,3,4
    for r in results:
        assert r["start_time"] == r["job_id"] - 1
        assert r["waiting_time"] == r["job_id"] - 1
    assert abs(avg - (0 + 1 + 2 + 3 + 4) / 5) < 1e-12


def test_large_idle_gaps():
    # Every job arrives long after the previous finishes: idle-jump every time.
    jobs = [
        (1, 0, 1, 1),
        (2, 100, 1, 1),
        (3, 200, 1, 1),
        (4, 300, 1, 1),
    ]
    results, avg, summary = simulate_queue(jobs, include_operation_summary=True)
    _check_original_fields(results)
    assert [r["start_time"] for r in results] == [0, 100, 200, 300]
    assert [r["completion_time"] for r in results] == [1, 101, 201, 301]
    assert all(r["waiting_time"] == 0 for r in results)
    assert summary["idle_jumps"] == 3
    assert summary["dispatches"] == 4
    assert abs(avg) < 1e-12


def test_descending_priorities_staggered_arrivals():
    # Higher-priority jobs arrive while lower-priority ones run.
    # Non-preemption must hold: a running job is never interrupted.
    jobs = [
        (1, 0, 5, 1),   # runs 0..5
        (2, 1, 2, 2),
        (3, 2, 2, 3),
        (4, 3, 2, 4),
    ]
    results, avg = simulate_queue(jobs)
    _check_original_fields(results)
    by_id = {r["job_id"]: r for r in results}

    # Job 1 started first at t=0 and must run to completion at t=5.
    assert by_id[1]["start_time"] == 0
    assert by_id[1]["completion_time"] == 5
    # Job 4 has highest priority; runs 5..7.
    assert by_id[4]["start_time"] == 5
    assert by_id[4]["completion_time"] == 7
    # Then job 3 (priority 3): 7..9.
    assert by_id[3]["start_time"] == 7
    assert by_id[3]["completion_time"] == 9
    # Then job 2 (priority 2): 9..11.
    assert by_id[2]["start_time"] == 9
    assert by_id[2]["completion_time"] == 11

    waits = {1: 0, 4: 2, 3: 5, 2: 8}
    for jid, w in waits.items():
        assert by_id[jid]["waiting_time"] == w
    assert abs(avg - (0 + 8 + 5 + 2) / 4) < 1e-12


def test_zero_service_times():
    # Completion equals start; clock does not advance for a zero-service job.
    jobs = [
        (1, 0, 0, 1),
        (2, 0, 3, 2),
        (3, 0, 0, 2),
    ]
    results, avg = simulate_queue(jobs)
    _check_original_fields(results)
    by_id = {r["job_id"]: r for r in results}
    # Priority 2 jobs (id 2, 3) run before priority 1 (id 1).
    # Tie on priority 2, same arrival 0: id 2 first, then id 3.
    assert by_id[2]["start_time"] == 0
    assert by_id[2]["completion_time"] == 3
    assert by_id[3]["start_time"] == 3
    assert by_id[3]["completion_time"] == 3   # zero service
    assert by_id[1]["start_time"] == 3
    assert by_id[1]["completion_time"] == 3   # zero service
    assert by_id[3]["waiting_time"] == 3
    assert by_id[1]["waiting_time"] == 3
    assert abs(avg - (3 + 0 + 3) / 3) < 1e-12


def test_large_stress_mixed():
    # O(n log n) stress: many jobs, all at time 0, mixed priorities.
    n = 5000
    jobs = []
    for jid in range(1, n + 1):
        priority = (jid * 7919) % 100          # deterministic pseudo-mix
        service = 1 + (jid % 5)
        jobs.append((jid, 0, service, priority))

    results, avg, summary = simulate_queue(jobs, include_operation_summary=True)
    _check_original_fields(results)

    # All jobs processed exactly once.
    assert len(results) == n
    assert sorted(r["job_id"] for r in results) == list(range(1, n + 1))

    # Dispatches == n; no idle because all arrive at t=0.
    assert summary["dispatches"] == n
    assert summary["arrival_loads"] == n
    assert summary["idle_jumps"] == 0

    # Server is busy the entire time: total completion == sum of services.
    total_service = sum(j[2] for j in jobs)
    assert max(r["completion_time"] for r in results) == total_service

    # Non-overlap: sorted by start, each start == previous completion.
    ordered = sorted(results, key=lambda r: r["start_time"])
    for prev, cur in zip(ordered, ordered[1:]):
        assert prev["completion_time"] == cur["start_time"]

    # Average is the mean of recorded waits.
    expected_avg = sum(r["waiting_time"] for r in results) / n
    assert abs(avg - expected_avg) < 1e-12


def test_original_outputs_unchanged_when_summary_disabled():
    jobs = [
        (1, 0, 5, 2),
        (1, 1, 3, 5),
        (3, 2, 2, 5),
        (4, 3, 4, 1),
        (5, 10, 1, 9),
    ]
    r1, a1 = simulate_queue(jobs)
    r2, a2, _ = simulate_queue(jobs, include_operation_summary=True)
    assert r1 == r2
    assert abs(a1 - a2) < 1e-12


if __name__ == "__main__":
    tests = [
        test_all_arrive_at_zero_mixed_priority,
        test_strictly_increasing_no_queue,
        test_identical_priority_and_arrival_distinct_ids,
        test_large_idle_gaps,
        test_descending_priorities_staggered_arrivals,
        test_zero_service_times,
        test_large_stress_mixed,
        test_original_outputs_unchanged_when_summary_disabled,
    ]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")