"""
Script principal de collecte de news avec la nouvelle configuration
Collecte sur une période plus longue avec tous les paramètres de production

USAGE:
    source venv/bin/activate
    python run_news_collection.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Vérifier environnement virtuel
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("\n⚠️  ERREUR: Environnement virtuel non activé!")
    print("\n💡 Veuillez d'abord activer l'environnement virtuel:")
    print("   source venv/bin/activate")
    print("\nPuis relancez:")
    print("   python run_news_collection.py\n")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.collectors.hybrid_news_collector import HybridNewsCollector
from loguru import logger
import pandas as pd


def main():
    """Collecte principale de news avec la nouvelle configuration"""

    setup_logger(level="INFO")

    logger.info("=" * 80)
    logger.info("🚀 COLLECTE PRINCIPALE DE NEWS - CONFIGURATION ÉLARGIE")
    logger.info("=" * 80)

    # Paramètres de collecte
    # Vous pouvez modifier ces valeurs selon vos besoins
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")  # 15 derniers jours
    MIN_RELEVANCE_SCORE = 3.0  # Nouveau seuil
    MAX_RECORDS_PER_QUERY = 250  # Maximum de records par requête GDELT
    DELAY_BETWEEN_REQUESTS = 2.0  # Délai entre les requêtes (secondes)
    TOP_N_GUARANTEED = 100  # Garantir les 100 meilleures news (0 = désactivé)

    logger.info(f"\n📅 PÉRIODE DE COLLECTE:")
    logger.info(f"  • Du: {START_DATE}")
    logger.info(f"  • Au: {END_DATE}")
    logger.info(f"\n⚙️  PARAMÈTRES:")
    logger.info(f"  • Seuil de pertinence minimum: {MIN_RELEVANCE_SCORE}")
    logger.info(f"  • Top N garanti: {TOP_N_GUARANTEED} {'(activé)' if TOP_N_GUARANTEED > 0 else '(désactivé)'}")
    logger.info(f"  • Records max par requête: {MAX_RECORDS_PER_QUERY}")
    logger.info(f"  • Délai entre requêtes: {DELAY_BETWEEN_REQUESTS}s")

    # Initialiser le collecteur
    logger.info("\n🔧 Initialisation du collecteur...")
    collector = HybridNewsCollector()

    # Lancer la collecte
    logger.info("\n" + "=" * 80)
    logger.info("⚡ DÉMARRAGE DE LA COLLECTE")
    logger.info("=" * 80)
    logger.info("⏳ Cela peut prendre plusieurs minutes selon la période...")

    try:
        mapped_news = collector.collect_and_map(
            start_date=START_DATE,
            end_date=END_DATE,
            min_relevance_score=MIN_RELEVANCE_SCORE,
            max_records_per_query=MAX_RECORDS_PER_QUERY,
            delay=DELAY_BETWEEN_REQUESTS,
            top_n_guaranteed=TOP_N_GUARANTEED
        )

        if not mapped_news.empty:
            logger.info("\n" + "=" * 80)
            logger.info("✅ COLLECTE TERMINÉE AVEC SUCCÈS")
            logger.info("=" * 80)

            # Statistiques détaillées
            total_news = mapped_news['url'].nunique()
            total_associations = len(mapped_news)
            total_assets = mapped_news['asset'].nunique()

            logger.info(f"\n📊 STATISTIQUES GLOBALES:")
            logger.info(f"  • News uniques collectées: {total_news}")
            logger.info(f"  • Associations news-actifs: {total_associations}")
            logger.info(f"  • Actifs impactés: {total_assets}")

            # Distribution par catégorie
            logger.info(f"\n📂 DISTRIBUTION PAR CATÉGORIE:")
            category_counts = mapped_news['event_category'].value_counts()
            for category, count in category_counts.items():
                pct = (count / total_associations) * 100
                logger.info(f"  • {category:15s}: {count:4d} ({pct:5.1f}%)")

            # Distribution des scores
            logger.info(f"\n📊 DISTRIBUTION DES SCORES DE PERTINENCE:")
            score_ranges = [
                (3, 5, "3.0-5.0 (capturé grâce au nouveau seuil)"),
                (5, 8, "5.0-8.0 (pertinence moyenne)"),
                (8, 10, "8.0-10.0 (pertinence élevée)"),
                (10, 999, "> 10.0 (très pertinent)")
            ]

            for min_s, max_s, label in score_ranges:
                count = len(mapped_news[(mapped_news['relevance_score'] >= min_s) &
                                        (mapped_news['relevance_score'] < max_s)])
                if count > 0:
                    pct = (count / total_associations) * 100
                    logger.info(f"  • {label:45s} | {count:4d} ({pct:5.1f}%)")

            # Top actifs impactés
            logger.info(f"\n🏆 TOP 10 ACTIFS LES PLUS IMPACTÉS:")
            top_assets = mapped_news['asset'].value_counts().head(10)
            for rank, (asset, count) in enumerate(top_assets.items(), 1):
                avg_score = mapped_news[mapped_news['asset'] == asset]['relevance_score'].mean()
                logger.info(f"  {rank:2d}. {asset:20s} | {count:3d} news | Score moyen: {avg_score:.1f}")

            # Top événements détectés
            logger.info(f"\n🎯 TOP 10 ÉVÉNEMENTS DÉTECTÉS:")
            event_counts = {}
            for events_str in mapped_news['matched_events'].dropna():
                for event in str(events_str).split(','):
                    event = event.strip()
                    if event:
                        event_counts[event] = event_counts.get(event, 0) + 1

            for rank, (event, count) in enumerate(sorted(event_counts.items(),
                                                          key=lambda x: x[1],
                                                          reverse=True)[:10], 1):
                logger.info(f"  {rank:2d}. {event:30s} | {count:3d} détections")

            # Distribution par langue
            logger.info(f"\n🌍 DISTRIBUTION PAR LANGUE:")
            lang_counts = mapped_news['language'].value_counts()
            for lang, count in lang_counts.items():
                pct = (count / total_associations) * 100
                logger.info(f"  • {lang}: {count:4d} ({pct:5.1f}%)")

            # Exemples de news récentes
            logger.info(f"\n📰 EXEMPLES DE NEWS RÉCENTES (top 5 par score):")
            top_news = mapped_news.nlargest(5, 'relevance_score')
            for idx, row in top_news.iterrows():
                logger.info(f"\n  [{row['relevance_score']:.1f}] {row['title'][:70]}...")
                logger.info(f"      Actif: {row['asset']} | Événement: {row['event_type']} | Source: {row['source']}")

            # Fichiers de sortie
            logger.info(f"\n" + "=" * 80)
            logger.info("💾 FICHIERS GÉNÉRÉS")
            logger.info("=" * 80)

            raw_file = Path("data/raw/news/hybrid_news_raw.csv")
            mapped_file = Path("data/raw/news/hybrid_news_mapped.csv")

            logger.info(f"  • News brutes: {raw_file}")
            logger.info(f"  • News mappées: {mapped_file}")

            # Sauvegarder aussi une version horodatée
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path(f"data/raw/news/hybrid_news_mapped_{timestamp}.csv")
            mapped_news.to_csv(backup_file, index=False)
            logger.info(f"  • Backup horodaté: {backup_file}")

            logger.info(f"\n✅ Toutes les données ont été sauvegardées avec succès!")

        else:
            logger.warning("\n⚠️  AUCUNE NEWS COLLECTÉE")
            logger.info("\n💡 SUGGESTIONS:")
            logger.info("  • Vérifiez votre connexion internet")
            logger.info("  • Vérifiez que l'API GDELT est accessible")
            logger.info("  • Essayez d'élargir la période de collecte")
            logger.info("  • Réduisez le min_relevance_score si nécessaire")

    except Exception as e:
        logger.error(f"\n❌ ERREUR LORS DE LA COLLECTE: {e}")
        logger.info("\n💡 Vérifiez les logs ci-dessus pour plus de détails")
        raise


if __name__ == "__main__":
    main()
