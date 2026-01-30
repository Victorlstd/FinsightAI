import pandas as pd
import os
from datetime import datetime
from typing import Dict, List
from glob import glob

# Mapping des tickers pour convertir entre différents formats
TICKER_MAPPING = {
    "SP500": "S&P 500",
    "AAPL": "Apple",
    "AMZN": "Amazon",
    "SAN": "Sanofi",
    "HO": "Intercontinental Hotels",
    "MC": "LVMH",
    "ENGI": "Engie",
    "TTE": "TotalEnergies",
    "RCO": "Intercontinental Hotels",
    "AIR": "Airbus",
    "STLA": "Stellantis",
    "TSLA": "Tesla",
    "OIL": "Oil",
    "GOLD": "Gold",
    "GAS": "Natural Gas"
}


def load_latest_sentiment_data(data_dir: str = "../NLP") -> pd.DataFrame:
    """
    Charge le fichier de sentiment analysis le plus récent
    """
    try:
        # Chercher d'abord les fichiers hybrid_news_financial_classified
        sentiment_files = glob(os.path.join(data_dir, "hybrid_news_financial_classified_*.csv"))
        
        # Si aucun fichier hybrid trouvé, chercher les anciens fichiers sentiment_analysis
        if not sentiment_files:
            sentiment_files = glob(os.path.join(data_dir, "sentiment_analysis_*.csv"))
        
        if not sentiment_files:
            print(f"❌ Aucun fichier de sentiment trouvé dans {data_dir}")
            return pd.DataFrame()
        
        latest_file = max(sentiment_files, key=os.path.getmtime)
        print(f"📂 Chargement: {os.path.basename(latest_file)}")
        
        df = pd.read_csv(latest_file)
        total_news = len(df)
        
        # Filtrer uniquement les news financières si la colonne financial_label existe
        if 'financial_label' in df.columns:
            df = df[df['financial_label'] == 'Financial'].copy()
            print(f"✅ {len(df)} news financières chargées (sur {total_news} au total)")
        else:
            print(f"✅ {len(df)} news chargées")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {str(e)}")
        return pd.DataFrame()

def fetch_news_for_asset(asset_ticker: str, sentiment_df: pd.DataFrame = None) -> List[Dict]:
    """
    Récupère toutes les news pour un actif spécifique avec leur sentiment
    """
    if sentiment_df is None:
        sentiment_df = load_latest_sentiment_data()
    
    if sentiment_df.empty:
        return []
    
    # Normaliser le ticker (enlever les suffixes .PA, etc.)
    normalized_ticker = asset_ticker.upper().replace('.PA', '').replace('.', '')
    
    # Filtrer les news pour cet actif
    asset_news = sentiment_df[
        sentiment_df['asset_ticker'].str.contains(normalized_ticker, case=False, na=False)
    ].copy()
    
    if asset_news.empty:
        print(f"❌ Aucune news trouvée pour {asset_ticker}")
        return []
    
    # Convertir en liste de dictionnaires
    news_list = []
    for _, row in asset_news.iterrows():
        news_item = {
            "asset_ticker": row['asset_ticker'],
            "title": row['title'],
            "description": row.get('description', ''),
            "source": row['source'],
            "published_at": row['published_at'],
            "sentiment": row['sentiment'],
            "confidence": row['confidence'],
            "prob_negative": row['prob_negative'],
            "prob_positive": row['prob_positive'],
            "url": row['url']
        }
        news_list.append(news_item)
    
    return news_list

def get_sentiment_summary(asset_ticker: str, sentiment_df: pd.DataFrame = None) -> Dict:
    """
    Calcule un résumé du sentiment pour un actif
    """
    news_list = fetch_news_for_asset(asset_ticker, sentiment_df)
    
    if not news_list:
        return {
            "asset_ticker": asset_ticker,
            "total_news": 0,
            "avg_positive": 0,
            "avg_negative": 0,
            "sentiment_trend": "NEUTRAL",
            "confidence": 0
        }
    
    # Calculer les moyennes
    avg_positive = sum(n['prob_positive'] for n in news_list) / len(news_list)
    avg_negative = sum(n['prob_negative'] for n in news_list) / len(news_list)
    avg_confidence = sum(n['confidence'] for n in news_list) / len(news_list)
    
    # Déterminer la tendance
    if avg_positive > avg_negative:
        sentiment_trend = "BULLISH"
    elif avg_negative > avg_positive:
        sentiment_trend = "BEARISH"
    else:
        sentiment_trend = "NEUTRAL"
    
    return {
        "asset_ticker": asset_ticker,
        "total_news": len(news_list),
        "avg_positive": avg_positive,
        "avg_negative": avg_negative,
        "sentiment_trend": sentiment_trend,
        "confidence": avg_confidence,
        "news": news_list
    }

def export_asset_news(asset_ticker: str, output_file: str = None) -> pd.DataFrame:
    """
    Exporte les news d'un actif dans un fichier CSV
    """
    sentiment_df = load_latest_sentiment_data()
    news_list = fetch_news_for_asset(asset_ticker, sentiment_df)
    
    if not news_list:
        return pd.DataFrame()
    
    df = pd.DataFrame(news_list)
    
    if output_file is None:
        output_file = f"news_{asset_ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ News exportées dans {output_file}")
    
    return df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        asset = sys.argv[1]
        print(f"🔍 Recherche de news pour {asset}...\n")
        
        summary = get_sentiment_summary(asset)
        
        print("="*60)
        print(f"📊 RÉSUMÉ SENTIMENT - {summary['asset_ticker']}")
        print("="*60)
        print(f"News trouvées: {summary['total_news']}")
        print(f"Tendance: {summary['sentiment_trend']}")
        print(f"Sentiment positif moyen: {summary['avg_positive']:.1%}")
        print(f"Sentiment négatif moyen: {summary['avg_negative']:.1%}")
        print(f"Confiance moyenne: {summary['confidence']:.1%}")
        print("="*60)
        
        # Exporter les news
        if summary['total_news'] > 0:
            export_asset_news(asset)
    else:
        print("Usage: python stock_fetcher.py <ASSET_TICKER>")
        print("Exemple: python stock_fetcher.py AAPL")

