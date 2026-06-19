"""FastAPI application exposing the Order API."""
from typing import Dict

from fastapi import FastAPI, HTTPException

from .models import (
    CreateOrderRequest,
    DiscountRequest,
    Order,
    StatusRequest,
)
from . import order_service

app = FastAPI(title="Order API", version="1.0.0")

# Simple in-memory store: order_id -> Order
_ORDERS: Dict[int, Order] = {}
_COUNTER: Dict[str, int] = {"next_id": 1}


def _next_id() -> int:
    order_id = _COUNTER["next_id"]
    _COUNTER["next_id"] += 1
    return order_id


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orders")
def create_order(request: CreateOrderRequest) -> dict:
    try:
        order = order_service.create_order(request.items)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    order_id = _next_id()
    _ORDERS[order_id] = order
    return {"order_id": order_id, "order": order.model_dump()}


@app.get("/orders/{order_id}")
def get_order(order_id: int) -> dict:
    order = _ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "order": order.model_dump()}


@app.post("/orders/{order_id}/discount")
def discount_order(order_id: int, request: DiscountRequest) -> dict:
    order = _ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        total = order_service.apply_discount(order, request.discount_percent)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"order_id": order_id, "discounted_total": total}


@app.post("/orders/{order_id}/status")
def update_status(order_id: int, request: StatusRequest) -> dict:
    order = _ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order_service.transition_status(order, request.status)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"order_id": order_id, "status": order.status.value}
