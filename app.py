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


/* *** KRITICKÉ: FIX PRO TABULKY (ČERNÉ POZADÍ / KRÉMOVÝ TEXT / OSTRÉ HRANY) *** */
/* Standardní tabulky Streamlit (st.table) - aplikujeme globální styl */

/* 1. EXTRÉMNÍ AGRESIVNÍ CÍLENÍ NA VŠECHNY ZNÁMÉ OBALY PRO ODSTRANĚNÍ ZAOUBLENÍ A STÍNŮ */
div[data-testid*="stTable"], 
div[data-testid*="stDataFrame"],
/* Cílení na všechny podřízené elementy s !important */
div[data-testid*="stTable"] *,
div[data-testid*="stDataFrame"] * {{
    border-radius: 0 !important;
    /* Odstranění stínů, které mohou způsobovat zatmavené rohy */
    box-shadow: none !important; 
}}

/* Cílení na hlavní Streamlit kontejnery, které mohou mít zaoblené rohy a stíny */
div[data-testid="stTable"] > div, 
div[data-testid="stDataFrame"] > div,
div[data-testid="stTable"] > div:first-child, 
div[data-testid="stDataFrame"] > div:first-child
{{
    border-radius: 0 !important;
    overflow: hidden; 
}}


/* 2. Cílení na samotné buňky a tělo tabulky */
div[data-testid="stTable"] table, div[data-testid="stDataFrame"] table {{
    width: 100% !important; 
    table-layout: auto; 
    border-collapse: collapse;
}}
div[data-testid="stTable"] table th, 
div[data-testid="stTable"] table td,
div[data-testid="stDataFrame"] table th,
div[data-testid="stDataFrame"] table td
{{
    background-color: {BG_BLACK} !important;
    color: {TEXT_CREAM} !important; 
    border: 1px solid {TEXT_CREAM};
    border-radius: 0 !important; /* Vynucení ostrých hran na buňkách */
}}

/* Zabrání zalamování textu v hlavičkách tabulek v kategoriích (oprava "Actua" a "l") */
div[data-testid="stTable"] table th {{
    white-space: nowrap !important;
}}


/* Centrování Celkového skóre (bez rámečku) */
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
    width: 100%; 
}}
/* Vynucuje centrování score-line-container */
.center-div {{
    display: flex;
    justify-content: center;
    width: 100%; 
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
    else: label = "Neutral" # Catches 1, 0, -1
    return total, label

# ZKRÁCENÉ AI shrnutí (cca 3-4 věty)
def generate_ai_summary(summary_df, final_score, overall_label):
    
    # Zde používáme bezpečné indexování, které funguje i pro DataFrame s jedním řádkem
    if not summary_df.empty:
        strongest = summary_df.sort_values('Total Points', ascending=False).iloc[0]
        weakest = summary_df.sort_values('Total Points', ascending=True).iloc[0]
    else:
        strongest = {'Category': 'N/A', 'Total Points': 0}
        weakest = {'Category': 'N/A', 'Total Points': 0}
    
    summary = f"Celkové fundamentální skóre pro USD za poslední 3 měsíce dosáhlo hodnoty {final_score:+d}, což signalizuje **{overall_label}** sentiment pro americký dolar. "
    
    if strongest['Total Points'] > 0:
        summary += f"Nejsilnější podporu poskytla kategorie **{strongest['Category']}** ({strongest['Total Points']:+d}), kde reporty konzistentně překonávaly očekávání. "
    
    if weakest['Total Points'] < 0:
        summary += f"Negativní tlak na dolar přichází ze sektoru **{weakest['Category']}** ({weakest['Total Points']:+d}). "
        
    summary += "Celkově se jedná o vyváženou situaci s jasnými silnými a slabými stránkami, které by měl investor sledovat."
    
    return summary

# --- FUNKCE PRO STYLOVÁNÍ DATAFRAMU (BEZ BAREVNÉHO ROZLIŠENÍ) ---
# Nyní zajišťuje pouze ostré hrany a vynucuje BG_BLACK/TEXT_CREAM na každé buňce.
def highlight_points_and_style_text(row):
    # Nový výchozí styl pro VŠECHNY buňky: Černé pozadí, Krémový text. 
    default_style = f'background-color: {BG_BLACK}; color: {TEXT_CREAM}; border: 1px solid {TEXT_CREAM}; border-radius: 0 !important;'
    styles = [default_style] * len(row)
    
    # Vynutíme stejný styl i pro sloupec Points
    if 'Points' in row.index:
        idx = row.index.get_loc('Points')
        styles[idx] = default_style
    
    return styles


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

# Zde jsou tabulky v Streamlit sloupcích (menší šířka)
cols = st.columns(2)

category_frames = {}
unique_categories = df_all_display["Category"].unique() 

for i, cat in enumerate(unique_categories):
    cat_df_display = df_all_display[df_all_display["Category"] == cat].copy()
    if cat_df_display.empty: continue 
    
    cat_df_scored = df_scored[df_scored["Category"] == cat].copy()
    category_frames[cat] = cat_df_scored

    cat_df_display = cat_df_display.sort_values("DateParsed", ascending=False)
    # Zobrazované sloupce
    display_df = cat_df_display[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    )
    
    # Aplikace OPRAVENÉHO STYLU (nyní bez barevného rozlišení bodů)
    styled_df = display_df.style.apply(highlight_points_and_style_text, axis=1)

    if i % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.table(styled_df)
    else:
        with cols[1]:
            st.subheader(cat)
            st.table(styled_df)
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

if final_score >= 2: final_label = "BULLISH"
elif final_score <= -2: final_label = "BEARISH"
else: final_label = "NEUTRAL"

# Zobrazení souhrnné tabulky (Bez jakéhokoliv barevného rozlišení)
styled_summary = summary_df.style.format({"Total Points":"{:+d}"})

st.table(styled_summary) 

# Podtržení Celkového skóre (bez rámečku, CENTROVÁNO)
st.markdown("<div class='center-div'>", unsafe_allow_html=True) # CENTROVÁNÍ RODIČ
st.markdown(f"<div class='score-line-container'><span class='score-line'>Celkové fundamentální skóre: {final_score:+d} — {final_label}</span></div>", unsafe_allow_html=True)
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