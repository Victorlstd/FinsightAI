# Pipeline de Récupération de Données Financières

Pipeline de collecte et traitement de données pour l'analyse d'impact des événements sur les marchés financiers.

## 🎯 Objectif

Collecter des **événements macro-économiques et sectoriels** qui peuvent impacter les actifs financiers **sans les mentionner directement**, puis les corréler avec les mouvements de marché.

## 📊 Actifs Surveillés

### Indices (3)
- SP500 (US)
- CAC40 (France)
- GER30 (Allemagne)

### Actions (12)
- **Tech**: APPLE, AMAZON, TESLA, CASIC
- **Pharma**: SANOFI
- **Défense/Aérospatial**: THALES, AIRBUS
- **Luxe**: LVMH
- **Énergie**: TOTALENERGIES, ENGIE
- **Hôtellerie**: INTERCONT_HOTELS
- **Automobile**: STELLANTIS

### Matières Premières (3)
- OIL (Pétrole)
- GOLD (Or)
- GAS (Gaz)

## 🚀 Installation

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## 📁 Structure du Projet

```
Pipeline recup Données/
├── config/
│   ├── config.yaml              # Configuration générale
│   └── news_strategy.yaml       # Stratégie de collecte de news
├── src/
│   ├── collectors/
│   │   ├── financial_data_collector.py
│   │   ├── news_collector.py    # Ancien collecteur (déprécié)
│   │   ├── hybrid_news_collector.py  # ✨ Nouveau collecteur hybride
│   │   ├── news_impact_mapper.py     # Système de scoring
│   │   └── social_media_collector.py
│   ├── processors/
│   │   └── correlator.py
│   ├── storage/
│   │   └── database.py
│   └── utils/
│       ├── config_loader.py
│       └── logger.py
├── data/
│   ├── raw/news/
│   │   ├── hybrid_news_raw.csv       # News brutes
│   │   └── hybrid_news_mapped.csv    # News mappées aux actifs
│   └── processed/
├── main_collect_historical.py   # Pipeline principal
├── test_pipeline.py
├── demo_hybrid_news.py          # ✨ Démonstration du nouveau système
└── STRATEGIE_NEWS.md            # Documentation complète de la stratégie

```

## 🎯 Nouveau Système de Collecte de News (Approche Hybride)

### Principe

Au lieu de chercher des news mentionnant directement "Apple" ou "SP500", le système collecte :
- **Événements macro** : Décisions Fed, inflation, géopolitique, etc.
- **Événements sectoriels** : Régulations tech, consommation luxe, prix énergie, etc.

Puis mappe intelligemment chaque news aux actifs qu'elle peut impacter.

### Exemple Concret

**News collectée** :
> "Federal Reserve raises interest rates to combat inflation"

**Mapping automatique** :
- SP500 → Score: 20.0 (impact macro fort)
- CAC40 → Score: 20.0
- APPLE → Score: 20.0
- GOLD → Score: 26.0 (+ bonus sensibilité)
- ... (tous les actifs impactés)

**Avantage** : La news ne mentionne ni Apple ni SP500, mais le système détecte l'impact potentiel !

## 🚀 Utilisation

### 1. Tester le nouveau système de news

```bash
source venv/bin/activate
python demo_hybrid_news.py
```

Cela collecte des news sur une courte période pour démonstration.

### 2. Collecte complète

Pour lancer une collecte sur une longue période :

```python
from src.collectors.hybrid_news_collector import HybridNewsCollector

collector = HybridNewsCollector()

# Collecte + mapping automatique
mapped_news = collector.collect_and_map(
    start_date="2023-01-01",
    end_date="2024-12-31",
    min_relevance_score=5.0,
    max_records_per_query=250,
    delay=2.0
)
```

### 3. Tester la pipeline

```bash
python test_pipeline.py
```

## 📊 Outputs

### News Brutes
`data/raw/news/hybrid_news_raw.csv`
- Titre, URL, date, source
- Type d'événement (monetary_policy, geopolitical_tensions, etc.)
- Catégorie (macro ou sector)

### News Mappées
`data/raw/news/hybrid_news_mapped.csv`
- Toutes les colonnes des news brutes
- **asset** : Actif impacté
- **relevance_score** : Score de pertinence (5-100)
- **matched_events** : Événements détectés

## ⚙️ Configuration

### Personnaliser les événements surveillés

Éditer `config/news_strategy.yaml` :

```yaml
macro_events:
  monetary_policy:
    keywords:
      - "Federal Reserve"
      - "interest rate"
      # Ajoutez vos keywords
    impact_score: 10
    affects: ["all"]
```

### Ajuster le scoring

Dans `src/collectors/news_impact_mapper.py`, modifier la formule de scoring.

## 📚 Documentation

- [STRATEGIE_NEWS.md](STRATEGIE_NEWS.md) - Documentation complète de la stratégie hybride
- `demo_hybrid_news.py` - Code commenté avec exemples

## 🛠️ Technologies

- **Python 3.12**
- **GDELT** - Collecte de news globales
- **yfinance** - Données financières
- **pandas** - Traitement de données
- **SQLAlchemy** - Stockage base de données

## 📈 Résultats de Démonstration

Sur une période de test de 5 jours (15-20 janvier 2024) :
- **58 news uniques** collectées
- **660 associations** news-actifs créées
- **18 actifs** impactés
- Score moyen : 10-12 par actif

Types d'événements détectés :
1. Santé/Pandémie - 324 associations
2. Événements politiques - 162 associations
3. Politique monétaire - 126 associations
4. Consommation luxe - 48 associations


## 📝 Notes

- Le système gère automatiquement le rate-limiting de GDELT
- Les news sont dédupliquées par URL
- Le délai entre requêtes est configurable (défaut: 2 secondes)

## 🤝 Contribution

Pour modifier ou améliorer :
1. Ajuster les keywords dans `config/news_strategy.yaml`
2. Modifier le scoring dans `news_impact_mapper.py`
3. Tester avec `demo_hybrid_news.py`

---

**Version** : 1.0
**Date** : Janvier 2026
**Auteur** : Pipeline de données PFE
