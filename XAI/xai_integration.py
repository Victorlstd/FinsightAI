"""
Module d'intégration XAI pour le dashboard Streamlit
Fournit des fonctions pour analyser l'impact des news sur les actifs
"""

import sys
import os

# Racine du projet (parent de XAI) pour importer NLP
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
# Chemin XAI pour stock_fetcher local
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stock_fetcher import (
    load_latest_sentiment_data,
    fetch_news_for_asset,
    get_sentiment_summary
)
# analyze_asset_news (news + Mistral) est dans NLP
try:
    from NLP.stock_analyzer import (
        analyze_asset_news,
        display_xai_analysis,
        format_news_for_analysis,
        analyze_news_impact_with_xai,
    )
except ImportError:
    analyze_asset_news = None
    display_xai_analysis = None
    format_news_for_analysis = None
    analyze_news_impact_with_xai = None
from mistralai import Mistral
from dotenv import load_dotenv
import pandas as pd

# Charger le .env depuis la racine du projet
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_xai_explanation_for_asset(asset_ticker: str) -> dict:
    """
    Fonction principale pour obtenir l'explication XAI d'un actif
    À utiliser dans le dashboard Streamlit (utilise NLP.stock_analyzer + Mistral)
    
    Args:
        asset_ticker: Le ticker de l'actif (ex: "AAPL", "TSLA")
    
    Returns:
        dict: Contient l'analyse XAI complète
    """
    if analyze_asset_news is None:
        return {
            "asset_ticker": asset_ticker,
            "error": "Module NLP.stock_analyzer non disponible",
            "sentiment_trend": "N/A",
            "recommendation": "ERREUR",
            "xai_explanation": "Impossible d'analyser: NLP non importé.",
        }
    try:
        analysis = analyze_asset_news(asset_ticker)
        return analysis
    except Exception as e:
        print(f"Erreur lors de l'analyse XAI: {str(e)}")
        return {
            "asset_ticker": asset_ticker,
            "error": str(e),
            "sentiment_trend": "N/A",
            "recommendation": "ERREUR",
            "xai_explanation": f"Impossible d'analyser cet actif: {str(e)}"
        }

def get_sentiment_for_asset(asset_ticker: str, sentiment_df: pd.DataFrame = None) -> dict:
    """
    Récupère uniquement le résumé du sentiment sans analyse XAI complète
    Plus rapide pour l'affichage en temps réel
    
    Args:
        asset_ticker: Le ticker de l'actif
        sentiment_df: DataFrame optionnel avec les données de sentiment
    
    Returns:
        dict: Résumé du sentiment
    """
    try:
        if sentiment_df is None:
            sentiment_df = load_latest_sentiment_data()
        
        summary = get_sentiment_summary(asset_ticker, sentiment_df)
        return summary
    except Exception as e:
        print(f"Erreur lors de la récupération du sentiment: {str(e)}")
        return {
            "asset_ticker": asset_ticker,
            "total_news": 0,
            "sentiment_trend": "N/A",
            "error": str(e)
        }

def format_xai_for_display(analysis: dict) -> str:
    """
    Formate l'analyse XAI pour un affichage dans Streamlit
    
    Args:
        analysis: Dictionnaire d'analyse XAI
    
    Returns:
        str: Texte formaté pour Streamlit (supporte Markdown)
    """
    if not analysis or "error" in analysis:
        return "⚠️ Analyse non disponible"
    
    output = f"""
### 🎯 Analyse XAI - {analysis['asset_ticker']}

#### 📊 Sentiment Global
- **Tendance**: {analysis['sentiment_trend']}
- **News analysées**: {analysis.get('total_news', 0)}
- **Sentiment positif**: {analysis.get('avg_positive', 0):.1%}
- **Sentiment négatif**: {analysis.get('avg_negative', 0):.1%}

#### 💡 Recommandation
- **Action**: {analysis['recommendation']}
- **Confiance**: {analysis['confidence']}

#### 📝 Explication Détaillée
{analysis['xai_explanation']}

---
*Généré le {analysis.get('timestamp', 'N/A')}*
"""
    return output

def get_news_list_for_asset(asset_ticker: str, sentiment_df: pd.DataFrame = None, limit: int = 10) -> list:
    """
    Récupère la liste des news pour un actif
    
    Args:
        asset_ticker: Le ticker de l'actif
        sentiment_df: DataFrame optionnel
        limit: Nombre maximum de news à retourner
    
    Returns:
        list: Liste de dictionnaires de news
    """
    try:
        news_list = fetch_news_for_asset(asset_ticker, sentiment_df)
        return news_list[:limit]
    except Exception as e:
        print(f"Erreur lors de la récupération des news: {str(e)}")
        return []

# Fonction utilitaire pour vérifier si l'API Mistral est configurée
def check_mistral_api() -> bool:
    """
    Vérifie si l'API Mistral est correctement configurée
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    return api_key is not None and api_key != ""

if __name__ == "__main__":
    # Test du module
    print("🧪 Test du module XAI Integration\n")
    
    if not check_mistral_api():
        print("❌ MISTRAL_API_KEY non configurée")
        print("   Créez un fichier .env avec MISTRAL_API_KEY=votre_cle")
    else:
        print("✅ MISTRAL_API_KEY configurée\n")
        
        # Test avec AAPL
        test_ticker = "AAPL"
        print(f"Test avec {test_ticker}...\n")
        
        # Test 1: Sentiment rapide
        print("1️⃣ Test sentiment rapide:")
        sentiment = get_sentiment_for_asset(test_ticker)
        print(f"   Tendance: {sentiment.get('sentiment_trend', 'N/A')}")
        print(f"   News: {sentiment.get('total_news', 0)}\n")
        
        # Test 2: Analyse XAI complète (plus lent)
        # print("2️⃣ Test analyse XAI complète:")
        # analysis = get_xai_explanation_for_asset(test_ticker)
        # print(format_xai_for_display(analysis))
