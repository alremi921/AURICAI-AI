# app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title="USD Macro AI Dashboard", layout="wide")
st.title("💵 USD Macro AI Dashboard — Category Scoring (last 30 days)")

# -------------------------
# CONFIG
# -------------------------
# how far back (days) - ZMĚNA na 30 dní
LOOKBACK_DAYS = 30
TODAY = datetime.utcnow()
START_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

# endpoints to try (robust)
JSON_WEEK_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
JSON_CDN = "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json"
XML_WEEK_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
XML_CDN = "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.xml"

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

# helper: map category by title
def categorize_title(title):
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return cat
    return None

# helper: clean numeric fields -> float or None
def clean_num(x):
    if x is None:
        return None
    s = str(x).strip()
    # OČISTNÁ ZMĚNA: Odstranění nežádoucího symbolu bodu (tečky) na začátku
    if s.startswith('.'):
         s = s[1:]
    
    if s == "" or s == "-" or s.lower() == "n/a":
        return None
    # remove % and commas
    s = s.replace("%", "").replace(",", "")
    try:
        return float(s)
    except:
        return None

# Try to fetch weekly JSON (current week)
def fetch_json(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# Fetch XML and parse events
def fetch_xml(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

# Parse JSON structure returned by ff_calendar_thisweek.json
def parse_faireconomy_json(json_data):
    rows = []
    if not json_data:
        return rows
    # data may be under 'data' or be a list
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

# Parse XML (ff_calendar_thisweek.xml format)
def parse_faireconomy_xml(xml_text):
    rows = []
    if not xml_text:
        return rows
    try:
        # PŘIDÁNO: Zkusit odstranit nečisté znaky před <root> nebo <events>
        xml_text = xml_text.strip()
        if not xml_text.startswith('<'):
            # Najdi první znak '<' a začni od něj, pokud to není validní XML
            xml_text = '<root>' + xml_text.split('<', 1)[1] if '<' in xml_text else xml_text
            if not xml_text.endswith('>'):
                 xml_text += '</root>'

        root = ET.fromstring(xml_text)
    except Exception:
        return rows
    # xml structure: <event> elements
    for event in root.findall(".//event"):
        try:
            title = event.findtext("title") or ""
            country = event.findtext("country")
            impact_text = event.findtext("impact")
            impact = None
            if impact_text:
                try:
                    impact = int(impact_text)
                except:
                    impact = {"Low":1,"Medium":2,"High":3}.get(impact_text.strip(), 0)
            
            date_text = event.findtext("date") or event.findtext("time") or event.findtext("date_time")
            dt_str = None
            if date_text:
                if date_text.startswith('.'):
                    date_text = date_text[1:]
                try:
                    dt = pd.to_datetime(date_text)
                    dt_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_str = date_text
            
            ts_node = event.findtext("timestamp")
            if not dt_str and ts_node:
                try:
                    dt = datetime.utcfromtimestamp(int(ts_node))
                    dt_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_str = None
            forecast = event.findtext("forecast")
            actual = event.findtext("actual")
            previous = event.findtext("previous")
            
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

# ZMĚNA: Použití st.cache_data s TTL pro automatické obnovení po 4 hodinách
@st.cache_data(ttl=4 * 3600) # Automatické obnovení dat každé 4 hodiny (4 * 3600 sekund)
def collect_events_data():
    all_rows = []

    # 1) Try the canonical JSON endpoint for current & near weeks
    for url in (JSON_CDN, JSON_WEEK_URL):
        j = fetch_json(url)
        if j:
            rows = parse_faireconomy_json(j)
            all_rows.extend(rows)

    # 2) Try XML weekly endpoint
    for url in (XML_CDN, XML_WEEK_URL):
        xml_text = fetch_xml(url)
        if xml_text:
            rows = parse_faireconomy_xml(xml_text)
            all_rows.extend(rows)

    # 3) Iterate backward weekly (4 týdny ~ 1 měsíc)
    weeks = 4
    for w in range(weeks):
        target = TODAY - timedelta(weeks=w)
        # try a few URL templates
        templates = [
            f"https://nfs.faireconomy.media/ff_calendar_thisweek.json?date={target.strftime('%Y-%m-%d')}",
            f"https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json?date={target.strftime('%Y-%m-%d')}",
            f"https://nfs.faireconomy.media/ff_calendar_thisweek.xml?date={target.strftime('%m.%Y')}",
            f"https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.xml?date={target.strftime('%m.%Y')}"
        ]
        
        for t in templates:
            try:
                if t.endswith(".json") or ".json?" in t:
                    j = fetch_json(t)
                    if j:
                        rows = parse_faireconomy_json(j)
                        if rows:
                            all_rows.extend(rows)
                else:
                    xml_text = fetch_xml(t)
                    if xml_text:
                        rows = parse_faireconomy_xml(xml_text)
                        if rows:
                            all_rows.extend(rows)
            except Exception:
                continue
    
    # deduplicate by Report + Date
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
    # normalize Date to datetime when possible
    df["DateParsed"] = pd.to_datetime(df["Date"], errors="coerce")
    # only keep within lookback window (30 dní)
    df = df[df["DateParsed"].notna()]
    df = df[df["DateParsed"] >= pd.Timestamp(START_DATE)]
    df = df.sort_values("DateParsed", ascending=False)
    df = df.drop_duplicates(subset=["Report", "DateParsed"], keep="first").reset_index(drop=True)
    return df

# Score each event: compare actual vs forecast -> +1 / -1 / 0
def score_event(row):
    a = clean_num(row.get("Actual"))
    f = clean_num(row.get("Forecast"))
    # Double check: Skóre bude 0 POUZE, pokud Actual nebo Forecast chybí (None)
    if a is None or f is None:
        return 0  # neutral if missing data (PROBLEM)
    if a > f:
        return 1
    if a < f:
        return -1
    return 0

# AI-style evaluator (simple rule-based aggregator requested)
def evaluate_category(df_cat):
    # sum points
    total = int(df_cat["Points"].sum())
    # return classification per user's rule:
    if total > 2:
        label = "Bullish"
    elif total < -2:
        label = "Bearish"
    else:
        label = "Neutral"
    return total, label

# NOVÁ FUNKCE: AI-style vyhodnocení
def generate_ai_summary(summary_df, final_score, overall_label):
    summary = f"Celkové fundamentální skóre pro USD za poslední měsíc (30 dní) je **{final_score:+d}**, což vyúsťuje v **{overall_label}** sentiment. "
    
    # Seřazení kategorií podle skóre
    sorted_summary = summary_df.sort_values("Total Points", ascending=False)
    
    # 1. Největší vliv (nejpozitivnější)
    best_cat = sorted_summary.iloc[0]
    if best_cat['Total Points'] > 0:
        summary += f"Nejsilnější pozitivní vliv na USD má kategorie **{best_cat['Category']}** s výsledkem **{best_cat['Total Points']:+d} bodů** ({best_cat['Events Count']} událostí). To značí, že makrodata z této oblasti překonala očekávání trhu. "
    
    # 2. Nejslabší vliv (nejnegativnější)
    worst_cat = sorted_summary.iloc[-1]
    if worst_cat['Total Points'] < 0:
        summary += f"Negativně působí kategorie **{worst_cat['Category']}** se skóre **{worst_cat['Total Points']:+d} bodů** ({worst_cat['Events Count']} událostí). Zde aktuální výsledky zaostaly za konsenzem. "
    
    # 3. Celková bilance
    if overall_label == "Bullish pro USD":
        summary += "Fundamentální býčí sentiment je tažen silnými daty z klíčových oblastí, která převážila mírně negativní zprávy. "
    elif overall_label == "Bearish pro USD":
        summary += "Celková medvědí nálada je způsobena kumulací slabších výsledků, což signalizuje zpomalení nebo překážky pro Fed/Ekonomiku. "
    else: # Neutral
        summary += "Celkový neutralní výsledek poukazuje na vyváženou situaci, kdy se pozitivní a negativní fundamenty navzájem vyrušily. "

    return summary

# -------------------------
# BUILD DASHBOARD
# -------------------------
st.header("Data fetch & processing")
with st.spinner(f"Stahuji a zpracovávám ekonomické události (posledních ~{LOOKBACK_DAYS} dní)..."):
    df_all = collect_events_data()

if df_all.empty:
    st.error("Nepodařilo se stáhnout žádné události z ekonomického kalendáře. Zkus znovu nebo zkontroluj konektivitu.")
    st.stop()

# Keep only high impact (impact >=3)
df_all["ImpactNum"] = pd.to_numeric(df_all["Impact"], errors="coerce").fillna(0).astype(int)
# If ImpactNum is 0 but title contains 'high', treat as 3
df_all.loc[(df_all["ImpactNum"] == 0) & (df_all["Report"].str.lower().str.contains("high")), "ImpactNum"] = 3
df_high = df_all[df_all["ImpactNum"] >= 3].copy()

# Add Category
df_high["Category"] = df_high["Report"].apply(lambda r: categorize_title(str(r)) )
# Keep only events that matched one of our categories
df_high = df_high[df_high["Category"].notna()].copy()

# Compute Points
df_high["Points"] = df_high.apply(score_event, axis=1)

# Standardize date string for display
df_high["DateDisplay"] = df_high["DateParsed"].dt.strftime("%Y-%m-%d %H:%M")

# Show counts
st.success(f"Nalezeno {len(df_high)} high-impact událostí v cílových kategoriích za posledních {LOOKBACK_DAYS} dní. Data se automaticky aktualizují každé 4 hodiny.")

# -------------------------
# Create per-category tables
# -------------------------
st.header("Tabulky podle témat")
cols = st.columns(2)

category_frames = {}
for cat in CATEGORY_KEYWORDS.keys():
    cat_df = df_high[df_high["Category"] == cat].copy()
    # sort by date desc
    cat_df = cat_df.sort_values("DateParsed", ascending=False)
    # display minimal columns
    display_df = cat_df[["DateDisplay", "Report", "Actual", "Forecast", "Previous", "Points"]].rename(
        columns={"DateDisplay":"Date","Report":"Report","Actual":"Actual","Forecast":"Forecast","Previous":"Previous","Points":"Points"}
    )
    category_frames[cat] = cat_df  # keep original for aggregation

    # place in UI: 2 columns, alternating
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

# calculate final combined score: sum of category totals
final_score = int(summary_df["Total Points"].sum())
# overall label by user's rule (>2 bullish, <-2 bearish, else neutral)
if final_score > 2:
    overall_label = "Bullish pro USD"
elif final_score < -2:
    overall_label = "Bearish pro USD"
else:
    overall_label = "Neutral pro USD"

# show category summary
st.subheader("Category summary")
st.table(summary_df.style.format({"Total Points":"{:+d}"}))

# final row
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

# full events CSV
csv_all = df_high.sort_values("DateParsed", ascending=False)[
    ["DateDisplay","Category","Report","Actual","Forecast","Previous","Points"]
].rename(columns={"DateDisplay":"Date"})
st.download_button("Download events CSV", csv_all.to_csv(index=False).encode("utf-8"), "usd_macro_events_30d.csv", "text/csv")

# summary CSV
st.download_button("Download summary CSV", summary_df.to_csv(index=False).encode("utf-8"), "usd_macro_summary.csv", "text/csv")

st.success("Hotovo — dashboard aktualizován a zaměřen na spolehlivost dat za poslední měsíc. Zkus znovu spustit.")