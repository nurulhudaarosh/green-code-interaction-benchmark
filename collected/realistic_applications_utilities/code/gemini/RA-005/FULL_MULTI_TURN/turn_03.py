def summarize_logs(logs):
    """
    Summarize log entries and detect repeated errors.

    Expected format:
        LEVEL: message

    Returns:
        {
            "INFO": count,
            "WARNING": count,
            "ERROR": count,
            "DEBUG": count,
            "repeated_errors": [...]
        }
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "DEBUG": 0,
        "repeated_errors": []
    }

    if not logs:
        return summary

    error_messages = {}

    for log in logs:
        if not isinstance(log, str):
            continue

        log = log.strip()
        if not log:
            continue

        parts = log.split(":", 1)

        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        if not level or not message:
            continue

        if level not in ("INFO", "WARNING", "ERROR", "DEBUG"):
            continue

        summary[level] += 1

        if level == "ERROR":
            error_messages[message] = error_messages.get(message, 0) + 1

    # An error is considered repeated when it occurs more than once.
    summary["repeated_errors"] = [
        message
        for message, count in error_messages.items()
        if count > 1
    ]

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Application started",
        "ERROR: Database connection failed",
        "WARNING: Low memory",
        "ERROR: Database connection failed",
        "DEBUG: Processing request",
        "ERROR: Request timeout",
        "ERROR: Database connection failed",
        "INFO: User logged in",
        "MALFORMED LOG"
    ]

    print(summarize_logs(logs))