#!/usr/bin/env python3
"""
Script de démonstration avec NewsAPI (version optimisée).

Usage:
    # Pipeline complet avec NewsAPI
    python demo_detection_newsapi.py --full --period 1y

    # Étapes individuelles
    python demo_detection_newsapi.py --step historical --period 1y
    python demo_detection_newsapi.py --step detect
    python demo_detection_newsapi.py --step correlate
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le chemin du module
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.historical_data_collector import HistoricalDataCollector
from src.detectors.anomaly_detector import AnomalyDetector
from src.correlators.newsapi_correlator import NewsAPICorrelator
from src.reporters.anomaly_report_generator import AnomalyReportGenerator
import pandas as pd


class AnomalyDetectionPipelineNewsAPI:
    """Pipeline de détection d'anomalies avec NewsAPI."""

    def __init__(
        self,
        period: str = "3y",
        threshold_1day: float = -3.0,
        threshold_5day: float = -5.0,
        threshold_30day: float = -10.0,
        window_before: int = 2,
        window_after: int = 1,
        min_relevance: float = 20.0,
        newsapi_key: str = None
    ):
        """
        Initialise le pipeline avec NewsAPI.

        Args:
            period: Période de données historiques
            threshold_*: Seuils de détection
            window_before/after: Fenêtre de recherche news
            min_relevance: Score minimum NewsAPI
            newsapi_key: Clé API NewsAPI
        """
        self.period = period
        self.threshold_1day = threshold_1day
        self.threshold_5day = threshold_5day
        self.threshold_30day = threshold_30day
        self.window_before = window_before
        self.window_after = window_after
        self.min_relevance = min_relevance

        self.collector = HistoricalDataCollector()
        self.detector = AnomalyDetector(
            threshold_1day=threshold_1day,
            threshold_5day=threshold_5day,
            threshold_30day=threshold_30day
        )
        self.correlator = NewsAPICorrelator(
            api_key=newsapi_key,
            window_before=window_before,
            window_after=window_after,
            min_relevance_score=min_relevance
        )

        self.historical_data = None
        self.anomalies = None
        self.correlations = None

    def step_1_collect_historical_data(self, assets: list = None):
        """Étape 1: Collecte des données historiques."""
        print("\n" + "="*70)
        print("ÉTAPE 1/3: COLLECTE DES DONNÉES HISTORIQUES")
        print("="*70)

        self.historical_data = self.collector.collect_and_save(
            period=self.period,
            symbols_to_fetch=assets
        )

        return bool(self.historical_data)

    def step_2_detect_anomalies(self):
        """Étape 2: Détection des anomalies."""
        print("\n" + "="*70)
        print("ÉTAPE 2/3: DÉTECTION DES ANOMALIES")
        print("="*70)

        if self.historical_data is None:
            print("⚠️  Chargement des données historiques...")
            self.historical_data = {}
            data_dir = Path(__file__).parent / "data/historical"

            for csv_file in data_dir.glob("*_historical.csv"):
                asset_name = csv_file.stem.replace("_historical", "")
                df = pd.read_csv(csv_file, parse_dates=['date'])
                self.historical_data[asset_name] = df

            if not self.historical_data:
                print("❌ Aucune donnée historique trouvée")
                return False

        self.anomalies = self.detector.detect_all_anomalies(self.historical_data)

        if self.anomalies.empty:
            print("⚠️  Aucune anomalie détectée")
            return False

        self.detector.save_anomalies(self.anomalies)
        self.detector.display_summary(self.anomalies)

        # Top 10
        print("🔻 TOP 10 DES ANOMALIES LES PLUS SÉVÈRES")
        print("="*70)
        top10 = self.detector.get_top_anomalies(self.anomalies, n=10)
        print(top10[['date', 'asset', 'variation_pct', 'severity', 'window']].to_string(index=False))
        print("="*70 + "\n")

        return True

    def step_3_correlate_with_news(
        self,
        max_anomalies: int = None,
        only_critical: bool = False,
        min_variation: float = None
    ):
        """Étape 3: Corrélation avec NewsAPI."""
        print("\n" + "="*70)
        print("ÉTAPE 3/3: CORRÉLATION AVEC NEWSAPI")
        print("="*70)

        if self.anomalies is None:
            print("⚠️  Chargement des anomalies...")
            anomalies_path = Path(__file__).parent / "data/anomalies/anomalies_detected.csv"

            if not anomalies_path.exists():
                print("❌ Aucune anomalie trouvée")
                return False

            self.anomalies = pd.read_csv(anomalies_path, parse_dates=['date'])

        # Appliquer les filtres
        filtered_anomalies = self.anomalies.copy()

        if only_critical:
            print("🎯 Filtre: Anomalies Critical uniquement")
            filtered_anomalies = filtered_anomalies[filtered_anomalies['severity'] == 'Critical']
            print(f"   {len(filtered_anomalies)} anomalies Critical trouvées")

        if min_variation is not None:
            print(f"🎯 Filtre: Variation <= {min_variation}%")
            filtered_anomalies = filtered_anomalies[filtered_anomalies['variation_pct'] <= min_variation]
            print(f"   {len(filtered_anomalies)} anomalies avec variation >= {abs(min_variation)}%")

        if filtered_anomalies.empty:
            print("❌ Aucune anomalie ne correspond aux filtres")
            return False

        # Info sur rate limiting
        print("\n⚠️  Note: NewsAPI limite gratuite = 100 requêtes/jour")
        if max_anomalies:
            print(f"   Limité aux {max_anomalies} premières anomalies")
        else:
            n_anomalies = len(filtered_anomalies)
            print(f"   {n_anomalies} anomalies à traiter")
            if n_anomalies > 50:
                print(f"   ⚠️  Cela fera {n_anomalies} requêtes!")
                print(f"   Utilisez --max-anomalies 20 pour limiter")

        self.correlations = self.correlator.correlate_anomalies_with_news(
            filtered_anomalies,
            max_anomalies=max_anomalies
        )

        if self.correlations.empty:
            print("⚠️  Aucune corrélation établie")
            return False

        self.correlator.save_correlations(self.correlations)
        self.correlator.display_correlation_summary(self.correlations)

        # Afficher les top news pour anomalies critiques
        self.correlator.display_top_news_for_critical_anomalies(
            self.correlations,
            n_anomalies=5,
            n_news_per_anomaly=3
        )

        # Export
        self.correlator.export_for_analysis(self.correlations)

        # Générer les rapports visuels
        print("\n📝 Génération des rapports visuels...")
        reporter = AnomalyReportGenerator()
        md_path, html_path = reporter.generate_both_reports(self.correlations, self.anomalies)

        print(f"\n💡 Ouvrir le rapport: open {html_path}")

        return True

    def run_full_pipeline(
        self,
        assets: list = None,
        max_anomalies: int = None,
        only_critical: bool = False,
        min_variation: float = None
    ):
        """Exécute le pipeline complet."""
        print("\n" + "🚀 " * 35)
        print("PIPELINE AVEC NEWSAPI - DÉTECTION & CORRÉLATION")
        print("🚀 " * 35)

        start_time = datetime.now()

        # Étape 1
        if not self.step_1_collect_historical_data(assets):
            return

        # Étape 2
        if not self.step_2_detect_anomalies():
            return

        # Étape 3
        self.step_3_correlate_with_news(
            max_anomalies=max_anomalies,
            only_critical=only_critical,
            min_variation=min_variation
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "✅ " * 35)
        print(f"PIPELINE TERMINÉ EN {duration:.1f}s")
        print("✅ " * 35 + "\n")

        self._print_final_summary()

    def _print_final_summary(self):
        """Résumé final."""
        print("\n" + "="*70)
        print("📊 RÉSUMÉ FINAL")
        print("="*70)

        if self.historical_data:
            print(f"\n📈 Données historiques: {len(self.historical_data)} actifs")

        if self.anomalies is not None:
            print(f"🔍 Anomalies détectées: {len(self.anomalies)}")

            if not self.anomalies.empty:
                severity_counts = self.anomalies['severity'].value_counts()
                print("\n   Par sévérité:")
                for severity, count in severity_counts.items():
                    print(f"   • {severity}: {count}")

        if self.correlations is not None and not self.correlations.empty:
            unique_anomalies_with_news = len(
                self.correlations[['asset', 'anomaly_date']].drop_duplicates()
            )
            print(f"\n📰 Corrélations établies (NewsAPI): {len(self.correlations)}")
            print(f"   Anomalies avec news: {unique_anomalies_with_news}")
            print(f"   Score moyen: {self.correlations['relevance_score'].mean():.1f}")

        print("\n📁 Fichiers générés:")
        print("   • data/historical/*.csv")
        print("   • data/anomalies/anomalies_detected.csv")
        print("   • data/news/anomalies_with_news_newsapi.csv")
        print("   • data/news/correlations_analysis_newsapi.csv")

        if self.correlations is not None and not self.correlations.empty:
            print("   • reports/anomaly_report.html  📊")
            print("   • reports/anomaly_report.md")

        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Détection d'anomalies avec NewsAPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:

  # Pipeline complet (limité à 10 anomalies pour économiser les requêtes)
  python main.py --full --period 1y --max-anomalies 10

  # Analyser uniquement les gros crashs (comme COVID)
  python main.py --full --period 5y --only-critical --max-anomalies 20
  python main.py --full --period 5y --min-variation -15 --max-anomalies 15

  # Étape par étape
  python main.py --step historical --period 1y
  python main.py --step detect
  python main.py --step correlate --max-anomalies 20

  # Cibler les crashs critiques sur longue période
  python main.py --step correlate --only-critical --max-anomalies 15

  # Avec plusieurs actifs
  python main.py --full --assets APPLE TESLA "SP 500"
        """
    )

    # Mode
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--step", choices=["historical", "detect", "correlate"])

    # Paramètres collecte
    parser.add_argument("--period", default="3y")
    parser.add_argument("--assets", nargs="+")

    # Paramètres détection
    parser.add_argument("--threshold-1d", type=float, default=-3.0)
    parser.add_argument("--threshold-5d", type=float, default=-5.0)
    parser.add_argument("--threshold-30d", type=float, default=-10.0)

    # Paramètres corrélation NewsAPI
    parser.add_argument("--window-before", type=int, default=2)
    parser.add_argument("--window-after", type=int, default=1)
    parser.add_argument("--min-relevance", type=float, default=20.0)
    parser.add_argument("--max-anomalies", type=int,
                        help="Limiter le nombre d'anomalies (économise requêtes NewsAPI)")
    parser.add_argument("--newsapi-key", help="Clé NewsAPI (ou NEWSAPI_KEY dans .env)")

    # Filtres pour cibler les gros crashs
    parser.add_argument("--only-critical", action="store_true",
                        help="Ne garder que les anomalies Critical (ex: COVID)")
    parser.add_argument("--min-variation", type=float,
                        help="Variation minimale en %% (ex: -15 pour très gros crashs)")

    args = parser.parse_args()

    if not args.full and not args.step:
        parser.print_help()
        print("\n❌ Erreur: Spécifiez --full ou --step")
        sys.exit(1)

    # Initialiser
    pipeline = AnomalyDetectionPipelineNewsAPI(
        period=args.period,
        threshold_1day=args.threshold_1d,
        threshold_5day=args.threshold_5d,
        threshold_30day=args.threshold_30d,
        window_before=args.window_before,
        window_after=args.window_after,
        min_relevance=args.min_relevance,
        newsapi_key=args.newsapi_key
    )

    # Exécuter
    if args.full:
        pipeline.run_full_pipeline(
            assets=args.assets,
            max_anomalies=args.max_anomalies,
            only_critical=args.only_critical,
            min_variation=args.min_variation
        )
    else:
        if args.step == "historical":
            pipeline.step_1_collect_historical_data(assets=args.assets)
        elif args.step == "detect":
            pipeline.step_2_detect_anomalies()
        elif args.step == "correlate":
            pipeline.step_3_correlate_with_news(
                max_anomalies=args.max_anomalies,
                only_critical=args.only_critical,
                min_variation=args.min_variation
            )


if __name__ == "__main__":
    main()
