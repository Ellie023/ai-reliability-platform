"""Unit tests for the order service business logic.

These tests describe the *correct* behaviour of the Order API. A patch that
introduces a bug will cause one or more of them to fail, which is exactly the
signal the reliability platform uses to detect regressions.
"""
import pytest

from app.models import Order, OrderItem, OrderStatus
from app.order_service import (
    OrderError,
    apply_discount,
    calculate_subtotal,
    create_order,
    transition_status,
)


def _item(sku="ABC", quantity=1, unit_price=10.0):
    return OrderItem(sku=sku, quantity=quantity, unit_price=unit_price)


# --------------------------------------------------------------------------
# create_order
# --------------------------------------------------------------------------
def test_create_order_valid():
    order = create_order([_item(quantity=2, unit_price=5.0)])
    assert order.status == OrderStatus.PENDING
    assert len(order.items) == 1


def test_create_order_multiple_items():
    order = create_order([_item(sku="A"), _item(sku="B", quantity=3)])
    assert len(order.items) == 2


def test_create_order_empty_raises():
    with pytest.raises(OrderError):
        create_order([])


def test_create_order_zero_quantity_raises():
    with pytest.raises(OrderError):
        create_order([_item(quantity=0)])


def test_create_order_negative_quantity_raises():
    with pytest.raises(OrderError):
        create_order([_item(quantity=-3)])


def test_create_order_negative_price_raises():
    with pytest.raises(OrderError):
        create_order([_item(unit_price=-1.0)])


# --------------------------------------------------------------------------
# subtotal / discount
# --------------------------------------------------------------------------
def test_calculate_subtotal():
    order = create_order([_item(quantity=2, unit_price=5.0), _item(quantity=1, unit_price=3.5)])
    assert calculate_subtotal(order) == pytest.approx(13.5)


def test_apply_discount_normal():
    order = create_order([_item(quantity=2, unit_price=50.0)])
    assert apply_discount(order, 10) == pytest.approx(90.0)


def test_apply_discount_zero():
    order = create_order([_item(quantity=1, unit_price=42.0)])
    assert apply_discount(order, 0) == pytest.approx(42.0)


def test_apply_discount_full():
    order = create_order([_item(quantity=1, unit_price=42.0)])
    assert apply_discount(order, 100) == pytest.approx(0.0)


def test_apply_discount_over_100_raises():
    order = create_order([_item()])
    with pytest.raises(OrderError):
        apply_discount(order, 150)


def test_apply_discount_negative_raises():
    order = create_order([_item()])
    with pytest.raises(OrderError):
        apply_discount(order, -5)


# --------------------------------------------------------------------------
# status transitions
# --------------------------------------------------------------------------
def test_transition_pending_to_paid():
    order = create_order([_item()])
    transition_status(order, OrderStatus.PAID)
    assert order.status == OrderStatus.PAID


def test_transition_paid_to_shipped():
    order = create_order([_item()])
    transition_status(order, OrderStatus.PAID)
    transition_status(order, OrderStatus.SHIPPED)
    assert order.status == OrderStatus.SHIPPED


def test_transition_shipped_to_delivered():
    order = create_order([_item()])
    transition_status(order, OrderStatus.PAID)
    transition_status(order, OrderStatus.SHIPPED)
    transition_status(order, OrderStatus.DELIVERED)
    assert order.status == OrderStatus.DELIVERED


def test_transition_cancel_from_pending():
    order = create_order([_item()])
    transition_status(order, OrderStatus.CANCELLED)
    assert order.status == OrderStatus.CANCELLED


def test_transition_invalid_pending_to_shipped_raises():
    order = create_order([_item()])
    with pytest.raises(OrderError):
        transition_status(order, OrderStatus.SHIPPED)


def test_transition_delivered_is_terminal():
    order = create_order([_item()])
    transition_status(order, OrderStatus.PAID)
    transition_status(order, OrderStatus.SHIPPED)
    transition_status(order, OrderStatus.DELIVERED)
    with pytest.raises(OrderError):
        transition_status(order, OrderStatus.PENDING)
