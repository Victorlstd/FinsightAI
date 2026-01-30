import pandas as pd
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from mistralai import Mistral
from stock_fetcher import load_latest_sentiment_data, fetch_news_for_asset, get_sentiment_summary

# Charger le .env depuis la racine du projet
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY non trouvée. Créez un fichier .env avec MISTRAL_API_KEY=votre_cle")
MISTRAL_MODEL = "mistral-large-latest"


def format_news_for_analysis(news_list: List[Dict], sentiment_summary: Dict) -> str:
    """
    Formate les news pour l'analyse XAI
    """
    if not news_list:
        return "Aucune actualité disponible pour cet actif."
    
    formatted = f"""
=== ANALYSE SENTIMENT - {sentiment_summary['asset_ticker']} ===

📊 RÉSUMÉ GLOBAL:
- Total d'actualités analysées: {sentiment_summary['total_news']}
- Tendance globale: {sentiment_summary['sentiment_trend']}
- Sentiment positif moyen: {sentiment_summary['avg_positive']:.1%}
- Sentiment négatif moyen: {sentiment_summary['avg_negative']:.1%}
- Confiance moyenne: {sentiment_summary['confidence']:.1%}

📰 ACTUALITÉS RÉCENTES:
"""
    
    # Limiter à 10 news pour ne pas surcharger le contexte
    for i, news in enumerate(news_list[:10], 1):
        sentiment_icon = "🟢" if news['sentiment'] == 'Positive' else "🔴"
        
        # Gérer les descriptions manquantes ou non-string (NaN)
        description = news.get('description', '')
        if pd.isna(description) or not isinstance(description, str):
            description = "Description non disponible"
        else:
            description = description[:200] + "..." if len(description) > 200 else description
        
        formatted += f"""
{i}. {sentiment_icon} {news['title']}
   Source: {news['source']} | Publié: {news['published_at']}
   Description: {description}
   Sentiment: {news['sentiment']} (Confiance: {news['confidence']:.1%})
   Prob. Positive: {news['prob_positive']:.1%} | Prob. Négative: {news['prob_negative']:.1%}
"""
    
    return formatted

def analyze_news_impact_with_xai(client: Mistral, asset_ticker: str, news_context: str, sentiment_summary: Dict) -> Dict:
    """
    Utilise Mistral pour générer une explication XAI de l'impact des news sur l'actif
    """
    
    trend_label = sentiment_summary['sentiment_trend']
    
    prompt = f"""Tu es un expert en analyse financière et en XAI (Explainable AI). 

Voici le contexte des actualités récentes concernant l'actif {asset_ticker}:

{news_context}

Ta mission est de fournir une analyse XAI (Explainable AI) détaillée qui explique:

1. **JUSTIFICATION DU SENTIMENT {trend_label}**
   - Pourquoi le sentiment global est-il {trend_label} ?
   - Quels sont les éléments factuels des actualités qui justifient ce sentiment ?
   - Analyse la cohérence entre les différentes sources d'information

2. **IMPACT SUR LE MARCHÉ**
   - Quel impact ces actualités peuvent-elles avoir sur le cours de l'actif {asset_ticker} ?
   - Impact à court terme (1-7 jours)
   - Impact à moyen terme (1-3 mois)
   - Quels sont les facteurs de risque identifiés dans ces actualités ?

3. **MÉCANISMES D'INFLUENCE**
   - Comment ces actualités influencent-elles la psychologie des investisseurs ?
   - Quels sont les canaux de transmission (confiance, anticipation, réaction du marché) ?
   - Y a-t-il des effets de contagion possibles sur le secteur ou l'indice ?

4. **RECOMMANDATION CONTEXTUALISÉE**
   - Recommandation: ACHETER / VENDRE / CONSERVER / SURVEILLER
   - Niveau de confiance: ÉLEVÉ / MOYEN / FAIBLE
   - Justification basée sur l'analyse des news
   - Conditions à surveiller

**IMPORTANT**: 
- Sois factuel et cite les actualités spécifiques
- Explique le "pourquoi" derrière chaque conclusion
- Fournis une analyse nuancée et équilibrée
- Reste concis (maximum 15 lignes au total)
- Structure ta réponse avec des sections claires

Réponds de manière structurée et professionnelle."""

    try:
        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Extraction automatique de la recommandation
        recommendation = "N/A"
        confidence = "N/A"
        
        if "ACHETER" in analysis_text.upper():
            recommendation = "ACHETER"
        elif "VENDRE" in analysis_text.upper():
            recommendation = "VENDRE"
        elif "CONSERVER" in analysis_text.upper():
            recommendation = "CONSERVER"
        elif "SURVEILLER" in analysis_text.upper():
            recommendation = "SURVEILLER"
        
        if "ÉLEVÉ" in analysis_text.upper() or "ELEVE" in analysis_text.upper():
            confidence = "ÉLEVÉ"
        elif "MOYEN" in analysis_text.upper():
            confidence = "MOYEN"
        elif "FAIBLE" in analysis_text.upper():
            confidence = "FAIBLE"
        
        return {
            "asset_ticker": asset_ticker,
            "sentiment_trend": sentiment_summary['sentiment_trend'],
            "total_news": sentiment_summary['total_news'],
            "avg_positive": sentiment_summary['avg_positive'],
            "avg_negative": sentiment_summary['avg_negative'],
            "recommendation": recommendation,
            "confidence": confidence,
            "xai_explanation": analysis_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse XAI pour {asset_ticker}: {str(e)}")
        return {
            "asset_ticker": asset_ticker,
            "sentiment_trend": sentiment_summary['sentiment_trend'],
            "total_news": sentiment_summary['total_news'],
            "recommendation": "ERREUR",
            "confidence": "N/A",
            "xai_explanation": f"Erreur lors de l'analyse: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }



def analyze_asset_news(asset_ticker: str, output_file: str = None) -> Dict:
    """
    Analyse complète des news d'un actif avec XAI
    """
    print(f"🔍 Analyse XAI pour {asset_ticker}...")
    
    # Charger les données de sentiment
    sentiment_df = load_latest_sentiment_data()
    
    if sentiment_df.empty:
        print("❌ Aucune donnée de sentiment disponible")
        return {}
    
    # Récupérer les news et le résumé
    print("📰 Récupération des actualités...")
    sentiment_summary = get_sentiment_summary(asset_ticker, sentiment_df)
    
    if sentiment_summary['total_news'] == 0:
        print(f"❌ Aucune news trouvée pour {asset_ticker}")
        return {}
    
    print(f"✅ {sentiment_summary['total_news']} news trouvées")
    print(f"📊 Tendance: {sentiment_summary['sentiment_trend']}")
    
    # Formater le contexte
    news_context = format_news_for_analysis(sentiment_summary['news'], sentiment_summary)
    
    # Analyse XAI avec Mistral
    print("🤖 Génération de l'analyse XAI...")
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    analysis = analyze_news_impact_with_xai(client, asset_ticker, news_context, sentiment_summary)
    
    # Sauvegarder si demandé
    if output_file:
        analysis_df = pd.DataFrame([analysis])
        analysis_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Analyse sauvegardée dans {output_file}")
    
    return analysis

def analyze_multiple_assets(asset_tickers: List[str], output_file: str = None) -> pd.DataFrame:
    """
    Analyse plusieurs actifs et génère un rapport consolidé
    """
    print(f"📊 Analyse de {len(asset_tickers)} actifs...\n")
    
    analyses = []
    
    for ticker in asset_tickers:
        print(f"\n{'='*60}")
        analysis = analyze_asset_news(ticker)
        if analysis:
            analyses.append(analysis)
        print(f"{'='*60}\n")
    
    if not analyses:
        print("❌ Aucune analyse générée")
        return pd.DataFrame()
    
    analysis_df = pd.DataFrame(analyses)
    
    if output_file is None:
        output_file = f"xai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    analysis_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Analyses consolidées sauvegardées dans {output_file}")
    
    return analysis_df

def display_xai_analysis(analysis: Dict):
    """
    Affiche l'analyse XAI de manière formatée
    """
    if not analysis:
        return
    
    print("\n" + "="*80)
    print(f"🎯 ANALYSE XAI - {analysis['asset_ticker']}")
    print("="*80)
    
    print(f"\n📊 SENTIMENT GLOBAL:")
    print(f"   Tendance: {analysis['sentiment_trend']}")
    print(f"   News analysées: {analysis['total_news']}")
    print(f"   Sentiment positif: {analysis['avg_positive']:.1%}")
    print(f"   Sentiment négatif: {analysis['avg_negative']:.1%}")
    
    print(f"\n🎯 RECOMMANDATION:")
    print(f"   Action: {analysis['recommendation']}")
    print(f"   Confiance: {analysis['confidence']}")
    
    print(f"\n📝 EXPLICATION XAI:")
    print("-"*80)
    print(analysis['xai_explanation'])
    print("-"*80)
    
    print(f"\n⏰ Généré le: {analysis['timestamp']}")
    print("="*80 + "\n")



if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Analyse d'un seul actif
        asset = sys.argv[1]
        analysis = analyze_asset_news(asset)
        
        if analysis:
            display_xai_analysis(analysis)
            
            # Sauvegarder l'analyse
            output_file = f"xai_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            pd.DataFrame([analysis]).to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"💾 Analyse sauvegardée dans {output_file}")
    else:
        print("Usage: python stock_analyzer.py <ASSET_TICKER>")
        print("Exemple: python stock_analyzer.py AAPL")
        print("\nOu pour analyser plusieurs actifs:")
        print("python stock_analyzer.py AAPL TSLA AMZN")

