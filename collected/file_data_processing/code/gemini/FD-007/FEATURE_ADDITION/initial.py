from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Any

def analyze_user_sessions(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes raw log events to compute total active time per user.
    
    Processing steps:
    1. Parse timestamps and group by user.
    2. Sort events chronologically.
    3. Pair logins with the next valid logout (ignoring missing pairs).
    4. Merge overlapping or contiguous session intervals.
    5. Calculate total active seconds per user.
    6. Return user summaries sorted alphabetically by user ID.
    """
    user_events = defaultdict(list)
    
    # Parse timestamps and group events by user
    for event in events:
        ts = datetime.fromisoformat(event["timestamp"])
        user_events[event["user_id"]].append((ts, event["action"]))
    
    summary_results = []
    
    # Process each user deterministically sorted by user_id
    for user_id in sorted(user_events.keys()):
        raw_events = user_events[user_id]
        # Sort chronologically by timestamp
        raw_events.sort(key=lambda x: x[0])
        
        # Step 1: Pair logins with the immediate next logout
        paired_sessions: List[Tuple[datetime, datetime]] = []
        pending_login = None
        
        for ts, action in raw_events:
            if action == "login":
                # If a login occurs while another is pending, update to latest login
                pending_login = ts
            elif action == "logout":
                if pending_login is not None:
                    # Valid pair found
                    paired_sessions.append((pending_login, ts))
                    pending_login = None
                # Ignore orphan logouts
        
        if not paired_sessions:
            summary_results.append({
                "user_id": user_id,
                "total_active_seconds": 0,
                "session_count": 0
            })
            continue

        # Step 2: Merge overlapping or touching intervals
        # Intervals are already sorted by start time because raw_events were sorted
        merged_sessions = [paired_sessions[0]]
        
        for current_start, current_end in paired_sessions[1:]:
            last_start, last_end = merged_sessions[-1]
            
            # Check for overlap or touch (current start <= last end)
            if current_start <= last_end:
                new_end = max(last_end, current_end)
                merged_sessions[-1] = (last_start, new_end)
            else:
                merged_sessions.append((current_start, current_end))
        
        # Step 3: Calculate total active seconds
        total_seconds = sum(
            int((end - start).total_seconds()) 
            for start, end in merged_sessions
        )
        
        summary_results.append({
            "user_id": user_id,
            "total_active_seconds": total_seconds,
            "session_count": len(merged_sessions)
        })
        
    return summary_results


# Example Usage & Verification
if __name__ == "__main__":
    sample_logs = [
        # User A: Overlapping sessions (10:00-10:30 and 10:15-10:45) -> Merged to 10:00-10:45 (2700s)
        {"user_id": "alice", "action": "login", "timestamp": "2026-09-12T10:00:00"},
        {"user_id": "alice", "action": "login", "timestamp": "2026-09-12T10:15:00"},
        {"user_id": "alice", "action": "logout", "timestamp": "2026-09-12T10:30:00"},
        {"user_id": "alice", "action": "logout", "timestamp": "2026-09-12T10:45:00"},
        
        # User B: Unmatched actions + separate valid session (12:00-12:10 -> 600s)
        {"user_id": "bob", "action": "logout", "timestamp": "2026-09-12T11:00:00"}, # Ignored orphan
        {"user_id": "bob", "action": "login", "timestamp": "2026-09-12T12:00:00"},
        {"user_id": "bob", "action": "logout", "timestamp": "2026-09-12T12:10:00"},
    ]

    results = analyze_user_sessions(sample_logs)
    print(results)