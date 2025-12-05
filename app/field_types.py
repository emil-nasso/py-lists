"""
Field Types Module
==================

Centralized module containing all field type related code:
- Field type models
- Field type creation schemas
- Discriminated unions
- Abstract handler base class
- Concrete handler implementations
- Registry system

This module provides a handler pattern for field types, making it easy to add new types
without modifying the repository or other core logic.
"""

from abc import ABC, abstractmethod
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Discriminator

# Type alias for field values
FieldValueType = str | bool | int


# =============================================================================
# Field Type Models
# =============================================================================


class FieldType(BaseModel):
    """Base model for all field types."""

    name: str


class BooleanFieldType(FieldType):
    """Boolean field type model."""

    type: Literal["boolean"] = "boolean"


class TextFieldType(FieldType):
    """Text field type model."""

    type: Literal["text"] = "text"
    multiline: bool = False


class NumberFieldType(FieldType):
    """Number field type model."""

    type: Literal["number"] = "number"


class URLFieldType(FieldType):
    """URL field type model."""

    type: Literal["url"] = "url"


class ImageFieldType(FieldType):
    """Image field type model."""

    type: Literal["image"] = "image"


# Discriminated union of all field type models
FieldTypeUnion = Annotated[
    BooleanFieldType | TextFieldType | NumberFieldType | URLFieldType | ImageFieldType,
    Discriminator("type"),
]


# =============================================================================
# Field Type Creation Schemas
# =============================================================================


class FieldTypeCreate(BaseModel):
    """Base schema for creating field types."""

    name: str


class BooleanFieldTypeCreate(FieldTypeCreate):
    """Schema for creating a boolean field."""

    type: Literal["boolean"] = "boolean"


class TextFieldTypeCreate(FieldTypeCreate):
    """Schema for creating a text field."""

    type: Literal["text"] = "text"
    multiline: bool = False


class NumberFieldTypeCreate(FieldTypeCreate):
    """Schema for creating a number field."""

    type: Literal["number"] = "number"


class URLFieldTypeCreate(FieldTypeCreate):
    """Schema for creating a URL field."""

    type: Literal["url"] = "url"


class ImageFieldTypeCreate(FieldTypeCreate):
    """Schema for creating a URL field."""

    type: Literal["image"] = "image"


# Discriminated union for field creation
FieldTypeCreateUnion = Annotated[
    BooleanFieldTypeCreate
    | TextFieldTypeCreate
    | NumberFieldTypeCreate
    | URLFieldTypeCreate
    | ImageFieldTypeCreate,
    Discriminator("type"),
]


# =============================================================================
# Abstract Handler Base Class
# =============================================================================


# Type variables for generic handler
TFieldType = TypeVar("TFieldType", bound=FieldType)
TFieldTypeCreate = TypeVar("TFieldTypeCreate", bound=FieldTypeCreate)


class FieldHandler(ABC, Generic[TFieldType, TFieldTypeCreate]):
    """
    Abstract base class for field type handlers.

    Each handler encapsulates all type-specific logic for a field type:
    - Default value generation
    - Validation (including custom rules)
    - Instance creation
    - Metadata generation
    """

    @property
    @abstractmethod
    def type_name(self) -> str:
        """The discriminator value for this field type (e.g., 'boolean', 'text')."""
        pass

    @property
    @abstractmethod
    def field_type_class(self) -> type[TFieldType]:
        """The Pydantic model class for this field type."""
        pass

    @property
    @abstractmethod
    def field_create_class(self) -> type[TFieldTypeCreate]:
        """The Pydantic schema class for creating this field type."""
        pass

    @abstractmethod
    def get_default_value(self) -> FieldValueType:
        """Return the default value for this field type."""
        pass

    @abstractmethod
    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        """
        Validate a value against this field type's rules.

        Args:
            value: The value to validate
            field_id: Optional field ID for error messaging

        Raises:
            ValueError: If validation fails
        """
        pass

    @abstractmethod
    def create_field_instance(self, field_create: TFieldTypeCreate) -> TFieldType:
        """
        Create a field type instance from a creation schema.

        Args:
            field_create: The creation schema

        Returns:
            A new field type instance
        """
        pass

    def get_validation_metadata(self) -> dict[str, Any]:
        """
        Return metadata about validation rules for API responses.

        Returns:
            Dictionary with validation metadata
        """
        return {}


# =============================================================================
# Concrete Handler Implementations
# =============================================================================


class BooleanFieldHandler(FieldHandler[BooleanFieldType, BooleanFieldTypeCreate]):
    """Handler for boolean field types."""

    @property
    def type_name(self) -> str:
        return "boolean"

    @property
    def field_type_class(self) -> type[BooleanFieldType]:
        return BooleanFieldType

    @property
    def field_create_class(self) -> type[BooleanFieldTypeCreate]:
        return BooleanFieldTypeCreate

    def get_default_value(self) -> bool:
        return False

    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        if not isinstance(value, bool):
            field_ref = f"Field {field_id}" if field_id else "Field"
            raise ValueError(f"{field_ref} expects a boolean value")

    def create_field_instance(self, field_create: BooleanFieldTypeCreate) -> BooleanFieldType:
        return BooleanFieldType(name=field_create.name)

    def get_validation_metadata(self) -> dict[str, Any]:
        return {"value_type": "boolean", "constraints": {}}


class TextFieldHandler(FieldHandler[TextFieldType, TextFieldTypeCreate]):
    """Handler for text field types with optional validation rules."""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
    ):
        """
        Initialize with optional validation rules.

        Args:
            min_length: Minimum string length
            max_length: Maximum string length
            pattern: Regex pattern for validation
        """
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern

    @property
    def type_name(self) -> str:
        return "text"

    @property
    def field_type_class(self) -> type[TextFieldType]:
        return TextFieldType

    @property
    def field_create_class(self) -> type[TextFieldTypeCreate]:
        return TextFieldTypeCreate

    def get_default_value(self) -> str:
        return ""

    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        field_ref = f"Field {field_id}" if field_id else "Field"

        # Type validation
        if not isinstance(value, str):
            raise ValueError(f"{field_ref} expects a string value")

        # Custom validation rules
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(f"{field_ref} must be at least {self.min_length} characters long")

        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(f"{field_ref} must be at most {self.max_length} characters long")

        if self.pattern is not None:
            import re

            if not re.match(self.pattern, value):
                raise ValueError(f"{field_ref} must match pattern: {self.pattern}")

    def create_field_instance(self, field_create: TextFieldTypeCreate) -> TextFieldType:
        return TextFieldType(name=field_create.name, multiline=field_create.multiline)

    def get_validation_metadata(self) -> dict[str, Any]:
        return {
            "value_type": "string",
            "constraints": {
                "min_length": self.min_length,
                "max_length": self.max_length,
                "pattern": self.pattern,
            },
        }


class NumberFieldHandler(FieldHandler[NumberFieldType, NumberFieldTypeCreate]):
    """Handler for number field types with optional validation rules."""

    def __init__(self, min_value: int | None = None, max_value: int | None = None):
        """
        Initialize with optional validation rules.

        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.min_value = min_value
        self.max_value = max_value

    @property
    def type_name(self) -> str:
        return "number"

    @property
    def field_type_class(self) -> type[NumberFieldType]:
        return NumberFieldType

    @property
    def field_create_class(self) -> type[NumberFieldTypeCreate]:
        return NumberFieldTypeCreate

    def get_default_value(self) -> int:
        # If min_value is set and > 0, use it as default
        if self.min_value is not None and self.min_value > 0:
            return self.min_value
        return 0

    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        field_ref = f"Field {field_id}" if field_id else "Field"

        # Type validation
        if not isinstance(value, int):
            raise ValueError(f"{field_ref} expects a number value")

        # Custom validation rules
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{field_ref} must be at least {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{field_ref} must be at most {self.max_value}")

    def create_field_instance(self, field_create: NumberFieldTypeCreate) -> NumberFieldType:
        return NumberFieldType(name=field_create.name)

    def get_validation_metadata(self) -> dict[str, Any]:
        return {
            "value_type": "integer",
            "constraints": {"min_value": self.min_value, "max_value": self.max_value},
        }


class URLFieldHandler(FieldHandler[URLFieldType, URLFieldTypeCreate]):
    """Handler for URL field types with basic format validation."""

    @property
    def type_name(self) -> str:
        return "url"

    @property
    def field_type_class(self) -> type[URLFieldType]:
        return URLFieldType

    @property
    def field_create_class(self) -> type[URLFieldTypeCreate]:
        return URLFieldTypeCreate

    def get_default_value(self) -> str:
        return ""

    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        field_ref = f"Field {field_id}" if field_id else "Field"

        # Type validation
        if not isinstance(value, str):
            raise ValueError(f"{field_ref} expects a string value")

        # Allow empty URLs
        if not value.strip():
            return

        # Basic URL format validation
        import re

        # Must start with http:// or https://
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError(f"{field_ref} must start with http:// or https://")

        # Basic URL structure validation
        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, value, re.IGNORECASE):
            raise ValueError(f"{field_ref} must be a valid URL starting with http:// or https://")

    def create_field_instance(self, field_create: URLFieldTypeCreate) -> URLFieldType:
        return URLFieldType(name=field_create.name)

    def get_validation_metadata(self) -> dict[str, Any]:
        return {
            "value_type": "string",
            "constraints": {
                "format": "url",
                "allowed_schemes": ["http", "https"],
            },
        }


class ImageFieldHandler(FieldHandler[ImageFieldType, ImageFieldTypeCreate]):
    """Handler for URL field types with basic format validation."""

    @property
    def type_name(self) -> str:
        return "image"

    @property
    def field_type_class(self) -> type[ImageFieldType]:
        return ImageFieldType

    @property
    def field_create_class(self) -> type[ImageFieldTypeCreate]:
        return ImageFieldTypeCreate

    def get_default_value(self) -> str:
        return ""

    def validate_value(self, value: Any, field_id: str | None = None) -> None:
        field_ref = f"Field {field_id}" if field_id else "Field"

        # Type validation
        if not isinstance(value, str):
            raise ValueError(f"{field_ref} expects a string value")

        # Allow empty URLs
        if not value.strip():
            return

        # Basic URL format validation
        import re

        # Must start with http:// or https://
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError(f"{field_ref} must start with http:// or https://")

        # Basic URL structure validation
        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, value, re.IGNORECASE):
            raise ValueError(f"{field_ref} must be a valid URL starting with http:// or https://")

    def create_field_instance(self, field_create: ImageFieldTypeCreate) -> ImageFieldType:
        return ImageFieldType(name=field_create.name)

    def get_validation_metadata(self) -> dict[str, Any]:
        return {
            "value_type": "string",
            "constraints": {
                "format": "url",
                "allowed_schemes": ["http", "https"],
            },
        }


# =============================================================================
# Registry System
# =============================================================================


class FieldHandlerRegistry:
    """
    Registry for field type handlers.

    Provides centralized access to all registered handlers and
    operations that delegate to the appropriate handler.
    """

    def __init__(self):
        self._handlers: dict[str, FieldHandler[Any, Any]] = {}

    def register(self, handler: FieldHandler[Any, Any]) -> None:
        """
        Register a field handler.

        Args:
            handler: The handler instance to register

        Raises:
            ValueError: If a handler for this type is already registered
        """
        type_name = handler.type_name
        if type_name in self._handlers:
            raise ValueError(f"Handler for type '{type_name}' is already registered")
        self._handlers[type_name] = handler

    def get_handler(self, type_name: str) -> FieldHandler[Any, Any]:
        """
        Get a handler by type name.

        Args:
            type_name: The field type name

        Returns:
            The registered handler

        Raises:
            ValueError: If no handler is registered for this type
        """
        if type_name not in self._handlers:
            raise ValueError(f"No handler registered for type '{type_name}'")
        return self._handlers[type_name]

    def get_handler_for_field(self, field: FieldType) -> FieldHandler[Any, Any]:
        """
        Get the handler for a field instance.

        Args:
            field: The field type instance

        Returns:
            The appropriate handler
        """
        return self.get_handler(field.type)  # type: ignore

    def get_handler_for_create(self, field_create: BaseModel) -> FieldHandler[Any, Any]:
        """
        Get the handler for a field creation schema.

        Args:
            field_create: The field creation schema

        Returns:
            The appropriate handler
        """
        # All create schemas have a 'type' field
        return self.get_handler(field_create.type)  # type: ignore

    def get_all_handlers(self) -> list[FieldHandler[Any, Any]]:
        """
        Get all registered handlers.

        Returns:
            List of all handlers
        """
        return list(self._handlers.values())

    def get_default_value(self, field: FieldType) -> FieldValueType:
        """
        Get default value for a field.

        Args:
            field: The field type instance

        Returns:
            The default value
        """
        handler = self.get_handler_for_field(field)
        return handler.get_default_value()

    def validate_value(self, field: FieldType, value: Any, field_id: str | None = None) -> None:
        """
        Validate a value against a field's rules.

        Args:
            field: The field type instance
            value: The value to validate
            field_id: Optional field ID for error messaging

        Raises:
            ValueError: If validation fails
        """
        handler = self.get_handler_for_field(field)
        handler.validate_value(value, field_id)

    def create_field_instance(self, field_create: BaseModel) -> FieldTypeUnion:
        """
        Create a field instance from a creation schema.

        Args:
            field_create: The creation schema

        Returns:
            A new field type instance
        """
        handler = self.get_handler_for_create(field_create)
        return handler.create_field_instance(field_create)  # type: ignore
