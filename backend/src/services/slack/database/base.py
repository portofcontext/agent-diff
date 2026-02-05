from sqlalchemy.orm import DeclarativeBase
from eval_platform.pydantic_mixin import PydanticMixin


class Base(DeclarativeBase, PydanticMixin):
    """Base class for Slack ORM models with Pydantic serialization."""

    pass
