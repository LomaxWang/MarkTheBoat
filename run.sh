#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  刻舟求剑 · 启动脚本
# ─────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="$SCRIPT_DIR/requirements.txt"
APP="$SCRIPT_DIR/app.py"
PORT="${PORT:-8501}"

# ── 颜色输出
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

echo ""
echo -e "${BOLD}${CYAN}⚔️  刻舟求剑 · K线形态匹配引擎${RESET}"
echo -e "${CYAN}────────────────────────────────────${RESET}"

# ── 1. 找 Python 3
if command -v python3 &>/dev/null; then
    PYTHON=$(command -v python3)
elif command -v python &>/dev/null; then
    PYTHON=$(command -v python)
else
    echo -e "${RED}❌  未找到 Python，请先安装 Python 3.9+${RESET}"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "🐍  Python: ${GREEN}${PYTHON}  (${PY_VER})${RESET}"

# ── 2. 找 pip
if "$PYTHON" -m pip --version &>/dev/null 2>&1; then
    PIP="$PYTHON -m pip"
elif command -v pip3 &>/dev/null; then
    PIP="pip3"
elif command -v pip &>/dev/null; then
    PIP="pip"
else
    echo -e "${RED}❌  未找到 pip，请手动安装：python3 -m ensurepip${RESET}"
    exit 1
fi

# ── 3. 安装依赖
echo -e "📦  检查依赖..."
$PIP install -r "$REQ" -q --disable-pip-version-check
echo -e "    ${GREEN}依赖已就绪${RESET}"

# ── 4. 找 streamlit 可执行文件
if command -v streamlit &>/dev/null; then
    STREAMLIT="streamlit"
else
    # 尝试 Python 用户目录
    USER_BIN="$("$PYTHON" -c "import site; print(site.getusersitepackages())" 2>/dev/null | sed 's|lib/python.*/site-packages|bin|')"
    if [ -x "$USER_BIN/streamlit" ]; then
        STREAMLIT="$USER_BIN/streamlit"
    elif [ -x "$HOME/Library/Python/${PY_VER}/bin/streamlit" ]; then
        STREAMLIT="$HOME/Library/Python/${PY_VER}/bin/streamlit"
    else
        # 最后回退：用 python -m streamlit
        STREAMLIT="$PYTHON -m streamlit"
    fi
fi

echo -e "🚀  Streamlit: ${GREEN}${STREAMLIT}${RESET}"

# ── 5. 启动
echo ""
echo -e "${BOLD}${GREEN}✅  正在启动，稍候浏览器会自动打开...${RESET}"
echo -e "🌐  本地地址：${CYAN}http://localhost:${PORT}${RESET}"
echo -e "${YELLOW}    按 Ctrl+C 可退出服务${RESET}"
echo ""

cd "$SCRIPT_DIR"
$STREAMLIT run "$APP" \
    --server.port "$PORT" \
    --server.headless false \
    --browser.gatherUsageStats false
