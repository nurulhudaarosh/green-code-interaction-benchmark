import csv
import re
from typing import Iterable, Optional

# Apache/Nginx Common + Combined Log Format
LOG_RE = re.compile(
    r'^(?P<ip>\S+) (?P<ident>\S+) (?P<user>\S+) '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+)(?: (?P<protocol>[^"]+))?" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)'
    r'(?: "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)")?\s*$'
)

FIELDS = [
    "ip", "ident", "user", "timestamp", "method", "path", "protocol",
    "status", "statusClass", "bytes", "referrer", "user_agent",
]


def status_class(status: int) -> str:
    return f"{status // 100}xx"


def parse_line(line: str) -> Optional[dict]:
    m = LOG_RE.match(line.strip())
    if not m:
        return None
    rec = m.groupdict()
    status = int(rec["status"])
    rec["status"] = status
    rec["statusClass"] = status_class(status)
    rec["bytes"] = 0 if rec["bytes"] == "-" else int(rec["bytes"])
    rec["protocol"] = rec["protocol"] or ""
    rec["referrer"] = rec["referrer"] or ""
    rec["user_agent"] = rec["user_agent"] or ""
    return rec


def logs_to_csv(lines: Iterable[str], out_path: str) -> tuple[int, int]:
    """Parse log lines and write them to CSV. Returns (parsed, skipped)."""
    parsed = skipped = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for line in lines:
            if not line.strip():
                continue
            rec = parse_line(line)
            if rec is None:
                skipped += 1
                continue
            writer.writerow(rec)
            parsed += 1
    return parsed, skipped


if __name__ == "__main__":
    import sys

    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8", errors="replace") as f:
        ok, bad = logs_to_csv(f, dst)
    print(f"parsed={ok} skipped={bad}")