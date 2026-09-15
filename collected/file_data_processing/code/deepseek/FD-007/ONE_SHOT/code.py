from datetime import datetime, timedelta
from collections import defaultdict
import re


def parse_timestamp(ts):
    """Parse various common timestamp formats."""
    ts = ts.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {ts}")


def parse_line(line):
    """Parse a log line into (timestamp, username, event)."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Expected: <timestamp> <username> <login|logout>
    # Timestamp may contain a space, so match event at the end.
    m = re.match(
        r"^(?P<ts>.+?)\s+(?P<user>\S+)\s+(?P<event>login|logout)\s*$",
        line,
        re.IGNORECASE,
    )
    if not m:
        return None
    return (
        parse_timestamp(m.group("ts")),
        m.group("user"),
        m.group("event").lower(),
    )


def merge_sessions(sessions):
    """Merge overlapping or touching [start, end] intervals."""
    if not sessions:
        return []
    sessions = sorted(sessions, key=lambda s: s[0])
    merged = [list(sessions[0])]
    for start, end in sessions[1:]:
        last = merged[-1]
        if start <= last[1]:  # overlap or touch (inclusive)
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])
    return [tuple(s) for s in merged]


def analyze(events):
    """
    events: iterable of (timestamp, username, event)
    Returns: dict username -> {sessions, total_seconds, logins, logouts, unmatched_logouts}
    """
    per_user = defaultdict(list)
    for ts, user, event in events:
        per_user[user].append((ts, event))

    results = {}
    for user, evs in per_user.items():
        evs.sort(key=lambda e: e[0])

        raw_sessions = []
        open_login = None
        logins = 0
        logouts = 0
        unmatched_logouts = 0

        for ts, event in evs:
            if event == "login":
                logins += 1
                if open_login is None:
                    open_login = ts
                else:
                    # Two logins in a row -> treat as session start refresh
                    # (or ignore). We extend/restart from earliest? Keep earliest.
                    pass
            elif event == "logout":
                logouts += 1
                if open_login is not None:
                    if ts >= open_login:
                        raw_sessions.append((open_login, ts))
                        open_login = None
                    else:
                        # Logout before login -> ignore
                        unmatched_logouts += 1
                else:
                    unmatched_logouts += 1

        merged = merge_sessions(raw_sessions)
        total_seconds = sum(int((e - s).total_seconds()) for s, e in merged)

        results[user] = {
            "sessions": merged,
            "total_seconds": total_seconds,
            "logins": logins,
            "logouts": logouts,
            "unmatched_logouts": unmatched_logouts,
        }

    return results


def format_duration(seconds):
    td = timedelta(seconds=seconds)
    total = int(td.total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def write_summary(results, output_path):
    with open(output_path, "w") as f:
        for user in sorted(results.keys()):
            data = results[user]
            f.write(f"User: {user}\n")
            f.write(f"  Logins: {data['logins']}\n")
            f.write(f"  Logouts: {data['logouts']}\n")
            f.write(f"  Unmatched logouts: {data['unmatched_logouts']}\n")
            f.write(f"  Sessions: {len(data['sessions'])}\n")
            f.write(f"  Active seconds: {data['total_seconds']} "
                    f"({format_duration(data['total_seconds'])})\n")
            for start, end in data["sessions"]:
                secs = int((end - start).total_seconds())
                f.write(f"    {start} -> {end}  ({secs}s)\n")
            f.write("\n")


def analyze_file(input_path, output_path="user_summaries.txt"):
    events = []
    with open(input_path, "r") as f:
        for lineno, line in enumerate(f, 1):
            parsed = parse_line(line)
            if parsed:
                events.append(parsed)
            elif line.strip() and not line.strip().startswith("#"):
                print(f"[warn] skipping malformed line {lineno}: {line.rstrip()}")

    results = analyze(events)
    write_summary(results, output_path)
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <logfile> [outputfile]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "user_summaries.txt"

    results = analyze_file(in_path, out_path)
    print(f"Analyzed {len(results)} user(s). Summary written to {out_path}")