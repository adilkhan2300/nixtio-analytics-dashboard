"""
generate_sample_data.py
=======================
Generates a realistic multi-sheet Excel dataset used by dashboard_app.py.
Run this ONCE before launching the Streamlit app:
    python generate_sample_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

REGIONS      = ["North", "South", "East", "West", "Central"]
CATEGORIES   = ["Electronics", "Clothing", "Food & Beverage", "Home & Garden", "Sports"]
PRODUCTS     = {
    "Electronics":      ["Laptop", "Smartphone", "Tablet", "Headphones", "Smart Watch"],
    "Clothing":         ["T-Shirt", "Jeans", "Jacket", "Dress", "Sneakers"],
    "Food & Beverage":  ["Coffee Beans", "Energy Drink", "Protein Bar", "Tea Set", "Juice Pack"],
    "Home & Garden":    ["Plant Pot", "Desk Lamp", "Chair", "Bookshelf", "Curtains"],
    "Sports":           ["Yoga Mat", "Dumbbells", "Running Shoes", "Bicycle", "Swim Goggles"],
}
SALES_REPS   = [f"Rep_{i:02d}" for i in range(1, 21)]
CHANNELS     = ["Online", "In-Store", "Wholesale", "Partner"]
CUSTOMER_SEG = ["Enterprise", "SMB", "Individual", "Government"]


def make_sales_data(n: int = 2000) -> pd.DataFrame:
    start = datetime(2023, 1, 1)
    rows  = []
    for _ in range(n):
        cat     = random.choice(CATEGORIES)
        product = random.choice(PRODUCTS[cat])
        region  = random.choice(REGIONS)
        channel = random.choice(CHANNELS)
        seg     = random.choice(CUSTOMER_SEG)
        rep     = random.choice(SALES_REPS)
        date    = start + timedelta(days=random.randint(0, 729))

        base_price = {
            "Electronics":      random.uniform(100, 1500),
            "Clothing":         random.uniform(20, 200),
            "Food & Beverage":  random.uniform(5, 80),
            "Home & Garden":    random.uniform(15, 400),
            "Sports":           random.uniform(10, 500),
        }[cat]

        quantity     = random.randint(1, 50)
        discount_pct = random.choice([0, 0, 0, 5, 10, 15, 20])
        unit_price   = round(base_price * (1 - discount_pct / 100), 2)
        revenue      = round(unit_price * quantity, 2)
        cost_pct     = random.uniform(0.35, 0.65)
        cost         = round(revenue * cost_pct, 2)
        profit       = round(revenue - cost, 2)
        rating       = round(max(1.0, min(5.0, random.gauss(4.0, 0.7))), 1)

        rows.append({
            "Date":             date.strftime("%Y-%m-%d"),
            "Year":             date.year,
            "Month":            date.month,
            "Month_Name":       date.strftime("%B"),
            "Quarter":          f"Q{(date.month - 1) // 3 + 1}",
            "Region":           region,
            "Category":         cat,
            "Product":          product,
            "Sales_Rep":        rep,
            "Channel":          channel,
            "Customer_Segment": seg,
            "Quantity":         quantity,
            "Unit_Price":       unit_price,
            "Discount_Pct":     discount_pct,
            "Revenue":          revenue,
            "Cost":             cost,
            "Profit":           profit,
            "Profit_Margin":    round(profit / revenue * 100, 2),
            "Customer_Rating":  rating,
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").reset_index(drop=True)


def make_targets_data() -> pd.DataFrame:
    rows = []
    for year in [2023, 2024]:
        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            for region in REGIONS:
                for cat in CATEGORIES:
                    rows.append({
                        "Year":           year,
                        "Quarter":        quarter,
                        "Region":         region,
                        "Category":       cat,
                        "Revenue_Target": round(random.uniform(20_000, 80_000), 2),
                        "Profit_Target":  round(random.uniform(5_000,  25_000), 2),
                    })
    return pd.DataFrame(rows)


def make_customers_data(n: int = 300) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "Customer_ID":   f"CUST_{i:04d}",
            "Segment":       random.choice(CUSTOMER_SEG),
            "Region":        random.choice(REGIONS),
            "Total_Orders":  random.randint(1, 50),
            "Total_Spend":   round(random.uniform(100, 50_000), 2),
            "Avg_Rating":    round(max(1.0, min(5.0, random.gauss(4.0, 0.5))), 1),
            "Tenure_Months": random.randint(1, 36),
            "Churn_Risk":    random.choice(["Low", "Medium", "High"]),
        })
    return pd.DataFrame(rows)


output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_data.xlsx")

print("[*] Generating dataset...")
sales     = make_sales_data(2000)
targets   = make_targets_data()
customers = make_customers_data(300)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    sales.to_excel(writer,     sheet_name="Sales",     index=False)
    targets.to_excel(writer,   sheet_name="Targets",   index=False)
    customers.to_excel(writer, sheet_name="Customers", index=False)

print(f"[OK] Dataset saved -> {output_path}")
print(f"   Sales sheet     : {len(sales):,} rows")
print(f"   Targets sheet   : {len(targets):,} rows")
print(f"   Customers sheet : {len(customers):,} rows")
print("\nNext step -> run:  streamlit run dashboard_app.py")
