use tennis_analytics;
SELECT COUNT(*) FROM Categories;
SELECT COUNT(*)FROM Competitions;
SELECT COUNT(*)FROM Complexes;
SELECT COUNT(*)FROM Venues;
SELECT COUNT(*)FROM Competitors;
SELECT COUNT(*)FROM Competitor_Rankings;
USE tennis_analytics;

-- ============================================================
-- SECTION 1: COMPETITIONS (7 queries)
-- ============================================================

-- 1) List all competitions along with their category name
SELECT c.competition_id, c.competition_name, cat.category_name
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id;

-- 2) Count the number of competitions in each category
SELECT cat.category_name, COUNT(*) AS total_competitions
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_id, cat.category_name
ORDER BY total_competitions DESC;

-- 3) Find all competitions of type 'doubles'
SELECT competition_id, competition_name, type, gender
FROM Competitions
WHERE type = 'doubles';

-- 4) Get competitions that belong to a specific category (e.g., ITF Men)
SELECT c.competition_id, c.competition_name
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
WHERE cat.category_name = 'ITF Men';

-- 5) Identify parent competitions and their sub-competitions
SELECT parent.competition_name AS parent_competition,
       child.competition_name AS sub_competition
FROM Competitions child
JOIN Competitions parent ON child.parent_id = parent.competition_id;

-- 6) Analyze the distribution of competition types by category
SELECT cat.category_name, c.type, COUNT(*) AS total
FROM Competitions c
JOIN Categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_id, cat.category_name, c.type
ORDER BY cat.category_name, total DESC;

-- 7) List all competitions with no parent (top-level competitions)
SELECT competition_id, competition_name
FROM Competitions
WHERE parent_id IS NULL;


-- ============================================================
-- SECTION 2: COMPLEXES & VENUES (7 queries)
-- ============================================================

-- 1) List all venues along with their associated complex name
SELECT v.venue_name, cx.complex_name
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id;

-- 2) Count the number of venues in each complex
SELECT cx.complex_name, COUNT(*) AS total_venues
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
ORDER BY total_venues DESC;

-- 3) Get details of venues in a specific country (e.g., Chile)
SELECT venue_name, city_name, country_name, timezone
FROM Venues
WHERE country_name = 'Chile';

-- 4) Identify all venues and their timezones
SELECT venue_name, timezone
FROM Venues;

-- 5) Find complexes that have more than one venue
SELECT cx.complex_name, COUNT(*) AS venue_count
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
HAVING COUNT(*) > 1
ORDER BY venue_count DESC;

-- 6) List venues grouped by country
SELECT country_name, COUNT(*) AS total_venues,
       GROUP_CONCAT(venue_name SEPARATOR ', ') AS venues
FROM Venues
GROUP BY country_name
ORDER BY total_venues DESC;

-- 7) Find all venues for a specific complex (e.g., Nacional)
SELECT v.venue_name, v.city_name, v.country_name
FROM Venues v
JOIN Complexes cx ON v.complex_id = cx.complex_id
WHERE cx.complex_name = 'Nacional';


-- ============================================================
-- SECTION 3: COMPETITOR RANKINGS (6 queries)
-- ============================================================

-- 1) Get all competitors with their rank and points
SELECT co.name, co.country, cr.rank, cr.points, cr.tour, cr.gender
FROM Competitor_Rankings cr
JOIN Competitors co ON cr.competitor_id = co.competitor_id;

-- 2) Find competitors ranked in the top 5
SELECT co.name, co.country, cr.rank, cr.tour, cr.gender
FROM Competitor_Rankings cr
JOIN Competitors co ON cr.competitor_id = co.competitor_id
WHERE cr.rank <= 5
ORDER BY cr.tour, cr.gender, cr.rank;

-- 3) List competitors with no rank movement (stable rank)
SELECT co.name, cr.rank, cr.movement, cr.tour
FROM Competitor_Rankings cr
JOIN Competitors co ON cr.competitor_id = co.competitor_id
WHERE cr.movement = 0;

-- 4) Get the total points of competitors from a specific country (e.g., Croatia)
SELECT co.country, SUM(cr.points) AS total_points
FROM Competitor_Rankings cr
JOIN Competitors co ON cr.competitor_id = co.competitor_id
WHERE co.country = 'Croatia'
GROUP BY co.country;

-- 5) Count the number of competitors per country
SELECT country, COUNT(*) AS total_competitors
FROM Competitors
GROUP BY country
ORDER BY total_competitors DESC;

-- 6) Find competitors with the highest points in the latest available snapshot
SELECT co.name, co.country, cr.points, cr.tour, cr.week, cr.year
FROM Competitor_Rankings cr
JOIN Competitors co ON cr.competitor_id = co.competitor_id
WHERE (cr.year, cr.week) = (
    SELECT year, week 
    FROM Competitor_Rankings 
    ORDER BY year DESC, week DESC 
    LIMIT 1
)
ORDER BY cr.points DESC
LIMIT 10;
