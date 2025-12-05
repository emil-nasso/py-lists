from typing import TYPE_CHECKING
from uuid import uuid4

from app.field_types import BooleanFieldType, NumberFieldType, TextFieldType
from app.models import FieldValue, List

if TYPE_CHECKING:
    from app.repositories import ListRepository


class ListSeeder:
    def __init__(self, repository: "ListRepository") -> None:
        self._repository = repository

    def run(self) -> None:
        """Seed the repository with initial data."""

        list1_text_field = uuid4()
        list1_boolean_field = uuid4()
        list1_number_field = uuid4()
        list1 = List(
            id=uuid4(),
            name="Groceries",
            fields={
                list1_text_field: TextFieldType(name="Item Name"),
                list1_number_field: NumberFieldType(name="Quantity"),
                list1_boolean_field: BooleanFieldType(name="Purchased"),
            },
            items={
                uuid4(): [
                    FieldValue(field_id=list1_text_field, value="Milk"),
                    FieldValue(field_id=list1_number_field, value=2),
                    FieldValue(field_id=list1_boolean_field, value=False),
                ],
                uuid4(): [
                    FieldValue(field_id=list1_text_field, value="Bread"),
                    FieldValue(field_id=list1_number_field, value=1),
                    FieldValue(field_id=list1_boolean_field, value=True),
                ],
            },
        )

        list2_title_field = uuid4()
        list2_author_field = uuid4()
        list2_read_field = uuid4()
        list2 = List(
            id=uuid4(),
            name="Books to Read",
            fields={
                list2_title_field: TextFieldType(name="Title"),
                list2_author_field: TextFieldType(name="Author"),
                list2_read_field: BooleanFieldType(name="Read"),
            },
            items={
                uuid4(): [
                    FieldValue(field_id=list2_title_field, value="1984"),
                    FieldValue(field_id=list2_author_field, value="George Orwell"),
                    FieldValue(field_id=list2_read_field, value=True),
                ],
                uuid4(): [
                    FieldValue(field_id=list2_title_field, value="The Great Gatsby"),
                    FieldValue(field_id=list2_author_field, value="F. Scott Fitzgerald"),
                    FieldValue(field_id=list2_read_field, value=False),
                ],
            },
        )

        self._repository.add(list1)
        self._repository.add(list2)
