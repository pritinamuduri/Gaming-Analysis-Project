"""
app.py

Streamlit application for the SportRadar Tennis Analytics project.
Connects to the tennis_analytics MySQL database and provides:

- Homepage dashboard with summary statistics
- Competitions explorer with category/type/gender filters
- Venues & Complexes explorer with country filter
- Competitor search, filtering, and a detail viewer
- Country-wise analysis and leaderboards

Run with:
    streamlit run app.py

You will be asked for your MySQL password in the sidebar the first time
you open the app -- it is kept only in the browser session, never written
to disk, so this file is safe to commit to GitHub.
"""

import mysql.connector
import pandas as pd
import streamlit as st
from mysql.connector import Error

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_NAME = "tennis_analytics"

st.set_page_config(
    page_title="Tennis Rankings Explorer",
    page_icon="🎾",
    layout="wide",
)


# --------------------------------------------------------------------------
# Connection handling
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_connection(password: str):
    """Open (and cache) a MySQL connection for this session's password."""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=password,
        database=DB_NAME,
    )


@st.cache_data(show_spinner=False)
def run_query(_conn, sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a SELECT and return the results as a DataFrame.

    The connection is prefixed with an underscore so Streamlit's cache
    does not try to hash it (connections aren't hashable); the query
    text and params are what determine whether a cached result is reused.
    """
    return pd.read_sql(sql, _conn, params=params)


def require_connection():
    """Ask for the MySQL password once, connect, and stop the app if it
    fails, so the rest of the page only renders once a connection exists.
    """
    if "db_password" not in st.session_state:
        st.session_state.db_password = ""

    with st.sidebar:
        st.header("Database connection")
        st.session_state.db_password = st.text_input(
            "MySQL password",
            type="password",
            value=st.session_state.db_password,
        )

    if not st.session_state.db_password:
        st.info("Enter your MySQL password in the sidebar to continue.")
        st.stop()

    try:
        return get_connection(st.session_state.db_password)
    except Error as err:
        st.error(f"Could not connect to MySQL: {err}")
        st.stop()


# --------------------------------------------------------------------------
# Page sections
# --------------------------------------------------------------------------
def show_homepage(conn):
    st.title("🎾 Tennis Rankings Explorer")
    st.caption(
        "Competition hierarchies, venues, and doubles rankings "
        "from the SportRadar Tennis API."
    )

    col1, col2, col3, col4 = st.columns(4)
    total_competitors = run_query(
        conn, "SELECT COUNT(*) AS n FROM Competitors"
    )["n"][0]
    total_countries = run_query(
        conn, "SELECT COUNT(DISTINCT country) AS n FROM Competitors"
    )["n"][0]
    top_points_df = run_query(
        conn, "SELECT MAX(points) AS n FROM Competitor_Rankings"
    )
    top_points = (
        top_points_df["n"][0]
        if not top_points_df.empty and pd.notna(top_points_df["n"][0])
        else 0
    )
    total_competitions = run_query(
        conn, "SELECT COUNT(*) AS n FROM Competitions"
    )["n"][0]

    col1.metric("Competitors", f"{total_competitors:,}")
    col2.metric("Countries represented", f"{total_countries:,}")
    col3.metric("Highest points", f"{int(top_points):,}")
    col4.metric("Competitions", f"{total_competitions:,}")

    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("Competitions by type")
        by_type = run_query(
            conn,
            "SELECT type, COUNT(*) AS total FROM Competitions "
            "GROUP BY type ORDER BY total DESC",
        )
        st.bar_chart(by_type.set_index("type"))

    with right:
        st.subheader("Competitors by country (top 10)")
        by_country = run_query(
            conn,
            "SELECT country, COUNT(*) AS total FROM Competitors "
            "GROUP BY country ORDER BY total DESC LIMIT 10",
        )
        st.bar_chart(by_country.set_index("country"))


def show_competitions(conn):
    st.title("Competitions")

    categories = run_query(
        conn,
        "SELECT DISTINCT category_name FROM Categories "
        "ORDER BY category_name",
    )["category_name"].tolist()
    types = run_query(
        conn, "SELECT DISTINCT type FROM Competitions ORDER BY type"
    )["type"].tolist()
    genders = run_query(
        conn, "SELECT DISTINCT gender FROM Competitions ORDER BY gender"
    )["gender"].tolist()

    col1, col2, col3 = st.columns(3)
    category = col1.selectbox("Category", ["All"] + categories)
    comp_type = col2.selectbox("Type", ["All"] + types)
    gender = col3.selectbox("Gender", ["All"] + genders)

    query = (
        "SELECT c.competition_name, c.type, c.gender, c.level, "
        "cat.category_name "
        "FROM Competitions c "
        "JOIN Categories cat ON c.category_id = cat.category_id "
        "WHERE 1=1"
    )
    params = []
    if category != "All":
        query += " AND cat.category_name = %s"
        params.append(category)
    if comp_type != "All":
        query += " AND c.type = %s"
        params.append(comp_type)
    if gender != "All":
        query += " AND c.gender = %s"
        params.append(gender)
    query += " ORDER BY c.competition_name"

    results = run_query(conn, query, tuple(params))
    st.write(f"{len(results)} competitions found")
    st.dataframe(results, use_container_width=True, hide_index=True)


def show_venues(conn):
    st.title("Venues & Complexes")

    countries = run_query(
        conn, "SELECT DISTINCT country_name FROM Venues ORDER BY country_name"
    )["country_name"].tolist()
    country = st.selectbox("Filter by country", ["All"] + countries)

    query = (
        "SELECT v.venue_name, v.city_name, v.country_name, v.timezone, "
        "cx.complex_name "
        "FROM Venues v JOIN Complexes cx ON v.complex_id = cx.complex_id "
        "WHERE 1=1"
    )
    params = []
    if country != "All":
        query += " AND v.country_name = %s"
        params.append(country)
    query += " ORDER BY v.country_name, v.venue_name"

    results = run_query(conn, query, tuple(params))
    st.write(f"{len(results)} venues found")
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Complexes with more than one venue")
    multi_venue = run_query(
        conn,
        "SELECT cx.complex_name, COUNT(*) AS venue_count "
        "FROM Venues v JOIN Complexes cx ON v.complex_id = cx.complex_id "
        "GROUP BY cx.complex_id, cx.complex_name HAVING COUNT(*) > 1 "
        "ORDER BY venue_count DESC",
    )
    st.dataframe(multi_venue, use_container_width=True, hide_index=True)


def show_competitors(conn):
    st.title("Competitors")

    countries = run_query(
        conn, "SELECT DISTINCT country FROM Competitors ORDER BY country"
    )["country"].tolist()

    rank_df = run_query(
        conn, "SELECT MAX(`rank`) AS max_r FROM Competitor_Rankings"
    )
    points_df = run_query(
        conn, "SELECT MAX(points) AS max_p FROM Competitor_Rankings"
    )

    max_rank = (
        int(rank_df["max_r"][0])
        if not rank_df.empty and pd.notna(rank_df["max_r"][0])
        else 100
    )
    max_points = (
        int(points_df["max_p"][0])
        if not points_df.empty and pd.notna(points_df["max_p"][0])
        else 1000
    )

    col1, col2 = st.columns(2)
    name_search = col1.text_input("Search by name")
    country = col2.selectbox("Country", ["All"] + countries)

    col3, col4 = st.columns(2)
    rank_range = col3.slider("Rank range", 1, max(10, max_rank), (1, max_rank))
    min_points = col4.slider("Minimum points", 0, max(10, max_points), 0)

    query = (
        "SELECT co.competitor_id, co.name, co.country, co.abbreviation, "
        "cr.rank, cr.points, cr.movement, cr.tour, cr.gender, "
        "cr.competitions_played "
        "FROM Competitors co "
        "JOIN Competitor_Rankings cr ON co.competitor_id = cr.competitor_id "
        "WHERE cr.rank BETWEEN %s AND %s AND cr.points >= %s"
    )
    params = [rank_range[0], rank_range[1], min_points]
    if name_search:
        query += " AND co.name LIKE %s"
        params.append(f"%{name_search}%")
    if country != "All":
        query += " AND co.country = %s"
        params.append(country)
    query += " ORDER BY cr.rank"

    results = run_query(conn, query, tuple(params))
    st.write(f"{len(results)} competitors found")
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Competitor details")
    if not results.empty:
        chosen = st.selectbox(
            "Select a competitor to view details", results["name"].tolist()
        )
        detail = results[results["name"] == chosen].iloc[0]
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Rank", int(detail["rank"]))
        d2.metric("Points", int(detail["points"]))
        d3.metric("Movement", int(detail["movement"]))
        d4.metric("Competitions played", int(detail["competitions_played"]))
        st.write(
            f"**Country:** {detail['country']} ({detail['abbreviation']}) | "
            f"**Tour:** {detail['tour']} | **Gender:** {detail['gender']}"
        )


def show_leaderboards(conn):
    st.title("Leaderboards & Country Analysis")

    st.subheader("Top-ranked competitors")
    top_ranked = run_query(
        conn,
        "SELECT co.name, co.country, cr.rank, cr.points, cr.tour "
        "FROM Competitor_Rankings cr "
        "JOIN Competitors co ON cr.competitor_id = co.competitor_id "
        "ORDER BY cr.rank ASC LIMIT 20",
    )
    st.dataframe(top_ranked, use_container_width=True, hide_index=True)

    st.subheader("Highest points")
    top_points = run_query(
        conn,
        "SELECT co.name, co.country, cr.points, cr.rank, cr.tour "
        "FROM Competitor_Rankings cr "
        "JOIN Competitors co ON cr.competitor_id = co.competitor_id "
        "ORDER BY cr.points DESC LIMIT 20",
    )
    st.dataframe(top_points, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Countries by competitor count and average points")
    country_stats = run_query(
        conn,
        "SELECT co.country, COUNT(*) AS total_competitors, "
        "ROUND(AVG(cr.points), 1) AS avg_points "
        "FROM Competitors co "
        "JOIN Competitor_Rankings cr ON co.competitor_id = cr.competitor_id "
        "GROUP BY co.country ORDER BY total_competitors DESC",
    )
    st.dataframe(country_stats, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    conn = require_connection()

    page = st.sidebar.radio(
        "Navigate",
        [
            "Homepage",
            "Competitions",
            "Venues & Complexes",
            "Competitors",
            "Leaderboards",
        ],
    )

    if page == "Homepage":
        show_homepage(conn)
    elif page == "Competitions":
        show_competitions(conn)
    elif page == "Venues & Complexes":
        show_venues(conn)
    elif page == "Competitors":
        show_competitors(conn)
    elif page == "Leaderboards":
        show_leaderboards(conn)


if __name__ == "__main__":
    main()