"""
Inventory Reconciliation System (v3)
- Handles duplicate SKUs (configurable policy)
- Validates records (missing fields, bad types, negatives, bad SKUs)
- Reconciles physical vs system
- NEW: Low-stock / reorder reporting with severity tiers
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
    AGGREGATE = "aggregate"
    LAST_WINS = "last_wins"
    FIRST_WINS = "first_wins"
    REJECT = "reject"


class IssueSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


class StockStatus(Enum):
    OUT_OF_STOCK = "out_of_stock"     # qty <= 0
    CRITICAL = "critical"             # qty <= critical_threshold
    LOW = "low"                       # qty <= reorder_point
    OK = "ok"


# ---------------- Data-quality ----------------
@dataclass
class DataIssue:
    source: str
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
    # --- low-stock fields ---
    reorder_point: int = 0
    reorder_qty: int = 0
    critical_threshold: int = 0
    lead_time_days: int = 0

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

    @property
    def available_qty(self) -> int:
        """Current on-hand used for stock checks (physical is source of truth)."""
        return self.physical_qty

    @property
    def stock_status(self) -> StockStatus:
        q = self.available_qty
        if q <= 0:
            return StockStatus.OUT_OF_STOCK
        if q <= self.critical_threshold:
            return StockStatus.CRITICAL
        if q <= self.reorder_point:
            return StockStatus.LOW
        return StockStatus.OK

    @property
    def suggested_order_qty(self) -> int:
        """Units to order to reach reorder_point + reorder_qty, never negative."""
        if self.stock_status == StockStatus.OK:
            return 0
        target = self.reorder_point + self.reorder_qty
        return max(0, target - self.available_qty)

    @property
    def suggested_order_value(self) -> float:
        return self.suggested_order_qty * self.unit_cost

    @property
    def days_of_supply(self) -> Optional[float]:
        """Rough days of supply given lead time — None if no lead-time data."""
        if self.lead_time_days <= 0:
            return None
        return round(self.available_qty / max(1, self.reorder_qty / self.lead_time_days), 1)


# ---------------- Low-stock report ----------------
@dataclass
class LowStockReport:
    timestamp: str
    items: List[InventoryItem] = field(default_factory=list)

    def _by_status(self, status: StockStatus) -> List[InventoryItem]:
        return [i for i in self.items if i.stock_status == status]

    @property
    def out_of_stock(self) -> List[InventoryItem]:
        return self._by_status(StockStatus.OUT_OF_STOCK)

    @property
    def critical(self) -> List[InventoryItem]:
        return self._by_status(StockStatus.CRITICAL)

    @property
    def low(self) -> List[InventoryItem]:
        return self._by_status(StockStatus.LOW)

    @property
    def total_reorder_value(self) -> float:
        return sum(i.suggested_order_value for i in self.items)

    def summary(self) -> str:
        lines = [
            "=" * 60,
            f"LOW-STOCK / REORDER REPORT — {self.timestamp}",
            "=" * 60,
            f"Items needing attention : {len(self.items)}",
            f"  Out of stock          : {len(self.out_of_stock)}",
            f"  Critical              : {len(self.critical)}",
            f"  Low                   : {len(self.low)}",
            f"Total reorder value     : ${self.total_reorder_value:,.2f}",
            "-" * 60,
        ]
        if not self.items:
            lines.append("OK: No items below reorder point.")
        else:
            lines.append(
                f"{'SKU':<12}{'Status':<14}{'OnHand':>7}{'ROP':>6}"
                f"{'Crit':>6}{'Order':>7}{'Value':>12}{'Lead':>6}"
            )
            lines.append("-" * 60)
            # Sort: out_of_stock -> critical -> low, then by value desc
            order = {StockStatus.OUT_OF_STOCK: 0, StockStatus.CRITICAL: 1, StockStatus.LOW: 2}
            for item in sorted(
                self.items,
                key=lambda i: (order[i.stock_status], -i.suggested_order_value),
            ):
                lines.append(
                    f"{item.sku:<12}{item.stock_status.value:<14}"
                    f"{item.available_qty:>7}{item.reorder_point:>6}"
                    f"{item.critical_threshold:>6}{item.suggested_order_qty:>7}"
                    f"{item.suggested_order_value:>12,.2f}"
                    f"{item.lead_time_days:>6}"
                )
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_purchase_orders(self, supplier_map: Optional[Dict[str, str]] = None) -> List[dict]:
        """Suggested PO lines grouped by supplier (if provided)."""
        supplier_map = supplier_map or {}
        pos: Dict[str, List[dict]] = {}
        for item in self.items:
            supplier = supplier_map.get(item.sku, "UNASSIGNED")
            pos.setdefault(supplier, []).append({
                "sku": item.sku,
                "description": item.description,
                "order_qty": item.suggested_order_qty,
                "unit_cost": item.unit_cost,
                "line_total": round(item.suggested_order_value, 2),
                "status": item.stock_status.value,
            })
        return [{"supplier": s, "lines": lines} for s, lines in pos.items()]


# ---------------- Reconciliation report (unchanged from v2) ----------------
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


def _coerce_int(value, field_name="qty") -> Tuple[bool, Optional[int], str]:
    if value is None:
        return False, None, f"missing {field_name}"
    if isinstance(value, bool):
        return False, None, f"bool is not a valid {field_name}"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False, None, f"non-numeric {field_name}: {value!r}"
    if f != int(f):
        return False, None, f"fractional {field_name} not allowed: {f}"
    return True, int(f), ""


def _coerce_cost(value) -> Tuple[bool, Optional[float], str]:
    if value is None or value == "":
        return True, 0.0, ""
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
    """Reconciles physical counts against system records with validation + low-stock."""

    def __init__(
        self,
        tolerance: int = 0,
        duplicate_mode: DuplicateMode = DuplicateMode.AGGREGATE,
        default_reorder_point: int = 0,
        default_reorder_qty: int = 0,
        default_critical_threshold: int = 0,
        default_lead_time_days: int = 0,
    ):
        self.tolerance = tolerance
        self.duplicate_mode = duplicate_mode
        self._items: Dict[str, InventoryItem] = {}
        self.data_quality = DataQualityReport()
        self._dup_tracker: Dict[Tuple[str, str], int] = {}
        # defaults applied when a record doesn't specify
        self.defaults = {
            "reorder_point": default_reorder_point,
            "reorder_qty": default_reorder_qty,
            "critical_threshold": default_critical_threshold,
            "lead_time_days": default_lead_time_days,
        }

    # --- internal ---
    def _record_issue(self, source, sku, row_idx, severity, reason, raw):
        self.data_quality.issues.append(
            DataIssue(source, sku, row_idx, severity, reason, raw)
        )

    def _apply_duplicate_policy(self, source, sku, incoming) -> Optional[dict]:
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
            self._items.pop(sku, None)
            return None
        return incoming  # AGGREGATE

    def _apply(self, source, record) -> None:
        sku = record["sku"]
        item = self._items.get(sku)
        if item is None:
            item = InventoryItem(sku=sku)
            # seed low-stock defaults
            item.reorder_point = self.defaults["reorder_point"]
            item.reorder_qty = self.defaults["reorder_qty"]
            item.critical_threshold = self.defaults["critical_threshold"]
            item.lead_time_days = self.defaults["lead_time_days"]
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
            # low-stock params come from the system side (authoritative)
            for key in ("reorder_point", "reorder_qty", "critical_threshold", "lead_time_days"):
                if record.get(key) is not None:
                    setattr(item, key, record[key])
        else:  # physical
            if self.duplicate_mode == DuplicateMode.AGGREGATE and item.physical_qty:
                item.physical_qty += record["qty"]
            else:
                item.physical_qty = record["qty"]
            if record.get("description") and not item.description:
                item.description = record["description"]
            if record.get("unit_cost") and not item.unit_cost:
                item.unit_cost = record["unit_cost"]

    def _ingest(self, source: str, rows: List[dict], require_cost: bool, with_stock_params: bool) -> None:
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
                self._record_issue(source, sku, idx, IssueSeverity.ERROR, f"negative qty: {qty}", raw)
                continue

            ok_cost, cost, cost_err = _coerce_cost(raw.get("unit_cost"))
            if not ok_cost:
                self.data_quality.rejected_rows += 1
                self._record_issue(source, sku, idx, IssueSeverity.ERROR, cost_err, raw)
                continue
            if require_cost and cost == 0.0:
                self._record_issue(source, sku, idx, IssueSeverity.WARNING, "unit_cost missing or zero", raw)

            record = {
                "sku": sku,
                "qty": qty,
                "unit_cost": cost or 0.0,
                "description": str(raw.get("description", "")).strip(),
                "_row": idx,
                "_raw": raw,
            }

            # optional low-stock params on the system side
            if with_stock_params:
                for key, label in (
                    ("reorder_point", "reorder_point"),
                    ("reorder_qty", "reorder_qty"),
                    ("critical_threshold", "critical_threshold"),
                    ("lead_time_days", "lead_time_days"),
                ):
                    if key in raw and raw[key] is not None:
                        ok, val, err = _coerce_int(raw[key], field_name=label)
                        if not ok or val < 0:
                            self._record_issue(
                                source, sku, idx, IssueSeverity.WARNING,
                                err or f"negative {label}: {val}", raw,
                            )
                        else:
                            record[key] = val

            decision = self._apply_duplicate_policy(source, sku, record)
            if decision is None:
                continue
            self._apply(source, decision)
            self.data_quality.accepted_rows += 1

    # --- public API ---
    def load_system_records(self, records: List[dict]) -> "InventoryReconciler":
        self._ingest("system", records, require_cost=True, with_stock_params=True)
        return self

    def load_physical_counts(self, counts: List[dict]) -> "InventoryReconciler":
        self._ingest("physical", counts, require_cost=False, with_stock_params=False)
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

    def low_stock_report(self, include_ok: bool = False) -> LowStockReport:
        """Identify SKUs at or below reorder point (or critical / out of stock)."""
        items = [
            i for i in self._items.values()
            if include_ok or i.stock_status != StockStatus.OK
        ]
        return LowStockReport(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            items=items,
        )

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
        {"sku": "A100", "description": "Widget",      "qty": 100, "unit_cost": 2.50,
         "reorder_point": 40, "reorder_qty": 100, "critical_threshold": 15, "lead_time_days": 7},
        {"sku": "B200", "description": "Gadget",      "qty": 50,  "unit_cost": 10.00,
         "reorder_point": 20, "reorder_qty": 50,  "critical_threshold": 10, "lead_time_days": 14},
        {"sku": "b200", "description": "Gadget dup",  "qty": 5,   "unit_cost": 10.00},  # dup
        {"sku": "C300", "description": "Gizmo",       "qty": 75,  "unit_cost": 5.00,
         "reorder_point": 30, "reorder_qty": 60,  "critical_threshold": 12, "lead_time_days": 5},
        {"sku": "D400", "description": "Doohickey",   "qty": 20,  "unit_cost": 15.00,
         "reorder_point": 25, "reorder_qty": 40,  "critical_threshold": 10, "lead_time_days": 21},
        {"sku": "E500", "description": "Thingamajig", "qty": 200, "unit_cost": 1.25,
         "reorder_point": 50, "reorder_qty": 200, "critical_threshold": 20, "lead_time_days": 3},
        {"sku": "",     "description": "No SKU",      "qty": 5,   "unit_cost": 1.00},
        {"sku": "X900", "description": "Bad qty",     "qty": -3,  "unit_cost": 1.00},
        {"sku": "Y901", "description": "Bad qty 2",   "qty": "abc","unit_cost": 1.00},
        {"sku": "Z902", "description": "Bad cost",    "qty": 10,  "unit_cost": -5.00},
    ]
    physical = [
        {"sku": "A100", "qty": 100},   # OK stock (100 > 40 ROP)
        {"sku": "B200", "qty": 47},    # OK stock
        {"sku": "C300", "qty": 25},    # LOW  (<= ROP 30)
        {"sku": "D400", "qty": 8},     # CRITICAL (<= 10)
        {"sku": "E500", "qty": 0},     # OUT OF STOCK
        {"sku": "F600", "qty": 12, "unit_cost": 3.00},  # new SKU, no ROP -> OK
        {"sku": "A100", "qty": 5},     # dup physical (aggregated -> 105)
        {"sku": "G700", "qty": 7},     # missing cost warning
        {"sku": "H800", "qty": None},  # missing qty -> rejected
    ]

    reconciler = (
        InventoryReconciler(tolerance=0, duplicate_mode=DuplicateMode.AGGREGATE)
        .load_system_records(system)
        .load_physical_counts(physical)
    )

    recon = reconciler.reconcile()
    low = reconciler.low_stock_report()

    print(reconciler.data_quality.summary())
    print()
    print(recon.summary())
    print()
    print(low.summary())
    print()
    print("Suggested Purchase Orders:")
    for po in low.to_purchase_orders(supplier_map={"C300": "ACME Corp", "D400": "ACME Corp", "E500": "GlobalParts"}):
        print(f"  Supplier: {po['supplier']}")
        for line in po["lines"]:
            print(f"    {line}")