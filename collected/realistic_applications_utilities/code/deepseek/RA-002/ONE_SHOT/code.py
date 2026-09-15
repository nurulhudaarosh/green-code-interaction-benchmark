"""
Inventory Reconciliation System
Implements: stock tracking, cycle counts, variance detection, adjustments,
shrinkage analysis, reconciliation reports, and audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import uuid


# ============================================================
# Enums & Constants
# ============================================================

class MovementType(Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    DAMAGE = "damage"
    SHRINKAGE = "shrinkage"
    CYCLE_COUNT = "cycle_count"


class VarianceReason(Enum):
    UNKNOWN = "unknown"
    THEFT = "theft"
    DAMAGE = "damage"
    MISCOUNT = "miscount"
    DATA_ENTRY = "data_entry"
    SUPPLIER_ERROR = "supplier_error"
    RECEIVING_ERROR = "receiving_error"


class VarianceSeverity(Enum):
    NEGLIGIBLE = "negligible"   # < 1% and < 5 units
    MINOR = "minor"             # < 2% or < 20 units
    MAJOR = "major"             # < 5% or < 100 units
    CRITICAL = "critical"       # >= 5% or >= 100 units


# ============================================================
# Data Models
# ============================================================

@dataclass
class InventoryItem:
    sku: str
    name: str
    unit_cost: float
    reorder_point: int = 0
    system_qty: int = 0
    counted_qty: Optional[int] = None
    last_counted: Optional[datetime] = None

    @property
    def variance(self) -> int:
        if self.counted_qty is None:
            return 0
        return self.counted_qty - self.system_qty

    @property
    def variance_pct(self) -> float:
        if self.system_qty == 0:
            return 0.0 if self.counted_qty == 0 else 100.0
        return (self.variance / self.system_qty) * 100

    @property
    def variance_value(self) -> float:
        return self.variance * self.unit_cost


@dataclass
class Movement:
    movement_id: str
    sku: str
    movement_type: MovementType
    quantity: int
    timestamp: datetime
    reference: str = ""
    notes: str = ""
    user: str = "system"


@dataclass
class Adjustment:
    adjustment_id: str
    sku: str
    quantity_change: int
    reason: VarianceReason
    timestamp: datetime
    approved_by: str
    notes: str = ""


@dataclass
class ReconciliationRecord:
    record_id: str
    sku: str
    system_qty: int
    counted_qty: int
    variance: int
    variance_pct: float
    variance_value: float
    severity: VarianceSeverity
    reason: VarianceReason
    timestamp: datetime
    status: str = "pending"  # pending, approved, rejected


@dataclass
class AuditEntry:
    entry_id: str
    action: str
    sku: str
    details: str
    timestamp: datetime
    user: str


# ============================================================
# Reconciliation Engine
# ============================================================

class InventoryReconciliation:
    def __init__(self):
        self.items: Dict[str, InventoryItem] = {}
        self.movements: List[Movement] = []
        self.adjustments: List[Adjustment] = []
        self.records: List[ReconciliationRecord] = []
        self.audit_log: List[AuditEntry] = []
        self.thresholds = {
            "negligible_pct": 1.0, "negligible_units": 5,
            "minor_pct": 2.0, "minor_units": 20,
            "major_pct": 5.0, "major_units": 100,
        }

    # ---------- Audit ----------
    def _audit(self, action: str, sku: str, details: str, user: str = "system"):
        self.audit_log.append(AuditEntry(
            entry_id=str(uuid.uuid4()), action=action, sku=sku,
            details=details, timestamp=datetime.now(), user=user
        ))

    # ---------- Item management ----------
    def add_item(self, sku: str, name: str, unit_cost: float,
                 initial_qty: int = 0, reorder_point: int = 0):
        if sku in self.items:
            raise ValueError(f"SKU {sku} already exists")
        self.items[sku] = InventoryItem(
            sku=sku, name=name, unit_cost=unit_cost,
            system_qty=initial_qty, reorder_point=reorder_point
        )
        self._audit("ITEM_ADDED", sku, f"Initial qty={initial_qty}")
        if initial_qty:
            self.record_movement(sku, MovementType.RECEIPT, initial_qty,
                                 reference="initial_stock")

    # ---------- Movements ----------
    def record_movement(self, sku: str, mtype: MovementType, qty: int,
                        reference: str = "", notes: str = "",
                        user: str = "system") -> Movement:
        if sku not in self.items:
            raise KeyError(f"Unknown SKU: {sku}")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        item = self.items[sku]
        signed = qty
        if mtype in (MovementType.SALE, MovementType.TRANSFER_OUT,
                     MovementType.DAMAGE, MovementType.SHRINKAGE):
            signed = -qty

        item.system_qty += signed
        mv = Movement(movement_id=str(uuid.uuid4()), sku=sku,
                      movement_type=mtype, quantity=signed,
                      timestamp=datetime.now(), reference=reference,
                      notes=notes, user=user)
        self.movements.append(mv)
        self._audit("MOVEMENT", sku,
                    f"{mtype.value} {signed:+d}, new={item.system_qty}", user)
        return mv

    def record_cycle_count(self, sku: str, counted_qty: int,
                           user: str = "system") -> InventoryItem:
        if sku not in self.items:
            raise KeyError(f"Unknown SKU: {sku}")
        item = self.items[sku]
        item.counted_qty = counted_qty
        item.last_counted = datetime.now()
        self._audit("CYCLE_COUNT", sku,
                    f"counted={counted_qty}, system={item.system_qty}", user)
        return item

    # ---------- Variance analysis ----------
    def _classify_severity(self, variance_pct: float, variance_units: int) -> VarianceSeverity:
        abs_pct = abs(variance_pct)
        abs_units = abs(variance_units)
        t = self.thresholds
        if abs_pct >= t["major_pct"] or abs_units >= t["major_units"]:
            return VarianceSeverity.CRITICAL
        if abs_pct >= t["minor_pct"] or abs_units >= t["minor_units"]:
            return VarianceSeverity.MAJOR
        if abs_pct >= t["negligible_pct"] or abs_units >= t["negligible_units"]:
            return VarianceSeverity.MINOR
        return VarianceSeverity.NEGLIGIBLE

    def analyze_variance(self, sku: str) -> Optional[ReconciliationRecord]:
        item = self.items.get(sku)
        if not item or item.counted_qty is None:
            return None
        severity = self._classify_severity(item.variance_pct, item.variance)
        record = ReconciliationRecord(
            record_id=str(uuid.uuid4()), sku=sku,
            system_qty=item.system_qty, counted_qty=item.counted_qty,
            variance=item.variance, variance_pct=item.variance_pct,
            variance_value=item.variance_value, severity=severity,
            reason=VarianceReason.UNKNOWN, timestamp=datetime.now(),
        )
        self.records.append(record)
        self._audit("VARIANCE_ANALYZED", sku,
                    f"var={item.variance}, sev={severity.value}")
        return record

    def reconcile(self, sku: str, reason: VarianceReason = VarianceReason.UNKNOWN,
                  approve: bool = False, user: str = "system") -> ReconciliationRecord:
        """Reconcile a single SKU: create adjustment for the variance."""
        item = self.items[sku]
        if item.counted_qty is None:
            raise ValueError(f"No cycle count for {sku}")

        record = self.analyze_variance(sku)
        record.reason = reason
        record.status = "approved" if approve else "pending"

        if approve and item.variance != 0:
            adj = Adjustment(
                adjustment_id=str(uuid.uuid4()), sku=sku,
                quantity_change=item.variance, reason=reason,
                timestamp=datetime.now(), approved_by=user,
                notes=f"Reconciliation {record.record_id}",
            )
            self.adjustments.append(adj)
            item.system_qty = item.counted_qty
            self.record_movement(sku, MovementType.ADJUSTMENT,
                                 abs(item.variance),
                                 reference=record.record_id,
                                 notes=f"Reconcile {reason.value}",
                                 user=user)
            # fix sign for ADJUSTMENT recorded as positive
            # (record_movement adds positive; we already set system_qty)
            self._audit("RECONCILED", sku,
                        f"adj={item.variance:+d}, reason={reason.value}", user)

        item.counted_qty = None  # clear count after reconciliation
        return record

    def reconcile_all(self, reason_map: Optional[Dict[str, VarianceReason]] = None,
                      auto_approve_severities: Tuple[VarianceSeverity, ...] =
                      (VarianceSeverity.NEGLIGIBLE, VarianceSeverity.MINOR),
                      user: str = "system") -> List[ReconciliationRecord]:
        results = []
        for sku, item in list(self.items.items()):
            if item.counted_qty is None:
                continue
            reason = (reason_map or {}).get(sku, VarianceReason.UNKNOWN)
            sev = self._classify_severity(item.variance_pct, item.variance)
            approve = sev in auto_approve_severities
            results.append(self.reconcile(sku, reason, approve=approve, user=user))
        return results

    # ---------- Shrinkage & KPIs ----------
    def shrinkage_report(self) -> Dict:
        shrink = [a for a in self.adjustments
                  if a.reason in (VarianceReason.THEFT, VarianceReason.DAMAGE)]
        total_units = sum(abs(a.quantity_change) for a in shrink)
        total_value = sum(abs(a.quantity_change) * self.items[a.sku].unit_cost
                          for a in shrink)
        by_reason: Dict[str, Dict] = {}
        for a in shrink:
            r = a.reason.value
            by_reason.setdefault(r, {"units": 0, "value": 0.0})
            by_reason[r]["units"] += abs(a.quantity_change)
            by_reason[r]["value"] += abs(a.quantity_change) * self.items[a.sku].unit_cost
        return {"total_units": total_units, "total_value": round(total_value, 2),
                "by_reason": by_reason, "adjustment_count": len(shrink)}

    def accuracy_metrics(self) -> Dict:
        if not self.records:
            return {"record_count": 0}
        total = len(self.records)
        accurate = sum(1 for r in self.records if r.variance == 0)
        by_sev = {s.value: 0 for s in VarianceSeverity}
        for r in self.records:
            by_sev[r.severity.value] += 1
        abs_var_value = sum(abs(r.variance_value) for r in self.records)
        return {
            "record_count": total,
            "accurate_records": accurate,
            "accuracy_pct": round(accurate / total * 100, 2),
            "by_severity": by_sev,
            "total_abs_variance_value": round(abs_var_value, 2),
        }

    # ---------- Reports ----------
    def inventory_value(self) -> float:
        return round(sum(i.system_qty * i.unit_cost for i in self.items.values()), 2)

    def low_stock_items(self) -> List[InventoryItem]:
        return [i for i in self.items.values()
                if i.system_qty <= i.reorder_point]

    def reconciliation_report(self) -> Dict:
        return {
            "generated_at": datetime.now().isoformat(),
            "items": len(self.items),
            "inventory_value": self.inventory_value(),
            "movements": len(self.movements),
            "adjustments": len(self.adjustments),
            "reconciliation_records": len(self.records),
            "accuracy": self.accuracy_metrics(),
            "shrinkage": self.shrinkage_report(),
            "low_stock": [i.sku for i in self.low_stock_items()],
            "pending_reconciliations": [
                r.record_id for r in self.records if r.status == "pending"
            ],
        }

    def audit_trail(self, sku: Optional[str] = None) -> List[AuditEntry]:
        if sku:
            return [e for e in self.audit_log if e.sku == sku]
        return list(self.audit_log)


# ============================================================
# Demo / Tests
# ============================================================

def _demo():
    rec = InventoryReconciliation()

    # Setup items
    rec.add_item("SKU001", "Widget A", 10.00, initial_qty=100, reorder_point=20)
    rec.add_item("SKU002", "Widget B", 25.50, initial_qty=50, reorder_point=10)
    rec.add_item("SKU003", "Gadget C", 5.75, initial_qty=200, reorder_point=50)

    # Normal movements
    rec.record_movement("SKU001", MovementType.SALE, 15, reference="SO-1001")
    rec.record_movement("SKU001", MovementType.RECEIPT, 50, reference="PO-2001")
    rec.record_movement("SKU002", MovementType.SALE, 10, reference="SO-1002")
    rec.record_movement("SKU002", MovementType.RETURN, 2, reference="RMA-01")
    rec.record_movement("SKU003", MovementType.DAMAGE, 5, notes="Forklift damage")
    rec.record_movement("SKU003", MovementType.TRANSFER_OUT, 20, reference="TR-01")

    # Cycle counts
    rec.record_cycle_count("SKU001", 134)   # system 135 -> -1 (negligible)
    rec.record_cycle_count("SKU002", 35)    # system 42 -> -7 (major)
    rec.record_cycle_count("SKU003", 170)   # system 175 -> -5 (minor)

    # Reconcile all (auto-approve negligible + minor)
    results = rec.reconcile_all(reason_map={
        "SKU002": VarianceReason.THEFT,
        "SKU003": VarianceReason.DAMAGE,
        "SKU001": VarianceReason.MISCOUNT,
    }, user="auditor_01")

    print("=== Reconciliation Results ===")
    for r in results:
        print(f"  {r.sku}: sys={r.system_qty} counted={r.counted_qty} "
              f"var={r.variance:+d} ({r.variance_pct:+.2f}%) "
              f"sev={r.severity.value} status={r.status}")

    # Manually approve SKU002 (major/theft)
    rec.reconcile("SKU002", VarianceReason.THEFT, approve=True, user="manager_01")

    print("\n=== Full Report ===")
    report = rec.reconciliation_report()
    for k, v in report.items():
        print(f"  {k}: {v}")

    print("\n=== Audit Trail (SKU002) ===")
    for e in rec.audit_trail("SKU002"):
        print(f"  [{e.timestamp.strftime('%H:%M:%S')}] {e.action}: {e.details}")

    return rec


if __name__ == "__main__":
    _demo()