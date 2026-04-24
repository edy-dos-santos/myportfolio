# 📱 Apple App Store — Market Analysis with SQL & Python

> Exploratory data analysis of 7,000+ apps on the Apple App Store, combining SQL (DuckDB) for data profiling and business analysis, and Python (Plotly) for visualisation.

---

## 🎯 Project Objective

This project was designed to simulate the kind of analysis a data analyst might deliver to a product or strategy team evaluating the mobile app market. The central questions were:

- Which genres are most saturated — and which are underserved?
- Do paid apps actually outperform free apps in user ratings?
- What app characteristics (description length, language support, price) correlate with higher ratings?
- Within the lowest-rated genres, which apps are exceptions worth studying?

---

## 🗂️ Dataset

| Table | Source | Records |
|---|---|---|
| `AppleStore_Dataset` | [Kaggle — App Store Apps](https://www.kaggle.com/datasets/ramamet4/app-store-apple-data-set-10k-apps) | ~7,200 apps |
| `AppleStoreDescription` | Same source (companion table) | ~7,200 descriptions |

**Key fields used:** `id`, `track_name`, `prime_genre`, `user_rating`, `rating_count_tot`, `price`, `lang_num`, `app_desc`

---

## 🛠️ Tools & Environment

- **SQL:** DuckDB (cloud-based environment) — chosen for its ability to query CSV files directly and its support for window functions and CTEs
- **Python:** Plotly Express — for interactive bubble chart visualisation
- **Version control:** Git

---

## 🔍 Analysis Structure

### 1. Data Quality Checks
Before any analysis, both tables were validated:
- Unique app ID counts were compared across tables to confirm alignment
- Missing values were checked in critical fields (`track_name`, `user_rating`, `prime_genre`, `app_desc`)
- Cross-table consistency was verified using a `UNION ALL` mismatch check

```sql
-- Example: identify apps present in one table but not the other
SELECT 'AppleStore_Dataset' AS source, track_name
FROM AppleStore_Dataset
WHERE track_name NOT IN (SELECT track_name FROM AppleStoreDescription)
UNION ALL
SELECT 'AppleStoreDescription' AS source, track_name
FROM AppleStoreDescription
WHERE track_name NOT IN (SELECT track_name FROM AppleStore_Dataset);
```

---

### 2. Genre Distribution
Counted apps per genre to map market saturation and identify crowded vs underrepresented categories.

**Key finding:** Games and Entertainment dominate the store volume — but volume alone doesn't indicate quality or opportunity.

---

### 3. Ratings Landscape
Calculated min, max, and average ratings across the full dataset, then broke ratings down by genre using window functions.

**Key finding:** The overall average user rating sits around 3.5/5. Several categories (Catalogs, Finance, Book) consistently underperform.

---

### 4. Low-Rated Genres — Standout Apps
Used a two-step CTE to find, within each of the 10 lowest-rated genres, the single highest-rated app with more than 10,000 ratings — to identify outliers that succeed where their category fails.

```sql
WITH LowRatedGenres AS (
    SELECT prime_genre, AVG(user_rating) AS Avg_Rating
    FROM AppleStore_DataSet
    GROUP BY prime_genre
    ORDER BY Avg_Rating ASC
    LIMIT 10
),
RankedTracks AS (
    SELECT a.prime_genre, a.track_name, a.user_rating, a.rating_count_tot,
           RANK() OVER (PARTITION BY a.prime_genre ORDER BY a.user_rating DESC, a.rating_count_tot DESC) AS rank
    FROM AppleStore_DataSet AS a
    JOIN LowRatedGenres AS lrg ON a.prime_genre = lrg.prime_genre
    WHERE a.rating_count_tot > 10000
)
SELECT prime_genre, track_name, user_rating
FROM RankedTracks
WHERE rank = 1
ORDER BY user_rating DESC;
```

**Visualised as:** Interactive bubble chart (Plotly) — genre on X axis, average rating on Y axis, bubble size = number of apps in genre.

---

### 5. Description Length vs Ratings
Bucketed app descriptions into Short (<500 chars), Medium (500–1000), and Long (1000+), then compared average ratings per bucket.

**Key finding:** Apps with longer, more detailed descriptions consistently achieve higher average ratings — suggesting that user expectations and perceived quality are influenced by how well an app is explained.

---

### 6. Language Support vs Ratings
Bucketed apps by number of supported languages (<10, 10–30, >30).

**Key finding:** The sweet spot is 10–30 languages. Supporting more languages than necessary showed diminishing returns on ratings.

---

### 7. Paid vs Free — Ratings Comparison
Compared average user ratings between free and paid apps.

**Key finding:** Paid apps average higher ratings than free apps. This likely reflects a combination of higher user commitment (paid users are more invested) and lower volume of casual or accidental downloads.

---

### 8. Price Range Distribution
Dynamically bucketed apps into price ranges using `FLOOR`-based logic to distribute price points evenly across brackets.

---

## 📊 Visualisation

The Plotly bubble chart produced for the low-rated genres analysis:

- **X axis:** Genre
- **Y axis:** Average genre rating
- **Bubble size:** Number of apps in that genre
- **Hover:** Genre name and app count

This was built directly from the SQL output using Python's Plotly Express library, demonstrating an end-to-end workflow: SQL query → dataframe → interactive chart.

---

## 💡 Key Takeaways

| Insight | Implication |
|---|---|
| Games/Entertainment are saturated | New entrants face high competition; niche genres may offer better opportunity |
| Paid apps rate higher on average | Monetisation strategy affects perceived quality signals |
| Longer descriptions → better ratings | Documentation and communication quality matter to users |
| 10–30 languages is the optimal range | Broad but targeted localisation outperforms both extremes |
| Low-rated genres still have standout apps | Market opportunity exists even in underperforming categories |

---

## 📁 Repository Structure

```
├── README.md
├── sql/
│   ├── 01_data_quality_checks.sql
│   ├── 02_genre_distribution.sql
│   ├── 03_ratings_analysis.sql
│   ├── 04_low_rated_genres_cte.sql
│   ├── 05_description_length.sql
│   ├── 06_language_support.sql
│   └── 07_paid_vs_free.sql
├── visualisation/
│   └── bubble_chart.py
└── data/
    └── (source files — see Kaggle link above)
```

---

## 👤 Author

**Edy dos Santos** — Data Analyst | Upskilling in Data Engineering
[GitHub Portfolio](https://github.com/edy-dos-santos/myportfolio)
