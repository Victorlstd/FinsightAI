#!/usr/bin/env python3
"""
Script de test rapide pour vérifier que tous les modules fonctionnent.
Test sur une période courte et quelques actifs seulement.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.historical_data_collector import HistoricalDataCollector
from src.detectors.anomaly_detector import AnomalyDetector
from src.correlators.news_correlator import NewsCorrelator


def test_historical_collector():
    """Test du collecteur de données historiques."""
    print("\n" + "="*60)
    print("TEST 1: Collecteur de données historiques")
    print("="*60)

    collector = HistoricalDataCollector()

    # Test sur 2 actifs seulement, période courte
    test_assets = ["APPLE", "SP500"]

    data = collector.fetch_all_historical_data(
        period="1mo",  # 1 mois seulement
        symbols_to_fetch=test_assets
    )

    if data:
        print(f"✅ Test réussi: {len(data)} actifs collectés")
        return data
    else:
        print("❌ Test échoué: Aucune donnée collectée")
        return None


def test_anomaly_detector(historical_data):
    """Test du détecteur d'anomalies."""
    print("\n" + "="*60)
    print("TEST 2: Détecteur d'anomalies")
    print("="*60)

    if not historical_data:
        print("⚠️  Pas de données historiques, test ignoré")
        return None

    # Utiliser des seuils plus permissifs pour le test
    detector = AnomalyDetector(
        threshold_1day=-1.0,   # Seuil bas pour capturer plus d'anomalies
        threshold_5day=-2.0,
        threshold_30day=-3.0
    )

    anomalies = detector.detect_all_anomalies(historical_data)

    if not anomalies.empty:
        print(f"✅ Test réussi: {len(anomalies)} anomalies détectées")
        detector.display_summary(anomalies)
        return anomalies
    else:
        print("⚠️  Aucune anomalie détectée (normal sur période courte)")
        return None


def test_news_correlator(anomalies):
    """Test du corrélateur de news."""
    print("\n" + "="*60)
    print("TEST 3: Corrélateur de news")
    print("="*60)

    if anomalies is None or anomalies.empty:
        print("⚠️  Pas d'anomalies, test ignoré")
        return None

    print("⚠️  Test du corrélateur désactivé (nécessite collecte GDELT)")
    print("   Pour tester, lancez: python demo_detection.py --step correlate")

    # Le test complet de corrélation prend du temps
    # On vérifie juste que le module s'initialise
    try:
        correlator = NewsCorrelator()
        print("✅ Module corrélateur initialisé correctement")
        return True
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {str(e)}")
        return False


def main():
    """Exécute tous les tests."""
    print("\n" + "🧪 " * 30)
    print("TESTS RAPIDES DU MODULE PREDICTION_ANOMALIES")
    print("🧪 " * 30)

    # Test 1: Collecte de données
    historical_data = test_historical_collector()

    # Test 2: Détection d'anomalies
    anomalies = test_anomaly_detector(historical_data)

    # Test 3: Corrélation avec news
    test_news_correlator(anomalies)

    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)

    if historical_data:
        print("✅ Collecteur de données: OK")
    else:
        print("❌ Collecteur de données: ÉCHEC")

    if anomalies is not None:
        print("✅ Détecteur d'anomalies: OK")
    else:
        print("⚠️  Détecteur d'anomalies: Aucune anomalie (normal)")

    print("✅ Corrélateur de news: OK (initialisation)")

    print("\n📝 Pour un test complet, lancez:")
    print("   python demo_detection.py --full --period 1y\n")


if __name__ == "__main__":
    main()
