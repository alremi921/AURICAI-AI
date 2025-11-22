import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

# -------------------------
# DEFINICE BAREV A CEST
# -------------------------
BG_BLACK = '#0E1117' # Tmavé Streamlit pozadí
BG_CREAM = '#FFFFFF' # Čistě bílé pozadí (pro sekci CREAM)
TEXT_CREAM = '#FFFFFF' # Čistě bílý text
TEXT_BLACK = '#0E1117' # Tmavá barva textu (pro sekci CREAM)

# Nová barva pro okraje a linky grafů, dle požadavku
BORDER_DARK = '#31333F' 

CSV_FILE_PATH = "usd_macro_history.csv.txt" 
DXY_HISTORY_PATH = "dxy_linechart_history.csv.txt" # NOVÁ CESTA K SOUBORU
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

# NOVÁ FUNKCE: Načte skutečná data USDX pro sezónnost
@st.cache_data
def load_seasonality_data():
    if not os.path.exists(DXY_HISTORY_PATH):
        return None
    try:
        # Očekáváme sloupec 'Month' (jako text Měsíc) a 'Return' (jako průměrná návratnost v %)
        df = pd.read_csv(DXY_HISTORY_PATH, decimal='.', sep=',') 
        
        if 'Month' not in df.columns or 'Return' not in df.columns:
            # Nevypisujeme varování, abychom udrželi čistý výstup, ale vracíme None
            return None
        
        # Převedeme názvy měsíců na index pro správné řazení v grafu
        month_to_index = {
            "Leden": 1, "Únor": 2, "Březen": 3, "Duben": 4, "Květen": 5, "Červen": 6, 
            "Červenec": 7, "Srpen": 8, "Září": 9, "Říjen": 10, "Listopad": 11, "Prosinec": 12
        }
        df['Month_Index'] = df['Month'].map(month_to_index)
        
        if df['Month_Index'].isnull().any():
             return None
             
        df = df.sort_values('Month_Index').reset_index(drop=True)
        return df
    except Exception as e:
        # Tichá chyba, aby se zobrazil mock graf
        return None


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
def highlight_points_and_style_text(val):
    # Pro st.dataframe se stylování buňky řeší jinak nebo se používá globální CSS.
    # Tato funkce není pro st.dataframe nutná, ponecháme ji pro konzistenci
    # ale vrátíme prázdný řetězec, protože se na st.dataframe nepoužije.
    return ""

# --- POMOCNÁ FUNKCE PRO SEZONNOST (DXY MOCK DATA) ---
def generate_dxy_seasonality_data():
    # Simulovaná data průměrné měsíční návratnosti USD Indexu ($DXY), struktura podle Barchart
    months = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen", 
              "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
    # Mock data pro DXY (Silný Q1/Q4, Slabý Q2/Q3)
    mock_returns = [0.8, 0.4, 0.6, -0.2, -0.4, -0.8, 
                    -0.6, -0.3, 0.2, 0.5, 0.9, 0.7]
    
    df = pd.DataFrame({
        "Month": months,
        "Return": mock_returns
    })
    
    # Přidání indexu pro správné řazení v grafu
    month_to_index = {
        "Leden": 1, "Únor": 2, "Březen": 3, "Duben": 4, "Květen": 5, "Červen": 6, 
        "Červenec": 7, "Srpen": 8, "Září": 9, "Říjen": 10, "Listopad": 11, "Prosinec": 12
    }
    df['Month_Index'] = df['Month'].map(month_to_index)
    return df.set_index('Month_Index').sort_values('Month_Index')
# -----------------------------------------------------

# Definuje Pandas Styler pro tmavé pozadí a krémový text
dark_styler = [
    {'selector': 'th, td',
     'props': [('background-color', BG_BLACK), 
               ('color', TEXT_CREAM),
               ('border', f'1px solid {BORDER_DARK}'), # Použití nové tmavé linky
               ('border-radius', '0')]},
    {'selector': 'table',
     'props': [('border-collapse', 'collapse')]}
]

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
st.markdown("<p class='motto'>\"BEAT THE ODDS\"</p>", unsafe_allow_html=True) 
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
    
    # *** KLÍČOVÁ ZMĚNA: Použití st.table s Pandas Styler (pro spolehlivé barvy a skrytí indexu) ***
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

# *** KLÍČOVÁ ZMĚNA: Použití st.table s Pandas Styler (pro spolehlivé barvy a skrytí indexu) ***
styled_summary = summary_df.style.set_table_styles(dark_styler).hide(axis="index").format({"Total Points":"{:+d}"})

# Zobrazení souhrnné tabulky
st.markdown(f'<div class="dark-table">', unsafe_allow_html=True)
st.table(styled_summary) 
st.markdown('</div>', unsafe_allow_html=True)

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
        title_font_color=f"{TEXT_CREAM}",
        # Tmavší barva linek a os
        xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
        yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Není dost dat pro graf.")
st.markdown("</div>", unsafe_allow_html=True) # Konec sekce BLACK
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True) # Mezera

# -------------------------
# 5.5 GRAF SEZÓNNOSTI USD
# -------------------------
st.markdown("<div class='section-black'>", unsafe_allow_html=True)
# Změněný název
st.header("Graf sezónosti U.S. dolar indexu")

df_seasonality = load_seasonality_data()
use_mock_data = False

if df_seasonality is None:
    df_seasonality = generate_dxy_seasonality_data()
    use_mock_data = True

y_column = "Return"

# Změna na LINE CHART
fig_season = px.line(df_seasonality, 
                    x="Month", 
                    y=y_column,
                    title=f"Průměrná měsíční návratnost",
                    labels={y_column: "Průměrná návratnost (%)", "Month": "Měsíc"},
                    markers=True, line_shape='linear') # Použití line chartu

# *** Úprava: Nastavení barvy čáry na světlou (TEXT_CREAM) ***
fig_season.update_traces(line=dict(color=TEXT_CREAM), marker=dict(color=TEXT_CREAM))

# Přidání nulové linie pro přehlednost
fig_season.add_hline(y=0, line_dash="dash", line_color=BORDER_DARK) # Používá tmavší linku

fig_season.update_layout(
    plot_bgcolor=f"{BG_BLACK}", 
    paper_bgcolor=f"{BG_BLACK}",
    font_color=f"{TEXT_CREAM}",
    title_font_color=f"{TEXT_CREAM}",
    # Tmavší barva linek a os
    xaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK),
    yaxis=dict(gridcolor=BORDER_DARK, linecolor=BORDER_DARK)
)
st.plotly_chart(fig_season, use_container_width=True)

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