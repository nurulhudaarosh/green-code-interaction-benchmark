def summarize_logs(logs):
    """
    Summarize log entries by level.

    Each valid log line is expected to contain:
        LEVEL: message

    Example:
        INFO: Server started
        ERROR: Database connection failed
        WARNING: High memory usage

    Returns:
        {
            "INFO": count,
            "WARNING": count,
            "ERROR": count
        }
    """
    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0
    }

    if not logs:
        return summary

    for line in logs:
        if not isinstance(line, str) or not line.strip():
            continue

        parts = line.split(":", 1)
        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()

        if level in summary:
            summary[level] += 1

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        "ERROR: Database connection failed",
        "WARNING: High memory usage",
        "INFO: User logged in",
        "ERROR: Request failed"
    ]

    print(summarize_logs(logs))