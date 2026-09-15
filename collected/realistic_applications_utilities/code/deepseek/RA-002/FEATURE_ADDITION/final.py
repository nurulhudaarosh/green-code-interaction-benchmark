"""
Inventory Management Utility with Low-Stock Reporting
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Item:
    """Represents a single inventory item."""
    sku: str
    name: str
    quantity: int
    reorder_threshold: int
    unit_price: float = 0.0

    @property
    def is_low_stock(self) -> bool:
        """Return True if quantity is at or below the reorder threshold."""
        return self.quantity <= self.reorder_threshold

    @property
    def stock_value(self) -> float:
        return self.quantity * self.unit_price


class Inventory:
    """Manages a collection of inventory items."""

    def __init__(self) -> None:
        self._items: Dict[str, Item] = {}

    # ---------- Core utility methods ----------

    def add_item(
        self,
        sku: str,
        name: str,
        quantity: int,
        reorder_threshold: int,
        unit_price: float = 0.0,
    ) -> Item:
        """Add a new item. Raises if SKU already exists or inputs invalid."""
        if sku in self._items:
            raise ValueError(f"SKU '{sku}' already exists.")
        if quantity < 0 or reorder_threshold < 0:
            raise ValueError("Quantity and threshold must be non-negative.")

        item = Item(sku, name, quantity, reorder_threshold, unit_price)
        self._items[sku] = item
        return item

    def remove_item(self, sku: str) -> None:
        """Remove an item by SKU."""
        if sku not in self._items:
            raise KeyError(f"SKU '{sku}' not found.")
        del self._items[sku]

    def get_item(self, sku: str) -> Optional[Item]:
        return self._items.get(sku)

    def update_quantity(self, sku: str, delta: int) -> Item:
        """Adjust quantity by delta (positive = restock, negative = sale/usage)."""
        item = self._items.get(sku)
        if item is None:
            raise KeyError(f"SKU '{sku}' not found.")
        new_qty = item.quantity + delta
        if new_qty < 0:
            raise ValueError(
                f"Cannot reduce '{sku}' below zero (current: {item.quantity}, delta: {delta})."
            )
        item.quantity = new_qty
        return item

    def set_threshold(self, sku: str, threshold: int) -> Item:
        item = self._items.get(sku)
        if item is None:
            raise KeyError(f"SKU '{sku}' not found.")
        if threshold < 0:
            raise ValueError("Threshold must be non-negative.")
        item.reorder_threshold = threshold
        return item

    def total_value(self) -> float:
        return sum(i.stock_value for i in self._items.values())

    def all_items(self) -> List[Item]:
        return list(self._items.values())

    # ---------- Low-stock reporting ----------

    def low_stock_items(self) -> List[Item]:
        """Return items at or below their reorder threshold, sorted by urgency."""
        return sorted(
            (i for i in self._items.values() if i.is_low_stock),
            key=lambda i: (i.quantity - i.reorder_threshold, i.sku),
        )

    def low_stock_report(self) -> str:
        """Build a human-readable low-stock report."""
        low = self.low_stock_items()
        lines = [
            "=" * 62,
            f"LOW-STOCK REPORT  ({datetime.now():%Y-%m-%d %H:%M:%S})",
            "=" * 62,
        ]

        if not low:
            lines.append("All items are sufficiently stocked. ✔")
            lines.append("=" * 62)
            return "\n".join(lines)

        header = f"{'SKU':<10}{'Name':<22}{'Qty':>5}{'Thr':>5}{'Deficit':>9}"
        lines.append(header)
        lines.append("-" * 62)

        for item in low:
            deficit = item.reorder_threshold - item.quantity
            lines.append(
                f"{item.sku:<10}{item.name[:20]:<22}"
                f"{item.quantity:>5}{item.reorder_threshold:>5}{deficit:>9}"
            )

        lines.append("-" * 62)
        lines.append(f"Total low-stock items: {len(low)}")
        lines.append("=" * 62)
        return "\n".join(lines)

    def reorder_suggestions(self, target_multiplier: float = 2.0) -> Dict[str, int]:
        """
        Suggest reorder quantities for low-stock items.
        Default: restock up to 2× the reorder threshold.
        """
        suggestions: Dict[str, int] = {}
        for item in self.low_stock_items():
            target = int(item.reorder_threshold * target_multiplier)
            suggestions[item.sku] = max(target - item.quantity, 0)
        return suggestions


# ---------- Demo / entry point ----------

def _demo() -> None:
    inv = Inventory()

    inv.add_item("A100", "Wireless Mouse", quantity=25, reorder_threshold=10, unit_price=19.99)
    inv.add_item("B200", "USB-C Cable", quantity=4, reorder_threshold=15, unit_price=8.50)
    inv.add_item("C300", "Mechanical Keyboard", quantity=12, reorder_threshold=5, unit_price=89.00)
    inv.add_item("D400", "HDMI Adapter", quantity=3, reorder_threshold=8, unit_price=14.75)
    inv.add_item("E500", "Laptop Stand", quantity=7, reorder_threshold=7, unit_price=34.99)

    print("Initial low-stock report:\n")
    print(inv.low_stock_report())

    print("\nReorder suggestions (restock to 2× threshold):")
    for sku, qty in inv.reorder_suggestions().items():
        print(f"  {sku}: order {qty} units")

    print("\nSimulating a sale of 2 USB-C cables...")
    inv.update_quantity("B200", -2)

    print("\nUpdated low-stock report:\n")
    print(inv.low_stock_report())

    print(f"\nTotal inventory value: ${inv.total_value():,.2f}")


if __name__ == "__main__":
    _demo()