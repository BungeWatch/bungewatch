from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base for all ORM models. Alembic's env.py imports this to autogenerate migrations."""
    pass
