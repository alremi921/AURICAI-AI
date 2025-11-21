import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="USD Macro Dashboard", layout="wide")

def fetch_history(symbol, period='30d', interval='1d'):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    return df['Close']

# Fetch historical close price series for line charts
dxy_history = fetch_history("DX-Y.NYB")
vix_history = fetch_history("^VIX")

# Display line charts for DXY and VIX
st.subheader("Daily Close Price Line Charts")
col1, col2 = st.columns(2)
with col1:
    st.line_chart(dxy_history, height=300)
with col2:
    st.line_chart(vix_history, height=300)

# Simplified example for fundamental data scoring
# In practice, this data would come from an API or real-time scraping of Forex Factory or similar
fundamental_scores = {
    "Non-Farm Employment Change": +1,  # example: actual > forecast so bullish
    # Add more indicators similarly
}

# Aggregation of fundamental scores
total_score = sum(fundamental_scores.values())

if total_score > 2:
    sentiment = "BULLISH USD"
elif total_score < -2:
    sentiment = "BEARISH USD"
else:
    sentiment = "NEUTRAL USD"

st.markdown(f"### Fundamental Report Sentiment Score: {total_score} -> {sentiment}")

# Existing metrics and delta with coloring can remain below
