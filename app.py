import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# GLOBAL CONFIGURATION
# -------------------------
# Streamlit se automaticky přepne na Dark/Light motiv podle systémového nastavení
st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide", initial_sidebar_state="collapsed") 

# Definováni barev pro Plotly (pro čitelnost v obou módech)
# BORDER_DARK používáme jako barvu mřížky, která je viditelná na světlém i tmavém pozadí
BORDER_DARK = '#31333F' 

CSV_FILE_PATH = "usd_macro_history.csv.txt" 
DXY_LINES_PATH = "dxy_linechart_history.csv.txt" 
DXY_HEATMAP_PATH = "dxy_seasonality_heatmap_history.csv.txt" 

LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# CATEGORY NAMES ARE ALREADY IN ENGLISH IN DATA FILE
CATEGORY_KEYWORDS = {
    "Inflation": [], "Interest Rates": [], "Labor Market": [], "Economic Activity": []
}


# -------------------------
# CORE CSS FOR STABILITY AND DESIGN (Základní styling)
# -------------------------
st.markdown(f"""
<style>
/* 1. Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@300;400;700&display=swap');

/* 3. Styling headers (Montserrat Light, Uppercase) */
h1, h2, h3, h4, .small-title {{
    font-family: 'Montserrat', sans-serif !important; 
    text-align: center;
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
}}

/* Centering Total Score (pouze text styling) */
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
}}

/* Centering of st.dataframe (pro původní vzhled tabulek) */
div[data-testid="stDataFrame"] {{
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
    # Použijeme replace(',', '.') pro ošetření evropského formátu desetinných čísel (čárka)
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
        return pd.DataFrame() 
    try:
        df = pd.read_csv(DXY_LINES_PATH, decimal='.', sep=',') 
        
        expected_cols = ['Month', 'Return_15Y', 'Return_10Y', 'Return_5Y']
        if not all(col in df.columns for col in expected_cols):
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
        
# Loads heatmap seasonality data (S ROBUSTNÍ A EXPLICITNÍ TYPOVOU OPRAVOU)
@st.cache_data
def load_seasonality_heatmap_data():
    if not os.path.exists(DXY_HEATMAP_PATH):
        return pd.DataFrame()
    try:
        # Přečteme soubor. decimal='.' zajišťuje, že čteme desetinnou tečku.
        df = pd.read_csv(DXY_HEATMAP_PATH, sep=',', decimal='.') 
        
        expected_cols = ['Year', 'Month', 'Return']
        if not all(col in df.columns for col in expected_cols):
            return pd.DataFrame()
            
        # Explicitní typová konverze
        df['Return'] = pd.to_numeric(df['Return'], errors='coerce', downcast='float')
        df = df[df['Return'].notna()] # Odstraníme řádky, kde se parsování nepodařilo
        
        df['Year'] = df['Year'].astype(str)
        
        month_to_index = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        df['Month_Index'] = df['Month'].map(month_to_index)
        
        if df['Month_Index'].isnull().any():
             return pd.DataFrame()
             
        df = df.sort_values(['Year', 'Month_Index'], ascending=[False, True]).reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()

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
    # Mock data pro Line Chart (použité při selhání načtení z CSV)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Mock data based on the provided values in dxy_linechart_history.csv.txt
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


# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. MAIN TITLE AND MOTTO
st.markdown("<div style='padding-top: 20px;'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True) 
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) 

# -------------------------
# 3. FUNDAMENTAL NEWS BREAKDOWN BY CATEGORY (Používá st.dataframe)
# -------------------------
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
    # Původní zobrazení tabulky
    display_df = cat_df_display[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    ).reset_index(drop=True) 

    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.dataframe(display_df, use_container_width=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.dataframe(display_df, use_container_width=True)

st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) 

# -------------------------
# 4. FUNDAMENTAL EVALUATION AND AI ANALYSIS 
# -------------------------
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

# Původní zobrazení tabulky
st.dataframe(summary_df.reset_index(drop=True).rename(columns={"Total Points":"Total Points"}), use_container_width=True)


# Highlight Total Score (CENTERED)
st.markdown("<div class='center-div'>", unsafe_allow_html=True) 
st.markdown(f"<div class='score-line-container'><span class='score-line'>Total Fundamental Score: {final_score:+d} — {final_label}</span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# AI Assessment (uses st.info)
st.subheader("AI Fundamental Assessment")
ai_text_content = generate_ai_summary(summary_df, final_score, final_label)
st.info(ai_text_content)
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) 

# -------------------------
# 5. FUNDAMENTAL CATEGORIES CHART
# -------------------------
st.header("Fundamental Categories Chart") 

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Points by Category Over Time (Daily Aggregate of Events)")
    
    # Plotly dynamický styling (Transparentní pro system preference)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data for the chart.")
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) 

# -------------------------
# 5.5 USD SEASONALITY CHARTS
# -------------------------
st.header("U.S. Dollar Index Seasonality Charts") 

# --- 5.5.1 Multi-Line Chart (15Y, 10Y, 5Y) ---
st.subheader("Average Monthly Return: 15Y vs. 10Y vs. 5Y")
df_seasonality_lines = load_seasonality_lines_data()

# Použijeme MOCK data pouze v případě, že se načtení nepodařilo
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

    fig_season_lines.add_hline(y=0, line_dash="dash", line_color=BORDER_DARK)

    # Plotly dynamic styling (Transparentní pro system preference)
    fig_season_lines.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        legend_title_text='Period' 
    )
    st.plotly_chart(fig_season_lines, use_container_width=True)
else:
    st.info("Seasonality line chart data is unavailable.")


# --- 5.5.2 Heatmap Chart ---
st.subheader("USDX Monthly Return Heatmap (By Year)")
df_seasonality_heatmap = load_seasonality_heatmap_data()

# --- Vykreslení Heatmap Chart ---
if df_seasonality_heatmap.empty:
    st.info(f"Note: Heatmap file '{DXY_HEATMAP_PATH}' missing or contains invalid data. Heatmap chart is not available.")
else:
    month_order = df_seasonality_lines['Month'].tolist() if not df_seasonality_lines.empty else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # 1. Výpočet pro striktně dvoubarevnou stupnici (červená/zelená)
    min_val = df_seasonality_heatmap['Return'].min()
    max_val = df_seasonality_heatmap['Return'].max()
    range_val = max_val - min_val

    # Vypočítáme normalizovanou pozici nuly v rozsahu [0, 1]
    P0 = (0 - min_val) / range_val if range_val != 0 else 0.5
    
    # Definice ostře přecházející barevné škály: Červená pro < 0, Zelená pro >= 0
    custom_two_color_scale = [
        [0.0, 'red'],
        [P0 - 1e-9, 'red'], # Vše pod nulou je červené
        [P0 + 1e-9, 'green'], # Vše nad nulou je zelené
        [1.0, 'green']
    ]

    # 2. Přidání textového popisku (formátováno na dvě desetinná místa)
    df_seasonality_heatmap['Return_Text'] = df_seasonality_heatmap['Return'].apply(lambda x: f"{x:+.2f}")

    # Seznam unikátních let pro explicitní řazení Y-osy
    year_order = sorted(df_seasonality_heatmap['Year'].unique(), key=lambda x: int(x), reverse=True)
    
    fig_heatmap = px.density_heatmap(df_seasonality_heatmap,
                                 x="Month", 
                                 y="Year", 
                                 z="Return", # Používá se pro určení barvy
                                 text_auto=False, # Vypneme automatický text
                                 # OPRAVA ZDE: Předáváme název sloupce jako řetězec, ne Pandas Series.
                                 text='Return_Text', # Nastavíme vlastní text
                                 category_orders={"Month": month_order, "Year": year_order},
                                 color_continuous_scale=custom_two_color_scale, # Aplikace dvoubarevné škály
                                 range_color=[min_val, max_val], # Rozsah musí pokrýt celá data
                                 title="Monthly Return Heatmap by Year (Red=Negative, Green=Positive)")

    # Plotly dynamic styling
    fig_heatmap.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=45, gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        coloraxis_colorbar=dict(title="Return (%)", tickvals=[min_val, 0, max_val], ticktext=[f"{min_val:.2f} (Negative)", "0.00", f"{max_val:.2f} (Positive)"]) 
    )
    # Zajištění, že text je viditelný a bez pop-upu
    fig_heatmap.update_traces(texttemplate='%{text}', hovertemplate=None, selector=dict(type='heatmap'))

    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) 
    
# -------------------------
# 6. EXPORT / DOWNLOAD
# -------------------------
st.header("Export / Download")

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download Events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_manual.csv", "text/csv")