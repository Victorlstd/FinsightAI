"""
Script de démonstration du nouveau système de collecte hybride de news
Collecte les événements macro et sectoriels sans mentionner directement les actifs

USAGE:
    source venv/bin/activate  # Activer l'environnement virtuel d'abord
    python demo_hybrid_news.py
"""
import sys
from pathlib import Path

# Vérifier que nous sommes dans un environnement virtuel
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("\n⚠️  ERREUR: Environnement virtuel non activé!")
    print("\n💡 Veuillez d'abord activer l'environnement virtuel:")
    print("   source venv/bin/activate")
    print("\nPuis relancez:")
    print("   python demo_hybrid_news.py\n")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.collectors.hybrid_news_collector import HybridNewsCollector
from loguru import logger


def main():
    """Démonstration du collecteur hybride"""

    setup_logger(level="INFO")

    logger.info("=" * 80)
    logger.info("🎯 DÉMONSTRATION DU COLLECTEUR HYBRIDE DE NEWS")
    logger.info("=" * 80)
    logger.info("\n📋 STRATÉGIE:")
    logger.info("  1. Collecte d'événements MACRO (Fed, inflation, géopolitique...)")
    logger.info("  2. Collecte d'événements SECTORIELS (tech, énergie, luxe...)")
    logger.info("  3. Mapping intelligent vers les actifs impactés")
    logger.info("  4. Scoring de pertinence pour chaque association news-actif")
    logger.info("\n✨ Les news NE mentionnent PAS directement vos actifs")
    logger.info("   mais peuvent les impacter indirectement!")

    # Initialiser le collecteur avec les chemins absolus
    script_dir = Path(__file__).parent
    config_path = script_dir / "config" / "news_strategy.yaml"
    output_dir = script_dir / "data" / "raw" / "news"
    
    collector = HybridNewsCollector(
        output_dir=str(output_dir),
        config_path=str(config_path)
    )

    # Collecter et mapper les news
    # ATTENTION: Pour une vraie collecte, augmenter la période et les records
    logger.info("\n" + "=" * 80)
    logger.info("⚡ COLLECTE DE TEST (période courte)")
    logger.info("=" * 80)

    mapped_news = collector.collect_and_map(
        start_date="2026-01-01",  # Mis à jour pour période récente
        end_date="2026-01-16",    # Date d'aujourd'hui
        min_relevance_score=3.0,  # Nouveau seuil réduit
        max_records_per_query=50,  # Réduit pour le test
        delay=2.0
    )

    if not mapped_news.empty:
        logger.info("\n" + "=" * 80)
        logger.info("📊 ANALYSE DES RÉSULTATS")
        logger.info("=" * 80)

        # Statistiques globales
        total_news = mapped_news['url'].nunique()
        total_associations = len(mapped_news)
        total_assets = mapped_news['asset'].nunique()

        logger.info(f"\n📰 News uniques collectées: {total_news}")
        logger.info(f"🔗 Associations news-actifs: {total_associations}")
        logger.info(f"📈 Actifs impactés: {total_assets}")

        # Top actifs
        logger.info("\n🏆 TOP 10 ACTIFS LES PLUS IMPACTÉS:")
        top_assets = mapped_news['asset'].value_counts().head(10)
        for rank, (asset, count) in enumerate(top_assets.items(), 1):
            avg_score = mapped_news[mapped_news['asset'] == asset]['relevance_score'].mean()
            logger.info(f"  {rank:2d}. {asset:20s} | {count:3d} news | Score moyen: {avg_score:.1f}")

        # Top événements
        logger.info("\n🌍 TOP TYPES D'ÉVÉNEMENTS DÉTECTÉS:")
        top_events = mapped_news['event_type'].value_counts().head(10)
        for rank, (event, count) in enumerate(top_events.items(), 1):
            logger.info(f"  {rank:2d}. {event:30s} | {count:3d} news")

        # Exemples de news macro
        logger.info("\n📰 EXEMPLES DE NEWS MACRO (haute pertinence):")
        macro_news = mapped_news[mapped_news['event_category'] == 'macro']
        if not macro_news.empty:
            top_macro = macro_news.nlargest(5, 'relevance_score')
            for idx, row in top_macro.iterrows():
                logger.info(f"\n  📌 {row['title'][:80]}...")
                logger.info(f"     Actif: {row['asset']} | Score: {row['relevance_score']} | Type: {row['event_type']}")

        # Exemples de news sectorielles
        logger.info("\n🏭 EXEMPLES DE NEWS SECTORIELLES (haute pertinence):")
        sector_news = mapped_news[mapped_news['event_category'] == 'sector']
        if not sector_news.empty:
            top_sector = sector_news.nlargest(5, 'relevance_score')
            for idx, row in top_sector.iterrows():
                logger.info(f"\n  📌 {row['title'][:80]}...")
                logger.info(f"     Actif: {row['asset']} | Score: {row['relevance_score']} | Type: {row['event_type']}")

        # Distribution des scores
        logger.info("\n📊 DISTRIBUTION DES SCORES DE PERTINENCE:")
        score_ranges = [
            (5, 10, "Faible"),
            (10, 15, "Moyen"),
            (15, 20, "Élevé"),
            (20, 100, "Très élevé")
        ]
        for min_score, max_score, label in score_ranges:
            count = len(mapped_news[
                (mapped_news['relevance_score'] >= min_score) &
                (mapped_news['relevance_score'] < max_score)
            ])
            if count > 0:
                logger.info(f"  {label:15s} ({min_score:2d}-{max_score:2d}): {count:4d} associations")

        logger.info("\n" + "=" * 80)
        logger.info("✅ FICHIERS GÉNÉRÉS:")
        logger.info("=" * 80)
        logger.info("  📁 data/raw/news/hybrid_news_raw.csv     - News brutes")
        logger.info("  📁 data/raw/news/hybrid_news_mapped.csv  - News mappées aux actifs")
        logger.info("\n💡 PROCHAINES ÉTAPES:")
        logger.info("  1. Ajuster les keywords dans config/news_strategy.yaml")
        logger.info("  2. Modifier min_relevance_score selon vos besoins")
        logger.info("  3. Intégrer dans le pipeline principal")
        logger.info("  4. Ajouter l'analyse de sentiment")

    else:
        logger.warning("\n⚠️  Aucune news collectée (période trop courte ou API indisponible)")
        logger.info("\n💡 Essayez:")
        logger.info("  - Augmenter la période de collecte")
        logger.info("  - Réduire min_relevance_score")
        logger.info("  - Vérifier votre connexion Internet")

    logger.success("\n🎉 Démonstration terminée!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Démonstration interrompue")
    except Exception as e:
        logger.error(f"\n❌ Erreur: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
