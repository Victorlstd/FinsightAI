"""
Script de démonstration du nouveau système de collecte hybride de news
Collecte les événements macro et sectoriels sans mentionner directement les actifs

USAGE:
    source venv/bin/activate  # Activer l'environnement virtuel d'abord
    python demo_hybrid_news.py
"""
import sys
from pathlib import Path
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')

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


def analyze_sentiment(text, model, tokenizer, device, max_length=512):
    """
    Analyse le sentiment d'un texte avec le modèle FinBERT
    
    Args:
        text: Texte à analyser (titre de la news)
        model: Modèle FinBERT
        tokenizer: Tokenizer
        device: CPU ou GPU
        max_length: Longueur maximale (512 pour FinBERT)
    
    Returns:
        dict avec sentiment, confiance, et probabilités
    """
    
    # Gestion des textes vides ou null
    if not text or pd.isna(text) or len(str(text).strip()) == 0:
        return {
            'sentiment': 'Unknown',
            'confidence': 0.0,
            'prob_negative': 0.5,
            'prob_positive': 0.5
        }
    
    # Tokenization
    encoding = tokenizer(
        str(text),
        add_special_tokens=True,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    
    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)
    
    # Prédiction
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=1)[0]
        
        prediction = torch.argmax(logits, dim=1).item()
        confidence = probabilities[prediction].item()
    
    # Labels: 0=Negative, 1=Positive
    sentiment_label = "Positive" if prediction == 1 else "Negative"
    
    return {
        'sentiment': sentiment_label,
        'confidence': confidence,
        'prob_negative': probabilities[0].item(),
        'prob_positive': probabilities[1].item()
    }


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
        # ========== ANALYSE DE SENTIMENT ==========
        logger.info("\n" + "=" * 80)
        logger.info("🤖 ANALYSE DE SENTIMENT AVEC FINBERT")
        logger.info("=" * 80)

        # Configuration du device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🖥️  Device: {device}")

        # Chemin du modèle FinBERT
        model_path = script_dir.parent / "NLP" / "news_finbert_sentiment_model"
        
        try:
            logger.info(f"📥 Chargement du modèle FinBERT depuis: {model_path}")
            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                num_labels=2,
                use_safetensors=True
            )
            model.to(device)
            model.eval()
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            logger.info("✓ Modèle FinBERT chargé et prêt")

            # Dédupliquer par URL pour avoir des news uniques
            total_entries = len(mapped_news)
            mapped_news_unique = mapped_news.drop_duplicates(subset=['url']).copy()
            total_unique = len(mapped_news_unique)
            logger.info(f"📰 Analyse de {total_unique} news uniques (dédupliquées de {total_entries} entrées)")

            # Analyser chaque news unique
            sentiments = []
            confidences = []
            prob_negatives = []
            prob_positives = []

            for idx, row in mapped_news_unique.iterrows():
                title = row['title']
                result = analyze_sentiment(title, model, tokenizer, device)
                
                sentiments.append(result['sentiment'])
                confidences.append(result['confidence'])
                prob_negatives.append(result['prob_negative'])
                prob_positives.append(result['prob_positive'])
                
                # Afficher la progression tous les 10%
                progress = (len(sentiments) / total_unique) * 100
                if len(sentiments) % max(1, total_unique // 10) == 0:
                    logger.info(f"   ⏳ Progression: {progress:.0f}% ({len(sentiments)}/{total_unique})")

            # Ajouter les colonnes de sentiment aux news uniques
            mapped_news_unique['sentiment'] = sentiments
            mapped_news_unique['confidence'] = confidences
            mapped_news_unique['prob_negative'] = prob_negatives
            mapped_news_unique['prob_positive'] = prob_positives

            # Mapper les sentiments vers toutes les entrées (y compris les duplicatas)
            sentiment_map = mapped_news_unique.set_index('url')[[
                'sentiment', 'confidence', 'prob_negative', 'prob_positive'
            ]].to_dict('index')
            
            mapped_news['sentiment'] = mapped_news['url'].map(lambda x: sentiment_map.get(x, {}).get('sentiment', 'Unknown'))
            mapped_news['confidence'] = mapped_news['url'].map(lambda x: sentiment_map.get(x, {}).get('confidence', 0.0))
            mapped_news['prob_negative'] = mapped_news['url'].map(lambda x: sentiment_map.get(x, {}).get('prob_negative', 0.5))
            mapped_news['prob_positive'] = mapped_news['url'].map(lambda x: sentiment_map.get(x, {}).get('prob_positive', 0.5))

            logger.info(f"✓ Analyse de sentiment terminée pour {total_unique} news")
            
            # Sauvegarder les résultats avec sentiment
            output_file = output_dir / f"hybrid_news_mapped_with_sentiment.csv"
            mapped_news.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"💾 Fichier avec sentiment sauvegardé: {output_file}")

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse de sentiment: {str(e)}")
            logger.warning("⚠️  Poursuite sans analyse de sentiment")

        # ========== ANALYSE DES RÉSULTATS ==========
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

        # Statistiques de sentiment
        if 'sentiment' in mapped_news.columns:
            logger.info("\n😊 DISTRIBUTION DES SENTIMENTS:")
            sentiment_counts = mapped_news_unique['sentiment'].value_counts()
            total = len(mapped_news_unique)
            for sentiment, count in sentiment_counts.items():
                pct = (count / total) * 100
                emoji = "📈" if sentiment == "Positive" else "📉" if sentiment == "Negative" else "❓"
                logger.info(f"  {emoji} {sentiment:10s}: {count:4d} news ({pct:.1f}%)")
            
            avg_confidence = mapped_news_unique['confidence'].mean()
            logger.info(f"\n🎯 Confiance moyenne: {avg_confidence:.2%}")

        # Exemples de news macro
        logger.info("\n📰 EXEMPLES DE NEWS MACRO (haute pertinence):")
        macro_news = mapped_news[mapped_news['event_category'] == 'macro']
        if not macro_news.empty:
            top_macro = macro_news.nlargest(5, 'relevance_score')
            for idx, row in top_macro.iterrows():
                logger.info(f"\n  📌 {row['title'][:80]}...")
                sentiment_info = f" | Sentiment: {row.get('sentiment', 'N/A')} ({row.get('confidence', 0):.1%})" if 'sentiment' in row else ""
                logger.info(f"     Actif: {row['asset']} | Score: {row['relevance_score']} | Type: {row['event_type']}{sentiment_info}")

        # Exemples de news sectorielles
        logger.info("\n🏭 EXEMPLES DE NEWS SECTORIELLES (haute pertinence):")
        sector_news = mapped_news[mapped_news['event_category'] == 'sector']
        if not sector_news.empty:
            top_sector = sector_news.nlargest(5, 'relevance_score')
            for idx, row in top_sector.iterrows():
                logger.info(f"\n  📌 {row['title'][:80]}...")
                sentiment_info = f" | Sentiment: {row.get('sentiment', 'N/A')} ({row.get('confidence', 0):.1%})" if 'sentiment' in row else ""
                logger.info(f"     Actif: {row['asset']} | Score: {row['relevance_score']} | Type: {row['event_type']}{sentiment_info}")

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
        logger.info("  📁 data/raw/news/hybrid_news_raw.csv                 - News brutes")
        logger.info("  📁 data/raw/news/hybrid_news_mapped.csv              - News mappées aux actifs")
        logger.info("  📁 data/raw/news/hybrid_news_mapped_with_sentiment.csv - News avec analyse de sentiment")
        logger.info("\n💡 PROCHAINES ÉTAPES:")
        logger.info("  1. Ajuster les keywords dans config/news_strategy.yaml")
        logger.info("  2. Modifier min_relevance_score selon vos besoins")
        logger.info("  3. Utiliser les données avec sentiment pour l'analyse")
        logger.info("  4. Intégrer dans le pipeline de trading")

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
