from datetime import datetime, timedelta
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
        # Sort chronologically
        user_events.sort(key=lambda x: (x[0], 0 if x[1] == "login" else 1))

        # Pair logins with next valid logout
        raw_sessions = []
        open_login = None
        for ts, action in user_events:
            if action == "login":
                if open_login is None:
                    open_login = ts
                else:
                    # login while already logged in: ignore duplicate (keep earliest)
                    continue
            elif action == "logout":
                if open_login is not None:
                    if ts >= open_login:
                        raw_sessions.append((open_login, ts))
                    open_login = None
                # logout without login: ignore

        # Merge overlapping or touching sessions
        merged = []
        for start, end in raw_sessions:
            if merged and start <= merged[-1][1]:
                # overlapping or touching
                prev_start, prev_end = merged[-1]
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        # Calculate active seconds
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