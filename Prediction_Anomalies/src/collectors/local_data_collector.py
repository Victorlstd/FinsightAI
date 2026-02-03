import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class LocalDataCollector:
    """
    Collecteur de données historiques à partir de fichiers CSV locaux.
    Lit les données depuis PFE_MVP/data/raw au lieu de télécharger via yfinance.
    """

    # Mapping des symboles vers noms conviviaux
    SYMBOL_TO_NAME = {
        "AAPL": "APPLE",
        "AMZN": "AMAZON",
        "TSLA": "TESLA",
        "GSPC": "SP 500",
        "FCHI": "CAC40",
        "GDAXI": "GER30",
        "SAN.PA": "SANOFI",
        "AIR.PA": "AIRBUS",
        "MC.PA": "LVMH",
        "ENGI.PA": "ENGIE",
        "TTE.PA": "TOTALENERGIES",
        "STLAP.PA": "STELLANTIS",
        "IHG.L": "INTERCONT HOTELS",
        "HO.PA": "THALES",
        "CL_F": "OIL",
        "GC_F": "GOLD",
        "NG_F": "GAS"
    }

    def __init__(self, input_dir: str = None, output_dir: str = "data/historical"):
        """
        Initialise le collecteur.

        Args:
            input_dir: Répertoire source des CSV (par défaut: PFE_MVP/data/raw)
            output_dir: Répertoire de sauvegarde des données traitées
        """
        # Chemin vers PFE_MVP/data/raw depuis Prediction_Anomalies/
        if input_dir is None:
            self.input_dir = Path(__file__).parent.parent.parent.parent / "PFE_MVP" / "data" / "raw"
        else:
            self.input_dir = Path(input_dir)

        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Vérifier que le répertoire source existe
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Répertoire source introuvable: {self.input_dir}")

        print(f"📂 Source des données: {self.input_dir}")
        print(f"💾 Destination: {self.output_dir}")

    def _get_available_symbols(self) -> Dict[str, str]:
        """
        Liste tous les fichiers CSV disponibles et crée un mapping symbole -> nom.

        Returns:
            Dict {nom: symbole}
        """
        available = {}
        csv_files = list(self.input_dir.glob("*.csv"))

        for csv_file in csv_files:
            # Extraire le symbole du nom de fichier (ex: AAPL.csv -> AAPL)
            symbol = csv_file.stem

            # Chercher le nom convivial
            name = self.SYMBOL_TO_NAME.get(symbol, symbol.replace(".PA", "").replace(".L", "").replace("_F", ""))
            available[name] = symbol

        return available

    def load_local_csv(
        self,
        symbol: str,
        name: str,
        max_years: int = None
    ) -> Optional[pd.DataFrame]:
        """
        Charge et traite un fichier CSV local.

        Args:
            symbol: Symbole du fichier (ex: "AAPL")
            name: Nom de l'actif (ex: "APPLE")
            max_years: Nombre d'années maximum à conserver (None = tout)

        Returns:
            DataFrame avec colonnes standardisées
        """
        csv_path = self.input_dir / f"{symbol}.csv"

        if not csv_path.exists():
            print(f"  ❌ {name} ({symbol}): fichier introuvable")
            return None

        try:
            print(f"  Chargement de {name} ({symbol})...", end=" ")

            # Charger le CSV
            df = pd.read_csv(csv_path)

            if df.empty:
                print("❌ Fichier vide")
                return None

            # Normaliser les noms de colonnes
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Convertir la date en datetime
            df['date'] = pd.to_datetime(df['date'])

            # Filtrer par période si spécifié
            if max_years:
                cutoff_date = datetime.now() - pd.DateOffset(years=max_years)
                df = df[df['date'] >= cutoff_date]

            # Trier par date croissante
            df = df.sort_values('date').reset_index(drop=True)

            # Calculer les variations
            df = self._calculate_variations(df)

            # Ajouter métadonnées
            df['symbol'] = symbol
            df['name'] = name

            # Sélectionner les colonnes finales
            df = df[[
                'date', 'open', 'high', 'low', 'close', 'volume',
                'daily_return', 'daily_variation', 'return_5d', 'return_30d',
                'symbol', 'name'
            ]]

            print(f"✅ {len(df)} jours chargés")
            return df

        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return None

    def _calculate_variations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les variations de prix sur différentes périodes.

        Args:
            df: DataFrame avec colonnes close

        Returns:
            DataFrame enrichi avec colonnes de variation
        """
        # Variation journalière (%)
        df['daily_return'] = df['close'].pct_change() * 100

        # Variation journalière (absolue)
        df['daily_variation'] = df['close'].diff()

        # Variation sur 5 jours (%)
        df['return_5d'] = ((df['close'] - df['close'].shift(5)) / df['close'].shift(5)) * 100

        # Variation sur 30 jours (%)
        df['return_30d'] = ((df['close'] - df['close'].shift(30)) / df['close'].shift(30)) * 100

        return df

    def collect_and_save(
        self,
        period: str = "3y",
        symbols_to_fetch: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Collecte et sauvegarde les données de tous les actifs disponibles.

        Args:
            period: Période au format "Xy" (ex: "3y", "5y", "10y", "max")
            symbols_to_fetch: Liste de noms d'actifs à charger (None = tous)

        Returns:
            Dict {nom_actif: DataFrame}
        """
        # Convertir période en années
        if period == "max":
            max_years = None
        else:
            max_years = int(period.rstrip('y'))

        # Récupérer les symboles disponibles
        available_symbols = self._get_available_symbols()

        if not available_symbols:
            print("❌ Aucun fichier CSV trouvé dans le répertoire source")
            return {}

        print(f"\n📊 {len(available_symbols)} actifs disponibles")

        # Filtrer si demandé
        if symbols_to_fetch:
            # Normaliser les noms demandés (uppercase)
            requested = [s.upper() for s in symbols_to_fetch]
            available_symbols = {
                name: symbol
                for name, symbol in available_symbols.items()
                if name.upper() in requested
            }

            if not available_symbols:
                print(f"❌ Aucun des actifs demandés n'a été trouvé")
                return {}

            print(f"🎯 {len(available_symbols)} actifs sélectionnés")

        # Collecter les données
        all_data = {}

        print(f"\n🔍 Chargement des données (période: {period})...")
        for name, symbol in available_symbols.items():
            df = self.load_local_csv(symbol, name, max_years)

            if df is not None:
                all_data[name] = df

                # Sauvegarder
                output_file = self.output_dir / f"{name}_historical.csv"
                df.to_csv(output_file, index=False)

        print(f"\n✅ {len(all_data)} actifs collectés avec succès")
        print(f"💾 Données sauvegardées dans: {self.output_dir}")

        return all_data

    def get_available_assets(self) -> List[str]:
        """
        Retourne la liste des actifs disponibles.

        Returns:
            Liste des noms d'actifs
        """
        return list(self._get_available_symbols().keys())


def main():
    """Exemple d'utilisation du collecteur local."""
    collector = LocalDataCollector()

    print("Actifs disponibles:")
    for asset in collector.get_available_assets():
        print(f"  - {asset}")

    # Collecter toutes les données (3 ans)
    data = collector.collect_and_save(period="3y")

    # Afficher un résumé
    print("\nRésumé des données collectées:")
    for name, df in data.items():
        print(f"  {name}: {len(df)} jours, de {df['date'].min().date()} à {df['date'].max().date()}")


if __name__ == "__main__":
    main()
