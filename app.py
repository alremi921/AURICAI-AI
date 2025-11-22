# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# Definice barev pro snadné použití
BG_BLACK = '#0C0C0C'
BG_CREAM = '#F2EEDB'
TEXT_CREAM = '#F2EEDB'
TEXT_BLACK = '#0C0C0C'

# -------------------------
# ZÁKLADNÍ CSS PRO CENTROVÁNÍ OBSAHU, FONT A TMVÉ TÉMA (Old Money Style)
# -------------------------
st.markdown(f"""
<style>
/* 1. Import Google Fonts (Fallback a Montserrat) */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400&display=swap');

/* Definice custom fontů (Zajištění stability: používáme Montserrat fallback) */
@font-face {{
    font-family: 'The Seasons';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Regular.ttf') format('truetype');
    font-weight: 400;
}}
@font-face {{
    font-family: 'Beautifully Delicious Light';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Light.ttf') format('truetype');
    font-weight: 300;
}}


/* 2. Streamlit celkové nastavení */
.stApp {{
    padding-top: 20px;
    background-color: {BG_BLACK}; /* Washed Black pozadí */
    color: {TEXT_CREAM};
}}

/* 3. Stylování nadpisů */
/* Hlavní nadpis H1: The Seasons (Regular) */
h1 {{
    font-family: 'The Seasons', 'Montserrat', sans-serif !important; 
    text-align: center;
    color: {TEXT_CREAM};
    font-weight: 400;
    letter-spacing: 2px;
}}

/* Ostatní nadpisy H2, H3: Beautifully Delicious Light */
h2, h3, h4 {{
    font-family: 'Beautifully Delicious Light', 'Montserrat', sans-serif !important; 
    text-align: center;
    font-weight: 300; 
    margin-bottom: 20px; /* Větší mezera pod nadpisy */
}}

/* 4. Stylování textu a motta */
p, div, label {{
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300; 
}}
.stMarkdown {{
    text-align: center;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300;
}}
/* Motto - Montserrat Light, Velká písmena */
.motto {{
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300; 
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: -10px;
    font-size: 1.1em;
}}

/* ZMĚNA: Stylování Tabulek */
.stDataFrame, .stTable {{
    margin-left: auto;
    margin-right: auto;
    border-radius: 0px !important; /* Ostré rohy */
}}
/* Cílení na hlavičky a buňky tabulek pro krémovou barvu */
.stDataFrame table thead th, .stDataFrame table tbody td {{
    background-color: {BG_CREAM} !important;
    color: {TEXT_BLACK} !important;
    border: 1px solid {TEXT_BLACK}; /* Čisté ostré rozdělení */
}}
/* Cílení na nadřazený kontejner tabulky (pro pozadí celého DataFrame) */
div[data-testid="stTable"] {{
    background-color: {BG_BLACK} !important; /* Pokud se nepodaří stylovat vnitřní buňky */
}}

/* Úprava AI boxu: transparentní pozadí, bílý text, modrý obrys */
div[data-testid="stAlert"] {{
    background-color: transparent !important; 
    border: 1px solid #4A4A99 !important; 
    color: {TEXT_CREAM} !important; 
    padding: 20px;
    margin-top: 10px;
}}
/* Centrování Celkového skóre */
.score-line {{
    border-bottom: 1px solid {TEXT_CREAM};
    padding-bottom: 5px;
    display: block; /* Změna na block pro plnou šířku a centrování */
    text-align: center;
    font-size: 1.5em;
    font-weight: 400; 
    margin-bottom: 30px; /* Více místa pod skóre */
    margin-top: 20px; /* Více místa nad skóre */
}}

/* --- BAREVNÉ SEKCE --- */
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
.section-cream .stDataFrame table thead th, .section-cream .stDataFrame table tbody td {{
    background-color: {BG_CREAM} !important;
    color: {TEXT_BLACK} !important;
}}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")

# -------------------------
# KONFIGURACE DAT
# -------------------------
CSV_FILE_PATH = "usd_macro_history.csv.txt" 
LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

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

# LOGIKA: Bullish >=+2, Neutral 1/0/-1, Bearish <=-2
def evaluate_category(df_cat):
    df_scored = df_cat[pd.to_numeric(df_cat['Points'], errors='coerce').notna()]
    total = int(df_scored["Points"].sum())
    
    if total >= 2: label = "Bullish"
    elif total <= -2: label = "Bearish"
    else: label = "Neutral"
    return total, label

# ZJEDNODUŠENÉ AI shrnutí (Původní verze bez detailního rozboru)
def generate_ai_summary(summary_df, final_score, overall_label):
    summary = f"Celkové fundamentální skóre pro USD za poslední 3 měsíce dosáhlo hodnoty {final_score:+d}, což signalizuje {overall_label} sentiment. Analýza kategorií ukazuje, že hlavní vliv mají sektory s nejvyšším bodovým ziskem, zatímco negativní tlaky pocházejí ze slabších reportů."
    return summary

# Funkce pro stylování Pandas DataFrame
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

# 1. HLAVNÍ TITULEK A MOTTO (Sekce #0C0C0C)
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.title("USD Macro AI Dashboard")
st.markdown("<p class='motto'>BEAT THE ODDS</p>", unsafe_allow_html=True) 
st.markdown("---")

# Načítání dat
with st.spinner(f"Načítám data z lokálního souboru '{CSV_FILE_PATH}'..."):
    df_high = load_events_from_csv()

if df_high.empty:
    st.error("Nepodařilo se načíst žádná platná data. Zkontrolujte 'usd_macro_history.csv.txt'.")
    st.stop()

df_high["Points"] = df_high.apply(score_event, axis=1)
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

df_scored = df_high[pd.to_numeric(df_high['Actual'], errors='coerce').notna()].copy()
df_all_display = df_high.copy()
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK

# -------------------------
# 3. ROZDĚLENÍ FUNDAMENTÁLNÍCH ZPRÁV DO KATEGORIÍ (Sekce #F2EEDB)
# -------------------------
st.markdown("<div class='section-cream'>", unsafe_allow_html=True)
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
    
    styled_df = display_df.style.applymap(color_points_basic, subset=['Points'])
    
    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.dataframe(styled_df, use_container_width=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.dataframe(styled_df, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce CREAM

# -------------------------
# 4. VYHODNOCENÍ FUNDAMENTU A AI ANALÝZA (Sekce #0C0C0C)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Vyhodnocení fundamentu") 

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

if final_score >= 2: final_label = "Bullish pro USD"
elif final_score <= -2: final_label = "Bearish pro USD"
else: final_label = "Neutral pro USD"

# Zobrazení standardní tabulky (bez "Category summary")
st.table(summary_df.style.format({"Total Points":"{:+d}"})) 

# Podtržení Celkového skóre (v Black sekci, text je CREAM)
st.markdown(f"<div class='score-line' style='color:{TEXT_CREAM};'>Celkové fundamentální skóre: **{final_score:+d}** — **{final_label}**</div>", unsafe_allow_html=True)

# AI Vyhodnocení (bílý text, obrys modrého čtverce, zjednodušený text)
st.subheader("AI Fundamentální Vyhodnocení")
ai_text_content = generate_ai_summary(summary_df, final_score, final_label)
st.info(ai_text_content)
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK

# -------------------------
# 5. GRAF FUNDAMENTÁLNÍCH KATEGORIÍ (Sekce #F2EEDB)
# -------------------------
st.markdown("<div class='section-cream'>", unsafe_allow_html=True)
st.header("Graf fundamentálních kategorií") 

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát z proběhlých událostí)")
    
    # Úprava grafu pro CREAM pozadí sekce, ale plot musí být čitelný
    fig.update_layout(
        plot_bgcolor='#eeeeee', 
        paper_bgcolor={BG_CREAM},
        font_color={TEXT_BLACK},
        title_font_color={TEXT_BLACK}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Není dost dat pro graf.")
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce CREAM
    
# -------------------------
# 6. Export (Sekce #0C0C0C)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Export / download")

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_manual.csv", "text/csv")
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK