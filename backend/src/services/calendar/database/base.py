# Base class for Calendar API database models
from sqlalchemy.orm import DeclarativeBase
from eval_platform.pydantic_mixin import PydanticMixin


class Base(DeclarativeBase, PydanticMixin):
    """Base class for all Calendar API ORM models with Pydantic serialization."""

    pass
