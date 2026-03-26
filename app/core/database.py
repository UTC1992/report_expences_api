"""
Future PostgreSQL session / engine wiring.

Keep SQLAlchemy (or asyncpg) imports isolated here so domain and application
stay persistence-agnostic. Replace `NotImplementedError` bodies when connecting.
"""

from collections.abc import AsyncGenerator
from typing import Any


def get_engine() -> Any | None:
    """Return a SQLAlchemy engine when DATABASE_URL is configured."""
    return None


async def get_session() -> AsyncGenerator[Any, None]:
    """Yield an async session for request-scoped repositories."""
    raise NotImplementedError("Wire SQLAlchemy async session when using PostgreSQL.")
