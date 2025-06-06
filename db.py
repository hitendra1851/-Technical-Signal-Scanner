import sqlite3
import os
from datetime import datetime, timedelta
import yfinance as yf

DB_FILE = "signals.db"

def create_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            signal_date TEXT NOT NULL,
            price_at_signal REAL NOT NULL,
            price_5d REAL,
            price_10d REAL,
            result_5d TEXT,
            result_10d TEXT,
            gain_5d REAL,
            gain_10d REAL,
            UNIQUE(symbol, signal_date)
        )
    """)
    conn.commit()
    conn.close()

def insert_signal(symbol: str, price: float):
    signal_date = datetime.now().strftime('%Y-%m-%d')
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO signals (symbol, signal_date, price_at_signal)
            VALUES (?, ?, ?)
        """, (symbol, signal_date, price))
        conn.commit()
    except Exception as e:
        print(f"Insert error: {e}")
    finally:
        conn.close()

def fetch_all_signals():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY signal_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_signal_prices():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, symbol, signal_date, price_at_signal FROM signals WHERE price_5d IS NULL OR price_10d IS NULL")
    rows = cursor.fetchall()

    for row in rows:
        signal_id, symbol, signal_date, price_at_signal = row
        try:
            df = yf.Ticker(symbol).history(start=signal_date, interval='1d')
            df = df[df.index > signal_date]  # only future prices

            if len(df) >= 5:
                price_5d = df.iloc[4]['Close']
                gain_5d = ((price_5d - price_at_signal) / price_at_signal) * 100
                result_5d = '✅' if gain_5d > 0 else '❌'
            else:
                price_5d = gain_5d = result_5d = None

            if len(df) >= 10:
                price_10d = df.iloc[9]['Close']
                gain_10d = ((price_10d - price_at_signal) / price_at_signal) * 100
                result_10d = '✅' if gain_10d > 0 else '❌'
            else:
                price_10d = gain_10d = result_10d = None

            cursor.execute("""
                UPDATE signals
                SET price_5d=?, gain_5d=?, result_5d=?,
                    price_10d=?, gain_10d=?, result_10d=?
                WHERE id=?
            """, (price_5d, gain_5d, result_5d,
                  price_10d, gain_10d, result_10d, signal_id))

            conn.commit()
        except Exception as e:
            print(f"Update failed for {symbol}: {e}")

    conn.close()
