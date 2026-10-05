from collections import Counter


def summarize_logs(logs):
    summary = {
        "total": 0,
        "levels": {},
        "messages": [],
        "repeated_errors": []
    }

    if not isinstance(logs, (list, tuple)):
        return summary

    error_messages = []

    for line in logs:
        if not isinstance(line, str):
            continue

        line = line.strip()
        if not line:
            continue

        line = line.strip(":;| \t")
        if not line:
            continue

        parts = line.split(":", 1)
        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        valid_levels = {"INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"}

        if level not in valid_levels or not message:
            continue

        summary["total"] += 1
        summary["levels"][level] = summary["levels"].get(level, 0) + 1

        summary["messages"].append({
            "level": level,
            "message": message
        })

        if level == "ERROR":
            error_messages.append(message)

    # Detect error messages that occur more than once.
    error_counts = Counter(error_messages)

    summary["repeated_errors"] = [
        {
            "message": message,
            "count": count
        }
        for message, count in error_counts.items()
        if count > 1
    ]

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "WARNING: Low disk space",
        "ERROR: Database connection failed",
        "INFO: User logged in",
        "error: Database connection failed",
        "CRITICAL: Server unavailable",
        "ERROR: Server unavailable"
    ]

    result = summarize_logs(logs)
    print(result)