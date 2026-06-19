"""Order service business logic for the sample Order API."""
from typing import List

from .models import Order, OrderItem, OrderStatus


# Allowed status transitions for an order's lifecycle.
VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class OrderError(ValueError):
    """Raised when an order operation is invalid."""


def create_order(items: List[OrderItem]) -> Order:
    """Create a new order after validating its items."""
    if not items:
        raise OrderError("Order must contain at least one item")
    for item in items:
        if item.quantity <= 0:
            raise OrderError("Item quantity must be positive")
        if item.unit_price < 0:
            raise OrderError("Item unit price must not be negative")
    return Order(items=list(items), status=OrderStatus.PENDING)


def calculate_subtotal(order: Order) -> float:
    """Return the sum of line totals for the order."""
    return round(sum(item.unit_price * item.quantity for item in order.items), 2)


def apply_discount(order: Order, discount_percent: float) -> float:
    """Apply a percentage discount to the order subtotal."""
    if discount_percent < 0 or discount_percent > 100:
        raise OrderError("Discount percent must be between 0 and 100")
    subtotal = calculate_subtotal(order)
    return round(subtotal * (1 - discount_percent / 100), 2)


def transition_status(order: Order, new_status: OrderStatus) -> Order:
    """Move the order to a new status if the transition is allowed."""
    allowed = VALID_TRANSITIONS[order.status]
    if new_status not in allowed:
        raise OrderError(
            f"Cannot transition from {order.status.value} to {new_status.value}"
        )
    order.status = new_status
    return order
