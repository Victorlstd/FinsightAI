#!/usr/bin/env python3
"""
Pipeline de détection d'anomalies avec données locales.
Utilise les CSV de PFE_MVP/data/raw au lieu de télécharger via yfinance.

Usage:
    # Pipeline complet avec données locales
    python main_local.py --full --period 3y

    # Actifs spécifiques
    python main_local.py --full --assets APPLE TESLA "SP 500"

    # Avec filtres
    python main_local.py --full --only-critical --min-variation -15

    # Étapes individuelles
    python main_local.py --step historical --period 1y
    python main_local.py --step detect
    python main_local.py --step correlate --max-anomalies 10
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le chemin du module
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.local_data_collector import LocalDataCollector
from src.detectors.anomaly_detector import AnomalyDetector
from src.correlators.newsapi_correlator import NewsAPICorrelator
from src.reporters.anomaly_report_generator import AnomalyReportGenerator
import pandas as pd


class AnomalyDetectionPipelineLocal:
    """Pipeline de détection d'anomalies avec données locales."""

    def __init__(
        self,
        period: str = "3y",
        threshold_1day: float = -3.0,
        threshold_5day: float = -5.0,
        threshold_30day: float = -10.0,
        window_before: int = 2,
        window_after: int = 1,
        min_relevance: float = 20.0,
        newsapi_key: str = None,
        input_dir: str = None
    ):
        """
        Initialise le pipeline avec données locales.

        Args:
            period: Période de données (1y, 3y, 5y, 10y, max)
            threshold_*: Seuils de détection d'anomalies
            window_before/after: Fenêtre de recherche news
            min_relevance: Score minimum NewsAPI
            newsapi_key: Clé API NewsAPI
            input_dir: Répertoire source des CSV (défaut: PFE_MVP/data/raw)
        """
        self.period = period
        self.threshold_1day = threshold_1day
        self.threshold_5day = threshold_5day
        self.threshold_30day = threshold_30day
        self.window_before = window_before
        self.window_after = window_after
        self.min_relevance = min_relevance

        # Utiliser le collector local au lieu de yfinance
        self.collector = LocalDataCollector(input_dir=input_dir)

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
        """Étape 1: Collecte des données historiques depuis les CSV locaux."""
        print("\n" + "="*70)
        print("ÉTAPE 1/3: CHARGEMENT DES DONNÉES LOCALES")
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

            # Charger depuis les fichiers sauvegardés
            historical_dir = Path("data/historical")
            if not historical_dir.exists():
                print("❌ Aucune donnée historique trouvée. Exécutez d'abord l'étape 1.")
                return False

            for csv_file in historical_dir.glob("*_historical.csv"):
                asset_name = csv_file.stem.replace("_historical", "")
                self.historical_data[asset_name] = pd.read_csv(csv_file)

        if not self.historical_data:
            print("❌ Aucune donnée à analyser")
            return False

        self.anomalies = self.detector.detect_all_anomalies(self.historical_data)

        if self.anomalies is None or len(self.anomalies) == 0:
            print("✅ Aucune anomalie détectée")
            return False

        # Afficher statistiques
        print(f"\n📊 Statistiques des anomalies détectées:")
        severity_counts = self.anomalies['severity'].value_counts()
        for severity, count in severity_counts.items():
            print(f"  - {severity}: {count}")

        print(f"\n✅ Total: {len(self.anomalies)} anomalies détectées")
        return True

    def step_3_correlate_with_news(
        self,
        max_anomalies: int = None,
        only_critical: bool = False,
        min_variation: float = None
    ):
        """Étape 3: Corrélation avec les actualités."""
        print("\n" + "="*70)
        print("ÉTAPE 3/3: CORRÉLATION AVEC LES ACTUALITÉS")
        print("="*70)

        if self.anomalies is None:
            print("⚠️  Chargement des anomalies...")
            anomalies_file = Path("data/anomalies/anomalies_detected.csv")
            if not anomalies_file.exists():
                print("❌ Aucune anomalie détectée. Exécutez d'abord l'étape 2.")
                return False
            self.anomalies = pd.read_csv(anomalies_file)

        # Filtrer les anomalies selon les critères
        filtered_anomalies = self.anomalies.copy()

        if only_critical:
            filtered_anomalies = filtered_anomalies[
                filtered_anomalies['severity'] == 'Critical'
            ]
            print(f"🎯 Filtrage: anomalies critiques uniquement")

        if min_variation is not None:
            filtered_anomalies = filtered_anomalies[
                filtered_anomalies['variation_pct'] <= min_variation
            ]
            print(f"🎯 Filtrage: variation <= {min_variation}%")

        if len(filtered_anomalies) == 0:
            print("⚠️  Aucune anomalie ne correspond aux filtres")
            return False

        print(f"📊 {len(filtered_anomalies)} anomalies après filtrage")

        # Limiter le nombre d'anomalies (pour tests NewsAPI)
        if max_anomalies and len(filtered_anomalies) > max_anomalies:
            print(f"⚠️  Limitation à {max_anomalies} anomalies (pour économiser l'API)")
            filtered_anomalies = filtered_anomalies.head(max_anomalies)

        # Corrélation avec NewsAPI
        self.correlations = self.correlator.correlate_anomalies_with_news(
            filtered_anomalies,
            max_anomalies=max_anomalies
        )

        if self.correlations is None or len(self.correlations) == 0:
            print("⚠️  Aucune corrélation trouvée")
            return False

        # Générer les rapports
        print("\n📝 Génération des rapports...")
        reporter = AnomalyReportGenerator()
        md_path, html_path = reporter.generate_both_reports(
            self.correlations,
            self.anomalies
        )

        print(f"\n✅ Rapports générés:")
        print(f"  - Markdown: {md_path}")
        print(f"  - HTML: {html_path}")

        # Afficher les top news pour les anomalies critiques
        critical_anomalies = filtered_anomalies[
            filtered_anomalies['severity'] == 'Critical'
        ]

        if len(critical_anomalies) > 0:
            print("\n" + "="*70)
            print("TOP NEWS POUR LES ANOMALIES CRITIQUES")
            print("="*70)
            self.correlator.display_top_news_for_critical_anomalies(
                self.correlations,
                critical_anomalies
            )

        return True

    def run_full_pipeline(
        self,
        assets: list = None,
        max_anomalies: int = None,
        only_critical: bool = False,
        min_variation: float = None
    ):
        """Exécute la pipeline complète."""
        print("\n" + "="*70)
        print("PIPELINE DE DÉTECTION D'ANOMALIES (DONNÉES LOCALES)")
        print("="*70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Période: {self.period}")
        print(f"🎯 Seuils: 1j={self.threshold_1day}%, 5j={self.threshold_5day}%, 30j={self.threshold_30day}%")
        print(f"📰 Fenêtre news: -{self.window_before}j à +{self.window_after}j")
        print(f"⭐ Score minimum: {self.min_relevance}")

        if assets:
            print(f"📌 Actifs: {', '.join(assets)}")

        # Étape 1: Collecte
        if not self.step_1_collect_historical_data(assets):
            print("\n❌ Échec de la collecte des données")
            return False

        # Étape 2: Détection
        if not self.step_2_detect_anomalies():
            print("\n⚠️  Pipeline arrêtée (pas d'anomalies)")
            return True

        # Étape 3: Corrélation
        success = self.step_3_correlate_with_news(
            max_anomalies=max_anomalies,
            only_critical=only_critical,
            min_variation=min_variation
        )

        print("\n" + "="*70)
        if success:
            print("✅ PIPELINE TERMINÉE AVEC SUCCÈS")
        else:
            print("⚠️  PIPELINE TERMINÉE (sans corrélations)")
        print("="*70)

        # Générer le fichier JSON pour le dashboard
        print("\n📊 Génération du fichier JSON pour le dashboard...")
        try:
            import subprocess
            result = subprocess.run(
                ["python", "generate_anomalies_data.py"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Fichier JSON généré pour le dashboard")
            else:
                print(f"⚠️  Erreur génération JSON: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Erreur génération JSON: {e}")

        return success


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Pipeline de détection d'anomalies avec données locales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Pipeline complet
  python main_local.py --full --period 3y

  # Avec filtres
  python main_local.py --full --only-critical --max-anomalies 10

  # Actifs spécifiques
  python main_local.py --full --assets APPLE TESLA

  # Étapes individuelles
  python main_local.py --step historical --period 1y
  python main_local.py --step detect
  python main_local.py --step correlate
        """
    )

    # Mode d'exécution
    parser.add_argument(
        '--full',
        action='store_true',
        help='Exécuter la pipeline complète'
    )
    parser.add_argument(
        '--step',
        choices=['historical', 'detect', 'correlate'],
        help='Exécuter une étape spécifique'
    )

    # Paramètres de collecte
    parser.add_argument(
        '--period',
        type=str,
        default='3y',
        choices=['1y', '3y', '5y', '10y', 'max'],
        help='Période de données (défaut: 3y)'
    )
    parser.add_argument(
        '--assets',
        nargs='+',
        help='Liste d\'actifs spécifiques à analyser'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Répertoire source des CSV (défaut: PFE_MVP/data/raw)'
    )

    # Paramètres de détection
    parser.add_argument(
        '--threshold-1d',
        type=float,
        default=-3.0,
        help='Seuil variation 1 jour en %% (défaut: -3.0)'
    )
    parser.add_argument(
        '--threshold-5d',
        type=float,
        default=-5.0,
        help='Seuil variation 5 jours en %% (défaut: -5.0)'
    )
    parser.add_argument(
        '--threshold-30d',
        type=float,
        default=-10.0,
        help='Seuil variation 30 jours en %% (défaut: -10.0)'
    )

    # Paramètres de corrélation
    parser.add_argument(
        '--window-before',
        type=int,
        default=2,
        help='Jours avant anomalie pour chercher news (défaut: 2)'
    )
    parser.add_argument(
        '--window-after',
        type=int,
        default=1,
        help='Jours après anomalie pour chercher news (défaut: 1)'
    )
    parser.add_argument(
        '--min-relevance',
        type=float,
        default=20.0,
        help='Score minimum de pertinence (0-100, défaut: 20.0)'
    )
    parser.add_argument(
        '--max-anomalies',
        type=int,
        help='Nombre max d\'anomalies à corréler (pour tests)'
    )

    # Filtres
    parser.add_argument(
        '--only-critical',
        action='store_true',
        help='Analyser uniquement les anomalies critiques'
    )
    parser.add_argument(
        '--min-variation',
        type=float,
        help='Variation minimale en %% (ex: -15 pour >= -15%%)'
    )

    args = parser.parse_args()

    # Vérifier les arguments
    if not args.full and not args.step:
        parser.print_help()
        sys.exit(1)

    # Récupérer la clé NewsAPI
    newsapi_key = os.getenv('NEWSAPI_KEY')
    if not newsapi_key:
        print("⚠️  NEWSAPI_KEY non trouvée dans .env")
        print("    La corrélation avec les actualités sera désactivée")

    # Créer la pipeline
    pipeline = AnomalyDetectionPipelineLocal(
        period=args.period,
        threshold_1day=args.threshold_1d,
        threshold_5day=args.threshold_5d,
        threshold_30day=args.threshold_30d,
        window_before=args.window_before,
        window_after=args.window_after,
        min_relevance=args.min_relevance,
        newsapi_key=newsapi_key,
        input_dir=args.input_dir
    )

    # Exécuter selon le mode
    if args.full:
        pipeline.run_full_pipeline(
            assets=args.assets,
            max_anomalies=args.max_anomalies,
            only_critical=args.only_critical,
            min_variation=args.min_variation
        )
    elif args.step == 'historical':
        pipeline.step_1_collect_historical_data(args.assets)
    elif args.step == 'detect':
        pipeline.step_2_detect_anomalies()
    elif args.step == 'correlate':
        pipeline.step_3_correlate_with_news(
            max_anomalies=args.max_anomalies,
            only_critical=args.only_critical,
            min_variation=args.min_variation
        )


if __name__ == "__main__":
    main()
