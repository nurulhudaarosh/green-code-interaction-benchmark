from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class Transaction:
    item_id: str
    quantity: int
    timestamp: datetime


@dataclass
class AuditRecord:
    item_id: str
    physical_count: int
    timestamp: datetime


@dataclass
class Discrepancy:
    item_id: str
    expected_qty: int
    physical_count: int
    discrepancy: int  # physical_count - expected_qty
    status: str  # 'SURPLUS', 'DEFICIT', or 'BALANCED'


@dataclass
class LowStockAlert:
    item_id: str
    current_qty: int
    reorder_threshold: int
    reorder_amount: int


class InventoryReconciler:
    """Handles inventory ledger tracking, boundary validation, deduplication, low-stock reporting, and physical count reconciliation."""

    def __init__(
        self,
        initial_stock: Optional[Dict[str, int]] = None,
        reorder_thresholds: Optional[Dict[str, int]] = None,
        target_stock_levels: Optional[Dict[str, int]] = None,
        default_threshold: int = 10,
    ):
        self.ledger: Dict[str, int] = defaultdict(int)
        self.transaction_history: List[Transaction] = []
        self.default_threshold = self._sanitize_non_negative_int(default_threshold, fallback=10)

        # Configurable reorder thresholds
        self.reorder_thresholds: Dict[str, int] = {}
        if isinstance(reorder_thresholds, dict):
            for k, v in reorder_thresholds.items():
                clean_k = self._clean_item_id(k)
                clean_v = self._sanitize_non_negative_int(v)
                if clean_k and clean_v is not None:
                    self.reorder_thresholds[clean_k] = clean_v

        # Configurable target stock levels
        self.target_stock_levels: Dict[str, int] = {}
        if isinstance(target_stock_levels, dict):
            for k, v in target_stock_levels.items():
                clean_k = self._clean_item_id(k)
                clean_v = self._sanitize_non_negative_int(v)
                if clean_k and clean_v is not None:
                    self.target_stock_levels[clean_k] = clean_v

        # Initial stock setup
        if isinstance(initial_stock, dict):
            for item_id, qty in initial_stock.items():
                clean_id = self._clean_item_id(item_id)
                clean_qty = self._sanitize_non_negative_int(qty)
                if clean_id and clean_qty is not None:
                    self.ledger[clean_id] = clean_qty

    @staticmethod
    def _clean_item_id(item_id: Optional[str]) -> Optional[str]:
        """Sanitizes and normalizes item identifiers. Rejects non-strings and empty/whitespace values."""
        if not isinstance(item_id, str):
            return None
        cleaned = item_id.strip().upper()
        return cleaned if cleaned else None

    @staticmethod
    def _sanitize_non_negative_int(val: object, fallback: Optional[int] = None) -> Optional[int]:
        """Ensures a value is a valid non-negative integer."""
        if isinstance(val, bool):  # Python booleans inherit from int (True == 1, False == 0)
            return fallback
        if isinstance(val, int) and val >= 0:
            return val
        return fallback

    def set_reorder_threshold(self, item_id: str, threshold: int, target_level: Optional[int] = None) -> bool:
        """Configures or updates low-stock thresholds for a specific item with boundary guards."""
        clean_id = self._clean_item_id(item_id)
        clean_threshold = self._sanitize_non_negative_int(threshold)

        if not clean_id or clean_threshold is None:
            return False

        self.reorder_thresholds[clean_id] = clean_threshold
        clean_target = self._sanitize_non_negative_int(target_level)

        if clean_target is not None and clean_target >= clean_threshold:
            self.target_stock_levels[clean_id] = clean_target

        return True

    def record_transaction(self, item_id: str, quantity: int, timestamp: Optional[datetime] = None) -> bool:
        """Validates and records stock movements. Allows negative/positive updates but guards against invalid types."""
        clean_id = self._clean_item_id(item_id)

        # Quantity must be a pure int, not bool
        if not clean_id or not isinstance(quantity, int) or isinstance(quantity, bool):
            return False

        # Guard against reducing stock below 0
        if self.ledger[clean_id] + quantity < 0:
            return False

        ts = timestamp if isinstance(timestamp, datetime) else datetime.now()
        self.ledger[clean_id] += quantity
        self.transaction_history.append(Transaction(clean_id, quantity, ts))
        return True

    def sanitize_audit_records(self, audit_records: Optional[List[AuditRecord]]) -> List[AuditRecord]:
        """
        Deduplicates and validates raw audit records against boundaries & empty inputs.
        - Handles None or non-list inputs safely.
        - Drops records with invalid item_ids, bad types, negative counts, or invalid timestamps.
        - Deduplicates multiple counts by taking the latest valid timestamp.
        """
        if not isinstance(audit_records, list) or not audit_records:
            return []

        valid_records: List[AuditRecord] = []

        for record in audit_records:
            if not isinstance(record, AuditRecord):
                continue

            clean_id = self._clean_item_id(record.item_id)
            clean_count = self._sanitize_non_negative_int(record.physical_count)
            valid_ts = record.timestamp if isinstance(record.timestamp, datetime) else None

            if clean_id and clean_count is not None and valid_ts:
                valid_records.append(
                    AuditRecord(
                        item_id=clean_id,
                        physical_count=clean_count,
                        timestamp=valid_ts,
                    )
                )

        # Deduplication step (Keep latest record per item_id)
        deduped: Dict[str, AuditRecord] = {}
        for record in valid_records:
            existing = deduped.get(record.item_id)
            if not existing or record.timestamp >= existing.timestamp:
                deduped[record.item_id] = record

        return list(deduped.values())

    def get_low_stock_report(self) -> List[LowStockAlert]:
        """Scans current system ledger for items at or below their reorder threshold."""
        alerts: List[LowStockAlert] = []

        for item_id, qty in self.ledger.items():
            threshold = self.reorder_thresholds.get(item_id, self.default_threshold)

            if qty <= threshold:
                target = self.target_stock_levels.get(item_id, max(threshold * 2, threshold))
                reorder_amount = max(0, target - qty)

                alerts.append(
                    LowStockAlert(
                        item_id=item_id,
                        current_qty=qty,
                        reorder_threshold=threshold,
                        reorder_amount=reorder_amount,
                    )
                )

        # Sort by most severely depleted stock relative to threshold
        alerts.sort(key=lambda x: x.current_qty - x.reorder_threshold)
        return alerts

    def reconcile(
        self, audit_records: Optional[List[AuditRecord]] = None, auto_adjust: bool = False
    ) -> Tuple[List[Discrepancy], Dict[str, int], List[LowStockAlert]]:
        """
        Cleans audit records, safely handles missing or boundary audit datasets,
        reconciles inventory, and generates low-stock alerts post-reconciliation.
        """
        clean_audits = self.sanitize_audit_records(audit_records)
        discrepancies: List[Discrepancy] = []

        for record in clean_audits:
            item_id = record.item_id
            expected_qty = self.ledger.get(item_id, 0)
            physical_qty = record.physical_count
            diff = physical_qty - expected_qty

            if diff > 0:
                status = "SURPLUS"
            elif diff < 0:
                status = "DEFICIT"
            else:
                status = "BALANCED"

            discrepancy_entry = Discrepancy(
                item_id=item_id,
                expected_qty=expected_qty,
                physical_count=physical_qty,
                discrepancy=diff,
                status=status,
            )
            discrepancies.append(discrepancy_entry)

            if auto_adjust and diff != 0:
                # Direct update for auto_adjust alignment to handle zero/negative boundary cases seamlessly
                self.ledger[item_id] = physical_qty
                self.transaction_history.append(
                    Transaction(item_id, diff, record.timestamp)
                )

        low_stock_alerts = self.get_low_stock_report()
        return discrepancies, dict(self.ledger), low_stock_alerts


# --- Verification Example ---
if __name__ == "__main__":
    now = datetime.now()

    # 1. Initialization with dirty/boundary values (None, Booleans, Negative Numbers, Strings)
    dirty_initial = {"SKU-100": 10, "SKU-200": -5, "   ": 20, "SKU-300": True}  # True is ignored
    dirty_thresholds = {"SKU-100": 5, "SKU-200": "invalid"}

    reconciler = InventoryReconciler(
        initial_stock=dirty_initial,
        reorder_thresholds=dirty_thresholds,
        default_threshold=-10,  # Fallbacks to 10
    )

    # 2. Border transactions (attempting to draw stock below 0, invalid types)
    assert reconciler.record_transaction("SKU-100", -50) is False  # Prevents negative stock balance
    assert reconciler.record_transaction("SKU-100", True) is False  # Rejects boolean
    assert reconciler.record_transaction("SKU-100", -5) is True    # Valid reduction (Stock becomes 5)

    # 3. Empty & Edge-case audit input
    edge_audits = [
        None,                                                            # Ignored
        "Not an AuditRecord",                                           # Ignored
        AuditRecord(item_id="SKU-100", physical_count=0, timestamp=now), # Boundary: 0 stock count
        AuditRecord(item_id="SKU-400", physical_count=15, timestamp=now) # New SKU seen for first time
    ]

    reports, stock, alerts = reconciler.reconcile(edge_audits, auto_adjust=True)

    print("Reconciliation Reports (Handled safely):")
    for r in reports:
        print(f"Item: {r.item_id} | Expected: {r.expected_qty} | Physical: {r.physical_count} | Status: {r.status}")

    print("\nCleaned Ledger State:")
    print(stock)

    print("\nEmpty Execution Test (reconcile with None):")
    empty_reports, empty_stock, _ = reconciler.reconcile(None)
    print(f"Reports Count: {len(empty_reports)} | Ledger Preserved: {bool(empty_stock)}")