"""
Corrélateur d'anomalies avec NewsAPI
Version optimisée utilisant NewsAPI au lieu de GDELT
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import sys

# Import du nouveau collecteur NewsAPI
sys.path.insert(0, str(Path(__file__).parent.parent))
from collectors.newsapi_collector import NewsAPICollector


class NewsAPICorrelator:
    """
    Corrélateur d'anomalies utilisant NewsAPI.
    Plus rapide et plus fiable que GDELT.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        window_before: int = 2,
        window_after: int = 1,
        min_relevance_score: float = 20.0,
        output_dir: str = "data/news"
    ):
        """
        Initialise le corrélateur NewsAPI.

        Args:
            api_key: Clé API NewsAPI
            window_before: Jours avant l'anomalie
            window_after: Jours après l'anomalie
            min_relevance_score: Score minimum de pertinence
            output_dir: Répertoire de sauvegarde
        """
        self.window_before = window_before
        self.window_after = window_after
        self.min_relevance_score = min_relevance_score
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialiser le collecteur NewsAPI
        self.collector = NewsAPICollector(api_key=api_key)

    def correlate_anomalies_with_news(
        self,
        anomalies_df: pd.DataFrame,
        delay: float = 0.5,
        max_anomalies: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Corrèle toutes les anomalies avec des news via NewsAPI.

        Args:
            anomalies_df: DataFrame des anomalies détectées
            delay: Délai entre requêtes (secondes)
            max_anomalies: Limite pour tests (None = toutes)

        Returns:
            DataFrame des corrélations
        """
        if anomalies_df.empty:
            print("⚠️  Aucune anomalie à corréler")
            return pd.DataFrame()

        print("\n🔗 Corrélation anomalies-news via NewsAPI...")
        print("="*60)

        # Collecter les news pour toutes les anomalies
        news_df = self.collector.collect_news_for_anomalies(
            anomalies_df=anomalies_df,
            window_before=self.window_before,
            window_after=self.window_after,
            delay=delay,
            max_anomalies=max_anomalies
        )

        if news_df.empty:
            print("⚠️  Aucune news collectée")
            return pd.DataFrame()

        # Calculer les scores de pertinence pour chaque asset
        all_scored = []

        for asset in news_df['asset'].unique():
            asset_news = news_df[news_df['asset'] == asset]
            scored = self.collector.calculate_relevance_score(asset_news, asset)
            all_scored.append(scored)

        result_df = pd.concat(all_scored, ignore_index=True)

        # Filtrer par score minimum
        result_df = result_df[result_df['relevance_score'] >= self.min_relevance_score]

        if result_df.empty:
            print(f"⚠️  Aucune news avec score >= {self.min_relevance_score}")
            return pd.DataFrame()

        # Calculer la distance temporelle
        # Convertir les dates en timezone-naive pour le calcul
        def make_naive(dt_series):
            """Convertit une série de dates en timezone-naive."""
            if pd.api.types.is_datetime64_any_dtype(dt_series):
                # Déjà datetime, vérifier la timezone
                try:
                    return dt_series.dt.tz_localize(None)
                except TypeError:
                    # Déjà naive
                    return dt_series
            else:
                # Convertir en datetime d'abord
                return pd.to_datetime(dt_series, utc=True).dt.tz_localize(None)

        result_df['days_before_anomaly'] = (
            make_naive(result_df['anomaly_date']) - make_naive(result_df['date'])
        ).dt.days

        # Réordonner les colonnes
        result_df = result_df[[
            'anomaly_date', 'asset', 'anomaly_variation', 'anomaly_severity',
            'date', 'title', 'description', 'url', 'source',
            'relevance_score', 'days_before_anomaly', 'query_used'
        ]]

        # Trier par date d'anomalie puis score
        result_df = result_df.sort_values(
            ['anomaly_date', 'relevance_score'],
            ascending=[False, False]
        )

        print("="*60)
        print(f"✅ {len(result_df)} corrélations établies")
        print(f"   Anomalies avec news: {result_df[['asset', 'anomaly_date']].drop_duplicates().shape[0]}")
        print(f"   Score moyen: {result_df['relevance_score'].mean():.1f}")
        print()

        return result_df

    def get_correlation_summary(self, correlations_df: pd.DataFrame) -> Dict:
        """
        Génère un résumé des corrélations.

        Args:
            correlations_df: DataFrame des corrélations

        Returns:
            Dictionnaire avec statistiques
        """
        if correlations_df.empty:
            return {
                'total_correlations': 0,
                'unique_anomalies_with_news': 0,
                'avg_news_per_anomaly': 0,
                'avg_relevance_score': 0,
                'news_by_severity': {},
                'top_sources': {}
            }

        # Compter les anomalies uniques avec news
        anomalies_with_news = correlations_df[['asset', 'anomaly_date']].drop_duplicates()

        # Sources les plus fréquentes
        top_sources = correlations_df['source'].value_counts().head(5).to_dict()

        summary = {
            'total_correlations': len(correlations_df),
            'unique_anomalies_with_news': len(anomalies_with_news),
            'avg_news_per_anomaly': len(correlations_df) / len(anomalies_with_news) if len(anomalies_with_news) > 0 else 0,
            'avg_relevance_score': correlations_df['relevance_score'].mean(),
            'news_by_severity': correlations_df.groupby('anomaly_severity').size().to_dict(),
            'top_sources': top_sources
        }

        return summary

    def display_correlation_summary(self, correlations_df: pd.DataFrame):
        """
        Affiche un résumé des corrélations.

        Args:
            correlations_df: DataFrame des corrélations
        """
        if correlations_df.empty:
            print("⚠️  Aucune corrélation à afficher")
            return

        summary = self.get_correlation_summary(correlations_df)

        print("\n" + "="*60)
        print("📊 RÉSUMÉ DES CORRÉLATIONS (NewsAPI)")
        print("="*60)

        print(f"\n🔗 Total de corrélations: {summary['total_correlations']}")
        print(f"📈 Anomalies avec news: {summary['unique_anomalies_with_news']}")
        print(f"📰 Moyenne news/anomalie: {summary['avg_news_per_anomaly']:.1f}")
        print(f"⭐ Score de pertinence moyen: {summary['avg_relevance_score']:.1f}")

        print(f"\n📊 Corrélations par sévérité:")
        for severity, count in summary['news_by_severity'].items():
            print(f"   {severity}: {count}")

        print(f"\n📰 Top 5 des sources:")
        for i, (source, count) in enumerate(list(summary['top_sources'].items())[:5], 1):
            print(f"   {i}. {source}: {count}")

        print("="*60 + "\n")

    def save_correlations(
        self,
        correlations_df: pd.DataFrame,
        filename: str = "anomalies_with_news_newsapi.csv"
    ) -> str:
        """
        Sauvegarde les corrélations.

        Args:
            correlations_df: DataFrame des corrélations
            filename: Nom du fichier de sortie

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / filename
        correlations_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"💾 Corrélations sauvegardées: {filepath}")
        return str(filepath)

    def export_for_analysis(
        self,
        correlations_df: pd.DataFrame,
        output_file: str = "correlations_analysis_newsapi.csv"
    ) -> str:
        """
        Export simplifié pour analyse externe.

        Args:
            correlations_df: DataFrame des corrélations
            output_file: Nom du fichier de sortie

        Returns:
            Chemin du fichier créé
        """
        if correlations_df.empty:
            return ""

        # Sélectionner les colonnes essentielles
        export_df = correlations_df[[
            'anomaly_date', 'asset', 'anomaly_variation', 'anomaly_severity',
            'date', 'title', 'url', 'source',
            'relevance_score', 'days_before_anomaly'
        ]].copy()

        # Renommer pour clarté
        export_df = export_df.rename(columns={
            'date': 'news_date',
            'title': 'news_title',
            'url': 'news_url',
            'source': 'news_source'
        })

        filepath = self.output_dir / output_file
        export_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"📊 Export d'analyse créé: {filepath}")

        return str(filepath)

    def get_top_news_for_anomaly(
        self,
        correlations_df: pd.DataFrame,
        asset: str,
        anomaly_date: str,
        n: int = 5
    ) -> pd.DataFrame:
        """
        Récupère les top N news pour une anomalie spécifique.

        Args:
            correlations_df: DataFrame des corrélations
            asset: Nom de l'actif
            anomaly_date: Date de l'anomalie
            n: Nombre de news à retourner

        Returns:
            DataFrame des top news
        """
        mask = (
            (correlations_df['asset'] == asset) &
            (correlations_df['anomaly_date'] == pd.to_datetime(anomaly_date))
        )

        top_news = correlations_df[mask].nlargest(n, 'relevance_score')

        return top_news

    def display_top_news_for_critical_anomalies(
        self,
        correlations_df: pd.DataFrame,
        n_anomalies: int = 5,
        n_news_per_anomaly: int = 3
    ):
        """
        Affiche les top news pour les anomalies les plus critiques.

        Args:
            correlations_df: DataFrame des corrélations
            n_anomalies: Nombre d'anomalies à afficher
            n_news_per_anomaly: Nombre de news par anomalie
        """
        if correlations_df.empty:
            return

        print("\n" + "="*60)
        print(f"🔻 TOP {n_anomalies} ANOMALIES CRITIQUES AVEC NEWS")
        print("="*60)

        # Récupérer les anomalies critiques/sévères uniques
        critical_anomalies = correlations_df[
            correlations_df['anomaly_severity'].isin(['Critical', 'Severe'])
        ].drop_duplicates(['asset', 'anomaly_date']).sort_values('anomaly_variation')

        for idx, anomaly in critical_anomalies.head(n_anomalies).iterrows():
            print(f"\n📉 {anomaly['asset']} - {anomaly['anomaly_date'].strftime('%Y-%m-%d')}")
            print(f"   Variation: {anomaly['anomaly_variation']:.2f}% ({anomaly['anomaly_severity']})")

            # Récupérer les top news
            top_news = self.get_top_news_for_anomaly(
                correlations_df,
                anomaly['asset'],
                str(anomaly['anomaly_date']),
                n=n_news_per_anomaly
            )

            print(f"   📰 Top {len(top_news)} news:")
            for _, news in top_news.iterrows():
                print(f"      {news['date'].strftime('%Y-%m-%d')} | Score: {news['relevance_score']:.0f}")
                print(f"      {news['title'][:70]}...")
                print(f"      {news['source']} - {news['url'][:50]}...")

        print("="*60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Corrélation avec NewsAPI")
    parser.add_argument("--anomalies", default="data/anomalies/anomalies_detected.csv")
    parser.add_argument("--window-before", type=int, default=2)
    parser.add_argument("--window-after", type=int, default=1)
    parser.add_argument("--min-score", type=float, default=20.0)
    parser.add_argument("--max-anomalies", type=int, help="Limite pour tests")

    args = parser.parse_args()

    # Charger les anomalies
    anomalies_path = Path(args.anomalies)

    if not anomalies_path.exists():
        print(f"❌ Fichier d'anomalies introuvable: {anomalies_path}")
        print("   Lancez d'abord: python demo_detection.py --step detect")
        exit(1)

    anomalies_df = pd.read_csv(anomalies_path, parse_dates=['date'])
    print(f"📊 {len(anomalies_df)} anomalies chargées")

    # Corréler avec NewsAPI
    correlator = NewsAPICorrelator(
        window_before=args.window_before,
        window_after=args.window_after,
        min_relevance_score=args.min_score
    )

    correlations = correlator.correlate_anomalies_with_news(
        anomalies_df,
        max_anomalies=args.max_anomalies
    )

    if not correlations.empty:
        correlator.save_correlations(correlations)
        correlator.display_correlation_summary(correlations)
        correlator.export_for_analysis(correlations)
        correlator.display_top_news_for_critical_anomalies(correlations)
