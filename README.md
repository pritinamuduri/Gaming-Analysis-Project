# 🎾 Tennis Rankings Explorer — SportRadar API



An end-to-end data analytics project that extracts tennis competition,

venue, and doubles competitor ranking data from the SportRadar API,

cleans and normalizes it into a MySQL database, and presents it through

an interactive Streamlit dashboard with search, filters, and leaderboards.



## Problem Statement



The SportRadar Event Explorer project develops a comprehensive solution

for managing, visualizing, and analyzing sports competition data from the

SportRadar API. It parses JSON data, stores it in a relational database,

and provides intuitive insights into tournaments, competition hierarchies,

and event details.



## Business Use Cases



- **Event Exploration** — navigate competition hierarchies (e.g., ATP Vienna events)

- **Trend Analysis** — visualize the distribution of events by type, gender, and level

- **Performance Insights** — analyze player participation across doubles rankings

- **Decision Support** — data-driven insights for event organizers



## What This Project Does



1. **Extracts** competitions, complexes/venues, and doubles competitor

rankings from the SportRadar Tennis API

2. **Cleans** and flattens the nested JSON into six normalized tables

3. **Loads** the data into a MySQL database with proper primary/foreign keys

4. **Analyzes** the data with 20 SQL queries covering competitions, venues, and rankings

5. **Visualizes** everything through an interactive Streamlit dashboard



## Project Structure



| File | Purpose |

|---|---|

| `API.py` | Pulls data from the SportRadar API and saves it as Excel files |

| `clean_data.py` | Cleans and flattens the raw Excel exports into normalized CSVs |

| `load_to_mysql.py` | Creates the MySQL schema and loads the cleaned CSVs |

| `queries.sql` | The 20 required SQL analysis queries |

| `app.py` | The Streamlit dashboard |

| `categories_clean.csv` | Cleaned category data |

| `competitions_clean.csv` | Cleaned competitions data |

| `complexes_clean.csv` | Cleaned complexes data |

| `venues_clean.csv` | Cleaned venues data |

| `competitors_clean.csv` | Cleaned competitors data |

| `competitor_rankings_clean.csv` | Cleaned doubles rankings data |



## Database Schema



Six normalized tables, matching the project's relational design:



- **Categories** (`category_id` PK, `category_name`)

- **Competitions** (`competition_id` PK, `competition_name`, `parent_id`,

`type`, `gender`, `category_id` FK → Categories, `level`)

- **Complexes** (`complex_id` PK, `complex_name`)

- **Venues** (`venue_id` PK, `venue_name`, `city_name`, `country_name`,

`country_code`, `timezone`, `complex_id` FK → Complexes)

- **Competitors** (`competitor_id` PK, `name`, `country`, `country_code`,

`abbreviation`)

- **Competitor_Rankings** (`rank_id` PK auto-increment, `rank`, `movement`,

`points`, `competitions_played`, `competitor_id` FK → Competitors,

`tour`, `gender`, `year`, `week`)



## Setup & Usage



### 1. Install dependencies

```bash

pip install pandas openpyxl requests mysql-connector-python streamlit 

Bash
pip install pandas openpyxl requests mysql-connector-python streamlit
2. Extract Data from SportRadar API
Execute API.py to fetch data from the SportRadar Tennis API endpoints and export the raw nested JSON into Excel spreadsheets:

Bash
python API.py
3. Clean and Normalize Data
Run clean_data.py to flatten nested JSON/Excel fields, drop duplicates, handle missing values, and generate six standardized CSV files:

Bash
python clean_data.py
4. Load Data into MySQL
Ensure your MySQL server is running, then execute load_to_mysql.py. The script will prompt for your local MySQL root password at runtime to build the schema and populate the database:

Bash
python load_to_mysql.py
5. Run SQL Analytical Queries (Optional)
To execute analytical queries directly against the database, open queries.sql in MySQL Workbench or run it via CLI:

Bash
mysql -u root -p tennis_analytics < queries.sql
6. Launch Streamlit Dashboard
