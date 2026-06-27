"""
Database connection utilities for Wahlkompass.

Reads DATABASE_URL from environment, defaults to local development connection.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = "postgresql://wahlkompass:***@localhost:5432/wahlkompass"


def get_database_url() -> str:
    """Return the database URL from environment or default."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_connection():
    """Return a psycopg2 connection to the Wahlkompass database."""
    return psycopg2.connect(get_database_url())


def get_dict_cursor(conn=None):
    """Return a RealDictCursor. Pass an existing connection or create one."""
    if conn is None:
        conn = get_connection()
    return conn.cursor(cursor_factory=RealDictCursor)
