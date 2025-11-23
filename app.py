import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")

# -------------------------
# COLOR AND PATH DEFINITIONS
# -------------------------

# Define color themes
THEME_COLORS = {
    'dark': {
        'BG_PRIMARY': '#0E1117',   # Hlavní tmavé pozadí
        'BG_SECONDARY': '#FFFFFF', # Světlé pozadí pro kontrastní sekci (kategorie)
        'TEXT_PRIMARY': '#FFFFFF', # Bílý text na tmavém pozadí
        'TEXT_SECONDARY': '#0E1117', # Tmavý text na světlém pozadí
        'BORDER_LINE': '#31333F',  # Tmavá linka / mřížka
        'TABLE_BG': '#0E1117',     # Pozadí tabulky (stejné jako BG_PRIMARY)
    },
    'light': {
        'BG_PRIMARY': '#FFFFFF',   # Hlavní světlé pozadí
        'BG_SECONDARY': '#F0F2F6', # Světle šedé pozadí pro kontrastní sekci
        'TEXT_PRIMARY': '#0E1117', # Tmavý text na světlém pozadí
        'TEXT_SECONDARY': '#0E1117', # Tmavý text na světlém pozadí
        'BORDER_LINE': '#CCCCCC',  # Světlá linka / mřížka
        'TABLE_BG': '#FFFFFF',     # Pozadí tabulky (stejné jako BG_PRIMARY)
    }
}

# 1. Theme Selector in sidebar
theme_name = st.sidebar.radio("Zvolte motiv:", ('Dark', 'Light'), index=0)
current_theme = THEME_COLORS[theme_name.lower()]

# Assign current theme colors to variables for simpler use
BG_PRIMARY = current_theme['BG_PRIMARY']
BG_SECONDARY = current_theme['BG_SECONDARY']
TEXT_PRIMARY = current_theme['TEXT_PRIMARY']
TEXT_SECONDARY = current_theme['TEXT_SECONDARY']
BORDER_LINE = current_theme['BORDER_LINE']
TABLE_BG = current_theme['TABLE_BG']

# File paths
CSV_FILE_PATH = "usd_macro_history.csv.txt" 
DXY_LINES_PATH = "dxy_linechart_history.csv.txt" # Původní název souboru
DXY_HEATMAP_PATH = "dxy_seasonality_heatmap_history.csv.txt" 

LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# CATEGORY NAMES ARE ALREADY IN ENGLISH IN DATA FILE
CATEGORY_KEYWORDS = {
    "Inflation": [], "Interest Rates": [], "Labor Market": [], "Economic Activity": []
}

# -------------------------
# CORE CSS FOR STABILITY AND DESIGN (DYNAMICALLY GENERATED)
# -------------------------
st.markdown(f"""
<style>
/* 1. Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@300;400;700&display=swap');

/* 2. Streamlit global settings */
.stApp {{
    padding-top: 20px;
    background-color: {BG_PRIMARY}; 
    color: {TEXT_PRIMARY}; 
}}

/* 3. Styling headers (Montserrat Light, Uppercase) */
h1, h2, h3, h4, .small-title {{
    font-family: 'Montserrat', sans-serif !important; 
    text-align: center;
    color: {TEXT_PRIMARY};
    font-weight: 300; 
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: 10px;
    margin-bottom: 20px;
}}
.small-title {{
    font-size: 0.9em;
    margin-bottom: 10px;
}}

/* 4. Styling text and motto */
p, div, label {{
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300; 
    color: {TEXT_PRIMARY}; 
}}
/* Motto - Libre Baskerville, Uppercase */
.motto {{
    font-family: 'Libre Baskerville', serif !important;
    font-weight: 400; 
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: -10px;
    font-size: 1.1em;
    text-align: center; 
    color: {TEXT_PRIMARY};
}}

/* Set text color in the secondary section */
.section-secondary p, .section-secondary div, .section-secondary label {{
    color: {TEXT_SECONDARY}; 
}}

/* *** CRITICAL FIX: AI BOX (st.info) - DYNAMIC COLORS *** */
div[data-testid="stAlert"] {{
    background-color: {BG_PRIMARY} !important; 
    border: 1px solid {TEXT_PRIMARY} !important; 
    color: {TEXT_PRIMARY} !important; 
    padding: 20px;
    margin-top: 10px;
}}
div[data-testid="stAlert"] div[role="alert"] {{
    background-color: {BG_PRIMARY} !important; 
}}
div[data-testid="stAlert"] svg {{
    fill: {TEXT_PRIMARY} !important; 
}}


/* *** Targeting PANDAS STYLER for dynamic tables *** */

/* 1. Aggressive target to remove wrapper borders from st.table */
div[data-testid="stTable"] {{
    box-shadow: none !important;
    border: none !important;
}}

/* 2. Styling the table itself, embedded in the .dynamic-table wrapper */
.dynamic-table table thead th, 
.dynamic-table table tbody td {{
    background-color: {TABLE_BG} !important; 
    color: {TEXT_PRIMARY} !important; 
    border: 1px solid {BORDER_LINE} !important; 
    border-radius: 0px !important;
    box-shadow: none !important;
}}
.dynamic-table table {{
    background-color: {TABLE_BG} !important;
    border-radius: 0px !important;
    border: none !important;
    border-collapse: collapse; 
}}

/* Prevents text wrapping in table headers in categories section */
.dynamic-table table th {{
    white-space: nowrap !important;
}}

/* Centering Total Score */
.score-line-container {{
    border: none; 
    padding: 0;
    display: block; 
    margin: 20px auto 30px auto; 
    text-align: center;
}}
.score-line {{
    font-size: 1.5em;
    font-weight: 400; 
    display: block; 
    color: {TEXT_PRIMARY}; 
}}

/* --- COLOR SECTIONS (Alternating Background) --- */
.section-primary {{ 
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    padding: 20px 0;
}}
.section-secondary {{ 
    background-color: {BG_SECONDARY};
    color: {TEXT_SECONDARY};
    padding: 20px 0;
}}
.section-secondary h2, .section-secondary h3, .section-secondary h4 {{
    color: {TEXT_SECONDARY} !important;
}}
.section-primary h2, .section-primary h3, .section-primary h4 {{
    color: {TEXT_PRIMARY} !important;
}}

/* Add spacing between sections */
.section-spacer {{
    height: 30px; 
}}

/* ENSURING CENTERING OF ALL ELEMENTS IN ST.TABLE AND ST.DATAFRAME AND SCORE */
div[data-testid="stTable"], div[data-testid="stDataFrame"] {{
    display: flex;
    justify-content: center;
    width: 100%; 
}}
/* Forces centering of score-line-container */
.center-div {{
    display: flex;
    justify-content: center;
    width: 100%; 
}}

</style>
""", unsafe_allow_html=True)

# -------------------------
# DATA CONFIGURATION AND HELPERS
# -------------------------

def clean_num(x):
    if x is None: return None
    s = str(x).strip()
    if s.startswith('.'): s = s[1:]
    if s == "" or s == "-" or s.lower() == "n/a" or s.lower() == "nan": return None
    # Při načítání CSV souboru se ujistíme, že data jsou správně parsována (např. nahrazením čárky tečkou)
    s = s.replace(",", ".").replace("%", "").replace("K", "000").replace("M", "000000").replace("B", "000000000")
    try: return float(s)
    except: return None

@st.cache_data
def load_events_from_csv():
    if not os.path.exists(CSV_FILE_PATH):
        st.error(f"Error: Data file '{CSV_FILE_PATH}' not found. Please create it according to the template.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        required_cols = ['Date', 'Category', 'Actual', 'Forecast', 'Report']
        if not all(col in df.columns for col in required_cols):
             st.error(f"Error: The CSV is missing one of the required columns: {required_cols}")
             return pd.DataFrame()

        df["DateParsed"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["DateParsed"].notna()]
        df = df[df["DateParsed"] >= pd.Timestamp(START_DATE)]
        
        return df.sort_values("DateParsed", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"Could not load or process the CSV file. Error: {e}")
        return pd.DataFrame()

# Loads multi-line seasonality data
@st.cache_data
def load_seasonality_lines_data():
    if not os.path.exists(DXY_LINES_PATH):
        return None
    try:
        # Použijeme decimal='.' a sep=',' pro konzistentní načítání
        df = pd.read_csv(DXY_LINES_PATH, decimal='.', sep=',') 
        
        expected_cols = ['Month', 'Return_15Y', 'Return_10Y', 'Return_5Y']
        if not all(col in df.columns for col in expected_cols):
            # Pokud chybí sloupce, vrátíme prázdný DataFrame, ne None, abychom zamezili KeyError v .melt()
            return pd.DataFrame()
        
        month_to_index = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        df['Month_Index'] = df['Month'].map(month_to_index)
        
        if df['Month_Index'].isnull().any():
             return pd.DataFrame()
             
        df = df.sort_values('Month_Index').reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()
        
# Loads heatmap seasonality data
@st.cache_data
def load_seasonality_heatmap_data():
    if not os.path.exists(DXY_HEATMAP_PATH):
        return None
    try:
        # Použijeme engine='python' a upravený regex pro oddělovače (problém s čárkou v May 2025)
        # NEBO POUŽIJEME: sep=',' a ubezpečíme se, že všechna data jsou s tečkou
        df = pd.read_csv(DXY_HEATMAP_PATH, decimal='.', sep=',') 
        
        expected_cols = ['Year', 'Month', 'Return']
        if not all(col in df.columns for col in expected_cols):
            return None
            
        # Převedeme sloupec Return, kde nahradíme čárky tečkami (kvůli May 2025 datům)
        df['Return'] = df['Return'].astype(str).str.replace(',', '.', regex=False)
        df['Return'] = pd.to_numeric(df['Return'], errors='coerce')
        df = df[df['Return'].notna()] # Odstraníme řádky s neparsovatelnými daty
        
        df['Year'] = df['Year'].astype(str)
        
        month_to_index = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        df['Month_Index'] = df['Month'].map(month_to_index)
        
        if df['Month_Index'].isnull().any():
             return None
             
        df = df.sort_values(['Year', 'Month_Index'], ascending=[False, True]).reset_index(drop=True)
        return df
    except Exception:
        return None

def score_event(row):
    a = clean_num(row.get("Actual"))
    f = clean_num(row.get("Forecast"))
    if a is None or f is None: return 0
    if a > f: return 1
    if a < f: return -1
    return 0

def evaluate_category(df_cat):
    df_scored = df_cat[pd.to_numeric(df_cat['Points'], errors='coerce').notna()]
    total = int(df_scored["Points"].sum())
    
    if total >= 2: label = "Bullish"
    elif total <= -2: label = "Bearish"
    else: label = "Neutral" # Catches 1, 0, -1
    return total, label

def generate_ai_summary(summary_df, final_score, overall_label):
    if not summary_df.empty:
        strongest = summary_df.sort_values('Total Points', ascending=False).iloc[0]
        weakest = summary_df.sort_values('Total Points', ascending=True).iloc[0]
    else:
        strongest = {'Category': 'N/A', 'Total Points': 0}
        weakest = {'Category': 'N/A', 'Total Points': 0}
    
    summary = f"The overall fundamental score for USD over the last 3 months reached {final_score:+d}, signaling a **{overall_label}** sentiment for the US Dollar. "
    
    if strongest['Total Points'] > 0:
        summary += f"The strongest support came from the **{strongest['Category']}** category ({strongest['Total Points']:+d}), where reports consistently beat expectations. "
    
    if weakest['Total Points'] < 0:
        summary += f"Negative pressure on the dollar is coming from the **{weakest['Category']}** sector ({weakest['Total Points']:+d}). "
        
    summary += "Overall, the situation is balanced with clear strengths and weaknesses that investors should monitor."
    
    return summary

def generate_dxy_seasonality_data():
    # Mock data for DXY lines (used if CSV file is missing or invalid)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Mock data based on the provided values in dxy_linechart_history.csv.txt [cite: 3]
    mock_returns_15Y = [0.16, 0.52, 0.03, -0.65, 1.19, -0.33, -0.35, 0.10, 0.62, 0.40, 0.67, -0.56]
    mock_returns_10Y = [0.35, 0.55, 0.05, -0.60, 0.90, -0.30, -0.50, 0.10, 0.70, 0.45, 0.80, -0.60]
    mock_returns_5Y = [0.15, 0.40, 0.20, -0.45, 1.20, -0.10, -0.35, 0.00, 0.55, 0.30, 0.65, -0.40]

    
    df = pd.DataFrame({
        "Month": months,
        "Return_15Y": mock_returns_15Y,
        "Return_10Y": mock_returns_10Y,
        "Return_5Y": mock_returns_5Y
    })
    
    month_to_index = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    df['Month_Index'] = df['Month'].map(month_to_index)
    return df.set_index('Month_Index').sort_values('Month_Index')

# Defines Pandas Styler dynamically based on theme
dynamic_styler = [
    {'selector': 'th, td',
     'props': [('background-color', TABLE_BG), 
               ('color', TEXT_PRIMARY),
               ('border', f'1px solid {BORDER_LINE}'), 
               ('border-radius', '0')]},
    {'selector': 'table',
     'props': [('border-collapse', 'collapse')]}
]

# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. MAIN TITLE AND MOTTO (Uses section-primary)
st.markdown("<div class='section-primary'>", unsafe_allow_html=True)
st.markdown("<p class='small-title'>USD MACRO AI DASHBOARD</p>", unsafe_allow_html=True) 
st.title("AURICAI AI")
st.markdown("<p class='motto'>\"BEAT THE ODDS\"</p>", unsafe_allow_html=True) 
st.markdown("---")

# Loading data
with st.spinner(f"Loading data from local file '{CSV_FILE_PATH}'..."):
    df_high = load_events_from_csv()

if df_high.empty:
    st.error("Could not load any valid data. Check 'usd_macro_history.csv.txt'.")
    st.stop()

df_high["Points"] = df_high.apply(score_event, axis=1)
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

df_scored = df_high[pd.to_numeric(df_high['Actual'], errors='coerce').notna()].copy()
df_all_display = df_high.copy()
st.markdown("</div>", unsafe_allow_html=True) # End PRIMARY section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 3. FUNDAMENTAL NEWS BREAKDOWN BY CATEGORY (Uses section-secondary)
# -------------------------
st.markdown("<div class='section-secondary'>", unsafe_allow_html=True)
st.header("Fundamental News Breakdown by Category")

cols = st.columns(2)

category_frames = {}
unique_categories = df_all_display["Category"].unique() 

for i, cat in enumerate(unique_categories):
    cat_df_display = df_all_display[df_all_display["Category"] == cat].copy()
    if cat_df_display.empty: continue 
    
    cat_df_scored = df_scored[df_scored["Category"] == cat].copy()
    category_frames[cat] = cat_df_scored

    cat_df_display = cat_df_display.sort_values("DateParsed", ascending=False)
    display_df = cat_df_display[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    )
    
    # Use dynamic styler (table is in original state, without row index)
    styled_df = display_df.style.set_table_styles(dynamic_styler).hide(axis="index")

    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.markdown(f'<div class="dynamic-table">', unsafe_allow_html=True)
            st.table(styled_df)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.markdown(f'<div class="dynamic-table">', unsafe_allow_html=True)
            st.table(styled_df)
            st.markdown('</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True) # End SECONDARY section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 4. FUNDAMENTAL EVALUATION AND AI ANALYSIS (Uses section-primary)
# -------------------------
st.markdown("<div class='section-primary'>", unsafe_allow_html=True)
st.header("Fundamental Evaluation") 

summary_rows = []
total_combined_score = 0

for cat, df_cat in category_frames.items():
    total, label = evaluate_category(df_cat)
    total_combined_score += total
    summary_rows.append({
        "Category": cat,
        "Events Count": int(len(df_cat)),
        "Total Points": total,
        "Evaluation": label
    })

summary_df = pd.DataFrame(summary_rows)
final_score = total_combined_score

if final_score >= 2: final_label = "BULLISH"
elif final_score <= -2: final_label = "BEARISH"
else: final_label = "NEUTRAL"

# Use dynamic styler (table is in original state, without row index)
styled_summary = summary_df.style.set_table_styles(dynamic_styler).hide(axis="index").format({"Total Points":"{:+d}"})

# Display summary table
st.markdown(f'<div class="dynamic-table">', unsafe_allow_html=True)
st.table(styled_summary) 
st.markdown('</div>', unsafe_allow_html=True)

# Highlight Total Score (CENTERED)
st.markdown("<div class='center-div'>", unsafe_allow_html=True) 
st.markdown(f"<div class='score-line-container'><span class='score-line'>Total Fundamental Score: {final_score:+d} — {final_label}</span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# AI Assessment (uses st.info, dynamically colored)
st.subheader("AI Fundamental Assessment")
ai_text_content = generate_ai_summary(summary_df, final_score, final_label)
st.info(ai_text_content)
st.markdown("</div>", unsafe_allow_html=True) # End PRIMARY section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 5. FUNDAMENTAL CATEGORIES CHART (Uses section-primary)
# -------------------------
st.markdown("<div class='section-primary'>", unsafe_allow_html=True)
st.header("Fundamental Categories Chart") 

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Points by Category Over Time (Daily Aggregate of Events)")
    
    # Plotly dynamic styling
    fig.update_layout(
        plot_bgcolor=f"{BG_PRIMARY}", 
        paper_bgcolor=f"{BG_PRIMARY}",
        font_color=f"{TEXT_PRIMARY}",
        title_font_color=f"{TEXT_PRIMARY}",
        xaxis=dict(gridcolor=BORDER_LINE, linecolor=BORDER_LINE),
        yaxis=dict(gridcolor=BORDER_LINE, linecolor=BORDER_LINE)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data for the chart.")
st.markdown("</div>", unsafe_allow_html=True) # End PRIMARY section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 5.5 USD SEASONALITY CHARTS (Uses section-primary)
# -------------------------
st.markdown("<div class='section-primary'>", unsafe_allow_html=True)
st.header("U.S. Dollar Index Seasonality Charts") 

# --- 5.5.1 Multi-Line Chart (15Y, 10Y, 5Y) ---
st.subheader("Average Monthly Return: 15Y vs. 10Y vs. 5Y")
df_seasonality_lines = load_seasonality_lines_data()

# Použijeme MOCK data pouze v případě, že se načtení nepodařilo (tedy df je prázdné)
if df_seasonality_lines.empty:
    df_seasonality_lines = generate_dxy_seasonality_data()
    st.info(f"Note: Could not load or process seasonality file '{DXY_LINES_PATH}' correctly. Displaying MOCK seasonality data based on expected columns.")
    
# --- Vykreslení Line Chart ---
if not df_seasonality_lines.empty:
    
    df_melted = df_seasonality_lines.melt(
        id_vars=['Month', 'Month_Index'], 
        value_vars=['Return_15Y', 'Return_10Y', 'Return_5Y'],
        var_name='Period', 
        value_name='Average Return (%)'
    )
    
    fig_season_lines = px.line(df_melted, 
                        x="Month", 
                        y="Average Return (%)",
                        color="Period", 
                        title="Average Monthly Return by Period",
                        labels={"Average Return (%)": "Average Return (%)", "Month": "Month"},
                        markers=True, line_shape='linear',
                        category_orders={"Month": df_seasonality_lines['Month'].tolist()}) 

    fig_season_lines.add_hline(y=0, line_dash="dash", line_color=BORDER_LINE)

    # Plotly dynamic styling
    fig_season_lines.update_layout(
        plot_bgcolor=f"{BG_PRIMARY}", 
        paper_bgcolor=f"{BG_PRIMARY}",
        font_color=f"{TEXT_PRIMARY}",
        title_font_color=f"{TEXT_PRIMARY}",
        xaxis=dict(gridcolor=BORDER_LINE, linecolor=BORDER_LINE),
        yaxis=dict(gridcolor=BORDER_LINE, linecolor=BORDER_LINE),
        legend_title_text='Period' 
    )
    st.plotly_chart(fig_season_lines, use_container_width=True)
else:
    st.info("Seasonality line chart data is unavailable.")


# --- 5.5.2 Heatmap Chart ---
st.subheader("USDX Monthly Return Heatmap (By Year)")
df_seasonality_heatmap = load_seasonality_heatmap_data()

# --- Vykreslení Heatmap Chart ---
if df_seasonality_heatmap is None or df_seasonality_heatmap.empty:
    st.info(f"Note: Heatmap file '{DXY_HEATMAP_PATH}' missing or contains invalid data. Heatmap chart is not available.")
else:
    # Použijeme měsíční pořadí z line chart, pokud je dostupné, jinak základní řazení
    month_order = df_seasonality_lines['Month'].tolist() if not df_seasonality_lines.empty else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Využijeme data z Heatmap pro max_abs, kde už jsou ošetřeny čárky v desetinných číslech
    max_abs = df_seasonality_heatmap['Return'].abs().max() * 1.05 
    
    fig_heatmap = px.density_heatmap(df_seasonality_heatmap,
                                 x="Month", 
                                 y="Year", 
                                 z="Return",
                                 category_orders={"Month": month_order, "Year": sorted(df_seasonality_heatmap['Year'].unique(), reverse=True)},
                                 color_continuous_scale='RdYlGn', 
                                 range_color=[-max_abs, max_abs],
                                 title="Monthly Return Heatmap by Year")

    # Plotly dynamic styling
    fig_heatmap.update_layout(
        plot_bgcolor=f"{BG_PRIMARY}", 
        paper_bgcolor=f"{BG_PRIMARY}",
        font_color=f"{TEXT_PRIMARY}",
        title_font_color=f"{TEXT_PRIMARY}",
        xaxis=dict(tickangle=45, gridcolor=BORDER_LINE, linecolor=BORDER_LINE),
        yaxis=dict(gridcolor=BORDER_LINE, linecolor=BORDER_LINE),
        coloraxis_colorbar=dict(title="Return (%)", tickfont=dict(color=TEXT_PRIMARY))
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # End PRIMARY section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer
    
# -------------------------
# 6. EXPORT / DOWNLOAD (Uses section-primary)
# -------------------------
st.markdown("<div class='section-primary'>", unsafe_allow_html=True)
st.header("Export / Download")

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download Events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_manual.csv", "text/csv")
st.markdown("</div>", unsafe_allow_html=True) # End PRIMARY section