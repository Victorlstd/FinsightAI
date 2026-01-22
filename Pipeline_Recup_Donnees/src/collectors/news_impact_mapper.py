"""
Mappage intelligent entre événements macro/sectoriels et actifs financiers
Système de scoring pour déterminer la pertinence d'une news pour un actif
"""
import yaml
from pathlib import Path
from typing import List, Dict, Set, Tuple
from loguru import logger


class NewsImpactMapper:
    """
    Cartographie l'impact potentiel des news sur les actifs financiers
    """

    def __init__(self, config_path: str = "./config/news_strategy.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.asset_sensitivity_map = self._build_sensitivity_map()
        self.event_keywords_map = self._build_event_keywords_map()

    def _load_config(self) -> dict:
        """Charge la configuration de stratégie de news"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _build_sensitivity_map(self) -> Dict[str, Dict]:
        """
        Construit une map de sensibilité pour chaque actif
        Returns: {asset_name: {sensitivity_factors, sector, type}}
        """
        sensitivity_map = {}

        # Indices
        for asset in self.config['assets'].get('indices', []):
            sensitivity_map[asset['name']] = {
                'sensitivity': set(asset.get('sensitivity', [])),
                'type': 'index',
                'sector': 'index',
                'region': asset.get('region', 'global')
            }

        # Stocks
        for asset in self.config['assets'].get('stocks', []):
            sensitivity_map[asset['name']] = {
                'sensitivity': set(asset.get('sensitivity', [])),
                'type': 'stock',
                'sector': asset.get('sector', 'unknown'),
                'region': asset.get('region', 'global')
            }

        # Commodities
        for asset in self.config['assets'].get('commodities', []):
            sensitivity_map[asset['name']] = {
                'sensitivity': set(asset.get('sensitivity', [])),
                'type': 'commodity',
                'sector': 'commodity',
                'region': 'global'
            }

        logger.info(f"Sensitivity map construit pour {len(sensitivity_map)} actifs")
        return sensitivity_map

    def _build_event_keywords_map(self) -> Dict[str, Dict]:
        """
        Construit la map des événements avec leurs keywords
        Returns: {event_name: {keywords, impact_score, affects}}
        """
        event_map = {}

        # Événements macro
        for event_name, event_data in self.config.get('macro_events', {}).items():
            event_map[event_name] = {
                'keywords': set([kw.lower() for kw in event_data.get('keywords', [])]),
                'gdelt_themes': event_data.get('gdelt_themes', []),
                'impact_score': event_data.get('impact_score', 5),
                'affects': event_data.get('affects', []),
                'type': 'macro'
            }

        # Événements sectoriels
        for event_name, event_data in self.config.get('sector_events', {}).items():
            event_map[event_name] = {
                'keywords': set([kw.lower() for kw in event_data.get('keywords', [])]),
                'impact_score': event_data.get('impact_score', 5),
                'affects': event_data.get('affects', []),
                'type': 'sector'
            }

        logger.info(f"Event keywords map construit avec {len(event_map)} types d'événements")
        return event_map

    def compute_relevance_score(
        self,
        news_title: str,
        news_content: str,
        asset_name: str
    ) -> Tuple[float, List[str]]:
        """
        Calcule le score de pertinence d'une news pour un actif donné

        Args:
            news_title: Titre de la news
            news_content: Contenu de la news (peut être vide)
            asset_name: Nom de l'actif (ex: "APPLE", "SP500")

        Returns:
            (score, matched_events): Score de pertinence et événements détectés
        """
        if asset_name not in self.asset_sensitivity_map:
            logger.warning(f"Actif inconnu: {asset_name}")
            return 0.0, []

        asset_info = self.asset_sensitivity_map[asset_name]
        text = (news_title + " " + news_content).lower()

        total_score = 0.0
        matched_events = []

        # Analyser chaque type d'événement
        for event_name, event_data in self.event_keywords_map.items():
            # Compter les keywords matchés (les keywords sont déjà en lowercase)
            # Utiliser une approche plus flexible : chercher si au moins 60% des mots du keyword sont présents
            matched_keywords = []
            for kw in event_data['keywords']:
                # Pour les phrases courtes (1-2 mots), chercher exactement
                kw_words = kw.split()
                if len(kw_words) <= 2:
                    if kw in text:
                        matched_keywords.append(kw)
                else:
                    # Pour les phrases longues, vérifier si 60% des mots sont présents
                    words_found = sum(1 for word in kw_words if word in text)
                    if words_found / len(kw_words) >= 0.6:
                        matched_keywords.append(kw)

            if not matched_keywords:
                continue

            # Calculer le score pour cet événement
            # Nouvelle formule : nombre de keywords matchés * impact de base
            # Au lieu d'un ratio, on compte le nombre absolu de matches
            keyword_count = len(matched_keywords)
            base_impact = event_data['impact_score']

            # Vérifier si l'événement affecte cet actif
            affects = event_data['affects']

            # Événement macro qui affecte tout
            if 'all' in affects:
                # Score = nombre de keywords * impact de base
                event_score = base_impact * keyword_count
                total_score += event_score
                matched_events.append(event_name)

            # Événement sectoriel
            elif event_data['type'] == 'sector':
                # Vérifie si l'actif est dans la liste des affectés
                if asset_name in affects:
                    event_score = base_impact * keyword_count * 1.2  # Bonus pour match direct
                    total_score += event_score
                    matched_events.append(event_name)
                # Ou si le secteur correspond
                elif asset_info['sector'] + '_sector' in asset_info['sensitivity']:
                    event_score = base_impact * keyword_count * 0.8
                    total_score += event_score
                    matched_events.append(event_name)

            # Vérifier la sensibilité spécifique de l'actif
            sensitivity_match = any(
                sens in event_name for sens in asset_info['sensitivity']
            )
            if sensitivity_match:
                total_score *= 1.3  # Bonus de sensibilité

        return round(total_score, 2), matched_events

    def get_relevant_assets_for_news(
        self,
        news_title: str,
        news_content: str = "",
        min_score: float = 5.0
    ) -> List[Tuple[str, float, List[str]]]:
        """
        Détermine quels actifs sont potentiellement impactés par une news

        Args:
            news_title: Titre de la news
            news_content: Contenu de la news
            min_score: Score minimum de pertinence

        Returns:
            Liste de (asset_name, score, matched_events) triée par score décroissant
        """
        results = []

        for asset_name in self.asset_sensitivity_map.keys():
            score, matched_events = self.compute_relevance_score(
                news_title, news_content, asset_name
            )

            if score >= min_score:
                results.append((asset_name, score, matched_events))

        # Trier par score décroissant
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_macro_event_queries(self) -> List[Dict]:
        """
        Génère la liste des requêtes pour les événements macro
        Returns: Liste de {query, type, impact_score, gdelt_themes}
        """
        queries = []

        for event_name, event_data in self.event_keywords_map.items():
            if event_data['type'] == 'macro':
                # Créer une requête pour chaque groupe de keywords
                keywords = list(event_data['keywords'])

                # Grouper par 3-5 keywords pour des requêtes efficaces
                for i in range(0, len(keywords), 3):
                    query_keywords = keywords[i:i+3]
                    queries.append({
                        'query': ' OR '.join(f'"{kw}"' for kw in query_keywords),
                        'event_type': event_name,
                        'impact_score': event_data['impact_score'],
                        'gdelt_themes': event_data.get('gdelt_themes', []),
                        'type': 'macro'
                    })

        return queries

    def get_sector_event_queries(self) -> List[Dict]:
        """
        Génère la liste des requêtes pour les événements sectoriels
        Returns: Liste de {query, type, sector, affects}
        """
        queries = []

        for event_name, event_data in self.event_keywords_map.items():
            if event_data['type'] == 'sector':
                keywords = list(event_data['keywords'])

                # Grouper par 3-5 keywords
                for i in range(0, len(keywords), 3):
                    query_keywords = keywords[i:i+3]
                    queries.append({
                        'query': ' OR '.join(f'"{kw}"' for kw in query_keywords),
                        'event_type': event_name,
                        'impact_score': event_data['impact_score'],
                        'affects': event_data['affects'],
                        'type': 'sector'
                    })

        return queries

    def get_all_assets(self) -> List[str]:
        """Retourne la liste de tous les actifs configurés"""
        return list(self.asset_sensitivity_map.keys())

    def get_assets_by_type(self, asset_type: str) -> List[str]:
        """
        Retourne les actifs d'un type donné
        Args:
            asset_type: 'index', 'stock', 'commodity'
        """
        return [
            name for name, info in self.asset_sensitivity_map.items()
            if info['type'] == asset_type
        ]

    def get_assets_by_sector(self, sector: str) -> List[str]:
        """Retourne les actifs d'un secteur donné"""
        return [
            name for name, info in self.asset_sensitivity_map.items()
            if info['sector'] == sector
        ]

    def explain_relevance(
        self,
        news_title: str,
        asset_name: str,
        score: float,
        matched_events: List[str]
    ) -> str:
        """
        Génère une explication textuelle de la pertinence
        """
        if score == 0:
            return f"Aucune pertinence détectée pour {asset_name}"

        asset_info = self.asset_sensitivity_map[asset_name]
        explanation = f"Pertinence pour {asset_name} (score: {score}):\n"
        explanation += f"  Type: {asset_info['type']}, Secteur: {asset_info['sector']}\n"
        explanation += f"  Événements détectés: {', '.join(matched_events)}\n"

        return explanation


if __name__ == "__main__":
    # Test du mapper
    from src.utils.logger import setup_logger

    setup_logger()

    mapper = NewsImpactMapper()

    # Test 1: News sur l'inflation
    print("\n" + "="*80)
    print("TEST 1: News sur l'inflation")
    print("="*80)
    news_title = "Federal Reserve raises interest rates to combat inflation"
    assets = mapper.get_relevant_assets_for_news(news_title, min_score=5.0)

    print(f"\nNews: {news_title}")
    print(f"\nActifs impactés (score >= 5.0):")
    for asset, score, events in assets[:10]:
        print(f"  - {asset:20s} | Score: {score:5.1f} | Événements: {', '.join(events)}")

    # Test 2: News sur le pétrole
    print("\n" + "="*80)
    print("TEST 2: News sur le pétrole")
    print("="*80)
    news_title = "OPEC announces production cuts amid Middle East tensions"
    assets = mapper.get_relevant_assets_for_news(news_title, min_score=5.0)

    print(f"\nNews: {news_title}")
    print(f"\nActifs impactés (score >= 5.0):")
    for asset, score, events in assets[:10]:
        print(f"  - {asset:20s} | Score: {score:5.1f} | Événements: {', '.join(events)}")

    # Test 3: News sur l'IA
    print("\n" + "="*80)
    print("TEST 3: News sur la régulation de l'IA")
    print("="*80)
    news_title = "EU approves strict AI regulation law affecting big tech companies"
    assets = mapper.get_relevant_assets_for_news(news_title, min_score=5.0)

    print(f"\nNews: {news_title}")
    print(f"\nActifs impactés (score >= 5.0):")
    for asset, score, events in assets[:10]:
        print(f"  - {asset:20s} | Score: {score:5.1f} | Événements: {', '.join(events)}")

    # Test 4: Afficher les requêtes macro
    print("\n" + "="*80)
    print("REQUÊTES MACRO GÉNÉRÉES")
    print("="*80)
    macro_queries = mapper.get_macro_event_queries()
    print(f"\nNombre de requêtes macro: {len(macro_queries)}")
    for i, q in enumerate(macro_queries[:5], 1):
        print(f"{i}. {q['event_type']:30s} | {q['query'][:60]}...")
