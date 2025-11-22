# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# DEFINICE BAREV A CEST
# -------------------------
BG_BLACK = '#0C0C0C' # Washed Black
BG_CREAM = '#F2EEDB' # Krémová
TEXT_CREAM = '#F2EEDB'
TEXT_BLACK = '#0C0C0C'

CSV_FILE_PATH = "usd_macro_history.csv.txt" 
LOOKBACK_DAYS = 90  
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

CATEGORY_KEYWORDS = {
    "Inflace": [], "Úrokové sazby": [], "Trh práce": [], "Ekonomická aktivita": []
}

# -------------------------
# ZÁKLADNÍ CSS PRO STABILITU A DESIGN
# -------------------------
st.markdown(f"""
<style>
/* 1. Import Google Fonts (Pro spolehlivé náhrady) */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@300;400;700&display=swap');

/* 2. Streamlit celkové nastavení */
.stApp {{
    padding-top: 20px;
    background-color: {BG_BLACK}; 
    color: {TEXT_CREAM};
}}

/* 3. Stylování nadpisů (Montserrat Light, Uppercase) */
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

/* 4. Stylování textu a motta */
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

/* Nastavení barvy textu v krémových sekcích */
.section-cream p, .section-cream div, .section-cream label {{
    color: {TEXT_BLACK}; 
}}

/* *** KRITICKÁ OPRAVA: AI BOX (st.info) - ZRUŠIT MODROU VÝPLŇ *** */
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


/* ZAJIŠTĚNÍ ČITELNOSTI TEXTU V TABULKÁCH (vše krémové, ale text černý) */
.stTable table thead th, .stTable table tbody td {{
    background-color: {BG_CREAM} !important;
    color: {TEXT_BLACK} !important; /* ZMĚNA: PRIORITA PRO ČITELNÝ TEXT */
    border: 1px solid {TEXT_BLACK}; 
    border-radius: 0px !important;
}}
/* Nastavení pozadí celého tabulkového kontejneru na krémovou */
.stTable table {{
    background-color: {BG_CREAM} !important;
}}

/* Centrování Celkového skóre s RÁMEČKEM */
.score-line-container {{
    padding: 15px;
    border: 1px solid {TEXT_CREAM}; 
    display: inline-block; 
    margin: 20px auto 30px auto; 
    text-align: center;
}}
.score-line {{
    font-size: 1.5em;
    font-weight: 400; 
    display: block; 
    color: {TEXT_CREAM}; 
}}

/* --- BAREVNÉ SEKCE (Střídavé Pozadí) --- */
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

/* Přidání mezer mezi sekce */
.section-spacer {{
    height: 30px; 
}}

/* ZAJIŠTĚNÍ CENTROVÁNÍ VŠECH PRVKŮ VE ST.TABLE A ST.DATAFRAME A SKÓRE */
div[data-testid="stTable"], div[data-testid="stDataFrame"] {{
    display: flex;
    justify-content: center;
}}
.center-div {{
    display: flex;
    justify-content: center;
    width: 100%; /* Zajištění, že se kontejner roztáhne */
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

# ZKRÁCENÉ AI shrnutí (cca 3-4 věty)
def generate_ai_summary(summary_df, final_score, overall_label):
    
    strongest = summary_df.sort_values('Total Points', ascending=False).iloc[0]
    weakest = summary_df.sort_values('Total Points', ascending=True).iloc[0]
    
    summary = f"Celkové fundamentální skóre pro USD za poslední 3 měsíce dosáhlo hodnoty {final_score:+d}, což signalizuje **{overall_label}** sentiment pro americký dolar. "
    
    if strongest['Total Points'] > 0:
        summary += f"Nejsilnější podporu poskytla kategorie **{strongest['Category']}** ({strongest['Total Points']:+d}), kde reporty konzistentně překonávaly očekávání. "
    
    if weakest['Total Points'] < 0:
        summary += f"Negativní tlak na dolar přichází ze sektoru **{weakest['Category']}** ({weakest['Total Points']:+d}). "
        
    summary += "Celkově se jedná o vyváženou situaci s jasnými silnými a slabými stránkami, které by měl investor sledovat."
    
    return summary

# Funkce pro stylování Pandas DataFrame
def color_points_basic(val):
    val = pd.to_numeric(val, errors='coerce')
    # Ostré krémové buňky
    style = f'background-color: {BG_CREAM}; color: {TEXT_BLACK}; border: 1px solid {TEXT_BLACK};' 
    if val > 0:
        style = 'background-color: #38761d; color: white; border: 1px solid #38761d;' 
    elif val < 0:
        style = 'background-color: #cc0000; color: white; border: 1px solid #cc0000;'
    return style

# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. HLAVNÍ TITULEK A MOTTO (Sekce #0C0C0C)
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
# Malý horní nadpis (Montserrat Light, Uppercase)
st.markdown("<p class='small-title'>USD MACRO AI DASHBOARD</p>", unsafe_allow_html=True) 
# Hlavní nadpis (Montserrat Light, Uppercase)
st.title("AURICAI AI")
# Motto (Libre Baskerville)
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
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Mezera

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
    
    # Používáme st.table s Pandas Styler pro zachování barevnosti
    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.table(display_df.style.applymap(color_points_basic, subset=['Points']))
    else:
        with cols[1]:
            st.subheader(cat)
            st.table(display_df.style.applymap(color_points_basic, subset=['Points']))
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce CREAM
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Mezera

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

# Zobrazení standardní tabulky (Vyhodnocení fundamentu - bude krémová)
st.table(summary_df.style.format({"Total Points":"{:+d}"})) 

# Podtržení Celkového skóre (v Black sekci, text je CREAM)
st.markdown("<div class='center-div'>", unsafe_allow_html=True) # CENTROVÁNÍ RODIČ
st.markdown(f"<div class='score-line-container'><span class='score-line'>Celkové fundamentální skóre: **{final_score:+d}** — **{final_label}**</span></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# AI Vyhodnocení (bílý text, obrys modrého čtverce, zjednodušený text)
st.subheader("AI Fundamentální Vyhodnocení")
ai_text_content = generate_ai_summary(summary_df, final_score, final_label)
st.info(ai_text_content)
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Mezera

# -------------------------
# 5. GRAF FUNDAMENTÁLNÍCH KATEGORIÍ (Sekce #0C0C0C)
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
st.header("Graf fundamentálních kategorií") 

viz_df = df_scored.copy() 
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát z proběhlých událostí)")
    
    # Oprava Plotly: Používáme F-string pro vkládání proměnných
    fig.update_layout(
        plot_bgcolor=f"{BG_BLACK}", 
        paper_bgcolor=f"{BG_BLACK}",
        font_color=f"{TEXT_CREAM}",
        title_font_color=f"{TEXT_CREAM}"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Není dost dat pro graf.")
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Mezera
    
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