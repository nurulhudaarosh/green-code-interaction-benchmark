import csv
from datetime import datetime
from collections import defaultdict

def parse_time(ts):
    return datetime.fromisoformat(ts)

def load_events(path):
    """
    Expects a CSV with columns: user, event, timestamp
    event is either 'login' or 'logout'
    timestamp is ISO format, e.g. 2024-01-01T09:00:00
    """
    events = defaultdict(list)
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = row['user'].strip()
            event = row['event'].strip().lower()
            ts = parse_time(row['timestamp'].strip())
            events[user].append((ts, event))
    return events

def pair_sessions(user_events):
    """
    Sort events chronologically, then pair each login with the
    next valid logout that comes after it. Unmatched logins/logouts
    are ignored (orphaned events).
    """
    user_events.sort(key=lambda x: x[0])

    sessions = []
    pending_login = None

    for ts, event in user_events:
        if event == 'login':
            if pending_login is None:
                pending_login = ts
        elif event == 'logout':
            if pending_login is not None:
                sessions.append((pending_login, ts))
                pending_login = None

    return sessions

def merge_sessions(sessions):
    """
    Merge overlapping or touching sessions.
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

def analyze(path):
    events_by_user = load_events(path)
    summaries = {}

    for user, events in events_by_user.items():
        sessions = pair_sessions(events)
        merged = merge_sessions(sessions)
        active_seconds = total_active_seconds(merged)
        summaries[user] = {
            'sessions': merged,
            'merged_interval_count': len(merged),
            'active_seconds': active_seconds,
        }

    return summaries

def print_summaries(summaries):
    for user in sorted(summaries.keys()):
        data = summaries[user]
        print(f"User: {user}")
        print(f"  Merged interval count: {data['merged_interval_count']}")
        print(f"  Total active seconds: {data['active_seconds']:.0f}")
        print(f"  Sessions:")
        for start, end in data['sessions']:
            print(f"    {start.isoformat()} -> {end.isoformat()}")
        print()

def write_summaries(summaries, out_path):
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user', 'merged_interval_count', 'active_seconds', 'sessions'])
        for user in sorted(summaries.keys()):
            data = summaries[user]
            sessions_str = '; '.join(
                f"{s.isoformat()}~{e.isoformat()}" for s, e in data['sessions']
            )
            writer.writerow([
                user,
                data['merged_interval_count'],
                f"{data['active_seconds']:.0f}",
                sessions_str
            ])

if __name__ == '__main__':
    input_path = 'events.csv'
    output_path = 'summary.csv'

    summaries = analyze(input_path)
    print_summaries(summaries)
    write_summaries(summaries, output_path)