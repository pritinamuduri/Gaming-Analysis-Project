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

DB_HOST = "mysql-2029afe4-gaming-analysis-project.e.aivencloud.com"
DB_PORT = 12498
DB_USER = "avnadmin"
DB_NAME = "defaultdb"

CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS Categories (
        category_id VARCHAR(50) PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
        FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Complexes (
        complex_id VARCHAR(50) PRIMARY KEY,
        complex_name VARCHAR(100) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
        FOREIGN KEY (complex_id) REFERENCES Complexes(complex_id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS Competitors (
        competitor_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        country VARCHAR(100) NOT NULL,
        country_code CHAR(3),
        abbreviation VARCHAR(10) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
        FOREIGN KEY (competitor_id) REFERENCES Competitors(competitor_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]

CSV_TO_TABLE = [
    ("categories_clean.csv", "Categories", None),
    ("competitions_clean.csv", "Competitions", None),
    ("complexes_clean.csv", "Complexes", None),
    ("venues_clean.csv", "Venues", None),
    ("competitors_clean.csv", "Competitors", None),
    ("competitor_rankings_clean.csv", "Competitor_Rankings",
     ["rank", "movement", "points", "competitions_played",
      "competitor_id", "tour", "gender", "year", "week"]),
]


def create_database_and_tables(cursor) -> None:
    """Create all six tables if they do not already exist."""
    for statement in CREATE_TABLE_STATEMENTS:
        cursor.execute(statement)
    logging.info("Database tables initialized successfully.")


def load_csv_into_table(cursor, connection, filename: str, table: str,
                         columns) -> None:
    """Read one CSV and INSERT (or IGNORE on duplicate) its rows into the given table."""
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        logging.error(f"File not found: {filename} -- skipping {table}.")
        return

    if df.empty:
        logging.warning(f"File {filename} is empty -- skipping {table}.")
        return

    if columns is not None:
        df = df[columns]

    df = df.replace({np.nan: None})

    column_names = list(df.columns)
    placeholders = ", ".join(["%s"] * len(column_names))
    quoted_columns = ", ".join(f"`{c}`" for c in column_names)
    
    # Using INSERT IGNORE to prevent key constraint crashes on script re-runs
    insert_sql = (
        f"INSERT IGNORE INTO {table} ({quoted_columns}) VALUES ({placeholders})"
    )

    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
    try:
        cursor.executemany(insert_sql, rows)
        connection.commit()
        logging.info(f"Successfully processed {len(rows)} records for table `{table}` from {filename}.")
    except Error as err:
        connection.rollback()
        logging.error(f"Failed to load {filename} into `{table}`: {err}")


def main() -> None:
    password = getpass.getpass(f"MySQL password for {DB_USER}@{DB_HOST}: ")

    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=password,
            database=DB_NAME,
            ssl_disabled=False,
        )
    except Error as err:
        logging.error(f"Could not connect to MySQL instance: {err}")
        return

    cursor = connection.cursor()
    try:
        create_database_and_tables(cursor)
        for filename, table, columns in CSV_TO_TABLE:
            load_csv_into_table(cursor, connection, filename, table, columns)
    finally:
        cursor.close()
        connection.close()
        logging.info("MySQL connection closed.")


if __name__ == "__main__":
    main()