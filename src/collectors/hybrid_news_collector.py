"""
Collecteur de news hybride: événements macro + sectoriels
Collecte les news qui peuvent impacter les actifs sans les mentionner directement
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import requests
from loguru import logger
import time
from .news_impact_mapper import NewsImpactMapper


class HybridNewsCollector:
    """
    Collecteur de news basé sur l'approche hybride:
    1. Événements macro-économiques et géopolitiques
    2. Événements sectoriels ciblés
    3. Mapping intelligent vers les actifs impactés
    """

    def __init__(
        self,
        output_dir: str = "data/raw/news",
        config_path: str = "config/news_strategy.yaml"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        self.mapper = NewsImpactMapper(config_path)

        # Statistiques
        self.stats = {
            'total_fetched': 0,
            'macro_events': 0,
            'sector_events': 0,
            'duplicates_removed': 0
        }

    def fetch_macro_news(
        self,
        start_date: str,
        end_date: str,
        max_records_per_query: int = 250,
        delay: float = 2.0
    ) -> pd.DataFrame:
        """
        Collecte les news sur les événements macro-économiques

        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin
            max_records_per_query: Nombre max d'articles par requête
            delay: Délai entre requêtes (secondes)

        Returns:
            DataFrame avec les news macro
        """
        logger.info("\n" + "="*80)
        logger.info("📰 COLLECTE DES ÉVÉNEMENTS MACRO")
        logger.info("="*80)

        all_news = []
        macro_queries = self.mapper.get_macro_event_queries()

        logger.info(f"Nombre de requêtes macro: {len(macro_queries)}")

        for i, query_info in enumerate(macro_queries, 1):
            logger.info(f"[{i}/{len(macro_queries)}] {query_info['event_type']}")

            df = self._fetch_gdelt_news(
                query=query_info['query'],
                start_date=start_date,
                end_date=end_date,
                max_records=max_records_per_query
            )

            if not df.empty:
                # Enrichir avec les métadonnées de l'événement
                df['event_type'] = query_info['event_type']
                df['event_category'] = 'macro'
                df['base_impact_score'] = query_info['impact_score']
                all_news.append(df)
                self.stats['macro_events'] += len(df)
                logger.success(f"  ✓ {len(df)} articles collectés")

            time.sleep(delay)

        if all_news:
            combined = pd.concat(all_news, ignore_index=True)
            logger.success(f"\n✓ Total événements macro: {len(combined)} articles")
            return combined
        else:
            logger.warning("Aucune news macro collectée")
            return pd.DataFrame()

    def fetch_sector_news(
        self,
        start_date: str,
        end_date: str,
        max_records_per_query: int = 250,
        delay: float = 2.0
    ) -> pd.DataFrame:
        """
        Collecte les news sur les événements sectoriels

        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin
            max_records_per_query: Nombre max d'articles par requête
            delay: Délai entre requêtes (secondes)

        Returns:
            DataFrame avec les news sectorielles
        """
        logger.info("\n" + "="*80)
        logger.info("🏭 COLLECTE DES ÉVÉNEMENTS SECTORIELS")
        logger.info("="*80)

        all_news = []
        sector_queries = self.mapper.get_sector_event_queries()

        logger.info(f"Nombre de requêtes sectorielles: {len(sector_queries)}")

        for i, query_info in enumerate(sector_queries, 1):
            logger.info(f"[{i}/{len(sector_queries)}] {query_info['event_type']}")

            df = self._fetch_gdelt_news(
                query=query_info['query'],
                start_date=start_date,
                end_date=end_date,
                max_records=max_records_per_query
            )

            if not df.empty:
                # Enrichir avec les métadonnées de l'événement
                df['event_type'] = query_info['event_type']
                df['event_category'] = 'sector'
                df['base_impact_score'] = query_info['impact_score']
                df['affects'] = str(query_info['affects'])  # Liste des actifs affectés
                all_news.append(df)
                self.stats['sector_events'] += len(df)
                logger.success(f"  ✓ {len(df)} articles collectés")

            time.sleep(delay)

        if all_news:
            combined = pd.concat(all_news, ignore_index=True)
            logger.success(f"\n✓ Total événements sectoriels: {len(combined)} articles")
            return combined
        else:
            logger.warning("Aucune news sectorielle collectée")
            return pd.DataFrame()

    def _fetch_gdelt_news(
        self,
        query: str,
        start_date: str,
        end_date: str,
        max_records: int = 250
    ) -> pd.DataFrame:
        """
        Requête GDELT pour une recherche donnée

        Args:
            query: Requête de recherche
            start_date: Date de début
            end_date: Date de fin
            max_records: Nombre max d'articles

        Returns:
            DataFrame avec les articles
        """
        try:
            # Formater les dates pour GDELT
            start_dt = self._format_date(start_date)
            end_dt = self._format_date(end_date)

            params = {
                'query': query,
                'mode': 'artlist',
                'maxrecords': min(max_records, 250),
                'format': 'json',
                'startdatetime': start_dt,
                'enddatetime': end_dt,
                'sourcelang': 'eng'  # Anglais principalement
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'articles' not in data or not data['articles']:
                return pd.DataFrame()

            articles = data['articles']
            df = pd.DataFrame(articles)

            # Nettoyer les données
            if not df.empty:
                df = self._process_gdelt_data(df)
                self.stats['total_fetched'] += len(df)

            return df

        except Exception as e:
            logger.error(f"Erreur GDELT: {str(e)}")
            return pd.DataFrame()

    def _format_date(self, date_str: str) -> str:
        """Convertit une date en format GDELT (YYYYMMDDHHMMSS)"""
        if len(date_str) == 14:
            return date_str

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d%H%M%S")

    def _process_gdelt_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Traite et nettoie les données GDELT"""
        # Convertir la date
        if 'seendate' in df.columns:
            df['date'] = pd.to_datetime(df['seendate'], format='%Y%m%dT%H%M%SZ', errors='coerce')

        # Renommer les colonnes
        column_mapping = {
            'url': 'url',
            'title': 'title',
            'domain': 'source',
            'language': 'language',
            'seendate': 'published_date'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and old_col != new_col:
                df = df.rename(columns={old_col: new_col})

        # Sélectionner les colonnes importantes
        important_cols = ['date', 'title', 'url', 'source', 'language']
        available_cols = [col for col in important_cols if col in df.columns]

        # Garder aussi les colonnes qu'on a ajoutées
        extra_cols = ['event_type', 'event_category', 'base_impact_score', 'affects']
        for col in extra_cols:
            if col in df.columns:
                available_cols.append(col)

        df = df[available_cols]

        return df

    def fetch_all_news(
        self,
        start_date: str,
        end_date: str,
        max_records_per_query: int = 250,
        delay: float = 2.0
    ) -> pd.DataFrame:
        """
        Collecte toutes les news (macro + sectorielles)

        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin
            max_records_per_query: Nombre max d'articles par requête
            delay: Délai entre requêtes

        Returns:
            DataFrame combiné avec toutes les news
        """
        logger.info("\n" + "="*80)
        logger.info("🚀 DÉMARRAGE COLLECTE HYBRIDE DE NEWS")
        logger.info("="*80)
        logger.info(f"Période: {start_date} → {end_date}")

        # Reset stats
        self.stats = {
            'total_fetched': 0,
            'macro_events': 0,
            'sector_events': 0,
            'duplicates_removed': 0
        }

        # Collecte macro
        macro_df = self.fetch_macro_news(start_date, end_date, max_records_per_query, delay)

        # Collecte sectorielle
        sector_df = self.fetch_sector_news(start_date, end_date, max_records_per_query, delay)

        # Combiner
        all_news = []
        if not macro_df.empty:
            all_news.append(macro_df)
        if not sector_df.empty:
            all_news.append(sector_df)

        if not all_news:
            logger.warning("Aucune news collectée")
            return pd.DataFrame()

        combined = pd.concat(all_news, ignore_index=True)

        # Dédupliquer par URL
        initial_count = len(combined)
        combined = combined.drop_duplicates(subset=['url'], keep='first')
        self.stats['duplicates_removed'] = initial_count - len(combined)

        logger.info("\n" + "="*80)
        logger.info("📊 STATISTIQUES DE COLLECTE")
        logger.info("="*80)
        logger.info(f"Total articles collectés: {self.stats['total_fetched']}")
        logger.info(f"  - Événements macro: {self.stats['macro_events']}")
        logger.info(f"  - Événements sectoriels: {self.stats['sector_events']}")
        logger.info(f"Doublons supprimés: {self.stats['duplicates_removed']}")
        logger.info(f"Articles uniques finaux: {len(combined)}")
        logger.info("="*80)

        return combined

    def map_news_to_assets(
        self,
        news_df: pd.DataFrame,
        min_relevance_score: float = 5.0,
        top_n_guaranteed: int = 0
    ) -> pd.DataFrame:
        """
        Mappe chaque news aux actifs qu'elle peut impacter

        Args:
            news_df: DataFrame avec les news collectées
            min_relevance_score: Score minimum de pertinence
            top_n_guaranteed: Nombre de news top à garantir (même si score < min)
                            0 = désactivé, 50/100 = garantit les N meilleures news

        Returns:
            DataFrame enrichi avec les actifs impactés et leurs scores
        """
        logger.info("\n" + "="*80)
        logger.info("🔗 MAPPING DES NEWS VERS LES ACTIFS")
        logger.info("="*80)

        if top_n_guaranteed > 0:
            logger.info(f"🎯 Mode garantie activé: Top {top_n_guaranteed} news les plus importantes")

        if news_df.empty:
            return pd.DataFrame()

        # Première passe: calculer les scores pour toutes les news
        all_scores = []

        for idx, row in news_df.iterrows():
            title = row.get('title', '')

            # Utiliser le mapper avec score minimum = 0 pour tout évaluer
            relevant_assets = self.mapper.get_relevant_assets_for_news(
                news_title=title,
                news_content="",
                min_score=0.0  # Pas de filtrage ici
            )

            if relevant_assets:
                for asset_name, score, matched_events in relevant_assets:
                    all_scores.append({
                        'row': row,
                        'asset': asset_name,
                        'score': score,
                        'matched_events': matched_events
                    })

        if not all_scores:
            logger.warning("Aucune news n'a pu être évaluée")
            return pd.DataFrame()

        # Créer un DataFrame temporaire pour l'analyse
        temp_df = pd.DataFrame(all_scores)

        # Déterminer le seuil effectif
        if top_n_guaranteed > 0:
            # Trier par score décroissant
            temp_df_sorted = temp_df.sort_values('score', ascending=False)

            # Prendre les top N scores
            if len(temp_df_sorted) > top_n_guaranteed:
                nth_score = temp_df_sorted.iloc[top_n_guaranteed - 1]['score']
                effective_threshold = min(min_relevance_score, nth_score)
                logger.info(f"Seuil effectif ajusté: {effective_threshold:.2f} (garantit top {top_n_guaranteed})")
            else:
                effective_threshold = min_relevance_score
                logger.info(f"Moins de {top_n_guaranteed} news, seuil standard appliqué: {effective_threshold:.2f}")
        else:
            effective_threshold = min_relevance_score
            logger.info(f"Seuil de pertinence: {effective_threshold:.2f}")

        # Filtrer selon le seuil effectif
        results = []
        for item in all_scores:
            if item['score'] >= effective_threshold:
                result_row = item['row'].copy()
                result_row['asset'] = item['asset']
                result_row['relevance_score'] = item['score']
                result_row['matched_events'] = ', '.join(item['matched_events'])
                results.append(result_row)

        if not results:
            logger.warning("Aucune news n'atteint le score minimum de pertinence")
            return pd.DataFrame()

        mapped_df = pd.DataFrame(results)

        logger.success(f"✓ {len(mapped_df)} associations news-actifs créées")
        logger.info(f"Nombre de news uniques: {mapped_df['url'].nunique()}")
        logger.info(f"Nombre d'actifs impactés: {mapped_df['asset'].nunique()}")

        # Statistiques sur les scores
        if top_n_guaranteed > 0:
            below_min = len(mapped_df[mapped_df['relevance_score'] < min_relevance_score])
            if below_min > 0:
                logger.info(f"📊 {below_min} associations capturées grâce au mode garantie (score < {min_relevance_score})")

        # Afficher les top actifs impactés
        top_assets = mapped_df['asset'].value_counts().head(10)
        logger.info("\n📊 Top 10 actifs les plus mentionnés:")
        for asset, count in top_assets.items():
            logger.info(f"  {asset}: {count} news")

        return mapped_df

    def collect_and_map(
        self,
        start_date: str,
        end_date: str,
        min_relevance_score: float = 5.0,
        max_records_per_query: int = 250,
        delay: float = 2.0,
        top_n_guaranteed: int = 0
    ) -> pd.DataFrame:
        """
        Pipeline complète: collecte + mapping

        Args:
            start_date: Date de début
            end_date: Date de fin
            min_relevance_score: Score minimum de pertinence
            max_records_per_query: Nombre max d'articles par requête
            delay: Délai entre requêtes
            top_n_guaranteed: Garantir les N news les plus importantes (0 = désactivé)

        Returns:
            DataFrame avec news mappées aux actifs
        """
        # Collecte
        news_df = self.fetch_all_news(start_date, end_date, max_records_per_query, delay)

        if news_df.empty:
            return pd.DataFrame()

        # Sauvegarder les news brutes
        raw_path = self.output_dir / "hybrid_news_raw.csv"
        news_df.to_csv(raw_path, index=False)
        logger.info(f"\n💾 News brutes sauvegardées: {raw_path}")

        # Mapping
        mapped_df = self.map_news_to_assets(news_df, min_relevance_score, top_n_guaranteed)

        if not mapped_df.empty:
            # Sauvegarder les news mappées
            mapped_path = self.output_dir / "hybrid_news_mapped.csv"
            mapped_df.to_csv(mapped_path, index=False)
            logger.success(f"💾 News mappées sauvegardées: {mapped_path}")

        return mapped_df


if __name__ == "__main__":
    # Test du collecteur hybride
    from src.utils.logger import setup_logger

    setup_logger()

    collector = HybridNewsCollector()

    # Test sur une courte période
    logger.info("🧪 TEST DU COLLECTEUR HYBRIDE")

    mapped_news = collector.collect_and_map(
        start_date="2024-01-15",
        end_date="2024-01-20",
        min_relevance_score=5.0,
        max_records_per_query=50,  # Réduit pour le test
        delay=2.0
    )

    if not mapped_news.empty:
        print("\n" + "="*80)
        print("APERÇU DES RÉSULTATS")
        print("="*80)
        print(f"\nNombre total d'associations: {len(mapped_news)}")
        print(f"\nColonnes: {mapped_news.columns.tolist()}")
        print(f"\nPremiers résultats:")
        print(mapped_news[['title', 'asset', 'relevance_score', 'event_type']].head(10))
