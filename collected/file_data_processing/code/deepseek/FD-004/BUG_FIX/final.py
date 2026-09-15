"""
Inventory Reconciliation Utility
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, Tuple

Key = Tuple[str, str]


def load_snapshot(path: Path) -> Dict[Key, int]:
    """Load a snapshot and sum quantities for duplicate (warehouse, product) keys."""
    totals: Dict[Key, int] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        required = {"warehouse", "product", "quantity"}
        if not reader.fieldnames or not required.issubset(
            {name.strip().lower() for name in reader.fieldnames}
        ):
            raise ValueError(
                f"{path}: expected columns {sorted(required)}, got {reader.fieldnames}"
            )
        field_map = {name.strip().lower(): name for name in reader.fieldnames}
        for lineno, row in enumerate(reader, start=2):
            try:
                warehouse = (row[field_map["warehouse"]] or "").strip()
                product = (row[field_map["product"]] or "").strip()
                qty_raw = (row[field_map["quantity"]] or "").strip()
                if not warehouse or not product:
                    raise ValueError("missing warehouse or product")
                quantity = int(float(qty_raw))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"{path}:{lineno}: bad row ({exc})") from exc

            key = (warehouse, product)
            # Explicit duplicate summing:
            if key in totals:
                totals[key] += quantity
            else:
                totals[key] = quantity
    return totals


def reconcile(old: Dict[Key, int], new: Dict[Key, int]) -> list:
    all_keys = sorted(set(old) | set(new))
    rows = []
    for key in all_keys:
        warehouse, product = key
        old_qty = old.get(key)
        new_qty = new.get(key)
        if old_qty is None:
            status, delta, old_out, new_out = "added", new_qty, "", new_qty
        elif new_qty is None:
            status, delta, old_out, new_out = "removed", -old_qty, old_qty, ""
        elif old_qty != new_qty:
            status = "changed"
            delta = new_qty - old_qty
            old_out, new_out = old_qty, new_qty
        else:
            status, delta, old_out, new_out = "unchanged", 0, old_qty, new_qty
        rows.append({
            "warehouse": warehouse,
            "product": product,
            "status": status,
            "old_quantity": old_out,
            "new_quantity": new_out,
            "delta": delta,
        })
    return rows


def write_report(rows: list, path: Path) -> None:
    priority = {"added": 0, "removed": 1, "changed": 2, "unchanged": 3}
    rows_sorted = sorted(
        rows,
        key=lambda r: (priority[r["status"]], r["warehouse"], r["product"]),
    )
    fieldnames = ["warehouse", "product", "status", "old_quantity", "new_quantity", "delta"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_sorted)


def summarize(rows: list) -> str:
    counts = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    for row in rows:
        counts[row["status"]] += 1
    total_delta = sum(row["delta"] for row in rows if isinstance(row["delta"], int))
    return (
        f"added={counts['added']} removed={counts['removed']} "
        f"changed={counts['changed']} unchanged={counts['unchanged']} "
        f"net_delta={total_delta}"
    )


def main(argv: list) -> int:
    if len(argv) != 4:
        print("Usage: python inventory_recon.py <old.csv> <new.csv> <report.csv>", file=sys.stderr)
        return 2
    old_path, new_path, out_path = map(Path, argv[1:4])
    old_snapshot = load_snapshot(old_path)
    new_snapshot = load_snapshot(new_path)
    rows = reconcile(old_snapshot, new_snapshot)
    write_report(rows, out_path)
    print(summarize(rows))
    print(f"Report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))