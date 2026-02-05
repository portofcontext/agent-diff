"""
Box Database Base - SQLAlchemy declarative base and common utilities.

Following patterns from Slack and Linear replicas.
"""

from sqlalchemy.orm import DeclarativeBase
from eval_platform.pydantic_mixin import PydanticMixin


class Base(DeclarativeBase, PydanticMixin):
    """SQLAlchemy declarative base for Box models with Pydantic serialization."""

    pass
