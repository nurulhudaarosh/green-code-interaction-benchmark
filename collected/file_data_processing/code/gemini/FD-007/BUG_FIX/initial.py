from datetime import datetime
from collections import defaultdict

def analyze_user_sessions(events):
    """
    Analyzes login/logout events for users.
    
    Expected event format: 
    [{"user": "alice", "type": "login", "timestamp": "2026-09-12T08:00:00"}, ...]
    """
    # 1. Parse timestamps and group by user
    user_events = defaultdict(list)
    for event in events:
        ts = datetime.fromisoformat(event["timestamp"])
        user_events[event["user"]].append((ts, event["type"]))

    summaries = []

    # Process each user independently
    for user, ev_list in sorted(user_events.items()):
        # Sort chronologically by timestamp
        ev_list.sort(key=lambda x: x[0])

        # 2. Pair each login with the next valid logout
        raw_sessions = []
        current_login = None

        for ts, ev_type in ev_list:
            if ev_type == "login":
                # If already logged in, ignore or overwrite (taking the earlier or latest; 
                # taking first login here to match standard session start)
                if current_login is None:
                    current_login = ts
            elif ev_type == "logout":
                if current_login is not None:
                    raw_sessions.append((current_login, ts))
                    current_login = None  # Reset state after valid pairing

        if not raw_sessions:
            summaries.append({
                "user": user,
                "total_active_seconds": 0,
                "merged_sessions": []
            })
            continue

        # 3. Merge overlapping or contiguous (touching) sessions
        merged_sessions = []
        curr_start, curr_end = raw_sessions[0]

        for next_start, next_end in raw_sessions[1:]:
            # If next session overlaps or touches current session
            if next_start <= curr_end:
                curr_end = max(curr_end, next_end)
            else:
                merged_sessions.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        
        merged_sessions.append((curr_start, curr_end))

        # 4. Calculate total active seconds
        total_seconds = sum((end - start).total_seconds() for start, end in merged_sessions)

        summaries.append({
            "user": user,
            "total_active_seconds": int(total_seconds),
            "merged_sessions": [
                {"start": start.isoformat(), "end": end.isoformat()} 
                for start, end in merged_sessions
            ]
        })

    # Output is already sorted by user alphabetically
    return summaries


# Example Usage:
if __name__ == "__main__":
    logs = [
        {"user": "alice", "type": "login", "timestamp": "2026-09-12T08:00:00"},
        {"user": "alice", "type": "login", "timestamp": "2026-09-12T08:15:00"}, # ignored redundant login
        {"user": "alice", "type": "logout", "timestamp": "2026-09-12T09:00:00"},
        {"user": "alice", "type": "login", "timestamp": "2026-09-12T08:30:00"}, # overlapping session start
        {"user": "alice", "type": "logout", "timestamp": "2026-09-12T10:00:00"}, # merges with previous session
        {"user": "bob", "type": "login", "timestamp": "2026-09-12T11:00:00"},
        {"user": "bob", "type": "logout", "timestamp": "2026-09-12T11:45:00"},
    ]

    results = analyze_user_sessions(logs)
    print(results)