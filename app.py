# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# ZÁKLADNÍ CSS PRO CENTROVÁNÍ OBSAHU, FONT A TMVÉ TÉMA
# -------------------------
st.markdown("""
<style>
/* 1. Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Source+Sans+Pro:wght@400;700&display=swap');

/* Streamlit standardní tmavé téma je zachováno, ale přidáme centrování */
.stApp {
    padding-top: 20px;
    background-color: #0e1117; /* Standardní tmavé Streamlit pozadí */
    color: #FAFAFA;
}

/* 2. Stylování nadpisů (H1, H2, H3) - Oswald font */
h1, h2, h3, h4 {
    font-family: 'Oswald', sans-serif !important;
    text-align: center;
    color: #FAFAFA; /* Světlá barva pro kontrast */
}

/* 3. Stylování textu a motta - Source Sans Pro font */
body, p, div {
    font-family: 'Source Sans Pro', sans-serif;
}

/* Centrování hlavních prvků (titulku a motta) */
.st-emotion-cache-18j3dkg { /* Cílí na Streamlit nadřazený kontejner titulků */
    text-align: center;
    width: 100%;
}
.st-emotion-cache-1c9v511 { /* Cílí na nadpis H1 */
    width: 100%;
}

/* Zarovnání textu na střed pro motto a AI summary */
.stMarkdown {
    text-align: center;
}

/* Zarovnání tabulek a grafů na střed (vyžaduje úpravu layoutu) */
.stDataFrame, .stTable {
    margin-left: auto;
    margin-right: auto;
}

/* Oprava zarovnání pro st.subheader (standardní Streamlit zarovnání) */
section[data-testid="stSidebar"] + div h3 {
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")

# -------------------------
# KONFIGURACE DAT
# -------------------------
# Cesta k vašemu manuálně spravovanému souboru s příponou .txt
CSV_FILE_PATH = "usd_macro_history.csv.txt" 
LOOKBACK_DAYS = 90  # 3 měsíce pro filtrování zobrazení
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# KEYWORDS (pouze pro definici kategorií v tabulkách)
CATEGORY_KEYWORDS = {
    "Inflace": [], "Úrokové sazby": [], "Trh práce": [], "Ekonomická aktivita": []
}

# --- POMOCNÉ FUNKCE ---
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
        st.error(f"Chyba: Soubor s daty '{CSV_FILE_PATH}' nebyl nalezen. Vytvořte jej prosím dle šablony.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        required_cols = ['Date', 'Category', 'Actual', 'Forecast', 'Report']
        if not all(col in df.columns for col in required_cols):
             st.error(f"Chyba: V CSV chybí jeden z povinných sloupců: {required_cols}")
             return pd.DataFrame()

        df["DateParsed"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["DateParsed"].notna()]
        df = df[df["DateParsed"] >= pd.Timestamp(START_DATE)]
        return df.sort_values("DateParsed", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"Nepodařilo se načíst nebo zpracovat soubor CSV. Chyba: {e}")
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
    
    if total > 2: label = "Bullish"
    elif total < -2: label = "Bearish"
    else: label = "Neutral"
    return total, label

# AI shrnutí
def generate_ai_summary(summary_df, final_score, overall_label):
    summary = f"Celkové fundamentální skóre pro USD za poslední 3 měsíce (manuálně zadaná data) je **{final_score:+d}**, což vyúsťuje v **{overall_label}** sentiment. "
    
    summary_df_scored = summary_df[summary_df['Events Count'] > 0]
    
    if not summary_df_scored.empty:
        sorted_summary = summary_df_scored.sort_values("Total Points", ascending=False)
        best_cat = sorted_summary.iloc[0]
        if best_cat['Total Points'] > 0:
            summary += f"Nejsilnější pozitivní vliv na USD má kategorie **{best_cat['Category']}** s výsledkem **{best_cat['Total Points']:+d} bodů** ({best_cat['Events Count']} proběhlých událostí). "
        
        worst_cat = sorted_summary.iloc[-1]
        if worst_cat['Total Points'] < 0:
            summary += f"Negativně působí kategorie **{worst_cat['Category']}** se skóre **{worst_cat['Total Points']:+d} bodů** ({worst_cat['Events Count']} proběhlých událostí). "
    
    if overall_label == "Bullish pro USD":
        summary += "Fundamentální býčí sentiment je tažen silnými daty, která převážila mírně negativní zprávy. "
    elif overall_label == "Bearish pro USD":
        summary += "Celková medvědí nálada je způsobena kumulací slabších výsledků. "
    else: summary += "Celkový neutralní výsledek poukazuje na vyváženou situaci. "
    return summary

# Funkce pro stylování Pandas DataFrame (Nativní Streamlit styly)
def color_points_basic(val):
    val = pd.to_numeric(val, errors='coerce')
    if val > 0:
        return 'background-color: #38761d; color: white' 
    elif val < 0:
        return 'background-color: #cc0000; color: white'
    return 'background-color: #3d85c6; color: white'

# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. HLAVNÍ TITULEK A MOTTO
st.title("USD Macro AI Dashboard")
st.markdown("#### *BEAT THE ODDS*", unsafe_allow_html=True) 
st.markdown("---")

# 2. SKRYTÍ SEKCE Data fetch & processing (pouze načítání)
with st.spinner(f"Načítám data z lokálního souboru '{CSV_FILE_PATH}'..."):
    df_high = load_events_from_csv()

if df_high.empty:
    st.error("Nepodařilo se načíst žádná platná data. Zkontrolujte 'usd_macro_history.csv.txt'.")
    st.stop()

df_high["Points"] = df_high.apply(score_event, axis=1)
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

df_scored = df_high[pd.to_numeric(df_high['Actual'], errors='coerce').notna()].copy()
df_all_display = df_high.copy()

# -------------------------
# 3. ROZDĚLENÍ FUNDAMENTÁLNÍCH ZPRÁV DO KATEGORIÍ
# -------------------------
st.header("Rozdělení fundamentálních zpráv do kategorií")
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
    
    # Stylování (pro jednoduchost používáme applymap přímo v tabulce, ne v summary)
    styled_df = display_df.style.applymap(color_points_basic, subset=['Points'])
    
    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.dataframe(styled_df, use_container_width=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.dataframe(styled_df, use_container_width=True)

st.markdown("---")

# -------------------------
# 4. VYHODNOCENÍ FUNDAMENTU A AI ANALÝZA (KONZOLIDACE)
# -------------------------
st.header("Vyhodnocení fundamentu") # Přejmenováno

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

if final_score > 2: final_label = "Bullish pro USD"
elif final_score < -2: final_label = "Bearish pro USD"
else: final_label = "Neutral pro USD"

st.subheader("Category summary") # Přejmenováno na Category summary

# Zobrazení standardní, nestylované tabulky pro stabilitu
st.table(summary_df.style.format({"Total Points":"{:+d}"})) 

# KONZOLIDACE: Celkové skóre + AI Vyhodnocení v jednom bloku
# Používáme st.markdown pro zobrazení finálního výsledku s barvou
st.markdown(f"### Celkové fundamentální skóre: **{final_score:+d}** — **{final_label}**")
st.subheader("AI Fundamentální Vyhodnocení")
st.info(generate_ai_summary(summary_df, final_score, final_label).replace('**', ''))


st.markdown("---")

# -------------------------
# 5. GRAF FUNDAMENTÁLNÍCH KATEGORIÍ
# -------------------------
st.header("Graf fundamentálních kategorií") # Přejmenováno

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát z proběhlých událostí)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Není dost dat pro graf.")
    
# -------------------------
# 6. Export
# -------------------------
st.markdown("---")
st.header("Export / download")

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_manual.csv", "text/csv")