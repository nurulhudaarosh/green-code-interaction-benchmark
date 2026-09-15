from datetime import datetime
from collections import defaultdict


def parse_timestamp(ts):
    """Parse various timestamp formats into datetime."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {ts}")


def merge_intervals(intervals):
    """
    Merge overlapping or touching intervals.
    intervals: list of (start, end) tuples, unsorted.
    Returns: sorted list of merged (start, end) tuples.
    """
    if not intervals:
        return []

    # Sort by start, then end
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))

    merged = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        prev_start, prev_end = merged[-1]
        # Overlapping or touching (start <= prev_end)
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def analyze_sessions(events):
    """
    events: list of dicts with keys 'user', 'timestamp', 'action' ('login'/'logout')
    Returns: dict user -> {'sessions': [(start, end)], 'active_seconds': int, 'session_count': int}
    """
    # Group events by user
    by_user = defaultdict(list)
    for e in events:
        user = e["user"]
        ts = parse_timestamp(e["timestamp"]) if isinstance(e["timestamp"], str) else e["timestamp"]
        action = e["action"].strip().lower()
        if action not in ("login", "logout"):
            continue
        by_user[user].append((ts, action))

    results = {}

    for user, user_events in by_user.items():
        # Sort chronologically; on tie, process logout before login
        # so a logout at the same instant as a login pairs with the earlier session.
        user_events.sort(key=lambda x: (x[0], 0 if x[1] == "logout" else 1))

        # Pair logins with next valid logout
        raw_sessions = []
        open_login = None
        for ts, action in user_events:
            if action == "login":
                if open_login is None:
                    open_login = ts
                # else: already logged in — keep earliest login, ignore duplicate
            elif action == "logout":
                if open_login is not None and ts >= open_login:
                    raw_sessions.append((open_login, ts))
                    open_login = None
                # else: stray logout, ignore

        # Merge overlapping / touching intervals BEFORE counting
        merged = merge_intervals(raw_sessions)

        # Calculate active seconds from merged intervals (no double counting)
        active_seconds = sum(int((end - start).total_seconds()) for start, end in merged)

        results[user] = {
            "sessions": merged,
            "active_seconds": active_seconds,
            "session_count": len(merged),
        }

    return results


def write_summary(results, output_path):
    """Write sorted user summaries to file."""
    with open(output_path, "w") as f:
        for user in sorted(results.keys()):
            data = results[user]
            f.write(f"User: {user}\n")
            f.write(f"  Sessions: {data['session_count']}\n")
            f.write(f"  Active seconds: {data['active_seconds']}\n")
            for start, end in data["sessions"]:
                dur = int((end - start).total_seconds())
                f.write(f"    {start} -> {end} ({dur}s)\n")
            f.write("\n")


if __name__ == "__main__":
    events = [
        {"user": "alice", "timestamp": "2024-01-01 09:00:00", "action": "login"},
        {"user": "alice", "timestamp": "2024-01-01 09:30:00", "action": "logout"},
        {"user": "alice", "timestamp": "2024-01-01 09:30:00", "action": "login"},  # touching
        {"user": "alice", "timestamp": "2024-01-01 10:00:00", "action": "logout"},
        {"user": "bob", "timestamp": "2024-01-01 08:00:00", "action": "login"},
        {"user": "bob", "timestamp": "2024-01-01 08:15:00", "action": "logout"},
        {"user": "bob", "timestamp": "2024-01-01 08:10:00", "action": "login"},  # overlapping
        {"user": "bob", "timestamp": "2024-01-01 08:45:00", "action": "logout"},
        {"user": "bob", "timestamp": "2024-01-01 08:50:00", "action": "logout"},  # stray logout
        {"user": "carol", "timestamp": "2024-01-01 12:00:00", "action": "login"},  # never logs out
    ]

    results = analyze_sessions(events)
    write_summary(results, "user_summaries.txt")

    for user in sorted(results):
        print(user, results[user])