import pytest  
from unittest.mock import patch, MagicMock
from src.services import user_service
from src.models.user import User
from datetime import datetime

# filepath: c:\Users\user-pc\Downloads\Personal Projects\Personalized-Tech-News-Digest\tests\test_user_service.py

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$KIXQJwQJwQJwQJwQJwQJwO",
        totp_secret="BASE32SECRET",
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0)
    )

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
def test_find_user_by_username_found(mock_close, mock_get_conn, mock_user):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (
        mock_user.id, mock_user.username, mock_user.email,
        mock_user.password_hash, mock_user.totp_secret,
        mock_user.created_at, mock_user.updated_at
    )
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user = user_service.find_user_by_username("testuser")
    assert user is not None
    assert user.username == "testuser"
    mock_close.assert_called_once_with(mock_conn)

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
def test_find_user_by_username_not_found(mock_close, mock_get_conn):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user = user_service.find_user_by_username("nouser")
    assert user is None
    mock_close.assert_called_once_with(mock_conn)

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
def test_find_user_by_email_found(mock_close, mock_get_conn, mock_user):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (
        mock_user.id, mock_user.username, mock_user.email,
        mock_user.password_hash, mock_user.totp_secret,
        mock_user.created_at, mock_user.updated_at
    )
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user = user_service.find_user_by_email("test@example.com")
    assert user is not None
    assert user.email == "test@example.com"
    mock_close.assert_called_once_with(mock_conn)

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
def test_find_user_by_email_not_found(mock_close, mock_get_conn):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user = user_service.find_user_by_email("noemail@example.com")
    assert user is None
    mock_close.assert_called_once_with(mock_conn)

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
@patch("src.services.user_service.bcrypt")
def test_create_user_success(mock_bcrypt, mock_close, mock_get_conn, mock_user):
    mock_bcrypt.generate_password_hash.return_value = b"hashed_pw"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (
        mock_user.id, mock_user.username, mock_user.email,
        "hashed_pw", mock_user.totp_secret,
        mock_user.created_at, mock_user.updated_at
    )
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    user = user_service.create_user("testuser", "password", "test@example.com")
    assert user is not None
    assert user.username == "testuser"
    mock_close.assert_called_once_with(mock_conn)

@patch("src.services.user_service.get_db_connection")
@patch("src.services.user_service.close_db_connection")
@patch("src.services.user_service.bcrypt")
def test_update_user_password_success(mock_bcrypt, mock_close, mock_get_conn):
    mock_bcrypt.generate_password_hash.return_value = b"new_hashed_pw"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    result = user_service.update_user_password(1, "newpassword")
    assert result is True
    mock_close.assert_called_once_with(mock_conn)

def test_check_password_true(mock_user):
    with patch.object(user_service.bcrypt, "check_password_hash", return_value=True):
        assert user_service.check_password(mock_user, "password") is True

def test_check_password_false(mock_user):
    with patch.object(user_service.bcrypt, "check_password_hash", return_value=False):
        assert user_service.check_password(mock_user, "wrongpassword") is False