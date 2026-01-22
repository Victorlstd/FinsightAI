"""
Script de test pour le nouveau filtre top_n_guaranteed
Garantit la récupération des N news les plus importantes

USAGE:
    source venv/bin/activate
    python test_top_n_filter.py
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
    print("   python test_top_n_filter.py\n")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.collectors.hybrid_news_collector import HybridNewsCollector
from loguru import logger


def main():
    """Test du filtre top_n_guaranteed"""

    setup_logger(level="INFO")

    logger.info("=" * 80)
    logger.info("🧪 TEST DU FILTRE TOP N GARANTI")
    logger.info("=" * 80)

    # Paramètres
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    MIN_RELEVANCE_SCORE = 3.0
    TOP_N_GUARANTEED = 100  # Garantir les 100 meilleures news

    logger.info(f"\n⚙️  CONFIGURATION:")
    logger.info(f"  • Période: {START_DATE} → {END_DATE}")
    logger.info(f"  • Seuil minimum: {MIN_RELEVANCE_SCORE}")
    logger.info(f"  • Top N garanti: {TOP_N_GUARANTEED}")

    logger.info(f"\n💡 FONCTIONNEMENT:")
    logger.info(f"  1. Toutes les news sont évaluées")
    logger.info(f"  2. Les {TOP_N_GUARANTEED} meilleures sont GARANTIES")
    logger.info(f"  3. En plus, toutes les news avec score ≥ {MIN_RELEVANCE_SCORE} sont incluses")
    logger.info(f"  4. Résultat: minimum {TOP_N_GUARANTEED} news, potentiellement plus")

    # Initialiser le collecteur
    collector = HybridNewsCollector()

    # Test 1: Sans garantie (mode standard)
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST 1: MODE STANDARD (sans garantie)")
    logger.info("=" * 80)

    try:
        mapped_standard = collector.collect_and_map(
            start_date=START_DATE,
            end_date=END_DATE,
            min_relevance_score=MIN_RELEVANCE_SCORE,
            max_records_per_query=50,
            delay=2.0,
            top_n_guaranteed=0  # DÉSACTIVÉ
        )

        count_standard = len(mapped_standard) if not mapped_standard.empty else 0
        logger.info(f"\n✓ Mode standard: {count_standard} associations")

    except Exception as e:
        logger.error(f"Erreur Test 1: {e}")
        count_standard = 0

    # Test 2: Avec garantie top 100
    logger.info("\n" + "=" * 80)
    logger.info(f"📊 TEST 2: MODE GARANTI (top {TOP_N_GUARANTEED})")
    logger.info("=" * 80)

    try:
        mapped_guaranteed = collector.collect_and_map(
            start_date=START_DATE,
            end_date=END_DATE,
            min_relevance_score=MIN_RELEVANCE_SCORE,
            max_records_per_query=50,
            delay=2.0,
            top_n_guaranteed=TOP_N_GUARANTEED  # ACTIVÉ
        )

        if not mapped_guaranteed.empty:
            count_guaranteed = len(mapped_guaranteed)
            unique_news = mapped_guaranteed['url'].nunique()

            logger.info(f"\n✓ Mode garanti: {count_guaranteed} associations")
            logger.info(f"✓ News uniques: {unique_news}")

            # Analyse détaillée
            logger.info(f"\n📊 ANALYSE DÉTAILLÉE:")

            # Distribution des scores
            score_ranges = [
                (0, 3, "< 3.0 (capturé uniquement grâce au top N)"),
                (3, 5, "3.0-5.0 (capturé par seuil ou top N)"),
                (5, 10, "5.0-10.0 (pertinence moyenne-élevée)"),
                (10, 999, "> 10.0 (très pertinent)")
            ]

            for min_s, max_s, label in score_ranges:
                count = len(mapped_guaranteed[(mapped_guaranteed['relevance_score'] >= min_s) &
                                               (mapped_guaranteed['relevance_score'] < max_s)])
                if count > 0:
                    pct = (count / count_guaranteed) * 100
                    logger.info(f"  • {label:45s} | {count:4d} ({pct:5.1f}%)")

            # News capturées uniquement grâce au top N
            below_threshold = mapped_guaranteed[mapped_guaranteed['relevance_score'] < MIN_RELEVANCE_SCORE]
            if not below_threshold.empty:
                logger.info(f"\n🎯 NEWS CAPTURÉES GRÂCE AU MODE GARANTI:")
                logger.info(f"   {len(below_threshold)} associations avec score < {MIN_RELEVANCE_SCORE}")
                logger.info(f"   (auraient été rejetées en mode standard)")

                # Exemples
                logger.info(f"\n📰 EXEMPLES (top 5):")
                for idx, row in below_threshold.nlargest(5, 'relevance_score').iterrows():
                    logger.info(f"\n  [{row['relevance_score']:.2f}] {row['title'][:70]}...")
                    logger.info(f"      Actif: {row['asset']} | Événement: {row['event_type']}")

            # Top actifs
            logger.info(f"\n🏆 TOP 10 ACTIFS:")
            top_assets = mapped_guaranteed['asset'].value_counts().head(10)
            for rank, (asset, count) in enumerate(top_assets.items(), 1):
                avg_score = mapped_guaranteed[mapped_guaranteed['asset'] == asset]['relevance_score'].mean()
                logger.info(f"  {rank:2d}. {asset:20s} | {count:3d} news | Score moyen: {avg_score:.1f}")

            # Comparaison
            if count_standard > 0:
                logger.info(f"\n" + "=" * 80)
                logger.info("📈 COMPARAISON DES MODES")
                logger.info("=" * 80)
                logger.info(f"  Mode standard:  {count_standard:4d} associations")
                logger.info(f"  Mode garanti:   {count_guaranteed:4d} associations")

                diff = count_guaranteed - count_standard
                if diff > 0:
                    pct_increase = (diff / count_standard) * 100 if count_standard > 0 else 0
                    logger.info(f"  Différence:     +{diff:4d} associations (+{pct_increase:.1f}%)")
                    logger.success(f"\n✅ Le mode garanti capture {diff} associations supplémentaires!")
                else:
                    logger.info(f"  Différence:      {diff:4d} associations")
                    logger.info(f"\n💡 Tous les résultats dépassaient déjà le seuil de {MIN_RELEVANCE_SCORE}")

        else:
            logger.warning("\n⚠️  Aucune news collectée en mode garanti")

    except Exception as e:
        logger.error(f"\n❌ Erreur Test 2: {e}")
        import traceback
        traceback.print_exc()

    # Recommandations
    logger.info(f"\n" + "=" * 80)
    logger.info("💡 RECOMMANDATIONS D'USAGE")
    logger.info("=" * 80)
    logger.info(f"")
    logger.info(f"👉 Utilisez top_n_guaranteed=50-100 si:")
    logger.info(f"   • Vous voulez GARANTIR un nombre minimum de news")
    logger.info(f"   • Vous acceptez des news avec score légèrement inférieur")
    logger.info(f"   • Vous préférez plus de couverture que de précision")
    logger.info(f"")
    logger.info(f"👉 Utilisez top_n_guaranteed=0 (désactivé) si:")
    logger.info(f"   • Vous voulez SEULEMENT les news pertinentes")
    logger.info(f"   • Vous préférez la qualité à la quantité")
    logger.info(f"   • Vous avez déjà assez de news avec le seuil actuel")
    logger.info(f"")
    logger.info(f"⚙️  EXEMPLE D'USAGE DANS VOS SCRIPTS:")
    logger.info(f"")
    logger.info(f"   collector.collect_and_map(")
    logger.info(f"       start_date='2026-01-01',")
    logger.info(f"       end_date='2026-01-16',")
    logger.info(f"       min_relevance_score=3.0,")
    logger.info(f"       top_n_guaranteed=100  # ← GARANTIR TOP 100")
    logger.info(f"   )")


if __name__ == "__main__":
    main()
