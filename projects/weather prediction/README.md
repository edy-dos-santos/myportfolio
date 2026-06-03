# Australian Weather Prediction — Will It Rain Tomorrow?

A classification project using 10 years of Bureau of Meteorology (BOM) data from 49 locations across Australia. Three modelling approaches — Decision Tree, Logistic Regression, and Neural Network (MLP) — are trained, tuned, and compared to predict whether it will rain the following day.

## Dataset

| Detail | Value |
|--------|-------|
| Source | Bureau of Meteorology (BOM) |
| Records | 145,490 |
| Features | 27 (numeric + categorical) |
| Locations | 49 Australian weather stations |
| Period | 2007–2017 |
| Target | `RainTomorrow` (binary: 1 = rain, 0 = no rain) |

Key variables include temperature readings (min, max, 9 am, 3 pm), humidity, atmospheric pressure, wind gust speed and direction, rainfall, evaporation, sunshine hours, cloud cover (oktas), and ENSO status.

## Project Workflow

### Phase 1 — Data Understanding & Type Validation

Loaded the dataset and inspected its structure. Several data-type mismatches flagged by pandas were corrected against the BOM variable descriptions, including date parsing and categorical encoding for wind direction and rain indicator columns.

### Phase 2 — Statistical Exploration

Computed summary statistics and skewness for all numeric variables. Rainfall (skewness ≈ 9.84) and Evaporation (≈ 3.76) showed heavy right skew — expected for precipitation data, where most days record little or no rain and a few record heavy falls. Variables such as Sunshine, Humidity, Pressure, and Temperature had skewness close to zero, indicating roughly symmetric distributions. WindGustSpeed was moderately skewed (≈ 0.87).

Domain-specific analytical questions were answered, including identifying the longest sunshine day, average maximum temperature under specific wind conditions at Uluru, top-5 rainfall locations in 2017, and wind direction frequency on rainy days.

### Phase 3 — Visual Exploration

Distribution plots, correlation heatmaps, and scatterplots were produced. The Humidity3pm–Pressure3pm relationship was examined for multicollinearity, and highly correlated variable pairs were flagged with treatment recommendations for downstream modelling.

### Phase 4 — Data Preparation

Cleaning steps included handling missing values (imputation or removal depending on variable), correcting out-of-range values (e.g., Cloud3pm values of 9 capped to the valid maximum of 8), outlier treatment, and one-hot encoding of categorical variables via `pd.get_dummies()`. The cleaned dataset was then split into training and test sets for modelling.

### Phase 5 — Predictive Modelling

Three model families were trained and progressively refined:

#### 1. Decision Tree Classifier

| Metric | Default Tree | GridSearchCV-Tuned Tree |
|--------|-------------|------------------------|
| Training Accuracy | 100.00% | 85.08% |
| Test Accuracy | 79.30% | 84.50% |
| AUC | 0.706 | 0.853 |
| Nodes | 8,245 | 63 |
| Rules | 4,122 | 32 |

The default tree massively overfit — near-perfect training accuracy but a 20-percentage-point gap to test accuracy. The first split variable was **Humidity3pm** in both models. The top-5 important features were Humidity3pm, Sunshine, Pressure3pm, WindGustSpeed, and Pressure9am.

Tuning via GridSearchCV constrained `max_depth`, `min_samples_split`, and `min_samples_leaf`, producing a much smaller tree with better generalisation and a significantly higher AUC.

#### 2. Logistic Regression

| Metric | Default Model | With Dimensionality Reduction |
|--------|--------------|-------------------------------|
| Training Accuracy | 85.98% | 85.99% |
| Test Accuracy | 85.33% | 85.34% |
| AUC | 0.883 | 0.883 |

Values were standardised (zero mean, unit variance) to handle the diverse scales across features. The top-5 important variables by coefficient magnitude were Pressure3pm (−1.34), Humidity3pm (+1.20), Pressure9am (+0.94), WindGustSpeed (+0.80), and Sunshine (−0.56).

The negative Pressure3pm coefficient aligns with meteorological expectations — lower pressure precedes rain. The positive Humidity3pm coefficient similarly confirms that higher afternoon humidity is a strong rain predictor.

Recursive Feature Elimination reduced features from 114 to 85 with negligible accuracy impact, confirming that many one-hot-encoded features contributed little. Training and test accuracy remained nearly identical, showing no overfitting.

#### 3. Neural Network (MLP Classifier)

| Metric | Default MLP | GridSearchCV-Tuned | With Decision Tree Features |
|--------|------------|--------------------|-----------------------------|
| Training Accuracy | 94.84% | 87.06% | 85.40% |
| Test Accuracy | 83.47% | 85.79% | 84.35% |
| AUC | — | 0.894 | — |
| Overfitting | Yes | No | No |
| Iterations to converge | 200 | 300 | 21 |

The default MLP showed overfitting (11+ point train-test gap). GridSearchCV tuning (best params: `alpha=0.001`, `hidden_layer_sizes=(5,)`) eliminated overfitting and improved test accuracy to 85.79%. When features were pre-selected using the decision tree's importance ranking, convergence was dramatically faster (21 vs 300 iterations) with no overfitting.

### Final Model Comparison

| Model | AUC | Overfitting |
|-------|-----|-------------|
| Decision Tree (tuned) | 0.849 | No |
| Logistic Regression | 0.882 | No |
| Neural Network (tuned) | **0.894** | No |

The tuned Neural Network achieved the highest AUC (0.894) and was selected as the best model for predicting rain tomorrow. However, the Logistic Regression performed very similarly (AUC 0.882) and offers greater interpretability — making it a strong choice where explainability matters.

## Key Takeaways

- **Humidity3pm** was consistently the most important predictor across all three model types — high afternoon humidity is the strongest signal for next-day rain.
- **Hyperparameter tuning matters.** The default decision tree overfit catastrophically (AUC 0.706 → 0.849 after tuning). The neural network similarly improved from overfitting to the best overall AUC after GridSearchCV.
- **Standardisation is essential for scale-sensitive models.** Logistic regression and neural networks both benefited from z-score normalisation.
- **Dimensionality reduction** had minimal impact on logistic regression accuracy, confirming that the core predictive signal sits in a handful of variables.
- **Feature transfer across models** worked well — using the decision tree's feature importances to pre-select inputs for the neural network cut convergence time by 90%.

## Tech Stack

- **Python 3** — pandas, NumPy, scikit-learn, matplotlib
- **scikit-learn** — `DecisionTreeClassifier`, `LogisticRegression`, `MLPClassifier`, `GridSearchCV`, `train_test_split`, `accuracy_score`, `classification_report`, `roc_curve`, `auc`
- **Jupyter Notebook** — exploratory analysis and modelling

## Repository Structure

```
.
├── README.md
├── data/
│   └── D1.csv                 # BOM weather dataset (145,490 records)
├── notebooks/
│   └── weather_prediction.ipynb   # Full analysis notebook
├── docs/
│   └── variable_descriptions.md   # Dataset schema and variable definitions
└── images/
    ├── roc_decision_tree.png
    ├── roc_logistic_regression.png
    ├── roc_neural_network.png
    └── roc_final_comparison.png
```

## How to Run

```bash
# Clone the repo
git clone https://github.com/edy-dos-santos/weather-prediction-australia.git
cd weather-prediction-australia

# Install dependencies
pip install pandas numpy scikit-learn matplotlib jupyter

# Launch the notebook
jupyter notebook notebooks/weather_prediction.ipynb
```

## Acknowledgements

Dataset sourced from the Australian Bureau of Meteorology (BOM). This project was originally completed as part of a university data science course and has been restructured here as a standalone portfolio piece.
