from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional


# ---------- Exceptions ----------

class InventoryError(Exception):
    """Base exception for inventory operations."""


class DuplicateSKUError(InventoryError):
    """Raised when adding a SKU that already exists."""


class InvalidQuantityError(InventoryError):
    """Raised when a quantity is negative, non-integer, or otherwise invalid."""


class UnknownSKUError(InventoryError):
    """Raised when referencing a SKU that isn't registered."""


# ---------- Helpers ----------

def _normalize_sku(sku: str) -> str:
    if not isinstance(sku, str):
        raise ValueError(f"SKU must be a string, got {type(sku).__name__}")
    normalized = sku.strip().upper()
    if not normalized:
        raise ValueError("SKU must be a non-empty string")
    return normalized


def _validate_quantity(quantity) -> int:
    # Reject bool explicitly since bool subclasses int.
    if isinstance(quantity, bool):
        raise InvalidQuantityError(f"Quantity must be an integer, got bool: {quantity!r}")
    if not isinstance(quantity, int):
        raise InvalidQuantityError(
            f"Quantity must be an integer, got {type(quantity).__name__}: {quantity!r}"
        )
    if quantity < 0:
        raise InvalidQuantityError(f"Quantity cannot be negative: {quantity}")
    return quantity


# ---------- Data model ----------

@dataclass
class Item:
    sku: str
    name: str
    quantity: int = 0
    price: Decimal = Decimal("0.00")
    reorder_threshold: int = 0  # low-stock trigger per item

    def __post_init__(self):
        self.sku = _normalize_sku(self.sku)
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
        _validate_quantity(self.reorder_threshold)

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.reorder_threshold


# ---------- Inventory ----------

class Inventory:
    def __init__(self, default_reorder_threshold: int = 5):
        _validate_quantity(default_reorder_threshold)
        self._items: Dict[str, Item] = {}
        self.default_reorder_threshold = default_reorder_threshold

    def add_item(self, sku: str, name: str, quantity: int = 0,
                 price: Decimal = Decimal("0.00"),
                 reorder_threshold: Optional[int] = None) -> Item:
        """Register a new item. Raises DuplicateSKUError if SKU already exists."""
        key = _normalize_sku(sku)
        if key in self._items:
            raise DuplicateSKUError(f"SKU already exists: {key}")
        _validate_quantity(quantity)
        if reorder_threshold is None:
            reorder_threshold = self.default_reorder_threshold
        item = Item(sku=key, name=name, quantity=quantity, price=price,
                    reorder_threshold=reorder_threshold)
        self._items[key] = item
        return item

    def get_item(self, sku: str) -> Item:
        key = _normalize_sku(sku)
        if key not in self._items:
            raise UnknownSKUError(f"Unknown SKU: {key}")
        return self._items[key]

    def adjust_quantity(self, sku: str, delta: int) -> Item:
        """Increment or decrement stock by delta. Result must stay >= 0."""
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise InvalidQuantityError(
                f"Delta must be an integer, got {type(delta).__name__}: {delta!r}"
            )
        item = self.get_item(sku)
        new_qty = item.quantity + delta
        if new_qty < 0:
            raise InvalidQuantityError(
                f"Adjustment would make quantity negative "
                f"({item.quantity} + {delta} = {new_qty}) for SKU {item.sku}"
            )
        item.quantity = new_qty
        return item

    def set_quantity(self, sku: str, quantity: int) -> Item:
        _validate_quantity(quantity)
        item = self.get_item(sku)
        item.quantity = quantity
        return item

    def set_reorder_threshold(self, sku: str, threshold: int) -> Item:
        _validate_quantity(threshold)
        item = self.get_item(sku)
        item.reorder_threshold = threshold
        return item

    def remove_item(self, sku: str) -> None:
        key = _normalize_sku(sku)
        if key not in self._items:
            raise UnknownSKUError(f"Unknown SKU: {key}")
        del self._items[key]

    def list_items(self) -> List[Item]:
        return list(self._items.values())

    # ---------- Low-stock reporting ----------

    def low_stock_items(self) -> List[Item]:
        """Return items at or below their reorder threshold, sorted by urgency."""
        low = [i for i in self._items.values() if i.is_low_stock]
        # Most urgent first: smallest remaining stock, then largest shortfall.
        low.sort(key=lambda i: (i.quantity, -(i.reorder_threshold - i.quantity), i.sku))
        return low

    def low_stock_report(self) -> str:
        """Human-readable low-stock report."""
        low = self.low_stock_items()
        if not low:
            return "Low-stock report: all items above threshold."

        lines = ["Low-stock report:"]
        for item in low:
            shortfall = item.reorder_threshold - item.quantity
            lines.append(
                f"  {item.sku:<12} {item.name:<20} "
                f"qty={item.quantity:<5} threshold={item.reorder_threshold:<5} "
                f"reorder {shortfall} unit(s)"
            )
        lines.append(f"  ({len(low)} item(s) need attention)")
        return "\n".join(lines)

    def reorder_suggestions(self, target_multiplier: int = 2) -> Dict[str, int]:
        """Suggested order quantity per low-stock SKU.

        Targets `target_multiplier * reorder_threshold` as the post-restock level,
        so a SKU near its threshold gets enough buffer to avoid churn.
        """
        if isinstance(target_multiplier, bool) or not isinstance(target_multiplier, int):
            raise InvalidQuantityError(
                f"target_multiplier must be an integer, got "
                f"{type(target_multiplier).__name__}: {target_multiplier!r}"
            )
        if target_multiplier < 1:
            raise InvalidQuantityError(
                f"target_multiplier must be >= 1, got {target_multiplier}"
            )
        suggestions: Dict[str, int] = {}
        for item in self.low_stock_items():
            target = item.reorder_threshold * target_multiplier
            suggestions[item.sku] = max(target - item.quantity, 0)
        return suggestions

    def __contains__(self, sku: str) -> bool:
        try:
            return _normalize_sku(sku) in self._items
        except ValueError:
            return False


# ---------- Demo ----------

if __name__ == "__main__":
    inv = Inventory(default_reorder_threshold=5)
    inv.add_item("abc-123", "Widget", quantity=10, price=Decimal("4.99"))
    inv.add_item("def-456", "Gadget", quantity=3, price=Decimal("12.50"))
    inv.add_item("ghi-789", "Gizmo", quantity=0, price=Decimal("7.25"),
                 reorder_threshold=2)
    inv.add_item("jkl-012", "Doohickey", quantity=20, price=Decimal("1.10"))

    # Duplicate SKU still rejected.
    try:
        inv.add_item("ABC-123", "Widget copy")
    except DuplicateSKUError as e:
        print("dup:", e)

    # Invalid quantity still rejected.
    try:
        inv.adjust_quantity("abc-123", -20)
    except InvalidQuantityError as e:
        print("qty:", e)

    print()
    print(inv.low_stock_report())
    print()
    print("reorder suggestions:", inv.reorder_suggestions())