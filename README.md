# 📈 Technical Signal Scanner

A powerful and extensible **NSE stock scanning tool** built with **Streamlit**, allowing traders and analysts to detect technical trading signals across selected stock groups using popular strategies like MACD, RSI, Bollinger Bands, and custom EMA-based filters.

---

## 🚀 Features

- 🔍 **Scan NSE Groups**: Nifty 50, Nifty 500, Midcap 100, Smallcap 250
- 📊 **Multiple Strategies Supported**:
  - MACD Bullish Crossover
  - Price Crosses Above 200 EMA
  - RSI Oversold Reversal
  - Bollinger Band Breakout
  - Gate – 4 EMA Tight Range (2–3%)
- ⏱️ Choose **data interval**: Weekly or Daily
- 📅 **Backtest Mode**: Run historical scans based on selected date
- 🧠 Stores all signals in local database (`SQLite`)
- 📈 Automatically tracks **5-day & 10-day** price performance
- 📉 Calculates **win rates** based on past performance
- 📌 Links to TradingView for each detected stock

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/technical-signal-scanner.git
   cd technical-signal-scanner
   pip install -r requirements.txt
