"""
Unit tests for the Orders domain layer.

These tests are fast, have zero I/O, and validate the core business rules.
"""

import pytest
from decimal import Decimal

from src.modules.orders.domain.entities import Order, OrderItem
from src.modules.orders.domain.events import (
    OrderCancelledEvent,
    OrderConfirmedEvent,
    OrderPlacedEvent,
    OrderReadyEvent,
    OrderPickedUpEvent,
)
from src.modules.orders.domain.exceptions import (
    EmptyOrderError,
    InvalidOrderTransitionError,
    OrderAlreadyCancelledError,
)
from src.modules.orders.domain.value_objects import (
    CustomerId,
    OrderId,
    OrderStatus,
    OrderTotal,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_item(**overrides) -> OrderItem:
    defaults = dict(
        dish_id="dish-001",
        dish_name="Lasagna",
        quantity=2,
        unit_price=Decimal("15.00"),
        currency="USD",
    )
    defaults.update(overrides)
    return OrderItem.create(**defaults)


def _make_order(**overrides) -> Order:
    defaults = dict(
        customer_id=CustomerId("customer-001"),
        items=[_make_item()],
        notes="No onions please",
    )
    defaults.update(overrides)
    return Order.create(**defaults)


# ---------------------------------------------------------------------------
# Value Object tests
# ---------------------------------------------------------------------------
class TestOrderId:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            OrderId("")

    def test_whitespace_raises(self):
        with pytest.raises(ValueError):
            OrderId("   ")

    def test_valid(self):
        oid = OrderId("order-123")
        assert oid.value == "order-123"


class TestCustomerId:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            CustomerId("")

    def test_valid(self):
        cid = CustomerId("cust-abc")
        assert cid.value == "cust-abc"


class TestOrderTotal:
    def test_valid_total(self):
        t = OrderTotal(amount=29.99)
        assert t.amount == Decimal("29.99")
        assert t.currency == "USD"

    def test_zero_is_allowed(self):
        # A total of 0 is technically valid (e.g., free promo order)
        t = OrderTotal(amount=0)
        assert t.amount == Decimal("0.00")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="negative"):
            OrderTotal(amount=-5)

    def test_quantizes_to_two_decimals(self):
        t = OrderTotal(amount=10.999)
        assert t.amount == Decimal("11.00")

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError, match="3-letter"):
            OrderTotal(amount=10, currency="US")


class TestOrderStatus:
    def test_placed_can_transition_to_confirmed(self):
        assert OrderStatus.CONFIRMED in VALID_TRANSITIONS[OrderStatus.PLACED]

    def test_placed_can_transition_to_cancelled(self):
        assert OrderStatus.CANCELLED in VALID_TRANSITIONS[OrderStatus.PLACED]

    def test_picked_up_is_terminal(self):
        assert len(VALID_TRANSITIONS[OrderStatus.PICKED_UP]) == 0

    def test_cancelled_is_terminal(self):
        assert len(VALID_TRANSITIONS[OrderStatus.CANCELLED]) == 0


# ---------------------------------------------------------------------------
# OrderItem tests
# ---------------------------------------------------------------------------
class TestOrderItem:
    def test_create_valid(self):
        item = OrderItem.create(
            dish_id="d1",
            dish_name="Pasta",
            quantity=3,
            unit_price=Decimal("10.00"),
        )
        assert item.dish_id == "d1"
        assert item.quantity == 3
        assert item.line_total == Decimal("30.00")

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="positive"):
            OrderItem.create(
                dish_id="d1",
                dish_name="Pasta",
                quantity=0,
                unit_price=Decimal("10.00"),
            )

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="positive"):
            OrderItem.create(
                dish_id="d1",
                dish_name="Pasta",
                quantity=1,
                unit_price=Decimal("-5.00"),
            )


# ---------------------------------------------------------------------------
# Order Aggregate tests
# ---------------------------------------------------------------------------
class TestOrderCreation:
    def test_creates_order_with_event(self):
        order = _make_order()

        assert order.status == OrderStatus.PLACED
        assert order.customer_id.value == "customer-001"
        assert len(order.items) == 1
        assert order.total.amount == Decimal("30.00")  # 2 × 15.00
        assert order.notes == "No onions please"
        assert order.is_active is True

        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderPlacedEvent)
        assert events[0].order_id == order.id
        assert events[0].total_amount == Decimal("30.00")

    def test_empty_items_raises(self):
        with pytest.raises(EmptyOrderError):
            Order.create(
                customer_id=CustomerId("c1"),
                items=[],
            )

    def test_multiple_items(self):
        items = [
            _make_item(dish_id="d1", dish_name="Pasta", quantity=1, unit_price=Decimal("10.00")),
            _make_item(dish_id="d2", dish_name="Salad", quantity=2, unit_price=Decimal("8.00")),
        ]
        order = Order.create(
            customer_id=CustomerId("c1"),
            items=items,
        )
        assert order.total.amount == Decimal("26.00")  # 10 + 16
        assert len(order.items) == 2


class TestOrderTransitions:
    def test_confirm(self):
        order = _make_order()
        order.confirm()

        assert order.status == OrderStatus.CONFIRMED
        events = order.collect_events()
        # OrderPlacedEvent already collected above, so only OrderConfirmedEvent
        confirmed_events = [e for e in events if isinstance(e, OrderConfirmedEvent)]
        assert len(confirmed_events) == 1

    def test_full_lifecycle(self):
        order = _make_order()
        order.collect_events()  # clear creation events

        order.confirm()
        order.start_preparing()
        order.mark_ready()
        order.pick_up()

        assert order.status == OrderStatus.PICKED_UP
        assert order.is_active is False

        events = order.collect_events()
        event_types = [type(e).__name__ for e in events]
        assert "OrderConfirmedEvent" in event_types
        assert "OrderReadyEvent" in event_types
        assert "OrderPickedUpEvent" in event_types

    def test_cancel_from_placed(self):
        order = _make_order()
        order.collect_events()

        order.cancel(reason="Changed my mind")

        assert order.status == OrderStatus.CANCELLED
        assert order.is_active is False

        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCancelledEvent)
        assert events[0].reason == "Changed my mind"
        assert len(events[0].items) == 1

    def test_cancel_from_confirmed(self):
        order = _make_order()
        order.confirm()
        order.collect_events()

        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cannot_cancel_preparing_order(self):
        order = _make_order()
        order.confirm()
        order.start_preparing()

        with pytest.raises(InvalidOrderTransitionError):
            order.cancel()

    def test_cannot_confirm_cancelled_order(self):
        order = _make_order()
        order.cancel()

        with pytest.raises(InvalidOrderTransitionError):
            order.confirm()

    def test_cancel_already_cancelled_raises(self):
        order = _make_order()
        order.cancel()

        with pytest.raises(OrderAlreadyCancelledError):
            order.cancel()

    def test_cannot_pick_up_before_ready(self):
        order = _make_order()
        order.confirm()
        order.start_preparing()

        with pytest.raises(InvalidOrderTransitionError):
            order.pick_up()

    def test_cannot_skip_preparing(self):
        order = _make_order()
        order.confirm()

        with pytest.raises(InvalidOrderTransitionError):
            order.mark_ready()


class TestOrderReconstitute:
    def test_reconstitute_does_not_emit_events(self):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        order = Order.reconstitute(
            order_id="ord-001",
            customer_id="cust-001",
            items=[_make_item()],
            status="CONFIRMED",
            total_amount=Decimal("30.00"),
            total_currency="USD",
            notes="",
            created_at=now,
            updated_at=now,
        )
        assert order.status == OrderStatus.CONFIRMED
        assert order.collect_events() == []
