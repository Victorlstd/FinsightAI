import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta
from pathlib import Path
import glob

# --- 1. CONFIGURATION (Source 45) ---
st.set_page_config(
    page_title="Finsight AI", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
<style>
.block-container {
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- 2. GESTION D'ÉTAT + PERSISTENCE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'first_login' not in st.session_state:
    st.session_state['first_login'] = True
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = "Dashboard"

# Persistance locale (navigateur) via query params
try:
    qp = st.query_params
    if "auth" in qp:
        st.session_state["authenticated"] = qp.get("auth") == "1"
    if "first_login" in qp:
        st.session_state["first_login"] = qp.get("first_login") == "1"
    if "profile" in qp:
        st.session_state["user_profile"] = qp.get("profile") or None
except Exception:
    qp = st.experimental_get_query_params()
    if "auth" in qp:
        st.session_state["authenticated"] = qp.get("auth", ["0"])[0] == "1"
    if "first_login" in qp:
        st.session_state["first_login"] = qp.get("first_login", ["1"])[0] == "1"
    if "profile" in qp:
        st.session_state["user_profile"] = qp.get("profile", [None])[0]

# Si l'etat est deja valide, force les query params pour survivre aux reloads
if st.session_state.get("authenticated") and not st.session_state.get("first_login"):
    try:
        st.query_params.update(
            auth="1",
            first_login="0",
            profile=st.session_state.get("user_profile") or "",
        )
    except Exception:
        st.experimental_set_query_params(
            auth="1",
            first_login="0",
            profile=st.session_state.get("user_profile") or "",
        )

# --- 3. CHARGEMENT DES DONNÉES (Source 129, 131) ---
@st.cache_data
def load_and_process_data():
    stocks = pd.DataFrame()
    news_processed = pd.DataFrame()
    aapl = pd.DataFrame()

    try:
        stocks = pd.read_csv('stock_data (1).csv')
    except Exception:
        stocks = pd.DataFrame()

    try:
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

    try:
        aapl = pd.read_csv('AAPL.csv')
        if 'Date' in aapl.columns:
            aapl['Date'] = pd.to_datetime(aapl['Date'])
    except Exception:
        aapl = pd.DataFrame()

    return stocks, news_processed, aapl

stock_df, news_df, aapl_df = load_and_process_data()

# --- 3b. NORMALISATION COLONNES ---
def normalize_stock_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    def first_col(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    name_col = first_col(["Nom", "Name", "Company", "Asset", "Symbole", "Ticker"])
    symbol_col = first_col(["Symbole", "Ticker", "Symbol", "Code"])
    price_col = first_col(["Prix", "Prix actuel", "Price", "Close", "Last"])
    var24_col = first_col(["Variation 24h", "Variation %", "Variation", "Change %", "Change 24h"])
    var7_col = first_col(["Variation 7d", "Change 7d"])
    sentiment_col = first_col(["Sentiment", "Sentiment global", "Mood"])

    if name_col and name_col != "Nom":
        df["Nom"] = df[name_col]
    if symbol_col and symbol_col != "Symbole":
        df["Symbole"] = df[symbol_col]
    if price_col and price_col != "Prix":
        df["Prix"] = pd.to_numeric(df[price_col], errors="coerce")
    if var24_col and var24_col != "Variation 24h":
        df["Variation 24h"] = pd.to_numeric(df[var24_col], errors="coerce")
    if var7_col and var7_col != "Variation 7d":
        df["Variation 7d"] = pd.to_numeric(df[var7_col], errors="coerce")

    if "Variation 7d" not in df.columns:
        df["Variation 7d"] = np.nan
    if "Variation 24h" not in df.columns:
        df["Variation 24h"] = np.nan
    if "Prix" not in df.columns:
        df["Prix"] = np.nan
    if "Nom" not in df.columns:
        df["Nom"] = "—"
    if "Symbole" not in df.columns:
        df["Symbole"] = "—"

    if "Sentiment" not in df.columns:
        if sentiment_col:
            df["Sentiment"] = df[sentiment_col]
        else:
            df["Sentiment"] = "Neutre"

    if "Graph" not in df.columns:
        def arrow(x):
            if pd.isna(x):
                return "—"
            return "⬆️" if x > 0 else "⬇️" if x < 0 else "→"

        df["Graph"] = df["Variation 24h"].apply(arrow)

    return df


stock_df = normalize_stock_df(stock_df)

# --- 3c. SENTIMENT GLOBAL (NLP) ---
@st.cache_data
def compute_sentiment_map(news: pd.DataFrame) -> dict:
    if news.empty:
        return {}
    required = {"asset_ticker", "prob_positive", "prob_negative"}
    if not required.issubset(set(news.columns)):
        return {}

    def label_from_row(row):
        if row["prob_positive"] > row["prob_negative"]:
            return "🟢 BULLISH"
        if row["prob_negative"] > row["prob_positive"]:
            return "🔴 BEARISH"
        return "🟡 NEUTRAL"

    grouped = news.groupby("asset_ticker").agg(
        prob_positive=("prob_positive", "mean"),
        prob_negative=("prob_negative", "mean"),
    ).reset_index()
    grouped["sentiment_label"] = grouped.apply(label_from_row, axis=1)
    return dict(zip(grouped["asset_ticker"], grouped["sentiment_label"]))


SENTIMENT_MAP = compute_sentiment_map(news_df)


@st.cache_data
def compute_overall_sentiment(news: pd.DataFrame) -> tuple[str, float]:
    if news.empty:
        return "—", 0.0
    avg_pos = news["prob_positive"].mean()
    avg_neg = news["prob_negative"].mean()
    label = "🟢 BULLISH" if avg_pos > avg_neg else "🔴 BEARISH"
    score = max(avg_pos, avg_neg) * 100
    return label, score


@st.cache_data
def top_positive_news_title(news: pd.DataFrame) -> str:
    if news.empty or "prob_positive" not in news.columns or "title" not in news.columns:
        return "—"
    row = news.loc[news["prob_positive"].idxmax()]
    title = row["title"]
    return title[:40] + "…" if isinstance(title, str) else "—"


OVERALL_SENTIMENT_LABEL, OVERALL_SENTIMENT_SCORE = compute_overall_sentiment(news_df)


@st.cache_data
def load_watchlist() -> list[str]:
    path = Path(__file__).resolve().parent / "PFE_MVP" / "configs" / "watchlist.txt"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def build_name_map(df: pd.DataFrame) -> dict:
    name_map = {}
    if df.empty:
        return name_map
    for _, row in df.iterrows():
        sym = row.get("Symbole", "")
        name = row.get("Nom", "")
        if sym and name:
            name_map[normalize_ticker(sym)] = name
    return name_map

# --- 3c. HISTORIQUE PRIX ---
DATA_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "data" / "raw"
CANDLES_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "candles"
PATTERNS_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "patterns"
XAI_ROOT = Path(__file__).resolve().parent / "NLP"

def safe_ticker(ticker: str) -> str:
    return str(ticker).replace("^", "").replace("=", "_").replace("/", "_")

@st.cache_data
def load_price_history(sym: str) -> pd.DataFrame:
    candle_path = CANDLES_ROOT / f"{safe_ticker(sym)}_daily.json"
    if candle_path.exists():
        try:
            payload = json.loads(candle_path.read_text())
            candles = payload.get("candles", [])
            if candles:
                df = pd.DataFrame(candles)
                df = df.rename(
                    columns={
                        "t": "Date",
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                    }
                )
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.sort_values("Date")
                return df
        except Exception:
            pass

    path = DATA_ROOT / f"{safe_ticker(sym)}.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
    return df


@st.cache_data
def load_patterns(sym: str) -> dict | None:
    path = PATTERNS_ROOT / f"{safe_ticker(sym)}_daily_patterns.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


@st.cache_data
def compute_variations(sym: str) -> tuple[float | None, float | None, float | None, float | None]:
    df = load_price_history(sym)
    if df.empty or "Close" not in df.columns:
        return None, None, None, None
    closes = df["Close"].dropna()
    if len(closes) < 2:
        return None, None, None, None

    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2])
    v24_abs = last - prev
    v24_pct = (v24_abs / prev) * 100 if prev else None

    if len(closes) >= 8:
        prev7 = float(closes.iloc[-8])
        v7_abs = last - prev7
        v7_pct = (v7_abs / prev7) * 100 if prev7 else None
    else:
        v7_abs = None
        v7_pct = None

    return v24_abs, v24_pct, v7_abs, v7_pct


def news_key_for_symbol(sym: str) -> str:
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


def normalize_ticker(sym: str) -> str:
    sym = str(sym).upper()
    sym = sym.replace("^", "")
    sym = sym.replace("=F", "")
    if "." in sym:
        sym = sym.split(".")[0]
    return sym


def sparkline_svg(sym: str, color: str, width: int = 110, height: int = 32, points: int = 24) -> str:
    df = load_price_history(sym)
    if df.empty or "Close" not in df.columns:
        return "—"
    if "Date" in df.columns:
        cutoff = df["Date"].max() - pd.Timedelta(days=90)
        df = df[df["Date"] >= cutoff]
    closes = df["Close"].dropna().tail(points)
    if len(closes) < 2:
        return "—"
    vals = closes.to_numpy()
    vmin = float(np.min(vals))
    vmax = float(np.max(vals))
    span = vmax - vmin if vmax != vmin else 1.0
    xs = np.linspace(0, width, len(vals))
    ys = height - ((vals - vmin) / span) * height
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    line_color = color
    return (
        f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
        f"xmlns='http://www.w3.org/2000/svg'>"
        f"<polyline fill='none' stroke='{line_color}' stroke-width='2' points='{pts}' />"
        f"</svg>"
    )
@st.cache_data
def load_xai_analysis(sym: str) -> pd.DataFrame:
    """Charge l'analyse XAI pour un ticker donné"""
    pattern = str(XAI_ROOT / f"xai_{sym}_*.csv")
    files = glob.glob(pattern)
    if not files:
        return pd.DataFrame()
    # Prendre le fichier le plus récent
    latest_file = max(files, key=lambda x: Path(x).stat().st_mtime)
    try:
        df = pd.read_csv(latest_file)
        return df
    except Exception:
        return pd.DataFrame()

# --- 4. LOGIQUE DE DÉCONNEXION (Source 126) ---
def logout_user():
    st.session_state['authenticated'] = False
    st.session_state['first_login'] = True
    st.session_state['user_profile'] = None
    try:
        st.query_params.update(auth="0", first_login="1", profile="")
    except Exception:
        st.experimental_set_query_params(auth="0", first_login="1", profile="")
    st.rerun()

# --- 5. NAV BAR HORIZONTALE ---
def show_top_nav():
    header_left, header_right = st.columns([5, 1])
    with header_left:
        st.markdown(
            "<h1 style='text-align: left; color: #00FFAA; margin-bottom: 6px;'>FINSIGHT AI</h1>",
            unsafe_allow_html=True,
        )
    with header_right:
        if st.button("Account", use_container_width=True):
            st.session_state["page"] = "Account"
    cols = st.columns([1.2, 1.2, 1.1, 1.1, 1.1, 0.9])
    if cols[0].button("TABLEAU DE BORD", use_container_width=True):
        st.session_state["page"] = "Dashboard"
    if cols[1].button("Actualités", use_container_width=True):
        st.session_state["page"] = "News"

    return st.session_state["page"]

# --- 6. LOGIQUE DES PAGES ---

def show_login(): # Source 47-62
    st.title("FINSIGHT AI")
    t1, t2 = st.tabs(["Connexion", "Inscription"])
    with t1:
        st.text_input("Email", key="l_email")
        st.text_input("Mot de passe", type="password", key="l_pwd")
        if st.button("Se connecter"):
            st.session_state['authenticated'] = True
            try:
                st.query_params.update(auth="1")
            except Exception:
                st.experimental_set_query_params(auth="1")
            st.rerun()

def show_onboarding(): # Source 63-79
    st.header("PROFILAGE INTELLIGENT")
    st.write("Calibrage de l'IA selon votre niveau d'expertise.")
    with st.form("full_onboarding"):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Âge", 18, 100, 25)
            st.selectbox("Horizon d'investissement", ["Court terme", "Moyen terme", "Long terme"])
            exp = st.radio("Expérience en trading", ["Aucune", "Occasionnelle", "Régulière/Expert"])
        with col2:
            st.selectbox("Fréquence d'ordres", ["Quotidienne", "Hebdomadaire", "Mensuelle", "Rarement"])
            st.slider("Tolérance au risque (perte 10%)", 0, 10, 5)
            st.checkbox("Maîtrise de l'Analyse Technique")
            st.checkbox("Maîtrise de l'Analyse Fondamentale")

        st.divider()
        liste_tickers = ["SP 500", "CAC40", "GER30", "APPLE", "AMAZON", "SANOFI", "THALES", "LVMH", "TOTALENERGIES", "AIRBUS", "TESLA", "OIL", "GOLD", "GAS"]
        st.multiselect("Actifs à surveiller", options=liste_tickers)

        if st.form_submit_button("VALIDER LE PROFIL"):
            if exp == "Occasionnelle":
                st.session_state['user_profile'] = "Intermédiaire"
            elif exp == "Régulière/Expert":
                st.session_state['user_profile'] = "Confirmé"
            else:
                st.session_state['user_profile'] = "Débutant"
            st.session_state['first_login'] = False
            try:
                st.query_params.update(
                    auth="1",
                    first_login="0",
                    profile=st.session_state['user_profile']
                )
            except Exception:
                st.experimental_set_query_params(
                    auth="1",
                    first_login="0",
                    profile=st.session_state['user_profile']
                )
            st.rerun()

def main_app(nav):
    # Handle deep-link from table click
    try:
        qp = st.query_params
        selected_sym = qp.get("stock")
    except Exception:
        qp = st.experimental_get_query_params()
        selected_sym = qp.get("stock", [None])[0]

    if nav == "Dashboard": # Source 80
        # KPI basés sur le stock avec la plus grande hausse sur 7 jours
        top_stock = None
        watchlist_syms = load_watchlist()
        name_map = build_name_map(stock_df)
        if watchlist_syms:
            rows = []
            for sym in watchlist_syms:
                _, _, _, v7_pct = compute_variations(sym)
                rows.append(
                    {
                        "Symbole": sym,
                        "Nom": name_map.get(normalize_ticker(sym), sym),
                        "__var7_pct": v7_pct,
                    }
                )
            tmp = pd.DataFrame(rows).dropna(subset=["__var7_pct"])
            if not tmp.empty:
                top_stock = tmp.sort_values("__var7_pct", ascending=False).iloc[0]

        c1, c2, c3 = st.columns(3)
        if top_stock is not None:
            top_name = top_stock.get("Nom", "—")
            top_sym = top_stock.get("Symbole", "—")
            top_var7 = top_stock.get("__var7_pct", 0.0)
            c1.metric("Top Stock (7j)", f"{top_name} ({top_sym})", f"{top_var7:+.2f}%")

            # Sentiment global lié au top stock
            if not news_df.empty and top_sym != "—":
                key = news_key_for_symbol(top_sym)
                news = news_df.copy()
                news["__ticker_norm"] = news["asset_ticker"].astype(str).map(normalize_ticker)
                key_norm = normalize_ticker(key)
                news_top = news[news["__ticker_norm"] == key_norm]
                if not news_top.empty:
                    avg_pos = news_top["prob_positive"].mean()
                    avg_neg = news_top["prob_negative"].mean()
                    sentiment_label = "🟢 BULLISH" if avg_pos > avg_neg else "🔴 BEARISH"
                    sentiment_score = max(avg_pos, avg_neg) * 100
                    c2.metric("Sentiment global", sentiment_label, f"{sentiment_score:.0f}/100")

                    main_row = news_top.loc[news_top["prob_positive"].idxmax()]
                    main_title = main_row["title"] if "title" in main_row else "—"
                    c3.metric("Main news", main_title[:40] + "…")
                else:
                    c2.metric("Sentiment global", OVERALL_SENTIMENT_LABEL, f"{OVERALL_SENTIMENT_SCORE:.0f}/100")
                    c3.metric("Main news", top_positive_news_title(news_df))
            else:
                c2.metric("Sentiment global", "—")
                c3.metric("Main news", "—")
        else:
            c1.metric("Top Stock (7j)", "—")
            c2.metric("Sentiment global", "—")
            c3.metric("Main news", "—")
        
        st.divider()
        
        st.subheader("PORTFEUILLE DE SURVEILLANCE")
        try:
            qp = st.query_params
            auth_param = qp.get("auth", "1")
            first_login_param = qp.get("first_login", "0")
            profile_param = qp.get("profile", st.session_state.get("user_profile", ""))
        except Exception:
            qp = st.experimental_get_query_params()
            auth_param = qp.get("auth", ["1"])[0]
            first_login_param = qp.get("first_login", ["0"])[0]
            profile_param = qp.get("profile", [st.session_state.get("user_profile", "")])[0]

        watchlist_syms = load_watchlist()
        name_map = build_name_map(stock_df)
        if watchlist_syms:
            rows = []
            for sym in watchlist_syms:
                hist = load_price_history(sym)
                last_price = hist["Close"].iloc[-1] if not hist.empty and "Close" in hist.columns else np.nan
                rows.append(
                    {
                        "Nom": name_map.get(normalize_ticker(sym), sym),
                        "Symbole": sym,
                        "Prix": last_price,
                        "Sentiment": SENTIMENT_MAP.get(news_key_for_symbol(sym), OVERALL_SENTIMENT_LABEL),
                    }
                )
            display_df = pd.DataFrame(rows)
        elif not stock_df.empty:
            display_df = stock_df[['Nom', 'Symbole', 'Prix', 'Variation 24h', 'Variation 7d', 'Sentiment', 'Graph']].copy()
        else:
            display_df = pd.DataFrame()

        if not display_df.empty:
            display_df = display_df.head(20)
            rows_html = []

            for _, r in display_df.iterrows():
                sym = str(r["Symbole"])
                name = str(r["Nom"])
                price = r["Prix"]
                v24_abs, v24_pct, v7_abs, v7_pct = compute_variations(sym)
                if v24_abs is None or v24_pct is None:
                    v24 = "—"
                    v24_color = "#64748b"
                else:
                    v24_color = "#16a34a" if v24_abs >= 0 else "#dc2626"
                    v24 = (
                        f"<span style='color:{v24_color}; font-weight:600;'>"
                        f"{v24_abs:+.2f} ({v24_pct:+.2f}%)</span>"
                    )
                if v7_abs is None or v7_pct is None:
                    v7 = "—"
                else:
                    v7_color = "#16a34a" if v7_abs >= 0 else "#dc2626"
                    v7 = (
                        f"<span style='color:{v7_color}; font-weight:600;'>"
                        f"{v7_abs:+.2f} ({v7_pct:+.2f}%)</span>"
                    )
                sent = str(r["Sentiment"])
                key = news_key_for_symbol(sym)
                sent = SENTIMENT_MAP.get(key, OVERALL_SENTIMENT_LABEL)
                graph = sparkline_svg(sym, color=v24_color)
                link_url = f"?stock={sym}&auth={auth_param}&first_login={first_login_param}&profile={profile_param}"
                rows_html.append(
                    f"""
<tr>
  <td><a href="{link_url}" target="_self">{name}</a></td>
  <td><a href="{link_url}" target="_self">{sym}</a></td>
  <td><a href="{link_url}" target="_self">{price}</a></td>
  <td><a href="{link_url}" target="_self">{v24}</a></td>
  <td><a href="{link_url}" target="_self">{v7}</a></td>
  <td><a href="{link_url}" target="_self">{sent}</a></td>
  <td class="graph-col"><a href="{link_url}" target="_self">{graph}</a></td>
</tr>
"""
                )

            st.markdown(
                """
<style>
.table-wrap {overflow-x:auto;}
.table-wrap table {width:100%; border-collapse:separate; border-spacing:0;}
.table-wrap th, .table-wrap td {padding:6px 8px; border-bottom:1px solid #e5e7eb; font-size:14px;}
.table-wrap th {text-align:left; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:.06em; font-size:12px;}
.table-wrap tr:hover {background:#f8fafc;}
.table-wrap a {color:#0f172a; text-decoration:none; font-weight:600; display:block;}
.table-wrap th.graph-col, .table-wrap td.graph-col {width:120px; min-width:120px; max-width:120px; padding-left:4px; padding-right:4px;}
.table-wrap td.graph-col a {padding:0; display:flex; align-items:center; justify-content:center;}
</style>
""",
                unsafe_allow_html=True,
            )
            st.markdown(
                """
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Nom</th>
        <th>Ticker</th>
        <th>Prix</th>
        <th>Variation 24h</th>
        <th>Variation 7d</th>
        <th>Sentiment</th>
        <th class="graph-col">Graph</th>
      </tr>
    </thead>
""" + "".join(rows_html) + """
  </table>
</div>
""",
                unsafe_allow_html=True,
            )

            if selected_sym and selected_sym in display_df["Symbole"].astype(str).values:
                row = display_df[display_df["Symbole"].astype(str) == str(selected_sym)].iloc[0]
                st.session_state["selected_stock"] = row.to_dict()
                st.session_state["page"] = "StockDetail"
                st.rerun()

    elif nav == "Predictions":
        st.title("PRÉDICTIONS MARKET")
        if not aapl_df.empty:
            hist_data = aapl_df.tail(100).copy()
            last_date = hist_data['Date'].max()
            last_price = hist_data['Close'].iloc[-1]
            future_dates = [last_date + timedelta(days=i) for i in range(1, 11)]
            future_prices = [last_price * (1 + (0.005 * i) + np.random.normal(0, 0.01)) for i in range(1, 11)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_data['Date'], y=hist_data['Close'], mode='lines', name='Historique', line=dict(color='#00FFAA', width=2)))
            fig.add_trace(go.Scatter(x=future_dates, y=future_prices, mode='lines+markers', name='Prédiction IA (J+10)', line=dict(color='#FF7675', width=2, dash='dot')))
            fig.update_layout(template="plotly_dark", hovermode="x unified", xaxis_title="Date", yaxis_title="Prix ($)")
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"Analyse IA : Tendance probable vers {future_prices[-1]:.2f}$ d'ici 10 jours.")
        else:
            st.error("Données historiques non disponibles.")

        # Layout principal avec timeline
        #main_col, timeline_col = st.columns([2, 1])
        
        # with timeline_col:
        #     st.subheader("📰 TIMELINE ACTUALITÉS")
            
        #     # Filtre actif pour la timeline
        #     all_assets = sorted(list(set([a.strip() for sub in news_df['asset_ticker'].str.split(',') for a in sub]))) if not news_df.empty else []
        #     selected_asset = st.selectbox("Actif", options=["Tous"] + all_assets, key="timeline_asset")
            
        #     # Filtrage des news
        #     timeline_news = news_df.copy()
        #     if selected_asset != "Tous":
        #         timeline_news = timeline_news[timeline_news['asset_ticker'].str.contains(selected_asset)]
            
        #     # Calcul du sentiment global
        #     if not timeline_news.empty:
        #         avg_positive = timeline_news['prob_positive'].mean()
        #         avg_negative = timeline_news['prob_negative'].mean()
                
        #         if avg_positive > avg_negative:
        #             sentiment_label = "🟢 BULLISH"
        #             sentiment_color = "#00FF88"
        #             sentiment_detail = f"Sentiment Positif: <strong>{avg_positive:.0%}</strong>"
        #         else:
        #             sentiment_label = "🔴 BEARISH"
        #             sentiment_color = "#FF4444"
        #             sentiment_detail = f"Sentiment Négatif: <strong>{avg_negative:.0%}</strong>"
                
        #         st.markdown(f"<div style='background-color: {sentiment_color}20; padding: 10px; border-radius: 5px; border-left: 4px solid {sentiment_color}; margin-bottom: 15px;'>"
        #                    f"<strong>{sentiment_label}</strong><br>"
        #                    f"{sentiment_detail}"
        #                    f"</div>", unsafe_allow_html=True)
            
        #     # Affichage des news
        #     st.markdown("---")
        #     for idx, row in timeline_news.head(8).iterrows():
        #         # Déterminer le sentiment de chaque news
        #         if row['prob_positive'] > row['prob_negative']:
        #             news_sentiment = "🟢"
        #             news_color = "#00FF88"
        #         else:
        #             news_sentiment = "🔴"
        #             news_color = "#FF4444"
                
        #         with st.container():
        #             st.markdown(f"<div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid {news_color};'>"
        #                        f"<span style='font-size: 18px;'>{news_sentiment}</span> "
        #                        f"<strong style='font-size: 13px;'>{row['title'][:60]}...</strong><br>"
        #                        f"<small style='color: #888;'>📊 {row['asset_ticker']}</small><br>"
        #                        f"<small style='color: {news_color};'>Confiance: {max(row['prob_positive'], row['prob_negative']):.0%}</small>"
        #                        f"</div>", unsafe_allow_html=True)
        #             st.link_button("📖 Lire", row['url'], use_container_width=True, type="secondary")

    elif nav == "StockDetail":
        st.title("DETAILS ACTIF")
        selected = st.session_state.get("selected_stock")
        if not selected:
            st.info("Aucun actif selectionne.")
        else:
            left, mid, right = st.columns([1, 2.2, 1.2])

            with left:
                symbols = stock_df["Symbole"].dropna().astype(str).unique().tolist()
                current = selected.get("Symbole", symbols[0] if symbols else "—")
                choice = st.selectbox("Actif", symbols, index=symbols.index(current) if current in symbols else 0)
                if choice != current:
                    row = stock_df[stock_df["Symbole"].astype(str) == str(choice)].iloc[0]
                    st.session_state["selected_stock"] = row.to_dict()
                    try:
                        st.query_params.update(stock=str(choice))
                    except Exception:
                        st.experimental_set_query_params(stock=str(choice))
                    st.rerun()

                # Récupérer les informations actualisées
                current_sym = selected.get('Symbole', '—')
                hist = load_price_history(current_sym)
                last_price = hist["Close"].iloc[-1] if not hist.empty and "Close" in hist.columns else selected.get("Prix", "—")
                
                st.markdown(f"**{selected.get('Nom', '—')}**")
                st.caption(f"Ticker: {current_sym}")
                st.metric("Prix", f"${last_price:.2f}" if isinstance(last_price, (int, float)) else last_price)
                
                # Calculer les variations
                v24_abs, v24_pct, v7_abs, v7_pct = compute_variations(current_sym)
                if v24_abs is not None and v24_pct is not None:
                    st.metric("Variation 24h", f"${v24_abs:+.2f}", f"{v24_pct:+.2f}%")
                else:
                    st.metric("Variation 24h", "—")
                    
                if v7_abs is not None and v7_pct is not None:
                    st.metric("Variation 7d", f"${v7_abs:+.2f}", f"{v7_pct:+.2f}%")
                else:
                    st.metric("Variation 7d", "—")
                
                # Récupérer le sentiment
                key = news_key_for_symbol(current_sym)
                sentiment = SENTIMENT_MAP.get(key, OVERALL_SENTIMENT_LABEL)
                st.caption(f"Sentiment: {sentiment}")

                if st.button("Retour"):
                    try:
                        st.query_params.update(stock="")
                    except Exception:
                        st.experimental_set_query_params(stock="")
                    st.session_state["page"] = "Dashboard"
                    st.rerun()

            with mid:
                sym = selected.get("Symbole", "")
                hist = load_price_history(sym)

                pdata = load_patterns(sym)
                patterns_list = pdata.get("patterns", []) if pdata else []

                if not patterns_list:
                    st.info("Aucun pattern detecte.")
                    show_patterns = False
                else:
                    st.caption(f"{len(patterns_list)} pattern(s) detecte(s).")
                    show_patterns = st.checkbox(
                        "Afficher les patterns",
                        value=False,
                        key="show_patterns_detail",
                    )

                if show_patterns and patterns_list:
                    pattern_labels = []
                    for i, pat in enumerate(patterns_list):
                        name = pat.get("alt_name") or pat.get("pattern") or f"Pattern {i+1}"
                        start = pat.get("start", "")[:10]
                        end = pat.get("end", "")[:10]
                        pattern_labels.append(f"{name} ({start} → {end})")
                    selected_idx = st.selectbox(
                        "Pattern",
                        list(range(len(pattern_labels))),
                        format_func=lambda i: pattern_labels[i],
                        key="pattern_select_detail",
                    )
                    range_opt = "LOCKED"
                else:
                    range_opt = st.selectbox(
                        "Horizon",
                        ["1M", "3M", "6M", "1Y", "5Y", "ALL"],
                        index=3,
                        key="range_opt_detail",
                    )

                if not hist.empty and "Date" in hist.columns:
                    if show_patterns and patterns_list:
                        pat = patterns_list[int(selected_idx)]
                        df_start = pat.get("df_start")
                        df_end = pat.get("df_end")
                        if df_start and df_end:
                            start_dt = pd.to_datetime(df_start)
                            end_dt = pd.to_datetime(df_end)
                            hist = hist[(hist["Date"] >= start_dt) & (hist["Date"] <= end_dt)]
                    elif range_opt != "ALL":
                        days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "5Y": 365 * 5}
                        days = days_map.get(range_opt, 365)
                        cutoff = hist["Date"].max() - pd.Timedelta(days=days)
                        hist = hist[hist["Date"] >= cutoff]

                if not hist.empty and {"Open", "High", "Low", "Close"}.issubset(hist.columns):
                    fig = go.Figure(
                        data=[
                            go.Candlestick(
                                x=hist["Date"],
                                open=hist["Open"],
                                high=hist["High"],
                                low=hist["Low"],
                                close=hist["Close"],
                                increasing_line_color="#13c296",
                                decreasing_line_color="#ef4444",
                            )
                        ]
                    )
                    fig.update_layout(
                        height=460,
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_rangeslider_visible=False,
                        template="plotly_white",
                    )

                    if show_patterns and patterns_list:
                        pat = patterns_list[int(selected_idx)]
                        pts = pat.get("points", {})

                        ordered_keys = ["X", "A", "B", "C", "D"]
                        xs, ys, labels = [], [], []
                        for key in ordered_keys:
                            if key not in pts:
                                continue
                            v = pts[key]
                            try:
                                xs.append(pd.to_datetime(v[0]))
                                ys.append(float(v[1]))
                                labels.append(str(key))
                            except Exception:
                                continue

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
                                    name=pat.get("pattern", "pattern"),
                                )
                            )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Historique prix indisponible pour cet actif.")


                current_ticker = selected.get("Symbole", "")

                xai_data = load_xai_analysis(current_ticker)

                # Section XAI Analysis détaillée
                if not xai_data.empty and len(xai_data) > 0:
                    xai_row = xai_data.iloc[0]
                    
                    st.markdown("---")
                    st.caption(f"📊 {int(xai_row['total_news'])} actualités analysées")
                    
                    # Explication XAI
                    st.markdown(xai_row['xai_explanation'])

            with right:
                st.subheader("📰 ACTUALITÉS")

                # Récupérer le ticker de l'actif sélectionné (celui de gauche)
                current_ticker = selected.get("Symbole", "")
                
                # Filtrer les news pour cet actif
                timeline_news = news_df.copy()
                if current_ticker:
                    timeline_news = timeline_news[
                        timeline_news["asset_ticker"].str.contains(
                            current_ticker, na=False, case=False
                        )
                    ]

                # Charger les données XAI
                xai_data = load_xai_analysis(current_ticker)
                
                if not timeline_news.empty:
                    avg_positive = timeline_news["prob_positive"].mean()
                    avg_negative = timeline_news["prob_negative"].mean()

                    if avg_positive > avg_negative:
                        sentiment_label = "🟢 BULLISH"
                        sentiment_color = "#00FF88"
                        sentiment_detail = (
                            f"Sentiment Positif: <strong>{avg_positive:.0%}</strong>"
                        )
                    else:
                        sentiment_label = "🔴 BEARISH"
                        sentiment_color = "#FF4444"
                        sentiment_detail = (
                            f"Sentiment Négatif: <strong>{avg_negative:.0%}</strong>"
                        )

                    # Ajouter la recommandation XAI si disponible
                    recommendation_html = ""
                    if not xai_data.empty and len(xai_data) > 0:
                        xai_row = xai_data.iloc[0]
                        rec_emoji = {"ACHETER": "🚀", "CONSERVER": "⏸️", "VENDRE": "⚠️"}.get(xai_row['recommendation'], "📊")
                        recommendation_html = (
                            f"<hr style='margin: 8px 0; border-color: {sentiment_color}40;'>"
                            f"<div style='text-align: center;'>"
                            f"<span style='font-size: 20px;'>{rec_emoji}</span> "
                            f"<strong style='font-size: 16px;'>{xai_row['recommendation']}</strong><br>"
                            f"<small style='color: #888;'>Confiance: {xai_row['confidence']}</small>"
                            f"</div>"
                        )

                    st.markdown(
                        f"<div style='background-color: {sentiment_color}20; "
                        f"padding: 10px; border-radius: 5px; border-left: 4px solid "
                        f"{sentiment_color}; margin-bottom: 15px;'>"
                        f"<strong>{sentiment_label}</strong><br>"
                        f"{sentiment_detail}"
                        f"{recommendation_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # # Section XAI Analysis détaillée
                # if not xai_data.empty and len(xai_data) > 0:
                #     xai_row = xai_data.iloc[0]
                    
                #     st.markdown("---")
                #     st.caption(f"📊 {int(xai_row['total_news'])} actualités analysées")
                    
                #     # Explication XAI dans un expander
                #     with st.expander("📖 Voir l'analyse détaillée", expanded=False):
                #         st.markdown(xai_row['xai_explanation'])
                
                # Filtrer les news avec confiance >= 75%
                if not timeline_news.empty:
                    timeline_news['confidence_max'] = timeline_news[['prob_positive', 'prob_negative']].max(axis=1)
                    high_confidence_news = timeline_news[timeline_news['confidence_max'] >= 0.75].copy()
                    
                    if not high_confidence_news.empty:
                        # Séparer news positives et négatives
                        positive_news = high_confidence_news[high_confidence_news['prob_positive'] > high_confidence_news['prob_negative']].nlargest(5, 'prob_positive')
                        negative_news = high_confidence_news[high_confidence_news['prob_negative'] > high_confidence_news['prob_positive']].nlargest(5, 'prob_negative')
                        
                        # Afficher les news positives
                        if not positive_news.empty:
                            st.markdown("**🟢 TOP IMPACT POSITIF**")
                            for _, row in positive_news.iterrows():
                                news_sentiment = "🟢"
                                news_color = "#00FF88"
                                news_sentiment_label = f"Positif {row['prob_positive']:.0%}"
                                
                                with st.container():
                                    st.markdown(
                                        f"<div style='background-color: #1E1E1E; padding: 12px; "
                                        f"border-radius: 8px; margin-bottom: 10px; border-left: 3px solid "
                                        f"{news_color};'>"
                                        f"<span style='font-size: 18px;'>{news_sentiment}</span> "
                                        f"<strong style='font-size: 13px;'>{row['title'][:60]}...</strong><br>"
                                        f"<small style='color: #888;'>📊 {row['asset_ticker']}</small><br>"
                                        f"<small style='color: {news_color};'>{news_sentiment_label}</small>"
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )
                                    st.link_button(
                                        "📖 Lire", row["url"], use_container_width=True, type="secondary"
                                    )
                        
                        # Afficher les news négatives
                        if not negative_news.empty:
                            st.markdown("**🔴 TOP IMPACT NÉGATIF**")
                            for _, row in negative_news.iterrows():
                                news_sentiment = "🔴"
                                news_color = "#FF4444"
                                news_sentiment_label = f"Négatif {row['prob_negative']:.0%}"
                                
                                with st.container():
                                    st.markdown(
                                        f"<div style='background-color: #1E1E1E; padding: 12px; "
                                        f"border-radius: 8px; margin-bottom: 10px; border-left: 3px solid "
                                        f"{news_color};'>"
                                        f"<span style='font-size: 18px;'>{news_sentiment}</span> "
                                        f"<strong style='font-size: 13px;'>{row['title'][:60]}...</strong><br>"
                                        f"<small style='color: #888;'>📊 {row['asset_ticker']}</small><br>"
                                        f"<small style='color: {news_color};'>{news_sentiment_label}</small>"
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )
                                    st.link_button(
                                        "📖 Lire", row["url"], use_container_width=True, type="secondary"
                                    )
                    else:
                        st.info("Aucune actualité avec une confiance ≥ 75%")
                else:
                    st.info("Aucune actualité disponible")

    elif nav == "Stocks":
        st.title("FLUX BOURSIER")
        st.dataframe(stock_df, use_container_width=True)

    elif nav == "News": # Source 23, 98
        st.title("ACTUALITÉS IA")
        with st.expander("FILTRES ET RECHERCHE", expanded=True):
            f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
            query = f_col1.text_input("Rechercher par titre")
            all_assets = sorted(list(set([a.strip() for sub in news_df['asset_ticker'].str.split(',') for a in sub]))) if not news_df.empty else []
            asset_search = f_col2.selectbox("Filtrer par actif", options=["Tous"] + all_assets)

        filtered = news_df.copy()
        if query: filtered = filtered[filtered['title'].str.contains(query, case=False)]
        if asset_search != "Tous": filtered = filtered[filtered['asset_ticker'].str.contains(asset_search)]

        # SENTIMENT GLOBAL PAR ACTIF
        st.subheader("SENTIMENT GLOBAL")
        if asset_search != "Tous" and not filtered.empty:
            avg_positive = filtered['prob_positive'].mean()
            avg_negative = filtered['prob_negative'].mean()
            sentiment_label = "🟢 BULLISH" if avg_positive > avg_negative else "🔴 BEARISH"
            sentiment_value = max(avg_positive, avg_negative)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Sentiment", sentiment_label)
            col2.metric("Confiance Positive", f"{avg_positive:.1%}")
            col3.metric("Confiance Négative", f"{avg_negative:.1%}")
        
        # FINSIGHT ADVISOR (Source 24-32)
        st.subheader("FINSIGHT ADVISOR")
        profile = st.session_state.get('user_profile', 'Débutant')
        if profile == "Débutant":
            st.info("ANALYSE : Le marché montre une tendance haussière stable. La presse est positive après les annonces récentes. Une position prudente est conseillée.")
        elif profile == "Confirmé":
            st.warning("ANALYSE : Rupture de résistance technique confirmée. Le sentiment positif suggère un momentum vers les zones de Fibonacci supérieures.")
        
        st.divider()
        for _, row in filtered.head(10).iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['title'].upper()}**")
                st.write(f"ACTIFS : {row['asset_ticker']}")
                st.link_button("LIRE L'ARTICLE", row['url'])
    elif nav == "Lexicon":
        st.title("LEXIQUE FINANCIER")
        lexicon = {
            "ETF": "Fonds qui suit un indice et s'échange en bourse comme une action.",
            "ANALYSE TECHNIQUE": "Étude des graphiques de prix pour prédire les tendances.",
            "SENTIMENT": "Psychologie globale des investisseurs (Optimiste/Pessimiste).",
            "VOLATILITÉ": "Mesure de l'ampleur des variations de prix d'un actif."
        }
        for word, definition in lexicon.items():
            with st.expander(word): st.write(definition)

# --- 7. ROUTAGE ---
if not st.session_state['authenticated']:
    show_login()
elif st.session_state['first_login']:
    show_onboarding()
else:
    active_nav = show_top_nav()
    main_app(active_nav)
