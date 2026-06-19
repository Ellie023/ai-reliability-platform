"""Domain models for the sample Order API."""
from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Lifecycle states an order can be in."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """A single line item on an order."""

    sku: str = Field(..., description="Stock keeping unit identifier")
    quantity: int = Field(..., description="Number of units ordered")
    unit_price: float = Field(..., description="Price per single unit")


class Order(BaseModel):
    """An order composed of one or more line items."""

    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING

    def line_total(self) -> float:
        """Return the un-discounted total for every line item."""
        return sum(item.unit_price * item.quantity for item in self.items)


class CreateOrderRequest(BaseModel):
    """Payload for creating a new order."""

    items: List[OrderItem]


class DiscountRequest(BaseModel):
    """Payload for applying a discount to an order."""

    discount_percent: float


class StatusRequest(BaseModel):
    """Payload for transitioning an order's status."""

    status: OrderStatus
