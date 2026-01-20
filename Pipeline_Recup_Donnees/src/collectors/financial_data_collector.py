"""
Collecteur de données financières historiques
Utilise yfinance pour récupérer les données de prix, volumes, etc.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import time
from loguru import logger


class FinancialDataCollector:
    """Collecte les données financières historiques via Yahoo Finance"""

    def __init__(self, output_dir: str = "./data/raw/financial"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Récupère les données historiques pour un ticker

        Args:
            ticker: Symbole du ticker (ex: 'AAPL')
            start_date: Date de début (format: 'YYYY-MM-DD')
            end_date: Date de fin (format: 'YYYY-MM-DD')
            interval: Intervalle de temps (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)

        Returns:
            DataFrame avec les données OHLCV + métriques calculées
        """
        try:
            logger.info(f"Récupération des données pour {ticker} de {start_date} à {end_date}")

            # Créer l'objet Ticker
            stock = yf.Ticker(ticker)

            # Télécharger les données historiques
            df = stock.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True  # Ajuster pour les splits/dividendes
            )

            if df.empty:
                logger.warning(f"Aucune donnée trouvée pour {ticker}")
                return None

            # Ajouter le ticker comme colonne
            df['Ticker'] = ticker

            # Calculer des métriques supplémentaires
            df = self._add_market_metrics(df)

            # Sauvegarder les données brutes
            self._save_raw_data(df, ticker)

            logger.success(f"✓ {len(df)} lignes récupérées pour {ticker}")
            return df

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de {ticker}: {str(e)}")
            return None

    def _add_market_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute des métriques de marché calculées"""

        # Retours (returns)
        df['Return'] = df['Close'].pct_change()
        df['Return_Abs'] = df['Close'].diff()

        # Volatilité (écart-type mobile sur 20 jours)
        df['Volatility_20d'] = df['Return'].rolling(window=20).std()

        # Volume anormal (ratio volume / moyenne mobile 20j)
        df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA20']

        # Prix high/low range
        df['Price_Range'] = df['High'] - df['Low']
        df['Price_Range_Pct'] = (df['High'] - df['Low']) / df['Open'] * 100

        # Moving averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()

        # Détection de mouvements anormaux (>2 sigma)
        df['Abnormal_Move'] = abs(df['Return']) > (2 * df['Return'].std())

        return df

    def _save_raw_data(self, df: pd.DataFrame, ticker: str):
        """Sauvegarde les données brutes en CSV"""
        output_file = self.output_dir / f"{ticker}_historical.csv"
        df.to_csv(output_file)
        logger.debug(f"Données sauvegardées: {output_file}")

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        delay: float = 0.5
    ) -> pd.DataFrame:
        """
        Récupère les données pour plusieurs tickers

        Args:
            tickers: Liste des symboles
            start_date: Date de début
            end_date: Date de fin
            interval: Intervalle de temps
            delay: Délai entre les requêtes (secondes)

        Returns:
            DataFrame combiné de tous les tickers
        """
        all_data = []

        for ticker in tickers:
            df = self.fetch_historical_data(ticker, start_date, end_date, interval)
            if df is not None:
                all_data.append(df)

            # Pause pour éviter le rate limiting
            time.sleep(delay)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=False)
            logger.success(f"✓ Données collectées pour {len(all_data)} tickers")
            return combined_df
        else:
            logger.warning("Aucune donnée collectée")
            return pd.DataFrame()

    def get_company_info(self, ticker: str) -> dict:
        """Récupère les informations sur l'entreprise"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'ticker': ticker,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'description': info.get('longBusinessSummary', '')
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos de {ticker}: {e}")
            return {}

    def detect_market_events(self, df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
        """
        Détecte les événements de marché significatifs

        Args:
            df: DataFrame avec les données financières
            threshold: Seuil de mouvement significatif (ex: 0.05 = 5%)

        Returns:
            DataFrame filtré avec uniquement les événements significatifs
        """
        # Mouvements de prix > threshold
        significant_moves = df[abs(df['Return']) > threshold].copy()

        # Volumes anormaux (>2x la moyenne)
        high_volume = df[df['Volume_Ratio'] > 2].copy()

        # Combiner les événements
        events = pd.concat([significant_moves, high_volume]).drop_duplicates()
        events = events.sort_index()

        logger.info(f"Détecté {len(events)} événements de marché significatifs")
        return events


if __name__ == "__main__":
    # Test du collecteur
    from src.utils.logger import setup_logger

    setup_logger()

    collector = FinancialDataCollector()

    # Test avec un ticker
    df = collector.fetch_historical_data(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01"
    )

    if df is not None:
        print("\nAperçu des données:")
        print(df.head())
        print(f"\nNombre total de lignes: {len(df)}")
        print(f"\nColonnes: {df.columns.tolist()}")

        # Événements significatifs
        events = collector.detect_market_events(df)
        print(f"\nÉvénements de marché détectés: {len(events)}")
