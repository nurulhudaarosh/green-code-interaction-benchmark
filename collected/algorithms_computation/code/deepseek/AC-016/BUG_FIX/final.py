import heapq
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass(order=False)
class Item:
    id: str
    arrival: int
    priority: int
    # service_time optional; not needed for ordering

    def key(self) -> Tuple[int, int, str]:
        # Lower priority value = served first.
        # Tie -> earlier arrival first.
        # Tie -> smaller id first (deterministic).
        return (self.priority, self.arrival, self.id)

    def __lt__(self, other: "Item") -> bool:
        return self.key() < other.key()


def simulate(arrivals: List[Item]) -> List[str]:
    """
    Returns the list of item ids in the exact order they are served.
    Rule: sort arrivals by (arrival, id); use a priority heap keyed by
    (priority, arrival, id) for deterministic tie handling.
    """
    # 1) Sort arrivals deterministically by arrival time, then id.
    arrivals_sorted = sorted(arrivals, key=lambda it: (it.arrival, it.id))

    heap: List[Item] = []
    served: List[str] = []

    # 2) Push all (or stream them). For simplicity, push all in sorted order.
    for it in arrivals_sorted:
        heapq.heappush(heap, it)

    # 3) Pop by priority with deterministic tiebreaker.
    while heap:
        served.append(heapq.heappop(heap).id)

    return served


# --- Demonstration ---
if __name__ == "__main__":
    items = [
        Item("A", 0, 5),
        Item("B", 1, 5),
        Item("C", 2, 5),
    ]
    print(simulate(items))   # Expected: ['A', 'B', 'C']