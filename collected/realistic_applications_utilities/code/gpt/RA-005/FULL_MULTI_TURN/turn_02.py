def summarize_logs(logs):
    summary = {
        "total": 0,
        "levels": {},
        "messages": []
    }

    if not isinstance(logs, (list, tuple)):
        return summary

    for line in logs:
        if not isinstance(line, str):
            continue

        line = line.strip()
        if not line:
            continue

        # Remove extra separators/whitespace around the log entry.
        line = line.strip(":;| \t")

        if not line:
            continue

        # Split only on the first separator so the message can contain colons.
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        if not level or not message:
            continue

        # Normalize common log-level formatting.
        valid_levels = {"INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"}

        if level not in valid_levels:
            continue

        summary["total"] += 1
        summary["levels"][level] = summary["levels"].get(level, 0) + 1
        summary["messages"].append({
            "level": level,
            "message": message
        })

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        " error : Database connection failed ",
        "WARNING: Low disk space",
        "INFO: User logged in: session active",
        "",
        "   ",
        "MALFORMED ENTRY",
        "ERROR:",
        ": Missing level",
        None
    ]

    result = summarize_logs(logs)
    print(result)