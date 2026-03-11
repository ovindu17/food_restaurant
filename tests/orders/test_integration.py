"""
Integration tests for the Orders module using an in-memory SQLite database.

These tests exercise the full stack (router → handler → repository → DB)
without needing a running PostgreSQL instance.  The Catalog module's
tables are also created so that the CatalogFacade works end-to-end.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.shared.infrastructure.database import Base, get_db
from src.shared.infrastructure.event_bus import InMemoryEventBus
from src.modules.catalog.presentation.dependencies import (
    get_event_bus as get_catalog_event_bus,
)
from src.modules.orders.presentation.dependencies import (
    get_event_bus as get_orders_event_bus,
)
from src.main import app


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite:///./test_orders.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


test_event_bus = InMemoryEventBus()


def override_get_event_bus():
    return test_event_bus


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_catalog_event_bus] = override_get_event_bus
app.dependency_overrides[get_orders_event_bus] = override_get_event_bus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Recreate tables before each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _create_dish(
    seller_id: str = "seller-001",
    name: str = "Homemade Lasagna",
    price: float = 14.99,
    portions: int = 10,
) -> dict:
    """Create a dish via the Catalog API and return the response."""
    resp = client.post(
        "/api/v1/catalog/dishes/",
        json={
            "seller_id": seller_id,
            "name": name,
            "description": "Delicious",
            "price": price,
            "currency": "USD",
            "initial_portions": portions,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _place_order(
    customer_id: str = "customer-001",
    dish_id: str = "",
    quantity: int = 2,
) -> dict:
    """Place an order and return the response."""
    resp = client.post(
        "/api/v1/orders/",
        json={
            "customer_id": customer_id,
            "items": [{"dish_id": dish_id, "quantity": quantity}],
            "notes": "Extra cheese",
        },
    )
    return resp.json(), resp.status_code


# ---------------------------------------------------------------------------
# Tests: Place Order
# ---------------------------------------------------------------------------
class TestPlaceOrder:
    def test_success(self):
        dish = _create_dish()
        data, status = _place_order(dish_id=dish["id"])

        assert status == 201
        assert data["customer_id"] == "customer-001"
        assert data["status"] == "PLACED"
        assert len(data["items"]) == 1
        assert data["items"][0]["dish_id"] == dish["id"]
        assert data["items"][0]["quantity"] == 2
        assert data["notes"] == "Extra cheese"
        assert "id" in data

    def test_deducts_portions_from_catalog(self):
        dish = _create_dish(portions=5)
        _place_order(dish_id=dish["id"], quantity=3)

        # Check remaining portions
        resp = client.get(f"/api/v1/catalog/dishes/{dish['id']}")
        assert resp.status_code == 200
        assert resp.json()["available_portions"] == 2

    def test_unavailable_dish_returns_error(self):
        data, status = _place_order(dish_id="nonexistent-dish")
        assert status in (404, 400)

    def test_empty_items_returns_422(self):
        resp = client.post(
            "/api/v1/orders/",
            json={
                "customer_id": "customer-001",
                "items": [],
                "notes": "",
            },
        )
        assert resp.status_code == 422  # Pydantic validation (min_length=1)


# ---------------------------------------------------------------------------
# Tests: Order Lifecycle
# ---------------------------------------------------------------------------
class TestOrderLifecycle:
    def test_confirm_order(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        resp = client.patch(f"/api/v1/orders/{order_id}/confirm")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CONFIRMED"

    def test_full_lifecycle(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        # Confirm
        resp = client.patch(f"/api/v1/orders/{order_id}/confirm")
        assert resp.json()["status"] == "CONFIRMED"

        # Start preparing
        resp = client.patch(f"/api/v1/orders/{order_id}/prepare")
        assert resp.json()["status"] == "PREPARING"

        # Mark ready
        resp = client.patch(f"/api/v1/orders/{order_id}/ready")
        assert resp.json()["status"] == "READY"

        # Pick up
        resp = client.patch(f"/api/v1/orders/{order_id}/pick-up")
        assert resp.json()["status"] == "PICKED_UP"

    def test_cancel_order(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}/cancel",
            json={"reason": "Changed my mind"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cannot_confirm_cancelled_order(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        client.patch(f"/api/v1/orders/{order_id}/cancel", json={"reason": ""})
        resp = client.patch(f"/api/v1/orders/{order_id}/confirm")
        assert resp.status_code == 409

    def test_cannot_cancel_preparing_order(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        client.patch(f"/api/v1/orders/{order_id}/confirm")
        client.patch(f"/api/v1/orders/{order_id}/prepare")

        resp = client.patch(f"/api/v1/orders/{order_id}/cancel", json={"reason": ""})
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Tests: Queries
# ---------------------------------------------------------------------------
class TestOrderQueries:
    def test_get_order_by_id(self):
        dish = _create_dish()
        order_data, _ = _place_order(dish_id=dish["id"])
        order_id = order_data["id"]

        resp = client.get(f"/api/v1/orders/{order_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_get_nonexistent_order_returns_404(self):
        resp = client.get("/api/v1/orders/nonexistent-id")
        assert resp.status_code == 404

    def test_list_customer_orders(self):
        dish = _create_dish(portions=20)
        _place_order(customer_id="cust-A", dish_id=dish["id"], quantity=1)
        _place_order(customer_id="cust-A", dish_id=dish["id"], quantity=2)
        _place_order(customer_id="cust-B", dish_id=dish["id"], quantity=1)

        resp = client.get("/api/v1/orders/", params={"customer_id": "cust-A"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(o["customer_id"] == "cust-A" for o in data)
