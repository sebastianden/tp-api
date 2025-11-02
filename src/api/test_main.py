"""Minimal tests for TP API endpoints and CSV functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app, create_csv_response

SUCCESS_STATUS = 200


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_db() -> tuple[MagicMock, MagicMock]:
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == SUCCESS_STATUS
    data = response.json()
    assert data["message"] == "Welcome to TP API"


@patch("main.get_db_connection")
def test_users_endpoint(
    mock_get_db: MagicMock,
    client: TestClient,
    mock_db: tuple[MagicMock, MagicMock],
) -> None:
    """Test users endpoint returns CSV."""
    mock_conn, mock_cursor = mock_db
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchall.return_value = [
        {"id": "user1", "name": "John", "email": "john@example.com"},
    ]

    response = client.get("/users")
    assert response.status_code == SUCCESS_STATUS
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


@patch("main.get_db_connection")
def test_businesses_endpoint(
    mock_get_db: MagicMock,
    client: TestClient,
    mock_db: tuple[MagicMock, MagicMock],
) -> None:
    """Test businesses endpoint returns CSV."""
    mock_conn, mock_cursor = mock_db
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchall.return_value = [{"id": "biz1", "name": "Acme Corp"}]

    response = client.get("/businesses")
    assert response.status_code == SUCCESS_STATUS
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


@patch("main.get_db_connection")
def test_reviews_endpoint(
    mock_get_db: MagicMock,
    client: TestClient,
    mock_db: tuple[MagicMock, MagicMock],
) -> None:
    """Test reviews endpoint returns CSV."""
    mock_conn, mock_cursor = mock_db
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchall.return_value = [
        {"review_id": "rev1", "user_name": "John", "business_name": "Acme"},
    ]

    response = client.get("/reviews")
    assert response.status_code == SUCCESS_STATUS
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_csv_response_with_data() -> None:
    """Test CSV response creation works correctly."""
    data = [{"name": "John", "city": "NYC"}, {"name": "Jane", "city": "LA"}]
    response = create_csv_response(data, "test.csv")

    assert response.media_type == "text/csv"
    assert "filename=test.csv" in response.headers["Content-Disposition"]
    assert response.status_code == SUCCESS_STATUS


def test_csv_response_empty_data() -> None:
    """Test CSV response with no data."""
    response = create_csv_response([], "empty.csv")

    assert response.media_type == "text/csv"
    assert "filename=empty.csv" in response.headers["Content-Disposition"]
    assert response.status_code == SUCCESS_STATUS
