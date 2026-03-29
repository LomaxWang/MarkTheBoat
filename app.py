import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="刻舟求剑 · K线形态匹配",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@400;700&display=swap');

:root {
    --bg-primary:    #0d1117;
    --bg-secondary:  #161b22;
    --bg-card:       #21262d;
    --accent-gold:   #f0b429;
    --accent-blue:   #58a6ff;
    --accent-green:  #3fb950;
    --accent-red:    #f85149;
    --text-primary:  #e6edf3;
    --text-muted:    #8b949e;
    --border:        #30363d;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary);
}

.hero-title {
    text-align: center;
    font-family: 'Noto Serif SC', serif;
    font-size: 3rem;
    background: linear-gradient(135deg, #f0b429, #ff8c42, #f85149);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
    letter-spacing: 0.1em;
}

.hero-sub {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.95rem;
    margin-bottom: 2rem;
    letter-spacing: 0.05em;
}

section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}

.info-box {
    background: rgba(88, 166, 255, 0.08);
    border: 1px solid rgba(88, 166, 255, 0.25);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.88rem;
    line-height: 1.6;
    color: #b1c5f6;
}

.tag-badge {
    display: inline-block;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 6px;
    vertical-align: middle;
}

.tag-macd { background: rgba(177, 151, 252, 0.2); color: #b197fc; border: 1px solid #b197fc44; }
.tag-rsi  { background: rgba(63, 185, 80, 0.15);  color: #3fb950; border: 1px solid #3fb95044; }

.stProgress > div > div {
    background: linear-gradient(90deg, #f0b429, #ff8c42) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #f0b429, #ff8c42) !important;
    color: #000 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 2rem !important;
    transition: opacity 0.2s !important;
}

.stButton > button:hover { opacity: 0.88 !important; }

div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
}

div[data-testid="stMetric"] label { color: var(--text-muted) !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: var(--accent-gold) !important; }

/* Comparison section header */
.compare-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.6rem 1rem;
    background: linear-gradient(90deg, rgba(240,180,41,0.08), transparent);
    border-left: 3px solid #f0b429;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0 0.5rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #e6edf3;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
PRESETS = {
    "🥇 黄金 (GC=F)":       "GC=F",
    "🥈 白银 (SI=F)":       "SI=F",
    "🛢️ 原油 (CL=F)":       "CL=F",
    "📈 标普500 (SPY)":     "SPY",
    "💻 纳指ETF (QQQ)":     "QQQ",
    "🏦 道指ETF (DIA)":     "DIA",
    "₿  比特币 (BTC-USD)":  "BTC-USD",
    "🍎 苹果 (AAPL)":       "AAPL",
    "🎮 英伟达 (NVDA)":     "NVDA",
    "🚗 特斯拉 (TSLA)":     "TSLA",
    "🔍 谷歌 (GOOGL)":      "GOOGL",
    "📊 自定义":            "__custom__",
}

INTERVALS = {
    "4小时 (4h)": "1h",
    "日线 (1d)":  "1d",
    "周线 (1w)":  "1wk",
}

PERIOD_MAP = {
    "1h":  "2y",
    "1d":  "10y",
    "1wk": "20y",
}

LOOKBACK_DEFAULT = {
    "1h":  48,
    "1d":  60,
    "1wk": 26,
}

PLOTLY_DARK = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#e6edf3", family="Inter"),
    margin=dict(l=8, r=8, t=36, b=8),
)


# ─────────────────────────────────────────────
#  Technical indicators
# ─────────────────────────────────────────────
def compute_ema(series: np.ndarray, span: int) -> np.ndarray:
    alpha = 2.0 / (span + 1)
    ema = np.empty_like(series)
    ema[0] = series[0]
    for i in range(1, len(series)):
        ema[i] = alpha * series[i] + (1 - alpha) * ema[i - 1]
    return ema


def compute_macd(close: np.ndarray, fast=12, slow=26, signal=9):
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast   = compute_ema(close, fast)
    ema_slow   = compute_ema(close, slow)
    macd_line  = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_rsi(close: np.ndarray, period=14) -> np.ndarray:
    """Returns RSI values in [0, 100]."""
    delta  = np.diff(close, prepend=close[0])
    gains  = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)

    avg_gain = np.empty_like(close)
    avg_loss = np.empty_like(close)
    avg_gain[0] = gains[0]
    avg_loss[0] = losses[0]

    for i in range(1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i])  / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

    rs  = np.where(avg_loss < 1e-9, 100.0, avg_gain / (avg_loss + 1e-9))
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


# ─────────────────────────────────────────────
#  Data utilities
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(ticker: str, interval: str, period: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, interval=interval, period=period,
                         auto_adjust=True, progress=False)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.error(f"数据获取失败：{e}")
        return pd.DataFrame()


def resample_4h(df: pd.DataFrame) -> pd.DataFrame:
    agg = {"Open": "first", "High": "max", "Low": "min",
           "Close": "last", "Volume": "sum"}
    return df.resample("4h", closed="left", label="left").agg(agg).dropna()


def normalize_series(series: np.ndarray) -> np.ndarray:
    mu, sigma = series.mean(), series.std()
    if sigma < 1e-9:
        return series - mu
    return (series - mu) / sigma


# ─────────────────────────────────────────────
#  Feature extraction  (MACD / RSI optional)
# ─────────────────────────────────────────────
def extract_features(df_slice: pd.DataFrame,
                     use_macd: bool = False,
                     use_rsi:  bool = False) -> np.ndarray:
    """
    Feature vector per bar:
      Always:  [norm_close, return, hl_range_ratio, body_ratio]
      +MACD:   [norm_macd, norm_signal, norm_hist]
      +RSI:    [rsi/100]   (already 0-1, then normalized)
    """
    close = df_slice["Close"].values.astype(float).flatten()
    open_ = df_slice["Open"].values.astype(float).flatten()
    high  = df_slice["High"].values.astype(float).flatten()
    low   = df_slice["Low"].values.astype(float).flatten()

    norm_close = normalize_series(close)
    returns    = np.diff(close, prepend=close[0]) / (np.abs(close) + 1e-9)
    hl_range   = (high - low) / (np.abs(close) + 1e-9)
    body       = (close - open_) / (np.abs(high - low) + 1e-9)

    features = [norm_close, returns, hl_range, body]

    if use_macd:
        macd_line, sig_line, hist = compute_macd(close)
        features += [
            normalize_series(macd_line),
            normalize_series(sig_line),
            normalize_series(hist),
        ]

    if use_rsi:
        rsi = compute_rsi(close)
        features.append(normalize_series(rsi / 100.0))

    return np.column_stack(features)


# ─────────────────────────────────────────────
#  Similarity search
# ─────────────────────────────────────────────
def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    dist, _ = fastdtw(a, b, dist=euclidean)
    return dist


def pearson_distance(a: np.ndarray, b: np.ndarray) -> float:
    ca = normalize_series(a[:, 0])
    cb = normalize_series(b[:, 0])
    corr = np.corrcoef(ca, cb)[0, 1]
    return 1.0 - corr


def composite_distance(a, b, w_dtw=0.6):
    d_dtw     = dtw_distance(a, b) / len(a)
    d_pearson = pearson_distance(a, b)
    return w_dtw * d_dtw + (1 - w_dtw) * d_pearson


def search_similar(df: pd.DataFrame, window: int, top_n: int = 5,
                   use_macd: bool = False, use_rsi: bool = False,
                   w_dtw: float = 0.6, progress_cb=None):
    total = len(df)
    if total < window * 2:
        return []

    query_feat = extract_features(df.iloc[-window:], use_macd, use_rsi)

    results = []
    n_steps = total - window * 2
    if n_steps <= 0:
        return []

    for i in range(n_steps):
        hist_feat = extract_features(df.iloc[i: i + window], use_macd, use_rsi)
        dist      = composite_distance(query_feat, hist_feat, w_dtw)
        results.append({"start_idx": i, "end_idx": i + window - 1, "distance": dist})
        if progress_cb and i % max(1, n_steps // 100) == 0:
            progress_cb(i / n_steps)

    results.sort(key=lambda x: x["distance"])
    max_dist = max(r["distance"] for r in results) + 1e-9
    for r in results:
        r["similarity_pct"] = (1.0 - r["distance"] / max_dist) * 100.0
    return results[:top_n]


# ─────────────────────────────────────────────
#  Chart builders
# ─────────────────────────────────────────────
def _xidx(n):
    return list(range(n))


def candlestick_single(df_slice: pd.DataFrame, title: str,
                       color="#f0b429", height=400) -> go.Figure:
    """Simple K-line + Volume chart for a single slice."""
    o = df_slice["Open"].values.flatten()
    h = df_slice["High"].values.flatten()
    l = df_slice["Low"].values.flatten()
    c = df_slice["Close"].values.flatten()
    x = df_slice.index

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(
        x=x, open=o, high=h, low=l, close=c,
        increasing_line_color="#3fb950", decreasing_line_color="#f85149",
        increasing_fillcolor="#3fb950", decreasing_fillcolor="#f85149",
        name="K线",
    ), row=1, col=1)
    vol_colors = ["#3fb950" if cv >= ov else "#f85149" for cv, ov in zip(c, o)]
    fig.add_trace(go.Bar(
        x=x, y=df_slice["Volume"].values.flatten(),
        marker_color=vol_colors, opacity=0.55, name="成交量",
    ), row=2, col=1)
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=color)),
        xaxis_rangeslider_visible=False, showlegend=False, height=height,
        **PLOTLY_DARK,
    )
    fig.update_yaxes(gridcolor="#21262d", showgrid=True)
    return fig


def make_comparison_fig(query_df: pd.DataFrame,
                        hist_df:  pd.DataFrame,
                        use_macd: bool,
                        use_rsi:  bool,
                        query_label: str = "当前区间",
                        hist_label:  str = "历史区间") -> go.Figure:
    """
    Side-by-side comparison figure:
      Col 1 = current window | Col 2 = historical match
      Row 1 = Candlestick
      Row 2 = Volume
      Row 3 = MACD  (if use_macd)
      Row 4 = RSI   (if use_rsi)
    Both columns share the same *relative* x-axis (bar index) so shapes align.
    """
    n = min(len(query_df), len(hist_df))
    query_df = query_df.iloc[-n:]
    hist_df  = hist_df.iloc[:n]
    xi = _xidx(n)

    # Build row layout
    rows_spec = [{"type": "candlestick"}, {"type": "bar"}]
    row_heights = [0.55, 0.18]
    if use_macd:
        rows_spec.append({"type": "scatter"})
        row_heights.append(0.18)
    if use_rsi:
        rows_spec.append({"type": "scatter"})
        row_heights.append(0.18)

    n_rows = len(rows_spec)
    # Normalize heights
    total_h = sum(row_heights)
    row_heights = [h / total_h for h in row_heights]

    subplot_titles = []
    for row in range(n_rows):
        subplot_titles += [query_label, hist_label]

    # Only title the first row
    titles = [query_label, hist_label] + [""] * (2 * (n_rows - 1))

    specs = [[{"type": r["type"]}, {"type": r["type"]}] for r in rows_spec]

    fig = make_subplots(
        rows=n_rows, cols=2,
        shared_xaxes=False,
        row_heights=row_heights,
        vertical_spacing=0.04,
        horizontal_spacing=0.04,
        subplot_titles=titles,
        specs=specs,
    )

    def add_candles(df, col, name_prefix):
        o = df["Open"].values.flatten()
        h = df["High"].values.flatten()
        l = df["Low"].values.flatten()
        c = df["Close"].values.flatten()
        vol_colors = ["#3fb950" if cv >= ov else "#f85149" for cv, ov in zip(c, o)]
        color_inc = "#3fb950"
        color_dec = "#f85149"

        fig.add_trace(go.Candlestick(
            x=xi, open=o, high=h, low=l, close=c,
            increasing_line_color=color_inc, decreasing_line_color=color_dec,
            increasing_fillcolor=color_inc, decreasing_fillcolor=color_dec,
            name=name_prefix, showlegend=False,
        ), row=1, col=col)

        fig.add_trace(go.Bar(
            x=xi, y=df["Volume"].values.flatten(),
            marker_color=vol_colors, opacity=0.5,
            name="Vol", showlegend=False,
        ), row=2, col=col)

    add_candles(query_df, 1, query_label)
    add_candles(hist_df,  2, hist_label)

    current_row = 3

    if use_macd:
        for col, df_s, name_pfx, base_color in [
            (1, query_df, query_label, "#f0b429"),
            (2, hist_df,  hist_label,  "#58a6ff"),
        ]:
            close = df_s["Close"].values.astype(float).flatten()
            macd_l, sig_l, hist_v = compute_macd(close)
            hist_colors = ["#3fb950" if v >= 0 else "#f85149" for v in hist_v]
            fig.add_trace(go.Bar(
                x=xi, y=hist_v, marker_color=hist_colors,
                opacity=0.6, name="MACD柱", showlegend=False,
            ), row=current_row, col=col)
            fig.add_trace(go.Scatter(
                x=xi, y=macd_l,
                line=dict(color=base_color, width=1.5),
                name="MACD", showlegend=False,
            ), row=current_row, col=col)
            fig.add_trace(go.Scatter(
                x=xi, y=sig_l,
                line=dict(color="#ff8c42", width=1.2, dash="dot"),
                name="Signal", showlegend=False,
            ), row=current_row, col=col)
        current_row += 1

    if use_rsi:
        for col, df_s, base_color in [
            (1, query_df, "#f0b429"),
            (2, hist_df,  "#58a6ff"),
        ]:
            close = df_s["Close"].values.astype(float).flatten()
            rsi = compute_rsi(close)
            fig.add_trace(go.Scatter(
                x=xi, y=rsi,
                line=dict(color=base_color, width=1.8),
                fill="tozeroy", fillcolor=f"rgba({int(base_color[1:3],16)},"
                                            f"{int(base_color[3:5],16)},"
                                            f"{int(base_color[5:7],16)},0.08)",
                name="RSI", showlegend=False,
            ), row=current_row, col=col)
            # Overbought / oversold lines
            for lvl, lcolor in [(70, "#f85149"), (30, "#3fb950")]:
                fig.add_hline(y=lvl, line_dash="dot", line_color=lcolor,
                              line_width=1, opacity=0.6,
                              row=current_row, col=col)
        current_row += 1

    # Global layout
    total_height = 380 + (n_rows - 2) * 120
    fig.update_layout(
        height=total_height,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        **PLOTLY_DARK,
    )
    fig.update_xaxes(gridcolor="#21262d", showgrid=True, zeroline=False)
    fig.update_yaxes(gridcolor="#21262d", showgrid=True, zeroline=False)

    # Annotate RSI row
    if use_rsi:
        rsi_row = n_rows
        fig.update_yaxes(range=[0, 100], row=rsi_row, col=1)
        fig.update_yaxes(range=[0, 100], row=rsi_row, col=2)

    return fig


def overlay_normalized_fig(query_df, matches, df_full) -> go.Figure:
    fig = go.Figure()
    q_close = normalize_series(query_df["Close"].values.flatten().astype(float))
    xi = _xidx(len(q_close))
    fig.add_trace(go.Scatter(
        x=xi, y=q_close, mode="lines",
        line=dict(color="#f0b429", width=3), name="当前区间",
    ))
    palette = ["#58a6ff", "#3fb950", "#f085b1", "#ff8c42", "#b197fc",
               "#79c0ff", "#56d364", "#ffa198", "#ffa657", "#d2a8ff"]
    for rank, m in enumerate(matches):
        hs = df_full.iloc[m["start_idx"]: m["end_idx"] + 1]
        h_close = normalize_series(hs["Close"].values.flatten().astype(float))
        label = f"#{rank+1} {hs.index[0].strftime('%Y-%m-%d')}"
        fig.add_trace(go.Scatter(
            x=xi, y=h_close, mode="lines",
            line=dict(color=palette[rank % len(palette)], width=1.5, dash="dot"),
            name=label, opacity=0.85,
        ))
    fig.update_layout(
        title=dict(text="归一化收盘价对比（当前 vs 历史最相似）",
                   font=dict(size=13, color="#e6edf3")),
        height=340,
        legend=dict(bgcolor="#21262d", bordercolor="#30363d",
                    borderwidth=1, font=dict(size=11)),
        xaxis=dict(gridcolor="#21262d", showgrid=True),
        yaxis=dict(gridcolor="#21262d", showgrid=True),
        **PLOTLY_DARK,
    )
    return fig


# ─────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0;'>
        <div style='font-size:2.5rem;'>⚔️</div>
        <div style='font-family:"Noto Serif SC",serif; font-size:1.3rem;
                    background:linear-gradient(135deg,#f0b429,#ff8c42);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    font-weight:700; letter-spacing:0.15em;'>刻舟求剑</div>
        <div style='color:#8b949e; font-size:0.78rem; margin-top:4px;'>
            K线形态相似度匹配引擎
        </div>
    </div>
    <hr style='border-color:#30363d; margin: 0.5rem 0 1rem;'/>
    """, unsafe_allow_html=True)

    # ── 标的
    st.markdown("#### 📊 标的")
    preset_label = st.selectbox("选择标的", list(PRESETS.keys()), index=0,
                                label_visibility="collapsed")
    ticker_sym = PRESETS[preset_label]
    if ticker_sym == "__custom__":
        ticker_sym = st.text_input("Yahoo Finance 代码", value="GC=F",
                                   placeholder="如 AAPL, BTC-USD, 0700.HK")

    # ── 周期
    st.markdown("#### ⏱ 周期")
    interval_label = st.selectbox("K线周期", list(INTERVALS.keys()), index=1,
                                  label_visibility="collapsed")
    interval_code = INTERVALS[interval_label]

    # ── 窗口
    st.markdown("#### 📐 窗口大小（根数）")
    win_default = LOOKBACK_DEFAULT.get(interval_code, 60)
    window_size = st.slider("", min_value=10, max_value=200,
                             value=win_default, step=5,
                             label_visibility="collapsed")

    # 实时换算对应时间跨度
    _hours_per_bar = {"1h": 4, "1d": 24, "1wk": 24 * 7}
    _total_hours   = window_size * _hours_per_bar.get(interval_code, 24)
    _total_days    = int(_total_hours // 24)
    _rem_hours     = int(_total_hours % 24)

    if _total_days > 0 and _rem_hours > 0:
        _span_str = f"{_total_days} 天 {_rem_hours} 小时"
    elif _total_days > 0:
        _span_str = f"{_total_days} 天"
    else:
        _span_str = f"{_rem_hours} 小时"

    st.markdown(
        f'<div style="margin-top:-8px; margin-bottom:6px; padding:6px 10px;'
        f'background:rgba(240,180,41,0.08); border-radius:6px;'
        f'border-left:3px solid #f0b429; font-size:0.82rem; color:#c9a227;">'
        f'⏳ &nbsp;约 <b style="font-size:1rem; color:#f0b429;">{_span_str}</b>'
        f'&nbsp;·&nbsp;共 <b>{_total_hours:,}</b> 小时'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Top N
    st.markdown("#### 🏆 返回最相似区间数")
    top_n = st.slider("", min_value=1, max_value=10, value=3,
                       label_visibility="collapsed")

    # ── DTW 权重
    st.markdown("#### ⚙️ DTW 权重（余量为 Pearson）")
    w_dtw = st.slider("", min_value=0.0, max_value=1.0, value=0.6, step=0.05,
                       label_visibility="collapsed")

    # ────────────────────────────────
    # ★ 技术指标参与匹配
    # ────────────────────────────────
    st.markdown("""
    <hr style='border-color:#30363d; margin: 0.8rem 0;'/>
    <div style='color:#e6edf3; font-size:0.9rem; font-weight:600; margin-bottom:0.5rem;'>
        🔬 技术指标参与匹配
    </div>
    <div style='color:#8b949e; font-size:0.76rem; margin-bottom:0.6rem; line-height:1.5;'>
        开启后，对应指标将加入特征向量，<br>影响相似度计算与对比图显示。
    </div>
    """, unsafe_allow_html=True)

    use_macd = st.checkbox("📊 MACD（快12 慢26 信号9）", value=False)
    use_rsi  = st.checkbox("📉 RSI（周期14）",           value=False)

    if use_macd or use_rsi:
        tags = []
        if use_macd: tags.append('<span class="tag-badge tag-macd">MACD ✓</span>')
        if use_rsi:  tags.append('<span class="tag-badge tag-rsi">RSI ✓</span>')
        st.markdown(
            f'<div style="margin-top:4px;">{"".join(tags)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color:#30363d; margin: 0.8rem 0;'/>",
                unsafe_allow_html=True)

    run_btn = st.button("🔍  开始匹配", use_container_width=True)

    # 算法说明
    indicator_note = ""
    if use_macd:
        indicator_note += "• <b>MACD</b>：DIF/DEA/柱，捕捉动量趋势相似性<br>"
    if use_rsi:
        indicator_note += "• <b>RSI(14)</b>：超买超卖位置相似性<br>"

    st.markdown(f"""
    <div style='color:#8b949e; font-size:0.75rem; line-height:1.7;'>
    <b style='color:#e6edf3;'>算法说明</b><br>
    • <b>基础特征</b>：归一化收盘价、涨跌幅、振幅、实体比<br>
    {indicator_note}• <b>DTW</b>：动态时间规整（形态弹性匹配）<br>
    • <b>Pearson</b>：收盘价方向相关性<br>
    • <b>数据源</b>：Yahoo Finance
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Main content
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">刻舟求剑</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">在历史长河中寻觅当下的倒影 · K线形态相似度匹配引擎</div>',
            unsafe_allow_html=True)

indicator_tags = ""
if use_macd:
    indicator_tags += '<span class="tag-badge tag-macd">MACD 已启用</span>'
if use_rsi:
    indicator_tags += '<span class="tag-badge tag-rsi">RSI 已启用</span>'

st.markdown(f"""
<div class="info-box">
⚡ <b>使用方法</b>：在左侧配置参数后点击「开始匹配」。系统将在历史数据中搜索与
<b>最近 {window_size} 根 K 线</b>形态最相似的历史区间，并展示
<b>当前区间 vs 历史区间</b>的并排对比图（含成交量
{"、MACD" if use_macd else ""}{"、RSI" if use_rsi else ""}）。{indicator_tags}
</div>
""", unsafe_allow_html=True)

if not run_btn:
    st.markdown("""
    <div style='text-align:center; padding: 5rem 2rem;'>
        <div style='font-size:5rem;'>⚔️</div>
        <div style='font-size:1.2rem; margin-top:1rem; font-family:"Noto Serif SC",serif;
                    color: #484f58;'>
            刻舟以记剑落之处，求历史中相似的涟漪
        </div>
        <div style='font-size:0.85rem; color: #30363d; margin-top:0.5rem;'>
            配置好参数后点击左侧「开始匹配」按钮
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─── Fetch data
with st.spinner(f"正在获取 {ticker_sym} 数据…"):
    period = PERIOD_MAP.get(interval_code, "10y")
    if interval_code == "1h":
        raw = fetch_data(ticker_sym, "1h", "2y")
        if raw.empty:
            st.error("❌ 数据为空，请检查标的代码或网络连接。")
            st.stop()
        df = resample_4h(raw)
    else:
        df = fetch_data(ticker_sym, interval_code, period)
        if df.empty:
            st.error("❌ 数据为空，请检查标的代码或网络连接。")
            st.stop()

if len(df) < window_size * 2:
    st.error(f"❌ 数据量不足（{len(df)} 根 K 线），请减小窗口大小。")
    st.stop()

# ─── Summary metrics
c1, c2, c3, c4 = st.columns(4)
last_close  = float(df["Close"].iloc[-1])
first_close = float(df["Close"].iloc[0])
total_ret   = (last_close - first_close) / first_close * 100
with c1: st.metric("📅 数据根数",  f"{len(df):,}")
with c2: st.metric("📆 起止时间",
                   f"{df.index[0].strftime('%Y-%m')} → {df.index[-1].strftime('%Y-%m')}")
with c3: st.metric("💰 最新收盘",  f"{last_close:,.4g}")
with c4: st.metric("📈 区间涨跌",  f"{total_ret:+.1f}%")

st.divider()

# ─── Current window chart
st.markdown(f"### 📌 当前匹配窗口（最近 {window_size} 根 K 线）")
query_df = df.iloc[-window_size:]
fig_query = candlestick_single(query_df, f"{ticker_sym} · 当前区间 ({interval_label})")
st.plotly_chart(fig_query, use_container_width=True)

# ─── Search
st.markdown("### 🔍 历史相似区间搜索")
progress_bar = st.progress(0, text="正在扫描历史数据…")

def update_progress(pct: float):
    progress_bar.progress(min(pct, 0.99), text=f"已扫描 {pct*100:.0f}%…")

with st.spinner(""):
    matches = search_similar(
        df, window_size, top_n=top_n,
        use_macd=use_macd, use_rsi=use_rsi,
        w_dtw=w_dtw, progress_cb=update_progress,
    )

progress_bar.progress(1.0, text="✅ 搜索完成！")

if not matches:
    st.error("未找到匹配结果，请调整参数重试。")
    st.stop()

# ─── Global overlay chart
st.markdown("### 📊 全局归一化形态对比")
fig_overlay = overlay_normalized_fig(query_df, matches, df)
st.plotly_chart(fig_overlay, use_container_width=True)

# ─── Individual match results
st.markdown(f"### 🏆 Top {top_n} 最相似历史区间")
medal = ["🥇", "🥈", "🥉"] + ["🔹"] * 7

for rank, m in enumerate(matches):
    hist_slice = df.iloc[m["start_idx"]: m["end_idx"] + 1]
    sim_pct    = m["similarity_pct"]
    dist       = m["distance"]
    start_dt   = hist_slice.index[0].strftime("%Y-%m-%d")
    end_dt     = hist_slice.index[-1].strftime("%Y-%m-%d")

    h_start = float(hist_slice["Close"].iloc[0])
    h_end   = float(hist_slice["Close"].iloc[-1])
    h_ret   = (h_end - h_start) / h_start * 100

    with st.expander(
        f"{medal[rank]}  #{rank+1}  {start_dt} → {end_dt}  "
        f"｜相似度 {sim_pct:.1f}%  "
        f"{'📈' if h_ret >= 0 else '📉'} 区间涨跌 {h_ret:+.2f}%",
        expanded=(rank == 0),
    ):
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1: st.metric("相似度",    f"{sim_pct:.2f}%")
        with cc2: st.metric("DTW 距离",  f"{dist:.4f}")
        with cc3: st.metric("区间回报",  f"{h_ret:+.2f}%")
        with cc4:
            q_start = float(query_df["Close"].iloc[0])
            q_end   = float(query_df["Close"].iloc[-1])
            q_ret   = (q_end - q_start) / q_start * 100
            st.metric("当前窗口涨跌", f"{q_ret:+.2f}%")

        # ══════════════════════════════════════════
        #  ★ 当前区间 vs 历史区间 并排对比图
        # ══════════════════════════════════════════
        _macd_tag = '<span class="tag-badge tag-macd">MACD</span>' if use_macd else ''
        _rsi_tag  = '<span class="tag-badge tag-rsi">RSI</span>'  if use_rsi  else ''
        st.markdown(
            f'<div class="compare-header">'
            f'🔄 并排对比：当前区间 vs 历史区间 #{rank+1}&nbsp;&nbsp;{_macd_tag}{_rsi_tag}'
            f'</div>',
            unsafe_allow_html=True,
        )
        fig_cmp = make_comparison_fig(
            query_df, hist_slice,
            use_macd=use_macd, use_rsi=use_rsi,
            query_label=f"当前 ({query_df.index[0].strftime('%Y-%m-%d')}→{query_df.index[-1].strftime('%Y-%m-%d')})",
            hist_label=f"历史#{rank+1} ({start_dt}→{end_dt})",
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # ── 历史区间后续走势
        after_end = m["end_idx"] + window_size
        if after_end <= len(df) - 1:
            after_slice = df.iloc[m["end_idx"] + 1: after_end + 1]
            if not after_slice.empty:
                st.markdown(
                    f"**⏩ 历史区间 #{rank+1} 结束后 {len(after_slice)} 根 K 线走势（参考）：**"
                )
                fig_after = candlestick_single(
                    after_slice,
                    f"历史续航 #{rank+1} · "
                    f"{after_slice.index[0].strftime('%Y-%m-%d')} → "
                    f"{after_slice.index[-1].strftime('%Y-%m-%d')}",
                    color="#3fb950",
                )
                st.plotly_chart(fig_after, use_container_width=True)
        else:
            st.info("该历史区间紧邻当前时间，后续走势暂无历史数据。")

st.divider()
st.markdown("""
<div style='text-align:center; color:#484f58; font-size:0.8rem; padding:1rem 0;'>
⚠️ 本工具仅供学习研究，历史形态相似不构成任何投资建议。<br>
刻舟求剑 · 以史为鉴，知兴替。
</div>
""", unsafe_allow_html=True)
