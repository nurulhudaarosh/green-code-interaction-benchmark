"""
Inventory Reconciliation System (v4)
- Duplicate + invalid record handling (configurable)
- Reconciliation + low-stock / reorder reporting
- NEW: Boundary & empty-input handling:
    * Empty / None inputs on every loader
    * Empty reconciler (no items loaded)
    * All-zero / all-match inventories
    * Extreme values (huge qty, zero cost, max ints)
    * Tolerance edge cases (negative tolerance, tolerance > variance)
    * Whitespace-only SKUs, control chars, overlong SKUs
    * Reports are safe to print when empty
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Iterable
from datetime import datetime
from enum import Enum
import re
import sys


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
    OUT_OF_STOCK = "out_of_stock"
    CRITICAL = "critical"
    LOW = "low"
    OK = "ok"


# ---------------- Constants / limits ----------------
MAX_QTY = 10 ** 9          # hard cap for a single qty value
MAX_COST = 10 ** 9         # hard cap for unit cost
MAX_ROWS = 1_000_000       # guard against runaway input
SKU_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,31}$")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


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
        ]
        if self.total_rows == 0:
            lines.append("No rows received.")
            lines.append("-" * 60)
            return "\n".join(lines)
        lines.extend([
            f"Total rows examined : {self.total_rows}",
            f"Accepted            : {self.accepted_rows}",
            f"Rejected            : {self.rejected_rows}",
            f"Duplicates resolved : {self.duplicates}",
            f"Total issues        : {len(self.issues)}",
        ])
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
        if self.stock_status == StockStatus.OK:
            return 0
        target = self.reorder_point + self.reorder_qty
        return max(0, target - self.available_qty)

    @property
    def suggested_order_value(self) -> float:
        return self.suggested_order_qty * self.unit_cost


# ---------------- Reports ----------------
@dataclass
class ReconciliationReport:
    timestamp: str
    total_items: int = 0
    matched: int = 0
    discrepancies: List[InventoryItem] = field(default_factory=list)
    total_variance_value: float = 0.0
    tolerance: int = 0
    is_empty: bool = False

    def summary(self) -> str:
        lines = [
            "=" * 60,
            f"INVENTORY RECONCILIATION REPORT — {self.timestamp}",
            "=" * 60,
        ]
        if self.is_empty:
            lines.append("No inventory loaded — nothing to reconcile.")
            lines.append("=" * 60)
            return "\n".join(lines)

        lines.extend([
            f"Total SKUs reviewed : {self.total_items}",
            f"Matched             : {self.matched}",
            f"Discrepancies       : {len(self.discrepancies)}",
            f"Net variance value  : ${self.total_variance_value:,.2f}",
            f"Tolerance threshold : ±{self.tolerance} units",
            "-" * 60,
        ])
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


@dataclass
class LowStockReport:
    timestamp: str
    items: List[InventoryItem] = field(default_factory=list)
    is_empty: bool = False

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
        ]
        if self.is_empty:
            lines.append("No inventory loaded — no low-stock items.")
            lines.append("=" * 60)
            return "\n".join(lines)

        lines.extend([
            f"Items needing attention : {len(self.items)}",
            f"  Out of stock          : {len(self.out_of_stock)}",
            f"  Critical              : {len(self.critical)}",
            f"  Low                   : {len(self.low)}",
            f"Total reorder value     : ${self.total_reorder_value:,.2f}",
            "-" * 60,
        ])
        if not self.items:
            lines.append("OK: No items below reorder point.")
        else:
            lines.append(
                f"{'SKU':<12}{'Status':<14}{'OnHand':>7}{'ROP':>6}"
                f"{'Crit':>6}{'Order':>7}{'Value':>12}{'Lead':>6}"
            )
            lines.append("-" * 60)
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
        if not self.items:
            return []
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


# ---------------- Validation helpers ----------------
def _coerce_int(value, field_name="qty", max_value: int = MAX_QTY) -> Tuple[bool, Optional[int], str]:
    """Parse an int with boundary checks. Returns (ok, value, reason)."""
    if value is None:
        return False, None, f"missing {field_name}"
    if isinstance(value, bool):
        return False, None, f"bool is not a valid {field_name}"
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return False, None, f"non-finite {field_name}: {value}"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False, None, f"non-numeric {field_name}: {value!r}"
    if f != int(f):
        return False, None, f"fractional {field_name} not allowed: {f}"
    i = int(f)
    if i > max_value:
        return False, None, f"{field_name} exceeds limit ({i} > {max_value})"
    return True, i, ""


def _coerce_cost(value, max_value: float = MAX_COST) -> Tuple[bool, Optional[float], str]:
    if value is None or value == "":
        return True, 0.0, ""
    if isinstance(value, bool):
        return False, None, "bool is not a valid cost"
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return False, None, f"non-finite cost: {value}"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False, None, f"non-numeric cost: {value!r}"
    if f < 0:
        return False, None, f"negative unit_cost: {f}"
    if f > max_value:
        return False, None, f"unit_cost exceeds limit ({f} > {max_value})"
    return True, f, ""


def _validate_sku(raw) -> Tuple[bool, Optional[str], str]:
    if raw is None:
        return False, None, "missing sku"
    if not isinstance(raw, (str, int, float)):
        return False, None, f"invalid sku type: {type(raw).__name__}"
    s = str(raw).strip()
    if s == "":
        return False, None, "blank sku"
    if CONTROL_CHAR_RE.search(s):
        return False, None, "sku contains control characters"
    if len(s) > 32:
        return False, None, f"sku too long ({len(s)} > 32)"
    s = s.upper()
    if not SKU_RE.match(s):
        return False, None, f"invalid sku format: {raw!r}"
    return True, s, ""


# ---------------- Reconciler ----------------
class InventoryReconciler:
    def __init__(
        self,
        tolerance: int = 0,
        duplicate_mode: DuplicateMode = DuplicateMode.AGGREGATE,
        default_reorder_point: int = 0,
        default_reorder_qty: int = 0,
        default_critical_threshold: int = 0,
        default_lead_time_days: int = 0,
    ):
        # Normalize tolerance: negative -> 0, non-int -> 0
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            tolerance = 0
        self.tolerance = max(0, int(tolerance))
        if not isinstance(duplicate_mode, DuplicateMode):
            raise TypeError("duplicate_mode must be a DuplicateMode")
        self.duplicate_mode = duplicate_mode

        self._items: Dict[str, InventoryItem] = {}
        self.data_quality = DataQualityReport()
        self._dup_tracker: Dict[Tuple[str, str], int] = {}
        self.defaults = {
            "reorder_point": max(0, int(default_reorder_point or 0)),
            "reorder_qty": max(0, int(default_reorder_qty or 0)),
            "critical_threshold": max(0, int(default_critical_threshold or 0)),
            "lead_time_days": max(0, int(default_lead_time_days or 0)),
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
        return incoming

    def _apply(self, source, record) -> None:
        sku = record["sku"]
        item = self._items.get(sku)
        if item is None:
            item = InventoryItem(sku=sku)
            item.reorder_point = self.defaults["reorder_point"]
            item.reorder_qty = self.defaults["reorder_qty"]
            item.critical_threshold = self.defaults["critical_threshold"]
            item.lead_time_days = self.defaults["lead_time_days"]
            self._items[sku] = item

        if source == "system":
            if self.duplicate_mode == DuplicateMode.AGGREGATE and item.system_qty:
                # clamp to avoid overflow
                item.system_qty = min(MAX_QTY, item.system_qty + record["qty"])
            else:
                item.system_qty = record["qty"]
            if record.get("description"):
                item.description = record["description"]
            if record.get("unit_cost"):
                item.unit_cost = record["unit_cost"]
            for key in ("reorder_point", "reorder_qty", "critical_threshold", "lead_time_days"):
                if record.get(key) is not None:
                    setattr(item, key, record[key])
        else:
            if self.duplicate_mode == DuplicateMode.AGGREGATE and item.physical_qty:
                item.physical_qty = min(MAX_QTY, item.physical_qty + record["qty"])
            else:
                item.physical_qty = record["qty"]
            if record.get("description") and not item.description:
                item.description = record["description"]
            if record.get("unit_cost") and not item.unit_cost:
                item.unit_cost = record["unit_cost"]

    def _normalize_rows(self, rows) -> List[dict]:
        """Coerce various input shapes to a list of dicts; reject bad containers."""
        if rows is None:
            return []
        if isinstance(rows, dict):
            return [rows]
        if isinstance(rows, (str, bytes)):
            return []
        if not isinstance(rows, Iterable):
            return []
        out: List[dict] = []
        for r in rows:
            if not isinstance(r, dict):
                # Represent non-dict rows as a synthetic dict so we can log + reject
                out.append({"_invalid_row": r})
            else:
                out.append(r)
            if len(out) > MAX_ROWS:
                # Guard: truncate and flag once
                break
        return out

    def _ingest(self, source: str, rows, require_cost: bool, with_stock_params: bool) -> None:
        rows = self._normalize_rows(rows)
        if len(rows) >= MAX_ROWS:
            self._record_issue(
                source, None, -1, IssueSeverity.ERROR,
                f"input exceeded MAX_ROWS ({MAX_ROWS}); truncated", {},
            )
        for idx, raw in enumerate(rows):
            self.data_quality.total_rows += 1

            if "_invalid_row" in raw:
                self.data_quality.rejected_rows += 1
                self._record_issue(
                    source, None, idx, IssueSeverity.ERROR,
                    f"row is not a dict: {type(raw['_invalid_row']).__name__}", {},
                )
                continue

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
                "description": str(raw.get("description", "")).strip()[:200],
                "_row": idx,
                "_raw": raw,
            }

            if with_stock_params:
                for key in ("reorder_point", "reorder_qty", "critical_threshold", "lead_time_days"):
                    if key in raw and raw[key] is not None:
                        ok, val, err = _coerce_int(raw[key], field_name=key)
                        if not ok or val < 0:
                            self._record_issue(
                                source, sku, idx, IssueSeverity.WARNING,
                                err or f"negative {key}: {val}", raw,
                            )
                        else:
                            record[key] = val

            decision = self._apply_duplicate_policy(source, sku, record)
            if decision is None:
                continue
            self._apply(source, decision)
            self.data_quality.accepted_rows += 1

    # --- public API ---
    def load_system_records(self, records) -> "InventoryReconciler":
        self._ingest("system", records, require_cost=True, with_stock_params=True)
        return self

    def load_physical_counts(self, counts) -> "InventoryReconciler":
        self._ingest("physical", counts, require_cost=False, with_stock_params=False)
        return self

    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0

    def reconcile(self) -> ReconciliationReport:
        report = ReconciliationReport(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            tolerance=self.tolerance,
            is_empty=self.is_empty,
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
        items = [
            i for i in self._items.values()
            if include_ok or i.stock_status != StockStatus.OK
        ]
        return LowStockReport(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            items=items,
            is_empty=self.is_empty,
        )

    def adjustments(self, report: ReconciliationReport) -> List[dict]:
        if report.is_empty:
            return []
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
def _demo_edge_cases():
    """Exercise boundary/empty scenarios; should never raise."""
    cases = [
        ("empty everything", [], []),
        ("None inputs", None, None),
        ("only system", [{"sku": "A1", "qty": 5, "unit_cost": 1.0}], None),
        ("only physical", None, [{"sku": "A1", "qty": 5}]),
        ("all match", [{"sku": "A1", "qty": 5, "unit_cost": 1.0}], [{"sku": "A1", "qty": 5}]),
        ("zero everything", [{"sku": "A1", "qty": 0, "unit_cost": 0.0}], [{"sku": "A1", "qty": 0}]),
        ("huge qty over cap", [{"sku": "A1", "qty": 10**12, "unit_cost": 1.0}], []),
        ("huge cost over cap", [{"sku": "A1", "qty": 1, "unit_cost": 10**12}], []),
        ("nan/inf", [{"sku": "A1", "qty": float("nan"), "unit_cost": float("inf")}], []),
        ("whitespace sku", [{"sku": "   ", "qty": 1}], []),
        ("control char sku", [{"sku": "A\x00B", "qty": 1}], []),
        ("overlong sku", [{"sku": "X" * 64, "qty": 1}], []),
        ("non-dict row", ["not a dict", 42], []),
        ("tolerance > variance", [{"sku": "A1", "qty": 100, "unit_cost": 1.0}], [{"sku": "A1", "qty": 99}]),
        ("tolerance zero, tiny variance", [{"sku": "A1", "qty": 1, "unit_cost": 1.0}], [{"sku": "A1", "qty": 0}]),
    ]
    for label, sys_rows, phys_rows in cases:
        print(f"\n### CASE: {label} ###")
        try:
            r = (
                InventoryReconciler(tolerance=0)
                .load_system_records(sys_rows)
                .load_physical_counts(phys_rows)
            )
            recon = r.reconcile()
            low = r.low_stock_report()
            print(r.data_quality.summary())
            print(recon.summary())
            print(low.summary())
        except Exception as e:  # pragma: no cover
            print(f"!! UNHANDLED EXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)


if __name__ == "__main__":
    # Smoke-test guards first
    assert InventoryReconciler(tolerance=-5).tolerance == 0
    assert InventoryReconciler(tolerance="abc").tolerance == 0
    try:
        InventoryReconciler(duplicate_mode="aggregate")
        raise AssertionError("expected TypeError for bad duplicate_mode")
    except TypeError:
        pass

    _demo_edge_cases()

    print("\n" + "=" * 60)
    print("MAIN DEMO (mixed valid + invalid + duplicates)")
    print("=" * 60)
    system = [
        {"sku": "A100", "description": "Widget", "qty": 100, "unit_cost": 2.50,
         "reorder_point": 40, "reorder_qty": 100, "critical_threshold": 15, "lead_time_days": 7},
        {"sku": "B200", "description": "Gadget", "qty": 50, "unit_cost": 10.00,
         "reorder_point": 20, "reorder_qty": 50, "critical_threshold": 10, "lead_time_days": 14},
        {"sku": "b200", "qty": 5, "unit_cost": 10.00},   # duplicate
        {"sku": "", "qty": 5, "unit_cost": 1.00},         # rejected
        {"sku": "X900", "qty": -3, "unit_cost": 1.00},    # rejected
    ]
    physical = [
        {"sku": "A100", "qty": 100},
        {"sku": "B200", "qty": 47},
        {"sku": "A100", "qty": 5},    # duplicate, aggregated
        {"sku": "H800", "qty": None}, # rejected
    ]
    r = (
        InventoryReconciler(tolerance=0, duplicate_mode=DuplicateMode.AGGREGATE)
        .load_system_records(system)
        .load_physical_counts(physical)
    )
    print(r.data_quality.summary())
    print()
    print(r.reconcile().summary())
    print()
    print(r.low_stock_report().summary())