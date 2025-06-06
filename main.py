import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils import (
    fetch_weekly_data, fetch_daily_data, calculate_macd,
    detect_macd_cross, load_group_symbols
)
from db import create_db, insert_signal, fetch_all_signals, update_signal_prices

st.set_page_config(page_title="📊 Stock Signal Scanner", layout="wide")
st.title("📈 Technical Signal Scanner")

# Sidebar Configuration
st.sidebar.header("🔧 Scanner Options")
group_option = st.sidebar.selectbox("Select NSE Group", ["Nifty 50", "Nifty 500", "Midcap 100", "Smallcap 250"])
scan_type = st.sidebar.selectbox("Scan Strategy", [
    "MACD Bullish Crossover",
    "Price Crosses Above 200 EMA"
])
interval = st.sidebar.radio("Data Interval", ["Weekly", "Daily"])
backtest_date = st.sidebar.date_input("Backtest As Of Date (optional)", value=None)

# Initialize DB
create_db()
tickers = load_group_symbols(group_option)
scan_triggered = st.button("🚀 Run Scan")

if scan_triggered:
    results = []
    progress = st.progress(0)

    for i, symbol in enumerate(tickers):
        progress.progress((i + 1) / len(tickers))
        df = fetch_weekly_data(symbol) if interval == "Weekly" else fetch_daily_data(symbol)
        if df.empty or 'Close' not in df.columns:
            continue

        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

        if scan_type == "MACD Bullish Crossover":
            df = calculate_macd(df)
            if backtest_date:
                signal_found = detect_macd_cross(df[df['Date'] <= pd.to_datetime(backtest_date)])
            else:
                signal_found = detect_macd_cross(df)

        elif scan_type == "Price Crosses Above 200 EMA":
            df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
            if len(df) < 2:
                continue
            prev_close = df.iloc[-2]['Close']
            prev_ema = df.iloc[-2]['EMA200']
            curr_close = df.iloc[-1]['Close']
            curr_ema = df.iloc[-1]['EMA200']
            signal_found = prev_close < prev_ema and curr_close > curr_ema

        else:
            signal_found = False

        if signal_found:
            price = df.iloc[-1]['Close']
            chart_url = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol.replace('.NS', '')}"
            if backtest_date:
                df_bt = df[df['Date'] <= pd.to_datetime(backtest_date)]
                if df_bt.empty:
                    continue
                price_then = df_bt.iloc[-1]['Close']
                gain_pct = ((price - price_then) / price_then) * 100
                result = "✅" if gain_pct > 0 else "❌"
                results.append({
                    "Symbol": symbol,
                    "Price on Backtest Date": round(price_then, 2),
                    "Current Price": round(price, 2),
                    "Gain %": round(gain_pct, 2),
                    "Result": result,
                    "Chart": chart_url
                })
            else:
                insert_signal(symbol, price)
                results.append({
                    "Symbol": symbol,
                    "Price": round(price, 2),
                    "Chart": chart_url
                })

        time.sleep(0.5)

    progress.empty()

    if results:
        st.subheader("📊 Scan Results")
        df_results = pd.DataFrame(results)
        st.dataframe(df_results)

        if backtest_date:
            win_rate = df_results['Result'].value_counts().get('✅', 0) / len(df_results) * 100
            st.metric("🏆 Backtest Win Rate", f"{win_rate:.2f}%")
        else:
            st.success(f"✅ {len(results)} stocks matched the criteria.")
    else:
        st.warning("No stocks matched the criteria.")

# Signal Log
with st.expander("📜 Show Signal Log"):
    rows = fetch_all_signals()
    if rows:
        df = pd.DataFrame(rows, columns=[
            "ID", "Symbol", "Signal Date", "Price at Signal",
            "Price+5D", "Price+10D", "Result 5D", "Result 10D",
            "Gain 5D (%)", "Gain 10D (%)"
        ])
        st.dataframe(df)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📈 5-Day Win Rate", f"{df['Result 5D'].value_counts().get('✅', 0) / len(df) * 100:.2f}%")
        with col2:
            st.metric("📈 10-Day Win Rate", f"{df['Result 10D'].value_counts().get('✅', 0) / len(df) * 100:.2f}%")
    else:
        st.info("No signals logged yet.")

# Update Past Signals
if st.button("📥 Update Prices for Signals"):
    update_signal_prices()
    st.success("✅ Prices updated for all past signals.")
