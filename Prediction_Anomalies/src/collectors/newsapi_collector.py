"""
Collecteur de news intelligent via NewsAPI
Utilise des filtres intelligents basés sur le type d'actif et le secteur
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()


class NewsAPICollector:
    """
    Collecteur de news via NewsAPI avec filtres intelligents.
    Génère automatiquement des requêtes pertinentes selon le type d'actif.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le collecteur NewsAPI.

        Args:
            api_key: Clé API NewsAPI (si None, cherche dans .env)
        """
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")

        if not self.api_key:
            raise ValueError(
                "Clé API NewsAPI manquante. "
                "Définissez NEWSAPI_KEY dans .env ou passez-la en paramètre."
            )

        self.base_url = "https://newsapi.org/v2/everything"

        # Mapping actif -> mots-clés intelligents
        self.asset_keywords = self._build_asset_keywords()

        # Mots-clés macro qui impactent tout
        self.macro_keywords = [
            "Federal Reserve", "interest rate", "inflation", "recession",
            "economic crisis", "market crash", "stock market", "wall street",
            "central bank", "monetary policy", "trade war", "tariffs",
            "geopolitical", "war", "pandemic", "lockdown", "GDP"
        ]

    def _build_asset_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Construit un mapping intelligent actif -> mots-clés.

        Returns:
            Dict avec structure: {
                "APPLE": {
                    "specific": ["Apple", "iPhone", "Tim Cook"],
                    "sector": ["tech", "technology", "smartphone"],
                    "competitors": ["Samsung", "Google Android"]
                },
                ...
            }
        """
        keywords = {
            # Indices
            "SP 500": {
                "specific": ["S&P 500", "SPX", "US stock market", "Wall Street"],
                "sector": ["US economy", "American market", "Dow Jones"],
                "macro": True
            },
            "CAC40": {
                "specific": ["CAC 40", "CAC40", "Paris stock market", "Euronext"],
                "sector": ["French economy", "France market"],
                "macro": True
            },
            "GER30": {
                "specific": ["DAX", "German stock market", "Frankfurt"],
                "sector": ["German economy", "Germany market"],
                "macro": True
            },

            # Tech
            "APPLE": {
                "specific": ["Apple Inc", "iPhone", "Tim Cook", "AAPL"],
                "sector": ["tech sector", "smartphone", "consumer electronics"],
                "competitors": ["Samsung", "Google", "Microsoft"]
            },
            "AMAZON": {
                "specific": ["Amazon", "AWS", "Jeff Bezos", "Andy Jassy", "AMZN"],
                "sector": ["e-commerce", "cloud computing", "tech sector"],
                "competitors": ["Microsoft Azure", "Google Cloud"]
            },
            "TESLA": {
                "specific": ["Tesla", "Elon Musk", "TSLA", "electric vehicle"],
                "sector": ["EV market", "automotive", "clean energy"],
                "competitors": ["Ford", "GM", "Rivian", "BYD"]
            },

            # Pharma
            "SANOFI": {
                "specific": ["Sanofi", "pharmaceutical"],
                "sector": ["pharma sector", "healthcare", "drug approval"],
                "competitors": ["Pfizer", "Novartis"]
            },

            # Défense/Aérospatial
            "THALES": {
                "specific": ["Thales Group", "defense contractor"],
                "sector": ["defense sector", "aerospace", "military"],
                "competitors": ["Airbus", "Boeing"]
            },
            "AIRBUS": {
                "specific": ["Airbus", "aircraft manufacturer"],
                "sector": ["aerospace", "aviation", "airline"],
                "competitors": ["Boeing", "Embraer"]
            },

            # Luxe
            "LVMH": {
                "specific": ["LVMH", "Louis Vuitton", "Bernard Arnault", "luxury"],
                "sector": ["luxury sector", "fashion", "high-end retail"],
                "competitors": ["Kering", "Hermès"]
            },

            # Énergie
            "TOTALENERGIES": {
                "specific": ["TotalEnergies", "Total", "oil company"],
                "sector": ["energy sector", "oil", "gas", "petroleum"],
                "competitors": ["Shell", "BP", "ExxonMobil"]
            },
            "ENGIE": {
                "specific": ["Engie", "utility company"],
                "sector": ["energy sector", "gas", "electricity", "renewable"],
                "competitors": ["EDF"]
            },

            # Hôtellerie
            "INTERCONT HOTELS": {
                "specific": ["InterContinental", "IHG", "hotel"],
                "sector": ["hospitality", "tourism", "hotel industry"],
                "competitors": ["Marriott", "Hilton"]
            },

            # Automobile
            "STELLANTIS": {
                "specific": ["Stellantis", "Peugeot", "Fiat", "Chrysler"],
                "sector": ["automotive", "car manufacturer", "auto industry"],
                "competitors": ["Volkswagen", "Toyota"]
            },

            # Matières premières
            "OIL": {
                "specific": ["crude oil", "oil price", "WTI", "Brent"],
                "sector": ["energy market", "OPEC", "petroleum"],
                "macro": True
            },
            "GOLD": {
                "specific": ["gold price", "precious metal", "bullion"],
                "sector": ["commodity", "safe haven"],
                "macro": True
            },
            "GAS": {
                "specific": ["natural gas", "gas price", "LNG"],
                "sector": ["energy market", "commodity"],
                "macro": True
            }
        }

        return keywords

    def _build_query_for_asset(
        self,
        asset: str,
        include_macro: bool = True,
        max_keywords: int = 10
    ) -> str:
        """
        Construit une requête intelligente pour un actif.

        Args:
            asset: Nom de l'actif
            include_macro: Inclure les mots-clés macro
            max_keywords: Nombre max de mots-clés

        Returns:
            Requête optimisée pour NewsAPI
        """
        if asset not in self.asset_keywords:
            # Fallback: utiliser le nom de l'actif
            return f'"{asset}"'

        keywords_config = self.asset_keywords[asset]
        query_parts = []

        # Mots-clés spécifiques (priorité)
        specific = keywords_config.get("specific", [])
        for kw in specific[:3]:  # Max 3 mots-clés spécifiques
            query_parts.append(f'"{kw}"')

        # Mots-clés sectoriels
        sector = keywords_config.get("sector", [])
        if sector and len(query_parts) < max_keywords:
            query_parts.append(f'"{sector[0]}"')

        # Pour les indices et matières premières, ajouter mots-clés macro
        if include_macro and keywords_config.get("macro", False):
            # Ajouter quelques mots-clés macro pertinents
            macro_subset = [
                "economic crisis", "market volatility", "central bank"
            ]
            for kw in macro_subset[:2]:
                if len(query_parts) < max_keywords:
                    query_parts.append(f'"{kw}"')

        # Joindre avec OR
        return " OR ".join(query_parts)

    def collect_news_for_anomaly(
        self,
        asset: str,
        date: str,
        window_before: int = 2,
        window_after: int = 1,
        language: str = "en",
        page_size: int = 20
    ) -> pd.DataFrame:
        """
        Collecte les news pour une anomalie spécifique.

        Args:
            asset: Nom de l'actif (ex: "APPLE")
            date: Date de l'anomalie (YYYY-MM-DD)
            window_before: Jours avant l'anomalie
            window_after: Jours après l'anomalie
            language: Langue des articles (en, fr)
            page_size: Nombre d'articles à récupérer (max 100)

        Returns:
            DataFrame des articles
        """
        # Calculer la fenêtre temporelle
        anomaly_date = pd.to_datetime(date)
        from_date = (anomaly_date - timedelta(days=window_before)).strftime("%Y-%m-%d")
        to_date = (anomaly_date + timedelta(days=window_after)).strftime("%Y-%m-%d")

        # Construire la requête
        query = self._build_query_for_asset(asset, include_macro=True)

        # Paramètres de la requête
        params = {
            "apiKey": self.api_key,
            "q": query,
            "from": from_date,
            "to": to_date,
            "language": language,
            "sortBy": "relevancy",  # Tri par pertinence
            "pageSize": min(page_size, 100)  # NewsAPI limite à 100
        }

        print(f"  Recherche news pour {asset}...")
        print(f"    Requête: {query[:100]}...")
        print(f"    Période: {from_date} à {to_date}")

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data["status"] != "ok":
                print(f"    ⚠️  Erreur API: {data.get('message', 'Unknown')}")
                return pd.DataFrame()

            articles = data.get("articles", [])

            if not articles:
                print(f"    ⚠️  Aucun article trouvé")
                return pd.DataFrame()

            print(f"    ✓ {len(articles)} articles trouvés")

            # Convertir en DataFrame
            df = pd.DataFrame([
                {
                    "date": pd.to_datetime(article["publishedAt"]),
                    "title": article["title"],
                    "description": article.get("description", ""),
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "asset": asset,
                    "anomaly_date": anomaly_date,
                    "query_used": query
                }
                for article in articles
            ])

            return df

        except requests.exceptions.RequestException as e:
            print(f"    ❌ Erreur réseau: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            print(f"    ❌ Erreur: {str(e)}")
            return pd.DataFrame()

    def collect_news_for_anomalies(
        self,
        anomalies_df: pd.DataFrame,
        window_before: int = 2,
        window_after: int = 1,
        delay: float = 1.0,
        max_anomalies: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Collecte les news pour plusieurs anomalies.

        Args:
            anomalies_df: DataFrame des anomalies
            window_before: Jours avant
            window_after: Jours après
            delay: Délai entre requêtes (secondes)
            max_anomalies: Limite le nombre d'anomalies (pour tests)

        Returns:
            DataFrame consolidé de tous les articles
        """
        if anomalies_df.empty:
            print("⚠️  Aucune anomalie à traiter")
            return pd.DataFrame()

        print(f"\n📰 Collecte de news via NewsAPI...")
        print(f"   Fenêtre: {window_before} jours avant, {window_after} jour(s) après")
        print(f"   Délai entre requêtes: {delay}s")
        print("="*60)

        # Limiter si nécessaire
        if max_anomalies:
            anomalies_df = anomalies_df.head(max_anomalies)
            print(f"⚠️  Limité aux {max_anomalies} premières anomalies")

        all_news = []

        for idx, anomaly in anomalies_df.iterrows():
            asset = anomaly["asset"]
            date = anomaly["date"]

            # Collecter les news
            news_df = self.collect_news_for_anomaly(
                asset=asset,
                date=str(date),
                window_before=window_before,
                window_after=window_after
            )

            if not news_df.empty:
                # Ajouter infos de l'anomalie
                news_df["anomaly_variation"] = anomaly["variation_pct"]
                news_df["anomaly_severity"] = anomaly["severity"]
                all_news.append(news_df)

            # Délai pour respecter rate limiting
            if idx < len(anomalies_df) - 1:  # Pas de délai après la dernière
                time.sleep(delay)

        if not all_news:
            print("\n⚠️  Aucune news collectée")
            return pd.DataFrame()

        # Concaténer tous les résultats
        result_df = pd.concat(all_news, ignore_index=True)

        # Dédupliquer par URL
        result_df = result_df.drop_duplicates(subset=["url"])

        print("="*60)
        print(f"✅ {len(result_df)} articles uniques collectés")
        print(f"   Anomalies avec news: {result_df['asset'].nunique()}")
        print()

        return result_df

    def calculate_relevance_score(
        self,
        news_df: pd.DataFrame,
        asset: str
    ) -> pd.DataFrame:
        """
        Calcule un score de pertinence pour chaque article.

        Args:
            news_df: DataFrame des news
            asset: Nom de l'actif

        Returns:
            DataFrame avec colonne "relevance_score"
        """
        if news_df.empty:
            return news_df

        news_df = news_df.copy()
        news_df["relevance_score"] = 0.0

        # Récupérer les mots-clés pour cet actif
        if asset not in self.asset_keywords:
            news_df["relevance_score"] = 50.0  # Score par défaut
            return news_df

        keywords_config = self.asset_keywords[asset]

        for idx, row in news_df.iterrows():
            score = 0.0
            title = row.get("title") or ""
            description = row.get("description") or ""
            text = (title + " " + description).lower()

            # Mots-clés spécifiques: +30 points par match
            for kw in keywords_config.get("specific", []):
                if kw.lower() in text:
                    score += 30

            # Mots-clés sectoriels: +15 points par match
            for kw in keywords_config.get("sector", []):
                if kw.lower() in text:
                    score += 15

            # Mots-clés compétiteurs: +10 points par match
            for kw in keywords_config.get("competitors", []):
                if kw.lower() in text:
                    score += 10

            # Mots-clés macro: +5 points par match
            for kw in self.macro_keywords:
                if kw.lower() in text:
                    score += 5

            # Bonus si dans le titre (x1.5)
            if any(kw.lower() in row["title"].lower()
                   for kw in keywords_config.get("specific", [])):
                score *= 1.5

            # Score minimum/maximum
            score = max(10.0, min(score, 100.0))

            news_df.at[idx, "relevance_score"] = round(score, 1)

        # Trier par score décroissant
        news_df = news_df.sort_values("relevance_score", ascending=False)

        return news_df


if __name__ == "__main__":
    # Test rapide
    import sys

    # Vérifier la clé API
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("❌ Clé API NewsAPI manquante")
        print("   Ajoutez NEWSAPI_KEY dans .env")
        print("   Obtenez une clé gratuite sur: https://newsapi.org/")
        sys.exit(1)

    collector = NewsAPICollector(api_key)

    # Test sur une anomalie fictive
    print("🧪 Test du collecteur NewsAPI\n")

    test_anomaly = {
        "asset": "APPLE",
        "date": "2025-04-21",  # Date d'une vraie anomalie détectée
        "variation_pct": -19.2,
        "severity": "Critical"
    }

    news_df = collector.collect_news_for_anomaly(
        asset=test_anomaly["asset"],
        date=test_anomaly["date"],
        window_before=2,
        window_after=1
    )

    if not news_df.empty:
        # Calculer les scores
        news_df = collector.calculate_relevance_score(news_df, test_anomaly["asset"])

        print("\n📊 Top 5 des articles les plus pertinents:")
        print("="*60)
        for idx, row in news_df.head(5).iterrows():
            print(f"\n{row['title']}")
            print(f"   Source: {row['source']}")
            print(f"   Score: {row['relevance_score']}")
            print(f"   URL: {row['url'][:60]}...")
    else:
        print("⚠️  Aucune news trouvée pour ce test")
