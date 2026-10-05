import csv
import re
from datetime import datetime
from typing import Iterable, NamedTuple, Optional

# Apache/Nginx "combined" format; referrer and user agent are optional (common format also works).
LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<ts>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+)(?: (?P<proto>[^"]*))?" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-)'
    r'(?: "(?P<referrer>[^"]*)" "(?P<agent>[^"]*)")?'
)

FIELDS = ["ip", "user", "timestamp", "method", "path", "protocol",
          "status", "bytes", "referrer", "user_agent"]


class Counts(NamedTuple):
    written: int
    skipped: int      # everything not written (malformed + filtered out)
    malformed: int    # subset of skipped that could not be parsed


def convert_access_log(
    src_path: str,
    dst_path: str,
    methods: Optional[Iterable[str]] = None,
    status_classes: Optional[Iterable[int]] = None,
) -> Counts:
    """Parse an access log, keep rows matching methods / status classes, write CSV.

    methods:        e.g. ["GET", "POST"]; None keeps all.
    status_classes: e.g. [4, 5] for 4xx and 5xx; None keeps all.
    Returns Counts(written, skipped, malformed) and prints a summary.
    """
    method_set = {m.upper() for m in methods} if methods else None
    class_set = {int(c) for c in status_classes} if status_classes else None

    written = skipped = malformed = 0

    with open(src_path, encoding="utf-8", errors="replace") as src, \
         open(dst_path, "w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=FIELDS)
        writer.writeheader()

        for line in src:
            line = line.strip()
            if not line:
                continue

            m = LOG_RE.match(line)
            if not m:
                skipped += 1
                malformed += 1
                continue

            try:
                ts = datetime.strptime(m["ts"], "%d/%b/%Y:%H:%M:%S %z").isoformat()
            except ValueError:
                skipped += 1
                malformed += 1
                continue

            status = int(m["status"])
            if method_set and m["method"] not in method_set:
                skipped += 1
                continue
            if class_set and status // 100 not in class_set:
                skipped += 1
                continue

            writer.writerow({
                "ip": m["ip"],
                "user": m["user"],
                "timestamp": ts,
                "method": m["method"],
                "path": m["path"],
                "protocol": m["proto"] or "",
                "status": status,
                "bytes": 0 if m["bytes"] == "-" else int(m["bytes"]),
                "referrer": m["referrer"] or "",
                "user_agent": m["agent"] or "",
            })
            written += 1

    print(f"Written: {written} | Skipped: {skipped} (malformed: {malformed})")
    return Counts(written, skipped, malformed)


if __name__ == "__main__":
    convert_access_log("access.log", "access.csv",
                       methods=["GET", "POST"], status_classes=[4, 5])