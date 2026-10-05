from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class LogAnalysisResult:
    top_errors: list[tuple[str, int]]
    malformed_lines: int


def normalize_message(msg: str) -> str:
    """Replaces dynamic fragments (IDs, IPs, timestamps, numbers) with placeholders."""
    msg = re.sub(r"\b0x[0-9a-fA-F]+\b", "<HEX>", msg)
    msg = re.sub(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        "<UUID>",
        msg,
    )
    msg = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b", "<IP>", msg)
    msg = re.sub(
        r"\b\d{4}[-/]\d{2}[-/]\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?\b",
        "<TIMESTAMP>",
        msg,
    )
    msg = re.sub(r"\b\d+\b", "<NUM>", msg)
    return re.sub(r"\s+", " ", msg).strip()


def analyze_error_log(
    path: str | Path, top_n: int | None = None
) -> LogAnalysisResult:
    """Reads a server log file, counts ERROR-level entries per normalized message,

    and returns the top-N errors sorted by count descending.

    Parameters:
        path: Path to the log file.
        top_n: Number of top error signatures to return. If None, returns all.

    Returns:
        LogAnalysisResult: Contains top_errors as [(message, count), ...]
                           and total count of malformed_lines.
    """
    counts = Counter()
    malformed_count = 0

    log_pattern = re.compile(
        r"(?:\[.*?\]\s*|\S+\s+)*\b(?:ERROR|CRITICAL)\b[:\s\-\]]+(?P<message>.+)$",
        re.IGNORECASE,
    )

    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            try:
                cleaned_line = raw_line.replace("\x00", "").strip()

                if not cleaned_line:
                    continue

                match = log_pattern.search(cleaned_line)
                if match:
                    raw_msg = match.group("message")
                    if not raw_msg or not raw_msg.strip():
                        malformed_count += 1
                        continue

                    normalized = normalize_message(raw_msg)
                    counts[normalized] += 1

            except Exception:
                malformed_count += 1

    # Counter.most_common(n) returns all items sorted descending if n is None
    ranked_errors = counts.most_common(top_n)

    return LogAnalysisResult(
        top_errors=ranked_errors, malformed_lines=malformed_count
    )