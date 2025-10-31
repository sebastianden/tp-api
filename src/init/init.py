"""Data ingestion script for TP API review system.

This module loads denormalized review data from an Excel file, normalizes the
data into three separate tables (users, businesses, reviews), inserts the data
into PostgreSQL and verifies that the data was loaded successfully.

Usage:
    python init.py

Environment Variables:
    DB_HOST: Database host (default: localhost)
    DB_PORT: Database port (default: 5432)
    DB_NAME: Database name (default: postgres)
    DB_USER: Database user (default: postgres)
    DB_PASSWORD: Database password (default: password)
"""

import os
from typing import Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Input file path - relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DATA_PATH = os.path.join(SCRIPT_DIR, "tp_reviews.xlsx")

# Database connection parameters
# pylint: disable=R0801
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
}


def load_excel_data(file_path: str) -> pd.DataFrame:
    """Loads data from Excel file.

    Args:
        file_path: Path to the Excel file to load.

    Returns:
        DataFrame containing the loaded Excel data.

    Raises:
        Exception: If the Excel file cannot be loaded.
    """
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Loaded {len(df)} rows from Excel file")
        return df
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        raise


def clean_and_normalize_data(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Takes denormalized review data and splits it into three normalized
    tables: users, businesses, and reviews with proper relationships.
    Deduplicates entries as needed.

    Args:
        df: Raw DataFrame containing denormalized review data with columns:
        - Reviewer Id, Reviewer Name, Email Address, Reviewer Country
        - Business Id, Business Name
        - Review Id, Review Title, Review Rating, Review Content,
            Review IP Address, Review Date

    Returns:
        Tuple of three DataFrames:
        - users_df: Unique users with id, name, email, country
        - businesses_df: Unique businesses with id, name
        - reviews_df: Reviews with user_id and business_id foreign keys
    """

    # Extract unique users
    users_df = df[
        ["Reviewer Id", "Reviewer Name", "Email Address", "Reviewer Country"]
    ].drop_duplicates(subset=["Reviewer Id"])
    users_df.columns = ["id", "name", "email", "country"]

    # Extract unique businesses
    businesses_df = df[["Business Id", "Business Name"]].drop_duplicates(
        subset=["Business Id"]
    )
    businesses_df.columns = ["id", "name"]

    # Extract reviews (some reviews are also duplicated, let's get rid of those)
    reviews_df = df[
        [
            "Review Id",
            "Reviewer Id",
            "Business Id",
            "Review Title",
            "Review Rating",
            "Review Content",
            "Review IP Address",
            "Review Date",
        ]
    ].drop_duplicates(subset=["Review Id"])
    reviews_df.columns = [
        "id",
        "user_id",
        "business_id",
        "title",
        "rating",
        "content",
        "ip_address",
        "date",
    ]

    # Convert date to proper datetime format
    reviews_df["date"] = pd.to_datetime(reviews_df["date"])

    # Clean rating column (ensure it's integer)
    reviews_df["rating"] = pd.to_numeric(reviews_df["rating"], errors="coerce")

    print("Normalized data:")
    print(f"- Users: {len(users_df)}")
    print(f"- Businesses: {len(businesses_df)}")
    print(f"- Reviews: {len(reviews_df)}", "\n")

    return users_df, businesses_df, reviews_df


def insert_data(
    conn: psycopg2.extensions.connection,
    users_df: pd.DataFrame,
    businesses_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> None:
    """Inserts normalized data into users, businesses, and reviews tables using
    batch inserts for performance.

    Args:
        conn: Active PostgreSQL database connection.
        users_df: DataFrame with user data (id, name, email, country).
        businesses_df: DataFrame with business data (id, name).
        reviews_df: DataFrame with review data (id, user_id, business_id,
                   title, rating, content, ip_address, date).

    Raises:
        Exception: If database insertion fails, rolls back transaction.
    """
    cursor = conn.cursor()

    try:
        # Insert users
        users_data = [tuple(row) for row in users_df.values]
        execute_values(
            cursor,
            "INSERT INTO users (id, name, email, country) VALUES %s",
            users_data,
            template=None,
            page_size=100,
        )
        print("✅ Inserted users data", "\n")

        # Insert businesses
        businesses_data = [tuple(row) for row in businesses_df.values]
        execute_values(
            cursor,
            "INSERT INTO businesses (id, name) VALUES %s",
            businesses_data,
            template=None,
            page_size=100,
        )
        print("✅ Inserted businesses data", "\n")

        # Insert reviews
        reviews_data = [tuple(row) for row in reviews_df.values]

        # pylint: disable=line-too-long
        execute_values(
            cursor,
            "INSERT INTO reviews (id, user_id, business_id, title, rating, content, ip_address, date) VALUES %s",
            reviews_data,
            template=None,
            page_size=100,
        )
        print("✅ Inserted reviews data", "\n")

        conn.commit()
        print("✅ All data inserted successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting data: {e}")
        raise


def verify_tables(conn: psycopg2.extensions.connection) -> None:
    """Verifies that required tables exist in the database and data has been
    loaded. Checks the row counts in users, businesses, and reviews tables and
    prints a summary of the data that was loaded.

    Args:
        conn: Active PostgreSQL database connection.
    """
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM businesses")
    business_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reviews")
    review_count = cursor.fetchone()[0]

    print("Database summary:")
    print(f"- Users: {user_count}")
    print(f"- Businesses: {business_count}")
    print(f"- Reviews: {review_count}", "\n")


def main() -> None:
    """Main function to load, process, insert, and verify data."""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database", "\n")

        # Load and process data
        df = load_excel_data(INPUT_DATA_PATH)
        users_df, businesses_df, reviews_df = clean_and_normalize_data(df)

        # Insert data
        insert_data(conn, users_df, businesses_df, reviews_df)

        # Verify tables and data
        verify_tables(conn)

        conn.close()
        print("✅ Data processing completed successfully", "\n")

    except Exception as e:
        print(f"Error in main process: {e}")
        raise


if __name__ == "__main__":

    main()
