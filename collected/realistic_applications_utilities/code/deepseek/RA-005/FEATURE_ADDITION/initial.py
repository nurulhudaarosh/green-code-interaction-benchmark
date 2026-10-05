#!/usr/bin/env python3
"""log_summarizer.py — log summarizer with malformed-line and repeated-error detection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple


# --- patterns ---
_LEVEL_ALT = r"TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL"
LEVEL_RE = re.compile(
    r"(?:^|[\s\[\(\<\|,;:])(" + _LEVEL_ALT + r")(?=[\s\]\)\>\|,;:.\-]|$)",
    re.IGNORECASE,
)
ISO_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,9})?(?:Z|[+-]\d{2}:?\d{2})?)"
)
SLASH_RE = re.compile(r"(\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2})")
SYSLOG_RE = re.compile(r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")
CLF_RE = re.compile(r"(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4})")
IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
URL_RE = re.compile(r"\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)")
HTTP_STATUS_CTX_RE = re.compile(
    r'(?:HTTP/\d\.\d"|\bstatus[=:]\s*|\s\[)(\d{3})(?:\]|\s|"|$)', re.IGNORECASE
)

MAX_LINE_LEN = 4000
MAX_UNIQUE_KEYS = 5000
MAX_SAMPLES = 20


def _bump(counter: Counter, key: str) -> None:
    if key in counter or len(counter) < MAX_UNIQUE_KEYS:
        counter[key] += 1
    else:
        counter["<other>"] += 1


def _valid_ip(ip: str) -> bool:
    try:
        return all(0 <= int(p) <= 255 for p in ip.split("."))
    except ValueError:
        return False


@dataclass
class ParsedLine:
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    ips: List[str] = field(default_factory=list)
    status: Optional[str] = None
    url: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    confidence: float = 0.0
    message: str = ""
    fingerprint: str = ""


class ErrorGroup:
    """Per-fingerprint aggregator (count, streak, sliding-window rate)."""

    __slots__ = (
        "fingerprint", "level", "template", "sample_line",
        "count", "first_seen", "last_seen",
        "streak", "cur_streak", "last_ts",
        "peak_rate", "_window", "streak_gap", "rate_window",
    )

    def __init__(self, fingerprint, level, template, first_seen,
                 streak_gap, rate_window):
        self.fingerprint = fingerprint
        self.level = level
        self.template = template
        self.sample_line = ""
        self.count = 0
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.streak = 0
        self.cur_streak = 0
        self.last_ts: Optional[datetime] = None
        self.peak_rate = 0
        self._window: deque = deque()
        self.streak_gap = streak_gap
        self.rate_window = rate_window

    def add(self, ts: Optional[datetime], raw_line: str) -> None:
        self.count += 1
        if not self.sample_line:
            self.sample_line = raw_line.strip()
        if ts is None:
            return

        self.last_seen = ts
        if self.last_ts is not None and (ts - self.last_ts) <= self.streak_gap:
            self.cur_streak += 1
        else:
            self.cur_streak = 1
        if self.cur_streak > self.streak:
            self.streak = self.cur_streak

        self._window.append(ts)
        cutoff = ts - self.rate_window
        while self._window and self._window[0] < cutoff:
            self._window.popleft()
        if len(self._window) > self.peak_rate:
            self.peak_rate = len(self._window)

        self.last_ts = ts


class LogSummarizer:
    REPEAT_MIN_TOTAL = 3
    REPEAT_STREAK_THRESHOLD = 5
    REPEAT_RATE_THRESHOLD = 5
    RATE_WINDOW = timedelta(seconds=60)
    STREAK_GAP = timedelta(seconds=10)
    MAX_FINGERPRINTS = 5000

    _FP_SUBS: Tuple[Tuple[re.Pattern, str], ...] = (
        (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"), "<TS>"),
        (re.compile(r"\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2}"), "<TS>"),
        (re.compile(r"\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4}"), "<TS>"),
        (re.compile(r"[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"), "<TS>"),
        (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<UUID>"),
        (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"), "<IP>"),
        (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
        (re.compile(r"\b[0-9a-fA-F]{8,}\b"), "<HEX>"),
        (re.compile(r'"[^"]*"'), '"<S>"'),
        (re.compile(r"'[^']*'"), "'<S>'"),
        (re.compile(r"(/[\w\-]+/)\d+"), r"\1<N>"),
        (re.compile(r"\b\d+\b"), "<N>"),
        (re.compile(r"\s+"), " "),
    )

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
        self.error_groups: "OrderedDict[str, ErrorGroup]" = OrderedDict()

    @staticmethod
    def _parse_iso(raw: str) -> Optional[datetime]:
        s = raw.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
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
        m = ISO_RE.search(line)
        if m:
            dt = self._parse_iso(m.group(1))
            if dt:
                return dt
        m = SLASH_RE.search(line)
        if m:
            for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%YT%H:%M:%S"):
                try:
                    return datetime.strptime(m.group(1), fmt)
                except ValueError:
                    continue
        m = CLF_RE.search(line)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%d/%b/%Y:%H:%M:%S %z")
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError:
                pass
        m = SYSLOG_RE.search(line)
        if m:
            for fmt in ("%b %d %H:%M:%S", "%b  %d %H:%M:%S"):
                try:
                    dt = datetime.strptime(m.group(1), fmt)
                    return dt.replace(year=datetime.now().year)
                except ValueError:
                    continue
        return None

    def parse_level(self, line: str) -> Optional[str]:
        m = LEVEL_RE.search(line)
        if not m:
            return None
        lvl = m.group(1).upper()
        return "WARNING" if lvl == "WARN" else lvl

    def _extract_message(self, line: str, level: str) -> str:
        m = re.search(
            r"(?:^|[\s\[\(\<\|,;:])" + re.escape(level)
            + r"(?:ING)?(?=[\s\]\)\>\|,;:.\-]|$)[:\-\s]*(.*)",
            line, re.IGNORECASE,
        )
        return m.group(1).strip() if m else ""

    def parse_line(self, line: str) -> ParsedLine:
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
            pl.message = self._extract_message(line, lvl)

        ips = [ip for ip in IP_RE.findall(line) if _valid_ip(ip)]
        if ips:
            pl.ips = ips
            score += 0.15

        m = HTTP_STATUS_CTX_RE.search(line)
        if m and m.group(1)[0] in "12345":
            pl.status = m.group(1)
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
    def _classify(pl: ParsedLine) -> str:
        has_anchor = pl.timestamp is not None or pl.level is not None
        has_content = bool(
            pl.ips or pl.status or pl.url or pl.emails
            or (pl.timestamp and pl.level)
        )
        if has_anchor and has_content and pl.confidence >= 0.5:
            return "well_formed"
        if pl.confidence >= 0.2:
            return "partial"
        return "malformed"

    def _diagnose_malformed(self, raw: str) -> str:
        if not raw.strip():
            return "blank"
        if len(raw) > MAX_LINE_LEN:
            return "line-too-long"
        if "\ufffd" in raw:
            return "decode-error"
        if any(ord(c) < 32 and c not in "\t\r\n" for c in raw):
            return "binary-control-chars"
        if not re.search(r"[A-Za-z]", raw):
            return "no-alpha"
        return "no-recognized-fields"

    def _record_error_message(self, line: str, level: str) -> None:
        m = re.search(r"\b" + level + r"\b[:\-\s]*(.*)", line, re.IGNORECASE)
        if not m:
            return
        msg = m.group(1).strip()
        if not msg:
            return
        msg = re.sub(r"0x[0-9a-fA-F]+", "HEX", msg)
        msg = re.sub(r"\b\d+\b", "N", msg)
        msg = re.sub(r'"[^"]*"', '"..."', msg)
        _bump(self.error_messages, msg[:140])

    @classmethod
    def _fingerprint(cls, level: str, message: str) -> Tuple[str, str]:
        template = message if message else f"<{level}>"
        for pat, repl in cls._FP_SUBS:
            template = pat.sub(repl, template)
        template = template.strip()
        bucket = {"WARNING": "W", "ERROR": "E",
                  "CRITICAL": "C", "FATAL": "F"}.get(level, "?")
        canonical = f"{bucket}|{template[:300]}"
        fp = hashlib.sha1(canonical.encode("utf-8", "replace")).hexdigest()[:12]
        return fp, template[:300]

    def _track_repeat(self, pl: ParsedLine, raw_line: str) -> None:
        if pl.level not in ("WARNING", "ERROR", "CRITICAL", "FATAL"):
            return
        fp, template = self._fingerprint(pl.level, pl.message)
        pl.fingerprint = fp
        group = self.error_groups.get(fp)
        if group is None:
            if len(self.error_groups) >= self.MAX_FINGERPRINTS:
                self.error_groups.popitem(last=False)
            group = ErrorGroup(
                fingerprint=fp, level=pl.level, template=template,
                first_seen=pl.timestamp,
                streak_gap=self.STREAK_GAP, rate_window=self.RATE_WINDOW,
            )
            self.error_groups[fp] = group
        group.add(pl.timestamp, raw_line)

    def _compute_repeated(self) -> List[ErrorGroup]:
        flagged = [
            g for g in self.error_groups.values()
            if (g.count >= self.REPEAT_MIN_TOTAL
                or g.streak >= self.REPEAT_STREAK_THRESHOLD
                or g.peak_rate >= self.REPEAT_RATE_THRESHOLD)
        ]
        flagged.sort(key=lambda g: (-g.peak_rate, -g.streak, -g.count))
        return flagged

    def process_line(self, raw: str) -> None:
        self.total_lines += 1
        line = raw.rstrip("\n")
        if not line.strip():
            self.blank_lines += 1
            return

        parsed = self.parse_line(line)
        classification = self._classify(parsed)

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

        if classification == "well_formed":
            self.well_formed += 1
        elif classification == "partial":
            self.partial += 1
            self.malformed_reasons["partial-parse"] += 1
            if len(self.malformed_samples) < MAX_SAMPLES:
                self.malformed_samples.append(f"[partial-parse] {line[:180]}")
        else:
            self.malformed += 1
            reason = self._diagnose_malformed(line)
            self.malformed_reasons[reason] += 1
            if len(self.malformed_samples) < MAX_SAMPLES:
                self.malformed_samples.append(f"[{reason}] {line[:180]}")

        self._track_repeat(parsed, line)

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

    def _pct(self, n: int) -> str:
        denom = max(self.total_lines - self.blank_lines, 1)
        return f"{n / denom * 100:5.1f}%"

    @staticmethod
    def format_duration(a, b) -> str:
        if not (a and b):
            return "unknown"
        secs = max(int((b - a).total_seconds()), 0)
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
        W = 72
        out: List[str] = []
        out.append("=" * W)
        out.append("LOG SUMMARY REPORT".center(W))
        out.append("=" * W)

        out.append("\nBASIC STATISTICS")
        out.append("-" * 40)
        out.append(f"  Total lines:        {self.total_lines:>12,}")
        out.append(f"  Blank lines:        {self.blank_lines:>12,}")
        out.append(f"  Well-formed:        {self.well_formed:>12,}  ({self._pct(self.well_formed)})")
        out.append(f"  Partial:            {self.partial:>12,}  ({self._pct(self.partial)})")
        out.append(f"  Malformed:          {self.malformed:>12,}  ({self._pct(self.malformed)})")
        if self.file_size:
            out.append(f"  File size:          {self.format_bytes(self.file_size):>12}")

        if self.first_ts and self.last_ts:
            out.append("\nTIME RANGE")
            out.append("-" * 40)
            out.append(f"  First:  {self.first_ts}")
            out.append(f"  Last:   {self.last_ts}")
            out.append(f"  Span:   {self.format_duration(self.first_ts, self.last_ts)}")

        if self.level_counts:
            out.append("\nLOG LEVELS")
            out.append("-" * 40)
            total = sum(self.level_counts.values())
            for lvl in sorted(self.level_counts):
                cnt = self.level_counts[lvl]
                pct = cnt / total * 100
                out.append(f"  {lvl:<10} {cnt:>10,} ({pct:>5.1f}%) {'#' * int(pct / 2)}")

        repeated = self._compute_repeated()
        out.append("\nREPEATED ERRORS")
        out.append("-" * 40)
        if not repeated:
            out.append("  (no repeated errors detected)")
        else:
            out.append(
                f"  Thresholds: total>={self.REPEAT_MIN_TOTAL} OR "
                f"streak>={self.REPEAT_STREAK_THRESHOLD} OR "
                f"rate>={self.REPEAT_RATE_THRESHOLD}/{int(self.RATE_WINDOW.total_seconds())}s"
            )
            out.append("")
            for g in repeated[:15]:
                dur = self.format_duration(g.first_seen, g.last_seen)
                out.append(f"  [{g.level:<8}] x{g.count:<6} streak={g.streak:<4} "
                           f"rate={g.peak_rate:<4} span={dur}")
                out.append(f"      fp={g.fingerprint}  {g.template}")
                if g.sample_line:
                    out.append(f"      e.g. {g.sample_line[:100]}")
                out.append("")

        if self.malformed_reasons:
            out.append("MALFORMED-LINE REASONS")
            out.append("-" * 40)
            for r, c in self.malformed_reasons.most_common():
                out.append(f"  {r:<25} {c:>10,}")

        if self.malformed_samples:
            out.append("\nMALFORMED SAMPLES")
            out.append("-" * 40)
            for s in self.malformed_samples[:8]:
                out.append(f"  {s}")

        if self.ip_addresses:
            out.append("\nTOP IP ADDRESSES")
            out.append("-" * 40)
            for ip, c in self.ip_addresses.most_common(10):
                out.append(f"  {ip:<20} {c:>10,}")

        if self.status_codes:
            out.append("\nHTTP STATUS CODES")
            out.append("-" * 40)
            for s, c in self.status_codes.most_common(10):
                out.append(f"  {s}: {c:,}")

        out.append("=" * W)
        return "\n".join(out)

    def to_dict(self) -> Dict:
        repeated = self._compute_repeated()
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
            "repeated_errors": [
                {
                    "fingerprint": g.fingerprint,
                    "level": g.level,
                    "count": g.count,
                    "streak": g.streak,
                    "peak_rate": g.peak_rate,
                    "window_seconds": int(self.RATE_WINDOW.total_seconds()),
                    "first_seen": g.first_seen.isoformat() if g.first_seen else None,
                    "last_seen": g.last_seen.isoformat() if g.last_seen else None,
                    "template": g.template,
                    "sample": g.sample_line,
                }
                for g in repeated
            ],
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="log_summarizer",
        description="Summarize logs with malformed-line and repeated-error detection.",
    )
    p.add_argument("input", nargs="?", default="-",
                   help="Log file path, or '-' for stdin (default)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--compact", action="store_true", help="Compact JSON")
    p.add_argument("-o", "--output", help="Write report to this file")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress stdout")
    p.add_argument("--repeat-min-total", type=int, default=LogSummarizer.REPEAT_MIN_TOTAL)
    p.add_argument("--repeat-streak", type=int, default=LogSummarizer.REPEAT_STREAK_THRESHOLD)
    p.add_argument("--repeat-rate", type=int, default=LogSummarizer.REPEAT_RATE_THRESHOLD)
    p.add_argument("--rate-window", type=int,
                   default=int(LogSummarizer.RATE_WINDOW.total_seconds()))
    p.add_argument("--streak-gap", type=int,
                   default=int(LogSummarizer.STREAK_GAP.total_seconds()))
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_argparser().parse_args(argv)

    s = LogSummarizer()
    s.REPEAT_MIN_TOTAL = args.repeat_min_total
    s.REPEAT_STREAK_THRESHOLD = args.repeat_streak
    s.REPEAT_RATE_THRESHOLD = args.repeat_rate
    s.RATE_WINDOW = timedelta(seconds=args.rate_window)
    s.STREAK_GAP = timedelta(seconds=args.streak_gap)

    if args.input == "-":
        s.process_stdin()
    else:
        s.process_file(args.input)

    report = s.to_json(indent=None if args.compact else 2) if args.json else s.generate_summary()

    if not args.quiet:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"report written to {args.output}", file=sys.stderr)
        else:
            print(report)

    if s.total_lines > 0 and s.well_formed == 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())