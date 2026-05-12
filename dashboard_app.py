"""
dashboard_app.py  –  Autonomous Data Analytics & Cleaning Engine
================================================================
Run:  streamlit run dashboard_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile, warnings, io, datetime
warnings.filterwarnings("ignore")
try:
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error, accuracy_score
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
try:
    from scipy import stats as scipy_stats
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
# DATA LOADING ENGINE  (multi-dataset)
# ═══════════════════════════════════════════════════════════════════════════
st.title("📊 Autonomous Data Analytics Engine")
st.markdown("#### Self-cleaning, intelligent exploratory data analysis")
st.markdown("---")

# ── Helper functions ────────────────────────────────────────────────────────
@st.cache_data
def get_sheet_names(path):
    return pd.ExcelFile(path).sheet_names

@st.cache_data
def load_data(path, sheet_name=None, skiprows=0, is_csv=False):
    if is_csv:
        df = pd.read_csv(path, skiprows=skiprows)
    else:
        xl = pd.ExcelFile(path)
        sheet = sheet_name if sheet_name else xl.sheet_names[0]
        df = xl.parse(sheet, skiprows=skiprows)
    df.dropna(how='all', axis=0, inplace=True)
    df.dropna(how='all', axis=1, inplace=True)
    for col in df.columns:
        if df[col].dtype == 'object':
            if df[col].astype(str).str.match(r'^\$?\s*[\d,]+(\.[\d]+)?$').all():
                try: df[col] = df[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
                except: pass
            elif df[col].astype(str).str.match(r'^-?\d+(\.\d+)?%$').all():
                try: df[col] = df[col].replace({'%': ''}, regex=True).astype(float) / 100
                except: pass
    for col in df.columns:
        if df[col].dtype == 'object':
            if df[col].astype(str).str.contains(r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', regex=True).any():
                try: df[col] = pd.to_datetime(df[col], errors='ignore')
                except: pass
    return df

# ── Sidebar: Multi-file upload ───────────────────────────────────────────────
st.sidebar.markdown("### 📂 1. Upload Datasets")
st.sidebar.markdown("<small style='color:#9CA3AF;'>Upload one or more Excel / CSV files at once.</small>", unsafe_allow_html=True)
uploaded_files = st.sidebar.file_uploader(
    "Upload Excel or CSV files",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    key="multi_upload"
)
default_path = "sales_data.xlsx"

# Build registry: {label -> (tmp_path, is_csv)}
if "dataset_registry" not in st.session_state:
    st.session_state.dataset_registry = {}
if "datasets_loaded" not in st.session_state:
    st.session_state.datasets_loaded = {}   # label -> DataFrame
if "cleaning_logs" not in st.session_state:
    st.session_state.cleaning_logs = []

# Process newly uploaded files
if uploaded_files:
    current_names = {f.name for f in uploaded_files}
    # Remove stale entries
    st.session_state.dataset_registry = {
        k: v for k, v in st.session_state.dataset_registry.items() if k in current_names
    }
    for uf in uploaded_files:
        if uf.name not in st.session_state.dataset_registry:
            is_csv_f = uf.name.lower().endswith(".csv")
            suffix = ".csv" if is_csv_f else ".xlsx"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uf.read())
            tmp.flush()
            st.session_state.dataset_registry[uf.name] = (tmp.name, is_csv_f)

# ── Sidebar: Dataset selector ────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ 2. Configuration")
all_dataset_labels = list(st.session_state.dataset_registry.keys())

# Merge option only when >1 dataset
merge_mode = False
if len(all_dataset_labels) > 1:
    merge_mode = st.sidebar.checkbox("🔀 Merge ALL datasets into one", value=False, key="merge_mode")

if not all_dataset_labels:
    # Fall back to default file
    active_label = "sales_data.xlsx (default)"
    active_path = default_path
    active_is_csv = False
else:
    if merge_mode:
        active_label = "__MERGED__"
    else:
        active_label = st.sidebar.selectbox("🗂️ Select Dataset to Analyse", all_dataset_labels, key="active_ds")

# Per-dataset sheet / skip config
if not merge_mode:
    if all_dataset_labels:
        active_path, active_is_csv = st.session_state.dataset_registry[active_label]
    else:
        active_path, active_is_csv = default_path, False

    selected_sheet = None
    if not active_is_csv:
        try:
            sheets = get_sheet_names(active_path)
            selected_sheet = st.sidebar.selectbox("📄 Select Excel Sheet", sheets, key="sheet_sel")
        except Exception as e:
            st.error(f"Failed to read sheets: {e}")
            st.stop()
    skip_rows = st.sidebar.number_input("Skip Header Rows", min_value=0, value=0, key="skip_rows")

    try:
        raw_df = load_data(active_path, sheet_name=selected_sheet, skiprows=skip_rows, is_csv=active_is_csv)
    except Exception as e:
        st.error(f"Error loading '{active_label}': {e}")
        st.stop()

    config_id = f"{active_label}_{selected_sheet}_{skip_rows}"
    if ("clean_df" not in st.session_state
            or st.session_state.get("config_id") != config_id):
        st.session_state.clean_df = raw_df.copy()
        st.session_state.config_id = config_id
        st.session_state.cleaning_logs = []

else:
    # ── MERGE MODE ──────────────────────────────────────────────────────────
    skip_rows = st.sidebar.number_input("Skip Header Rows (applied to each file)", min_value=0, value=0, key="skip_rows_merge")
    merged_frames = []
    for lbl, (path, is_csv_f) in st.session_state.dataset_registry.items():
        try:
            sheet = None
            if not is_csv_f:
                sheet = get_sheet_names(path)[0]
            fdf = load_data(path, sheet_name=sheet, skiprows=skip_rows, is_csv=is_csv_f)
            fdf["_source_file"] = lbl          # tag rows with source filename
            merged_frames.append(fdf)
        except Exception as e:
            st.warning(f"Skipped '{lbl}': {e}")

    if not merged_frames:
        st.error("Could not load any of the uploaded files.")
        st.stop()

    merge_how = st.sidebar.radio("Merge Strategy", ["Stack (append rows)", "Join on common columns"], key="merge_how")
    if merge_how == "Stack (append rows)":
        raw_df = pd.concat(merged_frames, ignore_index=True)
    else:
        raw_df = merged_frames[0]
        for fdf in merged_frames[1:]:
            common = list(set(raw_df.columns) & set(fdf.columns))
            if common:
                raw_df = pd.merge(raw_df, fdf, on=common, how="outer", suffixes=("", f"_{fdf['_source_file'].iloc[0]}"))
            else:
                raw_df = pd.concat([raw_df, fdf], ignore_index=True)

    config_id = f"merged_{'_'.join(all_dataset_labels)}_{skip_rows}_{merge_how}"
    if ("clean_df" not in st.session_state
            or st.session_state.get("config_id") != config_id):
        st.session_state.clean_df = raw_df.copy()
        st.session_state.config_id = config_id
        st.session_state.cleaning_logs = []

# ── Dataset status banner ────────────────────────────────────────────────────
if len(all_dataset_labels) > 0:
    if merge_mode:
        st.info(f"🔀 **Merged Mode** — {len(all_dataset_labels)} datasets combined | {st.session_state.clean_df.shape[0]:,} rows × {st.session_state.clean_df.shape[1]} cols")
    else:
        cols_status = st.columns(len(all_dataset_labels))
        for i, lbl in enumerate(all_dataset_labels):
            p, ic = st.session_state.dataset_registry[lbl]
            try:
                _tmp = load_data(p, is_csv=ic)
                badge = f"✅ **{lbl}**  `{_tmp.shape[0]:,}r × {_tmp.shape[1]}c`"
            except:
                badge = f"❌ **{lbl}** (error)"
            is_active = "border: 2px solid #F8D870;" if lbl == active_label else ""
            cols_status[i].markdown(
                f"<div class='metric-card' style='padding:12px 16px;{is_active}'>"
                f"<div class='metric-label'>Dataset {i+1}</div>"
                f"<div style='font-size:13px;color:#F9FAFB'>{badge}</div></div>",
                unsafe_allow_html=True
            )

df = st.session_state.clean_df

# Classify columns
all_cols = df.columns.tolist()
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS ENGINE TABS
# ═══════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🏠 Executive Overview",
    "🔍 Data Explorer",
    "🧠 Advanced Analytics",
    "💼 Business Intelligence",
    "⚙️ Data Management"
])

# ── DATA CLEANING (Management) ──────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="step-banner">Autonomous Data Preparation</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#9CA3AF;'>Use the autonomous engine to instantly clean messy data, or manually apply specific operations.</small>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.markdown("##### 🩺 Data Health Check")
        missing_count = df.isna().sum().sum()
        dup_count = df.duplicated().sum()
        
        st.info(f"**Missing Values:** {missing_count:,}")
        st.info(f"**Duplicate Rows:** {dup_count:,}")
        st.info(f"**Shape:** {df.shape[0]:,} rows × {df.shape[1]} cols")
        
        if st.button("✨ Auto-Clean Dataset", type="primary", use_container_width=True):
            clean_temp = df.copy()
            logs = []
            
            # Drop duplicates
            d_count = clean_temp.duplicated().sum()
            if d_count > 0:
                clean_temp.drop_duplicates(inplace=True)
                logs.append(f"✓ Dropped {d_count} duplicate rows.")
                
            # Fill numeric NAs with Median
            num_cols = clean_temp.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                n_count = clean_temp[col].isna().sum()
                if n_count > 0:
                    clean_temp[col].fillna(clean_temp[col].median(), inplace=True)
                    logs.append(f"✓ Filled {n_count} missing values in {col} with median.")
                    
            # Fill categorical NAs with 'Unknown'
            cat_cols = clean_temp.select_dtypes(include=['object', 'category']).columns
            for col in cat_cols:
                c_count = clean_temp[col].isna().sum()
                if c_count > 0:
                    clean_temp[col].fillna('Unknown', inplace=True)
                    logs.append(f"✓ Filled {c_count} missing values in {col} with 'Unknown'.")
                    
            # Strip whitespace
            for col in cat_cols:
                if clean_temp[col].dtype == 'object':
                    clean_temp[col] = clean_temp[col].astype(str).str.strip()
                    
            if not logs:
                logs.append("Dataset is already clean! No actions needed.")
                
            st.session_state.clean_df = clean_temp
            st.session_state.cleaning_logs = logs
            st.rerun()
            
        if st.button("🔄 Reset to Original", use_container_width=True):
            st.session_state.clean_df = raw_df.copy()
            st.session_state.cleaning_logs = ["Reset to original raw dataset."]
            st.rerun()

    with col_c2:
        st.markdown("##### 🛠️ Manual Operations")
        with st.expander("Remove Nulls / NAs"):
            if st.button("Drop Rows with ANY missing values"):
                st.session_state.clean_df.dropna(inplace=True)
                st.session_state.cleaning_logs.append("✓ Dropped all rows containing missing values.")
                st.rerun()
                
        with st.expander("Drop Columns"):
            cols_to_drop = st.multiselect("Select columns to drop", df.columns.tolist())
            if st.button("Drop Selected Columns") and cols_to_drop:
                st.session_state.clean_df.drop(columns=cols_to_drop, inplace=True)
                st.session_state.cleaning_logs.append(f"✓ Dropped columns: {', '.join(cols_to_drop)}")
                st.rerun()

        if st.session_state.cleaning_logs:
            st.markdown("##### 📜 Action Logs")
            for log in st.session_state.cleaning_logs:
                st.markdown(f"<span style='color:{C_GREEN};'>{log}</span>", unsafe_allow_html=True)


if not numeric_cols:
    st.warning("⚠️ No numeric columns remaining. Advanced analytics require at least one numeric value. Try adjusting 'Skip Rows' if headers are lower.")
    st.stop()

# ── OVERVIEW (Executive) ────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="step-banner">Dataset Profiling & Composition</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", f"{len(df):,}")
    c2.metric("Total Columns", f"{len(df.columns)}")
    if len(numeric_cols) >= 1:
        c3.metric(f"Sum of {numeric_cols[0]}", f"{df[numeric_cols[0]].sum():,.1f}")
    if len(numeric_cols) >= 2:
        c4.metric(f"Avg of {numeric_cols[1]}", f"{df[numeric_cols[1]].mean():,.1f}")

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
            
            # 🤖 AI Analyst Explanation
            top_cat_name = counts.iloc[0][cat_ov]
            top_cat_pct = (counts.iloc[0]['Count'] / counts['Count'].sum()) * 100
            st.info(f"**🤖 AI Analyst:** `{top_cat_name}` is the dominant category here, representing **{top_cat_pct:.1f}%** of the top 10 segments shown. Strategies should heavily prioritize this segment.")

# ── DISTRIBUTIONS (Explorer) ──────────────────────────────────────────────────
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
            
            # 🤖 AI Analyst Explanation
            s = df[hist_col].dropna()
            skew = s.skew()
            if skew > 1: skew_str = "right-skewed (contains unusually high spikes/anomalies)"
            elif skew < -1: skew_str = "left-skewed (contains unusually low drops/anomalies)"
            else: skew_str = "relatively balanced"
            st.info(f"**🤖 AI Analyst:** The distribution for `{hist_col}` is **{skew_str}**. Most values cluster around {s.median():,.1f}, with extremes ranging from {s.min():,.1f} to {s.max():,.1f}.")
            
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

# ── CORRELATIONS (Explorer) ───────────────────────────────────────────────────
with tabs[1]:
    st.markdown("---")
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

# ── TIME INTELLIGENCE (Explorer) ──────────────────────────────────────────────
with tabs[1]:
    st.markdown("---")
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
            
            # 🤖 AI Analyst Explanation
            if len(trend_agg) >= 2:
                first_val = trend_agg[val_col].iloc[0]
                last_val = trend_agg[val_col].iloc[-1]
                if last_val > first_val * 1.05: trend_dir = "an upward trend 📈"
                elif last_val < first_val * 0.95: trend_dir = "a downward trend 📉"
                else: trend_dir = "a flat/stable trend ➡️"
                st.info(f"**🤖 AI Analyst:** Over this timeline, `{val_col}` is showing **{trend_dir}**. It moved from {first_val:,.1f} to {last_val:,.1f}.")
            
        with col_t2:
            # Day of Week Seasonality
            dow_df = df.copy()
            dow_df['DayOfWeek'] = dow_df[time_col].dt.day_name()
            cats = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_df['DayOfWeek'] = pd.Categorical(dow_df['DayOfWeek'], categories=cats, ordered=True)
            dow_agg = dow_df.groupby('DayOfWeek')[val_col].mean().reset_index()
            
            fig_dow = px.bar(dow_agg, x='DayOfWeek', y=val_col, title=f"Avg {val_col} by Day of Week",
                             color_discrete_sequence=[C_AMBER])
            fig_dow = style_plotly(fig_dow)
            st.plotly_chart(fig_dow, use_container_width=True)
    else:
        st.info("⚠️ No Date/Time columns detected in the dataset. Time intelligence is disabled.")

# ── DEEP DIVE (Explorer) ────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("---")
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

# ── PREDICTIVE MODELS (Advanced Analytics) ──────────────────────────────────
with tabs[2]:
    st.markdown('<div class="step-banner">🤖 Predictive Modelling Engine</div>', unsafe_allow_html=True)
    if not SKLEARN_OK:
        st.error("Install scikit-learn: `pip install scikit-learn`")
    elif len(numeric_cols) < 2:
        st.info("Need at least 2 numeric columns to build a model.")
    else:
        pm_c1, pm_c2 = st.columns([1, 2])
        with pm_c1:
            task_type = st.radio("Task Type", ["Regression (Predict Value)", "Classification / Churn (Predict Category)"], key="pm_task")
            if "Regression" in task_type:
                target = st.selectbox("🎯 Target (What to predict)", numeric_cols, key="pm_target")
                algo_opts = ["Linear Regression", "Random Forest Regressor"]
            else:
                target = st.selectbox("🎯 Target (What to predict)", categorical_cols, key="pm_target_cls")
                algo_opts = ["Logistic Regression", "Random Forest Classifier"]
                
            features = st.multiselect("📥 Feature Columns", numeric_cols, default=numeric_cols[:min(3, len(numeric_cols))], key="pm_feats")
            model_type = st.selectbox("Model", algo_opts, key="pm_model")
            test_pct = st.slider("Test Split %", 10, 40, 20, key="pm_split")
            run_model = st.button("▶ Train Model", type="primary", use_container_width=True)
            
        with pm_c2:
            if run_model and features and target:
                sub = df[features + [target]].dropna()
                X = sub[features].values
                y = sub[target].values
                
                if "Regression" in task_type:
                    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=test_pct/100, random_state=42)
                    mdl = LinearRegression() if "Linear" in model_type else RandomForestRegressor(n_estimators=100, random_state=42)
                    mdl.fit(X_tr, y_tr)
                    preds = mdl.predict(X_te)
                    
                    r2 = r2_score(y_te, preds)
                    mae = mean_absolute_error(y_te, preds)
                    mc1, mc2 = st.columns(2)
                    mc1.metric("R² Score", f"{r2:.3f}")
                    mc2.metric("Mean Abs Error", f"{mae:,.2f}")
                    
                    fig_pred = px.scatter(x=y_te, y=preds, labels={"x": "Actual", "y": "Predicted"}, title="Actual vs Predicted", color_discrete_sequence=[C_AMBER])
                    fig_pred.add_shape(type="line", x0=y_te.min(), y0=y_te.min(), x1=y_te.max(), y1=y_te.max(), line=dict(color=C_GREEN, dash="dash"))
                    st.plotly_chart(style_plotly(fig_pred), use_container_width=True)
                else:
                    # Classification
                    le = LabelEncoder()
                    y_enc = le.fit_transform(y)
                    X_tr, X_te, y_tr, y_te = train_test_split(X, y_enc, test_size=test_pct/100, random_state=42)
                    mdl = LogisticRegression(max_iter=1000) if "Logistic" in model_type else RandomForestClassifier(n_estimators=100, random_state=42)
                    mdl.fit(X_tr, y_tr)
                    preds = mdl.predict(X_te)
                    
                    acc = accuracy_score(y_te, preds)
                    mc1, mc2 = st.columns(2)
                    mc1.metric("Accuracy", f"{acc*100:.1f}%")
                    mc2.metric("Classes Predicted", f"{len(le.classes_)}")
                    
                    st.info(f"**🤖 AI Analyst:** The model can predict `{target}` with **{acc*100:.1f}% accuracy** using the selected features. This is highly useful for churn prediction or customer classification.")
                if model_type == "Random Forest" and features:
                    fi = pd.DataFrame({"Feature": features, "Importance": mdl.feature_importances_}).sort_values("Importance", ascending=True)
                    fig_fi = px.bar(fi, x="Importance", y="Feature", orientation="h", title="Feature Importance", color_discrete_sequence=[C_AMBER])
                    st.plotly_chart(style_plotly(fig_fi), use_container_width=True)

# ── A/B TESTING (Advanced Analytics) ────────────────────────────────────────
with tabs[2]:
    st.markdown("---")
    st.markdown('<div class="step-banner">🧪 Experimentation & A/B Testing</div>', unsafe_allow_html=True)
    if not SCIPY_OK:
        st.error("Install scipy: `pip install scipy`")
    elif not categorical_cols or not numeric_cols:
        st.info("Need at least 1 categorical and 1 numeric column for A/B testing.")
    else:
        ab_c1, ab_c2 = st.columns([1, 2])
        with ab_c1:
            grp_col = st.selectbox("Group Column (A/B)", categorical_cols, key="ab_grp")
            metric_col = st.selectbox("Metric to Compare", numeric_cols, key="ab_metric")
            groups = df[grp_col].dropna().unique().tolist()
            grp_a = st.selectbox("Group A", groups, index=0, key="ab_ga")
            grp_b = st.selectbox("Group B", groups, index=min(1, len(groups)-1), key="ab_gb")
            conf = st.slider("Confidence Level", 0.90, 0.99, 0.95, step=0.01, key="ab_conf")
            run_ab = st.button("▶ Run Test", type="primary", use_container_width=True)
        with ab_c2:
            if run_ab and grp_a != grp_b:
                a_data = df[df[grp_col] == grp_a][metric_col].dropna()
                b_data = df[df[grp_col] == grp_b][metric_col].dropna()
                t_stat, p_val = scipy_stats.ttest_ind(a_data, b_data)
                sig = p_val < (1 - conf)
                lift = ((b_data.mean() - a_data.mean()) / a_data.mean() * 100) if a_data.mean() != 0 else 0
                r1, r2, r3 = st.columns(3)
                r1.metric("p-value", f"{p_val:.4f}")
                r2.metric("Lift (B vs A)", f"{lift:+.1f}%")
                r3.metric("Result", "✅ Significant" if sig else "❌ Not Significant")
                ab_plot = pd.DataFrame({"Value": list(a_data) + list(b_data), "Group": [grp_a]*len(a_data) + [grp_b]*len(b_data)})
                fig_ab = px.histogram(ab_plot, x="Value", color="Group", barmode="overlay", opacity=0.7, color_discrete_sequence=[C_AMBER, C_GREEN], title=f"Distribution: {grp_a} vs {grp_b}")
                st.plotly_chart(style_plotly(fig_ab), use_container_width=True)

# ── BUSINESS INSIGHTS (Intelligence) ────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="step-banner">💡 Business Decision Support & Plain-English Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="explanation-box"><b>What this does:</b> Automatically analyzes your dataset to surface deep, actionable business insights across performance, risk, segmentation, and key drivers. No technical knowledge required.</div>', unsafe_allow_html=True)

    if not numeric_cols:
        st.info("⚠️ Upload data with numeric columns to generate automatic business insights.")
    else:
        st.markdown("### 📊 Automated Executive Summary")
        
        c_perf, c_risk = st.columns(2)
        c_seg, c_driv = st.columns(2)
        
        # 1. Performance & Trends
        with c_perf:
            st.markdown("#### 📈 Performance & Trends")
            perf_insights = []
            if date_cols and numeric_cols:
                time_col = date_cols[0]
                val_col = numeric_cols[0]
                temp_df = df.dropna(subset=[time_col, val_col]).copy()
                if not temp_df.empty:
                    temp_df.set_index(time_col, inplace=True)
                    try:
                        monthly = temp_df[val_col].resample('ME').sum()
                        if len(monthly) >= 2:
                            last_month = monthly.iloc[-1]
                            prev_month = monthly.iloc[-2]
                            mom = ((last_month - prev_month) / prev_month) * 100 if prev_month != 0 else 0
                            dir_str = "grew" if mom > 0 else "declined"
                            perf_insights.append(f"**Month-over-Month**: `{val_col}` {dir_str} by **{abs(mom):.1f}%** in the most recent month (from {prev_month:,.0f} to {last_month:,.0f}).")
                    except:
                        pass
            
            for col in numeric_cols[:2]:
                s = df[col].dropna()
                if len(s) > 0:
                    perf_insights.append(f"**Baseline Volume**: The average `{col}` per record is **{s.mean():,.2f}** (Median: {s.median():,.2f}). Total accumulated `{col}` is **{s.sum():,.0f}**.")
            
            for ins in perf_insights:
                st.info(ins)

        # 2. Risk Factors & Anomalies
        with c_risk:
            st.markdown("#### ⚠️ Risk Factors & Volatility")
            risk_insights = []
            for col in numeric_cols[:3]:
                s = df[col].dropna()
                if len(s) > 0 and s.mean() != 0:
                    cv = (s.std() / s.mean()) * 100
                    if cv > 100:
                        risk_insights.append(f"**High Volatility in `{col}`**: Variance is extreme (CV = {cv:.0f}%). This indicates highly unpredictable outcomes or severe outliers. **Recommendation**: Investigate extreme highs/lows.")
                    elif cv < 15:
                        risk_insights.append(f"**Stable Predictability in `{col}`**: Very low variance (CV = {cv:.0f}%). This metric is highly consistent and safe for baseline forecasting.")
            
            missing = df.isna().sum().sum()
            if missing > 0:
                risk_insights.append(f"**Data Integrity Risk**: There are **{missing:,}** missing data points across the dataset. This could skew strategic decisions if not cleaned.")
            
            if not risk_insights:
                risk_insights.append("No immediate risk factors or high volatility detected in primary metrics.")
            
            for ins in risk_insights:
                st.warning(ins)

        # 3. Segment Analysis
        with c_seg:
            st.markdown("#### 🎯 Market Segment Analysis")
            seg_insights = []
            if categorical_cols and numeric_cols:
                main_cat = categorical_cols[0]
                main_num = numeric_cols[0]
                grp = df.groupby(main_cat)[main_num].sum().sort_values(ascending=False)
                if len(grp) > 1:
                    total = grp.sum()
                    top_cat = grp.index[0]
                    top_share = (grp.iloc[0] / total) * 100 if total > 0 else 0
                    bottom_cat = grp.index[-1]
                    seg_insights.append(f"**Market Leader**: `{top_cat}` dominates the `{main_cat}` category, contributing **{top_share:.1f}%** of total `{main_num}`.")
                    seg_insights.append(f"**Underperformer**: `{bottom_cat}` generated the lowest total `{main_num}` ({grp.iloc[-1]:,.2f}). **Recommendation**: Consider reallocating resources or investigating root causes for this segment.")
            
            if not seg_insights:
                seg_insights.append("Not enough categorical data to perform segment analysis.")
                
            for ins in seg_insights:
                st.success(ins)

        # 4. Key Drivers & Correlations
        with c_driv:
            st.markdown("#### 🔗 Key Business Drivers")
            driver_insights = []
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                found_strong = False
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        r = corr_matrix.iloc[i, j]
                        if abs(r) > 0.65:
                            found_strong = True
                            dir_ = "strongly boosts" if r > 0 else "strongly suppresses"
                            impact = "positive" if r > 0 else "negative"
                            driver_insights.append(f"**Strategic Lever**: An increase in `{numeric_cols[i]}` {dir_} `{numeric_cols[j]}` (Correlation: {r:.2f}). These two move in a {impact} lockstep.")
                if not found_strong:
                    driver_insights.append("No strong linear relationships found between numeric metrics. Performance drivers may be non-linear or driven by external factors.")
            else:
                driver_insights.append("Need multiple numeric columns to find business drivers.")
                
            for ins in driver_insights:
                st.info(ins)

        # ── Data-Driven Strategic Recommendations ──
        st.markdown("---")
        st.markdown("### 📋 Executive Action Plan")
        st.markdown("<small style='color:#9CA3AF;'>Based on the mathematical realities of your dataset, here are the recommended next steps:</small>", unsafe_allow_html=True)
        
        recs = []
        if date_cols and numeric_cols:
            recs.append(f"**Implement Trend Forecasting**: Your data contains time-series history. Move to the **Time Intel** tab to isolate seasonal peaks and valleys for `{numeric_cols[0]}` to optimize inventory/staffing schedules.")
        if len(numeric_cols) >= 2:
            recs.append(f"**Predict Future Outcomes**: You have enough quantitative data to build an AI model. Use the **Predictive Models** tab to predict `{numeric_cols[0]}` based on other variables to proactively manage KPIs.")
        if categorical_cols:
            recs.append(f"**A/B Test Your Segments**: You have `{len(categorical_cols)}` categories. If you recently changed strategies in any of these segments, use the **A/B Testing** tab to mathematically prove if the change was successful.")
        if df.duplicated().sum() > 0:
            recs.append(f"**Immediate Data Cleanup**: {df.duplicated().sum()} duplicate records exist. Navigate to **Data Cleaning** immediately to prevent double-counting revenue/costs.")
        
        for idx, r in enumerate(recs, 1):
            st.markdown(f"{idx}. {r}")

# ── AUTOMATION (Management) ───────────────────────────────────────────────────
with tabs[4]:
    st.markdown("---")
    st.markdown('<div class="step-banner">⚙️ Automation & Report Generation</div>', unsafe_allow_html=True)
    st.markdown('<div class="explanation-box"><b>What this does:</b> Auto-generates a ready-to-share text report and provides reusable Python scripts to automate your data workflow.</div>', unsafe_allow_html=True)

    aut_c1, aut_c2 = st.columns(2)
    with aut_c1:
        st.markdown("##### 📝 Auto-Generate Report")
        report_title = st.text_input("Report Title", value="Data Analytics Report", key="rpt_title")
        analyst_name = st.text_input("Analyst Name", value="Analytics Team", key="rpt_analyst")
        if st.button("📄 Generate Text Report", type="primary", use_container_width=True):
            lines = [
                f"# {report_title}",
                f"Prepared by: {analyst_name}",
                f"Date: {datetime.date.today()}",
                f"Dataset Shape: {df.shape[0]:,} rows × {df.shape[1]} columns",
                "",
                "## Summary Statistics",
            ]
            for col in numeric_cols[:5]:
                s = df[col].dropna()
                lines.append(f"- **{col}**: Mean={s.mean():,.2f}, Median={s.median():,.2f}, Std={s.std():,.2f}, Min={s.min():,.2f}, Max={s.max():,.2f}")
            lines += ["", "## Data Quality",
                f"- Missing values: {df.isna().sum().sum():,}",
                f"- Duplicate rows: {df.duplicated().sum():,}",
                "", "## Key Observations"]
            if categorical_cols and numeric_cols:
                grp = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().sort_values(ascending=False)
                lines.append(f"- Top {categorical_cols[0]}: **{grp.index[0]}** ({grp.iloc[0]:,.2f})")
            report_text = "\n".join(lines)
            st.download_button("⬇️ Download Report (.txt)", report_text.encode(), f"{report_title.replace(' ','_')}.txt", "text/plain", use_container_width=True)
            st.code(report_text, language="markdown")

    with aut_c2:
        st.markdown("##### 🐍 Auto-Generated Python Script")
        st.markdown("<small style='color:#9CA3AF;'>Copy this script to automate your analysis pipeline.</small>", unsafe_allow_html=True)
        script = f"""import pandas as pd
import numpy as np

# ── Load Data ──────────────────────────────────────
df = pd.read_excel('your_file.xlsx')  # or pd.read_csv()

# ── Clean Data ─────────────────────────────────────
df.drop_duplicates(inplace=True)
df.dropna(how='all', axis=1, inplace=True)
for col in df.select_dtypes(include=np.number).columns:
    df[col].fillna(df[col].median(), inplace=True)
for col in df.select_dtypes(include='object').columns:
    df[col].fillna('Unknown', inplace=True)
    df[col] = df[col].str.strip()

# ── Summary Stats ──────────────────────────────────
print(df.describe())

# ── Numeric Columns: {', '.join(numeric_cols[:4])} ──
# ── Categorical Cols: {', '.join(categorical_cols[:4])} ──

print('Shape:', df.shape)
print('Missing:', df.isna().sum().sum())
"""
        st.code(script, language="python")
        st.download_button("⬇️ Download Script (.py)", script.encode(), "auto_analysis.py", "text/x-python", use_container_width=True)

# ── GOVERNANCE (Management) ───────────────────────────────────────────────────
with tabs[4]:
    st.markdown("---")
    st.markdown('<div class="step-banner">🏛️ Data Governance, Quality & Strategy</div>', unsafe_allow_html=True)
    st.markdown('<div class="explanation-box"><b>What this does:</b> Provides a full data quality audit, schema documentation, and strategic data health score to maintain governance standards.</div>', unsafe_allow_html=True)

    gov_c1, gov_c2 = st.columns(2)
    with gov_c1:
        st.markdown("##### 🔍 Data Quality Audit")
        audit_rows = []
        for col in df.columns:
            miss = df[col].isna().sum()
            miss_pct = miss / len(df) * 100
            uniq = df[col].nunique()
            dtype = str(df[col].dtype)
            status = "🔴 Critical" if miss_pct > 20 else ("🟡 Warning" if miss_pct > 5 else "🟢 Good")
            audit_rows.append({"Column": col, "Type": dtype, "Missing": f"{miss} ({miss_pct:.1f}%)", "Unique Values": uniq, "Quality": status})
        audit_df = pd.DataFrame(audit_rows)
        st.dataframe(audit_df, use_container_width=True, height=300)

        # Health Score
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isna().sum().sum()
        dup_rows = df.duplicated().sum()
        health = max(0, 100 - (missing_cells / total_cells * 60) - (dup_rows / len(df) * 40))
        color = C_GREEN if health > 75 else (C_AMBER if health > 50 else "#F43F5E")
        st.metric("Overall Data Health Score", f"{health:.0f}/100")

    with gov_c2:
        st.markdown("##### 📖 Data Dictionary / Schema")
        schema = []
        for col in df.columns:
            sample = df[col].dropna().head(3).tolist()
            schema.append({"Column": col, "Data Type": str(df[col].dtype), "Sample Values": ", ".join(str(s) for s in sample), "Null Count": int(df[col].isna().sum())})
        st.dataframe(pd.DataFrame(schema), use_container_width=True, height=300)

        st.markdown("##### 🛡️ Governance Checklist")
        checks = [
            (df.isna().sum().sum() == 0, "No missing values in dataset"),
            (df.duplicated().sum() == 0, "No duplicate rows"),
            (len(numeric_cols) > 0, "Numeric columns present and usable"),
            (len(date_cols) > 0, "Date columns available for time analysis"),
            (len(df) >= 30, "Sufficient sample size (≥30 rows)"),
        ]
        for passed, label in checks:
            icon = "✅" if passed else "❌"
            st.markdown(f"{icon} {label}")

# ── RAW DATA (Management) ─────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("---")
    st.markdown("##### 🔎 Filtered & Cleaned Records")
    st.dataframe(df, use_container_width=True, height=450)
    st.download_button("⬇️ Export to CSV", df.to_csv(index=False).encode("utf-8"), "dataset_export.csv", "text/csv")

st.markdown("---")
st.markdown("<p style='text-align:center;color:#9CA3AF;font-size:13px;'>Data Analytics Dashboard • Built with Streamlit</p>", unsafe_allow_html=True)
