"""
Unit tests for the Catalog domain layer.

These tests are fast, have zero I/O, and validate the core business rules.
"""

import pytest
from decimal import Decimal

from src.modules.catalog.domain.entities import Dish
from src.modules.catalog.domain.events import (
    DishCreatedEvent,
    DishDeactivatedEvent,
    DishPriceChangedEvent,
    PortionsDeductedEvent,
    PortionsExhaustedEvent,
)
from src.modules.catalog.domain.exceptions import (
    DishAlreadyDeactivatedError,
    InsufficientPortionsError,
)
from src.modules.catalog.domain.value_objects import DishId, Money, Portions, SellerId


# ---------------------------------------------------------------------------
# Value Object tests
# ---------------------------------------------------------------------------
class TestMoney:
    def test_valid_money(self):
        m = Money(amount=12.99)
        assert m.amount == Decimal("12.99")
        assert m.currency == "USD"

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="positive"):
            Money(amount=0)

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="positive"):
            Money(amount=-5)

    def test_quantizes_to_two_decimals(self):
        m = Money(amount=10.999)
        assert m.amount == Decimal("11.00")

    def test_addition_same_currency(self):
        result = Money(amount=5) + Money(amount=3.5)
        assert result.amount == Decimal("8.50")

    def test_addition_different_currency_raises(self):
        with pytest.raises(ValueError, match="currencies"):
            Money(amount=5, currency="USD") + Money(amount=3, currency="EUR")


class TestPortions:
    def test_deduct(self):
        p = Portions(value=10)
        result = p.deduct(3)
        assert result.value == 7

    def test_deduct_exact(self):
        p = Portions(value=5)
        result = p.deduct(5)
        assert result.is_exhausted()

    def test_deduct_too_many_raises(self):
        p = Portions(value=2)
        with pytest.raises(ValueError, match="Cannot deduct"):
            p.deduct(5)

    def test_negative_clamped_to_zero(self):
        p = Portions(value=-3)
        assert p.value == 0


class TestTypedIds:
    def test_empty_dish_id_raises(self):
        with pytest.raises(ValueError):
            DishId("")

    def test_empty_seller_id_raises(self):
        with pytest.raises(ValueError):
            SellerId("   ")


# ---------------------------------------------------------------------------
# Dish Aggregate tests
# ---------------------------------------------------------------------------
class TestDishCreation:
    def test_creates_dish_with_event(self):
        dish = Dish.create(
            seller_id=SellerId("seller-1"),
            name="Lasagna",
            description="Homemade with love",
            price=Money(amount=15.00),
            portions=Portions(value=10),
        )

        assert dish.name == "Lasagna"
        assert dish.price.amount == Decimal("15.00")
        assert dish.portions.value == 10
        assert dish.is_active is True

        events = dish.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], DishCreatedEvent)
        assert events[0].dish_id == dish.id

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            Dish.create(
                seller_id=SellerId("s1"),
                name="",
                description="",
                price=Money(amount=10),
                portions=Portions(value=5),
            )

    def test_long_name_raises(self):
        with pytest.raises(ValueError, match="100"):
            Dish.create(
                seller_id=SellerId("s1"),
                name="x" * 101,
                description="",
                price=Money(amount=10),
                portions=Portions(value=5),
            )


class TestDishBehavior:
    @pytest.fixture
    def dish(self):
        d = Dish.create(
            seller_id=SellerId("seller-1"),
            name="Pasta",
            description="Al dente",
            price=Money(amount=10),
            portions=Portions(value=5),
        )
        d.collect_events()  # clear creation event
        return d

    def test_deduct_portions(self, dish):
        dish.deduct_portions(3)
        assert dish.portions.value == 2

        events = dish.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], PortionsDeductedEvent)

    def test_deduct_all_emits_exhausted(self, dish):
        dish.deduct_portions(5)

        events = dish.collect_events()
        assert len(events) == 2
        assert isinstance(events[0], PortionsDeductedEvent)
        assert isinstance(events[1], PortionsExhaustedEvent)

    def test_deduct_too_many_raises(self, dish):
        with pytest.raises(InsufficientPortionsError):
            dish.deduct_portions(99)

    def test_change_price(self, dish):
        dish.change_price(Money(amount=20))

        assert dish.price.amount == Decimal("20.00")
        events = dish.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], DishPriceChangedEvent)
        assert events[0].old_price == Decimal("10.00")
        assert events[0].new_price == Decimal("20.00")

    def test_deactivate(self, dish):
        dish.deactivate()
        assert dish.is_active is False

        events = dish.collect_events()
        assert isinstance(events[0], DishDeactivatedEvent)

    def test_double_deactivate_raises(self, dish):
        dish.deactivate()
        dish.collect_events()

        with pytest.raises(DishAlreadyDeactivatedError):
            dish.deactivate()


class TestDishReconstitute:
    """Ensure reconstitute does NOT re-trigger validation or events."""

    def test_reconstitute_skips_events(self):
        from datetime import datetime, timezone

        dish = Dish.reconstitute(
            dish_id="abc-123",
            seller_id="seller-1",
            name="Old Dish",
            description="From DB",
            price_amount=Decimal("9.99"),
            price_currency="USD",
            available_portions=0,
            is_active=False,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        assert dish.id == "abc-123"
        assert dish.portions.value == 0
        assert dish.is_active is False
        assert dish.collect_events() == []
