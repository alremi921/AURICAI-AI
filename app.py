# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# ZÁKLADNÍ CSS PRO CENTROVÁNÍ OBSAHU, FONT A TMVÉ TÉMA (Old Money Style)
# -------------------------
st.markdown("""
<style>
/* 1. Import Google Fonts (Fallback a Montserrat) */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400&display=swap');

/* Definice custom fontů (Zajištění stability: používáme fallback) */
@font-face {
    font-family: 'The Seasons';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Regular.ttf') format('truetype'); /* Použijeme stabilní Montserrat Regular jako placeholder/fallback */
    font-weight: 400;
}
@font-face {
    font-family: 'Beautifully Delicious Light';
    src: url('https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Light.ttf') format('truetype'); /* Použijeme stabilní Montserrat Light jako placeholder/fallback */
    font-weight: 300;
}


/* 2. Streamlit celkové nastavení */
.stApp {
    padding-top: 20px;
    background-color: #0C0C0C; /* Washed Black pozadí (0C0C0C) */
    color: #FAFAFA;
}

/* 3. Stylování nadpisů */
/* Hlavní nadpis H1: The Seasons (Regular) */
h1 {
    font-family: 'The Seasons', 'Montserrat', sans-serif !important; 
    text-align: center;
    color: #FAFAFA;
    font-weight: 400; /* Regular/Semi-bold */
    letter-spacing: 2px;
}

/* Ostatní nadpisy H2, H3: Beautifully Delicious Light */
h2, h3, h4 {
    font-family: 'Beautifully Delicious Light', 'Montserrat', sans-serif !important; 
    text-align: center;
    color: #FAFAFA;
    font-weight: 300; /* Light */
}

/* Nadpis pro tabulky (Trh práce, Inflace atd.) */
h3 {
    font-family: 'Beautifully Delicious Light', 'Montserrat', sans-serif !important; 
}


/* 4. Stylování textu a motta */
p, div, label, .stMarkdown {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300; /* Light */
    text-align: center;
}
/* Motto - Montserrat Light, Velká písmena */
.motto {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 300; 
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: -10px; /* Přiblížení k hlavnímu nadpisu */
    font-size: 1.1em;
}

/* 5. Stylování tabulek a boxů (Ostré rohy, Washed Black pozadí) */
.stDataFrame, .stTable {
    margin-left: auto;
    margin-right: auto;
    background-color: #1a1a1a;
    border-radius: 0px; /* Ostré rohy */
    border: 1px solid #333333;
}

/* Úprava AI boxu: odstraňujeme modré pozadí, ponecháváme bílý text a obrys */
div[data-testid="stAlert"] {
    background-color: transparent !important; /* Průhledné pozadí */
    border: 1px solid #4A4A99 !important; /* Jemný modrý obrys */
    color: #FAFAFA !important; /* Bílý text */
}

/* Podtržení Celkového skóre */
.score-line {
    border-bottom: 1px solid #666666;
    padding-bottom: 5px;
    display: inline-block;
    font-size: 1.5em;
    font-weight: 400; /* Regular */
    margin-bottom: 15px;
}

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

# ZMĚNA LOGIKY: Bullish >+2, Neutral 1/0/-1, Bearish <-2
def evaluate_category(df_cat):
    df_scored = df_cat[pd.to_numeric(df_cat['Points'], errors='coerce').notna()]
    total = int(df_scored["Points"].sum())
    
    if total >= 2: label = "Bullish"
    elif total <= -2: label = "Bearish"
    else: label = "Neutral" # Pokrývá 1, 0, -1
    return total, label

# ZMĚNA AI shrnutí - detailnější rozbor
def generate_ai_summary(summary_df, final_score, overall_label, category_frames):
    summary = []
    
    # 1. Úvodní shrnutí
    summary.append(f"Celkové fundamentální skóre pro USD za poslední 3 měsíce (manuálně zadaná data) dosáhlo hodnoty **{final_score:+d}**, což signalizuje **{overall_label}** sentiment.")
    
    # 2. Detailní rozbor kategorií
    for cat, df_cat_scored in category_frames.items():
        total, label = evaluate_category(df_cat_scored)
        count = len(df_cat_scored)
        
        if count > 0:
            if label == "Bullish":
                summary.append(f"**{cat}**: Tato kategorie ({count} zpráv) vykazuje silně **{label}** skóre **({total:+d} bodů)**. Většina reportů v této oblasti překonala tržní očekávání, což poskytuje USD silný býčí fundamentální impuls.")
            elif label == "Bearish":
                summary.append(f"**{cat}**: Zde ({count} zpráv) dominuje **{label}** sentiment s **({total:+d} bodů)**. Data zaostala za konsenzem, což působí jako hlavní fundamentální tlak proti USD.")
            else:
                summary.append(f"**{cat}**: Tato kategorie ({count} zpráv) je **{label}** ({total:+d} bodů). Pozitivní a negativní zprávy se vzájemně vyrovnaly, což ukazuje na vyvážený výhled v tomto sektoru ekonomiky.")
        else:
            summary.append(f"**{cat}**: V této kategorii nebyly v daném období nalezeny žádné proběhlé High-Impact události pro scoring.")

    # 3. Závěr
    if overall_label == "Bullish pro USD":
        summary.append("Celkový býčí sentiment je tažen zejména silnými daty z klíčových oblastí, které převážily mírně negativní zprávy. Toto silné fundamentální podhoubí naznačuje potenciál pro další posilování dolaru.")
    elif overall_label == "Bearish pro USD":
        summary.append("Celková medvědí nálada je způsobena kumulací slabších výsledků napříč hlavními sektory. Tento fundamentální tlak může signalizovat překážky pro Fed nebo ekonomiku jako celek, což by mohlo vést k oslabení USD.")
    else:
        summary.append("Celkový neutralní výsledek poukazuje na vyváženou situaci, kdy se pozitivní a negativní fundamenty navzájem vyrušily. Trh tak nemá jasný fundamentální směr z makrodat.")

    return "\n\n".join(summary).replace('**', '')

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
st.markdown("<p class='motto'>BEAT THE ODDS</p>", unsafe_allow_html=True) 
st.markdown("---")

# 2. SKRYTÍ SEKCE Data fetch & processing (pouze načítání)
with st.spinner(f"Načítám data z lokálního souboru '{CSV_FILE_PATH}'..."):
    df_high = load_events_from_csv()

if df_high.empty:
    st.error("Nepodařilo se načíst žádná platná data. Zkontrolujte 'usd_macro_history.csv.txt'.")
    st.stop()

df_high["Points"] = df_high.apply(score_event, axis=1)
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

# Filtrace: pouze události s Actual hodnotou (proběhlé)
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
    
    # Stylování bodů
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
st.header("Vyhodnocení fundamentu") 

summary_rows = []
total_combined_score = 0

for cat, df_cat in category_frames.items():
    # Používáme novou logiku evaluate_category
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

# Aplikujeme novou logiku bodování na finální skóre
if final_score >= 2: final_label = "Bullish pro USD"
elif final_score <= -2: final_label = "Bearish pro USD"
else: final_label = "Neutral pro USD"

# Odstranění "Category summary" - zobrazujeme pouze data
# Zobrazení standardní tabulky pro stabilitu
st.table(summary_df.style.format({"Total Points":"{:+d}"})) 

# KONZOLIDACE: Celkové skóre + AI Vyhodnocení v jednom bloku
# Podtržení Celkového skóre (pomocí CSS třídy score-line)
st.markdown(f"<div class='score-line'>Celkové fundamentální skóre: **{final_score:+d}** — **{final_label}**</div>", unsafe_allow_html=True)

# AI Vyhodnocení (bílý text, obrys modrého čtverce, delší text)
ai_text_content = generate_ai_summary(summary_df, final_score, final_label, category_frames)
st.subheader("AI Fundamentální Vyhodnocení")

# Použití st.info s upraveným CSS pro stylizovaný box
st.info(ai_text_content)


st.markdown("---")

# -------------------------
# 5. GRAF FUNDAMENTÁLNÍCH KATEGORIÍ
# -------------------------
st.header("Graf fundamentálních kategorií") 

# GRAF: Používá df_scored pro zobrazení pouze proběhlých událostí
viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát z proběhlých událostí)")
    
    # Úprava grafu pro tmavé pozadí a lepší čitelnost
    fig.update_layout(
        plot_bgcolor='#1a1a1a', 
        paper_bgcolor='#1a1a1a', 
        font_color='#FAFAFA'
    )
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