from datetime import datetime, timedelta
from collections import defaultdict

def analyze_user_sessions(log_events):
    """
    Analyzes log events per user, ignoring unmatched events and handling
    out-of-order logs. Returns sorted user summaries with total active time.
    """
    user_events = defaultdict(list)
    
    # Standardize timestamps and group by user
    for event in log_events:
        ts = datetime.strptime(event["timestamp"], "%Y-%m-%d %H:%M:%S") if isinstance(event["timestamp"], str) else event["timestamp"]
        user_events[event["user_id"]].append((ts, event["type"]))

    summaries = []

    for user_id, events in user_events.items():
        # 1. Sort events chronologically per user
        events.sort(key=lambda x: x[0])

        # 2. Pair logins with valid logouts (ignore unmatched logouts & unclosed logins)
        raw_sessions = []
        current_login = None

        for ts, event_type in events:
            if event_type == "login":
                # Save previous login timestamp if consecutive logins appear
                current_login = ts
            elif event_type == "logout":
                # Pair with the most recent login, ignore if no matching login exists
                if current_login is not None:
                    raw_sessions.append((current_login, ts))
                    current_login = None

        # 3. Merge overlapping or touching sessions
        merged_sessions = []
        for start, end in raw_sessions:
            if not merged_sessions:
                merged_sessions.append((start, end))
            else:
                last_start, last_end = merged_sessions[-1]
                if start <= last_end:  # Overlapping or touching
                    merged_sessions[-1] = (last_start, max(last_end, end))
                else:
                    merged_sessions.append((start, end))

        # 4. Calculate total active seconds
        total_seconds = sum((end - start).total_seconds() for start, end in merged_sessions)

        summaries.append({
            "user_id": user_id,
            "total_active_seconds": int(total_seconds),
            "total_active_time": str(timedelta(seconds=int(total_seconds))),
            "merged_sessions": merged_sessions
        })

    # Sort user summaries by user_id
    summaries.sort(key=lambda x: x["user_id"])
    return summaries


# Example usage with out-of-order events and unmatched logins/logouts:
if __name__ == "__main__":
    out_of_order_events = [
        {"user_id": "alice", "type": "logout", "timestamp": "2026-09-12 09:30:00"},  # Matched with login below
        {"user_id": "alice", "type": "logout", "timestamp": "2026-09-12 07:00:00"},  # Unmatched logout (ignored)
        {"user_id": "alice", "type": "login",  "timestamp": "2026-09-12 08:00:00"},  # Out of order
        {"user_id": "bob",   "type": "login",  "timestamp": "2026-09-12 10:00:00"},
        {"user_id": "alice", "type": "login",  "timestamp": "2026-09-12 11:00:00"},  # Unmatched login (ignored)
        {"user_id": "bob",   "type": "logout", "timestamp": "2026-09-12 10:30:00"}
    ]

    results = analyze_user_sessions(out_of_order_events)
    for summary in results:
        print(f"User: {summary['user_id']}")
        print(f"  Total Active Seconds: {summary['total_active_seconds']}")
        print(f"  Total Active Time: {summary['total_active_time']}")
        print(f"  Sessions: {summary['merged_sessions']}\n")