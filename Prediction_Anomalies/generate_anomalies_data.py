#!/usr/bin/env python3
"""
Génère un fichier JSON pour le dashboard à partir des CSV de la pipeline.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime


def load_anomalies_with_news():
    """Charge les anomalies avec leurs news depuis les CSV."""

    # Chemins des fichiers
    anomalies_file = Path("data/anomalies/anomalies_detected.csv")
    news_file = Path("data/news/anomalies_with_news_newsapi.csv")

    if not anomalies_file.exists():
        print(f"❌ Fichier introuvable: {anomalies_file}")
        return None

    if not news_file.exists():
        print(f"❌ Fichier introuvable: {news_file}")
        return None

    # Charger les DataFrames
    anomalies_df = pd.read_csv(anomalies_file)
    news_df = pd.read_csv(news_file)

    # Nettoyer les dates
    anomalies_df['date'] = pd.to_datetime(anomalies_df['date'], utc=True).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
    news_df['anomaly_date'] = pd.to_datetime(news_df['anomaly_date'], utc=True).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
    news_df['date'] = pd.to_datetime(news_df['date'], utc=True).dt.tz_localize(None).dt.strftime('%Y-%m-%d')

    # Calculer les stats globales
    total_anomalies = len(anomalies_df)
    severity_counts = anomalies_df['severity'].value_counts().to_dict()

    # Anomalies avec news (depuis news_df)
    unique_anomalies_with_news = news_df.groupby(['anomaly_date', 'asset']).size()
    anomalies_with_news_count = len(unique_anomalies_with_news)

    total_news = len(news_df)
    avg_score = news_df['relevance_score'].mean() if len(news_df) > 0 else 0

    stats = {
        "Anomalies détectées": str(total_anomalies),
        "Avec news": str(anomalies_with_news_count),
        "News trouvées": str(total_news),
        "Score moyen": f"{avg_score:.1f}/100"
    }

    # Construire la liste des anomalies
    anomalies_list = []

    # Grouper les news par anomalie
    for _, anomaly_row in anomalies_df.iterrows():
        anomaly_date = anomaly_row['date']
        asset = anomaly_row['asset']

        # Trouver les news pour cette anomalie
        matching_news = news_df[
            (news_df['anomaly_date'] == anomaly_date) &
            (news_df['asset'] == asset)
        ]

        # Prendre uniquement la meilleure news (score max)
        top_news_list = []
        if len(matching_news) > 0:
            best_news = matching_news.nlargest(1, 'relevance_score').iloc[0]

            # Formater le timing
            days_diff = int(best_news['days_before_anomaly'])
            if days_diff > 0:
                timing_text = f"{days_diff} jour(s) avant"
            elif days_diff == 0:
                timing_text = "Le même jour"
            else:
                timing_text = f"{abs(days_diff)} jour(s) après"

            top_news_list = [{
                "timing": f"{best_news['date']} | {timing_text}",
                "score": int(best_news['relevance_score']),
                "title": str(best_news['title']),
                "description": str(best_news['description'])[:200] + "..." if pd.notna(best_news['description']) and len(str(best_news['description'])) > 200 else str(best_news['description']),
                "source": str(best_news['source']),
                "url": str(best_news['url'])
            }]

        anomaly_obj = {
            "title": f"{asset} - {anomaly_date}",
            "severity": anomaly_row['severity'],
            "variation": f"{anomaly_row['variation_pct']:.2f}%",
            "news_count": len(matching_news),
            "top_news": top_news_list
        }

        anomalies_list.append(anomaly_obj)

    # Trier par date décroissante
    anomalies_list = sorted(
        anomalies_list,
        key=lambda x: x['title'].split(' - ')[1],
        reverse=True
    )

    # Construire le JSON final
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
        "severity_breakdown": severity_counts,
        "anomalies": anomalies_list
    }

    return report


def main():
    """Point d'entrée principal."""
    print("🔄 Génération du fichier JSON pour le dashboard...")

    report = load_anomalies_with_news()

    if report is None:
        print("❌ Échec de la génération")
        return False

    # Sauvegarder le JSON
    output_file = Path("reports/anomaly_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré: {output_file}")
    print(f"   - {len(report['anomalies'])} anomalies")
    print(f"   - {report['stats']['News trouvées']} news")
    print(f"   - Score moyen: {report['stats']['Score moyen']}")

    return True


if __name__ == "__main__":
    main()
