# app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import plotly.express as px
from bs4 import BeautifulSoup # NOVÝ IMPORT pro robustnější parsování (simulace scrapingu)

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")
st.title("💵 USD Macro AI Dashboard — Category Scoring (last 3 months, High-Effort API)")

# -------------------------
# CONFIG
# -------------------------
LOOKBACK_DAYS = 90  # Návrat k 3 měsícům pro vyšší šanci na Actual
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# endpoints (Forex Factory data často sdílí stejný formát/zdroj)
JSON_WEEK_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
JSON_CDN = "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json"
XML_WEEK_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
XML_CDN = "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.xml"

CATEGORY_KEYWORDS = {
    # ... (kategorie beze změny)
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

def categorize_title(title):
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return cat
    return None

def clean_num(x):
    if x is None:
        return None
    s = str(x).strip()
    
    if s.startswith('.'):
         s = s[1:]
    
    if s == "" or s == "-" or s.lower() == "n/a" or s.lower() == "nan":
        return None
    s = s.replace("%", "").replace(",", "").replace("K", "000").replace("M", "000000").replace("B", "000000000")
    try:
        return float(s)
    except:
        return None

def fetch_json(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

def fetch_xml(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

def parse_faireconomy_json(json_data):
    rows = []
    if not json_data:
        return rows
    data_list = json_data.get("data") if isinstance(json_data, dict) else json_data
    if data_list is None:
        return rows
    for ev in data_list:
        try:
            country = ev.get("country")
            impact = ev.get("impact", 0)
            event = ev.get("event") or ev.get("title") or ev.get("summary") or ""
            ts = ev.get("timestamp")  # unix timestamp (seconds)
            if ts:
                dt = datetime.utcfromtimestamp(int(ts))
                dt_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                dt_str = None
            rows.append({
                "Date": dt_str,
                "Country": country,
                "Impact": impact,
                "Report": event,
                "Actual": ev.get("actual"),
                "Forecast": ev.get("forecast"),
                "Previous": ev.get("previous")
            })
        except Exception:
            continue
    return rows

def parse_faireconomy_xml(xml_text):
    rows = []
    if not xml_text:
        return rows
    try:
        # Použití BeautifulSoup pro robustní parsování (pro Forex Factory data)
        soup = BeautifulSoup(xml_text, 'xml')
        events = soup.find_all('event')
    except Exception:
        return rows
    
    for event in events:
        try:
            title = event.find('title').text if event.find('title') else ""
            country = event.find('country').text if event.find('country') else None
            impact_text = event.find('impact').text if event.find('impact') else None
            impact = None
            if impact_text:
                try:
                    impact = int(impact_text)
                except:
                    impact = {"Low":1,"Medium":2,"High":3}.get(impact_text.strip(), 0)
            
            date_text = (event.find('date') or event.find('time') or event.find('date_time')).text if (event.find('date') or event.find('time') or event.find('date_time')) else None
            dt_str = None
            if date_text:
                if date_text.startswith('.'):
                    date_text = date_text[1:]
                try:
                    dt = pd.to_datetime(date_text)
                    dt_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_str = date_text
            
            ts_node = event.find('timestamp').text if event.find('timestamp') else None
            if not dt_str and ts_node:
                try:
                    dt = datetime.utcfromtimestamp(int(ts_node))
                    dt_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_str = None
            
            # Vysoce robustní získávání textu (zajištění, že se vezme i prázdný řetězec)
            forecast = event.find('forecast').text if event.find('forecast') else ""
            actual = event.find('actual').text if event.find('actual') else ""
            previous = event.find('previous').text if event.find('previous') else ""
            
            rows.append({
                "Date": dt_str,
                "Country": country,
                "Impact": int(impact) if impact is not None else 0,
                "Report": title,
                "Actual": actual,
                "Forecast": forecast,
                "Previous": previous
            })
        except Exception:
            continue
    return rows

# Hlavní funkce pro sběr dat (3 měsíce)
def collect_events_data():
    all_rows = []
    weeks = 13 # 3 měsíce ~ 13 týdnů
    
    for w in range(weeks):
        target = TODAY - timedelta(weeks=w)
        
        # Zkusit různé URL šablony
        templates = [
            f"https://nfs.faireconomy.media/ff_calendar_thisweek.json?date={target.strftime('%Y-%m-%d')}",
            f"https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json?date={target.strftime('%Y-%m-%d')}",
            f"https://nfs.faireconomy.media/ff_calendar_thisweek.xml?date={target.strftime('%Y-%m-%d')}",
            f"https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.xml?date={target.strftime('%Y-%m-%d')}"
        ]
        
        for t in templates:
            try:
                if t.endswith(".json") or ".json?" in t:
                    j = fetch_json(t)
                    if j:
                        rows = parse_faireconomy_json(j)
                        all_rows.extend(rows)
                else:
                    xml_text = fetch_xml(t)
                    if xml_text:
                        rows = parse_faireconomy_xml(xml_text)
                        all_rows.extend(rows)
            except Exception:
                continue

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df["DateParsed"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["DateParsed"].notna()]
    df = df[df["DateParsed"] >= pd.Timestamp(START_DATE)]
    df = df.sort_values("DateParsed", ascending=False)
    # Deduplikace
    df = df.drop_duplicates(subset=["Report", "DateParsed"], keep="first").reset_index(drop=True)
    return df

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

def evaluate_category(df_cat):
    total = int(df_cat["Points"].sum())
    if total > 2:
        label = "Bullish"
    elif total < -2:
        label = "Bearish"
    else:
        label = "Neutral"
    return total, label

def generate_ai_summary(summary_df, final_score, overall_label):
    summary = f"Celkové fundamentální skóre pro USD za poslední 3 měsíce (automatický sběr dat) je **{final_score:+d}**, což vyúsťuje v **{overall_label}** sentiment. "
    
    sorted_summary = summary_df.sort_values("Total Points", ascending=False)
    
    best_cat = sorted_summary.iloc[0]
    if best_cat['Total Points'] > 0:
        summary += f"Nejsilnější pozitivní vliv na USD má kategorie **{best_cat['Category']}** s výsledkem **{best_cat['Total Points']:+d} bodů** ({best_cat['Events Count']} událostí). "
    
    worst_cat = sorted_summary.iloc[-1]
    if worst_cat['Total Points'] < 0:
        summary += f"Negativně působí kategorie **{worst_cat['Category']}** se skóre **{worst_cat['Total Points']:+d} bodů** ({worst_cat['Events Count']} událostí). "
    
    if overall_label == "Bullish pro USD":
        summary += "Fundamentální býčí sentiment je tažen silnými daty z klíčových oblastí, která převážila mírně negativní zprávy. "
    elif overall_label == "Bearish pro USD":
        summary += "Celková medvědí nálada je způsobena kumulací slabších výsledků. "
    else:
        summary += "Celkový neutralní výsledek poukazuje na vyváženou situaci. "

    return summary

# -------------------------
# BUILD DASHBOARD
# -------------------------
st.header("Data fetch & processing")
with st.spinner(f"Stahuji a zpracovávám ekonomické události (posledních ~{LOOKBACK_DAYS} dní). POZOR: Actual hodnoty mohou u starších dat chybět, viz poznámka níže."):
    df_all = collect_events_data()

if df_all.empty:
    st.error("Nepodařilo se stáhnout žádné události z ekonomického kalendáře. Zkus znovu nebo zkontroluj konektivitu.")
    st.stop()

# Keep only high impact (impact >=3)
df_all["ImpactNum"] = pd.to_numeric(df_all["Impact"], errors="coerce").fillna(0).astype(int)
df_all.loc[(df_all["ImpactNum"] == 0) & (df_all["Report"].str.lower().str.contains("high")), "ImpactNum"] = 3
df_high = df_all[df_all["ImpactNum"] >= 3].copy()

# Add Category
df_high["Category"] = df_high["Report"].apply(lambda r: categorize_title(str(r)) )
df_high = df_high[df_high["Category"].notna()].copy()

# Compute Points
df_high["Points"] = df_high.apply(score_event, axis=1)

# Standardize date string for display
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

st.success(f"Nalezeno {len(df_high)} high-impact událostí v cílových kategoriích za posledních {LOOKBACK_DAYS} dní.")

st.markdown("---")
st.warning("""
**DŮLEŽITÉ UPOZORNĚNÍ:** Tato verze stahuje data **automaticky** z veřejných kalendářů.
Tyto zdroje **spolehlivě neposkytují historické hodnoty 'Actual'** pro události starší než pár týdnů.
To je důvod, proč může být skóre (body) u starších událostí **nula**.
""")
st.markdown("---")


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
st.download_button("Download events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_3mo_auto.csv", "text/csv")

st.download_button("Download summary CSV", summary_df.to_csv(index=False).encode("utf-8"), "usd_macro_summary_auto.csv", "text/csv")

st.success("Hotovo — aplikace běží na automatickém sběru dat za 3 měsíce. Zkus znovu spustit.")