<div align="center">

# ⚔️ 刻舟求剑 MarkTheBoat

**K线形态相似度匹配引擎**

*在历史长河中寻觅当下的倒影*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📖 项目简介

「刻舟求剑」是一个基于 **DTW（动态时间规整）** 与 **Pearson 相关性** 的双因子 K 线形态匹配工具。

你只需选择标的（黄金、美股、加密货币等）和 K 线周期，系统便会在数年历史数据中滑动搜寻，找出与**当前最近 N 根 K 线**形态最相似的历史区间，并同步展示那段历史之后的走势，供参考对比。

> ⚠️ **免责声明**：本工具仅供学习与研究，历史形态相似不构成任何投资建议。

---

## ✨ 功能特性

| 功能                         | 说明                                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| 🌍**多标的支持**       | 黄金、白银、原油、标普500、纳指、比特币、苹果、英伟达等，支持自定义 Yahoo Finance 代码  |
| ⏱**多周期**           | 4小时（4h）、日线（1d）、周线（1w）                                                     |
| 🧠**双因子算法**       | DTW（形态弹性匹配）+ Pearson（方向相关性），可自由调整权重                              |
| 🔬**技术指标参与匹配** | 可选开启 MACD（12/26/9）和 RSI（14）加入特征向量                                        |
| 📊**并排对比图**       | 每个匹配结果展示「当前区间 vs 历史区间」并排图表，含 K 线、成交量、可选 MACD / RSI 面板 |
| ⏩**历史续航展示**     | 自动展示历史匹配区间结束后的后续走势                                                    |
| ⏳**窗口时间换算**     | 根据所选周期实时显示窗口对应的天数和小时数                                              |
| 🎨**暗色 UI**          | 基于 Plotly + Streamlit，深色主题，交互流畅                                             |

---

## 🖼 界面预览

```
侧边栏                          主区域
┌──────────────────┐    ┌─────────────────────────────────┐
│ ⚔️ 刻舟求剑       │    │        ⚔️ 刻舟求剑               │
│                  │    │  在历史长河中寻觅当下的倒影        │
│ 📊 标的           │    │                                  │
│  [黄金 GC=F ▼]   │    │  📌 当前匹配窗口（60根K线）        │
│                  │    │  [K线图 + 成交量]                 │
│ ⏱ 周期           │    │                                  │
│  [日线 1d ▼]     │    │  📊 归一化形态对比                 │
│                  │    │  [当前 vs Top N 历史折线]          │
│ 📐 窗口大小       │    │                                  │
│  [━━●━━━] 60    │    │  🏆 Top 3 最相似历史区间           │
│  ⏳ 约 60 天      │    │  ├ 🥇 #1 2016-12-20 → ...       │
│                  │    │  │   [并排对比图: K线+MACD+RSI]   │
│ 🔬 技术指标       │    │  │   [历史续航走势]               │
│  ☑ MACD          │    │  ├ 🥈 #2 ...                     │
│  ☑ RSI           │    │  └ 🥉 #3 ...                     │
│                  │    └─────────────────────────────────┘
│ [🔍 开始匹配]    │
└──────────────────┘
```

---

## 🚀 快速开始

### 方式一：一键启动脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/LomaxWang/MarkTheBoat.git
cd MarkTheBoat
chmod +x run.sh
./run.sh
```

脚本会自动完成：检测 Python → 安装依赖 → 启动 Streamlit → 打开浏览器。

---

### 方式二：手动安装

```bash
# 1. 克隆项目
git clone https://github.com/LomaxWang/MarkTheBoat.git
cd MarkTheBoat

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
streamlit run app.py
```

访问 [http://localhost:8501](http://localhost:8501)

---

### 环境要求

| 依赖      | 版本      |
| --------- | --------- |
| Python    | ≥ 3.9    |
| streamlit | ≥ 1.33.0 |
| yfinance  | ≥ 0.2.40 |
| pandas    | ≥ 2.0.0  |
| numpy     | ≥ 1.26.0 |
| plotly    | ≥ 5.18.0 |
| scipy     | ≥ 1.11.0 |
| fastdtw   | ≥ 0.3.4  |

---

## 🧠 算法原理

### 特征向量构造

每根 K 线提取以下维度，组成多维时间序列：

| 特征              | 计算方式                          | 说明                   |
| ----------------- | --------------------------------- | ---------------------- |
| 归一化收盘价      | z-score 标准化                    | 消除绝对价差，保留形态 |
| 涨跌幅            | `Δclose / close`               | 捕捉动量方向           |
| 振幅比            | `(high - low) / close`          | 反映波动强度           |
| 实体比            | `(close - open) / (high - low)` | 区分多空力度           |
| MACD 三线（可选） | DIF / DEA / 柱状线，归一化        | 动量趋势相似性         |
| RSI（可选）       | RSI(14) / 100，归一化             | 超买超卖位置对齐       |

### 相似度计算

```
综合距离 = w_DTW × DTW距离/窗口长度 + (1 - w_DTW) × (1 - Pearson相关系数)
```

- **DTW（Dynamic Time Warping）**：允许时间轴的弹性伸缩，对节奏快慢不同的形态鲁棒
- **Pearson 相关系数**：衡量整体方向的线性相关，补偿 DTW 对幅度的敏感性
- **权重可调**：侧边栏 DTW 权重滑块（默认 0.6），适应不同使用偏好

### 搜索过程

```
历史数据                         当前窗口
|----[window]----[window]----[window]----[QUERY]|
      ↑              ↑              ↑
   计算距离       计算距离      计算距离
                      ↓
              按距离排序 → 返回 Top N
```

滑动窗口遍历除当前区间外的所有历史位置，计算与当前窗口的复合距离，返回距离最小的 Top N 结果。

---

## 📁 项目结构

```
刻舟求剑/
├── app.py            # 主程序（Streamlit UI + 匹配引擎）
├── requirements.txt  # Python 依赖
├── run.sh            # 一键启动脚本
└── README.md         # 本文档
```

---

## 🗺 支持的标的

开箱即支持以下常用标的，同时支持任意 [Yahoo Finance](https://finance.yahoo.com) 代码：

| 类别     | 标的                                                            |
| -------- | --------------------------------------------------------------- |
| 贵金属   | 黄金 `GC=F`、白银 `SI=F`                                    |
| 能源     | 原油 `CL=F`                                                   |
| 美股 ETF | 标普500 `SPY`、纳指 `QQQ`、道指 `DIA`                     |
| 加密货币 | 比特币 `BTC-USD`                                              |
| 个股     | 苹果 `AAPL`、英伟达 `NVDA`、特斯拉 `TSLA`、谷歌 `GOOGL` |
| 港股     | 腾讯 `0700.HK`（自定义输入）                                  |
| 自定义   | 任意 Yahoo Finance 支持的代码                                   |

---

## ⚙️ 参数说明

| 参数       | 默认值    | 说明                         |
| ---------- | --------- | ---------------------------- |
| 标的       | 黄金 GC=F | 搜索匹配的金融标的           |
| 周期       | 日线 1d   | K线时间粒度（4h / 1d / 1w）  |
| 窗口大小   | 60根      | 参与匹配的 K 线根数          |
| 返回区间数 | 3         | 返回相似度最高的 Top N       |
| DTW 权重   | 0.6       | DTW 在复合距离中的比重       |
| MACD       | 关闭      | 是否将 MACD 指标加入匹配特征 |
| RSI        | 关闭      | 是否将 RSI 指标加入匹配特征  |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建功能分支 `git checkout -b feat/your-feature`
3. 提交修改 `git commit -m 'feat: add your feature'`
4. 推送分支 `git push origin feat/your-feature`
5. 发起 Pull Request

---

## 📄 License

[MIT License](LICENSE) © 2026 [LomaxWang](https://github.com/LomaxWang)

---

<div align="center">

**刻舟求剑 · 以史为鉴，知兴替**

*本工具仅供学习研究，不构成任何投资建议。*

</div>
