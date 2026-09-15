import csv
from datetime import datetime
from collections import defaultdict

INPUT_FILE = "input.csv"
OUTPUT_FILE = "output.csv"

def parse_time(value):
    return datetime.fromisoformat(value.strip())

events = defaultdict(list)

with open(INPUT_FILE, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        user = row["user"].strip()
        event = row["event"].strip().lower()
        timestamp = parse_time(row["timestamp"])

        if event in ("login", "logout"):
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
        elif event == "logout" and login_time is not None:
            if timestamp >= login_time:
                sessions.append((login_time, timestamp))
                login_time = None

    if not sessions:
        active_seconds = 0
    else:
        merged = []

        for start, end in sessions:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                if end > merged[-1][1]:
                    merged[-1][1] = end

        active_seconds = sum(
            int((end - start).total_seconds())
            for start, end in merged
        )

    summaries.append({
        "user": user,
        "sessions": len(sessions),
        "active_seconds": active_seconds
    })

summaries.sort(key=lambda x: x["user"])

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["user", "sessions", "active_seconds"]
    )
    writer.writeheader()
    writer.writerows(summaries)