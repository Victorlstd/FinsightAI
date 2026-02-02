#!/usr/bin/env python3
"""
Script simple pour générer un rapport visuel à partir des données existantes.

Usage:
    python generate_report.py
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.reporters.anomaly_report_generator import AnomalyReportGenerator


def main():
    print("\n📊 Génération du Rapport d'Anomalies\n")
    print("="*60)

    # Charger les anomalies
    anomalies_path = Path(__file__).parent / "data/anomalies/anomalies_detected.csv"

    if not anomalies_path.exists():
        print("❌ Fichier d'anomalies introuvable")
        print("   Lancez d'abord: python main.py --step detect")
        sys.exit(1)

    anomalies_df = pd.read_csv(anomalies_path, parse_dates=['date'])
    print(f"✅ {len(anomalies_df)} anomalies chargées")

    # Charger les corrélations (si disponibles)
    correlations_path = Path(__file__).parent / "data/news/anomalies_with_news_newsapi.csv"

    if not correlations_path.exists():
        print("⚠️  Pas de corrélations trouvées")
        print("   Génération d'un rapport sans news...")
        print("   Pour ajouter les news: python main.py --step correlate --max-anomalies 10")
        correlations_df = pd.DataFrame()
    else:
        correlations_df = pd.read_csv(correlations_path, parse_dates=['date', 'anomaly_date'])
        print(f"✅ {len(correlations_df)} corrélations chargées")

    print("="*60)

    # Générer les rapports
    generator = AnomalyReportGenerator()
    md_path, html_path = generator.generate_both_reports(correlations_df, anomalies_df)

    print("\n" + "="*60)
    print("📄 Rapports générés:")
    print(f"   • HTML : {html_path}")
    print(f"   • Markdown : {md_path}")
    print("="*60)

    print(f"\n💡 Commandes utiles:")
    print(f"   • Ouvrir HTML : open {html_path}")
    print(f"   • Lire Markdown : cat {md_path}")
    print()


if __name__ == "__main__":
    main()
