import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# COLOR AND PATH DEFINITIONS
# -------------------------
BG_BLACK = '#0E1117' # Dark Streamlit Background
BG_CREAM = '#FFFFFF' # Pure White Background (for CREAM section)
TEXT_CREAM = '#FFFFFF' # Pure White Text
TEXT_BLACK = '#0E1117' # Dark text color (for CREAM section)

# New color for borders and chart lines
BORDER_DARK = '#31333F' 

CSV_FILE_PATH = "usd_macro_history.csv.txt" 
DXY_HISTORY_PATH = "dxy_linechart_history.csv.txt" # NEW FILE PATH
LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# CATEGORY NAMES ARE ALREADY IN ENGLISH IN DATA FILE
CATEGORY_KEYWORDS = {
    "Inflation": [], "Interest Rates": [], "Labor Market": [], "Economic Activity": []
}

# -------------------------
# CORE CSS FOR STABILITY AND DESIGN
# -------------------------
st.markdown(f"""
<style>
/* 1. Import Google Fonts (For reliable fallbacks) */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@300;400;700&display=swap');

/* 2. Streamlit global settings */
.stApp {{
    padding-top: 20px;
    background-color: {BG_BLACK}; 
    color: {TEXT_CREAM}; /* Pure White Text */
}}

/* 3. Styling headers (Montserrat Light, Uppercase) */
h1, h2, h3, h4, .small-title {{
    font-family: 'Montserrat', sans-serif !important; 
    text-align: center;
    color: {TEXT_CREAM};
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
    color: {TEXT_CREAM}; /* Default text color */
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
    color: {TEXT_CREAM};
}}

/* Set text color in the white section */
.section-cream p, .section-cream div, .section-cream label {{
    color: {TEXT_BLACK}; 
}}

/* *** CRITICAL FIX: AI BOX (st.info) - REMOVE BLUE FILL *** */
div[data-testid="stAlert"] {{
    background-color: {BG_BLACK} !important; 
    border: 1px solid {TEXT_CREAM} !important; 
    color: {TEXT_CREAM} !important; 
    padding: 20px;
    margin-top: 10px;
}}
div[data-testid="stAlert"] div[role="alert"] {{
    background-color: {BG_BLACK} !important; 
}}
div[data-testid="stAlert"] svg {{
    fill: {TEXT_CREAM} !important; 
}}


/* *** Targeting PANDAS STYLER for dark tables (st.table method) *** */

/* 1. Aggressive target to remove wrapper borders from st.table */
div[data-testid="stTable"] {{
    box-shadow: none !important;
    border: none !important;
}}

/* 2. Styling the table itself, embedded in the .dark-table wrapper */
.dark-table table thead th, 
.dark-table table tbody td {{
    background-color: {BG_BLACK} !important; 
    color: {TEXT_CREAM} !important; /* Pure white text on dark background */
    border: 1px solid {BORDER_DARK} !important; /* Dark table border */
    border-radius: 0px !important;
    box-shadow: none !important;
}}
.dark-table table {{
    background-color: {BG_BLACK} !important;
    border-radius: 0px !important;
    border: none !important;
    border-collapse: collapse; /* Ensures sharp edges */
}}

/* Prevents text wrapping in table headers in categories section (fixes "Actua" and "l") */
.dark-table table th {{
    white-space: nowrap !important;
}}

/* Centering Total Score (no border) */
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
    color: {TEXT_CREAM}; 
}}

/* --- COLOR SECTIONS (Alternating Background) --- */
.section-black {{
    background-color: {BG_BLACK};
    color: {TEXT_CREAM};
    padding: 20px 0;
}}
.section-cream {{
    background-color: {BG_CREAM};
    color: {TEXT_BLACK};
    padding: 20px 0;
}}
.section-cream h2, .section-cream h3, .section-cream h4 {{
    color: {TEXT_BLACK} !important;
}}
.section-black h2, .section-black h3, .section-black h4 {{
    color: {TEXT_CREAM} !important;
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

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")

# -------------------------
# DATA CONFIGURATION
# -------------------------
CSV_FILE_PATH = "usd_macro_history.csv.txt" 
DXY_HISTORY_PATH = "dxy_linechart_history.csv.txt" # NEW FILE PATH
LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# CATEGORY NAMES ARE ALREADY IN ENGLISH IN DATA FILE
CATEGORY_KEYWORDS = {
    "Inflation": [], "Interest Rates": [], "Labor Market": [], "Economic Activity": []
}

# --- HELPER FUNCTIONS ---
def clean_num(x):
    if x is None: return None
    s = str(x).strip()
    if s.startswith('.'): s = s[1:]
    if s == "" or s == "-" or s.lower() == "n/a" or s.lower() == "nan": return None
    s = s.replace("%", "").replace(",", "").replace("K", "000").replace("M", "000000").replace("B", "000000000")
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
        
        # Data file must now contain English categories (Inflation, Labor Market, etc.)
        
        return df.sort_values("DateParsed", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"Could not load or process the CSV file. Error: {e}")
        return pd.DataFrame()

# NEW FUNCTION: Loads actual USDX seasonality data
@st.cache_data
def load_seasonality_data():
    if not os.path.exists(DXY_HISTORY_PATH):
        return None
    try:
        # Expects 'Month' column (as month name) and 'Return' (as average return in %)
        # Data file must use English month names (Jan, Feb, etc.)
        df = pd.read_csv(DXY_HISTORY_PATH, decimal='.', sep=',') 
        
        if 'Month' not in df.columns or 'Return' not in df.columns:
            # Silence error for cleaner output, return None
            return None
        
        # Converts month names to index for correct plotting order
        month_to_index = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        df['Month_Index'] = df['Month'].map(month_to_index)
        
        if df['Month_Index'].isnull().any():
             # If mapping fails (e.g., if month names are still Czech), return None
             return None
             
        df = df.sort_values('Month_Index').reset_index(drop=True)
        return df
    except Exception as e:
        # Silent error to show mock chart
        return None


def score_event(row):
    a = clean_num(row.get("Actual"))
    f = clean_num(row.get("Forecast"))
    if a is None or f is None: return 0
    if a > f: return 1
    if a < f: return -1
    return 0

# LOGIC: Bullish >=+2, Neutral 1/0/-1, Bearish <=-2
def evaluate_category(df_cat):
    df_scored = df_cat[pd.to_numeric(df_cat['Points'], errors='coerce').notna()]
    total = int(df_scored["Points"].sum())
    
    if total >= 2: label = "Bullish"
    elif total <= -2: label = "Bearish"
    else: label = "Neutral" # Catches 1, 0, -1
    return total, label

# SHORT AI summary (approx 3-4 sentences)
def generate_ai_summary(summary_df, final_score, overall_label):
    
    # Use safe indexing
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

# --- FUNCTION FOR DATAFRAME STYLING (NO COLOR CODING) ---
def highlight_points_and_style_text(val):
    return ""

# --- HELPER FUNCTION FOR SEASONALITY (DXY MOCK DATA) ---
def generate_dxy_seasonality_data():
    # Simulated data of the average monthly return of the USD Index ($DXY)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Mock data for DXY (Strong Q1/Q4, Weak Q2/Q3)
    mock_returns = [0.8, 0.4, 0.6, -0.2, -0.4, -0.8, 
                    -0.6, -0.3, 0.2, 0.5, 0.9, 0.7]
    
    df = pd.DataFrame({
        "Month": months,
        "Return": mock_returns
    })
    
    # Adding index for correct plotting order
    month_to_index = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    df['Month_Index'] = df['Month'].map(month_to_index)
    return df.set_index('Month_Index').sort_values('Month_Index')
# -----------------------------------------------------

# Defines Pandas Styler for dark background and white text
dark_styler = [
    {'selector': 'th, td',
     'props': [('background-color', BG_BLACK), 
               ('color', TEXT_CREAM),
               ('border', f'1px solid {BORDER_DARK}'), # Use new dark line
               ('border-radius', '0')]},
    {'selector': 'table',
     'props': [('border-collapse', 'collapse')]}
]

# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. MAIN TITLE AND MOTTO (Section #0E1117)
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
# Small top title (Montserrat Light, Uppercase)
st.markdown("<p class='small-title'>USD MACRO AI DASHBOARD</p>", unsafe_allow_html=True) 
# Main title (Montserrat Light, Uppercase)
st.title("AURICAI AI")
# Motto (Libre Baskerville)
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
st.markdown("</div>", unsafe_allow_html=True) # End BLACK section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 3. FUNDAMENTAL NEWS BREAKDOWN BY CATEGORY (Section #FFFFFF)
# -------------------------
st.markdown("<div class='section-cream'>", unsafe_allow_html=True)
st.header("Fundamental News Breakdown by Category")

# Tables in Streamlit columns (smaller width)
cols = st.columns(2)

category_frames = {}
unique_categories = df_all_display["Category"].unique() 

for i, cat in enumerate(unique_categories):
    cat_df_display = df_all_display[df_all_display["Category"] == cat].copy()
    if cat_df_display.empty: continue 
    
    cat_df_scored = df_scored[df_scored["Category"] == cat].copy()
    category_frames[cat] = cat_df_scored

    cat_df_display = cat_df_display.sort_values("DateParsed", ascending=False)
    # Columns to display
    display_df = cat_df_display[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    )
    
    # *** KEY CHANGE: Use st.table with Pandas Styler (for reliable colors and index hiding) ***
    styled_df = display_df.style.set_table_styles(dark_styler).hide(axis="index")

    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.markdown(f'<div class="dark-table">', unsafe_allow_html=True)
            st.table(styled_df)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.markdown(f'<div class="dark-table">', unsafe_allow_html=True)
            st.table(styled_df)
            st.markdown('</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True) # End CREAM section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 4. FUNDAMENTAL EVALUATION AND AI ANALYSIS (Section #0E1117)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Fundamental Evaluation") # Changed to English

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

# *** KEY CHANGE: Use st.table with Pandas Styler (for reliable colors and index hiding) ***
styled_summary = summary_df.style.set_table_styles(dark_styler).hide(axis="index").format({"Total Points":"{:+d}"})

# Display summary table
st.markdown(f'<div class="dark-table">', unsafe_allow_html=True)
st.table(styled_summary) 
st.markdown('</div>', unsafe_allow_html=True)

# Highlight Total Score (no border, CENTERED)
st.markdown("<div class='center-div'>", unsafe_allow_html=True) # CENTERING PARENT
st.markdown(f"<div class='score-line-container'><span class='score-line'>Total Fundamental Score: {final_score:+d} — {final_label}</span></div>", unsafe_allow_html=True) # Changed to English
st.markdown("</div>", unsafe_allow_html=True)

# AI Assessment (white text, simplified text)
st.subheader("AI Fundamental Assessment") # Changed to English
ai_text_content = generate_ai_summary(summary_df, final_score, final_label)
st.info(ai_text_content)
st.markdown("</div>", unsafe_allow_html=True) # End BLACK section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 5. FUNDAMENTAL CATEGORIES CHART (Section #0E1117)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Fundamental Categories Chart") # Changed to English

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Points by Category Over Time (Daily Aggregate of Events)")
    
    # Plotly Fix: Use f-string for variable insertion
    fig.update_layout(
        plot_bgcolor=f"{BG_BLACK}", 
        paper_bgcolor=f"{BG_BLACK}",
        font_color=f"{TEXT_CREAM}",
        title_font_color=f"{TEXT_CREAM}",
        # Darker color for lines and axes
        xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data for the chart.") # Changed to English
st.markdown("</div>", unsafe_allow_html=True) # End BLACK section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer

# -------------------------
# 5.5 USD SEASONALITY CHART
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
# Changed name
st.header("U.S. Dollar Index Seasonality Chart") # Changed to English

df_seasonality = load_seasonality_data()
use_mock_data = False

if df_seasonality is None:
    # If file load fails or is missing, use mock data
    df_seasonality = generate_dxy_seasonality_data()
    use_mock_data = True
    st.info(f"Note: Could not load or process seasonality file. Displaying MOCK seasonality data. Please ensure '{DXY_HISTORY_PATH}' is correctly formatted (Month,Return) and contains English month names if file is used.") # Changed to English


y_column = "Return"

# Line Chart
fig_season = px.line(df_seasonality, 
                    x="Month", 
                    y=y_column,
                    title=f"Average Monthly Return",
                    labels={y_column: "Average Return (%)", "Month": "Month"},
                    markers=True, line_shape='linear') # Use line chart

# *** Adjustment: Set line color to light (TEXT_CREAM) ***
fig_season.update_traces(line=dict(color=TEXT_CREAM), marker=dict(color=TEXT_CREAM))

# Add zero line for clarity
fig_season.add_hline(y=0, line_dash="dash", line_color=BORDER_DARK)

fig_season.update_layout(
    plot_bgcolor=f"{BG_BLACK}", 
    paper_bgcolor=f"{BG_BLACK}",
    font_color=f"{TEXT_CREAM}",
    title_font_color=f"{TEXT_CREAM}",
    # Darker color for lines and axes
    xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
    yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK)
)
st.plotly_chart(fig_season, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # End BLACK section
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Spacer
    
# -------------------------
# 6. EXPORT / DOWNLOAD (Section #0E1117)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Export / Download") # Changed to English

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download Events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_manual.csv", "text/csv") # Changed to English
st.markdown("</div>", unsafe_allow_html=True) # End BLACK section