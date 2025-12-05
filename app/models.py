from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.field_types import FieldTypeUnion, FieldValueType


class FieldValue(BaseModel):
    field_id: UUID
    value: FieldValueType


class List(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    fields: dict[UUID, FieldTypeUnion] = {}
    items: dict[UUID, list[FieldValue]] = {}
    # items is a dict where the key is the item ID and the value is a list
    # containing the FieldValue instances associated with that item
    # This structure allows each item to have multiple field values associated with it.
