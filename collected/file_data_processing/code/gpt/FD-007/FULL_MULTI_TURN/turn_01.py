import csv
from datetime import datetime

INPUT_FILE = "login_logout.csv"
OUTPUT_FILE = "user_summary.csv"

events = {}

with open(INPUT_FILE, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        user = row["user_id"]
        event = row["event"].strip().lower()
        timestamp = datetime.fromisoformat(row["timestamp"])

        if user not in events:
            events[user] = []

        events[user].append((timestamp, event))

summaries = []

for user, user_events in events.items():
    user_events.sort(key=lambda x: x[0])

    sessions = []
    login_time = None

    for timestamp, event in user_events:
        if event == "login":
            if login_time is None:
                login_time = timestamp

        elif event == "logout":
            if login_time is not None and timestamp >= login_time:
                sessions.append((login_time, timestamp))
                login_time = None

    sessions.sort()

    merged = []

    for start, end in sessions:
        if not merged:
            merged.append([start, end])
        else:
            last_start, last_end = merged[-1]

            if start <= last_end:
                if end > last_end:
                    merged[-1][1] = end
            else:
                merged.append([start, end])

    active_seconds = sum(
        (end - start).total_seconds()
        for start, end in merged
    )

    summaries.append({
        "user_id": user,
        "interval_count": len(merged),
        "active_seconds": int(active_seconds)
    })

summaries.sort(key=lambda x: x["user_id"])

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["user_id", "interval_count", "active_seconds"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(summaries)