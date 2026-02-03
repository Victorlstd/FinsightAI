import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum


class AnomalySeverity(Enum):
    """Niveaux de sévérité des anomalies"""
    MINOR = "Minor"           # -3% à -5%
    MODERATE = "Moderate"     # -5% à -8%
    SEVERE = "Severe"         # -8% à -15%
    CRITICAL = "Critical"     # > -15%


class AnomalyDetector:
    """
    Détecteur d'anomalies basé sur des seuils statistiques.
    Identifie les baisses significatives de prix sur différentes fenêtres temporelles.
    """

    def __init__(
        self,
        threshold_1day: float = -3.0,
        threshold_5day: float = -5.0,
        threshold_30day: float = -10.0,
        output_dir: str = "data/anomalies"
    ):
        """
        Initialise le détecteur.

        Args:
            threshold_1day: Seuil de baisse sur 1 jour (%)
            threshold_5day: Seuil de baisse sur 5 jours (%)
            threshold_30day: Seuil de baisse sur 30 jours (%)
            output_dir: Répertoire de sauvegarde
        """
        self.threshold_1day = threshold_1day
        self.threshold_5day = threshold_5day
        self.threshold_30day = threshold_30day
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _determine_severity(self, variation_pct: float) -> AnomalySeverity:
        """
        Détermine la sévérité d'une anomalie.

        Args:
            variation_pct: Variation en pourcentage (négative)

        Returns:
            Niveau de sévérité
        """
        if variation_pct >= -5.0:
            return AnomalySeverity.MINOR
        elif variation_pct >= -8.0:
            return AnomalySeverity.MODERATE
        elif variation_pct >= -15.0:
            return AnomalySeverity.SEVERE
        else:
            return AnomalySeverity.CRITICAL

    def detect_anomalies_single_asset(
        self,
        df: pd.DataFrame,
        asset_name: str
    ) -> pd.DataFrame:
        """
        Détecte les anomalies pour un seul actif.

        Args:
            df: DataFrame avec colonnes date, close, daily_return, return_5d, return_30d
            asset_name: Nom de l'actif

        Returns:
            DataFrame des anomalies détectées
        """
        anomalies = []

        for idx, row in df.iterrows():
            # Vérifier les différentes fenêtres temporelles
            detected = False
            window_type = None
            variation_pct = None

            # Anomalie sur 1 jour
            if pd.notna(row['daily_return']) and row['daily_return'] <= self.threshold_1day:
                detected = True
                window_type = "1day"
                variation_pct = row['daily_return']

            # Anomalie sur 5 jours (plus prioritaire si plus sévère)
            elif pd.notna(row['return_5d']) and row['return_5d'] <= self.threshold_5day:
                detected = True
                window_type = "5day"
                variation_pct = row['return_5d']

            # Anomalie sur 30 jours
            elif pd.notna(row['return_30d']) and row['return_30d'] <= self.threshold_30day:
                detected = True
                window_type = "30day"
                variation_pct = row['return_30d']

            if detected:
                severity = self._determine_severity(variation_pct)

                anomaly = {
                    'date': row['date'],
                    'asset': asset_name,
                    'symbol': row['symbol'],
                    'close_price': row['close'],
                    'window': window_type,
                    'variation_pct': round(variation_pct, 2),
                    'severity': severity.value,
                    'severity_level': severity.name
                }

                anomalies.append(anomaly)

        return pd.DataFrame(anomalies)

    def detect_all_anomalies(
        self,
        historical_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Détecte les anomalies pour tous les actifs.

        Args:
            historical_data: Dictionnaire {nom_actif: DataFrame}

        Returns:
            DataFrame consolidé de toutes les anomalies
        """
        print("\n🔍 Détection des anomalies...")
        print("="*60)
        print(f"  Seuils: 1j={self.threshold_1day}% | 5j={self.threshold_5day}% | 30j={self.threshold_30day}%")
        print("="*60)

        all_anomalies = []

        for asset_name, df in historical_data.items():
            print(f"  Analyse de {asset_name}...", end=" ")

            anomalies_df = self.detect_anomalies_single_asset(df, asset_name)

            if not anomalies_df.empty:
                all_anomalies.append(anomalies_df)
                print(f"✓ {len(anomalies_df)} anomalie(s)")
            else:
                print("✓ Aucune anomalie")

        if not all_anomalies:
            print("\n⚠️  Aucune anomalie détectée sur l'ensemble des actifs\n")
            return pd.DataFrame()

        # Concaténer toutes les anomalies
        result_df = pd.concat(all_anomalies, ignore_index=True)

        # Trier par date (plus récent en premier)
        result_df = result_df.sort_values('date', ascending=False)

        print("="*60)
        print(f"✅ {len(result_df)} anomalies détectées au total\n")

        return result_df

    def filter_anomalies(
        self,
        anomalies_df: pd.DataFrame,
        min_severity: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        assets: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Filtre les anomalies selon plusieurs critères.

        Args:
            anomalies_df: DataFrame des anomalies
            min_severity: Sévérité minimale (MINOR, MODERATE, SEVERE, CRITICAL)
            date_from: Date de début (YYYY-MM-DD)
            date_to: Date de fin (YYYY-MM-DD)
            assets: Liste de noms d'actifs

        Returns:
            DataFrame filtré
        """
        filtered_df = anomalies_df.copy()

        # Filtre par sévérité
        if min_severity:
            severity_order = ['MINOR', 'MODERATE', 'SEVERE', 'CRITICAL']
            if min_severity.upper() in severity_order:
                min_idx = severity_order.index(min_severity.upper())
                allowed_severities = severity_order[min_idx:]
                filtered_df = filtered_df[
                    filtered_df['severity_level'].isin(allowed_severities)
                ]

        # Filtre par date
        if date_from:
            date_from_dt = pd.to_datetime(date_from)
            filtered_df = filtered_df[filtered_df['date'] >= date_from_dt]

        if date_to:
            date_to_dt = pd.to_datetime(date_to)
            filtered_df = filtered_df[filtered_df['date'] <= date_to_dt]

        # Filtre par actifs
        if assets:
            filtered_df = filtered_df[filtered_df['asset'].isin(assets)]

        return filtered_df

    def get_anomalies_summary(self, anomalies_df: pd.DataFrame) -> Dict:
        """
        Génère un résumé statistique des anomalies détectées.

        Args:
            anomalies_df: DataFrame des anomalies

        Returns:
            Dictionnaire avec statistiques
        """
        if anomalies_df.empty:
            return {
                'total_anomalies': 0,
                'by_severity': {},
                'by_asset': {},
                'by_window': {},
                'avg_variation': 0,
                'worst_anomaly': None
            }

        summary = {
            'total_anomalies': len(anomalies_df),
            'by_severity': anomalies_df['severity'].value_counts().to_dict(),
            'by_asset': anomalies_df['asset'].value_counts().to_dict(),
            'by_window': anomalies_df['window'].value_counts().to_dict(),
            'avg_variation': anomalies_df['variation_pct'].mean(),
            'worst_anomaly': anomalies_df.loc[anomalies_df['variation_pct'].idxmin()].to_dict()
        }

        return summary

    def save_anomalies(
        self,
        anomalies_df: pd.DataFrame,
        filename: str = "anomalies_detected.csv"
    ) -> str:
        """
        Sauvegarde les anomalies détectées.

        Args:
            anomalies_df: DataFrame des anomalies
            filename: Nom du fichier de sortie

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / filename
        anomalies_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"💾 Anomalies sauvegardées: {filepath}\n")
        return str(filepath)

    def display_summary(self, anomalies_df: pd.DataFrame):
        """
        Affiche un résumé visuel des anomalies.

        Args:
            anomalies_df: DataFrame des anomalies
        """
        if anomalies_df.empty:
            print("⚠️  Aucune anomalie à afficher\n")
            return

        summary = self.get_anomalies_summary(anomalies_df)

        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES ANOMALIES DÉTECTÉES")
        print("="*60)

        print(f"\n🔢 Total: {summary['total_anomalies']} anomalies")

        print(f"\n⚠️  Par sévérité:")
        for severity, count in sorted(summary['by_severity'].items()):
            print(f"   {severity}: {count}")

        print(f"\n📈 Par actif (Top 10):")
        for asset, count in list(summary['by_asset'].items())[:10]:
            print(f"   {asset}: {count}")

        print(f"\n📅 Par fenêtre temporelle:")
        for window, count in summary['by_window'].items():
            print(f"   {window}: {count}")

        print(f"\n📉 Variation moyenne: {summary['avg_variation']:.2f}%")

        worst = summary['worst_anomaly']
        print(f"\n🔻 Pire anomalie:")
        print(f"   Date: {worst['date']}")
        print(f"   Actif: {worst['asset']}")
        print(f"   Variation: {worst['variation_pct']}%")
        print(f"   Sévérité: {worst['severity']}")

        print("="*60 + "\n")

    def get_top_anomalies(
        self,
        anomalies_df: pd.DataFrame,
        n: int = 10,
        by: str = "severity"
    ) -> pd.DataFrame:
        """
        Récupère les N pires anomalies.

        Args:
            anomalies_df: DataFrame des anomalies
            n: Nombre d'anomalies à retourner
            by: Critère de tri ("severity" ou "variation")

        Returns:
            DataFrame des top anomalies
        """
        if by == "severity":
            # Trier par sévérité puis par variation
            severity_order = ['CRITICAL', 'SEVERE', 'MODERATE', 'MINOR']
            anomalies_df['severity_rank'] = anomalies_df['severity_level'].map(
                {s: i for i, s in enumerate(severity_order)}
            )
            top_df = anomalies_df.sort_values(
                ['severity_rank', 'variation_pct']
            ).head(n)
            top_df = top_df.drop('severity_rank', axis=1)
        else:
            # Trier par variation (la plus négative)
            top_df = anomalies_df.nsmallest(n, 'variation_pct')

        return top_df


if __name__ == "__main__":
    import argparse
    from ..collectors.historical_data_collector import HistoricalDataCollector

    parser = argparse.ArgumentParser(description="Détection d'anomalies")
    parser.add_argument("--threshold-1d", type=float, default=-3.0)
    parser.add_argument("--threshold-5d", type=float, default=-5.0)
    parser.add_argument("--threshold-30d", type=float, default=-10.0)
    parser.add_argument("--period", default="3y", help="Période de données")

    args = parser.parse_args()

    # Collecter les données historiques
    print("📊 Collecte des données historiques...")
    collector = HistoricalDataCollector()
    historical_data = collector.collect_and_save(period=args.period)

    # Détecter les anomalies
    detector = AnomalyDetector(
        threshold_1day=args.threshold_1d,
        threshold_5day=args.threshold_5d,
        threshold_30day=args.threshold_30d
    )

    anomalies = detector.detect_all_anomalies(historical_data)

    if not anomalies.empty:
        detector.save_anomalies(anomalies)
        detector.display_summary(anomalies)

        # Afficher les 10 pires anomalies
        print("🔻 TOP 10 DES PIRES ANOMALIES")
        print("="*60)
        top10 = detector.get_top_anomalies(anomalies, n=10)
        print(top10[['date', 'asset', 'variation_pct', 'severity']].to_string(index=False))
        print("="*60)
