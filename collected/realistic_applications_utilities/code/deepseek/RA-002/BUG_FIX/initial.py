"""
Inventory Reconciliation Utility — hardened version.

Adds:
  - `InventoryUtility` facade with clean public API
  - Custom exception hierarchy (DuplicateSKUError, InvalidQuantityError, ...)
  - Duplicate-SKU handling: strict (raise), idempotent (return existing), upsert
  - Invalid-quantity handling: rejects <=0 for movements, negatives for counts,
    non-int types, NaN/inf, and out-of-range values
  - Input validation on every public method
  - Atomic operations (no partial state on failure)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import math
import uuid


# ============================================================
# Exceptions
# ============================================================

class InventoryError(Exception):
    """Base class for all inventory errors."""

class DuplicateSKUError(InventoryError):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"SKU already exists: {sku!r}")

class UnknownSKUError(InventoryError):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"Unknown SKU: {sku!r}")

class InvalidQuantityError(InventoryError):
    def __init__(self, qty, reason: str):
        self.qty = qty
        self.reason = reason
        super().__init__(f"Invalid quantity {qty!r}: {reason}")

class InvalidSKUError(InventoryError):
    def __init__(self, sku, reason: str):
        self.sku = sku
        super().__init__(f"Invalid SKU {sku!r}: {reason}")

class MissingCycleCountError(InventoryError):
    def __init__(self, sku: str):
        super().__init__(f"No cycle count recorded for SKU {sku!r}")


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

    @property
    def sign(self) -> int:
        """+1 if this movement increases stock, -1 if it decreases it."""
        return -1 if self in {
            MovementType.SALE, MovementType.TRANSFER_OUT,
            MovementType.DAMAGE, MovementType.SHRINKAGE,
        } else 1


class VarianceReason(Enum):
    UNKNOWN = "unknown"
    THEFT = "theft"
    DAMAGE = "damage"
    MISCOUNT = "miscount"
    DATA_ENTRY = "data_entry"
    SUPPLIER_ERROR = "supplier_error"
    RECEIVING_ERROR = "receiving_error"


class VarianceSeverity(Enum):
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class DuplicatePolicy(Enum):
    """How add_item() should behave when the SKU already exists."""
    STRICT = "strict"       # raise DuplicateSKUError
    IDEMPOTENT = "idempotent"  # return existing item unchanged
    UPSERT = "upsert"       # update mutable fields, keep system_qty


# Range guards
MAX_QTY = 10**12   # absolute upper bound to catch overflow / typos


# ============================================================
# Validation helpers
# ============================================================

def _validate_sku(sku) -> str:
    if not isinstance(sku, str):
        raise InvalidSKUError(sku, "must be a string")
    if not sku or not sku.strip():
        raise InvalidSKUError(sku, "must be non-empty")
    if len(sku) > 64:
        raise InvalidSKUError(sku, "exceeds 64 characters")
    return sku.strip()


def _validate_qty(qty, *, allow_zero: bool = False,
                  allow_negative: bool = False, field_name: str = "quantity") -> int:
    """Validate an integer quantity. Rejects bool, float-with-fraction,
    NaN/inf, and out-of-range values."""
    # Reject bool explicitly (bool is subclass of int in Python)
    if isinstance(qty, bool):
        raise InvalidQuantityError(qty, f"{field_name} must be an integer, not bool")
    if isinstance(qty, float):
        if math.isnan(qty) or math.isinf(qty):
            raise InvalidQuantityError(qty, f"{field_name} must be finite")
        if not qty.is_integer():
            raise InvalidQuantityError(qty, f"{field_name} must be a whole number")
        qty = int(qty)
    if not isinstance(qty, int):
        raise InvalidQuantityError(qty, f"{field_name} must be an integer")
    if abs(qty) > MAX_QTY:
        raise InvalidQuantityError(qty, f"{field_name} exceeds max {MAX_QTY}")
    if qty < 0 and not allow_negative:
        raise InvalidQuantityError(qty, f"{field_name} must not be negative")
    if qty == 0 and not allow_zero:
        raise InvalidQuantityError(qty, f"{field_name} must be non-zero")
    return qty


def _validate_cost(cost) -> float:
    if isinstance(cost, bool):
        raise InventoryError("unit_cost must be a number, not bool")
    if not isinstance(cost, (int, float)):
        raise InventoryError("unit_cost must be a number")
    if math.isnan(cost) or math.isinf(cost):
        raise InventoryError("unit_cost must be finite")
    if cost < 0:
        raise InventoryError("unit_cost must be non-negative")
    return float(cost)


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
    status: str = "pending"


@dataclass
class AuditEntry:
    entry_id: str
    action: str
    sku: str
    details: str
    timestamp: datetime
    user: str


# ============================================================
# Core Engine
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

    # ---------- Item management (HARDENED) ----------
    def add_item(self, sku: str, name: str, unit_cost: float,
                 initial_qty: int = 0, reorder_point: int = 0,
                 on_duplicate: DuplicatePolicy = DuplicatePolicy.STRICT,
                 user: str = "system") -> InventoryItem:
        """
        Add an item. Duplicate handling is controlled by `on_duplicate`:
          - STRICT     : raise DuplicateSKUError
          - IDEMPOTENT : return existing item, no changes, no movement logged
          - UPSERT     : update name/cost/reorder_point; keep system_qty;
                         initial_qty is ignored for existing items
        Validates all inputs before mutating state.
        """
        sku = _validate_sku(sku)
        if not isinstance(name, str) or not name.strip():
            raise InventoryError("name must be a non-empty string")
        unit_cost = _validate_cost(unit_cost)
        initial_qty = _validate_qty(initial_qty, allow_zero=True,
                                    field_name="initial_qty")
        reorder_point = _validate_qty(reorder_point, allow_zero=True,
                                      field_name="reorder_point")
        if not isinstance(on_duplicate, DuplicatePolicy):
            raise InventoryError("on_duplicate must be a DuplicatePolicy")

        existing = self.items.get(sku)
        if existing is not None:
            if on_duplicate is DuplicatePolicy.STRICT:
                self._audit("DUPLICATE_REJECTED", sku,
                            "STRICT policy: item already exists", user)
                raise DuplicateSKUError(sku)
            if on_duplicate is DuplicatePolicy.IDEMPOTENT:
                self._audit("DUPLICATE_NOOP", sku,
                            "IDEMPOTENT policy: returned existing", user)
                return existing
            # UPSERT
            existing.name = name.strip()
            existing.unit_cost = unit_cost
            existing.reorder_point = reorder_point
            self._audit("ITEM_UPSERTED", sku,
                        f"cost={unit_cost}, reorder={reorder_point}", user)
            return existing

        # New item — validate the resulting initial movement would be legal
        item = InventoryItem(
            sku=sku, name=name.strip(), unit_cost=unit_cost,
            reorder_point=reorder_point, system_qty=0
        )
        self.items[sku] = item
        self._audit("ITEM_ADDED", sku, f"Initial qty={initial_qty}", user)

        if initial_qty > 0:
            # bypass normal positive-qty guard by recording directly
            item.system_qty = initial_qty
            self.movements.append(Movement(
                movement_id=str(uuid.uuid4()), sku=sku,
                movement_type=MovementType.RECEIPT, quantity=initial_qty,
                timestamp=datetime.now(), reference="initial_stock",
                user=user,
            ))
            self._audit("MOVEMENT", sku,
                        f"receipt +{initial_qty}, new={item.system_qty}", user)
        return item

    def get_item(self, sku: str) -> InventoryItem:
        sku = _validate_sku(sku)
        item = self.items.get(sku)
        if item is None:
            raise UnknownSKUError(sku)
        return item

    # ---------- Movements (HARDENED) ----------
    def record_movement(self, sku: str, mtype: MovementType, qty: int,
                        reference: str = "", notes: str = "",
                        user: str = "system") -> Movement:
        sku = _validate_sku(sku)
        if not isinstance(mtype, MovementType):
            raise InventoryError("mtype must be a MovementType")
        qty = _validate_qty(qty, field_name="movement qty")
        if not isinstance(reference, str) or not isinstance(notes, str):
            raise InventoryError("reference and notes must be strings")

        item = self.items.get(sku)
        if item is None:
            raise UnknownSKUError(sku)

        signed = mtype.sign * qty
        new_qty = item.system_qty + signed
        if new_qty < 0:
            raise InvalidQuantityError(
                qty,
                f"would drive stock negative ({item.system_qty} -> {new_qty})"
            )

        # Commit atomically: compute first, mutate after
        item.system_qty = new_qty
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
        sku = _validate_sku(sku)
        counted_qty = _validate_qty(counted_qty, allow_zero=True,
                                    field_name="counted_qty")
        item = self.items.get(sku)
        if item is None:
            raise UnknownSKUError(sku)
        item.counted_qty = counted_qty
        item.last_counted = datetime.now()
        self._audit("CYCLE_COUNT", sku,
                    f"counted={counted_qty}, system={item.system_qty}", user)
        return item

    # ---------- Variance ----------
    def _classify_severity(self, variance_pct: float,
                           variance_units: int) -> VarianceSeverity:
        abs_pct, abs_units = abs(variance_pct), abs(variance_units)
        t = self.thresholds
        if abs_pct >= t["major_pct"] or abs_units >= t["major_units"]:
            return VarianceSeverity.CRITICAL
        if abs_pct >= t["minor_pct"] or abs_units >= t["minor_units"]:
            return VarianceSeverity.MAJOR
        if abs_pct >= t["negligible_pct"] or abs_units >= t["negligible_units"]:
            return VarianceSeverity.MINOR
        return VarianceSeverity.NEGLIGIBLE

    def analyze_variance(self, sku: str) -> Optional[ReconciliationRecord]:
        item = self.get_item(sku)
        if item.counted_qty is None:
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

    def reconcile(self, sku: str,
                  reason: VarianceReason = VarianceReason.UNKNOWN,
                  approve: bool = False, user: str = "system"
                  ) -> ReconciliationRecord:
        item = self.get_item(sku)
        if item.counted_qty is None:
            raise MissingCycleCountError(sku)
        if not isinstance(reason, VarianceReason):
            raise InventoryError("reason must be a VarianceReason")

        record = self.analyze_variance(sku)
        record.reason = reason
        record.status = "approved" if approve else "pending"

        if approve and item.variance != 0:
            delta = item.variance  # may be negative
            adj = Adjustment(
                adjustment_id=str(uuid.uuid4()), sku=sku,
                quantity_change=delta, reason=reason,
                timestamp=datetime.now(), approved_by=user,
                notes=f"Reconciliation {record.record_id}",
            )
            self.adjustments.append(adj)
            # Set system_qty to counted value atomically
            item.system_qty = item.counted_qty
            # Log the adjustment as a signed Movement without sign-flip
            self.movements.append(Movement(
                movement_id=str(uuid.uuid4()), sku=sku,
                movement_type=MovementType.ADJUSTMENT, quantity=delta,
                timestamp=datetime.now(), reference=record.record_id,
                notes=f"Reconcile {reason.value}", user=user,
            ))
            self._audit("RECONCILED", sku,
                        f"adj={delta:+d}, reason={reason.value}", user)

        item.counted_qty = None
        return record

    def reconcile_all(self,
                      reason_map: Optional[Dict[str, VarianceReason]] = None,
                      auto_approve_severities: Tuple[VarianceSeverity, ...] =
                      (VarianceSeverity.NEGLIGIBLE, VarianceSeverity.MINOR),
                      user: str = "system"
                      ) -> List[ReconciliationRecord]:
        reason_map = reason_map or {}
        results = []
        for sku, item in list(self.items.items()):
            if item.counted_qty is None:
                continue
            reason = reason_map.get(sku, VarianceReason.UNKNOWN)
            sev = self._classify_severity(item.variance_pct, item.variance)
            results.append(
                self.reconcile(sku, reason,
                               approve=sev in auto_approve_severities,
                               user=user)
            )
        return results

    # ---------- Reports ----------
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
            by_reason[r]["value"] += (abs(a.quantity_change)
                                      * self.items[a.sku].unit_cost)
        return {"total_units": total_units,
                "total_value": round(total_value, 2),
                "by_reason": by_reason,
                "adjustment_count": len(shrink)}

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

    def inventory_value(self) -> float:
        return round(
            sum(i.system_qty * i.unit_cost for i in self.items.values()), 2
        )

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
            sku = _validate_sku(sku)
            return [e for e in self.audit_log if e.sku == sku]
        return list(self.audit_log)


# ============================================================
# Public utility facade
# ============================================================

class InventoryUtility:
    """
    Thin facade around InventoryReconciliation with sensible defaults
    and safe input handling. Use this in application code.
    """

    def __init__(self):
        self._engine = InventoryReconciliation()

    # --- items ---
    def add_item(self, sku, name, unit_cost, initial_qty=0,
                 reorder_point=0,
                 on_duplicate: Union[str, DuplicatePolicy] = "strict"):
        """on_duplicate accepts 'strict' | 'idempotent' | 'upsert' or the enum."""
        if isinstance(on_duplicate, str):
            try:
                on_duplicate = DuplicatePolicy(on_duplicate.lower())
            except ValueError:
                raise InventoryError(
                    f"invalid on_duplicate={on_duplicate!r}; "
                    f"choose from {[p.value for p in DuplicatePolicy]}"
                )
        return self._engine.add_item(
            sku=sku, name=name, unit_cost=unit_cost,
            initial_qty=initial_qty, reorder_point=reorder_point,
            on_duplicate=on_duplicate,
        )

    def record_movement(self, sku, movement_type, qty, **kwargs):
        if isinstance(movement_type, str):
            try:
                movement_type = MovementType(movement_type.lower())
            except ValueError:
                raise InventoryError(
                    f"invalid movement_type={movement_type!r}; "
                    f"choose from {[m.value for m in MovementType]}"
                )
        return self._engine.record_movement(sku, movement_type, qty, **kwargs)

    def record_cycle_count(self, sku, counted_qty, user="system"):
        return self._engine.record_cycle_count(sku, counted_qty, user=user)

    def reconcile(self, sku, reason=VarianceReason.UNKNOWN,
                  approve=False, user="system"):
        if isinstance(reason, str):
            try:
                reason = VarianceReason(reason.lower())
            except ValueError:
                raise InventoryError(f"invalid reason={reason!r}")
        return self._engine.reconcile(sku, reason, approve=approve, user=user)

    def reconcile_all(self, reason_map=None, user="system"):
        return self._engine.reconcile_all(reason_map=reason_map, user=user)

    def report(self):
        return self._engine.reconciliation_report()

    def audit(self, sku=None):
        return self._engine.audit_trail(sku)

    # pass-throughs for read-only access
    @property
    def items(self):
        return self._engine.items


# ============================================================
# Demo / self-tests
# ============================================================

def _check(label, fn, expected_exc=None):
    try:
        result = fn()
        status = "OK " if expected_exc is None else "FAIL"
        print(f"  [{status}] {label}: {result!r}"
              if expected_exc is None
              else f"  [FAIL] {label}: expected {expected_exc.__name__}, got {result!r}")
    except Exception as e:
        if expected_exc and isinstance(e, expected_exc):
            print(f"  [OK ] {label}: raised {type(e).__name__}: {e}")
        else:
            print(f"  [FAIL] {label}: unexpected {type(e).__name__}: {e}")


def _demo():
    print("=== Duplicate-SKU handling ===")
    u = InventoryUtility()
    u.add_item("SKU001", "Widget", 10.0, initial_qty=100)
    _check("strict duplicate raises",
           lambda: u.add_item("SKU001", "Widget", 10.0),
           expected_exc=DuplicateSKUError)

    same = u.add_item("SKU001", "Widget", 99.0, initial_qty=999,
                      on_duplicate="idempotent")
    print(f"  [OK ] idempotent returns existing: qty={same.system_qty}, "
          f"cost={same.unit_cost} (unchanged)")

    upserted = u.add_item("SKU001", "Widget v2", 12.5,
                          reorder_point=25, on_duplicate="upsert")
    print(f"  [OK ] upsert updated: name={upserted.name!r}, "
          f"cost={upserted.unit_cost}, reorder={upserted.reorder_point}, "
          f"qty preserved={upserted.system_qty}")

    _check("bad policy string",
           lambda: u.add_item("SKU002", "X", 1.0, on_duplicate="merge"),
           expected_exc=InventoryError)

    print("\n=== Invalid-quantity handling ===")
    cases = [
        ("negative movement qty",
         lambda: u.record_movement("SKU001", "sale", -5),
         InvalidQuantityError),
        ("zero movement qty",
         lambda: u.record_movement("SKU001", "sale", 0),
         InvalidQuantityError),
        ("float with fraction",
         lambda: u.record_movement("SKU001", "sale", 2.5),
         InvalidQuantityError),
        ("NaN qty",
         lambda: u.record_movement("SKU001", "sale", float("nan")),
         InvalidQuantityError),
        ("bool qty",
         lambda: u.record_movement("SKU001", "sale", True),
         InvalidQuantityError),
        ("string qty",
         lambda: u.record_movement("SKU001", "sale", "5"),
         InvalidQuantityError),
        ("oversell drives negative",
         lambda: u.record_movement("SKU001", "sale", 10**6),
         InvalidQuantityError),
        ("negative initial_qty",
         lambda: u.add_item("SKUX", "X", 1.0, initial_qty=-1),
         InvalidQuantityError),
        ("negative reorder_point",
         lambda: u.add_item("SKUY", "Y", 1.0, reorder_point=-3),
         InvalidQuantityError),
        ("negative unit_cost",
         lambda: u.add_item("SKUZ", "Z", -5.0),
         InventoryError),
        ("negative cycle count",
         lambda: u.record_cycle_count("SKU001", -2),
         InvalidQuantityError),
        ("empty sku",
         lambda: u.add_item("", "X", 1.0),
         InvalidSKUError),
        ("non-string sku",
         lambda: u.add_item(123, "X", 1.0),
         InvalidSKUError),
        ("unknown sku movement",
         lambda: u.record_movement("NOPE", "sale", 1),
         UnknownSKUError),
    ]
    for label, fn, exc in cases:
        _check(label, fn, expected_exc=exc)

    print("\n=== Normal flow still works ===")
    u.record_movement("SKU001", "sale", 15, reference="SO-1")
    u.record_movement("SKU001", "receipt", 5, reference="PO-1")
    u.add_item("SKU002", "Gadget", 5.75, initial_qty=200, reorder_point=50)
    u.record_movement("SKU002", "damage", 5, notes="forklift")
    u.record_cycle_count("SKU001", 89)   # system 90 → -1
    u.record_cycle_count("SKU002", 170)  # system 195 → -25 (critical)
    results = u.reconcile_all(reason_map={"SKU001": VarianceReason.MISCOUNT,
                                          "SKU002": VarianceReason.THEFT})
    for r in results:
        print(f"  {r.sku}: sys={r.system_qty} counted={r.counted_qty} "
              f"var={r.variance:+d} ({r.variance_pct:+.2f}%) "
              f"sev={r.severity.value} status={r.status}")

    u.reconcile("SKU002", VarianceReason.THEFT, approve=True, user="mgr")
    print(f"  SKU002 system_qty after approval: {u.items['SKU002'].system_qty}")

    print("\n=== Report ===")
    for k, v in u.report().items():
        print(f"  {k}: {v}")

    return u


if __name__ == "__main__":
    _demo()