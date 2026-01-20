"""
Module de corrélation entre événements de marché et données textuelles (news/social)
Permet de créer un dataset pour l'entraînement du modèle
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Optional
from loguru import logger
import numpy as np


class MarketNewsCorrelator:
    """
    Corrèle les mouvements de marché avec les news et posts sociaux
    pour détecter les patterns prédictifs
    """

    def __init__(self, time_window_hours: int = 24):
        """
        Args:
            time_window_hours: Fenêtre temporelle pour corréler les événements
                              (ex: 24h = chercher news dans les 24h précédent le mouvement)
        """
        self.time_window = timedelta(hours=time_window_hours)

    def correlate_market_events_with_news(
        self,
        market_df: pd.DataFrame,
        news_df: pd.DataFrame,
        social_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Corrèle les mouvements de marché avec les news et posts sociaux

        Args:
            market_df: DataFrame avec colonnes [date, ticker, close, return_pct, ...]
            news_df: DataFrame avec colonnes [date, query, title, sentiment_score, ...]
            social_df: DataFrame optionnel avec posts sociaux

        Returns:
            DataFrame corrélé avec features pour l'entraînement
        """
        logger.info("Démarrage de la corrélation market-news-social...")

        # S'assurer que les dates sont datetime
        market_df['date'] = pd.to_datetime(market_df['date'])
        news_df['date'] = pd.to_datetime(news_df['date'])

        if social_df is not None and not social_df.empty:
            social_df['date'] = pd.to_datetime(social_df['date'])

        # Trier par date
        market_df = market_df.sort_values('date')
        news_df = news_df.sort_values('date')

        correlated_data = []

        # Pour chaque ticker
        tickers = market_df['ticker'].unique()

        for ticker in tickers:
            logger.info(f"Corrélation pour {ticker}...")

            ticker_market = market_df[market_df['ticker'] == ticker].copy()

            # Filtrer les news pour ce ticker
            ticker_news = news_df[
                (news_df['query'] == ticker) |
                (news_df['query'].str.contains(ticker, case=False, na=False))
            ].copy()

            if social_df is not None:
                ticker_social = social_df[
                    (social_df['keyword'] == ticker) |
                    (social_df['keyword'].str.contains(ticker, case=False, na=False))
                ].copy()
            else:
                ticker_social = pd.DataFrame()

            # Pour chaque jour de trading
            for _, market_row in ticker_market.iterrows():
                market_date = market_row['date']

                # Fenêtre de temps pour chercher les news/posts
                window_start = market_date - self.time_window
                window_end = market_date

                # Filtrer news dans la fenêtre
                relevant_news = ticker_news[
                    (ticker_news['date'] >= window_start) &
                    (ticker_news['date'] < window_end)
                ]

                # Filtrer posts sociaux dans la fenêtre
                relevant_social = pd.DataFrame()
                if not ticker_social.empty:
                    relevant_social = ticker_social[
                        (ticker_social['date'] >= window_start) &
                        (ticker_social['date'] < window_end)
                    ]

                # Calculer les features
                features = self._extract_features(
                    market_row,
                    relevant_news,
                    relevant_social
                )

                correlated_data.append(features)

        result_df = pd.DataFrame(correlated_data)
        logger.success(f"✓ Corrélation terminée: {len(result_df)} points de données")

        return result_df

    def _extract_features(
        self,
        market_row: pd.Series,
        news_df: pd.DataFrame,
        social_df: pd.DataFrame
    ) -> dict:
        """
        Extrait les features pour un point de données

        Returns:
            Dictionnaire de features
        """
        features = {
            # Features de marché
            'date': market_row['date'],
            'ticker': market_row.get('ticker'),
            'close_price': market_row.get('close', market_row.get('Close')),
            'return_pct': market_row.get('return_pct', market_row.get('Return', 0)),
            'volume': market_row.get('volume', market_row.get('Volume')),
            'volatility': market_row.get('volatility_20d', market_row.get('Volatility_20d')),
            'volume_ratio': market_row.get('volume_ratio', market_row.get('Volume_Ratio', 1)),

            # Label: mouvement significatif (pour classification)
            'is_significant_move': abs(market_row.get('return_pct', 0)) > 0.02,  # >2%
            'is_abnormal': market_row.get('abnormal_move', market_row.get('Abnormal_Move', False)),

            # Direction du mouvement
            'move_direction': 1 if market_row.get('return_pct', 0) > 0 else -1,
        }

        # Features des news
        if not news_df.empty:
            features.update({
                'num_news': len(news_df),
                'avg_news_sentiment': news_df['sentiment_score'].mean() if 'sentiment_score' in news_df else 0,
                'min_news_sentiment': news_df['sentiment_score'].min() if 'sentiment_score' in news_df else 0,
                'max_news_sentiment': news_df['sentiment_score'].max() if 'sentiment_score' in news_df else 0,
                'std_news_sentiment': news_df['sentiment_score'].std() if 'sentiment_score' in news_df else 0,
            })

            # Compter les news par sentiment
            if 'sentiment_score' in news_df.columns:
                features['num_positive_news'] = (news_df['sentiment_score'] > 0.1).sum()
                features['num_negative_news'] = (news_df['sentiment_score'] < -0.1).sum()
                features['num_neutral_news'] = ((news_df['sentiment_score'] >= -0.1) &
                                                 (news_df['sentiment_score'] <= 0.1)).sum()
        else:
            features.update({
                'num_news': 0,
                'avg_news_sentiment': 0,
                'min_news_sentiment': 0,
                'max_news_sentiment': 0,
                'std_news_sentiment': 0,
                'num_positive_news': 0,
                'num_negative_news': 0,
                'num_neutral_news': 0,
            })

        # Features des posts sociaux
        if not social_df.empty:
            features.update({
                'num_social_posts': len(social_df),
                'avg_social_sentiment': social_df['sentiment_score'].mean() if 'sentiment_score' in social_df else 0,
                'total_social_score': social_df['score'].sum() if 'score' in social_df else 0,
                'avg_social_score': social_df['score'].mean() if 'score' in social_df else 0,
                'total_comments': social_df['num_comments'].sum() if 'num_comments' in social_df else 0,
            })
        else:
            features.update({
                'num_social_posts': 0,
                'avg_social_sentiment': 0,
                'total_social_score': 0,
                'avg_social_score': 0,
                'total_comments': 0,
            })

        # Features combinées
        features['total_content'] = features['num_news'] + features['num_social_posts']
        features['combined_sentiment'] = (
            features['avg_news_sentiment'] * features['num_news'] +
            features['avg_social_sentiment'] * features['num_social_posts']
        ) / max(features['total_content'], 1)

        return features

    def create_training_dataset(
        self,
        correlated_df: pd.DataFrame,
        target_column: str = 'is_significant_move',
        feature_columns: Optional[list] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Crée un dataset prêt pour l'entraînement

        Args:
            correlated_df: DataFrame corrélé
            target_column: Colonne cible (label)
            feature_columns: Liste des colonnes features (None = auto)

        Returns:
            (X, y) - Features et labels
        """
        if feature_columns is None:
            # Colonnes features par défaut
            feature_columns = [
                'return_pct', 'volume_ratio', 'volatility',
                'num_news', 'avg_news_sentiment', 'num_positive_news', 'num_negative_news',
                'num_social_posts', 'avg_social_sentiment', 'total_social_score',
                'combined_sentiment', 'total_content'
            ]

        # Filtrer les colonnes qui existent
        available_features = [col for col in feature_columns if col in correlated_df.columns]

        X = correlated_df[available_features].fillna(0)
        y = correlated_df[target_column]

        logger.info(f"Dataset créé: {len(X)} samples, {len(available_features)} features")
        logger.info(f"Distribution des labels: {y.value_counts().to_dict()}")

        return X, y

    def analyze_correlations(self, correlated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyse les corrélations entre features et mouvements de marché

        Returns:
            DataFrame avec les corrélations
        """
        numeric_cols = correlated_df.select_dtypes(include=[np.number]).columns
        correlations = correlated_df[numeric_cols].corr()['return_pct'].sort_values(ascending=False)

        logger.info("\nTop corrélations avec return_pct:")
        print(correlations.head(10))

        return correlations

    def get_event_statistics(self, correlated_df: pd.DataFrame) -> dict:
        """Calcule des statistiques sur les événements"""
        stats = {
            'total_days': len(correlated_df),
            'significant_moves': correlated_df['is_significant_move'].sum(),
            'pct_significant': correlated_df['is_significant_move'].mean() * 100,
            'avg_news_per_day': correlated_df['num_news'].mean(),
            'avg_social_per_day': correlated_df['num_social_posts'].mean(),
            'days_with_news': (correlated_df['num_news'] > 0).sum(),
            'days_with_social': (correlated_df['num_social_posts'] > 0).sum(),
        }

        logger.info("\n📊 Statistiques du dataset:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")

        return stats


if __name__ == "__main__":
    # Test du corrélateur
    from src.utils.logger import setup_logger

    setup_logger()

    # Créer des données de test
    dates = pd.date_range('2024-01-01', periods=30, freq='D')

    market_df = pd.DataFrame({
        'date': dates,
        'ticker': 'AAPL',
        'close': np.random.randn(30).cumsum() + 100,
        'return_pct': np.random.randn(30) * 0.02,
        'volume': np.random.randint(1000000, 5000000, 30),
        'volatility_20d': np.random.rand(30) * 0.02,
        'volume_ratio': np.random.rand(30) * 2,
        'abnormal_move': np.random.rand(30) > 0.8
    })

    news_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=50, freq='12H'),
        'query': 'AAPL',
        'title': ['News ' + str(i) for i in range(50)],
        'sentiment_score': np.random.randn(50) * 0.5
    })

    correlator = MarketNewsCorrelator(time_window_hours=24)
    correlated = correlator.correlate_market_events_with_news(market_df, news_df)

    print("\nDataset corrélé:")
    print(correlated.head())
    print(f"\nShape: {correlated.shape}")

    X, y = correlator.create_training_dataset(correlated)
    print(f"\nTraining set: X shape={X.shape}, y shape={y.shape}")
