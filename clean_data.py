"""
clean_data.py

Cleans the three raw SportRadar exports 
(competitions.xlsx, complexes.xlsx, double_competitors_rankings.xlsx) and 
flattens them into six normalized tables that match the project's SQL schema:

1. categories.csv            -> Categories table
2. competitions.csv          -> Competitions table
3. complexes.csv             -> Complexes table
4. venues.csv                -> Venues table
5. competitors.csv           -> Competitors table
6. competitor_rankings.csv   -> Competitor_Rankings table

Run this from the same folder as the three raw .xlsx files:
python clean_data.py
"""

import ast
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Raw input files (edit these paths if your files live elsewhere)
COMPETITIONS_FILE = "competitions.xlsx"
COMPLEXES_FILE = "complexes.xlsx"
RANKINGS_FILE = "double_competitors_rankings.xlsx"


def safe_parse(value):
    """
    Safely parse a stringified Python literal (dict or list) back into a real object.
    Excel stores nested JSON as plain text, so cells like 
    "{'id': 'sr:category:3', 'name': 'ATP'}" come back as strings, not dicts.
    Returns None for missing/NaN values instead of raising.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (dict, list)):
        return value  # already parsed
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as err:
        logging.warning(f"Could not parse value: {value!r} ({err})")
        return None


def clean_competitions(filepath: str):
    """
    Splits competitions.xlsx into two normalized tables:
    - categories: category_id, category_name
    - competitions: competition_id, competition_name, parent_id, type, gender, category_id
    """
    logging.info(f"Reading {filepath}...")
    df = pd.read_excel(filepath)

    # Pull the nested category dict apart into its own columns
    parsed_categories = df["category"].apply(safe_parse)
    df["category_id"] = parsed_categories.apply(lambda c: c["id"] if c else None)
    df["category_name"] = parsed_categories.apply(lambda c: c["name"] if c else None)

    # Categories table: unique category_id / category_name pairs
    categories = (
        df[["category_id", "category_name"]]
        .dropna(subset=["category_id"])
        .drop_duplicates(subset=["category_id"])
        .reset_index(drop=True)
    )

    # Competitions table
    competitions = df.rename(
        columns={"id": "competition_id", "name": "competition_name"}
    )[
        [
            "competition_id",
            "competition_name",
            "parent_id",
            "type",
            "gender",
            "category_id",
        ]
    ].reset_index(drop=True)

    logging.info(f"Categories: {len(categories)} rows | Competitions: {len(competitions)} rows")
    return categories, competitions


def clean_complexes(filepath: str):
    """
    Splits complexes.xlsx into two normalized tables:
    - complexes: complex_id, complex_name
    - venues: venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id
    """
    logging.info(f"Reading {filepath}...")
    df = pd.read_excel(filepath)

    complexes = df.rename(columns={"id": "complex_id", "name": "complex_name"})[
        ["complex_id", "complex_name"]
    ].drop_duplicates(subset=["complex_id"]).reset_index(drop=True)

    # Explode the nested venues list: one row per venue
    venue_rows = []
    for _, row in df.iterrows():
        venues = safe_parse(row["venues"])
        if not venues:
            continue  # complex has no venues on file
        for v in venues:
            venue_rows.append(
                {
                    "venue_id": v.get("id"),
                    "venue_name": v.get("name"),
                    "city_name": v.get("city_name"),
                    "country_name": v.get("country_name"),
                    "country_code": v.get("country_code"),
                    "timezone": v.get("timezone"),
                    "complex_id": row["id"],
                }
            )

    venues = pd.DataFrame(venue_rows).drop_duplicates(subset=["venue_id"]).reset_index(drop=True)
    logging.info(f"Complexes: {len(complexes)} rows | Venues: {len(venues)} rows")
    return complexes, venues


import logging
import pandas as pd


def clean_rankings(filepath: str):
    """
    Splits the already-flattened double_competitors_rankings.xlsx into two
    normalized tables:
    - competitors: competitor_id, name, country, country_code, abbreviation
    - competitor_rankings: rank_id, rank, movement, points, competitions_played, competitor_id, tour, gender, year, week
    """
    logging.info(f"Reading {filepath}...")
    df = pd.read_excel(filepath)

    competitor_rankings = df[
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
        ]
    ].reset_index(drop=True)
    competitor_rankings.insert(0, "rank_id", competitor_rankings.index + 1)

    competitors = (
        df[["competitor_id", "name", "country", "country_code", "abbreviation"]]
        .dropna(subset=["competitor_id"])
        .drop_duplicates(subset=["competitor_id"])
        .reset_index(drop=True)
    )

    logging.info(
        f"Competitors: {len(competitors)} rows | Competitor_Rankings: {len(competitor_rankings)} rows"
    )
    return competitors, competitor_rankings

def main():
    categories, competitions = clean_competitions(COMPETITIONS_FILE)
    complexes, venues = clean_complexes(COMPLEXES_FILE)
    competitors, competitor_rankings = clean_rankings(RANKINGS_FILE)

    categories.to_csv("categories_clean.csv", index=False)
    competitions.to_csv("competitions_clean.csv", index=False)
    complexes.to_csv("complexes_clean.csv", index=False)
    venues.to_csv("venues_clean.csv", index=False)
    competitors.to_csv("competitors_clean.csv", index=False)
    competitor_rankings.to_csv("competitor_rankings_clean.csv", index=False)

    logging.info("All cleaned tables saved as *_clean.csv in the current folder.")


if __name__ == "__main__":
    main()