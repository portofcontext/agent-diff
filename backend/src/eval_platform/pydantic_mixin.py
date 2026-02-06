"""
Pydantic mixin for SQLAlchemy models.

Adds Pydantic serialization/validation methods to SQLAlchemy ORM models
without requiring changes to existing model definitions.
"""

import json
import types
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Type, TypeVar, Union, get_args, get_origin
from uuid import UUID

from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy import inspect as sa_inspect

T = TypeVar("T", bound="PydanticMixin")


def resolve_pydantic_type(tp):
    """Recursively walk a type and replace any PydanticMixin subclass with its pydantic model."""
    # Base case: a concrete PydanticMixin subclass
    if isinstance(tp, type) and issubclass(tp, PydanticMixin):
        return tp.get_pydantic_model()

    origin = get_origin(tp)
    args = get_args(tp)

    if origin is None or not args:
        return tp

    resolved_args = tuple(resolve_pydantic_type(a) for a in args)

    # Union types (typing.Union or X | Y)
    if origin is Union or isinstance(tp, types.UnionType):
        return Union[resolved_args]

    # Generic types like list[X], dict[X, Y], tuple[X, ...], etc.
    return origin[resolved_args]


class PydanticMixin:
    """
    Mixin that adds Pydantic-like methods to SQLAlchemy models.

    Usage:
        class Base(DeclarativeBase, PydanticMixin):
            pass

        class User(Base):
            __tablename__ = "users"
            id: Mapped[str] = mapped_column(String, primary_key=True)
            name: Mapped[str] = mapped_column(String)

        user = User(id="1", name="John")
        user.model_dump()  # {'id': '1', 'name': 'John'}
        user.model_dump_json()  # '{"id": "1", "name": "John"}'
        User.model_validate({'id': '2', 'name': 'Jane'})  # Creates User instance
    """

    @classmethod
    def get_pydantic_model(cls) -> Type[BaseModel]:
        """
        Generate or retrieve cached Pydantic model for this SQLAlchemy model.

        Returns:
            Pydantic model class that mirrors this SQLAlchemy model
        """
        # Cache the Pydantic model on the class
        cache_attr = "_pydantic_model_cache"
        if hasattr(cls, cache_attr):
            return getattr(cls, cache_attr)

        # Get SQLAlchemy inspector
        inspector = sa_inspect(cls)
        field_definitions = {}

        # Process columns
        for column in inspector.columns:
            col_name = column.key
            python_type = Any
            default_value = None

            # Try to extract type from annotation
            if hasattr(cls, "__annotations__") and col_name in cls.__annotations__:
                annotation = cls.__annotations__[col_name]
                python_type = _extract_type_from_annotation(annotation)

            # Make optional if nullable
            if column.nullable and python_type is not Any:
                from typing import Optional

                python_type = Optional[python_type]
                default_value = None
            elif column.nullable:
                default_value = None
            else:
                default_value = ...  # Required

            python_type = resolve_pydantic_type(python_type)
            field_definitions[col_name] = (python_type, default_value)

        # Create Pydantic model
        pydantic_model = create_model(
            f"{cls.__name__}Schema",
            __config__=ConfigDict(from_attributes=True, arbitrary_types_allowed=True),
            **field_definitions,
        )

        # Cache it
        setattr(cls, cache_attr, pydantic_model)
        return pydantic_model

    def model_dump(
        self,
        *,
        mode: str = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        """
        Serialize the model to a dictionary (Pydantic-compatible interface).

        Args:
            mode: Serialization mode ('python' or 'json')
            include: Fields to include
            exclude: Fields to exclude
            exclude_unset: Exclude fields that were not explicitly set
            exclude_defaults: Exclude fields with default values
            exclude_none: Exclude fields with None values
            round_trip: Enable round-trip serialization
            warnings: Show warnings

        Returns:
            Dictionary representation of the model
        """
        inspector = sa_inspect(self.__class__)
        result = {}

        for column in inspector.columns:
            col_name = column.key

            # Apply include/exclude filters
            if include and col_name not in include:
                continue
            if exclude and col_name in exclude:
                continue

            # Get value
            value = getattr(self, col_name, None)

            # Apply filters
            if exclude_none and value is None:
                continue

            # Serialize value based on mode
            if mode == "json":
                value = _serialize_for_json(value)

            result[col_name] = value

        return result

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        """
        Serialize the model to a JSON string (Pydantic-compatible interface).

        Args:
            indent: JSON indentation level
            include: Fields to include
            exclude: Fields to exclude
            exclude_unset: Exclude fields that were not explicitly set
            exclude_defaults: Exclude fields with default values
            exclude_none: Exclude fields with None values
            round_trip: Enable round-trip serialization
            warnings: Show warnings

        Returns:
            JSON string representation of the model
        """
        data = self.model_dump(
            mode="json",
            include=include,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )
        return json.dumps(data, indent=indent, default=str)

    @classmethod
    def model_validate(cls: Type[T], obj: Any) -> T:
        """
        Create a model instance from a dictionary (Pydantic-compatible interface).

        Args:
            obj: Dictionary or object with attributes to validate

        Returns:
            Instance of this model class

        Example:
            user = User.model_validate({'id': '1', 'name': 'John'})
        """
        if isinstance(obj, dict):
            # Create instance from dict
            return cls(**obj)
        elif isinstance(obj, cls):
            # Already an instance
            return obj
        elif hasattr(obj, "__dict__"):
            # Has attributes, extract them
            return cls(**obj.__dict__)
        else:
            raise ValueError(f"Cannot validate {type(obj)} into {cls.__name__}")

    @classmethod
    def model_validate_json(cls: Type[T], json_data: str | bytes) -> T:
        """
        Create a model instance from a JSON string (Pydantic-compatible interface).

        Args:
            json_data: JSON string or bytes to parse

        Returns:
            Instance of this model class

        Example:
            user = User.model_validate_json('{"id": "1", "name": "John"}')
        """
        if isinstance(json_data, bytes):
            json_data = json_data.decode("utf-8")
        data = json.loads(json_data)
        return cls.model_validate(data)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        """
        Generate JSON Schema for this model (Pydantic-compatible interface).

        Returns:
            JSON Schema dictionary
        """
        pydantic_model = cls.get_pydantic_model()
        return pydantic_model.model_json_schema()


def _extract_type_from_annotation(annotation: Any) -> Any:
    """Extract Python type from SQLAlchemy Mapped[] annotation."""
    from typing import Optional

    origin = get_origin(annotation)

    # Handle Mapped[T]
    if origin is not None and hasattr(origin, "__name__"):
        if "Mapped" in str(origin):
            args = get_args(annotation)
            if args:
                inner_type = args[0]
                inner_origin = get_origin(inner_type)

                # Handle Mapped[Optional[T]]
                if inner_origin is type(Optional):
                    inner_args = get_args(inner_type)
                    non_none = [arg for arg in inner_args if arg is not type(None)]
                    if non_none:
                        return non_none[0]

                # Handle Mapped[list[T]]
                if inner_origin is list:
                    return inner_type

                return inner_type

    return Any


def _serialize_for_json(value: Any) -> Any:
    """Serialize Python value to JSON-compatible type."""
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, dict):
        return {k: _serialize_for_json(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_for_json(item) for item in value]
    elif isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    else:
        return str(value)
