import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_daily_data(symbol: str, period: str = "3mo") -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, interval='1d')
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # Strip timezone globally
        return df
    except Exception as e:
        print(f"Failed to fetch daily data for {symbol}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_weekly_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, interval='1wk')
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # Strip timezone globally
        return df
    except Exception as e:
        print(f"Failed to fetch weekly data for {symbol}: {e}")
        return pd.DataFrame()


def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate MACD indicators on the DataFrame.
    """
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    return df


def detect_macd_cross(df: pd.DataFrame) -> bool:
    """
    Detect if a bullish MACD crossover occurred in the last bar.
    """
    if len(df) < 2:
        return False
    prev_row = df.iloc[-2]
    last_row = df.iloc[-1]
    return prev_row['MACD'] < prev_row['Signal'] and last_row['MACD'] > last_row['Signal']


def load_group_symbols(group_name: str) -> list:
    """
    Load symbol list from CSV based on NSE group.
    """
    file_map = {
        "Nifty 50": "data/ind_nifty50list.csv",
        "Nifty 500": "data/ind_nifty500list.csv",
        "Midcap 100": "data/ind_niftysmallcap100list.csv",
        "Smallcap 250": "data/ind_niftysmallcap250list.csv"
    }
    try:
        df = pd.read_csv(file_map[group_name])
        df.columns = df.columns.str.strip()
        symbols = df['Symbol'].dropna().str.strip().str.upper().tolist()
        return [f"{symbol}.NS" for symbol in symbols]
    except Exception as e:
        print(f"Error loading {group_name}: {e}")
        return []


def update_signal_prices():
    from db import update_price
    from datetime import datetime, timedelta
    import yfinance as yf
    import sqlite3
    import pandas as pd

    conn = sqlite3.connect("macd_results.db")
    cursor = conn.execute("SELECT symbol, signal_date FROM macd_signals")
    today = datetime.now().date()

    for symbol, signal_date in cursor.fetchall():
        d = datetime.fromisoformat(signal_date).date()
        diff = (today - d).days

        df = yf.Ticker(symbol).history(period="15d", interval="1d").reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.date

        price_5d = df[df['Date'] == d + timedelta(days=5)]['Close'].values
        price_10d = df[df['Date'] == d + timedelta(days=10)]['Close'].values

        update_price(symbol, signal_date,
                     price_after_5d=price_5d[0] if len(price_5d) > 0 else None,
                     price_after_10d=price_10d[0] if len(price_10d) > 0 else None)

    conn.close()


