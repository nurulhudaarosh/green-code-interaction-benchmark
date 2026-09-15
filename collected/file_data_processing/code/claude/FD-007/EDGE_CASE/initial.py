from datetime import datetime
from collections import defaultdict

def parse_events(events):
    """
    events: list of dicts like {"user": "alice", "action": "login"/"logout", "timestamp": "2024-01-01T10:00:00"}
    Returns: dict of user -> sorted list of (datetime, action)
    """
    by_user = defaultdict(list)
    for e in events:
        ts = e["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        by_user[e["user"]].append((ts, e["action"].lower()))

    for user in by_user:
        by_user[user].sort(key=lambda x: x[0])

    return by_user


def pair_sessions(sorted_events):
    """
    Given a chronologically sorted list of (timestamp, action) for one user,
    pair each login with the next valid logout that follows it.
    Unmatched logins (no following logout) and stray logouts (no preceding
    open login) are ignored/discarded gracefully.
    Returns list of (login_time, logout_time) tuples.
    """
    sessions = []
    open_login = None

    for ts, action in sorted_events:
        if action == "login":
            if open_login is None:
                open_login = ts
            # if a login arrives while one is already open, keep the
            # earliest login as the session start (ignore duplicate login)
        elif action == "logout":
            if open_login is not None:
                if ts > open_login:
                    sessions.append((open_login, ts))
                open_login = None
            # stray logout with no matching login is discarded

    # any trailing open login with no logout is discarded (incomplete session)
    return sessions


def merge_sessions(sessions):
    """
    Merge sessions that overlap or touch (logout_time >= next login_time).
    sessions: list of (start, end) tuples, need not be sorted.
    Returns merged, sorted list of (start, end) tuples.
    """
    if not sessions:
        return []

    sessions = sorted(sessions, key=lambda x: x[0])
    merged = [sessions[0]]

    for start, end in sessions[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # overlapping or touching
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def total_active_seconds(merged_sessions):
    return sum((end - start).total_seconds() for start, end in merged_sessions)


def analyze(events):
    """
    Main entry point.
    Returns dict: user -> {
        "sessions": [(start, end), ...],   # merged, chronological
        "active_seconds": float,
        "session_count": int
    }
    """
    by_user = parse_events(events)
    summary = {}

    for user, sorted_events in by_user.items():
        raw_sessions = pair_sessions(sorted_events)
        merged = merge_sessions(raw_sessions)
        summary[user] = {
            "sessions": merged,
            "active_seconds": total_active_seconds(merged),
            "session_count": len(merged),
        }

    return summary


def format_summary(summary):
    """
    Produce a sorted, human-readable summary string.
    Sorted by username alphabetically.
    """
    lines = []
    for user in sorted(summary.keys()):
        data = summary[user]
        lines.append(f"User: {user}")
        lines.append(f"  Sessions: {data['session_count']}")
        lines.append(f"  Active time: {data['active_seconds']:.0f} seconds")
        for start, end in data["sessions"]:
            lines.append(f"    {start.isoformat()} -> {end.isoformat()}")
        lines.append("")
    return "\n".join(lines)


def write_summary(summary, filepath="session_summary.txt"):
    with open(filepath, "w") as f:
        f.write(format_summary(summary))


if __name__ == "__main__":
    sample_events = [
        {"user": "alice", "action": "login", "timestamp": "2024-01-01T09:00:00"},
        {"user": "alice", "action": "logout", "timestamp": "2024-01-01T09:30:00"},
        {"user": "alice", "action": "login", "timestamp": "2024-01-01T09:30:00"},  # touching
        {"user": "alice", "action": "logout", "timestamp": "2024-01-01T10:15:00"},
        {"user": "alice", "action": "login", "timestamp": "2024-01-01T11:00:00"},
        {"user": "alice", "action": "logout", "timestamp": "2024-01-01T11:20:00"},
        {"user": "bob", "action": "logout", "timestamp": "2024-01-01T08:00:00"},  # stray
        {"user": "bob", "action": "login", "timestamp": "2024-01-01T08:05:00"},
        {"user": "bob", "action": "login", "timestamp": "2024-01-01T08:10:00"},  # dup login
        {"user": "bob", "action": "logout", "timestamp": "2024-01-01T08:45:00"},
    ]

    result = analyze(sample_events)
    print(format_summary(result))
    write_summary(result)