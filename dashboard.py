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
    try:
        stocks = pd.read_csv('stock_data (1).csv')
        #news_raw = pd.read_csv('Pipeline_Recup_Donnees/data/raw/news/hybrid_news_mapped_with_sentiment.csv')
        news_raw = pd.read_csv('NLP/sentiment_analysis_20260123_170727.csv')
        aapl = pd.read_csv('AAPL.csv')
        aapl['Date'] = pd.to_datetime(aapl['Date'])
        
        # Dédoublonnage : regroupement par titre et fusion des actifs (Source 112)
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
        
        return stocks, news_processed, aapl
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
        c1, c2, c3 = st.columns(3)
        c1.metric("Top Stock", f"{stock_df['Variation'].mean():+.2f}" if not stock_df.empty else "0.00")
        c2.metric("Sentiment global", len(news_df))
        c3.metric("Main news", "72/100", "Optimiste")
        
        st.divider()
        
        st.subheader("PORTFEUILLE DE SURVEILLANCE")
        if not stock_df.empty:
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
            
            display_df = stock_df[['Nom', 'Symbole', 'Prix', 'Variation 24h', 'Variation 7d', 'Sentiment', 'Graph']].head(10)
            rows_html = []
            for _, r in display_df.iterrows():
                sym = str(r["Symbole"])
                name = str(r["Nom"])
                price = r["Prix"]
                v24 = r["Variation 24h"]
                v7 = r["Variation 7d"]
                sent = str(r["Sentiment"])
                graph = str(r["Graph"])
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
  <td><a href="{link_url}" target="_self">{graph}</a></td>
</tr>
"""
                )

            st.markdown(
                """
<style>
.table-wrap {overflow-x:auto;}
.table-wrap table {width:100%; border-collapse:separate; border-spacing:0;}
.table-wrap th, .table-wrap td {padding:12px 10px; border-bottom:1px solid #e5e7eb; font-size:14px;}
.table-wrap th {text-align:left; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:.06em; font-size:12px;}
.table-wrap tr:hover {background:#f8fafc;}
.table-wrap a {color:#2563eb; text-decoration:none; font-weight:600;display:block;}
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
        <th>Graph</th>
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

                st.markdown(f"**{selected.get('Nom', '—')}**")
                st.caption(f"Ticker: {selected.get('Symbole', '—')}")
                st.metric("Prix", selected.get("Prix", "—"))
                st.metric("Variation 24h", selected.get("Variation 24h", "—"))
                st.metric("Variation 7d", selected.get("Variation 7d", "—"))
                st.caption(f"Sentiment: {selected.get('Sentiment', '—')}")

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

                # Section XAI Analysis détaillée
                if not xai_data.empty and len(xai_data) > 0:
                    xai_row = xai_data.iloc[0]
                    
                    st.markdown("---")
                    st.caption(f"📊 {int(xai_row['total_news'])} actualités analysées")
                    
                    # Explication XAI dans un expander
                    with st.expander("📖 Voir l'analyse détaillée", expanded=False):
                        st.markdown(xai_row['xai_explanation'])

                st.markdown("---")
                
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
