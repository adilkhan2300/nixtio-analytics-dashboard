# 📊 Autonomous Data Analytics Engine

A powerful, generic data analytics and cleaning dashboard built entirely in Python using **Streamlit** and **Plotly**. This application is designed to take *any* raw Excel or CSV file and automatically process it, generating advanced statistical modeling, exploratory charts, and data health diagnostics.

## ✨ Features

* **🧹 Autonomous Data Cleaning:** One-click engine to drop duplicates, impute missing numeric values with medians, label missing categorical values, and clean text strings.
* **📈 Dynamic Profiling:** Automatically detects numeric, categorical, and timeline columns, generating top-level metrics on the fly.
* **📦 Outlier Detection:** Interactive Histograms and Box & Whisker plots to identify data skew and outliers.
* **🔄 Correlation Engine:** Multi-variable correlation matrices and dynamic scatter plots to find hidden relationships.
* **📅 Time Intelligence:** If time-series data is detected, it automatically plots monthly trends and Day-of-Week seasonality.
* **🎯 Advanced Cross-Analysis:** Pareto (80/20 Rule) charts and multi-dimensional Cross-Tabulation heatmaps.

---

## 🚀 How to Run Locally

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/adilkhan2300/nixtio-analytics-dashboard.git
cd nixtio-analytics-dashboard
```

### 3. Install Dependencies
It is recommended to use a virtual environment. Install the required packages via `pip`:
```bash
pip install -r requirements.txt
```

### 4. (Optional) Generate Sample Data
If you don't have your own dataset to test with, you can generate a realistic, multi-sheet, randomized sales dataset by running the generator script:
```bash
python generate_sample_data.py
```
*This will create a `sales_data.xlsx` file in your directory.*

### 5. Launch the Dashboard
Start the Streamlit application by running:
```bash
streamlit run dashboard_app.py
```
This will automatically open the dashboard in your default web browser at `http://localhost:8501`.

---

## 🖥️ Usage Guide

1. **Upload Data:** Use the sidebar on the left to upload any `.csv` or `.xlsx` file. If none is provided, it will fallback to `sales_data.xlsx`.
2. **Clean Data:** Head to the **Data Cleaning** tab to review data health. Click **✨ Auto-Clean Dataset** to instantly fix NaNs and duplicates.
3. **Explore Tabs:** Navigate through the top tabs (Overview, Distributions, Correlations, Time Intel, Deep Dive) to interact with your newly cleaned data. Dropdowns within the tabs will dynamically update based on the columns available in your specific dataset.
4. **Export:** Go to the **Raw Data** tab to download your fully cleaned and processed CSV file.
