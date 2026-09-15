from collections import defaultdict
from datetime import datetime

def parse_events(events):
    """
    events: list of tuples (user, event_type, timestamp_str)
    event_type: 'login' or 'logout'
    timestamp_str: 'YYYY-MM-DD HH:MM:SS'
    """
    user_events = defaultdict(list)
    for user, event_type, ts in events:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        user_events[user].append((dt, event_type))
    return user_events


def pair_sessions(events):
    """
    Given a list of (timestamp, event_type) for one user,
    sort chronologically and pair each login with the next valid logout.
    Returns list of (login_time, logout_time) tuples (may overlap/touch).
    """
    events = sorted(events, key=lambda x: (x[0], x[1] == "login"))
    sessions = []
    pending_login = None

    for ts, etype in events:
        if etype == "login":
            if pending_login is None:
                pending_login = ts
        elif etype == "logout":
            if pending_login is not None and ts > pending_login:
                sessions.append((pending_login, ts))
                pending_login = None

    return sessions


def merge_sessions(sessions):
    """
    Merge overlapping or touching (start <= previous end) intervals.
    Always sorts by start time first so merging is correct regardless
    of input order.
    """
    if not sessions:
        return []

    sessions = sorted(sessions, key=lambda x: x[0])
    merged = [sessions[0]]

    for start, end in sessions[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:          # overlap or touch -> merge
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def calculate_active_seconds(merged_sessions):
    """
    IMPORTANT: only call this on already-merged, non-overlapping sessions,
    otherwise overlapping time gets counted twice.
    """
    return sum((end - start).total_seconds() for start, end in merged_sessions)


def analyze(events):
    """
    Main entry point.
    events: list of (user, event_type, timestamp_str)
    Returns: dict {user: {"sessions": [...], "active_seconds": float}}
    """
    user_events = parse_events(events)
    summary = {}

    for user, evs in user_events.items():
        raw_sessions = pair_sessions(evs)      # step 1: pair
        merged = merge_sessions(raw_sessions)  # step 2: merge BEFORE summing
        active_seconds = calculate_active_seconds(merged)  # step 3: sum merged only
        summary[user] = {
            "sessions": merged,
            "active_seconds": active_seconds
        }

    return summary


def print_summary(summary):
    for user in sorted(summary.keys()):
        data = summary[user]
        print(f"User: {user}")
        print(f"  Active seconds: {data['active_seconds']:.0f}")
        print("  Sessions:")
        for start, end in data["sessions"]:
            print(f"    {start} -> {end}")
        print()


if __name__ == "__main__":
    sample_events = [
        ("alice", "login", "2024-01-01 09:00:00"),
        ("alice", "logout", "2024-01-01 10:00:00"),
        ("alice", "login", "2024-01-01 10:00:00"),   # touching -> merges
        ("alice", "logout", "2024-01-01 11:30:00"),
        ("bob", "login", "2024-01-01 08:00:00"),
        ("bob", "login", "2024-01-01 08:30:00"),      # duplicate login ignored
        ("bob", "logout", "2024-01-01 09:15:00"),
        ("bob", "login", "2024-01-01 09:10:00"),      # overlapping -> merges
        ("bob", "logout", "2024-01-01 09:45:00"),
    ]

    result = analyze(sample_events)
    print_summary(result)