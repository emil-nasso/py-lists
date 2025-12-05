from uuid import UUID, uuid4

from app.field_types import (
    FieldHandlerRegistry,
    FieldTypeCreateUnion,
    FieldValueType,
)
from app.migration import DataMigrator
from app.models import FieldValue, List
from app.persistence import PersistenceManager


class ListRepository:
    def __init__(
        self,
        field_registry: FieldHandlerRegistry,
        persistence_manager: PersistenceManager,
        migrator: DataMigrator,
    ) -> None:
        self._field_registry = field_registry
        self._persistence_manager = persistence_manager

        # Run migrations before loading lists
        migrator.run()

        # Load existing lists from disk (migrations already applied)
        self._lists = self._persistence_manager.load_all()

    def add(self, list: List) -> List:
        self._lists[list.id] = list
        self._persistence_manager.write_to_disk(list)
        return list

    def get(self, list_id: UUID) -> List | None:
        return self._lists.get(list_id)

    def get_all(self) -> list[List]:
        return list(self._lists.values())

    def update(self, list_id: UUID, name: str | None) -> List | None:
        list = self._lists.get(list_id)
        if not list:
            return None
        if name is not None:
            list.name = name

        self._persistence_manager.write_to_disk(list)
        return list

    def delete(self, list_id: UUID) -> bool:
        if list_id in self._lists:
            del self._lists[list_id]
            self._persistence_manager.delete_from_disk(list_id)
            return True
        return False

    def add_field(self, list_id: UUID, field_create: FieldTypeCreateUnion) -> List | None:
        """Add a field to a list and return the updated list."""
        list = self.get(list_id)
        if not list:
            return None

        # Generate a new field ID
        field_id = uuid4()

        # Calculate next order (max existing order + 1, or 0 if no fields)
        next_order = max((f.order for f in list.fields.values()), default=-1) + 1

        # Use registry to create field instance and get default value
        field = self._field_registry.create_field_instance(field_create)
        field.order = next_order
        default_value = self._field_registry.get_default_value(field)

        # Add the field to the list
        list.fields[field_id] = field

        # Add default field values to all existing items
        for item_values in list.items.values():
            item_values.append(FieldValue(field_id=field_id, value=default_value))

        self._persistence_manager.write_to_disk(list)
        return list

    def delete_field(self, list_id: UUID, field_id: UUID) -> List | None:
        """Delete a field from a list and remove associated field values from items."""
        list = self.get(list_id)
        if not list or field_id not in list.fields:
            return None

        # Remove the field from the list
        del list.fields[field_id]

        # Remove associated field values from all items
        for item_values in list.items.values():
            item_values[:] = [fv for fv in item_values if fv.field_id != field_id]

        self._persistence_manager.write_to_disk(list)
        return list

    def reorder_fields(self, list_id: UUID, field_orders: dict[UUID, int]) -> List | None:
        """
        Reorder fields in a list.

        Args:
            list_id: The list ID
            field_orders: Dictionary mapping field IDs to their new order positions

        Returns:
            Updated list or None if not found

        Raises:
            ValueError: If field_orders is invalid
        """
        list = self.get(list_id)
        if not list:
            return None

        # Validate all field IDs exist
        if set(field_orders.keys()) != set(list.fields.keys()):
            raise ValueError("Must provide orders for all fields")

        # Validate no duplicate orders
        orders = list(field_orders.values())
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate order values are not allowed")

        # Apply new orders
        for field_id, order in field_orders.items():
            list.fields[field_id].order = order

        # Normalize orders (sort by order, then reassign 0, 1, 2, ...)
        sorted_fields = sorted(list.fields.items(), key=lambda x: x[1].order)
        for idx, (field_id, field) in enumerate(sorted_fields):
            field.order = idx

        self._persistence_manager.write_to_disk(list)
        return list

    def move_field(self, list_id: UUID, field_id: UUID, direction: str) -> List | None:
        """
        Move a field up or down in the order.

        Args:
            list_id: The list ID
            field_id: The field to move
            direction: "up" or "down"

        Returns:
            Updated list or None if not found

        Raises:
            ValueError: If direction is invalid or move is not possible
        """
        if direction not in ("up", "down"):
            raise ValueError("Direction must be 'up' or 'down'")

        list = self.get(list_id)
        if not list or field_id not in list.fields:
            return None

        # Get sorted field list
        sorted_fields = sorted(list.fields.items(), key=lambda x: x[1].order)
        current_idx = next(i for i, (fid, _) in enumerate(sorted_fields) if fid == field_id)

        # Determine swap target
        if direction == "up":
            if current_idx == 0:
                raise ValueError("Cannot move first field up")
            swap_idx = current_idx - 1
        else:  # down
            if current_idx == len(sorted_fields) - 1:
                raise ValueError("Cannot move last field down")
            swap_idx = current_idx + 1

        # Swap orders
        current_field_id = sorted_fields[current_idx][0]
        swap_field_id = sorted_fields[swap_idx][0]

        current_order = list.fields[current_field_id].order
        list.fields[current_field_id].order = list.fields[swap_field_id].order
        list.fields[swap_field_id].order = current_order

        self._persistence_manager.write_to_disk(list)
        return list

    def _validate_field_values(self, list: List, field_values: dict[UUID, FieldValueType]) -> None:
        """Validate field values against list fields."""
        # Validate that all fields are provided
        if set(field_values.keys()) != set(list.fields.keys()):
            raise ValueError("Must provide values for all fields")

        # Validate field value types
        for field_id, value in field_values.items():
            field = list.fields.get(field_id)
            if not field:
                raise ValueError(f"Field {field_id} does not exist")

            # Delegate validation to the appropriate handler
            self._field_registry.validate_value(field, value, str(field_id))

    def add_item(self, list_id: UUID, field_values: dict[UUID, FieldValueType]) -> List | None:
        """Add an item to a list with the provided field values and return the updated list."""
        list = self.get(list_id)
        if not list:
            return None

        # Validate field values
        self._validate_field_values(list, field_values)

        # Create FieldValue objects
        item_id = uuid4()
        values = [
            FieldValue(field_id=field_id, value=value) for field_id, value in field_values.items()
        ]

        # Add the item to the list
        list.items[item_id] = values

        self._persistence_manager.write_to_disk(list)
        return list

    def update_item(
        self, list_id: UUID, item_id: UUID, field_values: dict[UUID, FieldValueType]
    ) -> List | None:
        """Update an item in a list and return the updated list."""
        list = self.get(list_id)
        if not list:
            return None

        if item_id not in list.items:
            return None

        # Validate field values
        self._validate_field_values(list, field_values)

        # Create new FieldValue objects
        values = [
            FieldValue(field_id=field_id, value=value) for field_id, value in field_values.items()
        ]

        # Update the item
        list.items[item_id] = values

        self._persistence_manager.write_to_disk(list)
        return list

    def delete_item(self, list_id: UUID, item_id: UUID) -> List | None:
        """Delete an item from a list and return the updated list."""
        list = self.get(list_id)
        if not list or item_id not in list.items:
            return None

        # Remove the item from the list
        del list.items[item_id]

        self._persistence_manager.write_to_disk(list)
        return list
