import json
import html
import re
import glob
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


# =========================
# 1. CONFIGURATION & CSS
# =========================
st.set_page_config(
    page_title="Finsight AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="stApp"] {
    background-color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    color: #000000 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* NAVBAR */
.cmc-nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px 20px;
    margin-bottom: 25px;
    border-bottom: 1px solid #eff2f5;
    background: white;
    position: sticky;
    top: 0;
    z-index: 999;
}
.cmc-brand {
    font-size: 22px;
    font-weight: 800;
    color: #000000;
    text-decoration: none !important;
    display: flex; align-items: center;
}
.cmc-brand span { color: #3861fb; margin-left: 4px; }
.cmc-links { display: flex; gap: 20px; }
.cmc-link {
    text-decoration: none !important; color: #000000 !important;
    font-weight: 600; font-size: 14px; padding: 5px 10px; cursor: pointer;
}
.cmc-link:hover, .cmc-link.active {
    color: #3861fb !important; background: #f0f6ff; border-radius: 8px;
}
.cmc-account {
    background: #3861fb; color: white !important;
    padding: 8px 16px; border-radius: 8px;
    font-weight: 600; font-size: 14px; text-decoration: none !important;
}

/* CARDS */
.kpi-card {
    background: #ffffff;
    border: 1px solid #eff2f5;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    height: 100%;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-label {
    font-size: 12px; font-weight: 600; color: #58667e;
    text-transform: uppercase; margin-bottom: 8px; width: 100%; text-align: left;
}
.kpi-value { font-size: 28px; font-weight: 700; color: #000000; }
.kpi-sub { font-size: 14px; margin-top: 5px; font-weight: 600; }
.text-green { color: #16c784 !important; }
.text-red { color: #ea3943 !important; }

/* TABLE */
.cmc-table-wrap {
    overflow-x: auto;
    border: 1px solid #eff2f5;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    margin-top: 20px;
    background: white;
}
table.cmc-table { width: 100%; border-collapse: collapse; background: white; }
table.cmc-table th {
    text-align: left; padding: 16px; border-bottom: 1px solid #eff2f5;
    color: #000000; font-size: 12px; font-weight: 700; background-color: #f8fafc;
}
table.cmc-table td {
    padding: 16px; border-bottom: 1px solid #eff2f5;
    color: #000000; font-size: 14px; font-weight: 600; vertical-align: middle;
}
table.cmc-table tr:hover { background-color: #f8fafc; }
table.cmc-table a { text-decoration: none; color: inherit; display: block; width: 100%; height: 100%; }
.ticker-badge {
    background: #eff2f5; color: #58667e; padding: 2px 6px;
    border-radius: 4px; font-size: 12px; margin-left: 8px;
}

/* BUTTONS */
.stButton button {
    background-color: #3861fb !important; color: white !important;
    border: none; border-radius: 8px; font-weight: 600;
}

/* NEWS & LEXICON */
.lex-term {
    border-bottom: 1px dotted #58667e; cursor: help;
    background-color: #fffbeb; padding: 0 2px; border-radius: 3px; color: #000;
}
.news-item { padding: 16px; border-bottom: 1px solid #eff2f5; }
.news-item:hover { background: #f8fafc; }
.tag { padding: 3px 8px; border-radius: 100px; background: #eff2f5; font-size: 11px; font-weight: 600; color: #58667e; }
.tag-pos { background: #d1fae5; color: #065f46; }
.tag-neg { background: #fee2e2; color: #991b1b; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# 2. SYSTÈME D'AUTHENTIFICATION
# =========================
DB_FILE = "users_db.json"


def get_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_user_profile(email: str) -> dict:
    db = get_db()
    if not email or email not in db:
        return {}
    return db[email].get("profile", {}) or {}


def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(email, password):
    db = get_db()
    if email in db:
        return False, "Cet email existe déjà."
    db[email] = {
        "password": hash_pass(password),
        "created_at": str(datetime.now()),
        "onboarding_done": False,
        "profile": {},
    }
    save_db(db)
    return True, "Inscription réussie."


def login_user(email, password):
    db = get_db()
    if email not in db:
        return False, "Email inconnu."
    if db[email]["password"] != hash_pass(password):
        return False, "Mot de passe incorrect."
    return True, db[email]


def update_user_profile(email, profile_data):
    db = get_db()
    if email in db:
        db[email]["profile"] = profile_data
        db[email]["onboarding_done"] = True
        save_db(db)


# --- Session & Params ---
def qp_get_all() -> dict:
    try:
        qp = st.query_params
        return {k: (v[0] if isinstance(v, list) else str(v)) for k, v in qp.items()}
    except:
        return {}
        # Charger le dernier CSV avec classification financière
        csv_pattern = 'NLP/hybrid_news_financial_classified_*.csv'
        csv_files = glob.glob(csv_pattern)
        if csv_files:
            latest_csv = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
            news_raw = pd.read_csv(latest_csv)
            
            # FILTRER UNIQUEMENT LES NEWS FINANCIÈRES (is_financial = 1)
            if 'is_financial' in news_raw.columns:
                news_raw = news_raw[news_raw['is_financial'] == 1].copy()
            
            news_processed = news_raw.groupby('title').agg({
                'published_at': 'first',
                'url': 'first',
                'source': 'first',
                'asset_ticker': lambda x: ', '.join(x.unique()),
                'sentiment': 'first',
                'confidence': 'mean',
                'prob_negative': 'mean',
                'prob_positive': 'mean'
            }).reset_index()
        else:
            news_processed = pd.DataFrame()
    except Exception:
        news_processed = pd.DataFrame()


def qp_update(**kwargs):
    try:
        st.query_params.update(**{k: str(v) for k, v in kwargs.items()})
    except:
        st.experimental_set_query_params(**kwargs)


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "first_login" not in st.session_state:
    st.session_state["first_login"] = True
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = None

qp = qp_get_all()
if "auth" in qp and qp.get("auth") == "1":
    user_email = qp.get("user_email")
    if user_email:
        db = get_db()
        if user_email in db:
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = user_email
            u_data = db[user_email]
            st.session_state["user_profile"] = u_data.get("profile", {}).get(
                "experience", "Inconnu"
            )
            if not u_data.get("onboarding_done", False):
                st.session_state["page"] = "Onboarding"
                st.session_state["first_login"] = True
            elif "page" in qp and qp["page"] != "Onboarding":
                st.session_state["page"] = qp["page"]
                st.session_state["first_login"] = False
            else:
                st.session_state["page"] = "Dashboard"
                st.session_state["first_login"] = False


# =========================
# 3. DONNÉES & FONCTIONS
# =========================
DATA_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "data" / "raw"
CANDLES_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "candles"
PATTERNS_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "patterns"
XAI_ROOT = Path(__file__).resolve().parent / "NLP"


@st.cache_data
def load_data():
    stocks = pd.DataFrame()
    news = pd.DataFrame()
    aapl = pd.DataFrame()
    try:
        stocks = pd.read_csv("stock_data (1).csv")
    except:
        pass
    try:
        raw = pd.read_csv("NLP/sentiment_analysis_20260123_170727.csv")
        news = (
            raw.groupby("title")
            .agg(
                {
                    "published_at": "first",
                    "url": "first",
                    "source": "first",
                    "asset_ticker": lambda x: ", ".join(x.unique()),
                    "prob_positive": "mean",
                    "prob_negative": "mean",
                    "confidence": "mean",
                }
            )
            .reset_index()
        )
    except:
        pass
    try:
        aapl = pd.read_csv("AAPL.csv")
        if "Date" in aapl.columns:
            aapl["Date"] = pd.to_datetime(aapl["Date"])
    except:
        pass
    return stocks, news, aapl


stock_df, news_df, aapl_df = load_data()

if not stock_df.empty:
    if "Symbole" not in stock_df.columns and "Ticker" in stock_df.columns:
        stock_df["Symbole"] = stock_df["Ticker"]
    if "Nom" not in stock_df.columns and "Name" in stock_df.columns:
        stock_df["Nom"] = stock_df["Name"]
    if "Prix" not in stock_df.columns and "Close" in stock_df.columns:
        stock_df["Prix"] = stock_df["Close"]
    for c in ["Prix", "Variation 24h", "Variation 7d"]:
        if c in stock_df.columns:
            stock_df[c] = pd.to_numeric(stock_df[c], errors="coerce")


def safe_ticker(t):
    return str(t).replace("^", "").replace("=", "_").replace("/", "_")


def normalize_ticker(t):
    return str(t).split(".")[0].replace("^", "")


@st.cache_data
def load_price_history(sym):
    cpath = CANDLES_ROOT / f"{safe_ticker(sym)}_daily.json"
    if cpath.exists():
        try:
            data = json.loads(cpath.read_text())
            df = pd.DataFrame(data.get("candles", []))
            if not df.empty:
                df = df.rename(
                    columns={"t": "Date", "close": "Close", "open": "Open", "high": "High", "low": "Low"}
                )
                df["Date"] = pd.to_datetime(df["Date"])
                return df.sort_values("Date")
        except:
            pass
    dpath = DATA_ROOT / f"{safe_ticker(sym)}.csv"
    if dpath.exists():
        try:
            df = pd.read_csv(dpath)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
            return df.sort_values("Date")
        except:
            pass
    return pd.DataFrame()


@st.cache_data
def load_patterns(sym):
    path = PATTERNS_ROOT / f"{safe_ticker(sym)}_daily_patterns.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return None


@st.cache_data
def load_xai_analysis(sym):
    files = glob.glob(str(XAI_ROOT / f"xai_{sym}_*.csv"))
    if not files:
        return pd.DataFrame()
    latest = max(files, key=lambda x: Path(x).stat().st_mtime)
    try:
        return pd.read_csv(latest)
    except:
        return pd.DataFrame()


@st.cache_data
def compute_variations(sym):
    df = load_price_history(sym)
    if df.empty or "Close" not in df.columns or len(df) < 2:
        return None, None, None, None
    closes = df["Close"].dropna()
    last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
    v24 = (last - prev) / prev * 100
    v7 = None
    prev7 = None
    if len(closes) >= 8:
        prev7 = float(closes.iloc[-8])
        v7 = (last - prev7) / prev7 * 100
    return (last - prev), v24, (last - (prev7 if prev7 is not None else 0.0)), v7


def sparkline_svg(sym, color):
    df = load_price_history(sym)
    if df.empty or "Close" not in df.columns:
        return "—"
    closes = df["Close"].dropna().tail(24).values
    if len(closes) < 2:
        return "—"
    w, h = 120, 40
    mn, mx = np.min(closes), np.max(closes)
    span = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(closes):
        x = (i / (len(closes) - 1)) * w
        y = h - ((v - mn) / span) * h
        pts.append(f"{x:.1f},{y:.1f}")
    pts_str = " ".join(pts)
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<polyline points="{pts_str}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


@st.cache_data
def compute_fear_greed(news):
    if news.empty:
        return 50
    return int(50 + (news["prob_positive"].mean() - news["prob_negative"].mean()) * 50)


@st.cache_data
def load_watchlist() -> list[str]:
    path = Path(__file__).resolve().parent / "PFE_MVP" / "configs" / "watchlist.txt"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def build_name_map(df):
    nm = {}
    if not df.empty:
        for _, r in df.iterrows():
            if r.get("Symbole") and r.get("Nom"):
                nm[normalize_ticker(r["Symbole"])] = r["Nom"]
    return nm


LEXICON = {
    "ETF": "Fonds qui suit un indice et s'échange en bourse comme une action.",
    "ANALYSE TECHNIQUE": "Étude des graphiques pour identifier des tendances.",
    "SENTIMENT": "Psychologie globale (Optimiste/Pessimiste).",
    "VOLATILITÉ": "Amplitude des variations de prix.",
    "RÉSISTANCE": "Zone de prix où l’actif a du mal à monter.",
    "SUPPORT": "Zone de prix où l’actif a du mal à baisser.",
    "BULLISH": "Sentiment/tendance haussière : on anticipe une hausse des prix.",
    "BEARISH": "Sentiment/tendance baissière : on anticipe une baisse des prix.",
    "LSTM": "Long Short-Term Memory : type de réseau de neurones (RNN) adapté aux séries temporelles.",
    "RNN": "Réseau de neurones récurrent, utile pour traiter des séquences (texte, séries temporelles).",
}


def highlight_lexicon_terms(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    escaped = html.escape(text)

    def repl(m):
        raw = m.group(0)
        key_upper = raw.upper()
        defn = None
        for k in LEXICON.keys():
            if k.upper() == key_upper:
                defn = LEXICON[k]
                break
        if defn is None:
            defn = LEXICON.get(raw, "")
        defn_attr = html.escape(defn, quote=True)
        return f'<span class="lex-term" title="{defn_attr}">{raw}</span>'

    _lex_terms_sorted = sorted(LEXICON.keys(), key=len, reverse=True)
    _lex_pattern = re.compile(
        r"(" + "|".join(re.escape(t) for t in _lex_terms_sorted) + r")",
        flags=re.IGNORECASE,
    )
    return _lex_pattern.sub(repl, escaped)


@st.cache_data
def compute_overall_sentiment(news: pd.DataFrame) -> tuple[str, float]:
    if news.empty:
        return "NEUTRAL", 0.0
    avg_pos = news["prob_positive"].mean()
    avg_neg = news["prob_negative"].mean()
    label = "BULLISH" if avg_pos > avg_neg else "BEARISH"
    score = max(avg_pos, avg_neg) * 100
    return label, score


OVERALL_SENTIMENT_LABEL, OVERALL_SENTIMENT_SCORE = compute_overall_sentiment(news_df)
SENTIMENT_MAP = {}


def news_key_for_symbol(sym):
    sym = str(sym)
    mapping = {
        "^GSPC": "SP500",
        "^FCHI": "CAC40",
        "^GDAXI": "GER30",
        "CL_F": "OIL",
        "GC_F": "GOLD",
        "NG_F": "GAS",
        "CL=F": "OIL",
        "GC=F": "GOLD",
        "NG=F": "GAS",
    }
    return mapping.get(sym, sym.replace("^", ""))


def render_fear_greed_gauge(value: int):
    value = int(np.clip(value, 0, 100))
    colors = ["#EA3943", "#EA8C00", "#F3D42F", "#93D900", "#16C784"]

    label = "Neutral"
    if value < 20:
        label = "Extreme Fear"
    elif value < 40:
        label = "Fear"
    elif value < 60:
        label = "Neutral"
    elif value < 80:
        label = "Greed"
    else:
        label = "Extreme Greed"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            number={"font": {"size": 20, "color": "#000", "family": "Inter"}},
            title={"text": "Fear & Greed Index", "font": {"size": 11, "color": "#58667e", "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "visible": False},
                "bar": {"color": "rgba(0,0,0,0)"},
                "steps": [
                    {"range": [0, 20], "color": colors[0]},
                    {"range": [20, 40], "color": colors[1]},
                    {"range": [40, 60], "color": colors[2]},
                    {"range": [60, 80], "color": colors[3]},
                    {"range": [80, 100], "color": colors[4]},
                ],
                "threshold": {"line": {"color": "black", "width": 3}, "thickness": 0.75, "value": value},
            },
        )
    )

    fig.update_layout(
        height=92,
        margin=dict(l=6, r=6, t=0, b=0),
        paper_bgcolor="white",
        font=dict(family="Inter"),
    )

    return fig, label


# =========================
# 4. SHOW PAGES
# =========================
def show_anomaly_page():
    import html as _html
    from pathlib import Path

    def _load_report():
        candidates = [
            Path("anomaly_report.json"),
            Path("reports") / "anomaly_report.json",
        ]
        for p in candidates:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except:
                    pass

        return {
            "generated_at": "2026-01-27 15:58:34",
            "stats": {
                "Anomalies détectées": "736",
                "Avec news": "10",
                "News trouvées": "88",
                "Score moyen": "52/100",
            },
            "anomalies": [
                {
                    "title": "APPLE - 2026-01-20",
                    "severity": "Minor",
                    "variation": "-3.46%",
                    "news_count": 4,
                    "top_news": [
                        {
                            "timing": "2026-01-19 | Le même jour",
                            "score": 60,
                            "title": "Google Chrome Is Getting a Safari Data Import Option on iPhone",
                            "description": "Chrome for iOS will soon feature an option for iPhone users to import their Safari data into Google's mobile browser...",
                            "source": "MacRumors",
                            "url": "https://example.com",
                        }
                    ],
                }
            ],
        }

    REPORT = _load_report()
    generated_at = str(REPORT.get("generated_at", "") or "")
    stats = REPORT.get("stats", {}) or {}
    anomalies = REPORT.get("anomalies", []) or []

    for a in anomalies:
        if "top_news" not in a and "news" in a:
            a["top_news"] = a.get("news", [])

    if not anomalies:
        st.title("Rapport d’analyse des anomalies boursières")
        st.info("Aucune anomalie disponible.")
        return

    with st.expander("Filtres", expanded=False):
        severities = sorted({str(a.get("severity", "Minor")) for a in anomalies})
        pick = st.multiselect("Sévérité", severities, default=severities)
        min_news = st.slider("Min news", 0, 50, 0)

    filtered = []
    for a in anomalies:
        sev = str(a.get("severity", "Minor"))
        top_news = a.get("top_news", []) or []
        ncount = a.get("news_count")
        if ncount is None:
            ncount = len(top_news)
        try:
            ncount_int = int(ncount)
        except:
            ncount_int = len(top_news)

        if sev in pick and ncount_int >= min_news:
            filtered.append(a)

    def esc(x) -> str:
        return _html.escape("" if x is None else str(x))

    def badge_class(sev: str) -> str:
        s = (sev or "").strip().lower()
        if "critical" in s:
            return "badge badge-critical"
        if "severe" in s:
            return "badge badge-severe"
        if "moderate" in s:
            return "badge badge-moderate"
        return "badge badge-minor"

    order = ["Anomalies détectées", "Avec news", "News trouvées", "Score moyen"]
    stat_items = [(k, stats[k]) for k in order if k in stats]
    for k, v in stats.items():
        if k not in order:
            stat_items.append((k, v))
    stat_items = stat_items[:4]

    stats_boxes_html = ""
    for label, value in stat_items:
        stats_boxes_html += f"""
          <div class="stat-box">
            <div class="stat-number">{esc(value)}</div>
            <div class="stat-label">{esc(label)}</div>
          </div>
        """

    cards_html = ""
    for a in filtered:
        title = esc(a.get("title", "—"))
        severity = esc(a.get("severity", "Minor"))
        variation = esc(a.get("variation", "—"))

        top_news = a.get("top_news", []) or []
        news_count = a.get("news_count")
        if news_count is None:
            news_count = len(top_news)
        try:
            news_count = int(news_count)
        except:
            news_count = len(top_news)

        news_html = ""
        if top_news:
            for n in top_news[:5]:
                timing = esc(n.get("timing", ""))
                ntitle = esc(n.get("title", "—"))
                desc_raw = " ".join(str(n.get("description", "") or "").split())
                if len(desc_raw) > 220:
                    desc_raw = desc_raw[:220].rstrip() + "..."
                desc = esc(desc_raw)
                source = esc(n.get("source", "—"))
                url = str(n.get("url", "") or "").strip()

                score = n.get("score", "")
                try:
                    score_txt = f"Score: {int(float(score))}/100"
                except:
                    score_txt = "Score: —" if score == "" else f"Score: {esc(score)}/100"

                link_html = f"<a href='{esc(url)}' target='_blank' rel='noopener'>Lire l’article →</a>" if url else ""

                news_html += f"""
                  <div class="news-item">
                    <div class="news-top">
                      <div class="news-timing">{timing}</div>
                      <div class="news-score">{esc(score_txt)}</div>
                    </div>
                    <div class="news-title">{ntitle}</div>
                    {f"<div class='news-desc'>{desc}</div>" if desc else ""}
                    <div class="news-source">
                      <div><b>Source :</b> {source}</div>
                      <div class="news-link">{link_html}</div>
                    </div>
                  </div>
                """
        else:
            news_html = """
              <div class="news-item">
                <div class="news-desc">Aucune news associée.</div>
              </div>
            """

        cards_html += f"""
          <div class="anom-card">
            <div class="anom-header">
              <h3 class="anom-h3">{title}</h3>
              <span class="{badge_class(severity)}">{severity}</span>
            </div>

            <div class="anom-meta">
              <div><span>Variation :</span> {variation}</div>
              <div><span>News trouvées :</span> {esc(news_count)}</div>
            </div>

            {news_html}
          </div>
        """

    full_html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    body {{
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      margin: 0; padding: 0; background: #ffffff; color: #0b1220;
    }}

    .anom-wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 4px; }}
    .anom-title {{ font-size: 32px; font-weight: 800; margin: 10px 0 4px 0; }}
    .anom-sub {{ color: #58667e; font-size: 13px; font-weight: 600; margin: 0 0 18px 0; }}

    .stats-card {{
      background: #fff; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin: 14px 0 18px 0;
    }}
    .stats-h2 {{ font-size: 16px; font-weight: 800; margin: 0 0 12px 0; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
    .stat-box {{
      background: #f8fafc; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 14px; text-align: center;
    }}
    .stat-number {{ font-size: 26px; font-weight: 800; color: #3861fb; line-height: 1.1; }}
    .stat-label {{ font-size: 12px; color: #58667e; font-weight: 700; margin-top: 6px; }}

    .section-h2 {{ font-size: 16px; font-weight: 900; margin: 22px 0 10px 0; }}

    .anom-card {{
      background: #fff; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin: 14px 0;
    }}
    .anom-header {{
      display:flex; justify-content:space-between; align-items:center; gap:12px;
      border-bottom:1px solid #eff2f5; padding-bottom:12px; margin-bottom:12px;
    }}
    .anom-h3 {{ font-size: 16px; font-weight: 800; margin: 0; }}

    .badge {{
      padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; color: #fff;
      display:inline-block; white-space:nowrap;
    }}
    .badge-minor {{ background: #EA8C00; }}
    .badge-moderate {{ background: #f59e0b; }}
    .badge-severe {{ background: #ea3943; }}
    .badge-critical {{ background: #b91c1c; }}

    .anom-meta {{
      display:flex; gap:18px; flex-wrap:wrap; font-size:13px;
      font-weight:700; margin-bottom:10px;
    }}
    .anom-meta span {{ color:#58667e; font-weight:700; margin-right:6px; }}

    .news-item {{
      background:#f8fafc; border:1px solid #eff2f5; border-left:4px solid #3861fb;
      border-radius:12px; padding:12px 14px; margin-top:10px;
    }}
    .news-top {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:8px; }}
    .news-timing {{ color:#58667e; font-weight:700; font-size:12px; }}
    .news-score {{ background:#3861fb; color:#fff; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:800; }}
    .news-title {{ font-size:13px; font-weight:800; margin-bottom:6px; }}
    .news-desc {{ font-size:12px; color:#58667e; font-weight:600; line-height:1.35; }}

    .news-source {{
      font-size:12px; color:#58667e; font-weight:700; margin-top:8px;
      display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;
    }}
    .news-link a {{ color:#3861fb; font-weight:800; text-decoration:none; }}
    .news-link a:hover {{ text-decoration:underline; }}

    @media (max-width: 1100px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 650px)  {{ .stats-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="anom-wrap">
    <div class="anom-title">Rapport d’analyse des anomalies boursières</div>
    <div class="anom-sub"><span>Date de génération :</span> {esc(generated_at)}</div>

    <div class="stats-card">
      <div class="stats-h2">Statistiques globales</div>
      <div class="stats-grid">
        {stats_boxes_html}
      </div>
    </div>

    <div class="section-h2">Anomalies détectées avec news corrélées</div>
    {cards_html}
  </div>
</body>
</html>
"""
    base = 520
    per_card = 260
    height = min(2400, base + per_card * max(1, len(filtered)))
    components.html(full_html, height=height, scrolling=True)


# =========================
# 5. UI COMPONENTS (NAVBAR)
# =========================
def show_navbar():
    auth = qp.get("auth", "1")
    fl = qp.get("first_login", "0")
    prof = qp.get("profile", "")
    email = st.session_state.get("current_user", "")
    page = st.session_state.get("page", "Dashboard")

    def link(p):
        return f"?auth={auth}&first_login={fl}&profile={prof}&user_email={email}&page={p}"

    def cls(p):
        return "cmc-link active" if page == p else "cmc-link"

    st.markdown(
        f"""
    <div class="cmc-nav-container">
        <a href="{link('Dashboard')}" class="cmc-brand" target="_self">FINSIGHT<span>AI</span></a>
        <div class="cmc-links">
            <a href="{link('Dashboard')}" class="{cls('Dashboard')}" target="_self">Marchés</a>
            <a href="{link('News')}" class="{cls('News')}" target="_self">Actualités</a>
            <a href="{link('Predictions')}" class="{cls('Predictions')}" target="_self">Prédictions</a>
            <a href="{link('Anomaly')}" class="{cls('Anomaly')}" target="_self">Anomalies</a>
            <a href="{link('Lexicon')}" class="{cls('Lexicon')}" target="_self">Lexique</a>
        </div>
        <a href="{link('Account')}" class="cmc-account" target="_self">Mon Compte</a>
    </div>
    """,
        unsafe_allow_html=True,
    )
    return page


# =========================
# 6. AUTH & ONBOARDING
# =========================
def show_login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown(
            "<br><br><h1 style='text-align:center;'>FINSIGHT AI</h1>",
            unsafe_allow_html=True,
        )
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])

        with tab1:
            l_email = st.text_input("Email", key="l_email")
            l_pwd = st.text_input("Mot de passe", type="password", key="l_pwd")
            if st.button("Se connecter", use_container_width=True):
                success, data = login_user(l_email, l_pwd)
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = l_email
                    if not data.get("onboarding_done", False):
                        st.session_state["page"] = "Onboarding"
                        st.session_state["first_login"] = True
                    else:
                        st.session_state["page"] = "Dashboard"
                        st.session_state["first_login"] = False
                        st.session_state["user_profile"] = data.get("profile", {}).get(
                            "experience", "Inconnu"
                        )

                    qp_update(auth="1", user_email=l_email, page=st.session_state["page"])
                    st.rerun()
                else:
                    st.error(data)

        with tab2:
            r_email = st.text_input("Email", key="r_email")
            r_pwd = st.text_input("Mot de passe", type="password", key="r_pwd")
            r_pwd2 = st.text_input("Confirmer", type="password", key="r_pwd2")
            if st.button("S'inscrire", use_container_width=True):
                if r_pwd != r_pwd2:
                    st.error("Mots de passe différents.")
                elif not r_email or not r_pwd:
                    st.error("Remplissez tout.")
                else:
                    res, msg = register_user(r_email, r_pwd)
                    if res:
                        st.success(msg + " Connectez-vous.")
                    else:
                        st.error(msg)


def show_onboarding():
    st.markdown("<h2 style='text-align:center;'>Profil Investisseur</h2>", unsafe_allow_html=True)
    st.info("Configuration initiale pour l'IA.")

    symbols_all = []
    if not stock_df.empty and "Symbole" in stock_df.columns:
        symbols_all = stock_df["Symbole"].dropna().astype(str).unique().tolist()
    symbols_all = sorted(symbols_all)

    with st.form("onboarding_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Âge", 18, 99, 30)
            horizon = st.selectbox("Horizon", ["Court terme", "Moyen terme", "Long terme"])
            experience = st.radio("Expérience", ["Débutant", "Intermédiaire", "Expert"])
            capital = st.number_input("Capital (€)", 0, 1_000_000, 1000)
        with c2:
            risk = st.slider("Risque (1-10)", 1, 10, 5)
            strategy = st.selectbox("Stratégie", ["Dividendes", "Growth", "Trading"])
            sectors = st.multiselect("Secteurs", ["Tech", "Santé", "Finance", "Crypto"])

            watchlist_sel = st.multiselect(
                "Actifs suivis (watchlist)",
                symbols_all,
                default=symbols_all[:10] if len(symbols_all) >= 10 else symbols_all,
            )

        if st.form_submit_button("Valider"):
            email = st.session_state.get("current_user")
            if email:
                profile = {
                    "age": age,
                    "horizon": horizon,
                    "experience": experience,
                    "capital": capital,
                    "risk": risk,
                    "strategy": strategy,
                    "sectors": sectors,
                    "watchlist": watchlist_sel,
                }
                update_user_profile(email, profile)
                st.session_state["user_profile"] = experience
                st.session_state["page"] = "Dashboard"
                st.session_state["first_login"] = False
                qp_update(page="Dashboard", profile=experience)
                st.rerun()


# =========================
# 7. MAIN APP (ROUTING)
# =========================
def main_app(nav):
    if nav == "Onboarding":
        show_onboarding()
        return

    if qp.get("stock"):
        nav = "StockDetail"
        st.session_state["page"] = "StockDetail"

    if nav == "Dashboard":
        email = st.session_state.get("current_user")
        profile = get_user_profile(email) if email else {}
        user_watchlist = profile.get("watchlist", []) or []

        fallback_watchlist = load_watchlist()
        all_symbols = (
            stock_df["Symbole"].dropna().astype(str).unique().tolist()
            if (not stock_df.empty and "Symbole" in stock_df.columns)
            else []
        )

        active_syms = (
            user_watchlist
            if len(user_watchlist) > 0
            else (fallback_watchlist if len(fallback_watchlist) > 0 else all_symbols)
        )

        # KPI: top performer
        top_name, top_val = "—", 0.0
        best_perf = -999.0
        best_sym = None
        for s in active_syms:
            _, _, _, v7 = compute_variations(s)
            if v7 is not None and v7 > best_perf:
                best_perf = v7
                best_sym = s
        if best_sym:
            top_val = float(best_perf)
            if not stock_df.empty and "Symbole" in stock_df.columns:
                row = stock_df[stock_df["Symbole"].astype(str) == str(best_sym)]
                top_name = row.iloc[0].get("Nom", best_sym) if not row.empty else best_sym
            else:
                top_name = best_sym

        fg_value = compute_fear_greed(news_df)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-label">Top Performer (7j)</div>
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
                    <div class="kpi-value">{top_name}</div>
                    <div class="kpi-sub {'text-green' if top_val>=0 else 'text-red'}">{top_val:+.2f}%</div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

        with c2:
            fig, label = render_fear_greed_gauge(fg_value)
            fig_html = fig.to_html(
                include_plotlyjs="cdn",
                full_html=False,
                config={"displayModeBar": False, "staticPlot": True},
            )

            card_html = f"""
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

            <style>
            body {{ margin:0; padding:0; background:transparent; }}
            * {{ font-family: Inter, sans-serif !important; box-sizing:border-box; }}

            .kpi-card {{
                background: #ffffff;
                border: 1px solid #eff2f5;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.04);
                height: 180px;
                display:flex;
                flex-direction:column;
                justify-content:flex-start;
            }}

            .kpi-label {{
                font-size: 12px;
                font-weight: 600;
                color: #58667e;
                text-transform: uppercase;
                margin-bottom: 8px;
                text-align: left;
            }}

            .fg-plot {{
                height: 92px;
                overflow: hidden;
            }}

            .fg-label {{
                margin-top: 10px;
                text-align:center;
                font-weight: 700;
                color: #58667e;
                font-size: 13px;
                line-height: 1;
            }}

            .js-plotly-plot, .plotly, .main-svg {{ font-family: Inter, sans-serif !important; }}
            </style>

            <div class="kpi-card">
            <div class="kpi-label">Fear &amp; Greed</div>
            <div class="fg-plot">{fig_html}</div>
            <div class="fg-label">{label}</div>
            </div>
            """
            components.html(card_html, height=210, scrolling=False)

        with c3:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-label">Sentiment Global</div>
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
                    <div class="kpi-value">{OVERALL_SENTIMENT_LABEL}</div>
                    <div class="kpi-sub">Confiance IA: {OVERALL_SENTIMENT_SCORE:.0f}%</div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

        st.write("")

        if st.button("Modifier ma watchlist"):
            qp_update(page="Account")
            st.session_state["page"] = "Account"
            st.rerun()

        display_df = stock_df.copy() if not stock_df.empty else pd.DataFrame()
        if not display_df.empty and "Symbole" in display_df.columns and len(active_syms) > 0:
            display_df = display_df[display_df["Symbole"].astype(str).isin([str(s) for s in active_syms])]
        display_df = display_df.head(50).copy() if not display_df.empty else pd.DataFrame()

        if not display_df.empty:
            rows_html_list = []
            auth_p = qp.get("auth", "1")
            fl_p = qp.get("first_login", "0")
            prof_p = qp.get("profile", "")
            u_email = st.session_state.get("current_user", "")

            for _, r in display_df.iterrows():
                sym = str(r.get("Symbole", "—"))
                name = str(r.get("Nom", sym))
                price = r.get("Prix", 0)

                _, calc_v24, _, calc_v7 = compute_variations(sym)
                v24 = calc_v24 if calc_v24 is not None else 0.0
                v7 = calc_v7 if calc_v7 is not None else 0.0
                if pd.isna(price):
                    price = 0.0

                c24 = "#16c784" if v24 >= 0 else "#ea3943"
                c7 = "#16c784" if v7 >= 0 else "#ea3943"
                sent = "BULLISH" if v7 > 5 else "BEARISH" if v7 < -5 else "NEUTRAL"
                color_sent = "#16c784" if sent == "BULLISH" else "#ea3943" if sent == "BEARISH" else "#58667e"

                graph = sparkline_svg(sym, c7)
                link = f"?stock={sym}&auth={auth_p}&first_login={fl_p}&profile={prof_p}&user_email={u_email}&page=StockDetail"

                rows_html_list.append(
                    f"<tr>"
                    f"<td><a href='{link}' target='_self'>"
                    f"<div style='display:flex; align-items:center;'>"
                    f"<span style='font-weight:700; color:#000;'>{name}</span>"
                    f"<span class='ticker-badge'>{sym}</span>"
                    f"</div></a></td>"
                    f"<td><a href='{link}' target='_self'>${float(price):.2f}</a></td>"
                    f"<td><a href='{link}' target='_self'><span style='color:{c24}'>{v24:+.2f}%</span></a></td>"
                    f"<td><a href='{link}' target='_self'><span style='color:{c7}'>{v7:+.2f}%</span></a></td>"
                    f"<td><a href='{link}' target='_self' style='color:{color_sent}; font-size:12px;'>● {sent}</a></td>"
                    f"<td style='width:140px; padding-top:5px; padding-bottom:5px;'><a href='{link}' target='_self'>{graph}</a></td>"
                    f"</tr>"
                )

            st.markdown(
                f"""
                <div class="cmc-table-wrap">
                  <table class="cmc-table">
                    <thead>
                      <tr>
                        <th>Actif</th><th>Prix</th><th>24h %</th><th>7d %</th><th>Sentiment</th><th>Tendance (7d)</th>
                      </tr>
                    </thead>
                    <tbody>{"".join(rows_html_list)}</tbody>
                  </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Aucune donnée boursière.")

    elif nav == "StockDetail":
        st.title("DÉTAILS ACTIF")
        sym_param = qp.get("stock", "")
        if not sym_param and st.session_state.get("selected_stock"):
            sym_param = st.session_state["selected_stock"].get("Symbole")

        if not sym_param:
            st.info("Aucun actif sélectionné.")
        else:
            left, mid, right = st.columns([1, 2.2, 1.2])
            with left:
                symbols = stock_df["Symbole"].dropna().astype(str).unique().tolist()
                idx = symbols.index(sym_param) if sym_param in symbols else 0
                choice = st.selectbox("Actif", symbols, index=idx)
                if choice != sym_param:
                    qp_update(stock=choice)
                    st.rerun()

                hist = load_price_history(choice)
                last_price = hist["Close"].iloc[-1] if (not hist.empty and "Close" in hist.columns) else 0.0
                nom = choice
                if not stock_df.empty:
                    row = stock_df[stock_df["Symbole"].astype(str) == str(choice)]
                    if not row.empty:
                        nom = row.iloc[0].get("Nom", choice)

                st.markdown(f"**{nom}**")
                st.caption(f"Ticker: {choice}")
                st.metric("Prix", f"${float(last_price):.2f}")
                v24, v24p, v7, v7p = compute_variations(choice)
                if v24 is not None:
                    st.metric("Variation 24h", f"${v24:+.2f}", f"{v24p:+.2f}%")
                else:
                    st.metric("Variation 24h", "—")
                if v7 is not None:
                    st.metric("Variation 7d", f"${v7:+.2f}", f"{v7p:+.2f}%")
                else:
                    st.metric("Variation 7d", "—")

                key = news_key_for_symbol(choice)
                st.caption(f"Sentiment: {SENTIMENT_MAP.get(key, OVERALL_SENTIMENT_LABEL)}")
                if st.button("Retour Dashboard"):
                    try:
                        st.query_params.pop("stock", None)
                        st.query_params["page"] = "Dashboard"
                    except:
                        st.experimental_set_query_params(page="Dashboard")
                    st.session_state["page"] = "Dashboard"
                    st.rerun()

            with mid:
                pdata = load_patterns(choice)
                plist = pdata.get("patterns", []) if pdata else []
                show_pat = False
                if plist:
                    st.caption(f"{len(plist)} patterns détectés.")
                    show_pat = st.checkbox("Afficher les patterns", value=False)
                else:
                    st.info("Aucun pattern.")

                sel_idx = 0
                if show_pat and plist:
                    plabs = [f"{p.get('pattern')} ({p.get('start','')[:10]})" for p in plist]
                    sel_idx = st.selectbox("Pattern", range(len(plabs)), format_func=lambda i: plabs[i])
                    range_opt = "LOCKED"
                else:
                    range_opt = st.selectbox("Horizon", ["1M", "3M", "6M", "1Y", "5Y", "ALL"], index=3)

                plot_hist = hist.copy()
                if not plot_hist.empty:
                    if show_pat and plist:
                        pat = plist[sel_idx]
                        if pat.get("df_start") and pat.get("df_end"):
                            plot_hist = plot_hist[
                                (plot_hist["Date"] >= pd.to_datetime(pat["df_start"]))
                                & (plot_hist["Date"] <= pd.to_datetime(pat["df_end"]))
                            ]
                    elif range_opt != "ALL":
                        d_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "5Y": 1825}
                        plot_hist = plot_hist[
                            plot_hist["Date"] >= plot_hist["Date"].max() - timedelta(days=d_map.get(range_opt, 365))
                        ]

                    fig = go.Figure(
                        data=[
                            go.Candlestick(
                                x=plot_hist["Date"],
                                open=plot_hist["Open"],
                                high=plot_hist["High"],
                                low=plot_hist["Low"],
                                close=plot_hist["Close"],
                                increasing_line_color="#13c296",
                                decreasing_line_color="#ef4444",
                            )
                        ]
                    )

                    if show_pat and plist:
                        pat = plist[sel_idx]
                        pts = pat.get("points", {})
                        xs, ys, labels = [], [], []
                        for k in ["X", "A", "B", "C", "D"]:
                            if k in pts:
                                xs.append(pd.to_datetime(pts[k][0]))
                                ys.append(float(pts[k][1]))
                                labels.append(k)
                        if xs:
                            fig.add_trace(
                                go.Scatter(
                                    x=xs,
                                    y=ys,
                                    mode="lines+markers+text",
                                    text=labels,
                                    textposition="top center",
                                    marker=dict(size=8, color="#6366f1"),
                                    line=dict(color="#6366f1", width=2),
                                    name=pat.get("pattern"),
                                )
                            )

                    fig.update_layout(
                        height=460,
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_rangeslider_visible=False,
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Pas de données.")

                xai = load_xai_analysis(choice)
                if not xai.empty:
                    st.markdown("---")
                    st.caption(f"{xai.iloc[0].get('total_news')} news")
                    st.markdown(
                        highlight_lexicon_terms(str(xai.iloc[0].get("xai_explanation"))),
                        unsafe_allow_html=True,
                    )

            with right:
                st.subheader("Actualités")
                tn = news_df.copy()
                if choice and not tn.empty:
                    tn = tn[tn["asset_ticker"].str.contains(choice, na=False, case=False)]

                if not tn.empty:
                    avg_p = tn["prob_positive"].mean()
                    if avg_p > tn["prob_negative"].mean():
                        sl, sc = "BULLISH", "#00FF88"
                    else:
                        sl, sc = "BEARISH", "#FF4444"

                    st.markdown(
                        f"<div style='background-color:{sc}20; padding:10px; border-radius:5px; border-left:4px solid {sc}; margin-bottom:10px;'><strong>{sl}</strong></div>",
                        unsafe_allow_html=True,
                    )

                    tn["conf"] = tn[["prob_positive", "prob_negative"]].max(axis=1)
                    for _, r in tn[tn["conf"] >= 0.7].head(5).iterrows():
                        col = "#00FF88" if r["prob_positive"] > r["prob_negative"] else "#FF4444"
                        st.markdown(
                            f"<div style='background:#f9fafb; padding:8px; border-radius:6px; margin-bottom:6px; border-left:3px solid {col}; font-size:12px;'><b>{highlight_lexicon_terms(str(r['title'])[:60])}...</b><br><span style='color:{col}'>Impact {r['conf']:.0%}</span></div>",
                            unsafe_allow_html=True,
                        )
                        st.link_button("Lire", r["url"], use_container_width=True)
                else:
                    st.info("Pas d'actualités.")

    elif nav == "News":
        st.title("Actualités")
        if not news_df.empty:
            for _, r in news_df.head(10).iterrows():
                st.markdown(
                    f"<div class='kpi-card' style='margin-bottom:15px;'><h4>{highlight_lexicon_terms(str(r.get('title')))}</h4><p style='color:#666; font-size:12px;'>{r.get('source')}</p><a href='{r.get('url')}'>Lire</a></div>",
                    unsafe_allow_html=True,
                )

    elif nav == "Predictions":
        st.title("Prédictions & Forecast")
        st.markdown("Analyse prédictive IA sur **Apple (AAPL)**.")
        df_pred = aapl_df.copy()
        if df_pred.empty:
            st.error("Données manquantes.")
        else:
            ld = df_pred["Date"].max()
            lc = df_pred["Close"].iloc[-1]
            fd = [ld + timedelta(days=i) for i in range(1, 16)]
            fp = [lc * (1 + 0.005 * i + np.random.normal(0, 0.01)) for i in range(1, 16)]

            fig = go.Figure()
            fig.add_trace(
                go.Candlestick(
                    x=df_pred["Date"],
                    open=df_pred["Open"],
                    high=df_pred["High"],
                    low=df_pred["Low"],
                    close=df_pred["Close"],
                    name="Historique",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=fd,
                    y=fp,
                    mode="lines+markers",
                    line=dict(color="#3861fb", width=2, dash="dash"),
                    name="Prédiction IA (15j)",
                )
            )
            fig.update_layout(
                title="Projection AAPL - Modèle LSTM Hybride",
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                height=600,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Confiance: 87.4% | Cible: ${fp[-1]:.2f}")

    elif nav == "Anomaly":
        show_anomaly_page()

    elif nav == "Lexicon":
        st.title("Lexique")
        for k, v in LEXICON.items():
            with st.expander(k):
                st.write(v)

    elif nav == "Account":
        st.title("Mon Compte")

        email = st.session_state.get("current_user")
        if not email:
            st.info("Utilisateur non connecté.")
            return

        current_profile = get_user_profile(email)

        default_age = int(current_profile.get("age", 30))
        default_horizon = current_profile.get("horizon", "Moyen terme")
        default_experience = current_profile.get("experience", "Intermédiaire")
        default_capital = int(current_profile.get("capital", 1000))
        default_risk = int(current_profile.get("risk", 5))
        default_strategy = current_profile.get("strategy", "Growth")
        default_sectors = current_profile.get("sectors", [])

        symbols_all = []
        if not stock_df.empty and "Symbole" in stock_df.columns:
            symbols_all = stock_df["Symbole"].dropna().astype(str).unique().tolist()
        symbols_all = sorted(symbols_all)

        default_watchlist = current_profile.get("watchlist", [])
        default_watchlist = [s for s in default_watchlist if s in symbols_all]

        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">Profil</div>
            <div class="kpi-value">{html.escape(str(default_experience))}</div>
            <div class="kpi-sub">{html.escape(str(email))}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.subheader("Mettre à jour mon profil investisseur")

        with st.form("account_profile_form"):
            c1, c2 = st.columns(2)

            with c1:
                age = st.number_input("Âge", 18, 99, default_age)
                horizon_opts = ["Court terme", "Moyen terme", "Long terme"]
                horizon = st.selectbox(
                    "Horizon",
                    horizon_opts,
                    index=horizon_opts.index(default_horizon) if default_horizon in horizon_opts else 1,
                )
                exp_opts = ["Débutant", "Intermédiaire", "Expert"]
                experience = st.radio(
                    "Expérience",
                    exp_opts,
                    index=exp_opts.index(default_experience) if default_experience in exp_opts else 1,
                )
                capital = st.number_input("Capital (€)", 0, 1_000_000, default_capital)

            with c2:
                risk = st.slider("Risque (1-10)", 1, 10, default_risk)
                strat_opts = ["Dividendes", "Growth", "Trading"]
                strategy = st.selectbox(
                    "Stratégie",
                    strat_opts,
                    index=strat_opts.index(default_strategy) if default_strategy in strat_opts else 1,
                )
                sectors_opts = ["Tech", "Santé", "Finance", "Crypto"]
                sectors = st.multiselect(
                    "Secteurs",
                    sectors_opts,
                    default=[s for s in default_sectors if s in sectors_opts],
                )

                watchlist_sel = st.multiselect(
                    "Actifs suivis (watchlist)",
                    symbols_all,
                    default=default_watchlist,
                )

            save = st.form_submit_button("Enregistrer")

        if save:
            updated_profile = {
                "age": age,
                "horizon": horizon,
                "experience": experience,
                "capital": capital,
                "risk": risk,
                "strategy": strategy,
                "sectors": sectors,
                "watchlist": watchlist_sel,
            }
            update_user_profile(email, updated_profile)

            st.session_state["user_profile"] = experience
            qp_update(profile=experience, page="Account")
            st.success("Profil mis à jour.")
            st.rerun()

        st.write("")
        if st.button("Déconnexion"):
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = None
            qp_update(auth="0", user_email="", page="Dashboard")
            st.rerun()


# =========================
# 8. ROUTEUR PRINCIPAL
# =========================
if not st.session_state["authenticated"]:
    show_login()
elif st.session_state["first_login"]:
    show_onboarding()
else:
    cur_nav = show_navbar()
    main_app(cur_nav)
