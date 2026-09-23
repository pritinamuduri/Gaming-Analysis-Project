"""
load_to_mysql.py

Creates the six normalized tables in MySQL (if they don't already exist)
and loads them from the cleaned CSV files produced by clean_data.py:

    categories_clean.csv          -> Categories
    competitions_clean.csv        -> Competitions
    complexes_clean.csv           -> Complexes
    venues_clean.csv              -> Venues
    competitors_clean.csv         -> Competitors
    competitor_rankings_clean.csv -> Competitor_Rankings

Run this from the same folder as the six *_clean.csv files:
    python load_to_mysql.py

You will be prompted for your MySQL password at runtime -- it is never
stored in this file, so it's safe to commit this script to GitHub.
"""

import getpass
import logging

import mysql.connector
import numpy as np
import pandas as pd
from mysql.connector import Error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_NAME = "tennis_analytics"

# Table definitions, in parent-before-child order so foreign keys succeed.
CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS Categories (
        category_id VARCHAR(50) PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Competitions (
        competition_id VARCHAR(50) PRIMARY KEY,
        competition_name VARCHAR(100) NOT NULL,
        parent_id VARCHAR(50),
        type VARCHAR(20) NOT NULL,
        gender VARCHAR(10) NOT NULL,
        category_id VARCHAR(50),
        level VARCHAR(50),
        FOREIGN KEY (category_id) REFERENCES Categories(category_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Complexes (
        complex_id VARCHAR(50) PRIMARY KEY,
        complex_name VARCHAR(100) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Venues (
        venue_id VARCHAR(50) PRIMARY KEY,
        venue_name VARCHAR(100) NOT NULL,
        city_name VARCHAR(100) NOT NULL,
        country_name VARCHAR(100) NOT NULL,
        country_code CHAR(3) NOT NULL,
        timezone VARCHAR(100) NOT NULL,
        complex_id VARCHAR(50),
        FOREIGN KEY (complex_id) REFERENCES Complexes(complex_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Competitors (
        competitor_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        country VARCHAR(100) NOT NULL,
        country_code CHAR(3),
        abbreviation VARCHAR(10) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Competitor_Rankings (
        rank_id INT PRIMARY KEY AUTO_INCREMENT,
        `rank` INT NOT NULL,
        movement INT NOT NULL,
        points INT NOT NULL,
        competitions_played INT NOT NULL,
        competitor_id VARCHAR(50),
        tour VARCHAR(20),
        gender VARCHAR(10),
        year INT,
        week INT,
        FOREIGN KEY (competitor_id) REFERENCES Competitors(competitor_id)
    )
    """,
]

# (csv filename, table name, columns to insert -- None means "all columns")
CSV_TO_TABLE = [
    ("categories_clean.csv", "Categories", None),
    ("competitions_clean.csv", "Competitions", None),
    ("complexes_clean.csv", "Complexes", None),
    ("venues_clean.csv", "Venues", None),
    ("competitors_clean.csv", "Competitors", None),
    # rank_id is AUTO_INCREMENT, so it is left out of the insert.
    (
        "competitor_rankings_clean.csv",
        "Competitor_Rankings",
        [
            "rank",
            "movement",
            "points",
            "competitions_played",
            "competitor_id",
            "tour",
            "gender",
            "year",
            "week",
        ],
    ),
]


def create_database_and_tables(cursor) -> None:
    """Create the database (if missing) and all six tables."""
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.execute(f"USE `{DB_NAME}`")
    
    for stmt in CREATE_TABLE_STATEMENTS:
        cursor.execute(stmt)
    
    logging.info(f"Database '{DB_NAME}' and all tables ensured.")


def load_csv_to_table(cursor, csv_path: str, table_name: str, cols: list = None) -> None:
    """Reads a cleaned CSV file and inserts its rows into the specified MySQL table."""
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logging.error(f"File not found: {csv_path}. Skipping table {table_name}.")
        return

    if df.empty:
        logging.warning(f"{csv_path} is empty. No rows inserted into {table_name}.")
        return

    if cols:
        df = df[cols]
    else:
        cols = list(df.columns)

    # Convert pandas NaN values to Python None for MySQL NULL conversion
    df = df.replace({np.nan: None})

    # Prepare parameterized query
    quoted_cols = [f"`{col}`" for col in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    query = f"INSERT INTO `{table_name}` ({', '.join(quoted_cols)}) VALUES ({placeholders})"

    # Convert DataFrame records to list of tuples
    records = [tuple(x) for x in df.to_numpy()]

    cursor.executemany(query, records)
    logging.info(f"Loaded {len(records)} rows from {csv_path} into `{table_name}`.")


def main():
    password = getpass.getpass(prompt=f"Enter MySQL password for {DB_USER}: ")

    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # 1. Create DB and schema
            create_database_and_tables(cursor)

            # 2. Populate tables from CSVs
            for csv_file, table, columns in CSV_TO_TABLE:
                load_csv_to_table(cursor, csv_file, table, columns)

            connection.commit()
            logging.info("All data loaded successfully and transaction committed.")

    except Error as e:
        logging.error(f"Error while connecting to or executing MySQL queries: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logging.info("MySQL connection closed.")


if __name__ == "__main__":
    main()
