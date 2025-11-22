# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os 

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")
st.title("💵 USD Macro AI Dashboard — Category Scoring (last 30 days, data z CSV)")

# -------------------------
# CONFIG
# -------------------------
# how far back (days)
LOOKBACK_DAYS = 30
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

CSV_FILE_PATH = "usd_macro_history.csv.txt" # ZMĚNA: Nová cesta k datům

# KEYWORDS for categories (case-insensitive)
CATEGORY_KEYWORDS = {
    "Inflace": [
        "cpi", "core cpi", "pce", "core pce", "consumer price", "inflation"
    ],
    "Úrokové sazby": [
        "fomc", "fed rate", "dot plot", "federal funds", "interest rate",
        "federal open market", "fed statement", "fed policy", "press conference", "fed speakers"
    ],
    "Trh práce": [
        "nonfarm payroll", "nfp", "unemployment rate", "jolts", "job openings",
        "average hourly", "hourly earnings", "initial jobless", "continuing claims"
    ],
    "Ekonomická aktivita": [
        "pmi", "ism", "retail sales", "gdp", "gross domestic product", "industrial production", "manufacturing", "services pmi"
    ]
}

# helper: clean numeric fields -> float or None
def clean_num(x):
    if x is None:
        return None
    s = str(x).strip()
    
    if s.startswith('.'):
         s = s[1:]
    
    if s == "" or s == "-" or s.lower() == "n/a" or s.lower() == "nan":
        return None
    # remove % and commas and K/M/B (if they exist)
    s = s.replace("%", "").replace(",", "").replace("K", "000").replace("M", "000000").replace("B", "000000000")
    try:
        return float(s)
    except:
        return None

# NOVÁ FUNKCE: Načtení dat z lokálního CSV
def load_events_from_csv():
    if not os.path.exists(CSV_FILE_PATH):
        st.error(f"Chyba: Soubor s daty '{CSV_FILE_PATH}' nebyl nalezen. Ujistěte se, že je uložen ve stejném adresáři jako 'app.py'.")
        return pd.DataFrame()

    try:
        # POUŽÍVÁME read_csv I PRO SOUBOR S PŘÍPONOU .txt, PROTOŽE SE JEDNÁ O CSV FORMÁT
        df = pd.read_csv(CSV_FILE_PATH)
        
        if 'Date' in df.columns:
             df["DateParsed"] = pd.to_datetime(df["Date"], errors="coerce")
        else:
             st.error("Chyba ve sloupcích CSV: Chybí sloupec 'Date'.")
             return pd.DataFrame()

        # Filtrace podle časového okna (posledních 30 dní)
        df = df[df["DateParsed"].notna()]
        df = df[df["DateParsed"] >= pd.Timestamp(START_DATE)]
        
        # Filtrace na High Impact (sloupec Impact musí existovat a mít hodnotu 3)
        if "Impact" in df.columns:
            df["ImpactNum"] = pd.to_numeric(df["Impact"], errors="coerce").fillna(0).astype(int)
            df = df[df["ImpactNum"] >= 3].copy()
        else:
            df["ImpactNum"] = 3

        df = df.sort_values("DateParsed", ascending=False)
        return df.reset_index(drop=True)
    
    except Exception as e:
        st.error(f"Nepodařilo se načíst nebo zpracovat soubor CSV. Zkontrolujte formátování. Chyba: {e}")
        return pd.DataFrame()

# Score each event: compare actual vs forecast -> +1 / -1 / 0
def score_event(row):
    a = clean_num(row.get("Actual"))
    f = clean_num(row.get("Forecast"))
    
    if a is None or f is None:
        return 0
    if a > f:
        return 1
    if a < f:
        return -1
    return 0

# AI-style evaluator (simple rule-based aggregator requested)
def evaluate_category(df_cat):
    total = int(df_cat["Points"].sum())
    if total > 2:
        label = "Bullish"
    elif total < -2:
        label = "Bearish"
    else:
        label = "Neutral"
    return total, label

# NOVÁ FUNKCE: AI-style vyhodnocení
def generate_ai_summary(summary_df, final_score, overall_label):
    summary = f"Celkové fundamentální skóre pro USD za poslední měsíc (data z CSV) je **{final_score:+d}**, což vyúsťuje v **{overall_label}** sentiment. "
    
    sorted_summary = summary_df.sort_values("Total Points", ascending=False)
    
    best_cat = sorted_summary.iloc[0]
    if best_cat['Total Points'] > 0:
        summary += f"Nejsilnější pozitivní vliv na USD má kategorie **{best_cat['Category']}** s výsledkem **{best_cat['Total Points']:+d} bodů** ({best_cat['Events Count']} událostí). To značí, že makrodata z této oblasti překonala očekávání trhu. "
    
    worst_cat = sorted_summary.iloc[-1]
    if worst_cat['Total Points'] < 0:
        summary += f"Negativně působí kategorie **{worst_cat['Category']}** se skóre **{worst_cat['Total Points']:+d} bodů** ({worst_cat['Events Count']} událostí). Zde aktuální výsledky zaostaly za konsenzem. "
    
    if overall_label == "Bullish pro USD":
        summary += "Fundamentální býčí sentiment je tažen silnými daty z klíčových oblastí, která převážila mírně negativní zprávy. "
    elif overall_label == "Bearish pro USD":
        summary += "Celková medvědí nálada je způsobena kumulací slabších výsledků. "
    else: # Neutral
        summary += "Celkový neutralní výsledek poukazuje na vyváženou situaci. "

    return summary


# -------------------------
# BUILD DASHBOARD
# -------------------------
st.header("Data fetch & processing")
with st.spinner(f"Načítám data z lokálního souboru '{CSV_FILE_PATH}' (posledních ~{LOOKBACK_DAYS} dní)..."):
    df_high = load_events_from_csv()

if df_high.empty:
    st.error("Nepodařilo se načíst žádná platná data. Zkontrolujte soubor 'usd_macro_history.csv.txt' a jeho formát (musí obsahovat hlavičku a čárky jako oddělovače).")
    st.stop()

if "Category" not in df_high.columns:
    st.error("Chyba: V souboru CSV chybí sloupec 'Category'. Bodování nelze provést.")
    st.stop()

df_high["Points"] = df_high.apply(score_event, axis=1)
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

st.success(f"Nalezeno {len(df_high)} High-Impact událostí v cílových kategoriích za posledních {LOOKBACK_DAYS} dní. Data pochází ze souboru CSV.")

# -------------------------
# Create per-category tables
# -------------------------
st.header("Tabulky podle témat")
cols = st.columns(2)

category_frames = {}
for cat in CATEGORY_KEYWORDS.keys(): 
    cat_df = df_high[df_high["Category"] == cat].copy()
    
    if cat_df.empty:
        continue 
    
    cat_df = cat_df.sort_values("DateParsed", ascending=False)
    display_df = cat_df[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    )
    category_frames[cat] = cat_df

    if list(CATEGORY_KEYWORDS.keys()).index(cat) % 2 == 0:
        with cols[0]:
            st.subheader(cat)
            st.dataframe(display_df, use_container_width=True)
    else:
        with cols[1]:
            st.subheader(cat)
            st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# -------------------------
# Aggregation & final evaluation
# -------------------------
st.header("Souhrn: agregace bodů + celkové vyhodnocení fundamentu")

summary_rows = []
for cat, df_cat in category_frames.items():
    total, label = evaluate_category(df_cat)
    summary_rows.append({
        "Category": cat,
        "Events Count": int(len(df_cat)),
        "Total Points": total,
        "Evaluation": label
    })

summary_df = pd.DataFrame(summary_rows)

final_score = int(summary_df["Total Points"].sum())
if final_score > 2:
    overall_label = "Bullish pro USD"
elif final_score < -2:
    overall_label = "Bearish pro USD"
else:
    overall_label = "Neutral pro USD"

st.subheader("Category summary")
st.table(summary_df.style.format({"Total Points":"{:+d}"}))

st.markdown(f"### 🔎 Celkové fundamentální skóre: **{final_score:+d}** — **{overall_label}**")

# NOVÁ SEKCE: AI Vyhodnocení
st.markdown("---")
st.header("🤖 AI Fundamentální Vyhodnocení")
ai_text = generate_ai_summary(summary_df, final_score, overall_label)
st.info(ai_text)


# -------------------------
# Optional: timeline & viz
# -------------------------
st.markdown("---")
st.header("Vizualizace: body v čase (timeline)")

viz_df = df_high.copy()
viz_df["DateSimple"] = viz_df["DateParsed"].dt.date
viz_agg = viz_df.groupby(["DateSimple","Category"])["Points"].sum().reset_index()

if not viz_agg.empty:
    fig = px.line(viz_agg, x="DateSimple", y="Points", color="Category", markers=True,
                  title="Body podle kategorie v čase (denní agregát)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Není dost dat pro graf.")
    
# -------------------------
# Allow CSV export
# -------------------------
st.markdown("---")
st.header("Export / download")
st.markdown("Stáhni data pro další analýzu:")

csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_30d_final.csv", "text/csv")

st.download_button("Download summary CSV", summary_df.to_csv(index=False).encode("utf-8"), "usd_macro_summary_final.csv", "text/csv")

st.success(f"Hotovo — Aplikace nyní čte data ze souboru '{CSV_FILE_PATH}'.")