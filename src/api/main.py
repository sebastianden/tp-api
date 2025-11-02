"""FastAPI application for review database queries.

This module provides a REST API for querying a PostgreSQL database for review
data. The API supports filtering and pagination for users, businesses, and
reviews with optional CSV export functionality.

Exposed Endpoints:
    GET /users: Retrieve users with optional filtering by country, name, and email.
    GET /businesses: Retrieve businesses with optional filtering by name.
    GET /reviews: Retrieve reviews with detailed user and business information,
                   with optional filtering by rating, user, business, title, content,
                   business name, user name, and user country.

Usage:
    fastapi run main.py --port 8000
"""

import csv
import io
import os
from datetime import datetime
from typing import Annotated

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

app = FastAPI(
    title="TP API",
    description="API for making ad-hoc queries on the reviews database",
)


# Database connection parameters
def get_db_password() -> str:
    """Get database password from Docker secret file."""
    password_file = os.getenv("DB_PASSWORD_FILE")
    try:
        with open(password_file, encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        msg = f"Error reading password file {password_file}: {e}"
        raise RuntimeError(msg) from e


def get_db_config() -> dict:
    """Get database configuration with lazy password loading."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": get_db_password(),
    }


# Pydantic models for response schemas
class User(BaseModel):
    """User/reviewer data model."""

    id: str
    name: str
    email: str
    country: str | None = None


class Business(BaseModel):
    """Business data model."""

    id: str
    name: str


class Review(BaseModel):
    """Review data model with denormalized user and business information."""

    review_id: str
    user_id: str
    business_id: str
    user_name: str
    user_email: str
    user_country: str | None = None
    business_name: str
    review_title: str | None = None
    review_rating: int | None = None
    review_content: str | None = None
    review_ip_address: str | None = None
    review_date: datetime | None = None


def get_db_connection() -> psycopg2.extensions.connection:
    """Get database connection."""
    try:
        return psycopg2.connect(**get_db_config(), cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {e!s}",
        ) from e


@app.get("/")
def read_root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to TP API",
        "endpoints": ["/users", "/businesses", "/reviews"],
    }


@app.get("/users", response_class=StreamingResponse)
def get_users(
    country: Annotated[str | None, Query(description="Filter by country")] = None,
    name: Annotated[str | None, Query(description="Filter by name (contains)")] = None,
    email: Annotated[
        str | None,
        Query(description="Filter by email (contains)"),
    ] = None,
    limit: Annotated[
        int | None,
        Query(description="Limit number of results (optional)", ge=1, le=10000),
    ] = None,
) -> StreamingResponse:
    """Get users as CSV download."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if country:
            query += " AND country ILIKE %s"
            params.append(f"%{country}%")

        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")

        if email:
            query += " AND email ILIKE %s"
            params.append(f"%{email}%")

        query += " ORDER BY id"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        users = cursor.fetchall()

        # Convert to list of dictionaries for CSV
        users_data = [dict(user) for user in users]
        return create_csv_response(users_data, "users.csv")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e!s}") from e
    finally:
        cursor.close()
        conn.close()


@app.get("/businesses", response_class=StreamingResponse)
def get_businesses(
    name: Annotated[
        str | None,
        Query(description="Filter by business name (contains)"),
    ] = None,
    limit: Annotated[
        int | None,
        Query(description="Limit number of results (optional)", ge=1, le=10000),
    ] = None,
) -> StreamingResponse:
    """Get businesses as CSV download."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = "SELECT * FROM businesses WHERE 1=1"
        params = []

        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")

        query += " ORDER BY id"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        businesses = cursor.fetchall()

        # Convert to list of dictionaries for CSV
        businesses_data = [dict(business) for business in businesses]
        return create_csv_response(businesses_data, "businesses.csv")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e!s}") from e
    finally:
        cursor.close()
        conn.close()


@app.get("/reviews", response_class=StreamingResponse)
def get_reviews(  # noqa: C901 PLR0912 PLR0913
    rating: Annotated[
        int | None,
        Query(description="Filter by rating", ge=1, le=5),
    ] = None,
    min_rating: Annotated[
        int | None,
        Query(description="Minimum rating", ge=1, le=5),
    ] = None,
    max_rating: Annotated[
        int | None,
        Query(description="Maximum rating", ge=1, le=5),
    ] = None,
    user_id: Annotated[str | None, Query(description="Filter by user ID")] = None,
    business_id: Annotated[
        str | None,
        Query(description="Filter by business ID"),
    ] = None,
    title: Annotated[
        str | None,
        Query(description="Filter by review title (contains)"),
    ] = None,
    content: Annotated[
        str | None,
        Query(description="Filter by review content (contains)"),
    ] = None,
    business_name: Annotated[
        str | None,
        Query(description="Filter by business name (contains)"),
    ] = None,
    user_name: Annotated[
        str | None,
        Query(description="Filter by user name (contains)"),
    ] = None,
    user_country: Annotated[
        str | None,
        Query(description="Filter by user country"),
    ] = None,
    limit: Annotated[
        int | None,
        Query(description="Limit number of results (optional)", ge=1, le=10000),
    ] = None,
) -> StreamingResponse:
    """Get reviews as CSV download."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Use the view created in schema.sql for detailed information
        query = "SELECT * FROM review_details WHERE 1=1"
        params = []

        if rating:
            query += " AND review_rating = %s"
            params.append(rating)

        if min_rating:
            query += " AND review_rating >= %s"
            params.append(min_rating)

        if max_rating:
            query += " AND review_rating <= %s"
            params.append(max_rating)

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        if business_id:
            query += " AND business_id = %s"
            params.append(business_id)

        if title:
            query += " AND review_title ILIKE %s"
            params.append(f"%{title}%")

        if content:
            query += " AND review_content ILIKE %s"
            params.append(f"%{content}%")

        if business_name:
            query += " AND business_name ILIKE %s"
            params.append(f"%{business_name}%")

        if user_name:
            query += " AND user_name ILIKE %s"
            params.append(f"%{user_name}%")

        if user_country:
            query += " AND user_country ILIKE %s"
            params.append(f"%{user_country}%")

        query += " ORDER BY review_date DESC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        reviews = cursor.fetchall()

        # Convert to list of dictionaries for CSV
        reviews_data = [dict(review) for review in reviews]
        return create_csv_response(reviews_data, "reviews.csv")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e!s}") from e
    finally:
        cursor.close()
        conn.close()


def create_csv_response(data: list[dict], filename: str) -> StreamingResponse:
    """Create a CSV streaming response from query results.

    Args:
        data: List of dictionaries containing the query results
        filename: Name for the downloaded CSV file

    Returns:
        StreamingResponse with CSV data for download

    """
    if not data:
        # Return empty CSV with headers if no data
        output = io.StringIO()
        output.write("No data found\n")
        output.seek(0)
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
