# 📊 Autonomous Data Analytics Engine

A powerful, generic data analytics and cleaning dashboard built entirely in Python using **Streamlit**, **Plotly**, **Scikit-learn**, and **SciPy**. This application is designed to take *any* raw Excel or CSV files and automatically process them, generating advanced statistical modeling, exploratory charts, and automated business intelligence.

## ✨ Core Features

* **🧹 Autonomous Data Cleaning:** One-click engine to drop duplicates, impute missing numeric values with medians, label missing categorical values, and clean text strings.
* **🔀 Multi-Dataset Merging:** Upload multiple datasets simultaneously and stack (append) or join them automatically on common columns for complex analysis.
* **📈 Dynamic Profiling:** Automatically detects numeric, categorical, and timeline columns, generating top-level metrics and distributions on the fly.
* **🤖 Predictive Modeling:** Train Linear Regression or Random Forest models directly in the UI to predict metrics and analyze feature importance.
* **🧪 A/B Testing:** Run statistically significant T-tests to compare performance across different data segments.
* **💡 Deep Business Insights:** Auto-generates a detailed Executive Summary analyzing Performance Trends, Volatility/Risk Factors, Market Segmentation, and Key Drivers, ending with a dynamic Executive Action Plan.
* **⚙️ Automation & Governance:** Instantly generate summary text reports, export reusable Python analysis scripts, and view overall Data Health scores.
* **📂 Large File Support:** Streamlit configuration included to allow ingestion of massive files up to **1 GB**.

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

1. **Upload Data:** Use the sidebar on the left to upload one or multiple `.csv` or `.xlsx` files. You can choose to join or stack multiple datasets.
2. **Clean Data:** Head to the **Data Cleaning** tab to review data health. Click **✨ Auto-Clean Dataset** to instantly fix NaNs and duplicates.
3. **Explore Tabs:** Navigate through the 11 specialized tabs (Overview, Distributions, Correlations, Time Intel, Deep Dive, Predictive Models, A/B Testing, Business Insights, Automation, Governance, and Raw Data).
4. **Actionable Insights:** Visit the **Business Insights** tab for a fully written plain-English analysis of your uploaded datasets.
5. **Export:** Export cleaned data, generated Python scripts, and automated summary reports directly from the interface.
