"""
Script de test pour la nouvelle configuration de filtrage élargie
Teste avec min_relevance_score=3.0 et les nouveaux keywords enrichis

USAGE:
    source venv/bin/activate
    python test_new_filters.py
"""
import sys
from pathlib import Path

# Vérifier environnement virtuel
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("\n⚠️  ERREUR: Environnement virtuel non activé!")
    print("\n💡 Veuillez d'abord activer l'environnement virtuel:")
    print("   source venv/bin/activate")
    print("\nPuis relancez:")
    print("   python test_new_filters.py\n")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.collectors.hybrid_news_collector import HybridNewsCollector
from loguru import logger


def main():
    """Test avec les nouveaux critères élargis"""

    setup_logger(level="INFO")

    logger.info("=" * 80)
    logger.info("🧪 TEST DE LA NOUVELLE CONFIGURATION DE FILTRAGE")
    logger.info("=" * 80)
    logger.info("\n📋 NOUVEAUX PARAMÈTRES:")
    logger.info("  • min_relevance_score: 3.0 (ancien: 5.0)")
    logger.info("  • Keywords enrichis pour tous les événements macro et sectoriels")
    logger.info("\n🎯 OBJECTIF: Capturer plus de news pertinentes")

    # Initialiser le collecteur
    collector = HybridNewsCollector()

    # Collecter avec le nouveau seuil
    logger.info("\n" + "=" * 80)
    logger.info("⚡ COLLECTE DE TEST (même période que précédemment)")
    logger.info("=" * 80)

    # Utiliser le nouveau seuil de 3.0 au lieu de 5.0
    mapped_news = collector.collect_and_map(
        start_date="2026-01-01",  # Mis à jour pour période récente
        end_date="2026-01-16",    # Date d'aujourd'hui
        min_relevance_score=3.0,  # ← NOUVEAU SEUIL
        max_records_per_query=50,
        delay=2.0
    )

    if not mapped_news.empty:
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPARAISON DES RÉSULTATS")
        logger.info("=" * 80)

        # Statistiques globales
        total_news = mapped_news['url'].nunique()
        total_associations = len(mapped_news)
        total_assets = mapped_news['asset'].nunique()

        logger.info(f"\n📰 News uniques collectées: {total_news}")
        logger.info(f"🔗 Associations news-actifs: {total_associations}")
        logger.info(f"📈 Actifs impactés: {total_assets}")

        # Distribution des scores
        logger.info("\n📊 DISTRIBUTION DES SCORES DE PERTINENCE:")
        score_ranges = [
            (0, 3, "< 3.0 (nouveau seuil aurait rejeté)"),
            (3, 5, "3.0-5.0 (capturé grâce au nouveau seuil)"),
            (5, 10, "5.0-10.0 (aurait été capturé avant)"),
            (10, 999, "> 10.0 (très pertinent)")
        ]

        for min_s, max_s, label in score_ranges:
            count = len(mapped_news[(mapped_news['relevance_score'] >= min_s) &
                                    (mapped_news['relevance_score'] < max_s)])
            if count > 0:
                pct = (count / total_associations) * 100
                logger.info(f"  • {label:45s} | {count:4d} ({pct:5.1f}%)")

        # Top actifs
        logger.info("\n🏆 TOP 10 ACTIFS LES PLUS IMPACTÉS:")
        top_assets = mapped_news['asset'].value_counts().head(10)
        for rank, (asset, count) in enumerate(top_assets.items(), 1):
            avg_score = mapped_news[mapped_news['asset'] == asset]['relevance_score'].mean()
            logger.info(f"  {rank:2d}. {asset:20s} | {count:3d} news | Score moyen: {avg_score:.1f}")

        # Top événements
        logger.info("\n🎯 TOP ÉVÉNEMENTS DÉTECTÉS:")
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

        # Exemples de news avec score 3-5
        logger.info("\n💡 EXEMPLES DE NEWS CAPTURÉES GRÂCE AU NOUVEAU SEUIL (score 3-5):")
        new_threshold_news = mapped_news[(mapped_news['relevance_score'] >= 3.0) &
                                          (mapped_news['relevance_score'] < 5.0)]

        if not new_threshold_news.empty:
            for idx, row in new_threshold_news.head(5).iterrows():
                logger.info(f"\n  📰 {row['title'][:70]}...")
                logger.info(f"     Actif: {row['asset']} | Score: {row['relevance_score']:.1f} | Événement: {row['event_type']}")
        else:
            logger.info("  (Aucune news dans cette tranche pour ce test)")

        logger.info("\n" + "=" * 80)
        logger.info("✅ TEST TERMINÉ")
        logger.info("=" * 80)

        # Conseil final
        logger.info("\n💡 RECOMMANDATION:")
        if total_associations > 289:  # 289 = nombre actuel dans hybrid_news_mapped.csv
            gain = total_associations - 289
            gain_pct = (gain / 289) * 100
            logger.info(f"  ✅ Augmentation de {gain} associations (+{gain_pct:.1f}%)")
            logger.info("  ✅ La nouvelle configuration capture bien plus de news!")
        else:
            logger.info("  ⚠️  Pas d'augmentation significative détectée")
            logger.info("  💡 Essayez d'augmenter max_records_per_query ou la période")

    else:
        logger.warning("\n⚠️  Aucune news collectée")
        logger.info("💡 Vérifiez votre connexion internet et l'API GDELT")


if __name__ == "__main__":
    main()
