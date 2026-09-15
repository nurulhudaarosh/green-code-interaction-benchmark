from datetime import datetime, timedelta
from collections import defaultdict
import json
import sys


def parse_time(ts):
    """Parse a timestamp string into a datetime object."""
    if isinstance(ts, datetime):
        return ts
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {ts}")


def analyze_sessions(events, merge_gap_seconds=0):
    """
    Analyze login/logout events.

    events: iterable of dicts with keys:
        - user (str)
        - type ('login' or 'logout')
        - time (str or datetime)

    merge_gap_seconds: sessions that are separated by <= this gap
                       (and overlap/touch when 0) are merged.

    Returns: dict {user: {'sessions': [(start, end, seconds), ...],
                          'total_seconds': int}}
    """
    # Bucket events by user
    by_user = defaultdict(list)
    for e in events:
        user = e["user"]
        etype = e["type"].lower().strip()
        if etype not in ("login", "logout"):
            continue
        by_user[user].append((parse_time(e["time"]), etype))

    results = {}

    for user, evs in by_user.items():
        # Sort chronologically (login before logout on ties for safety)
        evs.sort(key=lambda x: (x[0], 0 if x[1] == "login" else 1))

        # Pair logins with next valid logout
        raw_sessions = []
        pending_login = None
        for ts, etype in evs:
            if etype == "login":
                if pending_login is None:
                    pending_login = ts
                # else: ignore duplicate login (already in a session)
            else:  # logout
                if pending_login is not None:
                    if ts >= pending_login:
                        raw_sessions.append((pending_login, ts))
                    pending_login = None
                # else: logout without login -> ignore

        # Merge overlapping or touching sessions
        merged = []
        gap = timedelta(seconds=merge_gap_seconds)
        for start, end in raw_sessions:
            if merged and start <= merged[-1][1] + gap:
                # merge
                prev_start, prev_end = merged[-1]
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        # Compute durations
        sessions = []
        total = 0
        for start, end in merged:
            secs = int((end - start).total_seconds())
            sessions.append((start, end, secs))
            total += secs

        results[user] = {"sessions": sessions, "total_seconds": total}

    return results


def format_summary(results, time_fmt="%Y-%m-%d %H:%M:%S"):
    """Produce a sorted, human-readable summary."""
    lines = []
    for user in sorted(results.keys()):
        data = results[user]
        lines.append(f"User: {user}")
        lines.append(f"  Total active seconds: {data['total_seconds']}")
        lines.append(f"  Sessions: {len(data['sessions'])}")
        for i, (start, end, secs) in enumerate(data["sessions"], 1):
            lines.append(
                f"    [{i}] {start.strftime(time_fmt)} -> "
                f"{end.strftime(time_fmt)}  ({secs}s)"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def load_events(path):
    """Load events from a JSON file (list of {user, type, time})."""
    with open(path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        events = load_events(sys.argv[1])
    else:
        # Demo data: overlapping and touching sessions
        events = [
            {"user": "alice", "type": "login",  "time": "2024-01-01 09:00:00"},
            {"user": "alice", "type": "logout", "time": "2024-01-01 09:30:00"},
            {"user": "alice", "type": "login",  "time": "2024-01-01 09:30:00"},  # touching
            {"user": "alice", "type": "logout", "time": "2024-01-01 10:15:00"},
            {"user": "alice", "type": "login",  "time": "2024-01-01 11:00:00"},
            {"user": "alice", "type": "login",  "time": "2024-01-01 11:30:00"},  # duplicate
            {"user": "alice", "type": "logout", "time": "2024-01-01 12:00:00"},
            {"user": "bob",   "type": "login",  "time": "2024-01-01 08:00:00"},
            {"user": "bob",   "type": "logout", "time": "2024-01-01 08:45:00"},
            {"user": "bob",   "type": "logout", "time": "2024-01-01 09:00:00"},  # orphan
            {"user": "bob",   "type": "login",  "time": "2024-01-01 14:00:00"},  # dangling
        ]

    results = analyze_sessions(events, merge_gap_seconds=0)
    print(format_summary(results))