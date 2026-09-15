import re
from collections import Counter, defaultdict

# --- 1. ANALYZER ---
class LogAnalyzer:
    PATTERN = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
        r"(?P<level>DEBUG|INFO|WARN|ERROR|FATAL)\s+"
        r"(?P<service>\S+)\s+(?P<msg>.+)$"
    )

    def __init__(self, min_amount: int = 1):
        self.min_amount = min_amount          # <-- filter threshold
        self.levels = Counter()
        self.services = Counter()
        self.by_service_level = defaultdict(Counter)
        self.parsed = self.skipped = 0

    def feed(self, line: str) -> None:
        m = self.PATTERN.match(line.strip())
        if not m:
            self.skipped += 1
            return
        lvl, svc = m["level"], m["service"]
        self.levels[lvl] += 1
        self.services[svc] += 1
        self.by_service_level[svc][lvl] += 1
        self.parsed += 1

    # --- 2. MINIMUM-AMOUNT FILTERING (applied at report time) ---
    def report(self) -> dict:
        keep = lambda c: {k: v for k, v in c.most_common() if v >= self.min_amount}
        return {
            "parsed": self.parsed,
            "skipped": self.skipped,
            "min_amount": self.min_amount,
            "levels": keep(self.levels),
            "services": keep(self.services),
            "service_levels": {
                svc: dict(cnt.most_common())
                for svc, cnt in self.by_service_level.items()
                if sum(cnt.values()) >= self.min_amount
            },
        }


def analyze(lines, min_amount=2):
    a = LogAnalyzer(min_amount=min_amount)
    for line in lines:
        a.feed(line)
    return a.report()


if __name__ == "__main__":
    sample = [
        "2024-01-15 10:23:45 ERROR auth-service Failed login user=alice",
        "2024-01-15 10:23:46 ERROR auth-service Failed login user=bob",
        "2024-01-15 10:23:47 WARN  auth-service Slow response 1200ms",
        "2024-01-15 10:23:48 INFO  api-gateway Request routed /v1/users",
        "2024-01-15 10:23:49 ERROR db-service Connection timeout",
        "2024-01-15 10:23:50 ERROR db-service Connection timeout",
        "2024-01-15 10:23:51 ERROR db-service Connection timeout",
        "malformed line -- skipped",
    ]
    import json
    print(json.dumps(analyze(sample, min_amount=2), indent=2))