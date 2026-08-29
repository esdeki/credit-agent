# ==========================================================
#  AI CREDIT ANALYST — Streamlit Application
#  Dark-first financial dashboard with adaptive theming
# ==========================================================

import streamlit as st
import json
import uuid
import re
import pandas as pd

from src.exceptions import CompanyNotFoundError, ReportGenerationError
from src.memory_manager import MemoryManager
from src.chat_agent import create_chat_response
from src.conversation_manager import ConversationManager
from src.credit_pipeline import run_credit_analysis
from src.data_loader import load_financial_data

st.set_page_config(
    page_title="AI Credit Analyst",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.credit_rules import load_credit_policy
except Exception:
    load_credit_policy = None

print(">>> Agent start processing...", flush=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 250)
pd.set_option("display.width", 300)

# ==========================================================
# THEME ENGINE
# ==========================================================

DARK = {
    "mode":          "dark",
    "bg":            "#10151E",
    "bg_alt":        "#0B0F16",
    "surface":       "#171E2A",
    "surface_2":     "#1E2735",
    "surface_3":     "#243045",
    "border":        "rgba(255,255,255,0.07)",
    "border_strong": "rgba(255,255,255,0.14)",
    "shadow":        "rgba(0,0,0,0.45)",
    "text":          "#E7ECF5",
    "text_muted":    "#8D9AB0",
    "text_faint":    "#5F6C82",
    "primary":       "#4F8DF7",
    "success":       "#34D399",
    "warning":       "#F0B429",
    "danger":        "#F87171",
    "primary_soft":  "rgba(79,141,247,0.14)",
    "success_soft":  "rgba(52,211,153,0.14)",
    "warning_soft":  "rgba(240,180,41,0.14)",
    "danger_soft":   "rgba(248,113,113,0.14)",
    "grid":          "rgba(255,255,255,0.06)",
    "axis":          "#8D9AB0",
    "chart_text":    "#C6D0E0",
    "bar_neutral":   "rgba(141,154,176,0.35)",
    "gauge_bg":      "rgba(255,255,255,0.04)",
    "header_a":      "#16233A",
    "header_b":      "#0E1622",
}

LIGHT = {
    "mode":          "light",
    "bg":            "#F2F4F8",
    "bg_alt":        "#E9ECF3",
    "surface":       "#FFFFFF",
    "surface_2":     "#F7F9FC",
    "surface_3":     "#EDF1F7",
    "border":        "rgba(16,21,30,0.08)",
    "border_strong": "rgba(16,21,30,0.16)",
    "shadow":        "rgba(16,21,30,0.08)",
    "text":          "#131A26",
    "text_muted":    "#5A6678",
    "text_faint":    "#8A95A6",
    "primary":       "#2563EB",
    "success":       "#0F8A63",
    "warning":       "#B7791F",
    "danger":        "#C0392B",
    "primary_soft":  "rgba(37,99,235,0.10)",
    "success_soft":  "rgba(15,138,99,0.10)",
    "warning_soft":  "rgba(183,121,31,0.12)",
    "danger_soft":   "rgba(192,57,43,0.10)",
    "grid":          "rgba(16,21,30,0.07)",
    "axis":          "#5A6678",
    "chart_text":    "#2A3444",
    "bar_neutral":   "rgba(90,102,120,0.28)",
    "gauge_bg":      "rgba(16,21,30,0.03)",
    "header_a":      "#1E3A5F",
    "header_b":      "#152A45",
}

AUTO_CHART = {
    "chart_text":  "#94A3B8",
    "axis":        "#94A3B8",
    "grid":        "rgba(128,140,160,0.18)",
    "gauge_bg":    "rgba(128,140,160,0.08)",
    "bar_neutral": "rgba(128,140,160,0.30)",
}

THEME_OPTIONS = ["Dark", "Light", "Auto (system)"]


def _streamlit_theme_base():
    try:
        return st.get_option("theme.base")
    except Exception:
        return None


if "ui_theme" not in st.session_state:
    _base = _streamlit_theme_base()
    st.session_state.ui_theme = "Light" if _base == "light" else "Dark"

with st.sidebar:
    st.markdown("### ⚙️ Appearance")
    _idx = (
        THEME_OPTIONS.index(st.session_state.ui_theme)
        if st.session_state.ui_theme in THEME_OPTIONS else 0
    )
    st.session_state.ui_theme = st.radio(
        "Theme",
        options=THEME_OPTIONS,
        index=_idx,
        label_visibility="collapsed",
    )
    st.caption(
        "Auto follows your operating system / browser preference.\n\n"
        "حالت خودکار از تنظیمات سیستم یا مرورگر شما پیروی می‌کند."
    )

THEME_MODE = st.session_state.ui_theme
IS_AUTO = THEME_MODE.startswith("Auto")

if THEME_MODE == "Light":
    P = dict(LIGHT)
elif IS_AUTO:
    P = {**DARK, **AUTO_CHART}
else:
    P = dict(DARK)


def _vars_block(palette):
    return "\n".join(
        f"        --{k.replace('_', '-')}: {v};"
        for k, v in palette.items() if k != "mode"
    )


_ROOT_DARK = _vars_block(DARK)
_ROOT_LIGHT = _vars_block(LIGHT)

if THEME_MODE == "Light":
    THEME_VARS = f":root {{\n{_ROOT_LIGHT}\n}}"
elif THEME_MODE == "Dark":
    THEME_VARS = f":root {{\n{_ROOT_DARK}\n}}"
else:
    THEME_VARS = (
        f":root {{\n{_ROOT_DARK}\n}}\n"
        f"@media (prefers-color-scheme: light) {{\n"
        f"    :root {{\n{_ROOT_LIGHT}\n    }}\n"
        f"}}"
    )

# ==========================================================
# GLOBAL CSS
# ==========================================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

    {THEME_VARS}

    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInput"],
    footer {{
        background: var(--bg) !important;
        color: var(--text) !important;
    }}

    [data-testid="stHeader"] {{ border-bottom: 1px solid var(--border); }}
    [data-testid="stDecoration"] {{ display: none; }}

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {{
        background: var(--bg-alt) !important;
        border-right: 1px solid var(--border);
    }}
    [data-testid="stSidebar"] * {{ color: var(--text); }}

    .block-container {{
        padding-top: 2.2rem;
        padding-bottom: 5rem;
        max-width: 1500px;
    }}

    * {{ font-family: 'Inter', 'Vazirmatn', -apple-system, BlinkMacSystemFont, sans-serif; }}

    h1, h2, h3, h4, h5, h6,
    p, span, label, li, div,
    .stMarkdown, [data-testid="stMarkdownContainer"] {{
        color: var(--text);
    }}

    [data-testid="stWidgetLabel"] label p {{
        color: var(--text-muted) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: .05em;
        text-transform: uppercase;
    }}

    .stCaption,
    [data-testid="stCaptionContainer"] p {{ color: var(--text-faint) !important; }}

    .fa-text {{
        direction: rtl;
        text-align: right;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        font-size: 14px;
        line-height: 2.05;
        color: var(--text);
    }}

    .app-header {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(120deg, var(--header-a) 0%, var(--header-b) 100%);
        border: 1px solid var(--border-strong);
        border-radius: 18px;
        padding: 26px 30px;
        margin-bottom: 22px;
    }}
    .app-header::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(600px 160px at 88% -30%, var(--primary-soft), transparent 70%);
        pointer-events: none;
    }}
    .app-header h1 {{
        margin: 0;
        font-size: 26px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.4px;
    }}
    .app-header p {{
        margin: 6px 0 0 0;
        font-size: 13.5px;
        color: rgba(255,255,255,0.68);
    }}
    .app-header .dot {{
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        background: var(--success);
        margin-right: 8px;
        box-shadow: 0 0 0 4px rgba(52,211,153,.15);
    }}

    .section-title {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 12.5px;
        font-weight: 700;
        letter-spacing: .09em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 26px 0 12px 0;
    }}
    .section-title::after {{
        content: "";
        flex: 1;
        height: 1px;
        background: var(--border);
    }}

    [data-testid="stHorizontalBlock"] {{ align-items: stretch; gap: 16px; }}
    [data-testid="column"] {{ display: flex; flex-direction: column; }}
    [data-testid="column"] > div,
    [data-testid="column"] [data-testid="stVerticalBlock"],
    [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="column"] .stMarkdown,
    [data-testid="column"] [data-testid="stMarkdownContainer"] {{
        height: 100%;
    }}

    .card {{
        position: relative;
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 300px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 1px 2px var(--shadow), 0 8px 24px -18px var(--shadow);
        overflow: hidden;
        transition: border-color .18s ease;
    }}
    .card:hover {{ border-color: var(--border-strong); }}
    .card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent, var(--primary)), transparent 75%);
        opacity: .85;
    }}
    .card-title {{
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .card-title .tag {{
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--accent, var(--primary));
        flex: 0 0 auto;
    }}
    .card-body {{
        flex: 1 1 auto;
        max-height: 240px;
        overflow-y: auto;
        padding-left: 4px;
    }}
    .card--tall  {{ min-height: 360px; }}
    .card--tall  .card-body {{ max-height: 300px; }}
    .card--short {{ min-height: 200px; }}
    .card--short .card-body {{ max-height: 150px; }}

    .card-body::-webkit-scrollbar {{ width: 6px; }}
    .card-body::-webkit-scrollbar-track {{ background: transparent; }}
    .card-body::-webkit-scrollbar-thumb {{
        background: var(--border-strong);
        border-radius: 8px;
    }}

    .kpi-card {{
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        min-height: 138px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 1px 2px var(--shadow), 0 8px 24px -18px var(--shadow);
        overflow: hidden;
    }}
    .kpi-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--accent, var(--primary));
    }}
    .kpi-card::after {{
        content: "";
        position: absolute;
        right: -40px; top: -40px;
        width: 120px; height: 120px;
        border-radius: 50%;
        background: var(--accent-soft, var(--primary-soft));
        pointer-events: none;
    }}
    .kpi-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }}
    .kpi-label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--text-muted);
    }}
    .kpi-icon {{ font-size: 15px; opacity: .75; line-height: 1; }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -.6px;
        color: var(--text);
        margin-top: 10px;
        line-height: 1.15;
    }}
    .kpi-value.is-badge {{ font-size: 15px; }}
    .kpi-sub {{
        margin-top: 8px;
        font-size: 11.5px;
        color: var(--text-faint);
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
    }}

    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 13px;
        border-radius: 999px;
        font-size: 12.5px;
        font-weight: 700;
        border: 1px solid transparent;
        white-space: nowrap;
    }}
    .badge-success {{ background: var(--success-soft); color: var(--success); border-color: var(--success); }}
    .badge-danger  {{ background: var(--danger-soft);  color: var(--danger);  border-color: var(--danger); }}
    .badge-warning {{ background: var(--warning-soft); color: var(--warning); border-color: var(--warning); }}
    .badge-info    {{ background: var(--primary-soft); color: var(--primary); border-color: var(--primary); }}

    .list-item {{
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 9px 0;
        border-bottom: 1px dashed var(--border);
        direction: rtl;
        text-align: right;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        font-size: 13.5px;
        line-height: 1.95;
        color: var(--text);
    }}
    .list-item:last-child {{ border-bottom: none; }}
    .list-item .ic {{
        flex: 0 0 auto;
        margin-top: 4px;
        font-size: 12px;
        line-height: 1;
    }}
    .empty-state {{
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 120px;
        color: var(--text-faint);
        font-size: 13px;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        direction: rtl;
    }}

    .loan-box {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(120deg, var(--header-a) 0%, var(--header-b) 100%);
        border: 1px solid var(--border-strong);
        border-radius: 18px;
        padding: 24px 26px;
        color: #FFFFFF;
    }}
    .loan-box::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(520px 180px at 92% -40%, var(--primary-soft), transparent 70%);
        pointer-events: none;
    }}
    .loan-grid {{
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin-top: 6px;
    }}
    .loan-cell {{
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
        padding: 16px 18px;
        min-height: 96px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .loan-cell .label {{
        font-size: 10.5px;
        letter-spacing: .09em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.62);
        font-weight: 700;
    }}
    .loan-cell .value {{
        font-size: 19px;
        font-weight: 800;
        margin-top: 6px;
        direction: rtl;
        color: #FFFFFF;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
    }}
    .loan-just {{
        position: relative;
        z-index: 1;
        margin-top: 18px;
        padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.12);
        direction: rtl;
        text-align: right;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        font-size: 13.5px;
        line-height: 2;
        color: rgba(255,255,255,0.85);
    }}

    .final-note {{
        background: var(--warning-soft);
        border: 1px solid var(--warning);
        border-right: 4px solid var(--warning);
        border-radius: 16px;
        padding: 20px 22px;
        margin-top: 16px;
        font-size: 13.5px;
        line-height: 2;
        direction: rtl;
        text-align: right;
        color: var(--text);
        font-family: 'Vazirmatn', 'Inter', sans-serif;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:has(.js-plotly-plot),
    [data-testid="stVerticalBlockBorderWrapper"]:has(.chart-shell) {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 6px 10px 4px 10px !important;
        height: 100%;
        min-height: 392px;
        box-shadow: 0 1px 2px var(--shadow), 0 8px 24px -18px var(--shadow);
        overflow: hidden;
    }}
    .chart-shell {{
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: var(--text-muted);
        padding: 12px 12px 10px 12px;
        margin: 0 0 4px 0;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .chart-shell .tag {{
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--accent, var(--primary));
        flex: 0 0 auto;
    }}
    .chart-shell .hint {{
        margin-left: auto;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: .04em;
        text-transform: none;
        color: var(--text-faint);
    }}

    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 12px !important;
        color: var(--text) !important;
        min-height: 46px;
    }}
    [data-testid="stSelectbox"] svg {{ fill: var(--text-muted) !important; }}
    [data-baseweb="popover"] div[role="listbox"],
    [data-baseweb="menu"] {{
        background: var(--surface-2) !important;
        border: 1px solid var(--border-strong) !important;
    }}
    [data-baseweb="menu"] li {{ color: var(--text) !important; }}
    [data-baseweb="menu"] li:hover {{ background: var(--surface-3) !important; }}

    .stButton > button {{
        background: var(--primary);
        color: #FFFFFF;
        border: 1px solid var(--primary);
        border-radius: 12px;
        font-weight: 700;
        font-size: 14px;
        min-height: 46px;
        transition: filter .15s ease, transform .15s ease;
    }}
    .stButton > button:hover {{
        filter: brightness(1.08);
        border-color: var(--primary);
        color: #FFFFFF;
    }}
    .stButton > button:active {{ transform: translateY(1px); }}
    .stButton > button:disabled {{
        background: var(--surface-3);
        border-color: var(--border);
        color: var(--text-faint);
    }}

    [data-testid="stChatInput"] > div {{
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 14px !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background: var(--surface) !important;
        color: var(--text) !important;
        border-radius: 12px;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{ color: var(--text-faint) !important; }}
    [data-testid="stChatInput"] svg {{ fill: var(--primary) !important; }}

    [data-testid="stChatMessage"] {{
        background: var(--surface) !important;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }}
    [data-testid="stChatMessage"] p {{ color: var(--text); }}

    [data-testid="stAlert"] {{
        background: var(--surface-2) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 14px;
        color: var(--text) !important;
    }}
    [data-testid="stAlert"] p {{
        color: var(--text) !important;
        direction: rtl;
        text-align: right;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
        line-height: 2;
    }}

    [data-testid="stSpinner"] p {{ color: var(--text-muted) !important; }}

    hr, [data-testid="stDivider"] {{ border-color: var(--border) !important; }}

    [data-testid="stMetric"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 20px;
        min-height: 118px;
    }}
    [data-testid="stMetricLabel"] p {{ color: var(--text-muted) !important; }}
    [data-testid="stMetricValue"] {{ color: var(--text) !important; }}

    .toolbar {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 22px 8px 22px;
        margin-bottom: 6px;
        box-shadow: 0 1px 2px var(--shadow);
    }}

    .app-footer {{
        margin-top: 34px;
        padding: 18px 22px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        font-size: 11.5px;
        color: var(--text-faint);
        letter-spacing: .03em;
    }}
    .app-footer .right {{
        direction: rtl;
        font-family: 'Vazirmatn', 'Inter', sans-serif;
    }}

    .js-plotly-plot .plotly .modebar {{ display: none !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# UI HELPERS
# ==========================================================


def _esc(value):
    return "" if value is None else str(value)


# ==========================================================
# PATCH HELPERS · NORMALIZATION / ADAPTER / DATA QUALITY
# ==========================================================

_FA_NORMALIZE_MAP = {
    "ي": "ی",
    "ك": "ک",
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "\u200c": " ",
    "\u200f": "",
    "\u200e": "",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
}

NON_PERIOD_MARKERS = (
    "درصد تغيير",
    "درصد تغییر",
    "درصد تغييرات",
    "درصد تغییرات",
    "میانگین",
    "ميانگين",
    "جمع",
    "total",
    "average",
)


def norm_fa(value):
    if value is None:
        return ""
    text = str(value)
    for src, dst in _FA_NORMALIZE_MAP.items():
        text = text.replace(src, dst)
    return " ".join(text.split()).strip()


def norm_key(value):
    return re.sub(r"[^0-9a-zA-Z\u0600-\u06FF]+", "", norm_fa(value).lower())


def company_key(value):
    return norm_key(value)


def safe_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(norm_fa(value))
    except (TypeError, ValueError):
        return default


def fmt_num(value, digits=2, dash="—"):
    value = safe_float(value, None)
    if value is None:
        return dash
    return f"{value:.{digits}f}"


def fmt_pct(value, dash="—"):
    value = safe_float(value, None)
    if value is None:
        return dash
    if abs(value - round(value)) < 1e-9:
        return f"{value:.0f}%"
    return f"{value:.1f}%"


def is_real_period_label(value):
    label = norm_fa(value).lower()
    if not label:
        return False
    return not any(norm_fa(marker).lower() in label for marker in NON_PERIOD_MARKERS)


def _as_list(value):
    if value in (None, "", [], {}):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if str(x).strip()]
    return [
        p.strip()
        for p in re.split(r"[\n•]+|(?<=[.؛])\s+", str(value))
        if p.strip()
    ]


def _pick(d, names, default=None):
    if not isinstance(d, dict):
        return default
    for name in names:
        value = d.get(name)
        if value not in (None, "", [], {}):
            return value
    return default


def get_company_financial_rows(company_name):
    try:
        full_df = load_financial_data()
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), 0

    if full_df is None or full_df.empty or "Company_Name" not in full_df.columns:
        return pd.DataFrame(), pd.DataFrame(), 0

    target = company_key(company_name)
    raw = full_df[
        full_df["Company_Name"].apply(lambda x: company_key(x) == target)
    ].copy()

    if raw.empty:
        return raw, raw, 0

    if "Period_Date" not in raw.columns:
        return raw, raw, 0

    valid = raw[raw["Period_Date"].apply(is_real_period_label)].copy()
    excluded_count = len(raw) - len(valid)
    return raw, valid, excluded_count


def recompute_clean_analysis(company_name, existing_analysis):
    raw_df, valid_df, excluded_count = get_company_financial_rows(company_name)
    corrected = dict(existing_analysis or {})
    warnings = []

    if raw_df.empty or valid_df.empty:
        return corrected, warnings, raw_df, valid_df, excluded_count

    ratio_columns = [
        "Current_Ratio",
        "Quick_Ratio",
        "Debt_Ratio",
        "Bank_Leverage_Ratio",
        "Mada_141_Score",
        "Asset_Quality_Ratio",
    ]

    for col in ratio_columns:
        if col not in valid_df.columns:
            continue

        values = [safe_float(v, None) for v in valid_df[col].tolist()]
        values = [v for v in values if v is not None]

        if not values:
            continue

        clean_avg = sum(values) / len(values)
        avg_key = f"{col}_Average"

        old_value = safe_float(corrected.get(avg_key), None)
        if old_value is not None and abs(old_value - clean_avg) > 0.01:
            warnings.append(
                f"{avg_key}: مقدار pipeline={old_value:.4f} ولی مقدار اصلاح‌شده={clean_avg:.4f}"
            )

        corrected[avg_key] = clean_avg

    corrected["_valid_periods_count"] = len(valid_df)
    corrected["_excluded_non_period_rows"] = excluded_count

    return corrected, warnings, raw_df, valid_df, excluded_count


def derive_analysis_year(valid_df):
    if valid_df is None or valid_df.empty or "Period_Date" not in valid_df.columns:
        return None

    years = []
    for value in valid_df["Period_Date"].tolist():
        text = norm_fa(value)
        years.extend(re.findall(r"\b(13\d{2}|14\d{2})\b", text))

    return max(years) if years else None


def derive_industry(raw_df, report):
    if report.get("industry"):
        return report.get("industry")

    if raw_df is None or raw_df.empty:
        return None

    for col in ("Industry", "industry", "Sector", "sector", "Business_Sector"):
        if col in raw_df.columns:
            value = norm_fa(raw_df[col].iloc[0])
            if value:
                return value

    return None


def extract_rule_result(result):
    if not result:
        return {}

    for key in (
        "rule_result",
        "rules_result",
        "credit_rules",
        "policy_result",
        "check_credit_rules",
        "rule_engine",
        "credit_rules_result",
    ):
        value = result.get(key)
        if isinstance(value, dict):
            return value

    return {}


def extract_engine_risk(result):
    if not result:
        return None

    for key in (
        "risk_evaluation",
        "evaluate_risk",
        "risk_result",
        "engine_risk",
    ):
        value = result.get(key)
        if isinstance(value, dict) and value.get("risk_level"):
            return value.get("risk_level")
        if isinstance(value, str) and value.strip():
            return value.strip()

    rule_result = extract_rule_result(result)
    if isinstance(rule_result, dict):
        for key in ("risk_level", "risk", "risk_grade"):
            if rule_result.get(key):
                return rule_result.get(key)

    return None


def report_is_safe_to_save(data_warnings, report_risk, engine_risk):
    problems = []

    if data_warnings:
        problems.append(
            "اختلاف میان محاسبات pipeline و محاسبات اصلاح‌شده app.py وجود دارد."
        )

    if report_risk and engine_risk and risk_key(report_risk) != risk_key(engine_risk):
        problems.append(
            f"تناقض سطح ریسک: report={report_risk} / engine={engine_risk}")

    return len(problems) == 0, problems


def build_chat_context(
    company,
    result,
    corrected_analysis,
    valid_df,
    data_warnings,
    previous_memory=None,
):
    report = (result or {}).get("report", {}) or {}
    rule_result = extract_rule_result(result)

    context_parts = [
        f"[شرکت]\n{company}",
        f"[تحلیل اصلاح‌شده]\n{json.dumps(corrected_analysis, ensure_ascii=False, default=str)}",
        f"[گزارش]\n{json.dumps(report, ensure_ascii=False, default=str)}",
        f"[نتیجه قواعد]\n{json.dumps(rule_result, ensure_ascii=False, default=str)}",
    ]

    if valid_df is not None and not valid_df.empty:
        try:
            context_parts.append(
                "[دوره‌های مالی معتبر]\n" + valid_df.to_markdown(index=False)
            )
        except Exception:
            context_parts.append(
                "[دوره‌های مالی معتبر]\n"
                + json.dumps(
                    valid_df.to_dict(orient="records"),
                    ensure_ascii=False,
                    default=str,
                )
            )

    if data_warnings:
        context_parts.append(
            "[هشدارهای صحت داده]\n"
            + "\n".join(f"- {w}" for w in data_warnings)
        )

    if previous_memory:
        context_parts.append("[حافظه بلندمدت قبلی]\n" + previous_memory)

    return "\n\n".join(context_parts)


def adapt_result(raw_result, company_name):
    result = dict(raw_result or {})

    analysis = result.get("analysis") or {}
    report = dict(result.get("report") or {})

    corrected_analysis, data_warnings, raw_rows, valid_rows, excluded_count = (
        recompute_clean_analysis(company_name, analysis)
    )

    result["analysis"] = corrected_analysis

    for key in (
        "strengths",
        "weaknesses",
        "supporting_factors",
        "objection_factors",
        "recommendations",
        "reasons",
    ):
        report[key] = _as_list(report.get(key))

    if not report.get("analysis_year"):
        report["analysis_year"] = derive_analysis_year(valid_rows)

    if not report.get("industry"):
        report["industry"] = derive_industry(raw_rows, report)

    result["report"] = report
    result["_data_warnings"] = data_warnings
    result["_raw_financial_rows"] = raw_rows
    result["_valid_financial_rows"] = valid_rows
    result["_excluded_non_period_rows"] = excluded_count
    result["_engine_risk"] = extract_engine_risk(result)

    return result


def section(title):
    st.markdown(
        f'<div class="section-title">{_esc(title)}</div>',
        unsafe_allow_html=True,
    )


# ==========================================================
# PATCH 2 · RISK / DECISION MAPPING
# ==========================================================

_DECISION_APPROVE = {
    "تایید",
    "تاییدشد",
    "approve",
    "approved",
    "موافقت",
    "قبول",
}

_DECISION_REJECT = {
    "رد",
    "reject",
    "rejected",
    "عدمموافقت",
    "مردود",
}

_RISK_MAP = {
    "low": "low",
    "پایین": "low",
    "کم": "low",
    "medium": "medium",
    "moderate": "medium",
    "متوسط": "medium",
    "میانه": "medium",
    "high": "high",
    "بالا": "high",
    "زیاد": "high",
    "veryhigh": "high",
    "بسیاربالا": "high",
}


def decision_key(decision):
    key = norm_key(decision)
    if key in _DECISION_APPROVE:
        return "approve"
    if key in _DECISION_REJECT:
        return "reject"
    return "conditional"


def decision_badge_class(decision):
    return {
        "approve": "badge-success",
        "reject": "badge-danger",
    }.get(decision_key(decision), "badge-warning")


def decision_accent(decision):
    return {
        "approve": "success",
        "reject": "danger",
    }.get(decision_key(decision), "warning")


def risk_key(risk):
    return _RISK_MAP.get(norm_key(risk), "medium" if norm_key(risk) else "")


def risk_badge_class(risk):
    return {
        "low": "badge-success",
        "high": "badge-danger",
    }.get(risk_key(risk), "badge-warning")


def risk_accent(risk):
    return {
        "low": "success",
        "high": "danger",
    }.get(risk_key(risk), "warning")


def score_accent(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "primary"
    if score >= 70:
        return "success"
    if score >= 40:
        return "warning"
    return "danger"


def ratio_accent(value, threshold, higher_is_better=True):
    if threshold is None:
        return "primary"
    try:
        ok = (float(value) >= float(threshold)) if higher_is_better \
            else (float(value) <= float(threshold))
    except (TypeError, ValueError):
        return "primary"
    return "success" if ok else "danger"


def render_kpi(label, value, icon="•", accent="primary",
               badge_class=None, sub=None):
    inner = (
        f'<span class="badge {badge_class}">{_esc(value)}</span>'
        if badge_class else _esc(value)
    )
    value_cls = "kpi-value is-badge" if badge_class else "kpi-value"
    sub_html = (
        f'<div class="kpi-sub">{_esc(sub)}</div>' if sub
        else '<div class="kpi-sub">&nbsp;</div>'
    )

    st.markdown(
        f"""
        <div class="kpi-card" style="--accent: var(--{accent}); --accent-soft: var(--{accent}-soft);">
            <div class="kpi-head">
                <div class="kpi-label">{_esc(label)}</div>
                <div class="kpi-icon">{icon}</div>
            </div>
            <div class="{value_cls}">{inner}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_text_card(title, content, accent="primary", size="",
                     empty_text="اطلاعاتی ثبت نشده است."):
    body = _esc(content).strip()
    inner = (
        f'<div class="fa-text">{body}</div>' if body
        else f'<div class="empty-state">{empty_text}</div>'
    )
    st.markdown(
        f"""
        <div class="card {size}" style="--accent: var(--{accent});">
            <div class="card-title"><span class="tag"></span>{_esc(title)}</div>
            <div class="card-body">{inner}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_list_card(title, items, icon="•", accent="primary", size="",
                     empty_text="موردی ثبت نشده است."):
    items = _as_list(items)
    if items:
        inner = "".join(
            f'<div class="list-item"><span class="ic">{icon}</span>'
            f'<span>{_esc(item)}</span></div>'
            for item in items
        )
    else:
        inner = f'<div class="empty-state">{empty_text}</div>'

    st.markdown(
        f"""
        <div class="card {size}" style="--accent: var(--{accent});">
            <div class="card-title">
                <span class="tag"></span>{_esc(title)}
                <span style="margin-left:auto;font-size:11px;color:var(--text-faint);">
                    {len(items)}
                </span>
            </div>
            <div class="card-body">{inner}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_card(title, accent="primary", hint=""):
    box = st.container(border=True)
    with box:
        st.markdown(
            f'<div class="chart-shell" style="--accent: var(--{accent});">'
            f'<span class="tag"></span>{_esc(title)}'
            f'<span class="hint">{_esc(hint)}</span></div>',
            unsafe_allow_html=True,
        )
    return box


# ==========================================================
# THEME-AWARE CHARTS
# ==========================================================


def _base_layout(height):
    dark_side = (P["mode"] == "dark") or IS_AUTO
    return dict(
        height=height,
        margin=dict(l=12, r=12, t=34, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=12, color=P["chart_text"]),
        hoverlabel=dict(
            bgcolor="#1E2735" if dark_side else "#FFFFFF",
            font=dict(
                color="#E7ECF5" if dark_side else "#131A26",
                family="Inter",
                size=12,
            ),
            bordercolor=P["border_strong"],
        ),
    )


def render_ratio_chart(analysis, policy):
    labels = ["Current Ratio", "Quick Ratio", "Debt Ratio"]
    actual = [
        float(analysis.get("Current_Ratio_Average", 0) or 0),
        float(analysis.get("Quick_Ratio_Average", 0) or 0),
        float(analysis.get("Debt_Ratio_Average", 0) or 0),
    ]
    threshold = [
        (policy or {}).get("current_ratio_min"),
        (policy or {}).get("quick_ratio_min"),
        (policy or {}).get("debt_ratio_max"),
    ]
    higher_better = [True, True, False]

    bar_colors = []
    for value, thr, hb in zip(actual, threshold, higher_better):
        if thr is None:
            bar_colors.append(P["primary"])
        else:
            try:
                ok = value >= float(thr) if hb else value <= float(thr)
            except (TypeError, ValueError):
                bar_colors.append(P["primary"])
                continue
            bar_colors.append(P["success"] if ok else P["danger"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=actual,
        name="Actual",
        marker=dict(color=bar_colors, line=dict(width=0)),
        width=0.34,
        text=[f"{v:.2f}" for v in actual],
        textposition="outside",
        textfont=dict(color=P["chart_text"], size=12),
        hovertemplate="<b>%{x}</b><br>Actual: %{y:.2f}<extra></extra>",
    ))

    if all(t is not None for t in threshold):
        fig.add_trace(go.Bar(
            x=labels,
            y=[float(t) for t in threshold],
            name="Policy threshold",
            marker=dict(color=P["bar_neutral"], line=dict(width=0)),
            width=0.34,
            text=[f"{float(t):.2f}" for t in threshold],
            textposition="outside",
            textfont=dict(color=P["axis"], size=11),
            hovertemplate="<b>%{x}</b><br>Policy: %{y:.2f}<extra></extra>",
        ))

    fig.update_layout(
        barmode="group",
        bargap=0.42,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.04,
            xanchor="right", x=1,
            font=dict(color=P["chart_text"], size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        **_base_layout(300),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        linecolor=P["grid"],
        tickfont=dict(color=P["axis"], size=11.5),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=P["grid"], gridwidth=1,
        zeroline=False, showline=False,
        tickfont=dict(color=P["axis"], size=11),
    )

    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})


def render_confidence_gauge(score, risk):
    accent_key = risk_accent(risk)
    color = P.get(accent_key, P["primary"])
    try:
        score = float(score or 0)
    except (TypeError, ValueError):
        score = 0.0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            "suffix": "%",
            "font": {"size": 34, "color": P["chart_text"], "family": "Inter"},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": P["grid"],
                "tickfont": {"color": P["axis"], "size": 10},
            },
            "bar": {"color": color, "thickness": 0.72},
            "bgcolor": P["gauge_bg"],
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],   "color": P["danger_soft"]},
                {"range": [40, 70],  "color": P["warning_soft"]},
                {"range": [70, 100], "color": P["success_soft"]},
            ],
            "threshold": {
                "line": {"color": P["chart_text"], "width": 2},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(**_base_layout(300))
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})


# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    """
    <div class="app-header">
        <h1>🏦 AI Credit Analyst</h1>
        <p><span class="dot"></span>AI-powered financial credit assessment system
        &nbsp;·&nbsp; سامانه هوشمند ارزیابی اعتباری</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# SESSION STATE
# ==========================================================

if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()

if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = MemoryManager()

if "result" not in st.session_state:
    st.session_state.result = None

if "corrected_analysis" not in st.session_state:
    st.session_state.corrected_analysis = {}

if "data_warnings" not in st.session_state:
    st.session_state.data_warnings = []

if "raw_financial_rows" not in st.session_state:
    st.session_state.raw_financial_rows = None

if "valid_financial_rows" not in st.session_state:
    st.session_state.valid_financial_rows = None

if "excluded_non_period_rows" not in st.session_state:
    st.session_state.excluded_non_period_rows = 0

if "analyzed_company" not in st.session_state:
    st.session_state.analyzed_company = None

if "analyzed_company_key" not in st.session_state:
    st.session_state.analyzed_company_key = None

if "active_company_key" not in st.session_state:
    st.session_state.active_company_key = None

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "run_id" not in st.session_state:
    st.session_state.run_id = None

if "memory_saved_for_run" not in st.session_state:
    st.session_state.memory_saved_for_run = False

conversation_manager = st.session_state.conversation_manager
memory_manager = st.session_state.memory_manager


def reset_analysis_state(new_company):
    st.session_state.conversation_manager = ConversationManager()
    st.session_state.result = None
    st.session_state.corrected_analysis = {}
    st.session_state.data_warnings = []
    st.session_state.raw_financial_rows = None
    st.session_state.valid_financial_rows = None
    st.session_state.excluded_non_period_rows = 0
    st.session_state.analyzed_company = None
    st.session_state.analyzed_company_key = None
    st.session_state.chat_log = []
    st.session_state.memory_saved_for_run = False
    st.session_state.active_company_key = company_key(new_company)


# ==========================================================
# COMPANY SELECTOR
# ==========================================================

section("Portfolio · انتخاب شرکت")

try:
    df = load_financial_data()
    companies = list(df["Company_Name"].unique())
except Exception as error:
    companies = []
    st.error(
        "⚠️ بارگذاری داده‌های مالی ناموفق بود. لطفاً از صحت فایل داده اطمینان حاصل کنید.\n\n"
        f"جزئیات فنی: {error}"
    )

col_select, col_button = st.columns([4, 1], gap="medium")

with col_select:
    company_name = st.selectbox(
        "Select company · انتخاب شرکت",
        companies,
        index=None,
        placeholder="انتخاب کنید",
        disabled=not companies,
    )

if company_name and company_key(company_name) != st.session_state.active_company_key:
    reset_analysis_state(company_name)
    conversation_manager = st.session_state.conversation_manager

with col_button:
    st.markdown("<div style='height:29px'></div>", unsafe_allow_html=True)
    analyze_clicked = st.button(
        "🔍  Analyze Credit",
        use_container_width=True,
        disabled=not companies,
    )

if company_name:
    try:
        previous_summary = memory_manager.get_latest_memory_summary(
            company_name)
    except Exception:
        previous_summary = None

    if previous_summary and "یافت نشد" not in previous_summary:
        with st.expander("🕓 آخرین تحلیل ثبت‌شده برای این شرکت (حافظهٔ بلندمدت)"):
            st.markdown(
                f'<div class="fa-text">{_esc(previous_summary)}</div>',
                unsafe_allow_html=True,
            )

# ==========================================================
# RUN ANALYSIS
# ==========================================================

if analyze_clicked and company_name:
    selected_key = company_key(company_name)

    if st.session_state.analyzed_company_key != selected_key:
        st.session_state.conversation_manager = ConversationManager()
        conversation_manager = st.session_state.conversation_manager
        st.session_state.chat_log = []
        st.session_state.result = None
        st.session_state.corrected_analysis = {}
        st.session_state.data_warnings = []
        st.session_state.raw_financial_rows = None
        st.session_state.valid_financial_rows = None
        st.session_state.excluded_non_period_rows = 0
        st.session_state.memory_saved_for_run = False

    st.session_state.run_id = uuid.uuid4().hex[:12]
    st.session_state.active_company_key = selected_key
    st.session_state.analyzed_company_key = selected_key

    with st.spinner("در حال تحلیل صورت‌های مالی و تدوین گزارش اعتباری…"):
        try:
            result = run_credit_analysis(company_name, conversation_manager)

        except CompanyNotFoundError as error:
            st.error(
                f"⚠️ {error}\n\n"
                "لطفاً نام شرکت را از لیست موجود انتخاب کنید. "
                "اگر شرکت مدنظر شما در لیست نیست، ابتدا باید اطلاعات آن به پایگاه‌داده اضافه شود."
            )

        except ReportGenerationError as error:
            st.error(
                f"⚠️ {error}\n\n"
                "این خطا مربوط به خروجی هوش مصنوعی است، نه اطلاعات شرکت. "
                "لطفاً دوباره تلاش کنید. اگر خطا تکرار شد، احتمالاً باید "
                "`max_tokens` یا ساختار خروجی JSON در `credit_agent` اصلاح شود."
            )

        except Exception as error:
            st.error(
                "⚠️ در حین تحلیل این شرکت خطایی رخ داد. "
                "لطفاً دوباره تلاش کنید یا با پشتیبانی فنی تماس بگیرید.\n\n"
                f"جزئیات فنی خطا (برای گزارش به توسعه‌دهنده): {error}"
            )

        else:
            result = adapt_result(result, company_name)

            report_data = result.get("report", {}) or {}
            corrected_analysis = result.get("analysis", {}) or {}
            data_warnings = result.get("_data_warnings", []) or []
            raw_rows = result.get("_raw_financial_rows")
            valid_rows = result.get("_valid_financial_rows")
            excluded_count = result.get("_excluded_non_period_rows", 0)
            engine_risk = result.get("_engine_risk")
            report_risk = report_data.get("risk_level")

            st.session_state.result = result
            st.session_state.corrected_analysis = corrected_analysis
            st.session_state.data_warnings = data_warnings
            st.session_state.raw_financial_rows = raw_rows
            st.session_state.valid_financial_rows = valid_rows
            st.session_state.excluded_non_period_rows = excluded_count
            st.session_state.analyzed_company = company_name
            st.session_state.analyzed_company_key = selected_key
            st.session_state.chat_log = []

            safe_to_save, save_problems = report_is_safe_to_save(
                data_warnings,
                report_risk,
                engine_risk,
            )

            if data_warnings:
                st.warning(
                    "⚠️ هشدار صحت داده: برخی نسبت‌های مالی توسط app.py دوباره محاسبه شدند، "
                    "زیرا احتمال ورود ردیف‌های غیر دوره‌ای مثل «درصد تغيير» در محاسبات pipeline وجود دارد.\n\n"
                    + "\n".join(f"- {w}" for w in data_warnings)
                )

            if excluded_count:
                st.info(
                    f"ℹ️ {excluded_count} ردیف غیر دوره‌ای از محاسبات نمایشی کنار گذاشته شد."
                )

            if engine_risk and report_risk and risk_key(engine_risk) != risk_key(report_risk):
                st.warning(
                    f"⚠️ تناقض سطح ریسک تشخیص داده شد: "
                    f"risk گزارش = {report_risk} / risk موتور = {engine_risk}"
                )

            if safe_to_save:
                memory_payload = {
                    "run_id": st.session_state.run_id,
                    "decision": report_data.get("decision"),
                    "risk_level": report_data.get("risk_level"),
                    "engine_risk_level": engine_risk,
                    "confidence_score": report_data.get("confidence_score"),
                    "summary": report_data.get("executive_summary"),
                    "analysis_year": report_data.get("analysis_year"),
                    "industry": report_data.get("industry"),
                    "corrected_analysis": corrected_analysis,
                    "excluded_non_period_rows": excluded_count,
                    "consistent": True,
                }
                try:
                    memory_manager.save_memory(
                        company_name,
                        "credit_analysis",
                        json.dumps(memory_payload,
                                   ensure_ascii=False, default=str),
                    )
                    st.session_state.memory_saved_for_run = True
                except Exception as mem_error:
                    st.warning(
                        f"⚠️ ذخیرهٔ حافظهٔ بلندمدت ناموفق بود: {mem_error}")
            else:
                st.warning(
                    "⚠️ این گزارش به دلیل ناسازگاری یا هشدار صحت داده، "
                    "در حافظهٔ بلندمدت ذخیره نشد.\n\n"
                    + "\n".join(f"- {p}" for p in save_problems)
                )

            st.success("تحلیل با موفقیت انجام شد.")

# ==========================================================
# REPORT RENDERING
# ==========================================================


def render_report(result, company):
    analysis = result.get("analysis", {}) or {}
    report = result.get("report", {}) or {}

    raw_rows = st.session_state.get("raw_financial_rows")
    valid_rows = st.session_state.get("valid_financial_rows")
    data_warnings = st.session_state.get("data_warnings", []) or []
    excluded_count = st.session_state.get("excluded_non_period_rows", 0)

    policy = None
    if load_credit_policy:
        try:
            policy = load_credit_policy() or {}
        except Exception:
            policy = None

    decision = report.get("decision") or "-"
    risk = report.get("risk_level") or "-"
    score = report.get("confidence_score", 0)
    engine_risk = extract_engine_risk(result)

    def _num(key):
        try:
            return float(analysis.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    cr = _num("Current_Ratio_Average")
    qr = _num("Quick_Ratio_Average")
    dr = _num("Debt_Ratio_Average")

    cr_min = (policy or {}).get("current_ratio_min")
    qr_min = (policy or {}).get("quick_ratio_min")
    dr_max = (policy or {}).get("debt_ratio_max")

    strengths = _as_list(report.get("strengths"))
    weaknesses = _as_list(report.get("weaknesses"))
    reasons = _as_list(report.get("reasons"))

    analysis_year = report.get(
        "analysis_year") or derive_analysis_year(valid_rows)
    industry = report.get("industry") or derive_industry(raw_rows, report)

    section(f"Credit File · {company}")

    if data_warnings:
        st.error(
            "🔴 هشدار کیفیت داده: مقادیر نسبت‌های مالی در این صفحه با حذف ردیف‌های غیر دوره‌ای "
            "مثل «درصد تغيير» دوباره محاسبه شده‌اند. اصلاح ریشه‌ای باید در pipeline/tools انجام شود."
        )
        with st.expander("جزئیات اختلاف محاسبات"):
            for warning in data_warnings:
                st.markdown(f"- {warning}")

    if excluded_count:
        st.info(
            f"ℹ️ تعداد ردیف‌های غیر دوره‌ای حذف‌شده از محاسبات نمایشی: {excluded_count}"
        )

    if engine_risk and risk_key(engine_risk) != risk_key(risk):
        st.warning(
            f"⚠️ تناقض سطح ریسک: مقدار گزارش نهایی «{risk}» است، "
            f"اما خروجی موتور ریسک «{engine_risk}» بوده است."
        )

    a1, a2, a3, a4 = st.columns(4, gap="medium")

    with a1:
        render_kpi(
            "Credit decision", decision, icon="⚖️",
            accent=decision_accent(decision),
            badge_class=decision_badge_class(decision),
            sub="تصمیم نهایی موتور اعتباری",
        )
    with a2:
        render_kpi(
            "Risk level", risk, icon="🛡️",
            accent=risk_accent(risk),
            badge_class=risk_badge_class(risk),
            sub=f"engine: {engine_risk}" if engine_risk else "سطح ریسک ارزیابی‌شده",
        )
    with a3:
        render_kpi(
            "Confidence score", fmt_pct(score), icon="🎯",
            accent=score_accent(score),
            sub="درجه اطمینان تحلیل",
        )
    with a4:
        render_kpi(
            "Current ratio", f"{cr:.2f}", icon="💧",
            accent=ratio_accent(cr, cr_min, higher_is_better=True),
            sub=f"حد سیاست: {cr_min}" if cr_min is not None else "نسبت جاری اصلاح‌شده",
        )

    b1, b2, b3, b4 = st.columns(4, gap="medium")

    with b1:
        render_kpi(
            "Quick ratio", f"{qr:.2f}", icon="⚡",
            accent=ratio_accent(qr, qr_min, higher_is_better=True),
            sub=f"حد سیاست: {qr_min}" if qr_min is not None else "نسبت سریع اصلاح‌شده",
        )
    with b2:
        render_kpi(
            "Debt ratio", f"{dr:.2f}", icon="📊",
            accent=ratio_accent(dr, dr_max, higher_is_better=False),
            sub=f"حد سیاست: {dr_max}" if dr_max is not None else "نسبت بدهی اصلاح‌شده",
        )
    with b3:
        render_kpi(
            "Analysis year",
            analysis_year or "-", icon="📅",
            accent="primary" if analysis_year else "warning",
            sub="سال مالی تحلیل" if analysis_year else "در خروجی تحلیل موجود نیست",
        )
    with b4:
        render_kpi(
            "Industry",
            industry or "-", icon="🏭",
            accent="primary" if industry else "warning",
            sub="بخش صنعتی شرکت" if industry else "در خروجی تحلیل موجود نیست",
        )

    if PLOTLY_AVAILABLE:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            with chart_card("Financial ratios", accent=decision_accent(decision)):
                render_ratio_chart(analysis, policy)
        with c2:
            with chart_card("Confidence score",
                            accent=risk_accent(risk),
                            hint=f"risk: {risk}"):
                render_confidence_gauge(score, risk)
    else:
        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            st.metric("Current Ratio", f"{cr:.2f}")
        with m2:
            st.metric("Quick Ratio", f"{qr:.2f}")
        with m3:
            st.metric("Debt Ratio", f"{dr:.2f}")
        st.caption(
            "برای نمایش نمودارها بستهٔ plotly را نصب کنید:  pip install plotly"
        )

    if valid_rows is not None and not valid_rows.empty:
        with st.expander("📊 ردیف‌های مالی معتبر استفاده‌شده در محاسبات"):
            st.dataframe(valid_rows, use_container_width=True)

    if raw_rows is not None and valid_rows is not None and excluded_count:
        with st.expander("🚫 ردیف‌های حذف‌شده از محاسبات"):
            try:
                excluded_rows = raw_rows[
                    ~raw_rows["Period_Date"].apply(is_real_period_label)
                ]
                st.dataframe(excluded_rows, use_container_width=True)
            except Exception:
                st.caption("امکان نمایش ردیف‌های حذف‌شده وجود ندارد.")

    section("Executive summary · خلاصه مدیریتی")

    render_text_card(
        "Executive summary",
        report.get("executive_summary"),
        accent=decision_accent(decision),
        size="card--short",
    )

    section("Detailed analysis · تحلیل تفصیلی")

    d1, d2 = st.columns(2, gap="medium")
    with d1:
        render_text_card(
            "Financial analysis",
            report.get("financial_analysis_detailed"),
            accent="primary",
        )
    with d2:
        render_text_card(
            "Trend analysis",
            report.get("trend_analysis"),
            accent="primary",
        )

    d3, d4 = st.columns(2, gap="medium")
    with d3:
        render_text_card(
            "Article 141 assessment",
            report.get("article_141_assessment"),
            accent="warning",
        )
    with d4:
        render_text_card(
            "External risk assessment",
            report.get("external_risk_assessment"),
            accent="warning",
        )

    render_text_card(
        "Credit policy compliance",
        report.get("credit_policy_compliance"),
        accent="success",
        size="card--short",
    )

    section("Assessment · نقاط قوت و ضعف")

    if reasons:
        render_list_card(
            "Decision reasons · دلایل تصمیم",
            reasons,
            "●",
            accent=decision_accent(decision),
            empty_text="دلیلی ثبت نشده است.",
        )

    s1, s2 = st.columns(2, gap="medium")
    with s1:
        render_list_card(
            "Strengths",
            strengths,
            "✅",
            accent="success",
            empty_text="نقطه قوت شاخصی شناسایی نشد.",
        )
    with s2:
        render_list_card(
            "Weaknesses",
            weaknesses,
            "⚠️",
            accent="danger",
            empty_text="نقطه ضعف شاخصی شناسایی نشد.",
        )

    f1, f2 = st.columns(2, gap="medium")
    with f1:
        render_list_card(
            "Supporting factors",
            report.get("supporting_factors"),
            "▲",
            accent="primary",
            empty_text="عامل حمایتی ثبت نشده است.",
        )
    with f2:
        render_list_card(
            "Objection factors",
            report.get("objection_factors"),
            "▼",
            accent="warning",
            empty_text="عامل بازدارنده‌ای ثبت نشده است.",
        )

    section("Facility proposal · پیشنهاد تسهیلات")

    st.markdown(
        f"""
        <div class="loan-box">
            <div class="card-title" style="color:rgba(255,255,255,.70);
                 border-color:rgba(255,255,255,.14);">
                <span class="tag" style="background:var(--success)"></span>
                Loan recommendation
            </div>
            <div class="loan-grid">
                <div class="loan-cell">
                    <div class="label">Suggested amount</div>
                    <div class="value">{_esc(report.get("suggested_loan_amount")) or "—"}</div>
                </div>
                <div class="loan-cell">
                    <div class="label">Repayment tenor</div>
                    <div class="value">{_esc(report.get("suggested_repayment_months")) or "—"}</div>
                </div>
                <div class="loan-cell">
                    <div class="label">Decision · Risk</div>
                    <div class="value">{_esc(decision)} · {_esc(risk)}</div>
                </div>
            </div>
            <div class="loan-just">
                <b style="color:#FFFFFF;">توجیه اعتباری:</b><br>
                {_esc(report.get("loan_justification")) or "—"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    render_list_card(
        "AI recommendations",
        report.get("recommendations"),
        "→",
        accent="primary",
        empty_text="توصیه‌ای ثبت نشده است.",
    )

    if report.get("final_notes"):
        st.markdown(
            f'<div class="final-note">📌&nbsp; {_esc(report.get("final_notes"))}</div>',
            unsafe_allow_html=True,
        )


if st.session_state.result:
    render_report(st.session_state.result, st.session_state.analyzed_company)
else:
    st.markdown(
        """
        <div class="card card--short" style="--accent: var(--primary);">
            <div class="card-title"><span class="tag"></span>Getting started</div>
            <div class="card-body">
                <div class="fa-text">
                    برای شروع، یک شرکت را از فهرست بالا انتخاب کنید و روی
                    <b>Analyze Credit</b> کلیک کنید.<br>
                    پس از تولید گزارش، می‌توانید در بخش گفت‌وگو پرسش‌های تخصصی
                    خود را دربارهٔ همان شرکت مطرح کنید.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================================
# CHAT
# ==========================================================

section("💬 Ask Credit Analyst · گفت‌وگو با تحلیل‌گر")

if st.session_state.analyzed_company:
    st.caption(f"Context: {st.session_state.analyzed_company}")

for role, text in st.session_state.chat_log:
    with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "🏦"):
        st.markdown(
            f'<div class="fa-text">{_esc(text)}</div>',
            unsafe_allow_html=True,
        )

question = st.chat_input("سؤال خود را دربارهٔ این شرکت بپرسید…")

if question:
    base_context = conversation_manager.get_context()

    if not base_context or not st.session_state.result:
        st.warning(
            "⚠️ ابتدا یک شرکت را تحلیل کنید تا امکان پاسخ‌گویی فراهم شود.\n\n"
            "Please analyze a company first."
        )
    else:
        previous_long_term = None

        try:
            previous_long_term = memory_manager.get_latest_memory_summary(
                st.session_state.analyzed_company
            )
        except Exception:
            previous_long_term = None

        if previous_long_term and "یافت نشد" in previous_long_term:
            previous_long_term = None

        enriched_context = build_chat_context(
            company=st.session_state.analyzed_company,
            result=st.session_state.result,
            corrected_analysis=st.session_state.corrected_analysis,
            valid_df=st.session_state.valid_financial_rows,
            data_warnings=st.session_state.data_warnings,
            previous_memory=previous_long_term,
        )

        st.session_state.chat_log.append(("user", question))

        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(
                f'<div class="fa-text">{_esc(question)}</div>',
                unsafe_allow_html=True,
            )

        conversation_manager.add_user_message(question)
        chat_history = conversation_manager.get_chat_history()

        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("در حال بررسی…"):
                try:
                    answer = create_chat_response(
                        question,
                        {
                            "company": st.session_state.analyzed_company,
                            "analysis": st.session_state.corrected_analysis,
                            "report": st.session_state.result.get("report", {}),
                            "rule_result": extract_rule_result(st.session_state.result),
                            "engine_risk": extract_engine_risk(st.session_state.result),
                            "data_warnings": st.session_state.data_warnings,
                            "context": enriched_context,
                            "run_id": st.session_state.get("run_id"),
                        },
                        chat_history,
                    )
                except Exception as error:
                    answer = (
                        "متأسفانه در تولید پاسخ خطایی رخ داد. لطفاً دوباره تلاش کنید.\n\n"
                        f"جزئیات فنی: {error}"
                    )

            st.markdown(
                f'<div class="fa-text">{_esc(answer)}</div>',
                unsafe_allow_html=True,
            )

        conversation_manager.add_assistant_message(answer)
        st.session_state.chat_log.append(("assistant", answer))

# ==========================================================
# FOOTER
# ==========================================================

st.markdown(
    f"""
    <div class="app-footer">
        <div class="left">
            AI CREDIT ANALYST · v2.0 · THEME: {THEME_MODE.upper()} · RUN: {st.session_state.get("run_id") or "—"}
        </div>
        <div class="right">
            این گزارش جنبهٔ پشتیبان تصمیم دارد و جایگزین مصوبهٔ کمیتهٔ اعتباری نیست.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
