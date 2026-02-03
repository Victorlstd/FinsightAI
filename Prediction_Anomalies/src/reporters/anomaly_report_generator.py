"""
Générateur de rapports visuels pour les anomalies et leurs news associées.
Crée des documents HTML et Markdown lisibles pour vérifier les corrélations.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional


class AnomalyReportGenerator:
    """
    Génère des rapports visuels des anomalies avec leurs news.
    """

    def __init__(self, output_dir: str = "reports"):
        """
        Initialise le générateur de rapports.

        Args:
            output_dir: Répertoire de sauvegarde des rapports
        """
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(
        self,
        correlations_df: pd.DataFrame,
        anomalies_df: pd.DataFrame,
        output_file: str = "anomaly_report.md"
    ) -> str:
        """
        Génère un rapport Markdown lisible.

        Args:
            correlations_df: DataFrame des corrélations
            anomalies_df: DataFrame des anomalies
            output_file: Nom du fichier de sortie

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / output_file

        with open(filepath, 'w', encoding='utf-8') as f:
            # En-tête
            f.write("# 📊 Rapport d'Analyse des Anomalies Boursières\n\n")
            f.write(f"**Date de génération** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Statistiques globales
            f.write("## 📈 Statistiques Globales\n\n")
            f.write(f"- **Total d'anomalies détectées** : {len(anomalies_df)}\n")

            if not correlations_df.empty:
                unique_with_news = len(correlations_df[['asset', 'anomaly_date']].drop_duplicates())
                f.write(f"- **Anomalies avec news** : {unique_with_news}\n")
                f.write(f"- **Total de news trouvées** : {len(correlations_df)}\n")
                f.write(f"- **Score de pertinence moyen** : {correlations_df['relevance_score'].mean():.1f}/100\n")

            # Par sévérité
            f.write("\n### Répartition par sévérité\n\n")
            severity_counts = anomalies_df['severity'].value_counts()
            for severity, count in severity_counts.items():
                emoji = self._get_severity_emoji(severity)
                f.write(f"- {emoji} **{severity}** : {count}\n")

            f.write("\n---\n\n")

            # Anomalies avec news
            if not correlations_df.empty:
                f.write("## 🔍 Anomalies Détectées avec News Corrélées\n\n")

                # Grouper par anomalie
                grouped = correlations_df.groupby(['asset', 'anomaly_date', 'anomaly_variation', 'anomaly_severity'])

                anomaly_num = 1
                for (asset, date, variation, severity), group in grouped:
                    f.write(f"### {anomaly_num}. {asset} - {pd.to_datetime(date).strftime('%Y-%m-%d')}\n\n")

                    # Détails de l'anomalie
                    emoji = self._get_severity_emoji(severity)
                    f.write(f"**{emoji} Sévérité** : {severity}\n\n")
                    f.write(f"**📉 Variation** : {variation:.2f}%\n\n")

                    # News associées
                    f.write(f"**📰 News trouvées** : {len(group)}\n\n")

                    # Meilleure news uniquement
                    top_news = group.nlargest(1, 'relevance_score')

                    f.write("#### 🏆 News la plus pertinente\n\n")

                    for idx, news in top_news.iterrows():
                        news_date = pd.to_datetime(news['date']).strftime('%Y-%m-%d')
                        days_diff = news['days_before_anomaly']

                        if days_diff > 0:
                            timing = f"**{days_diff} jour(s) avant**"
                        elif days_diff == 0:
                            timing = "**Le même jour**"
                        else:
                            timing = f"**{abs(days_diff)} jour(s) après**"

                        f.write(f"##### {news_date} | Score: {news['relevance_score']:.0f}/100 | {timing}\n\n")
                        f.write(f"**Titre** : {news['title']}\n\n")

                        if pd.notna(news.get('description', '')) and news.get('description', ''):
                            desc = news['description'][:200] + "..." if len(news['description']) > 200 else news['description']
                            f.write(f"**Description** : {desc}\n\n")

                        f.write(f"**Source** : {news['source']}\n\n")
                        f.write(f"**Lien** : [{news['url']}]({news['url']})\n\n")
                        f.write("---\n\n")

                    anomaly_num += 1
                    f.write("\n")

            # Anomalies sans news
            if not correlations_df.empty:
                anomalies_with_news_ids = set(
                    zip(correlations_df['asset'], correlations_df['anomaly_date'].astype(str))
                )
                anomalies_ids = set(
                    zip(anomalies_df['asset'], anomalies_df['date'].astype(str))
                )
                anomalies_without_news = anomalies_ids - anomalies_with_news_ids

                if anomalies_without_news:
                    f.write("## ⚠️ Anomalies Sans News Trouvées\n\n")
                    f.write(f"*{len(anomalies_without_news)} anomalie(s) détectée(s) mais aucune news pertinente trouvée*\n\n")

                    for asset, date in list(anomalies_without_news)[:10]:  # Limiter à 10
                        anomaly = anomalies_df[
                            (anomalies_df['asset'] == asset) &
                            (anomalies_df['date'].astype(str) == date)
                        ].iloc[0]

                        f.write(f"- **{asset}** ({date}) : {anomaly['variation_pct']:.2f}% ({anomaly['severity']})\n")

            # Footer
            f.write("\n\n---\n\n")
            f.write("*Rapport généré automatiquement par prediction_Anomalies v2.0*\n")

        print(f"✅ Rapport Markdown généré: {filepath}")
        return str(filepath)

    def generate_html_report(
        self,
        correlations_df: pd.DataFrame,
        anomalies_df: pd.DataFrame,
        output_file: str = "anomaly_report.html"
    ) -> str:
        """
        Génère un rapport HTML interactif.

        Args:
            correlations_df: DataFrame des corrélations
            anomalies_df: DataFrame des anomalies
            output_file: Nom du fichier de sortie

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / output_file

        with open(filepath, 'w', encoding='utf-8') as f:
            # En-tête HTML
            f.write("""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'Analyse des Anomalies Boursières</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #2c3e50;
            background-color: #ecf0f1;
            padding: 10px;
            border-radius: 5px;
        }
        .stats {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-box {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .anomaly-card {
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .anomaly-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        .severity-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .severity-minor { background-color: #f39c12; }
        .severity-moderate { background-color: #e67e22; }
        .severity-severe { background-color: #e74c3c; }
        .severity-critical { background-color: #c0392b; }
        .news-item {
            background-color: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }
        .news-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .news-score {
            background-color: #3498db;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        .news-timing {
            color: #7f8c8d;
            font-style: italic;
        }
        .news-title {
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }
        .news-description {
            color: #555;
            margin: 10px 0;
        }
        .news-source {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
""")

            # Titre
            f.write(f"""
    <h1>📊 Rapport d'Analyse des Anomalies Boursières</h1>
    <p><strong>Date de génération :</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
""")

            # Statistiques globales
            f.write("""
    <div class="stats">
        <h2>📈 Statistiques Globales</h2>
        <div class="stats-grid">
""")

            f.write(f"""
            <div class="stat-box">
                <div class="stat-number">{len(anomalies_df)}</div>
                <div>Anomalies détectées</div>
            </div>
""")

            if not correlations_df.empty:
                unique_with_news = len(correlations_df[['asset', 'anomaly_date']].drop_duplicates())
                f.write(f"""
            <div class="stat-box">
                <div class="stat-number">{unique_with_news}</div>
                <div>Avec news</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(correlations_df)}</div>
                <div>News trouvées</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{correlations_df['relevance_score'].mean():.0f}/100</div>
                <div>Score moyen</div>
            </div>
""")

            f.write("""
        </div>
    </div>
""")

            # Anomalies avec news
            if not correlations_df.empty:
                f.write("<h2>🔍 Anomalies Détectées avec News Corrélées</h2>")

                grouped = correlations_df.groupby(['asset', 'anomaly_date', 'anomaly_variation', 'anomaly_severity'])

                for (asset, date, variation, severity), group in grouped:
                    severity_class = f"severity-{severity.lower()}"
                    date_str = pd.to_datetime(date).strftime('%Y-%m-%d')

                    f.write(f"""
    <div class="anomaly-card">
        <div class="anomaly-header">
            <div>
                <h3>{asset} - {date_str}</h3>
            </div>
            <div>
                <span class="severity-badge {severity_class}">{severity}</span>
            </div>
        </div>
        <p><strong>📉 Variation :</strong> {variation:.2f}%</p>
        <p><strong>📰 News trouvées :</strong> {len(group)}</p>
        <h4>🏆 News la plus pertinente</h4>
""")

                    top_news = group.nlargest(1, 'relevance_score')

                    for idx, news in top_news.iterrows():
                        news_date = pd.to_datetime(news['date']).strftime('%Y-%m-%d')
                        days_diff = news['days_before_anomaly']

                        if days_diff > 0:
                            timing = f"{days_diff} jour(s) avant"
                        elif days_diff == 0:
                            timing = "Le même jour"
                        else:
                            timing = f"{abs(days_diff)} jour(s) après"

                        desc = ""
                        if pd.notna(news.get('description', '')) and news.get('description', ''):
                            desc = news['description'][:200] + "..." if len(news['description']) > 200 else news['description']

                        f.write(f"""
        <div class="news-item">
            <div class="news-header">
                <span class="news-timing">{news_date} | {timing}</span>
                <span class="news-score">Score: {news['relevance_score']:.0f}/100</span>
            </div>
            <div class="news-title">{news['title']}</div>
""")
                        if desc:
                            f.write(f"""
            <div class="news-description">{desc}</div>
""")

                        f.write(f"""
            <div class="news-source">
                <strong>Source :</strong> {news['source']} |
                <a href="{news['url']}" target="_blank">Lire l'article →</a>
            </div>
        </div>
""")

                    f.write("    </div>\n")

            # Footer
            f.write("""
    <div class="footer">
        <p><em>Rapport généré automatiquement par prediction_Anomalies v2.0</em></p>
    </div>
</body>
</html>
""")

        print(f"✅ Rapport HTML généré: {filepath}")
        return str(filepath)

    def _get_severity_emoji(self, severity: str) -> str:
        """Retourne l'emoji correspondant à la sévérité."""
        emojis = {
            'Minor': '⚠️',
            'Moderate': '⚠️',
            'Severe': '🔴',
            'Critical': '🔴'
        }
        return emojis.get(severity, '📊')

    def generate_both_reports(
        self,
        correlations_df: pd.DataFrame,
        anomalies_df: pd.DataFrame
    ) -> tuple:
        """
        Génère à la fois le rapport Markdown et HTML.

        Args:
            correlations_df: DataFrame des corrélations
            anomalies_df: DataFrame des anomalies

        Returns:
            Tuple (chemin_md, chemin_html)
        """
        print("\n📝 Génération des rapports...")
        print("="*60)

        md_path = self.generate_markdown_report(correlations_df, anomalies_df)
        html_path = self.generate_html_report(correlations_df, anomalies_df)

        print("="*60)
        print("✅ Rapports générés avec succès !\n")

        return md_path, html_path


if __name__ == "__main__":
    # Test du générateur
    import sys
    from pathlib import Path

    # Charger les données
    anomalies_path = Path(__file__).parent.parent.parent / "data/anomalies/anomalies_detected.csv"
    correlations_path = Path(__file__).parent.parent.parent / "data/news/anomalies_with_news_newsapi.csv"

    if not anomalies_path.exists():
        print("❌ Fichier d'anomalies introuvable")
        print("   Lancez d'abord: python main.py --step detect")
        sys.exit(1)

    anomalies_df = pd.read_csv(anomalies_path, parse_dates=['date'])
    print(f"📊 {len(anomalies_df)} anomalies chargées")

    if not correlations_path.exists():
        print("⚠️  Pas de corrélations trouvées")
        print("   Génération d'un rapport sans news...")
        correlations_df = pd.DataFrame()
    else:
        correlations_df = pd.read_csv(correlations_path, parse_dates=['date', 'anomaly_date'])
        print(f"📰 {len(correlations_df)} corrélations chargées")

    # Générer les rapports
    generator = AnomalyReportGenerator()
    md_path, html_path = generator.generate_both_reports(correlations_df, anomalies_df)

    print(f"\n📄 Fichiers générés:")
    print(f"   • Markdown: {md_path}")
    print(f"   • HTML: {html_path}")
    print(f"\n💡 Ouvrir le rapport: open {html_path}")
