import pandas as pd
import yfinance as yf
import streamlit as st
import requests
from io import StringIO


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


def load_group_symbols(market, group_option):
    if market == "India":
        group_map = {
            "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
            "Nifty Next 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
            "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "Nifty 200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            "Small cap 50": "https://archives.nseindia.com/content/indices/ind_smallcap50list.csv",
            "Small cap 100": "https://archives.nseindia.com/content/indices/ind_smallcap100list.csv",
            "Small cap 250": "https://archives.nseindia.com/content/indices/ind_smallcap250list.csv",
            "Mid cap 50": "https://archives.nseindia.com/content/indices/ind_midcap50list.csv",
            "Mid cap 100": "https://archives.nseindia.com/content/indices/ind_midcap100list.csv",
            "Mid cap 150": "https://archives.nseindia.com/content/indices/ind_midcap150list.csv"
        }

        if group_option in group_map:
            df = pd.read_csv(group_map[group_option])
            return [symbol + ".NS" for symbol in df["Symbol"].tolist()]
        else:
            return []

    elif market == "USA" and group_option == "ALL USA Stocks":
        return [
            "MMM", "ABT", "ABBV", "ABMD", "ACN", "ATVI", "ADBE", "AMD", "AAP", "AES", "AFL", "A", "APD", "AKAM",
            "ALK", "ALB", "ARE", "ALXN", "ALGN", "ALLE", "AGN", "ADS", "LNT", "ALL", "GOOGL", "GOOG", "MO", "AMZN",
            "AMCR", "AEE", "AAL", "AEP", "AXP", "AIG", "AMT", "AWK", "AMP", "ABC", "AME", "AMGN", "APH", "ADI",
            "ANSS", "ANTM", "AON", "AOS", "APA", "AIV", "AAPL", "AMAT", "APTV", "ADM", "ARNC", "ANET", "AJG",
            "AIZ", "ATO", "T", "ADSK", "ADP", "AZO", "AVB", "AVY", "BKR", "BLL", "BAC", "BK", "BAX", "BDX", "BRK.B",
            "BBY", "BIIB", "BLK", "BA", "BKNG", "BWA", "BXP", "BSX", "BMY", "AVGO", "BR", "BF.B", "CHRW", "COG",
            "CDNS", "CPB", "COF", "CPRI", "CAH", "KMX", "CCL", "CAT", "CBOE", "CBRE", "CDW", "CE", "CNC", "CNP",
            "CTL", "CERN", "CF", "SCHW", "CHTR", "CVX", "CMG", "CB", "CHD", "CI", "XEC", "CINF", "CTAS", "CSCO",
            "C", "CFG", "CTXS", "CLX", "CME", "CMS", "KO", "CTSH", "CL", "CMCSA", "CMA", "CAG", "CXO", "COP", "ED",
            "STZ", "COO", "CPRT", "GLW", "CTVA", "COST", "COTY", "CCI", "CSX", "CMI", "CVS", "DHI", "DHR", "DRI",
            "DVA", "DE", "DAL", "XRAY", "DVN", "FANG", "DLR", "DFS", "DISCA", "DISCK", "DISH", "DG", "DLTR", "D",
            "DOV", "DOW", "DTE", "DUK", "DRE", "DD", "DXC", "ETFC", "EMN", "ETN", "EBAY", "ECL", "EIX", "EW", "EA",
            "EMR", "ETR", "EOG", "EFX", "EQIX", "EQR", "ESS", "EL", "EVRG", "ES", "RE", "EXC", "EXPE", "EXPD",
            "EXR", "XOM", "FFIV", "FB", "FAST", "FRT", "FDX", "FIS", "FITB", "FE", "FRC", "FISV", "FLT", "FLIR",
            "FLS", "FMC", "F", "FTNT", "FTV", "FBHS", "FOXA", "FOX", "BEN", "FCX", "GPS", "GRMN", "IT", "GD", "GE",
            "GIS", "GM", "GPC", "GILD", "GL", "GPN", "GS", "GWW", "HRB", "HAL", "HBI", "HOG", "HIG", "HAS", "HCA",
            "PEAK", "HP", "HSIC", "HSY", "HES", "HPE", "HLT", "HFC", "HOLX", "HD", "HON", "HRL", "HST", "HPQ",
            "HUM", "HBAN", "HII", "IEX", "IDXX", "INFO", "ITW", "ILMN", "IR", "INTC", "ICE", "IBM", "INCY", "IP",
            "IPG", "IFF", "INTU", "ISRG", "IVZ", "IPGP", "IQV", "IRM", "JKHY", "J", "JBHT", "SJM", "JNJ", "JCI",
            "JPM", "JNPR", "KSU", "K", "KEY", "KEYS", "KMB", "KIM", "KMI", "KLAC", "KSS", "KHC", "KR", "LB", "LHX",
            "LH", "LRCX", "LW", "LVS", "LEG", "LDOS", "LEN", "LLY", "LNC", "LIN", "LYV", "LKQ", "LMT", "L", "LOW",
            "LYB", "MTB", "M", "MRO", "MPC", "MKTX", "MAR", "MMC", "MLM", "MAS", "MA", "MKC", "MXIM", "MCD", "MCK",
            "MDT", "MRK", "MET", "MTD", "MGM", "MCHP", "MU", "MSFT", "MAA", "MHK", "TAP", "MDLZ", "MNST", "MCO",
            "MS", "MOS", "MSI", "MSCI", "MYL", "NDAQ", "NOV", "NTAP", "NFLX", "NWL", "NEM", "NWSA", "NWS", "NEE",
            "NLSN", "NKE", "NI", "NBL", "JWN", "NSC", "NTRS", "NOC", "NLOK", "NCLH", "NRG", "NUE", "NVDA", "NVR",
            "ORLY", "OXY", "ODFL", "OMC", "OKE", "ORCL", "PCAR", "PKG", "PH", "PAYX", "PYPL", "PNR", "PBCT", "PEP",
            "PKI", "PRGO", "PFE", "PM", "PSX", "PNW", "PXD", "PNC", "PPG", "PPL", "PFG", "PG", "PGR", "PLD", "PRU",
            "PEG", "PSA", "PHM", "PVH", "QRVO", "PWR", "QCOM", "DGX", "RL", "RJF", "RTN", "O", "REG", "REGN", "RF",
            "RSG", "RMD", "RHI", "ROK", "ROL", "ROP", "ROST", "RCL", "SPGI", "CRM", "SBAC", "SLB", "STX", "SEE",
            "SRE", "NOW", "SHW", "SPG", "SWKS", "SLG", "SNA", "SO", "LUV", "SWK", "SBUX", "STT", "STE", "SYK",
            "SIVB", "SYF", "SNPS", "SYY", "TMUS", "TROW", "TTWO", "TPR", "TGT", "TEL", "FTI", "TFX", "TXN", "TXT",
            "TMO", "TIF", "TJX", "TSCO", "TDG", "TRV", "TFC", "TWTR", "TSN", "UDR", "ULTA", "USB", "UAA", "UA",
            "UNP", "UAL", "UNH", "UPS", "URI", "UTX", "UHS", "UNM", "VFC", "VLO", "VAR", "VTR", "VRSN", "VRSK",
            "VZ", "VRTX", "VIAC", "V", "VNO", "VMC", "WRB", "WAB", "WMT", "WBA", "DIS", "WM", "WAT", "WEC", "WCG",
            "WFC", "WELL", "WDC", "WU", "WRK", "WY", "WHR", "WMB", "WLTW", "WYNN", "XEL", "XRX", "XLNX", "XYL",
            "YUM", "ZBRA", "ZBH", "ZION", "ZTS"
        ]
    else:
        return []


def load_nse_csv_symbols(url: str, symbol_column_name: str = 'Symbol') -> list:
    """
    Loads NSE CSV from given URL and extracts the symbol list.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        df.columns = df.columns.str.strip()
        symbols = df[symbol_column_name].dropna().str.strip().str.upper().tolist()
        return symbols
    except Exception as e:
        print(f"Failed to load symbols from {url}: {e}")
        return []


def update_signal_prices():
    from db import update_price
    from datetime import datetime, timedelta
    import yfinance as yf
    import sqlite3
    import pandas as pd

    conn = sqlite3.connect("signals.db")
    cursor = conn.execute("SELECT symbol, signal_date FROM signals")
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
