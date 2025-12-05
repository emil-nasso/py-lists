from uuid import UUID

from pydantic import BaseModel

from app.field_types import FieldValueType


class ListCreate(BaseModel):
    name: str


class ListUpdate(BaseModel):
    name: str


class ItemValues(BaseModel):
    """Schema for creating a new item with field values."""

    field_values: dict[UUID, FieldValueType]


class FieldReorderRequest(BaseModel):
    """Schema for reordering fields in a list."""

    field_orders: dict[UUID, int]


class FieldMoveRequest(BaseModel):
    """Schema for moving a field up or down."""

    direction: str  # "up" or "down"
