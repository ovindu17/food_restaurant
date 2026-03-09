# 🍽️ Homemade Food E-Commerce API

A production-ready backend for a **homemade food marketplace**, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. The application follows a **Modular Monolith** architecture guided by **Domain-Driven Design (DDD)** and **Clean Architecture** principles.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
  - [Modular Monolith](#modular-monolith)
  - [Clean Architecture Layers](#clean-architecture-layers)
  - [Domain-Driven Design Concepts](#domain-driven-design-concepts)
- [Project Structure](#project-structure)
- [Modules](#modules)
  - [Catalog Module](#catalog-module)
- [API Reference](#api-reference)
- [Domain Events](#domain-events)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Database Migrations](#database-migrations)

---

## Overview

The platform enables sellers to list homemade dishes and manage their catalog. The architecture is designed for long-term maintainability — each business capability lives in its own self-contained module that can independently evolve or be extracted into a microservice.

---

## Architecture

### Modular Monolith

The application is structured as a **Modular Monolith** — a single deployable unit composed of clearly bounded, loosely coupled modules. Modules communicate exclusively through:

- **Domain Events** published over an `EventBus` (no direct imports between module internals).
- **Shared kernel** primitives (base classes, event bus abstraction) located in `src/shared/`.

Future modules planned include: `Orders`, `Users`, and `Notifications`.

### Clean Architecture Layers

Each module is organized into four layers (innermost → outermost):

```
Domain  →  Application  →  Infrastructure  →  Presentation
```

| Layer | Responsibility |
|---|---|
| **Domain** | Entities, Aggregate Roots, Value Objects, Domain Events, Repository interfaces, Domain Exceptions |
| **Application** | Command/Query objects, Command Handlers, Query Handlers, DTOs |
| **Infrastructure** | SQLAlchemy ORM models, Repository implementations, Unit of Work, Event Bus |
| **Presentation** | FastAPI routers, Pydantic request/response schemas, Dependency injection, Exception handlers |

> **Dependency rule:** inner layers never import from outer layers. The domain knows nothing about FastAPI, SQLAlchemy, or HTTP.

### Domain-Driven Design Concepts

| Concept | Implementation |
|---|---|
| **Aggregate Root** | `Dish` — the consistency boundary for the Catalog context |
| **Value Objects** | `Money`, `Portions`, `DishId`, `SellerId` — immutable, validated, compared by value |
| **Domain Events** | Emitted by the aggregate on every state change; published after commit |
| **Repository** | Abstract `DishRepository` interface in domain; `SqlAlchemyDishRepository` in infrastructure |
| **Unit of Work** | `SqlAlchemyUnitOfWork` — atomically commits the DB transaction and publishes domain events |
| **Command / Query** | CQRS-style separation — write operations are Commands, reads are Queries |

---

## Project Structure

```
food_restaurant/
├── pyproject.toml               # Pytest configuration
├── requirements.txt             # Python dependencies
├── src/
│   ├── main.py                  # FastAPI app entry point
│   ├── shared/                  # Cross-cutting concerns
│   │   ├── domain/
│   │   │   ├── base.py          # Entity, AggregateRoot, DomainEvent base classes
│   │   │   └── event_bus.py     # Abstract EventBus port
│   │   └── infrastructure/
│   │       ├── database.py      # SQLAlchemy engine, session, settings
│   │       ├── event_bus.py     # InMemoryEventBus implementation
│   │       └── unit_of_work.py  # SqlAlchemyUnitOfWork
│   └── modules/
│       └── catalog/
│           ├── domain/
│           │   ├── entities.py        # Dish aggregate root
│           │   ├── events.py          # Domain events
│           │   ├── exceptions.py      # Domain-specific exceptions
│           │   ├── repositories.py    # DishRepository interface
│           │   └── value_objects.py   # Money, Portions, DishId, SellerId
│           ├── application/
│           │   ├── commands.py        # Command & Query DTOs
│           │   ├── command_handlers.py# Write operation handlers
│           │   ├── query_handlers.py  # Read operation handlers
│           │   └── dtos.py            # Response data transfer objects
│           ├── infrastructure/
│           │   ├── models.py          # DishModel (SQLAlchemy ORM)
│           │   └── repositories.py    # SqlAlchemyDishRepository
│           └── presentation/
│               ├── router.py          # FastAPI endpoints
│               ├── schemas.py         # Pydantic request/response schemas
│               ├── dependencies.py    # FastAPI dependency providers
│               └── exception_handlers.py
└── tests/
    └── catalog/
        ├── test_domain.py       # Pure unit tests (no I/O)
        └── test_integration.py  # Full-stack tests with in-memory SQLite
```

---

## Modules

### Catalog Module

Manages the lifecycle of dishes that sellers list on the platform.

#### Domain Rules

- A dish name must be between 2 and 100 characters.
- Price must be a positive monetary amount using a 3-letter ISO currency code (e.g., `USD`).
- Portions are non-negative integers; they cannot be deducted below zero.
- A seller cannot have more than **50 active dishes** at a time.
- A dish that is already deactivated cannot be deactivated again.

#### Dish States & Transitions

```
Created ──► Active ──► Deactivated
                └──► Portions deducted (by Orders module)
                └──► Portions exhausted (fires PortionsExhaustedEvent)
```

#### Domain Exceptions

| Exception | Meaning |
|---|---|
| `DishNotFoundError` | Dish ID does not exist |
| `DishAlreadyDeactivatedError` | Dish is already inactive |
| `InsufficientPortionsError` | Requested deduction exceeds available portions |
| `InvalidPriceError` | Price is zero or negative |
| `SellerDishLimitExceededError` | Seller has reached the 50-dish limit |

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs` (Swagger UI) | `http://localhost:8000/redoc`

### Catalog Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/catalog/dishes/` | Create a new dish |
| `PATCH` | `/catalog/dishes/{dish_id}/deactivate` | Soft-delete a dish |
| `PATCH` | `/catalog/dishes/{dish_id}/price` | Update the price of a dish |
| `POST` | `/catalog/dishes/{dish_id}/deduct-portions` | Deduct portions (used by Orders module) |
| `GET` | `/catalog/dishes/{dish_id}` | Retrieve a dish by ID |
| `GET` | `/catalog/dishes/?seller_id={seller_id}` | List all dishes for a seller |
| `GET` | `/health` | Health check |

#### Example: Create a Dish

```http
POST /api/v1/catalog/dishes/
Content-Type: application/json

{
  "seller_id": "seller-001",
  "name": "Homemade Lasagna",
  "description": "Three-cheese with béchamel",
  "price": 14.99,
  "currency": "USD",
  "initial_portions": 8
}
```

**Response `201 Created`:**

```json
{
  "id": "a3f9c1b2-...",
  "seller_id": "seller-001",
  "name": "Homemade Lasagna",
  "description": "Three-cheese with béchamel",
  "price": "14.99",
  "currency": "USD",
  "available_portions": 8,
  "is_active": true,
  "created_at": "2026-03-09T10:00:00Z"
}
```

#### Example: Change Dish Price

```http
PATCH /api/v1/catalog/dishes/{dish_id}/price
Content-Type: application/json

{
  "new_price": 16.50,
  "currency": "USD"
}
```

#### Example: Deduct Portions

```http
POST /api/v1/catalog/dishes/{dish_id}/deduct-portions
Content-Type: application/json

{
  "amount": 2
}
```

---

## Domain Events

Every state-changing operation on the `Dish` aggregate emits a domain event. These events are collected after a successful database commit and published through the `EventBus` to any registered subscribers.

| Event | Trigger |
|---|---|
| `DishCreatedEvent` | A new dish is listed |
| `DishPriceChangedEvent` | The price of a dish is updated |
| `DishDeactivatedEvent` | A dish is deactivated |
| `PortionsDeductedEvent` | Portions are successfully deducted |
| `PortionsExhaustedEvent` | Portions reach zero after a deduction |

> Other modules (e.g., `Notifications`) subscribe to events like `PortionsExhaustedEvent` without importing anything from the Catalog module.

---

## Tech Stack

| Concern | Technology |
|---|---|
| Web Framework | [FastAPI](https://fastapi.tiangolo.com/) 0.110 |
| ASGI Server | [Uvicorn](https://www.uvicorn.org/) 0.27 |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 |
| Data Validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Settings | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 2.2 |
| Database | [PostgreSQL](https://www.postgresql.org/) (SQLite for tests) |
| DB Driver | psycopg2-binary 2.9 |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) 1.13 |
| Testing | [pytest](https://pytest.org/) + FastAPI `TestClient` |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (running locally or via Docker)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd food_restaurant
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

The application is configured via environment variables (prefixed with `APP_`). Create a `.env` file in the project root:

```env
APP_DATABASE_URL=postgresql://user:password@localhost/homemade_food_db
APP_DB_POOL_SIZE=10
APP_DB_MAX_OVERFLOW=20
APP_DB_ECHO=false
```

| Variable | Default | Description |
|---|---|---|
| `APP_DATABASE_URL` | `postgresql://user:password@localhost/homemade_food_db` | PostgreSQL connection string |
| `APP_DB_POOL_SIZE` | `10` | SQLAlchemy connection pool size |
| `APP_DB_MAX_OVERFLOW` | `20` | Maximum pool overflow connections |
| `APP_DB_ECHO` | `false` | Log all SQL statements (useful for debugging) |

### Running the Application

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`.

> **Note:** On startup, the application automatically creates any missing database tables. For production deployments, use Alembic migrations instead (see [Database Migrations](#database-migrations)).

---

## Running Tests

The test suite consists of two levels:

- **Unit tests** (`test_domain.py`) — fast, zero I/O, test domain logic and invariants in isolation.
- **Integration tests** (`test_integration.py`) — exercise the full request → handler → repository → database stack using an in-memory SQLite database.

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run only unit tests:

```bash
pytest tests/catalog/test_domain.py
```

Run only integration tests:

```bash
pytest tests/catalog/test_integration.py
```

---

## Database Migrations

[Alembic](https://alembic.sqlalchemy.org/) is included for schema migrations. In production, use Alembic instead of relying on `Base.metadata.create_all`.

Initialize Alembic (first time only):

```bash
alembic init alembic
```

Generate a migration after model changes:

```bash
alembic revision --autogenerate -m "describe your change"
```

Apply all pending migrations:

```bash
alembic upgrade head
```

Roll back the last migration:

```bash
alembic downgrade -1
```
