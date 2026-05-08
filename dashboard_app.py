"""
dashboard_app.py  –  Comprehensive Generic Analytics Dashboard
============================================================
Run:  streamlit run dashboard_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS (Dark Theme) ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }
body, .main, .stApp { 
    background-color: #0B0F19 !important;
    color: #F9FAFB !important;
}

[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937;
}
[data-testid="stSidebar"] * { color: #F9FAFB !important; }
h1, h2, h3, h4, h5, h6, .markdown-text-container { color: #F9FAFB !important; }

.metric-card {
    background: rgba(31, 41, 55, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 10px 40px -10px rgba(0,0,0,0.3);
    transition: transform 0.2s ease;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 15px 50px -10px rgba(0,0,0,0.5); }
.metric-label { color: #9CA3AF; font-size: 14px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.metric-value { color: #F9FAFB; font-size: 32px; font-weight: 800; letter-spacing: -1px; }

.step-banner {
    background: #111827;
    border-left: 6px solid #F8D870;
    border-radius: 16px;
    padding: 18px 24px;
    margin: 32px 0 16px 0;
    color: #F9FAFB;
    font-weight: 700;
    font-size: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.explanation-box {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 24px;
    color: #9CA3AF;
    font-size: 14px;
    line-height: 1.6;
}
.explanation-box b { color: #F9FAFB; font-size: 15px; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: #111827; border-radius: 100px; padding: 8px 20px;
    color: #9CA3AF; font-weight: 600; border: 1px solid #1F2937;
}
.stTabs [aria-selected="true"] { background: #F8D870 !important; color: #111827 !important; border: 1px solid #F8D870 !important; }

[data-testid="stDataFrame"] { background: #111827; border-radius: 16px; padding: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
hr { border-top: 1px solid #1F2937; }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ──────────────────────────────────────────────────────────
C_AMBER = "#F8D870"
C_BLACK = "#1A1A1A"
C_WHITE = "#FFFFFF"
C_GRAY_LIGHT = "#1F2937"
C_GRAY_DARK = "#9CA3AF"
C_GREEN = "#34D399"

CHART_COLORS = [C_AMBER, C_WHITE, "#9CA3AF", "#4B5563", "#374151", "#10B981", "#6366F1", "#F43F5E"]

def style_plotly(fig):
    fig.update_layout(
        template="plotly_dark", 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#F9FAFB"),
        xaxis=dict(showgrid=False, linecolor="#374151"), 
        yaxis=dict(gridcolor="#1F2937", linecolor="#374151"),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# STEP 0 – Load Generic Data
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data(path):
    try:
        xl = pd.ExcelFile(path)
        df = xl.parse(xl.sheet_names[0])
    except Exception:
        df = pd.read_csv(path) if str(path).endswith(".csv") else pd.read_excel(path)
    
    for col in df.columns:
        if df[col].dtype == 'object':
            if df[col].astype(str).str.contains(r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', regex=True).any():
                try: df[col] = pd.to_datetime(df[col], errors='ignore')
                except: pass
    return df

st.title("📊 Data Analytics Dashboard")
st.markdown("#### Comprehensive exploratory data analysis for any dataset")
st.markdown("---")

uploaded = st.sidebar.file_uploader("📂 Upload any Excel or CSV file", type=["xlsx", "xls", "csv"])
default_path = "sales_data.xlsx"

try:
    if uploaded:
        import tempfile
        ext = ".csv" if uploaded.name.endswith(".csv") else ".xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        df = load_data(tmp_path)
    else:
        df = load_data(default_path)
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Classify columns
all_cols = df.columns.tolist()
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

if not numeric_cols:
    st.warning("⚠️ No numeric columns found. Advanced analytics require at least one numeric value.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# METRICS OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="metric-card"><div class="metric-label">Total Rows</div><div class="metric-value">{len(df):,}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card"><div class="metric-label">Total Columns</div><div class="metric-value">{len(df.columns)}</div></div>', unsafe_allow_html=True)
if len(numeric_cols) >= 1:
    c3.markdown(f'<div class="metric-card"><div class="metric-label">Sum of {numeric_cols[0]}</div><div class="metric-value">{df[numeric_cols[0]].sum():,.1f}</div></div>', unsafe_allow_html=True)
if len(numeric_cols) >= 2:
    c4.markdown(f'<div class="metric-card"><div class="metric-label">Avg of {numeric_cols[1]}</div><div class="metric-value">{df[numeric_cols[1]].mean():,.1f}</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS ENGINE
# ═══════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📈 Overview", 
    "📦 Distributions", 
    "🔄 Correlations", 
    "📅 Time Intel", 
    "🎯 Deep Dive", 
    "📋 Raw Data"
])

# ── 1. OVERVIEW ─────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="step-banner">Dataset Profiling & Composition</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 📝 Statistical Summary (Numeric)")
        st.dataframe(df[numeric_cols].describe().T.style.format("{:.2f}"), use_container_width=True)
    
    with col_b:
        if categorical_cols:
            cat_ov = st.selectbox("Select Category to View Distribution", categorical_cols, key="ov_cat")
            counts = df[cat_ov].value_counts().reset_index().head(10)
            counts.columns = [cat_ov, 'Count']
            fig_pie = px.pie(counts, names=cat_ov, values='Count', hole=0.6, 
                             color_discrete_sequence=CHART_COLORS, title=f"Top 10 {cat_ov} Share")
            fig_pie = style_plotly(fig_pie)
            st.plotly_chart(fig_pie, use_container_width=True)

# ── 2. DISTRIBUTIONS ────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="step-banner">Data Shape & Outliers</div>', unsafe_allow_html=True)
    
    if numeric_cols:
        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown("##### 📊 Value Distribution (Histogram)")
            hist_col = st.selectbox("Select Numeric Column", numeric_cols, key="hist_col")
            fig_hist = px.histogram(df, x=hist_col, nbins=30, marginal="box", 
                                    color_discrete_sequence=[C_AMBER],
                                    title=f"Distribution of {hist_col}")
            fig_hist = style_plotly(fig_hist)
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col_y:
            st.markdown("##### 📦 Outlier Detection (Box Plot)")
            box_num = st.selectbox("Numeric Value", numeric_cols, index=min(1, len(numeric_cols)-1), key="box_num")
            box_cat = st.selectbox("Split by Category (Optional)", ["None"] + categorical_cols, key="box_cat")
            
            c_val = None if box_cat == "None" else box_cat
            fig_box = px.box(df, x=c_val, y=box_num, color=c_val, 
                             color_discrete_sequence=CHART_COLORS,
                             title=f"Box Plot of {box_num}" + (f" by {box_cat}" if c_val else ""))
            fig_box = style_plotly(fig_box)
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

# ── 3. CORRELATIONS ─────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="step-banner">Relationships & Drivers</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 1.5])
    with col_a:
        st.markdown("##### 🔄 Correlation Matrix")
        st.markdown("<small style='color:#9CA3AF;'>Shows linear relationship between all numeric fields (-1 to 1)</small>", unsafe_allow_html=True)
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", 
                                 color_continuous_scale=[C_GRAY_LIGHT, C_AMBER, C_WHITE], zmin=-1, zmax=1)
            fig_corr = style_plotly(fig_corr)
            fig_corr.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Need at least 2 numeric columns for a correlation matrix.")
            
    with col_b:
        st.markdown("##### 🎯 Multi-variable Scatter Matrix")
        if len(numeric_cols) > 1:
            scat_x = st.selectbox("X-Axis", numeric_cols, index=0, key="scat_x")
            scat_y = st.selectbox("Y-Axis", numeric_cols, index=1, key="scat_y")
            scat_c = st.selectbox("Color By", ["None"] + categorical_cols, key="scat_c")
            scat_s = st.selectbox("Size By (Optional)", ["None"] + numeric_cols, key="scat_s")
            
            c_val = None if scat_c == "None" else scat_c
            s_val = None if scat_s == "None" else scat_s
            
            fig_scat = px.scatter(df, x=scat_x, y=scat_y, color=c_val, size=s_val,
                                  color_discrete_sequence=CHART_COLORS, opacity=0.7)
            fig_scat = style_plotly(fig_scat)
            st.plotly_chart(fig_scat, use_container_width=True)

# ── 4. TIME INTELLIGENCE ────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="step-banner">Time Series & Seasonality</div>', unsafe_allow_html=True)
    
    if date_cols:
        time_col = st.selectbox("Timeline Column", date_cols, key="ti_date")
        val_col = st.selectbox("Metric to Track", numeric_cols, key="ti_val")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            # Monthly Trend
            trend_df = df.copy()
            trend_df[time_col] = trend_df[time_col].dt.to_period("M").astype(str)
            trend_agg = trend_df.groupby(time_col)[val_col].sum().reset_index()
            
            fig_line = px.line(trend_agg, x=time_col, y=val_col, markers=True, title=f"Monthly Trend ({val_col})")
            fig_line.update_traces(line=dict(color=C_WHITE, width=3), marker=dict(color=C_AMBER, size=8))
            fig_line = style_plotly(fig_line)
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_t2:
            # Day of Week Seasonality
            dow_df = df.copy()
            dow_df['DayOfWeek'] = dow_df[time_col].dt.day_name()
            # Order days logically
            cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_df['DayOfWeek'] = pd.Categorical(dow_df['DayOfWeek'], categories=cats, ordered=True)
            dow_agg = dow_df.groupby('DayOfWeek')[val_col].mean().reset_index()
            
            fig_dow = px.bar(dow_agg, x='DayOfWeek', y=val_col, title=f"Avg {val_col} by Day of Week",
                             color_discrete_sequence=[C_AMBER])
            fig_dow = style_plotly(fig_dow)
            st.plotly_chart(fig_dow, use_container_width=True)
    else:
        st.info("⚠️ No Date/Time columns detected in the dataset. Time intelligence is disabled.")

# ── 5. DEEP DIVE (Pareto & Crosstab) ────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="step-banner">Advanced Segment Cross-Analysis</div>', unsafe_allow_html=True)
    
    if len(categorical_cols) >= 2 and numeric_cols:
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.markdown("##### ⚡ Pareto Analysis (80/20 Rule)")
            st.markdown("<small style='color:#9CA3AF;'>Identifies the vital few categories driving the most value.</small>", unsafe_allow_html=True)
            par_cat = st.selectbox("Category", categorical_cols, key="par_cat")
            par_num = st.selectbox("Metric", numeric_cols, key="par_num")
            
            pareto = df.groupby(par_cat)[par_num].sum().sort_values(ascending=False).reset_index()
            pareto['Cumulative %'] = (pareto[par_num].cumsum() / pareto[par_num].sum()) * 100
            
            # Subplot with secondary Y axis
            fig_par = make_subplots(specs=[[{"secondary_y": True}]])
            fig_par.add_trace(go.Bar(x=pareto[par_cat], y=pareto[par_num], name="Value", marker_color=C_GRAY_LIGHT), secondary_y=False)
            fig_par.add_trace(go.Scatter(x=pareto[par_cat], y=pareto['Cumulative %'], name="Cumulative %", 
                                         line=dict(color=C_AMBER, width=3), mode='lines+markers'), secondary_y=True)
            
            fig_par = style_plotly(fig_par)
            fig_par.update_layout(title=f"Pareto Chart: {par_cat} by {par_num}", showlegend=False)
            fig_par.update_yaxes(title_text="Value", secondary_y=False)
            fig_par.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
            st.plotly_chart(fig_par, use_container_width=True)
            
        with col_p2:
            st.markdown("##### 🔀 Pivot / Cross-Tabulation Heatmap")
            st.markdown("<small style='color:#9CA3AF;'>Maps performance across two different category intersections.</small>", unsafe_allow_html=True)
            ct_row = st.selectbox("Row Category", categorical_cols, index=0, key="ct_r")
            ct_col = st.selectbox("Column Category", categorical_cols, index=1 if len(categorical_cols)>1 else 0, key="ct_c")
            ct_val = st.selectbox("Metric to Aggregate", numeric_cols, key="ct_v")
            
            if ct_row != ct_col:
                pivot = df.pivot_table(values=ct_val, index=ct_row, columns=ct_col, aggfunc="sum").fillna(0)
                fig_ct = px.imshow(pivot, text_auto=".2s", aspect="auto", 
                                   color_continuous_scale=[C_GRAY_LIGHT, C_AMBER, C_WHITE],
                                   title=f"{ct_val} by {ct_row} & {ct_col}")
                fig_ct = style_plotly(fig_ct)
                st.plotly_chart(fig_ct, use_container_width=True)
            else:
                st.warning("Please select different categories for Row and Column.")
    else:
        st.info("Need at least 2 categorical columns and 1 numeric column for Advanced Cross-Analysis.")

# ── 6. RAW DATA ─────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("##### 🔎 Filtered Records")
    st.dataframe(df, use_container_width=True, height=450)
    st.download_button("⬇️ Export to CSV", df.to_csv(index=False).encode("utf-8"), "dataset_export.csv", "text/csv")

st.markdown("---")
st.markdown("<p style='text-align:center;color:#9CA3AF;font-size:13px;'>Data Analytics Dashboard • Built with Streamlit</p>", unsafe_allow_html=True)
