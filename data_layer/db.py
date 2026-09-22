from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL_ENV = "DATABASE_URL"


class DatabaseConfigurationError(RuntimeError):
    """Raised when the database configuration is unavailable."""


def get_database_url() -> str:
    """
    Return the configured PostgreSQL database URL.

    Missing configuration fails closed. No fallback credentials,
    host, database, or connection parameters are invented.
    """
    value = os.getenv(DATABASE_URL_ENV)

    if value is None or not value.strip():
        raise DatabaseConfigurationError(
            "DATABASE_URL is not configured"
        )

    return value.strip()


def build_engine(database_url: str) -> Engine:
    """
    Build a SQLAlchemy engine without opening a database connection.

    Connection establishment is deferred until the engine is actually
    used. No schema creation or migration is performed here.
    """
    if not database_url or not database_url.strip():
        raise DatabaseConfigurationError(
            "database_url is empty"
        )

    normalized_url = database_url.strip()
    parsed_url = make_url(normalized_url)

    if parsed_url.drivername == "postgresql":
        normalized_url = parsed_url.set(
            drivername="postgresql+psycopg"
        ).render_as_string(hide_password=False)

    return create_engine(
        normalized_url,
        future=True,
        pool_pre_ping=True,
    )


def get_engine() -> Engine:
    """
    Build the configured engine on demand.

    Importing this module does not create an engine or connect to the DB.
    """
    return build_engine(get_database_url())


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """
    Build a SQLAlchemy session factory for the supplied engine.
    """
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


@contextmanager
def transaction(
    session_factory: sessionmaker[Session],
) -> Iterator[Session]:
    """
    Provide one explicit database transaction.

    Successful completion commits.
    Any exception rolls back and is re-raised.
    The session is always closed.
    """
    session = session_factory()

    try:
        with session.begin():
            yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
