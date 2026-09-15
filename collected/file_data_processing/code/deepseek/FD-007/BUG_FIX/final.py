from datetime import datetime
from collections import defaultdict
import sys


def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def merge_intervals(intervals):
    """Merge overlapping or touching [start, end] intervals."""
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        last = merged[-1]
        if start <= last[1]:  # overlapping or touching
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def analyze(events):
    """
    events: list of (username, action, timestamp_string)
    action: 'login' or 'logout'
    Returns sorted list of (username, total_active_seconds, session_count, sessions)
    """
    per_user = defaultdict(list)
    for user, action, ts in events:
        per_user[user].append((parse_time(ts), action.lower()))

    results = []
    for user, evs in per_user.items():
        evs.sort(key=lambda x: x[0])

        sessions = []
        pending_login = None

        for ts, action in evs:
            if action == "login":
                if pending_login is None:
                    pending_login = ts
            elif action == "logout":
                if pending_login is not None and ts >= pending_login:
                    sessions.append((pending_login, ts))
                    pending_login = None

        # Merge overlapping/touching sessions BEFORE summing active time
        merged = merge_intervals(sessions)
        total_seconds = sum(int((e - s).total_seconds()) for s, e in merged)

        results.append((user, total_seconds, len(merged), merged))

    results.sort(key=lambda x: (-x[1], x[0]))
    return results


def main():
    sample_events = [
        ("alice", "login",  "2024-01-01 09:00:00"),
        ("bob",   "login",  "2024-01-01 09:05:00"),
        ("alice", "logout", "2024-01-01 09:30:00"),
        ("alice", "login",  "2024-01-01 09:30:00"),  # touching -> merged
        ("bob",   "logout", "2024-01-01 09:45:00"),
        ("alice", "logout", "2024-01-01 10:00:00"),
        ("carol", "login",  "2024-01-01 11:00:00"),
        ("carol", "login",  "2024-01-01 11:05:00"),
        ("carol", "logout", "2024-01-01 11:30:00"),
        ("carol", "logout", "2024-01-01 11:45:00"),
        ("bob",   "login",  "2024-01-01 10:30:00"),
        ("bob",   "logout", "2024-01-01 10:40:00"),
        ("dave",  "login",  "2024-01-01 12:00:00"),
        ("dave",  "logout", "2024-01-01 12:20:00"),
        ("dave",  "login",  "2024-01-01 12:10:00"),  # overlaps -> merged
        ("dave",  "logout", "2024-01-01 12:30:00"),
    ]

    if len(sys.argv) > 1:
        events = []
        with open(sys.argv[1]) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 3:
                    continue
                events.append(tuple(parts))
    else:
        events = sample_events

    results = analyze(events)

    print(f"{'User':<10} {'Active (s)':>10} {'Sessions':>9}  Session Ranges")
    print("-" * 70)
    for user, total, count, sessions in results:
        ranges = ", ".join(
            f"{s.strftime('%H:%M:%S')}-{e.strftime('%H:%M:%S')}"
            for s, e in sessions
        )
        print(f"{user:<10} {total:>10} {count:>9}  {ranges}")


if __name__ == "__main__":
    main()