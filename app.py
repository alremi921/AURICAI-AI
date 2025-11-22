# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")

# -------------------------
# VLOŽENÍ VLASTNÍHO FUTURISTICKÉHO CSS
# -------------------------
# Primární barvy: Černá/Navy pozadí, Pink (#FF00FF), Baby Blue (#89CFF0)
custom_css = """
<style>
/* 1. Celkové pozadí a písmo (Dark Theme Override) */
.stApp {
    background-color: #0d0d0d; /* Velmi tmavé pozadí */
    color: #e0e0e0;
}
/* 2. Stylování titulků a akcentů */
h1 {
    color: #FF00FF; /* Růžová pro hlavní titulek */
    text-shadow: 0 0 5px #FF00FF, 0 0 10px #FF00FF; /* Světelný efekt */
    font-size: 2.5em;
    font-weight: 700;
}
h2, h3 {
    color: #89CFF0; /* Baby Blue pro podtitulky */
    border-bottom: 2px solid #333344;
    padding-bottom: 5px;
    margin-top: 20px;
}
/* 3. Streamlit kontejnery a karty */
.stAlert.info, .stDataFrame, .stTable, .stPlotlyChart {
    background-color: #1a1a1a; /* Tmavě šedé pozadí pro karty */
    border-radius: 8px;
    padding: 10px;
    border: 1px solid #333344; /* Jemný rámeček */
}
/* 4. Tlačítka pro download */
.stDownloadButton button {
    background-color: #89CFF0;
    color: #000000;
    border-radius: 15px;
    font-weight: bold;
    border: 2px solid #000000;
}
/* 5. Infobox (AI Vyhodnocení) - Konzolidovaný blok */
.ai-summary-block {
    padding: 15px; 
    border-radius: 8px; 
    background-color: #1a1a1a; 
    margin-top: 20px;
    border: 2px solid #FF00FF; /* Růžový akcent */
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


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

# Funkce pro stylování Pandas DataFrame (futuristické barvy pro body)
def color_points(val):
    val = pd.to_numeric(val, errors='coerce')
    if val > 0:
        color = 'background-color: #203020; color: #00FF00' # Zelená záře
    elif val < 0:
        color = 'background-color: #302020; color: #FF0000' # Červená záře
    else:
        color = 'background-color: #202030; color: #89CFF0' # Modrá záře
    return color

# Funkce pro barvu celkového labelu
def color_score_label(label):
    if 'Bullish' in label: return '#00FF00' 
    if 'Bearish' in label: return '#FF0000'
    return '#89CFF0'

# -------------------------
# BUILD DASHBOARD
# -------------------------

# 1. HLAVNÍ TITULEK A MOTTO
st.title("USD Macro AI Dashboard")
st.markdown("#### *BEAT THE ODDS*", unsafe_allow_html=True) # ZMĚNĚNO MOTTO
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
    
    styled_df = display_df.style.applymap(color_points, subset=['Points'])
    
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

st.subheader("Category summary")
# Tabulka s hodnocením jednotlivých kategorií
styled_summary = summary_df.style.applymap(
    lambda x: color_score_label(x) if x in ["Bullish", "Bearish", "Neutral"] else '', 
    subset=['Evaluation']
).format({"Total Points":"{:+d}"})

st.table(styled_summary)

# KONZOLIDACE: Celkové skóre + AI Vyhodnocení v jednom bloku
st.markdown(f"""
    <div class="ai-summary-block">
        <h3 style="margin-bottom: 5px; color: #FF00FF; border-bottom: none;">
            Celkové fundamentální skóre: 
            <span style="font-size: 1.5em; font-weight: bold; color: {color_score_label(final_label)}; text-shadow: 0 0 8px {color_score_label(final_label)};">{final_score:+d}</span> 
            — <span style="font-weight: bold; color: {color_score_label(final_label)};">{final_label}</span>
        </h3>
        
        <p style="color: #89CFF0; font-weight: bold; margin-top: 20px; font-size: 1.1em;">
            AI Fundamentální Vyhodnocení:
        </p>
        <div style="color: #e0e0e0; margin-top: 5px;">
            {generate_ai_summary(summary_df, final_score, final_label).replace('**', '')}
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# 5. GRAF FUNDAMENTÁLNÍCH KATEGORIÍ
# -------------------------
st.header("Graf fundamentálních kategorií")

viz_df = df_scored.copy() # Graf zobrazuje pouze proběhlé události
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát z proběhlých událostí)")
    
    # Úprava grafu pro tmavý/futuristický design
    fig.update_layout(
        plot_bgcolor='#1a1a1a', 
        paper_bgcolor='#1a1a1a', 
        font_color='#e0e0e0',
        title_font_color='#89CFF0',
        legend_title_font_color='#FF00FF'
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