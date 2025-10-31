from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from datetime import datetime
import os
import io
import csv

app = FastAPI(
    title="TP API", description="API for making ad-hoc queries on the reviews database"
)

TABLES = {
    "reviewers": "reviewers",
    "businesses": "businesses",
    "reviews": "review_details",
}

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
}


# Pydantic models for response schemas
class Reviewer(BaseModel):
    id: str
    name: str
    email: str
    country: Optional[str] = None


class Business(BaseModel):
    id: str
    name: str


class Review(BaseModel):
    review_id: str
    user_id: str
    business_id: str
    reviewer_name: str
    reviewer_email: str
    reviewer_country: Optional[str] = None
    business_name: str
    review_title: Optional[str] = None
    review_rating: Optional[int] = None
    review_content: Optional[str] = None
    review_ip_address: Optional[str] = None
    review_date: Optional[datetime] = None


def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to TP API",
        "endpoints": ["/reviewers", "/businesses", "/reviews"],
    }


@app.get("/reviewers", response_model=List[Reviewer])
def get_reviewers(
    country: Optional[str] = Query(None, description="Filter by country"),
    name: Optional[str] = Query(None, description="Filter by name (contains)"),
    email: Optional[str] = Query(None, description="Filter by email (contains)"),
    limit: int = Query(100, description="Limit number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
):
    """Get reviewers with optional filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = f"SELECT * FROM {TABLES["reviewers"]} WHERE 1=1"
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

        query += " ORDER BY id LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        reviewers = cursor.fetchall()

        return [Reviewer(**reviewer) for reviewer in reviewers]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/businesses", response_model=List[Business])
def get_businesses(
    name: Optional[str] = Query(None, description="Filter by business name (contains)"),
    limit: int = Query(100, description="Limit number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
):
    """Get businesses with optional filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with filters
        query = f"SELECT * FROM {TABLES["businesses"]} WHERE 1=1"
        params = []

        if name:
            query += " AND name ILIKE %s"
            params.append(f"%{name}%")

        query += " ORDER BY id LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        businesses = cursor.fetchall()

        return [Business(**business) for business in businesses]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/reviews", response_model=List[Review])
def get_reviews(
    rating: Optional[int] = Query(None, description="Filter by rating", ge=1, le=5),
    min_rating: Optional[int] = Query(None, description="Minimum rating", ge=1, le=5),
    max_rating: Optional[int] = Query(None, description="Maximum rating", ge=1, le=5),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    business_id: Optional[str] = Query(None, description="Filter by business ID"),
    title: Optional[str] = Query(None, description="Filter by review title (contains)"),
    content: Optional[str] = Query(
        None, description="Filter by review content (contains)"
    ),
    business_name: Optional[str] = Query(
        None, description="Filter by business name (contains)"
    ),
    reviewer_name: Optional[str] = Query(
        None, description="Filter by reviewer name (contains)"
    ),
    reviewer_country: Optional[str] = Query(
        None, description="Filter by reviewer country"
    ),
    limit: int = Query(100, description="Limit number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
):
    """Get reviews with detailed user and business information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Use the view created in schema.sql for detailed information
        query = f"SELECT * FROM {TABLES['reviews']} WHERE 1=1"
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

        if reviewer_name:
            query += " AND reviewer_name ILIKE %s"
            params.append(f"%{reviewer_name}%")

        if reviewer_country:
            query += " AND reviewer_country ILIKE %s"
            params.append(f"%{reviewer_country}%")

        query += " ORDER BY review_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        reviews = cursor.fetchall()

        return [Review(**review) for review in reviews]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def create_csv_response(data: List[dict], filename: str) -> StreamingResponse:
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


if __name__ == "__main__":
    import uvicorn

    # TODO: Why?
    uvicorn.run(app, host="0.0.0.0", port=8000)
