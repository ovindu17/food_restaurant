"""
HTTP endpoints for the Orders module.

Endpoints are thin — they validate input via Pydantic, delegate to
Application-layer handlers, and return response schemas.  Exception
mapping is handled globally by ``order_exception_handler``.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status

from src.modules.orders.application.command_handlers import (
    CancelOrderHandler,
    ConfirmOrderHandler,
    MarkReadyHandler,
    PickUpOrderHandler,
    PlaceOrderHandler,
    StartPreparingHandler,
)
from src.modules.orders.application.commands import (
    CancelOrderCommand,
    ConfirmOrderCommand,
    GetOrderQuery,
    ListCustomerOrdersQuery,
    MarkReadyCommand,
    PickUpOrderCommand,
    PlaceOrderCommand,
    StartPreparingCommand,
)
from src.modules.orders.application.query_handlers import (
    GetOrderHandler,
    ListCustomerOrdersHandler,
)
from src.modules.orders.presentation.dependencies import (
    get_cancel_order_handler,
    get_confirm_order_handler,
    get_get_order_handler,
    get_list_customer_orders_handler,
    get_mark_ready_handler,
    get_pick_up_order_handler,
    get_place_order_handler,
    get_start_preparing_handler,
)
from src.modules.orders.presentation.schemas import (
    CancelOrderRequest,
    OrderResponse,
    OrderItemResponse,
    PlaceOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order",
)
def place_order(
    body: PlaceOrderRequest,
    handler: PlaceOrderHandler = Depends(get_place_order_handler),
) -> OrderResponse:
    from src.modules.orders.application.commands import OrderItemInput

    command = PlaceOrderCommand(
        customer_id=body.customer_id,
        items=[
            OrderItemInput(dish_id=item.dish_id, quantity=item.quantity)
            for item in body.items
        ],
        notes=body.notes,
    )
    result = handler.handle(command)
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.patch(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    summary="Seller confirms the order",
)
def confirm_order(
    order_id: str,
    handler: ConfirmOrderHandler = Depends(get_confirm_order_handler),
) -> OrderResponse:
    result = handler.handle(ConfirmOrderCommand(order_id=order_id))
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an order",
)
def cancel_order(
    order_id: str,
    body: CancelOrderRequest,
    handler: CancelOrderHandler = Depends(get_cancel_order_handler),
) -> OrderResponse:
    result = handler.handle(
        CancelOrderCommand(order_id=order_id, reason=body.reason)
    )
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.patch(
    "/{order_id}/prepare",
    response_model=OrderResponse,
    summary="Seller starts preparing the order",
)
def start_preparing(
    order_id: str,
    handler: StartPreparingHandler = Depends(get_start_preparing_handler),
) -> OrderResponse:
    result = handler.handle(StartPreparingCommand(order_id=order_id))
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.patch(
    "/{order_id}/ready",
    response_model=OrderResponse,
    summary="Mark order as ready for pickup",
)
def mark_ready(
    order_id: str,
    handler: MarkReadyHandler = Depends(get_mark_ready_handler),
) -> OrderResponse:
    result = handler.handle(MarkReadyCommand(order_id=order_id))
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.patch(
    "/{order_id}/pick-up",
    response_model=OrderResponse,
    summary="Customer picks up the order",
)
def pick_up_order(
    order_id: str,
    handler: PickUpOrderHandler = Depends(get_pick_up_order_handler),
) -> OrderResponse:
    result = handler.handle(PickUpOrderCommand(order_id=order_id))
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
def get_order(
    order_id: str,
    handler: GetOrderHandler = Depends(get_get_order_handler),
) -> OrderResponse:
    result = handler.handle(GetOrderQuery(order_id=order_id))
    return OrderResponse(
        id=result.id,
        customer_id=result.customer_id,
        items=[OrderItemResponse(**i.__dict__) for i in result.items],
        status=result.status,
        total_amount=result.total_amount,
        currency=result.currency,
        notes=result.notes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List orders for a customer",
)
def list_customer_orders(
    customer_id: str,
    handler: ListCustomerOrdersHandler = Depends(get_list_customer_orders_handler),
) -> List[OrderResponse]:
    results = handler.handle(ListCustomerOrdersQuery(customer_id=customer_id))
    return [
        OrderResponse(
            id=r.id,
            customer_id=r.customer_id,
            items=[OrderItemResponse(**i.__dict__) for i in r.items],
            status=r.status,
            total_amount=r.total_amount,
            currency=r.currency,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in results
    ]
