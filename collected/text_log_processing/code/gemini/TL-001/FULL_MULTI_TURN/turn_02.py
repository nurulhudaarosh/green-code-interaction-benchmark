from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class LogAnalysisResult:
    error_counts: Counter
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


def analyze_error_log(path: str | Path) -> LogAnalysisResult:
    """Reads a server log file, counts ERROR-level entries per normalized message,

    and skips/counts blank or malformed lines without crashing.
    """
    counts = Counter()
    malformed_count = 0

    log_pattern = re.compile(
        r"(?:\[.*?\]\s*|\S+\s+)*\b(?:ERROR|CRITICAL)\b[:\s\-\]]+(?P<message>.+)$",
        re.IGNORECASE,
    )

    # errors="surrogateescape" or "replace" prevents decoding crashes on corrupted byte sequences
    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        for raw_line in log_file:
            try:
                # Strip null bytes and non-printable control chars from binary dumps
                cleaned_line = raw_line.replace("\x00", "").strip()

                # Safely ignore empty lines without counting them as malformed
                if not cleaned_line:
                    continue

                match = log_pattern.search(cleaned_line)
                if match:
                    raw_msg = match.group("message")
                    if not raw_msg or not raw_msg.strip():
                        # Contains ERROR header but no trailing message body
                        malformed_count += 1
                        continue

                    normalized = normalize_message(raw_msg)
                    counts[normalized] += 1

            except Exception:
                # Catches internal regex failures or encoding/surrogate issues
                malformed_count += 1

    return LogAnalysisResult(error_counts=counts, malformed_lines=malformed_count)