from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class Transaction:
    item_id: str
    quantity: int  # Positive for additions/received, negative for sales/dispatches
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
    reorder_amount: int  # Difference needed to reach safety/target stock level


class InventoryReconciler:
    """Handles inventory ledger tracking, validation, deduplication, low-stock reporting, and physical count reconciliation."""

    def __init__(
        self,
        initial_stock: Optional[Dict[str, int]] = None,
        reorder_thresholds: Optional[Dict[str, int]] = None,
        target_stock_levels: Optional[Dict[str, int]] = None,
        default_threshold: int = 10,
    ):
        self.ledger: Dict[str, int] = defaultdict(int)
        self.transaction_history: List[Transaction] = []
        self.default_threshold = max(0, default_threshold)
        
        # Configurable reorder thresholds (minimum safety stock)
        self.reorder_thresholds: Dict[str, int] = {}
        if reorder_thresholds:
            for k, v in reorder_thresholds.items():
                clean_k = self._clean_item_id(k)
                if clean_k and isinstance(v, int) and v >= 0:
                    self.reorder_thresholds[clean_k] = v

        # Configurable target stock levels (for calculating reorder amounts)
        self.target_stock_levels: Dict[str, int] = {}
        if target_stock_levels:
            for k, v in target_stock_levels.items():
                clean_k = self._clean_item_id(k)
                if clean_k and isinstance(v, int) and v >= 0:
                    self.target_stock_levels[clean_k] = v

        if initial_stock:
            for item_id, qty in initial_stock.items():
                clean_id = self._clean_item_id(item_id)
                if clean_id and isinstance(qty, int) and qty >= 0:
                    self.ledger[clean_id] = qty

    @staticmethod
    def _clean_item_id(item_id: Optional[str]) -> Optional[str]:
        """Sanitizes and normalizes item identifiers."""
        if not item_id or not isinstance(item_id, str):
            return None
        cleaned = item_id.strip().upper()
        return cleaned if cleaned else None

    def set_reorder_threshold(self, item_id: str, threshold: int, target_level: Optional[int] = None) -> None:
        """Configures or updates low-stock thresholds for a specific item."""
        clean_id = self._clean_item_id(item_id)
        if clean_id and isinstance(threshold, int) and threshold >= 0:
            self.reorder_thresholds[clean_id] = threshold
            if target_level is not None and isinstance(target_level, int) and target_level >= threshold:
                self.target_stock_levels[clean_id] = target_level

    def record_transaction(self, item_id: str, quantity: int, timestamp: Optional[datetime] = None) -> bool:
        """Validates and records a stock movement."""
        clean_id = self._clean_item_id(item_id)
        if not clean_id or not isinstance(quantity, int):
            return False

        ts = timestamp or datetime.now()
        self.ledger[clean_id] += quantity
        self.transaction_history.append(Transaction(clean_id, quantity, ts))
        return True

    def sanitize_audit_records(self, audit_records: List[AuditRecord]) -> List[AuditRecord]:
        """Deduplicates and validates raw audit records."""
        valid_records: List[AuditRecord] = []

        for record in audit_records:
            clean_id = self._clean_item_id(record.item_id)
            if (
                clean_id
                and isinstance(record.physical_count, int)
                and record.physical_count >= 0
                and isinstance(record.timestamp, datetime)
            ):
                valid_records.append(
                    AuditRecord(
                        item_id=clean_id,
                        physical_count=record.physical_count,
                        timestamp=record.timestamp,
                    )
                )

        deduped: Dict[str, AuditRecord] = {}
        for record in valid_records:
            existing = deduped.get(record.item_id)
            if not existing or record.timestamp >= existing.timestamp:
                deduped[record.item_id] = record

        return list(deduped.values())

    def get_low_stock_report(self) -> List[LowStockAlert]:
        """
        Scans current system ledger for items at or below their reorder threshold.
        
        Returns:
            List of LowStockAlert instances sorted by critical shortage level.
        """
        alerts: List[LowStockAlert] = []

        for item_id, qty in self.ledger.items():
            threshold = self.reorder_thresholds.get(item_id, self.default_threshold)
            
            if qty <= threshold:
                target = self.target_stock_levels.get(item_id, threshold * 2)
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
        self, audit_records: List[AuditRecord], auto_adjust: bool = False
    ) -> Tuple[List[Discrepancy], Dict[str, int], List[LowStockAlert]]:
        """
        Cleans audit records, reconciles inventory, and generates a low-stock report post-reconciliation.
        
        Returns:
            Tuple of (Discrepancies, Updated Ledger, Low Stock Alerts)
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
                self.record_transaction(
                    item_id=item_id,
                    quantity=diff,
                    timestamp=record.timestamp,
                )

        low_stock_alerts = self.get_low_stock_report()
        return discrepancies, dict(self.ledger), low_stock_alerts


# --- Verification Example ---
if __name__ == "__main__":
    now = datetime.now()

    # Define low-stock rules
    custom_thresholds = {"SKU-100": 15, "SKU-200": 10, "SKU-300": 5}
    custom_targets = {"SKU-100": 50, "SKU-200": 30, "SKU-300": 20}

    reconciler = InventoryReconciler(
        initial_stock={"SKU-100": 50, "SKU-200": 20, "SKU-300": 8},
        reorder_thresholds=custom_thresholds,
        target_stock_levels=custom_targets,
        default_threshold=10,
    )

    # Physical audit shows high deficit on SKU-100
    audit = [
        AuditRecord(item_id="SKU-100", physical_count=10, timestamp=now),  # Deficit -> Current: 10 <= Threshold: 15
        AuditRecord(item_id="SKU-200", physical_count=8, timestamp=now),   # Deficit -> Current: 8 <= Threshold: 10
        AuditRecord(item_id="SKU-300", physical_count=12, timestamp=now),  # Surplus -> Current: 12 > Threshold: 5
    ]

    reports, updated_stock, low_stock = reconciler.reconcile(audit, auto_adjust=True)

    print(f"{'ITEM ID':<10} | {'EXPECTED':<8} | {'PHYSICAL':<8} | {'DIFF':<6} | {'STATUS'}")
    print("-" * 50)
    for r in reports:
        print(f"{r.item_id:<10} | {r.expected_qty:<8} | {r.physical_count:<8} | {r.discrepancy:<+6} | {r.status}")

    print("\n" + "=" * 50)
    print("LOW STOCK ALERT REPORT")
    print("=" * 50)
    print(f"{'ITEM ID':<10} | {'CURRENT':<8} | {'THRESHOLD':<10} | {'REORDER QTY'}")
    print("-" * 50)
    for alert in low_stock:
        print(
            f"{alert.item_id:<10} | {alert.current_qty:<8} | "
            f"{alert.reorder_threshold:<10} | +{alert.reorder_amount}"
        )