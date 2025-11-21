import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# ============= STYLE =============
st.set_page_config(page_title="USD Macro Dashboard", layout="wide")

PRIMARY_GREEN = "#2ECC71"
PRIMARY_RED = "#E74C3C"
PRIMARY_BLUE = "#2E86C1"
CARD_BG = "#F4F6F7"
CARD_BORDER = "#D5D8DC"

st.markdown("""
<style>
.big-metric {
    font-size: 48px;
    font-weight: 700;
    padding: 0px;
}
.metric-label {
    font-size: 18px;
    color: #555;
}
.result-box {
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 25px;
}
.card {
    background: #F4F6F7;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #D5D8DC;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# ============= FETCH FUNCTIONS =============
def fetch_history(symbol, period="1y"):
    return yf.Ticker(symbol).history(period=period)


def fetch_last_price(symbol):
    df = yf.Ticker(symbol).history(period="5d")
    if df.empty:
        return None
    return df["Close"].iloc[-1]


# ============= LOAD DATA =============
dxy_df = fetch_history("DX-Y.NYB")
vix_df = fetch_history("^VIX")

dxy_price = fetch_last_price("DX-Y.NYB")
vix_price = fetch_last_price("^VIX")

# ============= MAIN HEADER =============
st.title("💵 USD Macro Dashboard — Professional Version")
st.write("Realtime makro přehled + grafy DXY a VIX")


# ============= SENTIMENT PLACEHOLDER (FUNDAMENTS WILL FEED THIS) =============
sentiment = "NEUTRAL"
sentiment_color = PRIMARY_BLUE

st.markdown(
    f"""
    <div class='result-box' style="background:{sentiment_color}15;">
        <div class='metric-label'>Celkový USD sentiment</div>
        <div class='big-metric' style="color:{sentiment_color};">{sentiment}</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============= DXY + VIX CARDS =============
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 DXY — Dollar Index")
    st.metric("Aktuální hodnota", f"{dxy_price:.2f}")
    st.plotly_chart(px.line(dxy_df, y="Close", title="DXY — Daily Line Chart"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("⚡ VIX — Volatility Index")
    st.metric("Aktuální hodnota", f"{vix_price:.2f}")
    st.plotly_chart(px.line(vix_df, y="Close", title="VIX — Daily Line Chart"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ========= PLACE FOR FUNDAMENTS + SEASONALITY =========
# ===== FUNDAMENTY - TradingEconomics API (guest:guest) =====
import requests
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

TE_USER = "guest"
TE_PASS = "guest"

def fetch_te_us_calendar_last_30d():
    """
    Fetch TradingEconomics calendar for United States last 30 days.
    Uses demo credentials guest:guest.
    Returns DataFrame with Date, Event, Actual, Forecast, Previous, Impact, Signal.
    """

    end = datetime.utcnow()
    start = end - timedelta(days=30)

    # TradingEconomics calendar endpoint (demo usage)
    url = "https://api.tradingeconomics.com/calendar"
    params = {
        "country": "united states",
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "c": f"{TE_USER}:{TE_PASS}"
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            st.warning(f"TradingEconomics API returned status {r.status_code}")
            return pd.DataFrame()
        items = r.json()
    except Exception as e:
        st.warning(f"Chyba při volání TradingEconomics: {e}")
        return pd.DataFrame()

    rows = []
    for e in items:
        # Some events may not use these exact keys; guard with .get
        country = e.get("Country") or e.get("country") or e.get("location")
        if country is None or "united" not in str(country).lower():
            continue

        event = e.get("Event") or e.get("event") or e.get("title") or ""
        date_raw = e.get("Date") or e.get("date") or e.get("time") or ""
        # normalize date to YYYY-MM-DD
        try:
            date = pd.to_datetime(date_raw).strftime("%Y-%m-%d")
        except:
            date = (e.get("DateTime") or date_raw)[:10] if date_raw else ""

        actual = e.get("Actual") if e.get("Actual") is not None else e.get("actual")
        forecast = e.get("Forecast") if e.get("Forecast") is not None else e.get("estimate")
        previous = e.get("Previous") if e.get("Previous") is not None else e.get("previous")
        impact = e.get("Impact") or e.get("impact") or e.get("importance") or ""

        # If forecast missing, fallback to previous (common practice)
        if forecast is None:
            forecast = previous

        # Keep only events that have actual and forecast/previous
        if actual is None or forecast is None:
            continue

        # Convert to float if possible (guard)
        def to_num(x):
            try:
                return float(x)
            except:
                return None

        a = to_num(actual)
        f = to_num(forecast)
        prev = to_num(previous)

        if a is None or f is None:
            continue

        if a > f:
            signal = 1
        elif a < f:
            signal = -1
        else:
            signal = 0

        rows.append({
            "Date": date,
            "Report": event,
            "Actual": a,
            "Forecast": f,
            "Previous": prev,
            "Impact": impact,
            "Signal": signal
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    return df

# Streamlit display (insert where needed)
st.header("📰 USD Makro Fundamenty — Posledních 30 dní (TradingEconomics)")

fund_df = fetch_te_us_calendar_last_30d()
if fund_df.empty:
    st.warning("⚠️ Za posledních 30 dní nebyly nalezeny validní US makro události (nebo API neodpovědělo).")
else:
    # colorize signal
    def sig_style(x):
        if x > 0: return '🔺 +1'
        if x < 0: return '🔻 -1'
        return '⏺ 0'

    # show dataframe with signal text and numeric column
    fund_df_display = fund_df.copy()
    fund_df_display["SignalText"] = fund_df_display["Signal"].apply(sig_style)
    st.dataframe(fund_df_display[["Date", "Report", "Actual", "Forecast", "Previous", "Impact", "SignalText"]], use_container_width=True)

    total_score = int(fund_df["Signal"].sum())
    st.subheader(f"📊 Celkové fundamentální skóre (30 dní): **{total_score}**")
# ===== SEASONALITY — Monthly & Weekly (proper agr.) =====
import yfinance as yf
import pandas as pd
import plotly.express as px
import streamlit as st

def seasonality_monthly_proper(symbol, years=20):
    """
    For each year, compute monthly returns as: (last_close_of_month / last_close_of_prev_month - 1)
    Then average these monthly returns across years -> monthly seasonality (percent).
    """
    df = yf.Ticker(symbol).history(period=f"{years}y")
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df["Year"] = df.index.year
    df["Month"] = df.index.month

    # get last close per (Year,Month)
    monthly = df["Close"].groupby([df["Year"], df["Month"]]).last().reset_index()
    # compute pct change within same year (month vs previous month)
    monthly["Return"] = monthly.groupby("Year")["Close"].pct_change() * 100
    monthly = monthly.dropna()
    # average across years
    season = monthly.groupby("Month")["Return"].mean().reset_index()
    # fill month names
    season["MonthName"] = season["Month"].map({1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"})
    season = season.sort_values("Month")
    return season

def seasonality_weekly_proper(symbol, years=20):
    """
    For each year, compute weekly returns using ISO week numbers:
    - take last close of each ISO-week within a given year
    - compute pct change week-over-week within the same year
    - average the weekly returns for each week number across years (1..53)
    """
    df = yf.Ticker(symbol).history(period=f"{years}y")
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    # get ISO year and week
    isocal = df.index.isocalendar()
    df["ISO_Year"] = isocal.year
    df["ISO_Week"] = isocal.week

    weekly = df["Close"].groupby([df["ISO_Year"], df["ISO_Week"]]).last().reset_index()
    weekly["Return"] = weekly.groupby("ISO_Year")["Close"].pct_change() * 100
    weekly = weekly.dropna()

    # average across years by ISO_Week
    wk = weekly.groupby("ISO_Week")["Return"].mean().reset_index()
    wk = wk.sort_values("ISO_Week")
    return wk

def seasonality_heatmap_months(symbol, years=20):
    df = yf.Ticker(symbol).history(period=f"{years}y")
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index)
    df["Year"] = df.index.year
    df["Month"] = df.index.month
    monthly = df["Close"].groupby([df["Year"], df["Month"]]).last().reset_index()
    monthly["Return"] = monthly.groupby("Year")["Close"].pct_change() * 100
    monthly = monthly.dropna()
    pivot = monthly.pivot(index="Year", columns="Month", values="Return").fillna(0)
    # reorder columns 1..12
    pivot = pivot[sorted(pivot.columns)]
    # convert numeric month to names
    pivot.columns = [ {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}[c] for c in pivot.columns ]
    return pivot

def display_seasonality_block(symbol, title):
    st.subheader(title)
    m = seasonality_monthly_proper(symbol)
    if m.empty:
        st.write("Data not available for symbol:", symbol)
        return

    # Line chart (months)
    fig_line = px.line(m, x="MonthName", y="Return", markers=True, title=f"{title} — Monthly Seasonality (avg % change)")
    st.plotly_chart(fig_line, use_container_width=True)

    # Heatmap months × years
    heat = seasonality_heatmap_months(symbol)
    if not heat.empty:
        fig_heat = px.imshow(heat.T, aspect="auto", origin="lower", labels=dict(x="Year", y="Month", color="% Return"),
                            x=heat.index.astype(str), y=list(heat.columns), title=f"{title} — Monthly Returns Heatmap (each year)")
        st.plotly_chart(fig_heat, use_container_width=True)

    # Weekly
    wk = seasonality_weekly_proper(symbol)
    if not wk.empty:
        fig_wk = px.line(wk, x="ISO_Week", y="Return", markers=True, title=f"{title} — Weekly Seasonality (avg % change by ISO week)")
        st.plotly_chart(fig_wk, use_container_width=True)

    # Ranking top months
    top_months = m[["MonthName", "Return"]].sort_values("Return", ascending=False).reset_index(drop=True)
    top_months.index = top_months.index + 1
    st.markdown("**Top months (average monthly return)**")
    st.table(top_months.head(6).rename(columns={"MonthName":"Month","Return":"Avg % Return"}))

# Insert display calls where you want seasonality shown:
st.header("📈 Seasonality — DXY, Gold, S&P500 (monthly & weekly)")
display_seasonality_block("DX-Y.NYB", "DXY (Dollar Index)")
display_seasonality_block("GC=F", "Gold (XAU/USD)")
display_seasonality_block("^GSPC", "S&P 500 (SPX)")


# FOOTER
st.caption("Dashboard v.2.0 — Base version (bez fundamentů)")
