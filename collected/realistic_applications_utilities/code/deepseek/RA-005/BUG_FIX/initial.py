"""
log_summarizer.py — Complete log summarizer with hardened malformed-line parsing.

Run:  python log_summarizer.py <logfile> [--json|--compact|--verbose-malformed]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_LEVELS = ("TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL")

# Strict, word-boundary-anchored level pattern.  Also matches common
# bracketed forms: [INFO]  <INFO>  (INFO)  INFO:  INFO -
LEVEL_RE = re.compile(
    r"(?:^|[\s\[\(\<\|:])(" + "|".join(LOG_LEVELS) + r")(?=[\s\]\)\>\|:\-]|$)",
    re.IGNORECASE,
)

TIMESTAMP_PATTERNS: List[Tuple[re.Pattern, List[str]]] = [
    # ISO 8601 with optional fractional seconds and optional Z / ±HH:MM
    (re.compile(
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
        r"(?:\.\d{1,9})?(?:Z|[+-]\d{2}:?\d{2})?)"
    ), ["iso"]),
    # US / EU slash format
    (re.compile(r"(\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2})"), ["slash"]),
    # Syslog
    (re.compile(r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"), ["syslog"]),
    # Apache/Nginx common log: 10/Oct/2000:13:55:36 -0700
    (re.compile(r"(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4})"), ["clf"]),
]

IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
HTTP_STATUS_RE = re.compile(r"\s(\d{3})\s")  # context-required, see below
URL_RE = re.compile(r"\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
# RFC5424-ish bracketed HTTP: [200] or "GET /x HTTP/1.1" 200
HTTP_STATUS_CTX_RE = re.compile(
    r'(?:(?:HTTP/\d\.\d"|\bstatus[=:]\s*|\[)(\d{3})(?:\]|\b|\s))',
    re.IGNORECASE,
)

# Bounded counter caps (prevents OOM on huge logs)
MAX_UNIQUE = 5_000
MAX_SAMPLES = 20


def _bump(counter: Counter, key: str, cap: int = MAX_UNIQUE) -> None:
    """Increment `counter[key]` but bound the number of unique keys."""
    if key in counter or len(counter) < cap:
        counter[key] += 1
    else:
        counter["<other>"] += 1


# ---------------------------------------------------------------------------
# Structured result per parsed line
# ---------------------------------------------------------------------------

@dataclass
class ParsedLine:
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    ips: List[str] = field(default_factory=list)
    status: Optional[str] = None
    url: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    confidence: float = 0.0        # 0.0 .. 1.0

    @property
    def is_well_formed(self) -> bool:
        # A line is "well-formed" if it has a timestamp OR a level AND at
        # least one piece of structural content.  This is the key fix.
        has_anchor = self.timestamp is not None or self.level is not None
        has_content = bool(
            self.ips or self.status or self.url or self.emails
            or (self.timestamp and self.level)
        )
        return has_anchor and has_content and self.confidence >= 0.5


# ---------------------------------------------------------------------------
# Summarizer
# ---------------------------------------------------------------------------

class LogSummarizer:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.total_lines = 0
        self.blank_lines = 0
        self.well_formed = 0
        self.partial = 0
        self.malformed = 0

        self.level_counts: Counter = Counter()
        self.hourly: Counter = Counter()
        self.ip_addresses: Counter = Counter()
        self.status_codes: Counter = Counter()
        self.urls: Counter = Counter()
        self.emails: Counter = Counter()
        self.error_messages: Counter = Counter()
        self.malformed_reasons: Counter = Counter()

        self.first_ts: Optional[datetime] = None
        self.last_ts: Optional[datetime] = None

        self.malformed_samples: List[str] = []
        self.file_size = 0

    # ---------------- timestamp parsing ----------------

    @staticmethod
    def _parse_iso(ts: str) -> Optional[datetime]:
        """Parse ISO8601 with fractional seconds, Z, and ±HH:MM offsets."""
        s = ts.strip()
        # Normalize 'T'/' ' separator already accepted by fromisoformat on 3.11+,
        # but be safe for older versions.
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        # Insert colon in +HHMM / -HHMM if missing
        if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
            s = s[:-2] + ":" + s[-2:]
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def parse_timestamp(self, line: str) -> Optional[datetime]:
        for pat, kinds in TIMESTAMP_PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            raw = m.group(1)
            for kind in kinds:
                if kind == "iso":
                    dt = self._parse_iso(raw)
                    if dt:
                        return dt
                else:
                    for fmt in (
                        "%m/%d/%Y %H:%M:%S",
                        "%m/%d/%YT%H:%M:%S",
                        "%b %d %H:%M:%S",
                        "%d/%b/%Y:%H:%M:%S %z",
                    ):
                        try:
                            dt = datetime.strptime(raw, fmt)
                            if dt.tzinfo is not None:
                                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                            # syslog has no year: assume current year
                            if kind == "syslog":
                                dt = dt.replace(year=datetime.now().year)
                            return dt
                        except ValueError:
                            continue
        return None

    # ---------------- level parsing ----------------

    def parse_level(self, line: str) -> Optional[str]:
        m = LEVEL_RE.search(line)
        if not m:
            return None
        lvl = m.group(1).upper()
        if lvl == "WARN":
            lvl = "WARNING"
        return lvl

    # ---------------- main line parser ----------------

    def parse_line(self, line: str) -> ParsedLine:
        """Parse a single line into a ParsedLine with a confidence score."""
        pl = ParsedLine()
        score = 0.0

        ts = self.parse_timestamp(line)
        if ts:
            pl.timestamp = ts
            score += 0.4

        lvl = self.parse_level(line)
        if lvl:
            pl.level = lvl
            score += 0.3

        ips = IP_RE.findall(line)
        if ips:
            pl.ips = [ip for ip in ips if self._valid_ip(ip)]
            if pl.ips:
                score += 0.15

        # Status code: only accept when there's surrounding HTTP context.
        m = HTTP_STATUS_CTX_RE.search(line)
        if m and m.group(1).startswith(("1", "2", "3", "4", "5")):
            pl.status = m.group(1)
            score += 0.1
        else:
            # Fallback: status code adjacent to HTTP version
            m2 = re.search(r"HTTP/\d\.\d\"?\s+(\d{3})", line)
            if m2:
                pl.status = m2.group(1)
                score += 0.1

        m = URL_RE.search(line)
        if m:
            pl.url = m.group(1)
            score += 0.1

        emails = EMAIL_RE.findall(line)
        if emails:
            pl.emails = emails
            score += 0.05

        pl.confidence = min(score, 1.0)
        return pl

    @staticmethod
    def _valid_ip(ip: str) -> bool:
        parts = ip.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    # ---------------- line ingestion ----------------

    def process_line(self, raw: str) -> None:
        self.total_lines += 1
        line = raw.rstrip("\n")

        if not line.strip():
            self.blank_lines += 1
            return

        parsed = self.parse_line(line)

        # Update stats only for values that were actually found.
        if parsed.timestamp:
            if self.first_ts is None or parsed.timestamp < self.first_ts:
                self.first_ts = parsed.timestamp
            if self.last_ts is None or parsed.timestamp > self.last_ts:
                self.last_ts = parsed.timestamp
            self.hourly[parsed.timestamp.hour] += 1

        if parsed.level:
            self.level_counts[parsed.level] += 1
            if parsed.level in ("ERROR", "CRITICAL", "FATAL"):
                self._record_error_message(line, parsed.level)

        for ip in parsed.ips:
            _bump(self.ip_addresses, ip)
        if parsed.status:
            _bump(self.status_codes, parsed.status)
        if parsed.url:
            _bump(self.urls, parsed.url[:200])
        for e in parsed.emails:
            _bump(self.emails, e)

        # Categorize
        if parsed.is_well_formed:
            self.well_formed += 1
        elif parsed.confidence >= 0.2:
            self.partial += 1
            self._record_malformed(line, reason="partial-parse")
        else:
            self.malformed += 1
            self._record_malformed(line, reason=self._diagnose(line, parsed))

    def _record_error_message(self, line: str, level: str) -> None:
        # Extract text after the level token; strip numeric noise.
        m = re.search(r"\b" + level + r"\b[:\-\s]*(.*)", line, re.IGNORECASE)
        if not m:
            return
        msg = m.group(1).strip()
        if not msg:
            return
        # Normalize: replace numbers, hex, quoted strings
        msg = re.sub(r"0x[0-9a-fA-F]+", "HEX", msg)
        msg = re.sub(r"\b\d+\b", "N", msg)
        msg = re.sub(r"\"[^\"]*\"", '"..."', msg)
        _bump(self.error_messages, msg[:140])

    def _record_malformed(self, line: str, reason: str) -> None:
        self.malformed_reasons[reason] += 1
        if len(self.malformed_samples) < MAX_SAMPLES:
            self.malformed_samples.append(
                f"[{reason}] {line[:180]}"
            )

    def _diagnose(self, line: str, parsed: ParsedLine) -> str:
        """Produce a short reason label for malformed lines."""
        if not line.strip():
            return "blank"
        # Garbage heuristics
        nonprint = sum(1 for c in line if ord(c) < 32 and c not in "\t")
        if nonprint > 0:
            return "binary-control-chars"
        if len(line) > 4000:
            return "line-too-long"
        if "\ufffd" in line:
            return "decode-error"
        if not re.search(r"[A-Za-z]", line):
            return "no-alpha"
        if parsed.confidence == 0.0:
            return "no-recognized-fields"
        return "unclassified"

    # ---------------- I/O ----------------

    def process_file(self, path: str) -> None:
        try:
            self.file_size = os.path.getsize(path)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    self.process_line(line)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"error: cannot read {path}: {e}", file=sys.stderr)
            sys.exit(1)

    def process_stdin(self) -> None:
        for line in sys.stdin:
            self.process_line(line)

    # ---------------- reporting ----------------

    def format_duration(self) -> str:
        if not (self.first_ts and self.last_ts):
            return "unknown"
        secs = int((self.last_ts - self.first_ts).total_seconds())
        d, secs = divmod(secs, 86400)
        h, secs = divmod(secs, 3600)
        m, s = divmod(secs, 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s or not parts: parts.append(f"{s}s")
        return " ".join(parts)

    @staticmethod
    def format_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024.0:
                return f"{n:.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f} PB"

    def generate_summary(self) -> str:
        out: List[str] = []
        W = 72
        out.append("=" * W)
        out.append("LOG SUMMARY REPORT".center(W))
        out.append("=" * W)

        out.append("\nBASIC STATISTICS")
        out.append("-" * 40)
        out.append(f"  Total lines:        {self.total_lines:>12,}")
        out.append(f"  Blank lines:        {self.blank_lines:>12,}")
        out.append(f"  Well-formed:        {self.well_formed:>12,}"
                   f"  ({self._pct(self.well_formed)})")
        out.append(f"  Partial:            {self.partial:>12,}"
                   f"  ({self._pct(self.partial)})")
        out.append(f"  Malformed:          {self.malformed:>12,}"
                   f"  ({self._pct(self.malformed)})")
        if self.file_size:
            out.append(f"  File size:          {self.format_bytes(self.file_size):>12}")

        if self.first_ts and self.last_ts:
            out.append("\nTIME RANGE")
            out.append("-" * 40)
            out.append(f"  First:  {self.first_ts}")
            out.append(f"  Last:   {self.last_ts}")
            out.append(f"  Span:   {self.format_duration()}")

        if self.level_counts:
            out.append("\nLOG LEVELS")
            out.append("-" * 40)
            total = sum(self.level_counts.values())
            for lvl, cnt in sorted(self.level_counts.items()):
                pct = cnt / total * 100
                bar = "#" * int(pct / 2)
                out.append(f"  {lvl:<10} {cnt:>10,} ({pct:>5.1f}%) {bar}")

        if self.hourly:
            out.append("\nHOURLY DISTRIBUTION")
            out.append("-" * 40)
            peak = max(self.hourly.values())
            for h in range(24):
                c = self.hourly.get(h, 0)
                if c:
                    bar = "@" * int(c / peak * 40)
                    out.append(f"  {h:02d}:00 {c:>10,}  {bar}")

        if self.status_codes:
            out.append("\nHTTP STATUS CODES")
            out.append("-" * 40)
            for s, c in self.status_codes.most_common(10):
                out.append(f"  {s}: {c:,}")

        if self.ip_addresses:
            out.append("\nTOP IP ADDRESSES")
            out.append("-" * 40)
            for ip, c in self.ip_addresses.most_common(10):
                out.append(f"  {ip:<20} {c:>10,}")

        if self.urls:
            out.append("\nTOP URLS")
            out.append("-" * 40)
            for u, c in self.urls.most_common(10):
                out.append(f"  [{c:>7,}] {u[:60]}")

        if self.error_messages:
            out.append("\nTOP ERROR MESSAGES")
            out.append("-" * 40)
            for msg, c in self.error_messages.most_common(10):
                out.append(f"  [{c:>7,}] {msg}")

        if self.malformed_reasons:
            out.append("\nMALFORMED-LINE REASONS")
            out.append("-" * 40)
            for r, c in self.malformed_reasons.most_common():
                out.append(f"  {r:<25} {c:>10,}")

        if self.malformed_samples:
            out.append("\nMALFORMED SAMPLES")
            out.append("-" * 40)
            for s in self.malformed_samples[:8]:
                out.append(f"  {s}")

        out.append("=" * W)
        return "\n".join(out)

    def _pct(self, n: int) -> str:
        denom = max(self.total_lines - self.blank_lines, 1)
        return f"{n / denom * 100:5.1f}%"

    def to_dict(self) -> Dict:
        return {
            "total_lines": self.total_lines,
            "blank_lines": self.blank_lines,
            "well_formed": self.well_formed,
            "partial": self.partial,
            "malformed": self.malformed,
            "file_size": self.file_size,
            "time_range": {
                "first": self.first_ts.isoformat() if self.first_ts else None,
                "last": self.last_ts.isoformat() if self.last_ts else None,
                "span_seconds": (
                    (self.last_ts - self.first_ts).total_seconds()
                    if self.first_ts and self.last_ts else None
                ),
            },
            "levels": dict(self.level_counts),
            "hourly": dict(self.hourly),
            "status_codes": dict(self.status_codes),
            "top_ips": self.ip_addresses.most_common(10),
            "top_urls": self.urls.most_common(10),
            "top_errors": self.error_messages.most_common(10),
            "malformed_reasons": dict(self.malformed_reasons),
            "malformed_samples": self.malformed_samples,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="log_summarizer",
        description="Summarize log files with hardened malformed-line detection.",
    )
    p.add_argument("input", nargs="?", default="-",
                   help="Log file path, or '-' for stdin (default)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--compact", action="store_true", help="Compact JSON (no indent)")
    p.add_argument("-o", "--output", help="Write report to this file")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress stdout")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_argparser().parse_args(argv)

    s = LogSummarizer()
    if args.input == "-":
        s.process_stdin()
    else:
        s.process_file(args.input)

    if args.json:
        report = s.to_json(indent=None if args.compact else 2)
    else:
        report = s.generate_summary()

    if not args.quiet:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"report written to {args.output}", file=sys.stderr)
        else:
            print(report)

    # exit codes: 0 ok, 1 file error (handled in process_file), 2 no content parsed
    if s.total_lines > 0 and s.well_formed == 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())