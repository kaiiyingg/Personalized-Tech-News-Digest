#Type PYTHONPATH=./ pytest tests/ in terminal to run tests
import pytest # type: ignore
from src.database.connection import get_db_connection, close_db_connection

def test_db_connection():
    conn = get_db_connection()
    assert conn is not None
    close_db_connection(conn)
