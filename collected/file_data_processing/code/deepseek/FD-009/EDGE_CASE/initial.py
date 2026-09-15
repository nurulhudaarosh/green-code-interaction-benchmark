import csv
import statistics
from collections import defaultdict, deque
from typing import List, Dict, NamedTuple, Optional, Tuple
from pathlib import Path
import json


class Transaction(NamedTuple):
    account_id: str
    amount: float
    sequence: int


class AnalysisResult(NamedTuple):
    account_id: str
    sequence: int
    amount: float
    rolling_mean: Optional[float]
    rolling_stddev: Optional[float]
    threshold: Optional[float]
    flagged: bool
    reason: str


ZERO_DEVIATION_RULE_MESSAGE = "zero deviation rule applied"
INSUFFICIENT_HISTORY_MESSAGE = "insufficient preceding transactions"
FLAGGED_MESSAGE = "amount exceeds mean + 3 population std deviations"
NOT_FLAGGED_MESSAGE = "within expected range"


def load_transactions(path: Path) -> List[Transaction]:
    transactions: List[Transaction] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"account_id", "amount", "sequence"}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        for row in reader:
            transactions.append(
                Transaction(
                    account_id=row["account_id"].strip(),
                    amount=float(row["amount"]),
                    sequence=int(row["sequence"]),
                )
            )
    return transactions


def analyze(transactions: List[Transaction]) -> List[AnalysisResult]:
    by_account: Dict[str, List[Transaction]] = defaultdict(list)
    for tx in transactions:
        by_account[tx.account_id].append(tx)

    results: List[AnalysisResult] = []

    for account_id in sorted(by_account.keys()):
        account_txs = sorted(by_account[account_id], key=lambda t: (t.sequence, t.amount))
        window: deque = deque(maxlen=5)

        for tx in account_txs:
            if len(window) < 5:
                results.append(
                    AnalysisResult(
                        account_id=account_id,
                        sequence=tx.sequence,
                        amount=tx.amount,
                        rolling_mean=None,
                        rolling_stddev=None,
                        threshold=None,
                        flagged=False,
                        reason=INSUFFICIENT_HISTORY_MESSAGE,
                    )
                )
                window.append(tx.amount)
                continue

            preceding = list(window)
            mean = statistics.fmean(preceding)
            population_stddev = statistics.pstdev(preceding)

            if population_stddev == 0.0:
                threshold = mean
                flagged = tx.amount > mean
                reason = ZERO_DEVIATION_RULE_MESSAGE
            else:
                threshold = mean + 3.0 * population_stddev
                flagged = tx.amount > threshold
                reason = FLAGGED_MESSAGE if flagged else NOT_FLAGGED_MESSAGE

            results.append(
                AnalysisResult(
                    account_id=account_id,
                    sequence=tx.sequence,
                    amount=tx.amount,
                    rolling_mean=mean,
                    rolling_stddev=population_stddev,
                    threshold=threshold,
                    flagged=flagged,
                    reason=reason,
                )
            )
            window.append(tx.amount)

    results.sort(key=lambda r: (r.account_id, r.sequence, r.amount))
    return results


def format_float(value: Optional[float]) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def write_results(results: List[AnalysisResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "account_id",
                "sequence",
                "amount",
                "rolling_mean",
                "rolling_stddev",
                "threshold",
                "flagged",
                "reason",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.account_id,
                    r.sequence,
                    f"{r.amount:.6f}",
                    format_float(r.rolling_mean),
                    format_float(r.rolling_stddev),
                    format_float(r.threshold),
                    "true" if r.flagged else "false",
                    r.reason,
                ]
            )


def write_summary(results: List[AnalysisResult], path: Path) -> None:
    summary = {
        "total_transactions": len(results),
        "flagged_transactions": sum(1 for r in results if r.flagged),
        "accounts": sorted({r.account_id for r in results}),
        "zero_deviation_events": sum(
            1 for r in results if r.reason == ZERO_DEVIATION_RULE_MESSAGE
        ),
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")


def main(input_path: str = "transactions.csv", output_dir: str = "output") -> None:
    input_file = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    transactions = load_transactions(input_file)
    results = analyze(transactions)

    write_results(results, out_dir / "analysis.csv")
    write_summary(results, out_dir / "summary.json")


if __name__ == "__main__":
    main()