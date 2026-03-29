<div align="center">

# ⚔️ MarkTheBoat

**Candlestick Pattern Similarity Matching Engine**

*Find historical echoes of current price patterns*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[中文文档](README.md)** · **[English](README.en.md)**

</div>

---

## 📖 About

**MarkTheBoat** is a dual-factor candlestick pattern matching tool powered by **DTW (Dynamic Time Warping)** and **Pearson Correlation**.

The name comes from the Chinese idiom *刻舟求剑* (kè zhōu qiú jiàn) — "marking the boat to find the sword" — a parable about someone who marks the spot on a boat where their sword fell into the river, then tries to retrieve it after the boat has moved. It's used to describe rigid, backward-looking thinking.

Here, we use it ironically: knowing full well that history never repeats exactly, we still search for its echoes.

Select an asset (gold, US stocks, crypto, etc.) and a timeframe. The engine slides across years of historical data to find the **N most similar historical windows** to the current period — then shows you what happened next.

> ⚠️ **Disclaimer**: This tool is for educational and research purposes only. Historical pattern similarity does not constitute investment advice.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-asset** | Gold, Silver, Oil, S&P 500, Nasdaq, Bitcoin, Apple, Nvidia, etc. Supports any Yahoo Finance ticker |
| ⏱ **Multi-timeframe** | 4-hour (4h), Daily (1d), Weekly (1w) |
| 🧠 **Dual-factor algorithm** | DTW (flexible shape matching) + Pearson (directional correlation), with adjustable weighting |
| 🔬 **Optional indicators** | Enable MACD (12/26/9) and/or RSI (14) to be included in the feature vector |
| 📊 **Side-by-side comparison** | Each match shows a synchronized current vs. historical chart with K-lines, volume, and optional MACD / RSI panels |
| ⏩ **Post-match projection** | Automatically displays the price action that followed each historical match |
| ⏳ **Window time display** | Real-time conversion of bar count to days and hours |
| 🎨 **Dark UI** | Plotly + Streamlit, dark theme, smooth interactions |

---

## 🖼 Preview

```
Sidebar                         Main Area
┌──────────────────┐    ┌─────────────────────────────────┐
│ ⚔️ MarkTheBoat   │    │        ⚔️ MarkTheBoat            │
│                  │    │  Find historical echoes...       │
│ 📊 Asset         │    │                                  │
│  [Gold GC=F ▼]   │    │  📌 Current Window (60 bars)     │
│                  │    │  [Candlestick + Volume]           │
│ ⏱ Timeframe      │    │                                  │
│  [Daily 1d ▼]    │    │  📊 Normalized Shape Overlay      │
│                  │    │  [Current vs Top N historical]    │
│ 📐 Window Size   │    │                                  │
│  [━━●━━━] 60    │    │  🏆 Top 3 Similar Periods         │
│  ⏳ ~60 days     │    │  ├ 🥇 #1 2016-12-20 → ...        │
│                  │    │  │   [Side-by-side: K + MACD/RSI] │
│ 🔬 Indicators    │    │  │   [Post-match projection]      │
│  ☑ MACD          │    │  ├ 🥈 #2 ...                     │
│  ☑ RSI           │    │  └ 🥉 #3 ...                     │
│                  │    └─────────────────────────────────┘
│ [🔍 Find Match]  │
└──────────────────┘
```

---

## 🚀 Quick Start

### Option 1: One-click script (recommended)

```bash
# Clone the repo
git clone https://github.com/LomaxWang/MarkTheBoat.git
cd MarkTheBoat

# Grant execute permission and run (auto-installs dependencies)
chmod +x run.sh
./run.sh
```

The script will: detect Python → install dependencies → launch Streamlit → open your browser.

---

### Option 2: Manual setup

```bash
# Clone the repo
git clone https://github.com/LomaxWang/MarkTheBoat.git
cd MarkTheBoat

# Install dependencies
pip install -r requirements.txt

# Launch
streamlit run app.py
```

Then visit [http://localhost:8501](http://localhost:8501).

---

### Requirements

| Dependency | Version |
|------------|---------|
| Python | ≥ 3.9 |
| streamlit | ≥ 1.33.0 |
| yfinance | ≥ 0.2.40 |
| pandas | ≥ 2.0.0 |
| numpy | ≥ 1.26.0 |
| plotly | ≥ 5.18.0 |
| scipy | ≥ 1.11.0 |
| fastdtw | ≥ 0.3.4 |

---

## 🧠 How It Works

### Feature Vector

For each candlestick bar, the following features are extracted and stacked into a multi-dimensional time series:

| Feature | Calculation | Purpose |
|---------|-------------|---------|
| Normalized close | z-score standardization | Removes absolute price differences, preserves shape |
| Return | `Δclose / close` | Captures momentum direction |
| Range ratio | `(high - low) / close` | Reflects volatility intensity |
| Body ratio | `(close - open) / (high - low)` | Distinguishes bull/bear candle strength |
| MACD lines (optional) | DIF / DEA / Histogram, normalized | Momentum trend similarity |
| RSI (optional) | RSI(14) / 100, normalized | Overbought/oversold position alignment |

### Similarity Score

```
Composite Distance = w_DTW × (DTW Distance / window_length)
                   + (1 - w_DTW) × (1 - Pearson Correlation)
```

- **DTW**: Allows elastic time-axis warping — robust to patterns with different speeds or rhythms
- **Pearson**: Measures linear directional correlation of normalized closes
- **Adjustable weighting**: Default DTW weight = 0.6; tunable via sidebar slider

### Search Process

```
Historical data                              Query window
|----[window]----[window]----[window]----[  QUERY  ]|
       ↑              ↑              ↑
  compute dist    compute dist   compute dist
                       ↓
              sort by distance → return Top N
```

A sliding window scans all historical positions (excluding the query window itself), computes the composite distance to the current window, and returns the Top N closest matches.

---

## 📁 Project Structure

```
MarkTheBoat/
├── app.py            # Main app (Streamlit UI + matching engine)
├── requirements.txt  # Python dependencies
├── run.sh            # One-click launch script
├── README.md         # Chinese documentation
├── README.en.md      # English documentation (this file)
└── LICENSE           # MIT License
```

---

## 🗺 Supported Assets

Any [Yahoo Finance](https://finance.yahoo.com) ticker is supported. Built-in presets:

| Category | Assets |
|----------|--------|
| Precious Metals | Gold `GC=F`, Silver `SI=F` |
| Energy | Crude Oil `CL=F` |
| US ETFs | S&P 500 `SPY`, Nasdaq `QQQ`, Dow Jones `DIA` |
| Crypto | Bitcoin `BTC-USD` |
| US Stocks | Apple `AAPL`, Nvidia `NVDA`, Tesla `TSLA`, Google `GOOGL` |
| HK Stocks | Tencent `0700.HK` (via custom input) |
| Custom | Any Yahoo Finance ticker symbol |

---

## ⚙️ Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Asset | Gold GC=F | Target financial instrument |
| Timeframe | Daily 1d | Bar granularity: 4h / 1d / 1w |
| Window size | 60 bars | Number of bars to match |
| Top N results | 3 | Number of best matches to return |
| DTW weight | 0.6 | DTW's share in composite distance |
| MACD | Off | Include MACD in feature vector |
| RSI | Off | Include RSI in feature vector |

---

## 🤝 Contributing

Issues and pull requests are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feat/your-feature`
5. Open a Pull Request

---

## 📄 License

[MIT License](LICENSE) © 2026 [LomaxWang](https://github.com/LomaxWang)

---

<div align="center">

**MarkTheBoat · Those who know history are condemned to repeat it anyway**

*For educational and research purposes only. Not financial advice.*

</div>
