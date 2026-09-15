"""
Inventory Reconciliation System (v2)
- Handles duplicate SKUs (aggregates or flags based on mode)
- Validates records (negative qty, missing fields, bad types, non-numeric)
- Produces a data-quality report alongside the reconciliation report
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re


# ---------------- Enums ----------------
class DiscrepancyType(Enum):
    MATCH = "match"
    SHORTAGE = "shortage"
    OVERAGE = "overage"
    MISSING_IN_SYSTEM = "missing_in_system"
    MISSING_IN_PHYSICAL = "missing_in_physical"


class DuplicateMode(Enum):
    AGGREGATE = "aggregate"   # sum quantities across duplicate rows
    LAST_WINS = "last_wins"   # keep the last record
    FIRST_WINS = "first_wins" # keep the first record
    REJECT = "reject"         # drop all but flag them


class IssueSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


# ---------------- Data-quality tracking ----------------
@dataclass
class DataIssue:
    source: str            # "system" | "physical"
    sku: Optional[str]
    row_index: int
    severity: IssueSeverity
    reason: str
    raw: dict


@dataclass
class DataQualityReport:
    total_rows: int = 0
    accepted_rows: int = 0
    rejected_rows: int = 0
    duplicates: int = 0
    issues: List[DataIssue] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "-" * 60,
            "DATA QUALITY REPORT",
            "-" * 60,
            f"Total rows examined : {self.total_rows}",
            f"Accepted            : {self.accepted_rows}",
            f"Rejected            : {self.rejected_rows}",
            f"Duplicates resolved : {self.duplicates}",
            f"Total issues        : {len(self.issues)}",
        ]
        if self.issues:
            lines.append("-" * 60)
            lines.append(f"{'Src':<9}{'Row':>4}  {'SKU':<10}{'Sev':<8}Reason")
            lines.append("-" * 60)
            for i in self.issues:
                lines.append(
                    f"{i.source:<9}{i.row_index:>4}  "
                    f"{(i.sku or '<none>'):<10}{i.severity.value:<8}{i.reason}"
                )
        lines.append("-" * 60)
        return "\n".join(lines)


# ---------------- Domain ----------------
@dataclass
class InventoryItem:
    sku: str
    description: str = ""
    system_qty: int = 0
    physical_qty: int = 0
    unit_cost: float = 0.0

    @property
    def variance(self) -> int:
        return self.physical_qty - self.system_qty

    @property
    def variance_value(self) -> float:
        return self.variance * self.unit_cost

    @property
    def discrepancy_type(self) -> DiscrepancyType:
        if self.system_qty == 0 and self.physical_qty > 0:
            return DiscrepancyType.MISSING_IN_SYSTEM
        if self.physical_qty == 0 and self.system_qty > 0:
            return DiscrepancyType.MISSING_IN_PHYSICAL
        if self.variance == 0:
            return DiscrepancyType.MATCH
        return DiscrepancyType.SHORTAGE if self.variance < 0 else DiscrepancyType.OVERAGE


@dataclass
class ReconciliationReport:
    timestamp: str
    total_items: int = 0
    matched: int = 0
    discrepancies: List[InventoryItem] = field(default_factory=list)
    total_variance_value: float = 0.0
    tolerance: int = 0

    def summary(self) -> str:
        lines = [
            "=" * 60,
            f"INVENTORY RECONCILIATION REPORT — {self.timestamp}",
            "=" * 60,
            f"Total SKUs reviewed : {self.total_items}",
            f"Matched             : {self.matched}",
            f"Discrepancies       : {len(self.discrepancies)}",
            f"Net variance value  : ${self.total_variance_value:,.2f}",
            f"Tolerance threshold : ±{self.tolerance} units",
            "-" * 60,
        ]
        if not self.discrepancies:
            lines.append("OK: No discrepancies found. Inventory is balanced.")
        else:
            lines.append(
                f"{'SKU':<12}{'Type':<22}{'Sys':>6}{'Phys':>6}{'Var':>6}{'Value':>12}"
            )
            lines.append("-" * 60)
            for item in sorted(
                self.discrepancies, key=lambda i: abs(i.variance_value), reverse=True
            ):
                lines.append(
                    f"{item.sku:<12}{item.discrepancy_type.value:<22}"
                    f"{item.system_qty:>6}{item.physical_qty:>6}"
                    f"{item.variance:>+6}{item.variance_value:>12,.2f}"
                )
        lines.append("=" * 60)
        return "\n".join(lines)


# ---------------- Validation helpers ----------------
SKU_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,31}$")


def _coerce_int(value) -> Tuple[bool, Optional[int], str]:
    """Return (ok, int_value, reason)."""
    if value is None:
        return False, None, "missing qty"
    if isinstance(value, bool):
        return False, None, "bool is not a valid qty"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False, None, f"non-numeric qty: {value!r}"
    if f != int(f):
        return False, None, f"fractional qty not allowed: {f}"
    return True, int(f), ""


def _coerce_cost(value) -> Tuple[bool, Optional[float], str]:
    if value is None or value == "":
        return True, 0.0, ""  # missing cost defaults to 0 with no error
    if isinstance(value, bool):
        return False, None, "bool is not a valid cost"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False, None, f"non-numeric cost: {value!r}"
    if f < 0:
        return False, None, f"negative unit_cost: {f}"
    return True, f, ""


def _validate_sku(raw) -> Tuple[bool, Optional[str], str]:
    if raw is None or str(raw).strip() == "":
        return False, None, "missing sku"
    sku = str(raw).strip().upper()
    if not SKU_RE.match(sku):
        return False, None, f"invalid sku format: {raw!r}"
    return True, sku, ""


# ---------------- Reconciler ----------------
class InventoryReconciler:
    """Reconciles physical counts against system records with validation."""

    def __init__(self, tolerance: int = 0, duplicate_mode: DuplicateMode = DuplicateMode.AGGREGATE):
        self.tolerance = tolerance
        self.duplicate_mode = duplicate_mode
        self._items: Dict[str, InventoryItem] = {}
        self.data_quality = DataQualityReport()
        self._dup_tracker: Dict[Tuple[str, str], int] = {}  # (source, sku) -> count

    # --- internal ---
    def _record_issue(self, source, sku, row_idx, severity, reason, raw):
        self.data_quality.issues.append(
            DataIssue(source, sku, row_idx, severity, reason, raw)
        )

    def _apply_duplicate_policy(self, source: str, sku: str, incoming: dict) -> Optional[dict]:
        """Decide how to handle a duplicate. Returns the record to apply, or None."""
        key = (source, sku)
        count = self._dup_tracker.get(key, 0)
        self._dup_tracker[key] = count + 1

        if count == 0:
            return incoming

        self.data_quality.duplicates += 1
        self._record_issue(
            source, sku, incoming["_row"], IssueSeverity.WARNING,
            f"duplicate sku ({self.duplicate_mode.value})", incoming["_raw"],
        )

        mode = self.duplicate_mode
        if mode == DuplicateMode.FIRST_WINS:
            return None
        if mode == DuplicateMode.LAST_WINS:
            return incoming
        if mode == DuplicateMode.REJECT:
            # Remove any previously applied record and refuse new one
            self._items.pop(sku, None)
            return None
        # AGGREGATE
        return incoming

    def _apply(self, source: str, record: dict) -> None:
        sku = record["sku"]
        item = self._items.get(sku)
        if item is None:
            item = InventoryItem(sku=sku)
            self._items[sku] = item

        if source == "system":
            if self.duplicate_mode == DuplicateMode.AGGREGATE and item.system_qty:
                item.system_qty += record["qty"]
            else:
                item.system_qty = record["qty"]
            if record.get("description"):
                item.description = record["description"]
            if record.get("unit_cost"):
                item.unit_cost = record["unit_cost"]
        else:  # physical
            if self.duplicate_mode == DuplicateMode.AGGREGATE and item.physical_qty:
                item.physical_qty += record["qty"]
            else:
                item.physical_qty = record["qty"]
            if record.get("description") and not item.description:
                item.description = record["description"]
            if record.get("unit_cost") and not item.unit_cost:
                item.unit_cost = record["unit_cost"]

    def _ingest(self, source: str, rows: List[dict], require_cost: bool) -> None:
        for idx, raw in enumerate(rows):
            self.data_quality.total_rows += 1

            ok_sku, sku, sku_err = _validate_sku(raw.get("sku"))
            if not ok_sku:
                self.data_quality.rejected_rows += 1
                self._record_issue(source, None, idx, IssueSeverity.ERROR, sku_err, raw)
                continue

            ok_qty, qty, qty_err = _coerce_int(raw.get("qty"))
            if not ok_qty:
                self.data_quality.rejected_rows += 1
                self._record_issue(source, sku, idx, IssueSeverity.ERROR, qty_err, raw)
                continue
            if qty < 0:
                self.data_quality.rejected_rows += 1
                self._record_issue(
                    source, sku, idx, IssueSeverity.ERROR,
                    f"negative qty: {qty}", raw,
                )
                continue

            ok_cost, cost, cost_err = _coerce_cost(raw.get("unit_cost"))
            if not ok_cost:
                self.data_quality.rejected_rows += 1
                self._record_issue(source, sku, idx, IssueSeverity.ERROR, cost_err, raw)
                continue
            if require_cost and cost == 0.0:
                self._record_issue(
                    source, sku, idx, IssueSeverity.WARNING,
                    "unit_cost missing or zero", raw,
                )

            record = {
                "sku": sku,
                "qty": qty,
                "unit_cost": cost or 0.0,
                "description": str(raw.get("description", "")).strip(),
                "_row": idx,
                "_raw": raw,
            }

            decision = self._apply_duplicate_policy(source, sku, record)
            if decision is None:
                continue

            self._apply(source, decision)
            self.data_quality.accepted_rows += 1

    # --- public API ---
    def load_system_records(self, records: List[dict]) -> "InventoryReconciler":
        self._ingest("system", records, require_cost=True)
        return self

    def load_physical_counts(self, counts: List[dict]) -> "InventoryReconciler":
        self._ingest("physical", counts, require_cost=False)
        return self

    def reconcile(self) -> ReconciliationReport:
        report = ReconciliationReport(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            tolerance=self.tolerance,
        )
        for item in self._items.values():
            report.total_items += 1
            if abs(item.variance) <= self.tolerance:
                report.matched += 1
            else:
                report.discrepancies.append(item)
                report.total_variance_value += item.variance_value
        return report

    def adjustments(self, report: ReconciliationReport) -> List[dict]:
        return [
            {
                "sku": i.sku,
                "adjust_qty": i.variance,
                "new_system_qty": i.physical_qty,
                "reason": i.discrepancy_type.value,
                "value_impact": round(i.variance_value, 2),
            }
            for i in report.discrepancies
        ]


# ---------------- Demo ----------------
if __name__ == "__main__":
    system = [
        {"sku": "A100", "description": "Widget",     "qty": 100, "unit_cost": 2.50},
        {"sku": "B200", "description": "Gadget",     "qty": 50,  "unit_cost": 10.00},
        {"sku": "b200", "description": "Gadget dup", "qty": 5,   "unit_cost": 10.00},  # duplicate (case)
        {"sku": "C300", "description": "Gizmo",      "qty": 75,  "unit_cost": 5.00},
        {"sku": "D400", "description": "Doohickey",  "qty": 20,  "unit_cost": 15.00},
        {"sku": "E500", "description": "Thingamajig","qty": 200, "unit_cost": 1.25},
        {"sku": "",     "description": "No SKU",     "qty": 5,   "unit_cost": 1.00},   # missing sku
        {"sku": "X900", "description": "Bad qty",    "qty": -3,  "unit_cost": 1.00},   # negative
        {"sku": "Y901", "description": "Bad qty 2",  "qty": "abc","unit_cost": 1.00},  # non-numeric
        {"sku": "Z902", "description": "Bad cost",   "qty": 10,  "unit_cost": -5.00},  # negative cost
    ]
    physical = [
        {"sku": "A100", "qty": 100},                                  # match
        {"sku": "B200", "qty": 47},                                   # shortage (after aggregate: 50+5=55 sys -> -8)
        {"sku": "C300", "qty": 80},                                   # overage
        {"sku": "D400", "qty": 0},                                    # missing in physical
        {"sku": "F600", "qty": 12, "unit_cost": 3.00},                # missing in system
        {"sku": "A100", "qty": 5},                                    # duplicate physical (aggregated)
        {"sku": "G700", "qty": 7},                                    # missing cost warning
        {"sku": "H800", "qty": None},                                 # missing qty -> rejected
    ]

    reconciler = (
        InventoryReconciler(tolerance=0, duplicate_mode=DuplicateMode.AGGREGATE)
        .load_system_records(system)
        .load_physical_counts(physical)
    )

    report = reconciler.reconcile()
    print(reconciler.data_quality.summary())
    print()
    print(report.summary())
    print("\nSuggested Adjustments:")
    for adj in reconciler.adjustments(report):
        print(f"  {adj}")