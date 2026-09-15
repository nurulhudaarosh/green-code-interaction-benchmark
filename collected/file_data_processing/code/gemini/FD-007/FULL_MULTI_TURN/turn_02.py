from datetime import datetime
from collections import defaultdict

def parse_time(ts_str):
    """Parses ISO timestamp string into a datetime object."""
    return datetime.fromisoformat(ts_str)

def analyze_user_sessions(events):
    """
    Analyzes login/logout events for each user.
    - Sorts events chronologically per user.
    - Pairs logins with the next valid logout.
    - Merges overlapping or adjacent sessions BEFORE computing active time.
    - Returns sorted user summaries with total non-overlapping active seconds.
    """
    user_events = defaultdict(list)
    for event in events:
        user_events[event["user"]].append(event)
    
    user_summaries = {}

    for user, u_events in user_events.items():
        # 1. Sort events chronologically
        u_events.sort(key=lambda x: parse_time(x["timestamp"]))
        
        raw_sessions = []
        current_login = None
        
        # 2. Extract valid raw login-logout pairs
        for event in u_events:
            action = event["action"].lower()
            ts = parse_time(event["timestamp"])
            
            if action == "login":
                # If a login occurs while already logged in, record the preceding session
                if current_login is not None:
                    raw_sessions.append((current_login, ts))
                current_login = ts
            elif action == "logout" and current_login is not None:
                if ts >= current_login:
                    raw_sessions.append((current_login, ts))
                    current_login = None

        if not raw_sessions:
            user_summaries[user] = {
                "total_active_seconds": 0,
                "sessions": []
            }
            continue

        # Sort intervals by start time to guarantee order for interval merging
        raw_sessions.sort(key=lambda x: x[0])

        # 3. Merge overlapping or touching intervals (start <= last_end)
        merged_sessions = [list(raw_sessions[0])]
        for start, end in raw_sessions[1:]:
            last_start, last_end = merged_sessions[-1]
            if start <= last_end:  # Overlapping or touching intervals
                merged_sessions[-1][1] = max(last_end, end)
            else:
                merged_sessions.append([start, end])

        # 4. Calculate total active seconds from merged, non-overlapping intervals
        total_seconds = sum(
            int((end - start).total_seconds()) for start, end in merged_sessions
        )

        user_summaries[user] = {
            "total_active_seconds": total_seconds,
            "sessions": [
                (start.isoformat(), end.isoformat()) for start, end in merged_sessions
            ]
        }

    # 5. Return sorted summaries by user ID/name
    return dict(sorted(user_summaries.items()))

# Example usage demonstrating merged overlapping sessions:
if __name__ == "__main__":
    sample_events = [
        # Session 1: 08:00 to 09:00
        {"user": "alice", "action": "login", "timestamp": "2026-03-30T08:00:00"},
        {"user": "alice", "action": "logout", "timestamp": "2026-03-30T09:00:00"},
        # Session 2: 08:30 to 09:30 (Overlaps with Session 1 -> Merges into 08:00 to 09:30)
        {"user": "alice", "action": "login", "timestamp": "2026-03-30T08:30:00"},
        {"user": "alice", "action": "logout", "timestamp": "2026-03-30T09:30:00"},
    ]

    import json
    results = analyze_user_sessions(sample_events)
    print(json.dumps(results, indent=2))