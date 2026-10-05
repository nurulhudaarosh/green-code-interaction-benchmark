import heapq
import unittest

def solve_interval_partitioning(intervals, include_summary=False):
    """
    Assigns every interval a room ID to minimize total rooms without overlapping.
    Deterministically reuses the smallest available room_id.
    
    :param intervals: List of tuples/lists [start, end]
    :param include_summary: Bool, if True returns a dict with assignments and operation summary.
    :return: List of room IDs if include_summary is False, 
             else dict with 'room_assignments' and 'operation_summary'.
    """
    if not intervals:
        result = []
        if not include_summary:
            return result
        return {
            "room_assignments": result,
            "operation_summary": {
                "total_intervals": 0,
                "rooms_created": 0,
                "room_reuses": 0,
                "room_releases": 0,
                "total_decisions": 0
            }
        }
    
    # Store intervals with their original index: (start, end, original_index)
    # Sort deterministically by start time, end time, then original index
    indexed_intervals = sorted(
        [(start, end, i) for i, (start, end) in enumerate(intervals)],
        key=lambda x: (x[0], x[1], x[2])
    )
    
    busy_rooms = []  # Min-heap: (end_time, room_id)
    free_rooms = []  # Min-heap: room_id
    
    assignments = [0] * len(intervals)
    next_room_id = 0
    
    room_releases = 0
    room_reuses = 0
    rooms_created = 0
    
    for start, end, orig_idx in indexed_intervals:
        # Transfer all rooms available at `start` from busy_rooms to free_rooms
        while busy_rooms and busy_rooms[0][0] <= start:
            _, freed_room_id = heapq.heappop(busy_rooms)
            heapq.heappush(free_rooms, freed_room_id)
            room_releases += 1
            
        # Reuse smallest available room_id if any free room exists
        if free_rooms:
            room_id = heapq.heappop(free_rooms)
            room_reuses += 1
        else:
            room_id = next_room_id
            next_room_id += 1
            rooms_created += 1
            
        assignments[orig_idx] = room_id
        heapq.heappush(busy_rooms, (end, room_id))

    if not include_summary:
        return assignments

    summary = {
        "total_intervals": len(intervals),
        "rooms_created": rooms_created,
        "room_reuses": room_reuses,
        "room_releases": room_releases,
        "total_decisions": len(intervals) + room_releases
    }

    return {
        "room_assignments": assignments,
        "operation_summary": summary
    }


# ==========================================
# Comprehensive Unit Tests
# ==========================================

class TestMinimumRoomAssignment(unittest.TestCase):

    def test_empty_and_single(self):
        """Test edge cases with empty lists and single intervals."""
        self.assertEqual(solve_interval_partitioning([]), [])
        self.assertEqual(solve_interval_partitioning([[1, 5]]), [0])

    def test_worst_case_staggered_flush(self):
        """
        Worst-case scenario:
        Phase 1: N intervals [0, 10], [1, 10], ..., [N-1, 10] all overlap.
                 Requires N rooms (0 to N-1).
        Phase 2: At time 10, all N rooms finish.
                 N new intervals starting at 10 must drain free_rooms in order.
                 Smallest room_ids (0 to N-1) must be assigned deterministically.
        """
        N = 100
        phase1 = [[i, 10] for i in range(N)]
        phase2 = [[10, 20] for _ in range(N)]
        intervals = phase1 + phase2

        result = solve_interval_partitioning(intervals, include_summary=True)
        assignments = result["room_assignments"]
        summary = result["operation_summary"]

        # Phase 1 intervals should be assigned room IDs 0 to N-1
        self.assertEqual(assignments[:N], list(range(N)))
        
        # Phase 2 intervals should reuse room IDs 0 to N-1 deterministically
        self.assertEqual(assignments[N:], list(range(N)))
        
        # Verify operation summary counts
        self.assertEqual(summary["total_intervals"], 200)
        self.assertEqual(summary["rooms_created"], N)
        self.assertEqual(summary["room_reuses"], N)
        self.assertEqual(summary["room_releases"], N)

    def test_tie_breaking_smallest_room_id(self):
        """Verify that when multiple rooms are free, the smallest room_id is reused."""
        intervals = [[0, 10], [0, 5], [5, 7], [10, 15]]
        # 1. [0, 10] -> Room 0 (ends at 10)
        # 2. [0, 5]  -> Room 1 (ends at 5)
        # 3. [5, 7]  -> Room 1 free, reused -> Room 1 (ends at 7)
        # 4. [10, 15]-> Both Room 0 (ends 10) and Room 1 (ends 7) free. Must pick Room 0!
        expected = [0, 1, 1, 0]
        self.assertEqual(solve_interval_partitioning(intervals), expected)

    def test_touching_endpoints(self):
        """Verify that intervals touching at endpoints (end == start) correctly reuse rooms."""
        intervals = [[0, 5], [5, 10], [10, 15], [15, 20]]
        self.assertEqual(solve_interval_partitioning(intervals), [0, 0, 0, 0])

    def test_unsorted_input_order_preservation(self):
        """Verify output maintains original index mapping for out-of-order inputs."""
        intervals = [[10, 15], [0, 5], [2, 8]]
        # Order sorted by start: [0, 5] (idx 1), [2, 8] (idx 2), [10, 15] (idx 0)
        # [0, 5]  -> Room 0
        # [2, 8]  -> Room 1
        # [10, 15]-> Room 0 free and reused
        # Result mapped to original indices [0, 1, 2] -> [0, 0, 1]
        self.assertEqual(solve_interval_partitioning(intervals), [0, 0, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)