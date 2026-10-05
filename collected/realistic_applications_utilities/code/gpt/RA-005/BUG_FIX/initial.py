from collections import Counter
from datetime import datetime


VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_log_line(line):
    """
    Parse a log line in the format:
    YYYY-MM-DD HH:MM:SS | LEVEL | MESSAGE

    Malformed lines are rejected safely.
    """
    if not isinstance(line, str):
        return None

    line = line.strip()
    if not line:
        return None

    parts = line.split("|")

    # A valid record must contain exactly three fields.
    if len(parts) != 3:
        return None

    timestamp_text = parts[0].strip()
    level = parts[1].strip().upper()
    message = parts[2].strip()

    # Reject missing fields.
    if not timestamp_text or not level or not message:
        return None

    # Validate timestamp.
    try:
        timestamp = datetime.strptime(timestamp_text, TIMESTAMP_FORMAT)
    except (ValueError, TypeError):
        return None

    # Validate log level.
    if level not in VALID_LEVELS:
        return None

    return {
        "timestamp": timestamp,
        "level": level,
        "message": message
    }


def summarize_logs(logs):
    """
    Summarize all valid log records while ignoring malformed lines.
    """
    valid_logs = []
    invalid_count = 0

    if logs is None:
        logs = []

    for line in logs:
        record = parse_log_line(line)

        if record is None:
            invalid_count += 1
            continue

        valid_logs.append(record)

    level_counts = Counter(record["level"] for record in valid_logs)
    message_counts = Counter(record["message"] for record in valid_logs)

    if valid_logs:
        first_timestamp = min(
            record["timestamp"] for record in valid_logs
        )
        last_timestamp = max(
            record["timestamp"] for record in valid_logs
        )
    else:
        first_timestamp = None
        last_timestamp = None

    return {
        "total": len(valid_logs),
        "invalid": invalid_count,
        "by_level": {
            "DEBUG": level_counts.get("DEBUG", 0),
            "INFO": level_counts.get("INFO", 0),
            "WARNING": level_counts.get("WARNING", 0),
            "ERROR": level_counts.get("ERROR", 0),
            "CRITICAL": level_counts.get("CRITICAL", 0)
        },
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "messages": dict(message_counts)
    }


def format_summary(summary):
    """
    Format the log summary as readable text.
    """
    first_timestamp = summary["first_timestamp"]
    last_timestamp = summary["last_timestamp"]

    first_text = (
        first_timestamp.strftime(TIMESTAMP_FORMAT)
        if first_timestamp is not None
        else "N/A"
    )

    last_text = (
        last_timestamp.strftime(TIMESTAMP_FORMAT)
        if last_timestamp is not None
        else "N/A"
    )

    output = [
        "Log Summary",
        "-----------",
        f"Total valid entries: {summary['total']}",
        f"Malformed entries: {summary['invalid']}",
        f"First timestamp: {first_text}",
        f"Last timestamp: {last_text}",
        "",
        "Entries by level:"
    ]

    for level, count in summary["by_level"].items():
        output.append(f"  {level}: {count}")

    output.append("")
    output.append("Message frequencies:")

    if summary["messages"]:
        sorted_messages = sorted(
            summary["messages"].items(),
            key=lambda item: (-item[1], item[0])
        )

        for message, count in sorted_messages:
            output.append(f"  {count}x - {message}")
    else:
        output.append("  N/A")

    return "\n".join(output)


def analyze_logs(logs):
    """
    Complete log summarizer with robust malformed-line handling.
    """
    summary = summarize_logs(logs)
    return format_summary(summary)


if __name__ == "__main__":
    logs = [
        "2026-10-04 09:15:00 | INFO | Application started",
        "2026-10-04 09:16:10 | INFO | User logged in",
        "2026-10-04 09:17:22 | WARNING | Slow response detected",
        "2026-10-04 09:18:30 | ERROR | Database connection failed",
        "malformed line",
        "2026-99-99 10:00:00 | ERROR | Invalid date",
        "2026-10-04 09:19:00 | ERROR | Database connection failed",
        "2026-10-04 09:20:00 | UNKNOWN | Unsupported level",
        "2026-10-04 09:21:00 | CRITICAL | Service unavailable",
        "",
        "   ",
        "2026-10-04 09:22:00 | INFO",
        "2026-10-04 09:23:00 | INFO |"
    ]

    print(analyze_logs(logs))