"""
Integration tests for the Catalog module using an in-memory SQLite database.

These tests exercise the full stack (router → handler → repository → DB)
without needing a running PostgreSQL instance.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.shared.infrastructure.database import Base, get_db
from src.shared.infrastructure.event_bus import InMemoryEventBus
from src.modules.catalog.presentation.dependencies import get_event_bus
from src.main import app


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

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
app.dependency_overrides[get_event_bus] = override_get_event_bus

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Recreate tables before each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestCreateDish:
    def test_success(self):
        response = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Homemade Lasagna",
                "description": "Three-cheese with béchamel",
                "price": 14.99,
                "currency": "USD",
                "initial_portions": 8,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Homemade Lasagna"
        assert data["available_portions"] == 8
        assert data["is_active"] is True
        assert "id" in data

    def test_invalid_price_returns_400(self):
        response = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Free Food",
                "description": "",
                "price": -5,
                "currency": "USD",
                "initial_portions": 1,
            },
        )
        assert response.status_code == 422  # Pydantic validation (gt=0)

    def test_empty_name_returns_422(self):
        response = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "",
                "description": "",
                "price": 10.0,
                "currency": "USD",
                "initial_portions": 1,
            },
        )
        assert response.status_code == 422


class TestGetDish:
    def test_get_existing(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Tacos",
                "description": "Spicy beef",
                "price": 8.50,
                "currency": "USD",
                "initial_portions": 20,
            },
        )
        dish_id = create.json()["id"]

        response = client.get(f"/api/v1/catalog/dishes/{dish_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Tacos"

    def test_get_nonexistent_returns_404(self):
        response = client.get("/api/v1/catalog/dishes/nonexistent-id")
        assert response.status_code == 404


class TestDeactivateDish:
    def test_deactivate(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Sushi",
                "description": "",
                "price": 22.00,
                "currency": "USD",
                "initial_portions": 5,
            },
        )
        dish_id = create.json()["id"]

        response = client.patch(f"/api/v1/catalog/dishes/{dish_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_double_deactivate_returns_409(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Pizza",
                "description": "",
                "price": 18.00,
                "currency": "USD",
                "initial_portions": 3,
            },
        )
        dish_id = create.json()["id"]
        client.patch(f"/api/v1/catalog/dishes/{dish_id}/deactivate")

        response = client.patch(f"/api/v1/catalog/dishes/{dish_id}/deactivate")
        assert response.status_code == 409


class TestDeductPortions:
    def test_deduct(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Curry",
                "description": "",
                "price": 11.00,
                "currency": "USD",
                "initial_portions": 10,
            },
        )
        dish_id = create.json()["id"]

        response = client.post(
            f"/api/v1/catalog/dishes/{dish_id}/deduct-portions",
            json={"amount": 3},
        )
        assert response.status_code == 200
        assert response.json()["available_portions"] == 7

    def test_deduct_too_many_returns_409(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Salad",
                "description": "",
                "price": 9.00,
                "currency": "USD",
                "initial_portions": 2,
            },
        )
        dish_id = create.json()["id"]

        response = client.post(
            f"/api/v1/catalog/dishes/{dish_id}/deduct-portions",
            json={"amount": 50},
        )
        assert response.status_code == 409


class TestChangeDishPrice:
    def test_change_price(self):
        create = client.post(
            "/api/v1/catalog/dishes/",
            json={
                "seller_id": "seller-001",
                "name": "Burger",
                "description": "",
                "price": 12.00,
                "currency": "USD",
                "initial_portions": 15,
            },
        )
        dish_id = create.json()["id"]

        response = client.patch(
            f"/api/v1/catalog/dishes/{dish_id}/price",
            json={"new_price": 14.50, "currency": "USD"},
        )
        assert response.status_code == 200
        assert response.json()["price"] == "14.50"


class TestListSellerDishes:
    def test_list(self):
        for name in ("Dish A", "Dish B", "Dish C"):
            client.post(
                "/api/v1/catalog/dishes/",
                json={
                    "seller_id": "seller-list",
                    "name": name,
                    "description": "",
                    "price": 10.00,
                    "currency": "USD",
                    "initial_portions": 5,
                },
            )

        response = client.get("/api/v1/catalog/dishes/seller/seller-list")
        assert response.status_code == 200
        assert len(response.json()) == 3
