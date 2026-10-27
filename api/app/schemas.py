"""Modelli Pydantic: input validati (422 con dettagli) e forma delle risposte in OpenAPI."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Il silenzio di Trieste"])
    author_id: int = Field(ge=1)
    category_id: int = Field(ge=1)
    price: float = Field(ge=0, le=999, examples=[14.9])
    isbn: str | None = Field(default=None, max_length=20)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=1400, le=2100)
    language: str = Field(default="it", min_length=2, max_length=5)
    in_stock: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict, examples=[{"format": "brossura", "ebook": True}])
    tags: list[str] = Field(default_factory=list, examples=[["novità"]])


class BookPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author_id: int | None = Field(default=None, ge=1)
    category_id: int | None = Field(default=None, ge=1)
    price: float | None = Field(default=None, ge=0, le=999)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=1400, le=2100)
    language: str | None = None
    in_stock: bool | None = None
    attributes: dict[str, Any] | None = None
    tags: list[str] | None = None


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    city: str = Field(min_length=2, max_length=60)


class OrderItemIn(BaseModel):
    book_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=50)


class Address(BaseModel):
    street: str
    city: str
    zip: str = Field(pattern=r"^\d{5}$")
    country: str = Field(default="IT", min_length=2, max_length=2)


class OrderIn(BaseModel):
    customer_id: int = Field(ge=1)
    items: list[OrderItemIn] = Field(min_length=1, max_length=20)
    shipping_address: Address


OrderStatus = Literal["pending", "paid", "shipped", "delivered", "cancelled"]


class OrderPatch(BaseModel):
    status: OrderStatus


class ReviewIn(BaseModel):
    customer_id: int = Field(ge=1)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


# --- /query: filtri strutturati -------------------------------------------------------

Op = Literal["eq", "ne", "lt", "lte", "gt", "gte", "in", "like", "is_null"]


class Condition(BaseModel):
    field: str = Field(examples=["price", "attributes.format"])
    op: Op = "eq"
    value: Any = None


class Group(BaseModel):
    and_: list["Condition | Group"] | None = Field(default=None, alias="and")
    or_: list["Condition | Group"] | None = Field(default=None, alias="or")


class QueryIn(BaseModel):
    from_: Literal["books", "authors", "customers", "orders", "reviews"] = Field(alias="from", examples=["books"])
    select: list[str] | None = Field(default=None, examples=[["id", "title", "price"]])
    where: Condition | Group | None = None
    order_by: list[str] = Field(default_factory=list, examples=[["-price"]])
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    model_config = {"populate_by_name": True}


class SqlIn(BaseModel):
    sql: str = Field(min_length=6, max_length=4000, examples=["SELECT title, price FROM books ORDER BY price DESC LIMIT 5"])
    params: list[Any] = Field(default_factory=list)
    explain: bool = False
