import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="USD Macro Dashboard",
    layout="wide",
    page_icon="💵"
)

# ----------------------------
#  STYLING
# ----------------------------
st.markdown("""
<style>
.big-number {
    font-size: 38px;
    font-weight: 700;
    color: white;
    padding: 18px;
    border-radius: 14px;
    text-align: center;
}
.green-box { background: #16a34a; }
.red-box { background: #dc2626; }
.gray-box { background: #334155; }

.section-title {
    font-size: 28px;
    font-weight: 700;
    margin-top: 30px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------
#  FUNKCE PRO FETCH
# ----------------------------
def get_price(ticker):
    try:
        df = yf.download(ticker, period="5d", progress=False)
        return df["Close"].iloc[-1]
    except:
        return None


# ----------------------------
#  FETCH ASSETŮ
# ----------------------------
dxy = get_price("DX-Y.NYB")  # DXY
vix = get_price("^VIX")       # VIX
us10y = get_price("^TNX")     # 10Y yield

# ----------------------------
#  SENTIMENT SCORE
# ----------------------------
def usd_sentiment(dxy, vix, us10y):
    score = 0
    if dxy and dxy > 100: score += 1
    if vix and vix < 15: score += 1
    if us10y and us10y > 4: score += 1
    return score


sent = usd_sentiment(dxy, vix, us10y)

if sent == 3:
    sentiment_text = "USD STRONG — Risk OFF"
    sentiment_color = "green-box"
elif sent == 2:
    sentiment_text = "USD MIXED — Neutral"
    sentiment_color = "gray-box"
else:
    sentiment_text = "USD WEAK — Risk ON"
    sentiment_color = "red-box"


# ----------------------------
#  LAYOUT
# ----------------------------
st.title("💵 USD MACRO DASHBOARD — PRO VERSION")

st.markdown(f"""
<div class="big-number {sentiment_color}">
{sentiment_text}
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 DXY")
    st.metric("Google Finance", value=f"{dxy:.2f}" if dxy else "N/A")

with col2:
    st.subheader("🧨 VIX Index")
    st.metric("Fear / Volatility", value=f"{vix:.2f}" if vix else "N/A")

with col3:
    st.subheader("🏦 US 10Y Yield")
    st.metric("Treasury", value=f"{us10y:.2f}%" if us10y else "N/A")


st.markdown("---")

# ----------------------------
#  GRAFY – DXY & VIX
# ----------------------------

def load_history(ticker):
    df = yf.download(ticker, period="6mo", progress=False)
    return df

hist_dxy = load_history("DX-Y.NYB")
hist_vix = load_history("^VIX")

colA, colB = st.columns(2)

with colA:
    st.markdown("### 📊 DXY – posledních 6 měsíců")
    if not hist_dxy.empty:
        fig = px.line(hist_dxy, y="Close", title="", labels={"Close": "Price"})
        st.plotly_chart(fig, use_container_width=True)

with colB:
    st.markdown("### 📊 VIX – posledních 6 měsíců")
    if not hist_vix.empty:
        fig = px.line(hist_vix, y="Close", title="", labels={"Close": "Volatility"})
        st.plotly_chart(fig, use_container_width=True)


# ----------------------------
#  ECONOMIC CALENDAR
# ----------------------------
st.markdown("## 🗓 Economic Calendar (USD FILTERED)")

st.markdown("""
<iframe src="https://www.tradingeconomics.com/calendar?country=united-states" 
width="100%" height="800px"></iframe>
""", unsafe_allow_html=True)


# ----------------------------
#  NOTES
# ----------------------------
st.markdown("## 📝 Trading Notes")
notes = st.text_area("Poznámky:", height=180)
