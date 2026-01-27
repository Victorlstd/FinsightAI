"""
Exemple d'intégration du module XAI dans le dashboard Streamlit
Copiez et adaptez ce code dans votre dashboard.py
"""

import streamlit as st
import sys
import os

# Ajouter le chemin XAI au path Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'XAI'))

# Import du module XAI
from xai_integration import (
    get_xai_explanation_for_asset,
    get_sentiment_for_asset,
    format_xai_for_display,
    get_news_list_for_asset,
    check_mistral_api
)

def show_xai_analysis_section():
    """
    Section complète d'analyse XAI à intégrer dans le dashboard
    """
    st.header("🔍 ANALYSE XAI - IMPACT DES NEWS")
    
    # Vérifier la configuration de l'API
    if not check_mistral_api():
        st.error("⚠️ API Mistral non configurée. Créez un fichier .env avec MISTRAL_API_KEY")
        return
    
    # Sélection de l'actif
    # Note: Remplacez par votre propre logique de sélection d'actif
    all_assets = ["AAPL", "TSLA", "AMZN", "SP500", "MSFT", "GOOGL"]
    selected_asset = st.selectbox(
        "Sélectionnez un actif pour l'analyse XAI",
        options=all_assets,
        key="xai_asset_selector"
    )
    
    if not selected_asset:
        st.info("Sélectionnez un actif pour voir l'analyse")
        return
    
    # Section 1: Sentiment rapide (sans appel API)
    st.subheader("📊 Sentiment Global")
    
    with st.spinner("Chargement du sentiment..."):
        sentiment = get_sentiment_for_asset(selected_asset)
    
    if sentiment and sentiment['total_news'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        # Déterminer la couleur de la tendance
        if sentiment['sentiment_trend'] == 'BULLISH':
            trend_color = "🟢"
        elif sentiment['sentiment_trend'] == 'BEARISH':
            trend_color = "🔴"
        else:
            trend_color = "⚪"
        
        col1.metric("Tendance", f"{trend_color} {sentiment['sentiment_trend']}")
        col2.metric("News", sentiment['total_news'])
        col3.metric("Sentiment +", f"{sentiment['avg_positive']:.1%}")
        col4.metric("Sentiment -", f"{sentiment['avg_negative']:.1%}")
        
        # Barre de progression du sentiment
        if sentiment['avg_positive'] > sentiment['avg_negative']:
            sentiment_value = sentiment['avg_positive']
            sentiment_label = "Positif"
            bar_color = "green"
        else:
            sentiment_value = sentiment['avg_negative']
            sentiment_label = "Négatif"
            bar_color = "red"
        
        st.progress(sentiment_value, text=f"{sentiment_label}: {sentiment_value:.1%}")
        
    else:
        st.warning(f"Aucune actualité trouvée pour {selected_asset}")
        return
    
    st.divider()
    
    # Section 2: Analyse XAI complète (avec appel API)
    st.subheader("🤖 Analyse Explicable (XAI)")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("Générez une analyse détaillée qui explique l'impact des news sur le marché")
    
    with col2:
        analyze_button = st.button("🔍 Analyser avec XAI", type="primary", use_container_width=True)
    
    if analyze_button or st.session_state.get(f'xai_analysis_{selected_asset}'):
        with st.spinner("Génération de l'analyse explicable... (2-5 secondes)"):
            analysis = get_xai_explanation_for_asset(selected_asset)
            st.session_state[f'xai_analysis_{selected_asset}'] = analysis
        
        if analysis and "error" not in analysis:
            # Afficher la recommandation en grand
            rec_color = {
                "ACHETER": "green",
                "VENDRE": "red",
                "CONSERVER": "blue",
                "SURVEILLER": "orange"
            }.get(analysis['recommendation'], "gray")
            
            st.markdown(f"""
            <div style='background-color: {rec_color}22; padding: 20px; border-radius: 10px; border-left: 5px solid {rec_color};'>
                <h3 style='margin:0; color:{rec_color};'>Recommandation: {analysis['recommendation']}</h3>
                <p style='margin:5px 0 0 0;'>Confiance: {analysis['confidence']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Afficher l'analyse détaillée
            st.markdown(format_xai_for_display(analysis))
            
            # Bouton de téléchargement
            st.download_button(
                label="📥 Télécharger l'analyse",
                data=format_xai_for_display(analysis),
                file_name=f"xai_analysis_{selected_asset}.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ Impossible de générer l'analyse XAI")
            if "error" in analysis:
                st.error(f"Erreur: {analysis['error']}")
    
    st.divider()
    
    # Section 3: Liste des news
    st.subheader("📰 Actualités Analysées")
    
    news_list = get_news_list_for_asset(selected_asset, limit=10)
    
    if news_list:
        for i, news in enumerate(news_list, 1):
            sentiment_icon = "🟢" if news['sentiment'] == 'Positive' else "🔴"
            
            with st.expander(f"{i}. {sentiment_icon} {news['title'][:80]}..."):
                st.write(f"**Source:** {news['source']}")
                st.write(f"**Publié:** {news['published_at']}")
                st.write(f"**Description:** {news['description']}")
                
                col1, col2 = st.columns(2)
                col1.metric("Sentiment", news['sentiment'])
                col2.metric("Confiance", f"{news['confidence']:.1%}")
                
                st.link_button("📖 Lire l'article complet", news['url'], use_container_width=True)
    else:
        st.info("Aucune actualité à afficher")


def show_xai_quick_widget(asset_ticker: str):
    """
    Widget compact pour afficher rapidement le sentiment XAI
    Peut être utilisé dans une sidebar ou une colonne
    
    Args:
        asset_ticker: Le ticker de l'actif (ex: "AAPL")
    """
    sentiment = get_sentiment_for_asset(asset_ticker)
    
    if sentiment and sentiment['total_news'] > 0:
        trend_emoji = "🟢" if sentiment['sentiment_trend'] == 'BULLISH' else "🔴"
        
        st.markdown(f"""
        <div style='background-color: #1E1E1E; padding: 10px; border-radius: 5px;'>
            <strong>{asset_ticker}</strong><br>
            {trend_emoji} {sentiment['sentiment_trend']}<br>
            <small>{sentiment['total_news']} news • {sentiment['avg_positive']:.0%} positif</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Analyser {asset_ticker}", key=f"quick_xai_{asset_ticker}"):
            # Rediriger vers la page d'analyse complète
            st.session_state['selected_asset'] = asset_ticker
            st.session_state['page'] = 'XAI_Analysis'
            st.rerun()


def show_multi_asset_comparison():
    """
    Affiche une comparaison du sentiment de plusieurs actifs
    """
    st.header("📊 Comparaison Multi-Actifs")
    
    # Sélection multiple d'actifs
    all_assets = ["AAPL", "TSLA", "AMZN", "SP500", "MSFT", "GOOGL", "META", "NVDA"]
    selected_assets = st.multiselect(
        "Sélectionnez les actifs à comparer",
        options=all_assets,
        default=["AAPL", "TSLA", "AMZN"],
        max_selections=6
    )
    
    if not selected_assets:
        st.info("Sélectionnez au moins un actif")
        return
    
    # Créer un tableau de comparaison
    comparison_data = []
    
    for asset in selected_assets:
        sentiment = get_sentiment_for_asset(asset)
        if sentiment and sentiment['total_news'] > 0:
            comparison_data.append({
                "Actif": asset,
                "Tendance": sentiment['sentiment_trend'],
                "News": sentiment['total_news'],
                "Positif": f"{sentiment['avg_positive']:.1%}",
                "Négatif": f"{sentiment['avg_negative']:.1%}",
                "Confiance": f"{sentiment['confidence']:.1%}"
            })
    
    if comparison_data:
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        
        # Colorier les tendances
        def color_trend(val):
            if val == 'BULLISH':
                return 'background-color: #00FF8822'
            elif val == 'BEARISH':
                return 'background-color: #FF444422'
            else:
                return ''
        
        st.dataframe(
            df.style.applymap(color_trend, subset=['Tendance']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Aucune donnée disponible pour les actifs sélectionnés")


# ============================================================================
# EXEMPLE D'INTÉGRATION DANS LE MAIN APP
# ============================================================================

def example_main_app_integration():
    """
    Exemple complet d'intégration dans la fonction main_app de dashboard.py
    """
    
    # Dans votre navigation
    nav = st.sidebar.radio("Navigation", ["Dashboard", "News", "XAI Analysis", "Comparaison"])
    
    if nav == "XAI Analysis":
        show_xai_analysis_section()
    
    elif nav == "Comparaison":
        show_multi_asset_comparison()
    
    elif nav == "Dashboard":
        # Dans votre dashboard, ajoutez des widgets XAI rapides
        st.title("TABLEAU DE BORD")
        
        # Colonne sidebar avec sentiment rapide
        with st.sidebar:
            st.subheader("🎯 Sentiment du jour")
            for asset in ["AAPL", "TSLA", "SP500"]:
                show_xai_quick_widget(asset)
                st.markdown("---")


# ============================================================================
# POUR TESTER CE FICHIER
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="XAI Analysis Demo",
        page_icon="🔍",
        layout="wide"
    )
    
    # Test de la section complète
    show_xai_analysis_section()
