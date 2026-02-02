import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from pathlib import Path

# Import des symboles depuis le module fetching_data
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from fetching_data.stock_fetcher import SYMBOLS


class HistoricalDataCollector:
    """
    Collecteur de données historiques pour l'analyse d'anomalies.
    Récupère les données OHLCV (Open, High, Low, Close, Volume) sur plusieurs années.
    """

    def __init__(self, output_dir: str = "data/historical"):
        """
        Initialise le collecteur.

        Args:
            output_dir: Répertoire de sauvegarde des données
        """
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.symbols = self._flatten_symbols()

    def _flatten_symbols(self) -> Dict[str, str]:
        """
        Aplatit la structure SYMBOLS en un dictionnaire {nom: symbole}.

        Returns:
            Dict avec nom de l'actif comme clé et symbole comme valeur
        """
        flat_symbols = {}
        for category, items in SYMBOLS.items():
            for name, symbol in items.items():
                flat_symbols[name] = symbol
        return flat_symbols

    def fetch_historical_data(
        self,
        symbol: str,
        name: str,
        period: str = "3y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Récupère les données historiques pour un symbole donné.

        Args:
            symbol: Symbole Yahoo Finance (ex: "AAPL")
            name: Nom de l'actif (ex: "APPLE")
            period: Période de récupération (1y, 3y, 5y, 10y, max)
            interval: Intervalle des données (1d, 1h, etc.)

        Returns:
            DataFrame avec colonnes: Date, Open, High, Low, Close, Volume
        """
        try:
            print(f"  Récupération de {name} ({symbol})...", end=" ")

            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                print("❌ Aucune donnée")
                return None

            # Réinitialiser l'index pour avoir Date comme colonne
            df = df.reset_index()

            # Renommer les colonnes pour cohérence
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Garder uniquement les colonnes essentielles
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            # Ajouter des colonnes calculées
            df['daily_return'] = df['close'].pct_change() * 100  # Variation % journalière
            df['daily_variation'] = df['close'].diff()  # Variation absolue

            # Variation sur 5 jours
            df['return_5d'] = df['close'].pct_change(periods=5) * 100

            # Variation sur 30 jours
            df['return_30d'] = df['close'].pct_change(periods=30) * 100

            # Ajouter métadonnées
            df['symbol'] = symbol
            df['name'] = name

            print(f"✓ {len(df)} lignes")
            return df

        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return None

    def fetch_all_historical_data(
        self,
        period: str = "3y",
        interval: str = "1d",
        symbols_to_fetch: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Récupère les données historiques pour tous les symboles ou une sélection.

        Args:
            period: Période de récupération
            interval: Intervalle des données
            symbols_to_fetch: Liste de noms d'actifs à récupérer (None = tous)

        Returns:
            Dictionnaire {nom_actif: DataFrame}
        """
        print(f"\n🔄 Récupération des données historiques ({period})...")
        print("="*60)

        all_data = {}

        # Filtrer les symboles si nécessaire
        symbols = self.symbols
        if symbols_to_fetch:
            symbols = {k: v for k, v in symbols.items() if k in symbols_to_fetch}

        for name, symbol in symbols.items():
            df = self.fetch_historical_data(symbol, name, period, interval)
            if df is not None:
                all_data[name] = df

        print("="*60)
        print(f"✅ {len(all_data)}/{len(symbols)} actifs récupérés\n")

        return all_data

    def save_historical_data(
        self,
        data: Dict[str, pd.DataFrame],
        suffix: str = ""
    ) -> List[str]:
        """
        Sauvegarde les données historiques en fichiers CSV.

        Args:
            data: Dictionnaire {nom_actif: DataFrame}
            suffix: Suffixe optionnel pour les noms de fichiers

        Returns:
            Liste des chemins de fichiers créés
        """
        print("💾 Sauvegarde des données...")

        saved_files = []

        for name, df in data.items():
            filename = f"{name}_historical{suffix}.csv"
            filepath = self.output_dir / filename

            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            saved_files.append(str(filepath))
            print(f"  ✓ {filename}")

        print(f"\n✅ {len(saved_files)} fichiers sauvegardés dans {self.output_dir}\n")

        return saved_files

    def load_historical_data(self, name: str, suffix: str = "") -> Optional[pd.DataFrame]:
        """
        Charge les données historiques depuis un fichier CSV.

        Args:
            name: Nom de l'actif
            suffix: Suffixe du nom de fichier

        Returns:
            DataFrame ou None si fichier introuvable
        """
        filename = f"{name}_historical{suffix}.csv"
        filepath = self.output_dir / filename

        if not filepath.exists():
            print(f"❌ Fichier {filename} introuvable")
            return None

        df = pd.read_csv(filepath, parse_dates=['date'])
        return df

    def get_data_summary(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Génère un résumé des données collectées.

        Args:
            data: Dictionnaire {nom_actif: DataFrame}

        Returns:
            DataFrame résumé
        """
        summary_rows = []

        for name, df in data.items():
            summary_rows.append({
                'asset': name,
                'symbol': df['symbol'].iloc[0],
                'start_date': df['date'].min(),
                'end_date': df['date'].max(),
                'num_days': len(df),
                'min_price': df['close'].min(),
                'max_price': df['close'].max(),
                'avg_volume': df['volume'].mean(),
                'total_return': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
            })

        summary_df = pd.DataFrame(summary_rows)
        return summary_df

    def collect_and_save(
        self,
        period: str = "3y",
        interval: str = "1d",
        symbols_to_fetch: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Pipeline complet : récupère et sauvegarde les données.

        Args:
            period: Période de récupération
            interval: Intervalle des données
            symbols_to_fetch: Liste de noms d'actifs (None = tous)

        Returns:
            Dictionnaire des données collectées
        """
        # Récupérer les données
        data = self.fetch_all_historical_data(period, interval, symbols_to_fetch)

        if not data:
            print("❌ Aucune donnée récupérée")
            return {}

        # Sauvegarder
        self.save_historical_data(data)

        # Afficher le résumé
        summary = self.get_data_summary(data)
        print("📊 RÉSUMÉ DES DONNÉES")
        print("="*60)
        print(summary.to_string(index=False))
        print("="*60 + "\n")

        return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collecte de données historiques")
    parser.add_argument("--period", default="3y", help="Période (1y, 3y, 5y, 10y, max)")
    parser.add_argument("--assets", nargs="+", help="Liste d'actifs spécifiques")

    args = parser.parse_args()

    collector = HistoricalDataCollector()
    collector.collect_and_save(period=args.period, symbols_to_fetch=args.assets)
