"""
Exemple d'intégration de l'analyse de sentiment dans une application Streamlit multi-pages

Ce fichier montre comment intégrer facilement la page d'analyse de sentiment
dans un projet Streamlit plus large avec plusieurs fonctionnalités.
"""

import streamlit as st
from streamlit_sentiment_app import render_sentiment_analysis_page

def main():
    """Application principale avec navigation"""
    
    st.set_page_config(
        page_title="FinsightAI - Dashboard",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar pour la navigation
    with st.sidebar:
        st.title("💼 FinsightAI")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            [
                "🏠 Accueil",
                "📈 Analyse de Sentiment",
                "📊 Dashboard Financier",
                "📰 Collecte de News",
                "⚙️ Configuration"
            ],
            index=0
        )
        
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Dernière mise à jour:** 21/01/2026")
    
    # Router vers la bonne page
    if page == "🏠 Accueil":
        render_home_page()
    
    elif page == "📈 Analyse de Sentiment":
        # Intégration de la page d'analyse de sentiment
        render_sentiment_analysis_page()
    
    elif page == "📊 Dashboard Financier":
        render_financial_dashboard()
    
    elif page == "📰 Collecte de News":
        render_news_collection()
    
    elif page == "⚙️ Configuration":
        render_configuration()


def render_home_page():
    """Page d'accueil"""
    st.title("🏠 Bienvenue sur FinsightAI")
    st.markdown("---")
    
    st.markdown("""
    ## 👋 Bienvenue !
    
    FinsightAI est une plateforme d'analyse financière basée sur l'IA qui combine:
    
    - 📈 **Analyse de Sentiment** - Analyse automatique du sentiment des news financières
    - 📊 **Dashboard Financier** - Visualisation des données de marché
    - 📰 **Collecte de News** - Agrégation de news de sources multiples
    - 🤖 **Machine Learning** - Modèles d'IA pour la prédiction
    
    ### 🚀 Pour commencer
    
    Utilisez le menu à gauche pour naviguer entre les différentes fonctionnalités.
    """)
    
    # Statistiques rapides
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**📰 News analysées**\n\n1,234")
    
    with col2:
        st.success("**📈 Précision du modèle**\n\n94.2%")
    
    with col3:
        st.warning("**🔄 Dernière mise à jour**\n\nIl y a 2h")


def render_financial_dashboard():
    """Page du dashboard financier (exemple)"""
    st.title("📊 Dashboard Financier")
    st.markdown("---")
    
    st.info("🚧 Cette page sera développée prochainement")
    
    st.markdown("""
    ### Fonctionnalités prévues:
    
    - Graphiques de prix en temps réel
    - Indicateurs techniques
    - Corrélation sentiment/prix
    - Alertes personnalisées
    """)


def render_news_collection():
    """Page de collecte de news (exemple)"""
    st.title("📰 Collecte de News")
    st.markdown("---")
    
    st.info("🚧 Cette page sera développée prochainement")
    
    st.markdown("""
    ### Fonctionnalités prévues:
    
    - Configuration des sources de news
    - Filtres par asset et mots-clés
    - Planification des collectes
    - Historique des collectes
    """)


def render_configuration():
    """Page de configuration (exemple)"""
    st.title("⚙️ Configuration")
    st.markdown("---")
    
    st.markdown("### 🔧 Paramètres de l'application")
    
    # Exemple de paramètres
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Modèle FinBERT")
        model_path = st.text_input("Chemin du modèle", "./news_finbert_sentiment_model")
        confidence_threshold = st.slider("Seuil de confiance", 0.0, 1.0, 0.5)
    
    with col2:
        st.subheader("Sources de données")
        news_path = st.text_input("Chemin des news", "../Pipeline_Recup_Donnees/data/raw/news/")
        auto_refresh = st.checkbox("Actualisation automatique", value=True)
    
    if st.button("💾 Sauvegarder la configuration"):
        st.success("✅ Configuration sauvegardée !")


if __name__ == "__main__":
    main()
