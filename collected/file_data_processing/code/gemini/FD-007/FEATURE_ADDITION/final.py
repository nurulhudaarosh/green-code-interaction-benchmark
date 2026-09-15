from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Any

def analyze_user_sessions_detailed(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses login/logout logs, merges overlapping intervals, and reports 
    both the merged interval count and total active seconds per user.
    """
    user_events = defaultdict(list)
    
    # 1. Parse timestamps and group by user
    for event in events:
        ts = datetime.fromisoformat(event["timestamp"])
        user_events[event["user_id"]].append((ts, event["action"]))
    
    summary_results = []
    
    # 2. Process sorted users alphabetically
    for user_id in sorted(user_events.keys()):
        raw_events = sorted(user_events[user_id], key=lambda x: x[0])
        
        # 3. Pair logins with valid logouts
        paired_sessions: List[Tuple[datetime, datetime]] = []
        pending_login = None
        
        for ts, action in raw_events:
            if action == "login":
                pending_login = ts
            elif action == "logout":
                if pending_login is not None:
                    paired_sessions.append((pending_login, ts))
                    pending_login = None

        if not paired_sessions:
            summary_results.append({
                "user_id": user_id,
                "merged_interval_count": 0,
                "total_active_seconds": 0
            })
            continue

        # 4. Merge overlapping or touching intervals
        merged_sessions = [paired_sessions[0]]
        
        for current_start, current_end in paired_sessions[1:]:
            last_start, last_end = merged_sessions[-1]
            
            if current_start <= last_end:
                merged_sessions[-1] = (last_start, max(last_end, current_end))
            else:
                merged_sessions.append((current_start, current_end))
        
        # 5. Calculate total active seconds across merged intervals
        total_seconds = sum(
            int((end - start).total_seconds()) 
            for start, end in merged_sessions
        )
        
        summary_results.append({
            "user_id": user_id,
            "merged_interval_count": len(merged_sessions),
            "total_active_seconds": total_seconds
        })
        
    return summary_results


# Example Usage & Verification
if __name__ == "__main__":
    sample_logs = [
        # Alice: 2 overlapping logins -> merged into 1 interval (10:00-10:45 = 2700s)
        {"user_id": "alice", "action": "login", "timestamp": "2026-09-12T10:00:00"},
        {"user_id": "alice", "action": "login", "timestamp": "2026-09-12T10:15:00"},
        {"user_id": "alice", "action": "logout", "timestamp": "2026-09-12T10:30:00"},
        {"user_id": "alice", "action": "logout", "timestamp": "2026-09-12T10:45:00"},
        
        # Bob: 2 distinct non-overlapping sessions -> 2 intervals (300s + 600s = 900s)
        {"user_id": "bob", "action": "login", "timestamp": "2026-09-12T08:00:00"},
        {"user_id": "bob", "action": "logout", "timestamp": "2026-09-12T08:05:00"},
        {"user_id": "bob", "action": "login", "timestamp": "2026-09-12T12:00:00"},
        {"user_id": "bob", "action": "logout", "timestamp": "2026-09-12T12:10:00"},
    ]

    for summary in analyze_user_sessions_detailed(sample_logs):
        print(f"User: {summary['user_id']} | Merged Intervals: {summary['merged_interval_count']} | Total Active Seconds: {summary['total_active_seconds']}")