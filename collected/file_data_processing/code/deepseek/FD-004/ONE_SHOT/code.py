#!/usr/bin/env python3
"""
Inventory Reconciliation Utility

Compares two CSV inventory snapshots (old vs new) and produces a reconciled
report. Each snapshot must contain at least these columns:

    warehouse, product, quantity

Behavior:
    - Duplicate (warehouse, product) rows within a single snapshot are summed.
    - Every key in the union of both snapshots is classified as one of:
        added     -> key only in new snapshot
        removed   -> key only in old snapshot
        changed   -> key in both, quantity differs
        unchanged -> key in both, quantity identical
    - The delta column is (new_quantity - old_quantity).
    - Output is deterministic: rows are sorted by (warehouse, product).

Usage:
    python reconcile.py old.csv new.csv -o report.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, NamedTuple, Tuple


Key = Tuple[str, str]


class ReconcileRow(NamedTuple):
    warehouse: str
    product: str
    old_quantity: int
    new_quantity: int
    delta: int
    status: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "warehouse": self.warehouse,
            "product": self.product,
            "old_quantity": self.old_quantity,
            "new_quantity": self.new_quantity,
            "delta": self.delta,
            "status": self.status,
        }


STATUS_ADDED = "added"
STATUS_REMOVED = "removed"
STATUS_CHANGED = "changed"
STATUS_UNCHANGED = "unchanged"

OUTPUT_FIELDS = [
    "warehouse",
    "product",
    "old_quantity",
    "new_quantity",
    "delta",
    "status",
]


def _normalize_key(value: str) -> str:
    return (value or "").strip()


def _parse_quantity(raw: str, *, path: Path, line_no: int) -> int:
    text = (raw or "").strip()
    if text == "":
        return 0
    try:
        return int(text)
    except ValueError:
        try:
            as_float = float(text)
        except ValueError as exc:
            raise ValueError(
                f"{path}: line {line_no}: invalid quantity {raw!r}"
            ) from exc
        if not as_float.is_integer():
            raise ValueError(
                f"{path}: line {line_no}: non-integer quantity {raw!r}"
            )
        return int(as_float)


def load_snapshot(path: Path) -> Dict[Key, int]:
    if not path.is_file():
        raise FileNotFoundError(f"snapshot not found: {path}")

    totals: Dict[Key, int] = {}

    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: file is empty or has no header row")

        required = {"warehouse", "product", "quantity"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{path}: missing required column(s): {sorted(missing)}"
            )

        for line_no, row in enumerate(reader, start=2):
            warehouse = _normalize_key(row.get("warehouse", ""))
            product = _normalize_key(row.get("product", ""))

            if not warehouse or not product:
                if not warehouse and not product and not (row.get("quantity") or "").strip():
                    continue
                raise ValueError(
                    f"{path}: line {line_no}: warehouse and product are required"
                )

            qty = _parse_quantity(row.get("quantity", ""), path=path, line_no=line_no)
            key = (warehouse, product)
            totals[key] = totals.get(key, 0) + qty

    return totals


def reconcile(
    old: Dict[Key, int],
    new: Dict[Key, int],
) -> list[ReconcileRow]:
    all_keys: Iterable[Key] = sorted(set(old) | set(new))

    rows: list[ReconcileRow] = []
    for key in all_keys:
        warehouse, product = key
        in_old = key in old
        in_new = key in new

        old_qty = old.get(key, 0)
        new_qty = new.get(key, 0)
        delta = new_qty - old_qty

        if in_new and not in_old:
            status = STATUS_ADDED
        elif in_old and not in_new:
            status = STATUS_REMOVED
        elif old_qty != new_qty:
            status = STATUS_CHANGED
        else:
            status = STATUS_UNCHANGED

        rows.append(
            ReconcileRow(
                warehouse=warehouse,
                product=product,
                old_quantity=old_qty,
                new_quantity=new_qty,
                delta=delta,
                status=status,
            )
        )

    return rows


def write_report(rows: Iterable[ReconcileRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())


def summarize(rows: Iterable[ReconcileRow]) -> Dict[str, int]:
    counts = {
        STATUS_ADDED: 0,
        STATUS_REMOVED: 0,
        STATUS_CHANGED: 0,
        STATUS_UNCHANGED: 0,
    }
    for row in rows:
        counts[row.status] += 1
    return counts


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconcile two inventory CSV snapshots.",
    )
    parser.add_argument("old", type=Path, help="path to the old snapshot CSV")
    parser.add_argument("new", type=Path, help="path to the new snapshot CSV")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="path to write the reconciliation report (default: stdout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        old = load_snapshot(args.old)
        new = load_snapshot(args.new)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = reconcile(old, new)

    if args.output is None:
        writer = csv.DictWriter(
            sys.stdout, fieldnames=OUTPUT_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())
    else:
        write_report(rows, args.output)
        counts = summarize(rows)
        print(
            f"wrote {len(rows)} rows to {args.output} "
            f"(added={counts[STATUS_ADDED]}, "
            f"removed={counts[STATUS_REMOVED]}, "
            f"changed={counts[STATUS_CHANGED]}, "
            f"unchanged={counts[STATUS_UNCHANGED]})",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())