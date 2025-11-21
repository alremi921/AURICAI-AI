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
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta


def fetch_tradingview_high_impact():
    # ONLY HIGH-IMPACT + USA
    url = "https://economic-calendar.tradingview.com/events?importance=3&filter=country%3Dunited_states"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
    except:
        return pd.DataFrame()

    if "events" not in data:
        return pd.DataFrame()

    rows = []
    for event in data["events"]:
        try:
            name = event.get("event", None)
            country = event.get("country", None)
            actual = event.get("actual", None)
            forecast = event.get("forecast", None)
            previous = event.get("previous", None)
            timestamp = event.get("timestamp", None)

            if country != "United States":
                continue

            if timestamp:
                date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            else:
                date = None

            # Sentiment score
            if actual is not None and forecast is not None:
                if actual > forecast:
                    signal = 1
                elif actual < forecast:
                    signal = -1
                else:
                    signal = 0
            else:
                signal = 0

            rows.append({
                "Date": date,
                "Report": name,
                "Actual": actual,
                "Forecast": forecast,
                "Previous": previous,
                "Signal": signal
            })
        except:
            continue

    df = pd.DataFrame(rows)
    return df


# =========== STREAMLIT OUTPUT ===============

st.header("📰 USD Makro Fundamenty — High Impact (TradingView)")

fund = fetch_tradingview_high_impact()

if fund.empty:
    st.warning("⚠️ Nepodařilo se načíst data z TradingView API.")
else:
    fund = fund.sort_values("Date", ascending=False)

    fund["Signal Label"] = fund["Signal"].map({
        1: "🔺 +1 (Bullish)",
        0: "⏺ 0 (Neutral)",
        -1: "🔻 -1 (Bearish)"
    })

    st.dataframe(
        fund[["Date", "Report", "Actual", "Forecast", "Previous", "Signal Label"]],
        use_container_width=True
    )

    total = fund["Signal"].sum()
    st.subheader(f"📊 Celkové USD Fundamentální Skóre: **{total}**")
import yfinance as yf
import pandas as pd
import plotly.express as px
import streamlit as st

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

MONTH_MAP = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
}

def seasonality_monthly(symbol, years=20):
    df = yf.Ticker(symbol).history(period=f"{years}y")
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df.index = pd.to_datetime(df.index)
    df["Year"] = df.index.year
    df["Month"] = df.index.month

    # last monthly close
    monthly = df["Close"].groupby([df["Year"], df["Month"]]).last().reset_index()

    # monthly returns relative to previous month
    monthly["Return"] = monthly.groupby("Year")["Close"].pct_change() * 100
    monthly = monthly.dropna()

    # map month names
    monthly["MonthName"] = monthly["Month"].map(MONTH_MAP)

    # Ensure all 12 months exist even if they have NaN
    all_months = pd.DataFrame({"Month": list(range(1,13))})
    all_months["MonthName"] = all_months["Month"].map(MONTH_MAP)

    mean_monthly = (
        monthly.groupby("Month")[["Return"]]
        .mean()
        .reset_index()
        .merge(all_months, on="Month", how="right")
        .sort_values("Month")
    )

    return mean_monthly, monthly


def seasonality_heatmap(monthly_df):
    heat = monthly_df.pivot(index="Year", columns="MonthName", values="Return")

    # Reorder months correctly
    heat = heat.reindex(columns=MONTH_ORDER)

    return heat


def render_seasonality(symbol, title):
    st.subheader(title)

    mean_monthly, monthly_full = seasonality_monthly(symbol)

    # Line chart (12 months, ordered)
    fig_line = px.line(
        mean_monthly,
        x="MonthName",
        y="Return",
        markers=True,
        category_orders={"MonthName": MONTH_ORDER},
        title=f"{title} — Avg Monthly Seasonality (20Y)",
        labels={"Return": "% Average Monthly Return"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Heatmap
    heat = seasonality_heatmap(monthly_full)
    fig_hm = px.imshow(
        heat.T,
        aspect="auto",
        title=f"{title} — Heatmap (20Y)",
        labels=dict(x="Year", y="Month", color="% Return")
    )
    st.plotly_chart(fig_hm, use_container_width=True)


st.header("📈 Seasonality — DXY / XAU / S&P 500 (20Y)")

render_seasonality("DX-Y.NYB", "DXY (US Dollar Index)")
render_seasonality("GC=F", "Gold (XAU/USD)")
render_seasonality("^GSPC", "S&P 500 Index")

# FOOTER
st.caption("Dashboard v.2.0 — Base version (bez fundamentů)")
