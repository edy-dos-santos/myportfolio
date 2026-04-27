# 📱 Apple App Store — Market Analysis with SQL & Python

> Exploratory data analysis of 7,000+ apps on the Apple App Store, using SQL (PostgreSQL) for data profiling and business analysis, and Python (Plotly) for visualisation.

---

## 🎯 Objective

In this scenario, the stakeholder is an app developer aiming to create a successful, marketable app. To achieve this, the developer seeks to understand the most popular app categories, optimal pricing strategies, and how to maximise platform user ratings.

---

## 🔄 Workflow Overview

**1. Dataset Acquisition** — Sourced appropriate datasets from Kaggle.com to support the analysis.

**2. Data Exploration** — Used SQL to become familiar with the data and determine which columns would be primarily used. The main objective was to identify opportunities for investment by examining key metrics within the dataset.

**3. Exploratory Data Analysis (EDA)** — After a preliminary examination of the data, began an EDA covering data cleaning and verifying compatibility between dataset frames to ensure consistency.

**4. Data Analysis** — Executed several queries to uncover insights, including:
- The most numerous app genres
- User ratings in combination with price ranges and genres
- The lowest-rated app genres
- Correlations between app description length and average user ratings
- Correlations between average ratings and the number of languages supported
- Genres that are least common among the lowest-rated categories
- The relationship between price range, number of apps, and average user ratings

**5. Visualisations & Recommendations** — Built charts to communicate findings, and derived actionable recommendations for the stakeholder.

---

## 🗂️ Dataset

| Table | Source | Records |
|---|---|---|
| `applestore_dataset` | [Kaggle — App Store Apps](https://www.kaggle.com/datasets/ramamet4/app-store-apple-data-set-10k-apps) | ~7,200 apps |
| `applestoredescription` | Same source (companion table) | ~7,200 descriptions |

**Key fields used:** `id`, `track_name`, `prime_genre`, `user_rating`, `rating_count_tot`, `price`, `lang_num`, `app_desc`

---

## 🛠️ Tools & Environment

- **SQL:** PostgreSQL — tables loaded via `COPY` from CSV, with full support for window functions, CTEs, and recursive queries
- **Python:** Plotly Express — for interactive chart visualisations
- **Notebook:** Jupyter — queries, charts, and narrative in one place
- **Version control:** Git

---

## 🔍 Analysis Structure

### 1. Data Quality Checks
Before any analysis, both tables were validated:
- Unique app ID counts were compared across tables to confirm alignment
- Missing values were checked in critical fields (`track_name`, `user_rating`, `prime_genre`, `app_desc`)
- Cross-table consistency was verified using a `UNION ALL` mismatch check

```sql
SELECT 'applestore_dataset' AS source, track_name
FROM applestore_dataset
WHERE track_name NOT IN (SELECT track_name FROM applestoredescription)
UNION ALL
SELECT 'applestoredescription' AS source, track_name
FROM applestoredescription
WHERE track_name NOT IN (SELECT track_name FROM applestore_dataset);
```

---

### 2. Genre Distribution
Counted apps per genre to map market saturation and identify crowded vs underrepresented categories.

**Key finding:** Games dominate the store with 3,862 apps — over 53% of the entire dataset — suggesting high competition in that category.

---

### 3. Ratings Landscape
Calculated min, max, and average ratings across the full dataset, then broke ratings down by genre using window functions.

**Key finding:** The overall average user rating sits around 3.5/5. Several categories (Catalogs, Finance, Book) consistently underperform.

---

### 4. Standout Apps in Low-Rated Genres
Used a two-step CTE to find, within each of the 10 lowest-rated genres, the single highest-rated app with more than 5,000 ratings — to identify outliers that succeed where their category fails.

```sql
WITH low_rated_genres AS (
    SELECT prime_genre,
           ROUND(AVG(user_rating)::numeric, 2) AS avg_rating
    FROM applestore_dataset
    GROUP BY prime_genre
    ORDER BY avg_rating ASC
    LIMIT 10
),
ranked_tracks AS (
    SELECT a.prime_genre, a.track_name, a.user_rating, a.rating_count_tot,
           RANK() OVER (PARTITION BY a.prime_genre ORDER BY a.user_rating DESC, a.rating_count_tot DESC) AS rank
    FROM applestore_dataset AS a
    JOIN low_rated_genres AS lrg ON a.prime_genre = lrg.prime_genre
    WHERE a.rating_count_tot > 5000
)
SELECT prime_genre, track_name, user_rating
FROM ranked_tracks
WHERE rank = 1
ORDER BY user_rating DESC;
```

---

### 5. Description Length vs Ratings
Bucketed app descriptions into Short (<500 chars), Medium (500–1000), and Long (1000+), then compared average ratings per bucket.

**Key finding:** Apps with longer, more detailed descriptions consistently achieve higher average ratings.

---

### 6. Language Support vs Ratings
Bucketed apps by number of supported languages (<10, 10–30, >30).

**Key finding:** Supporting multiple languages increases the app's reach and appeal in global markets, with the best results seen in the 10–30 language range.

---

### 7. Paid vs Free — Ratings Comparison
Compared average user ratings and app counts between free and paid apps.

**Key finding:** Paid apps average slightly higher ratings than free apps. It is worth noting that many free apps may operate under a Freemium model, which this dataset does not distinguish.

---

### 8. Price Range Distribution
Dynamically bucketed apps into price ranges using `FLOOR`-based logic.

**Key finding:** Most paid apps are priced between $1 and $3.

---

## 📊 Visualisations

Charts built with Plotly Express directly from SQL query outputs:
- Stacked bar chart — genres and user rating distribution
- Bar chart — 10 lowest-rated genres
- Bar chart — paid vs free comparison
- Bubble chart — average genre ratings vs low-rated genres (over 5,000 entries)

---

## 💡 Recommendations

**Target Underserved Categories** — Consider developing an app in underrepresented, low-rated categories such as Catalogs, Finance, and Navigation. These present opportunities due to smaller competition and room for a well-designed app to stand out.

**Books Category Investigation** — Further investigation is needed to determine whether low ratings in Books are due to content quality or e-reader functionality before committing to this space.

**Pricing Model** — Launch a paid app priced between USD 1.00 and USD 4.00, or adopt a Freemium model offering basic features for free while monetising through premium options.

**Language Support** — Supporting multiple languages increases the app's reach and appeal in global markets.

**App Description** — Invest in a long, detailed description. The data shows a clear positive correlation between description length and user ratings.

---

## 📁 Repository Structure

```
├── README.md
├── AppleStore_Analysis.ipynb
├── applestore_queries.txt
└── data/
    └── (source files — see Kaggle link above)
```

---

## 👤 Author

**Edy dos Santos** — Data Analyst | Upskilling in Data Engineering
[GitHub Portfolio](https://github.com/edy-dos-santos/myportfolio)
