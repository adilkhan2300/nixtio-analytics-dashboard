# 📊 Autonomous Data Analytics Engine

An end-to-end, production-ready Data Analytics and Business Intelligence dashboard engineered in Python. This application acts as a "Data Scientist in a Box", autonomously ingesting messy raw data (CSV/Excel), performing robust data cleaning, conducting advanced statistical modeling, and generating plain-English executive insights.

---

## 🏗️ Architecture & Technology Stack

The application is built entirely in Python, leveraging a modern data science stack:

* **Frontend / UI Framework:** [Streamlit](https://streamlit.io/) — Handles routing, state management, and the interactive web interface.
* **Data Manipulation:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) — Serves as the core engine for in-memory data transformation, aggregation, and vectorized operations.
* **Data Visualization:** [Plotly Express & Graph Objects](https://plotly.com/python/) — Renders interactive, hardware-accelerated D3.js charts.
* **Machine Learning:** [Scikit-Learn](https://scikit-learn.org/) — Powers the predictive modeling capabilities (Linear Regression, Random Forest Regressors, Label Encoding, Train-Test splits).
* **Statistical Analysis:** [SciPy](https://scipy.org/) — Calculates statistical significance (Independent T-Tests) for A/B testing and variance tracking.

---

## ⚙️ Core Technical Modules

### 1. Data Ingestion & Session Management
* **Multi-Dataset Handling:** Uses `st.session_state` to persist a dataset registry, allowing users to upload multiple files (up to 1GB per file via `.streamlit/config.toml`). 
* **Dynamic Merging:** Utilizes `pd.merge` (outer joins) to map common schema columns, or `pd.concat` to vertically stack datasets.
* **Smart Parsing:** Employs regex and type-casting strategies to automatically convert currency strings (e.g., `$1,200`), percentages, and raw dates into native float/datetime datatypes during the initial data load.

### 2. Autonomous Data Cleaning Pipeline
* **Imputation Strategy:** Scans memory schemas (`df.select_dtypes`) to separate numeric and categorical arrays. It imputes missing continuous variables with the median (to avoid outlier skew) and fills missing discrete categoricals with 'Unknown'.
* **Deduplication:** Automatically drops exact row matches to ensure data integrity.

### 3. Statistical & Predictive Engine
* **A/B Significance Testing:** Employs `scipy.stats.ttest_ind` to calculate p-values across categorical variables. It compares means between two selected groups to mathematically prove if performance lifts are statistically significant or due to random variance.
* **Predictive Modeling Engine:** 
  * Automatically isolates continuous target variables (`y`) and feature matrices (`X`).
  * Applies `LabelEncoder` for discrete text columns.
  * Trains `RandomForestRegressor` or `LinearRegression` models on the fly.
  * Outputs R² scores, Mean Absolute Error (MAE), and extracts feature importances to determine the biggest drivers of the target variable.

### 4. Heuristic-Based Business Intelligence
* **Variance & Risk Analysis:** Calculates the Coefficient of Variation (CV) using standard deviation and mean to flag highly volatile metrics.
* **Automated Correlation:** Computes a Pearson correlation matrix (`df.corr()`). It scans the matrix for absolute values `|r| > 0.65` to automatically flag strong positive/negative business drivers.

---

## 📂 Repository Structure

```text
nixtio-analytics-dashboard/
│
├── dashboard_app.py           # Main application file containing the UI and Engine logic
├── generate_sample_data.py    # Faker script to generate localized dummy sales data
├── requirements.txt           # Python dependency manifest
├── README.md                  # Project documentation
│
└── .streamlit/
    └── config.toml            # Server configuration (e.g., maxUploadSize = 1000MB)
```

---

## 🚀 Local Development Setup

### 1. Prerequisites
Ensure you have **Python 3.9+** and `git` installed on your local machine.

### 2. Clone the Repository
```bash
git clone https://github.com/adilkhan2300/nixtio-analytics-dashboard.git
cd nixtio-analytics-dashboard
```

### 3. Setup Virtual Environment
It is highly recommended to isolate dependencies using `venv`:
```bash
python -m venv venv

# Activate on Windows:
.\venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Dashboard Server
Start the local Streamlit development server:
```bash
streamlit run dashboard_app.py
```
*The app will be served locally, typically at `http://localhost:8501`.*

---

## 🛠️ Usage Workflow

1. **Upload Payload:** Ingest standard `CSV` or `XLSX` files via the sidebar.
2. **Execute Cleaning:** Navigate to the Data Cleaning tab to trigger the autonomous imputation engine.
3. **Explore Metrics:** Analyze interactive distributions, correlation matrices, cross-tabulation pivot heatmaps, and time-series seasonality.
4. **Deploy AI Models:** Use the Predictive Models tab to define a target variable and train a Random Forest model.
5. **Extract Insights:** Read the auto-generated Executive Action Plan in the Business Insights tab, or download a reusable `.py` script from the Automation tab to execute your pipeline programmatically.
