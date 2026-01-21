import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

# --- 1. CONFIGURATION (Source 45) ---
st.set_page_config(
    page_title="Finsight AI", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. GESTION D'ÉTAT (Source 46) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'first_login' not in st.session_state:
    st.session_state['first_login'] = True
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = "Dashboard"

# --- 3. CHARGEMENT DES DONNÉES (Source 129, 131) ---
@st.cache_data
def load_and_process_data():
    try:
        stocks = pd.read_csv('stock_data (1).csv')
        news_raw = pd.read_csv('Pipeline_Recup_Donnees/data/raw/news/hybrid_news_mapped_with_sentiment.csv')
        #news_raw = pd.read_csv('hybrid_news_mapped.csv')
        aapl = pd.read_csv('AAPL.csv')
        aapl['Date'] = pd.to_datetime(aapl['Date'])
        
        # Dédoublonnage : regroupement par titre et fusion des actifs (Source 112)
        news_processed = news_raw.groupby('title').agg({
            'date': 'first', 
            'url': 'first', 
            'source': 'first',
            'asset': lambda x: ', '.join(x.unique()),
            'base_impact_score': 'mean', 
            'event_type': 'first',
            'sentiment': 'first',
            'confidence': 'mean',
            'prob_negative': 'mean',
            'prob_positive': 'mean'
        }).reset_index()
        
        return stocks, news_processed, aapl
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

stock_df, news_df, aapl_df = load_and_process_data()

# --- 4. LOGIQUE DE DÉCONNEXION (Source 126) ---
def logout_user():
    st.session_state['authenticated'] = False
    st.session_state['first_login'] = True
    st.session_state['user_profile'] = None
    st.rerun()

# --- 5. SIDEBAR PROFESSIONNELLE (Source 118-127) ---
def show_sidebar():
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: #00FFAA; margin-bottom: 0;'>FINSIGHT AI</h1>", unsafe_allow_html=True)
        st.selectbox("Language", ["Français", "English"], label_visibility="collapsed")
        st.divider()

        st.markdown("### UTILISATEUR")
        st.write("**Nom :** Utilisateur Démo")
        
        profile = st.session_state.get('user_profile', 'Débutant')
        color = "#55efc4" if profile == "Débutant" else "#fdcb6e" if profile == "Intermédiaire" else "#ff7675"
        st.markdown(f"Niveau : <span style='color:{color}; font-weight:bold;'>{profile.upper() if profile else 'NON DÉFINI'}</span>", unsafe_allow_html=True)
        
        st.divider()

        st.markdown("### MENU")
        if st.button("TABLEAU DE BORD", use_container_width=True):
            st.session_state['page'] = "Dashboard"
        if st.button("PRÉDICTIONS MARKET", use_container_width=True):
            st.session_state['page'] = "Predictions"
        if st.button("FLUX BOURSIER", use_container_width=True):
            st.session_state['page'] = "Stocks"
        if st.button("ACTUALITÉS IA", use_container_width=True):
            st.session_state['page'] = "News"
        if st.button("LEXIQUE FINANCIER", use_container_width=True):
            st.session_state['page'] = "Lexicon"
        
        st.divider()
        if st.button("DÉCONNEXION", use_container_width=True, type="secondary"):
            logout_user()
            
    return st.session_state['page']

# --- 6. LOGIQUE DES PAGES ---

def show_login(): # Source 47-62
    st.title("FINSIGHT AI")
    t1, t2 = st.tabs(["Connexion", "Inscription"])
    with t1:
        st.text_input("Email", key="l_email")
        st.text_input("Mot de passe", type="password", key="l_pwd")
        if st.button("Se connecter"):
            st.session_state['authenticated'] = True
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
            st.rerun()

def main_app(nav):
    if nav == "Dashboard": # Source 80
        st.title("TABLEAU DE BORD")
        c1, c2, c3 = st.columns(3)
        c1.metric("TENDANCE MARCHÉ", f"{stock_df['Variation'].mean():+.2f}" if not stock_df.empty else "0.00")
        c2.metric("FLUX ACTUALITÉS", len(news_df))
        c3.metric("SENTIMENT GLOBAL", "72/100", "Optimiste")
        
        st.divider()
        st.subheader("PORTFEUILLE DE SURVEILLANCE")
        if not stock_df.empty:
            st.dataframe(stock_df[['Symbole', 'Nom', 'Prix actuel', 'Variation %']].head(10), use_container_width=True, hide_index=True)

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

    elif nav == "Stocks":
        st.title("FLUX BOURSIER")
        st.dataframe(stock_df, use_container_width=True)

    elif nav == "News": # Source 23, 98
        st.title("ACTUALITÉS IA")
        with st.expander("FILTRES ET RECHERCHE", expanded=True):
            f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
            query = f_col1.text_input("Rechercher par titre")
            all_assets = sorted(list(set([a.strip() for sub in news_df['asset'].str.split(',') for a in sub]))) if not news_df.empty else []
            asset_search = f_col2.selectbox("Filtrer par actif", options=["Tous"] + all_assets)
            impact_min = f_col3.slider("Impact Minimum", 0, 10, 0)

        filtered = news_df.copy()
        if query: filtered = filtered[filtered['title'].str.contains(query, case=False)]
        if asset_search != "Tous": filtered = filtered[filtered['asset'].str.contains(asset_search)]
        filtered = filtered[filtered['base_impact_score'] >= impact_min]

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
                st.caption(f"SOURCE : {row['source']} | IMPACT : {row['base_impact_score']:.1f}/10 SENTIMENT : **{row['sentiment']}** Confiance : {row['confidence']:.2f}")
                st.write(f"ACTIFS : {row['asset']}")
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
    active_nav = show_sidebar()
    main_app(active_nav)