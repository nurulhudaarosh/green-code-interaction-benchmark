from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple


def parse_events(events: List[Tuple[str, str, str]]) -> Dict[str, List[Tuple[datetime, str]]]:
    """Group raw (user, event_type, timestamp_str) events by user."""
    users = defaultdict(list)
    for user, event_type, ts_str in events:
        ts = datetime.fromisoformat(ts_str)
        users[user].append((ts, event_type.lower()))
    return users


def pair_sessions(user_events: List[Tuple[datetime, str]]) -> List[Tuple[datetime, datetime]]:
    """Sort events chronologically and pair each login with the next valid logout."""
    user_events.sort(key=lambda e: e[0])

    sessions = []
    pending_login = None

    for ts, event_type in user_events:
        if event_type == "login":
            pending_login = ts  # newest open login wins; unmatched prior login discarded
        elif event_type == "logout":
            if pending_login is not None and ts >= pending_login:
                sessions.append((pending_login, ts))
                pending_login = None
            # logout without a matching login is ignored

    return sessions


def merge_sessions(sessions: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """
    Merge overlapping or touching (start <= previous end) intervals.
    This MUST run before any duration calculation, otherwise overlapping
    sessions get summed independently and double-count the shared time.
    """
    if not sessions:
        return []

    ordered = sorted(sessions, key=lambda s: s[0])
    merged = [ordered[0]]

    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # overlap or touch -> combine into one interval
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def calculate_active_seconds(sessions: List[Tuple[datetime, datetime]]) -> float:
    """
    Sum durations of non-overlapping intervals.
    Defensively re-merges first, so this function is safe to call
    even if the caller forgot to merge — it can never double-count.
    """
    safe_sessions = merge_sessions(sessions)
    return sum((end - start).total_seconds() for start, end in safe_sessions)


def analyze_login_logout(events: List[Tuple[str, str, str]]) -> Dict[str, Dict]:
    """
    Full pipeline: group -> pair -> merge -> summarize.
    Merge happens BEFORE duration calculation to prevent double-counting
    overlapping/touching sessions. Returns summaries sorted by user.
    """
    grouped = parse_events(events)
    summaries = {}

    for user, user_events in grouped.items():
        raw_sessions = pair_sessions(user_events)
        merged = merge_sessions(raw_sessions)          # merge first
        active_seconds = calculate_active_seconds(merged)  # then calculate

        summaries[user] = {
            "sessions": [
                (start.isoformat(), end.isoformat()) for start, end in merged
            ],
            "session_count": len(merged),
            "active_seconds": active_seconds,
        }

    return dict(sorted(summaries.items(), key=lambda kv: kv[0]))


def print_summary(summaries: Dict[str, Dict]) -> None:
    for user, data in summaries.items():
        print(f"User: {user}")
        print(f"  Sessions ({data['session_count']}):")
        for start, end in data["sessions"]:
            print(f"    {start} -> {end}")
        print(f"  Active seconds: {data['active_seconds']:.2f}")
        print()


if __name__ == "__main__":
    sample_events = [
        ("alice", "login", "2024-01-01T09:00:00"),
        ("alice", "logout", "2024-01-01T10:00:00"),
        ("alice", "login", "2024-01-01T09:30:00"),  # overlaps prior session
        ("alice", "logout", "2024-01-01T11:30:00"),
        ("alice", "login", "2024-01-01T11:30:00"),  # touches previous logout -> merge
        ("alice", "logout", "2024-01-01T12:00:00"),
        ("alice", "login", "2024-01-01T13:00:00"),
        ("alice", "logout", "2024-01-01T13:45:00"),
        ("bob", "login", "2024-01-01T08:00:00"),
        ("bob", "login", "2024-01-01T08:30:00"),  # duplicate login, overrides pending
        ("bob", "logout", "2024-01-01T09:00:00"),
        ("bob", "logout", "2024-01-01T09:30:00"),  # unmatched logout, ignored
    ]

    result = analyze_login_logout(sample_events)
    print_summary(result)