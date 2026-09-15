import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedRecord:
    raw: str
    name: Optional[str] = None
    value: Optional[float] = None
    valid: bool = False
    issue: Optional[str] = None


@dataclass
class AnalysisResult:
    total_records: int = 0
    valid_records: int = 0
    empty_count: int = 0
    malformed_count: int = 0
    zero_value_count: int = 0
    whitespace_heavy_count: int = 0
    values: List[float] = field(default_factory=list)
    issues: List[ParsedRecord] = field(default_factory=list)

    @property
    def sum(self) -> float:
        return sum(self.values)

    @property
    def average(self) -> Optional[float]:
        return self.sum / len(self.values) if self.values else None

    @property
    def minimum(self) -> Optional[float]:
        return min(self.values) if self.values else None

    @property
    def maximum(self) -> Optional[float]:
        return max(self.values) if self.values else None

    def summary(self) -> str:
        return "\n".join([
            f"Total records:        {self.total_records}",
            f"Valid records:        {self.valid_records}",
            f"Empty records:        {self.empty_count}",
            f"Malformed records:    {self.malformed_count}",
            f"Zero-value records:   {self.zero_value_count}",
            f"Whitespace-heavy:     {self.whitespace_heavy_count}",
            f"Sum of values:        {self.sum}",
            f"Average value:        {self.average}",
            f"Min / Max:            {self.minimum} / {self.maximum}",
        ])


class RecordAnalyzer:
    """Parses 'name,value' records (whitespace-tolerant) and aggregates stats,
    classifying edge cases instead of dropping or crashing on them."""

    WHITESPACE_HEAVY_RATIO = 0.5  # fraction of raw text that's "padding"

    def __init__(self, records: Optional[List[str]] = None):
        self.records = records or []

    def _is_whitespace_heavy(self, raw: str) -> bool:
        if not raw:
            return False
        collapsed = re.sub(r"\s+", " ", raw).strip()
        ratio_padding = 1 - (len(collapsed) / max(len(raw), 1))
        return ratio_padding >= self.WHITESPACE_HEAVY_RATIO

    def _parse_record(self, raw: str) -> ParsedRecord:
        pr = ParsedRecord(raw=raw)

        # Empty check (None or whitespace-only)
        if raw is None or raw.strip() == "":
            pr.issue = "empty"
            return pr

        whitespace_heavy = self._is_whitespace_heavy(raw)
        cleaned = re.sub(r"\s+", " ", raw).strip()

        parts = [p.strip() for p in cleaned.split(",")]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            pr.issue = "whitespace_heavy_malformed" if whitespace_heavy else "malformed"
            return pr

        name, raw_value = parts
        try:
            value = float(raw_value)
        except ValueError:
            pr.issue = "whitespace_heavy_malformed" if whitespace_heavy else "malformed"
            return pr

        pr.name = name
        pr.value = value
        pr.valid = True

        if whitespace_heavy:
            pr.issue = "whitespace_heavy_valid"
        elif value == 0:
            pr.issue = "zero_value"

        return pr

    def analyze(self, records: Optional[List[str]] = None) -> AnalysisResult:
        records = records if records is not None else self.records
        result = AnalysisResult(total_records=len(records))

        for raw in records:
            pr = self._parse_record(raw)

            if pr.issue == "empty":
                result.empty_count += 1
                result.issues.append(pr)
                continue

            if pr.issue in ("malformed", "whitespace_heavy_malformed"):
                result.malformed_count += 1
                if pr.issue == "whitespace_heavy_malformed":
                    result.whitespace_heavy_count += 1
                result.issues.append(pr)
                continue

            result.valid_records += 1
            result.values.append(pr.value)

            if pr.issue == "zero_value":
                result.zero_value_count += 1
                result.issues.append(pr)
            elif pr.issue == "whitespace_heavy_valid":
                result.whitespace_heavy_count += 1
                result.issues.append(pr)

        return result


if __name__ == "__main__":
    sample_records = [
        "apples,10",
        "",                      # empty
        "   ",                   # empty (whitespace only)
        "bananas,0",             # zero-value
        "cherries,,extra",       # malformed
        "  \t dates ,  5\n",     # whitespace-heavy but valid
        "figs,not_a_number",     # malformed
        "  \n\n grapes,0  \n",   # whitespace-heavy AND zero-value
        "kiwi,7",
    ]

    analyzer = RecordAnalyzer(sample_records)
    result = analyzer.analyze()
    print(result.summary())
    print("\nFlagged records:")
    for pr in result.issues:
        print(f"  [{pr.issue:>26}] raw={pr.raw!r}")