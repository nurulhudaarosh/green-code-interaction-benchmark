def summarize_logs(logs):
    """
    Summarize log entries by log level.

    Each log entry is expected to contain a level such as:
    INFO, WARNING, ERROR, or DEBUG.
    """

    summary = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "DEBUG": 0
    }

    if not logs:
        return summary

    for log in logs:
        if not isinstance(log, str):
            continue

        log = log.strip()
        if not log:
            continue

        # Assume the log level is the first whitespace-separated field.
        level = log.split()[0].upper()

        if level in summary:
            summary[level] += 1

    return summary


if __name__ == "__main__":
    logs = [
        "INFO Application started",
        "ERROR Database connection failed",
        "WARNING Low memory",
        "INFO User logged in",
        "DEBUG Processing request",
        "ERROR Request failed"
    ]

    print(summarize_logs(logs))