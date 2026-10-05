def summarize_logs(logs):
    """
    Robustly summarize log entries by level.

    Expected format:
        LEVEL: message

    Handles:
        - Empty logs
        - Blank lines
        - Non-string entries
        - Extra whitespace
        - Case differences
        - Missing separators
        - Extra separators inside messages
        - Unknown log levels
    """
    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0
    }

    if not logs:
        return summary

    for line in logs:
        if not isinstance(line, str):
            continue

        line = line.strip()
        if not line:
            continue

        # Split only on the first separator so messages can contain ":"
        parts = line.split(":", 1)

        if len(parts) != 2:
            continue

        level = parts[0].strip().upper()
        message = parts[1].strip()

        # Both the level and message must be present
        if not level or not message:
            continue

        if level in summary:
            summary[level] += 1

    return summary


if __name__ == "__main__":
    logs = [
        "INFO: Server started",
        " error : Database connection failed ",
        "WARNING: High memory usage",
        "Info: User logged in",
        "ERROR: Request failed: timeout",
        "",
        "   ",
        "MALFORMED LINE",
        "DEBUG: Debug message",
        None,
        123
    ]

    print(summarize_logs(logs))