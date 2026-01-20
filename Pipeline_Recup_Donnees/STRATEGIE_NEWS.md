# Stratégie de Collecte de News - Approche Hybride

## 🎯 Objectif

Collecter des **événements macro-économiques et sectoriels** qui peuvent impacter vos actifs **sans les mentionner directement**.

Au lieu de chercher "Apple" ou "SP500", on collecte :
- Décisions de la Fed qui impactent tous les indices
- Tensions géopolitiques qui affectent le pétrole
- Régulations tech qui touchent les GAFA
- Etc.

---

## 📊 Actifs Surveillés

### Indices (3)
- **SP500** (US)
- **CAC40** (France)
- **GER30** (Allemagne)

### Actions (12)
- **Tech**: APPLE, AMAZON, TESLA, CASIC
- **Pharma**: SANOFI
- **Défense/Aérospatial**: THALES, AIRBUS
- **Luxe**: LVMH
- **Énergie**: TOTALENERGIES, ENGIE
- **Hôtellerie**: INTERCONT HOTELS
- **Automobile**: STELLANTIS

### Matières Premières (3)
- **OIL** (Pétrole)
- **GOLD** (Or)
- **GAS** (Gaz)

---

## 🌍 Types d'Événements Collectés

### 1. ÉVÉNEMENTS MACRO (impact global)

#### Politique Monétaire (impact: 10/10)
- Décisions Fed, BCE, BoJ
- Taux d'intérêt
- Inflation
- Quantitative easing

**Exemple**: *"Federal Reserve raises interest rates to combat inflation"*
→ Impacte: **TOUS les actifs**

#### Géopolitique (impact: 9/10)
- Guerres, conflits
- Sanctions internationales
- Tensions commerciales US-Chine
- Crises au Moyen-Orient

**Exemple**: *"OPEC announces production cuts amid Middle East tensions"*
→ Impacte: **Pétrole, Gaz, Énergie, Défense**

#### Crise Bancaire (impact: 10/10)
- Faillites bancaires
- Crises de liquidité
- Défauts souverains

**Exemple**: *"Major bank faces liquidity crisis"*
→ Impacte: **TOUS les actifs**

#### Commerce International (impact: 8/10)
- Tarifs douaniers
- Accords commerciaux
- Restrictions d'import/export

**Exemple**: *"New tariffs announced on European goods"*
→ Impacte: **Indices, Entreprises exportatrices**

### 2. ÉVÉNEMENTS SECTORIELS (impact ciblé)

#### Technology (impact: 8/10)
- Régulations IA
- Antitrust tech
- Privacy laws
- Pénurie semi-conducteurs

**Exemple**: *"EU approves strict AI regulation law affecting big tech"*
→ Impacte: **APPLE, AMAZON, TESLA, CASIC**

#### Automotive (impact: 8/10)
- Transition électrique
- Normes d'émissions
- Supply chain batteries

**Exemple**: *"New emission standards force automakers to accelerate EV transition"*
→ Impacte: **TESLA, STELLANTIS**

#### Energy (impact: 9/10)
- Décisions OPEP
- Transition énergétique
- Crise du gaz russe
- Prix de l'énergie

**Exemple**: *"Europe faces energy crisis as gas prices surge"*
→ Impacte: **OIL, GAS, TOTALENERGIES, ENGIE**

#### Luxury (impact: 7/10)
- Consommation chinoise
- Tourisme international
- Confiance consommateur

**Exemple**: *"Chinese consumer spending drops amid economic slowdown"*
→ Impacte: **LVMH, INTERCONT HOTELS**

#### Defense/Aerospace (impact: 7/10)
- Budgets défense
- Commandes militaires
- Contrats aéronautiques

**Exemple**: *"NATO countries agree to increase defense spending"*
→ Impacte: **THALES, AIRBUS**

---

## 🔄 Fonctionnement du Système

### Architecture

```
┌─────────────────────────────────────────┐
│  1. COLLECTE ÉVÉNEMENTS MACRO          │
│     - Requêtes thématiques GDELT       │
│     - Keywords: Fed, inflation, war... │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. COLLECTE ÉVÉNEMENTS SECTORIELS     │
│     - Par industrie/secteur            │
│     - Keywords: AI regulation, OPEC... │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. MAPPING INTELLIGENT                │
│     - Analyse titre/contenu            │
│     - Match keywords → événements      │
│     - Check sensibilité actif          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. SCORING DE PERTINENCE              │
│     Score = Impact × Nb_keywords       │
│     Bonus si sensibilité spécifique    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  OUTPUT: News → Actifs impactés        │
│     + Score de pertinence              │
└─────────────────────────────────────────┘
```

### Calcul du Score de Pertinence

```python
Score = Impact_Base × Nb_Keywords_Matchés

# Avec bonus:
- Événement macro affecting "all": +0%
- Match direct actif sectoriel: +20%
- Match sensibilité spécifique: +30%
```

**Exemples**:
- News Fed + 2 keywords matchés → Score = 10 × 2 = 20 pour tous les actifs
- News tech + 2 keywords matchés + match APPLE → Score = 8 × 2 × 1.2 = 19.2

### Seuils

- **Score minimum**: 5.0 (configurable)
- **Impact macro**: 7-10/10
- **Impact sectoriel**: 6-8/10

---

## 📁 Fichiers de Configuration

### `config/news_strategy.yaml`

Fichier principal contenant:
- Liste des actifs avec leurs sensibilités
- Événements macro avec keywords
- Événements sectoriels avec keywords
- Paramètres de collecte

**Personnalisation**:
```yaml
# Ajouter de nouveaux keywords
macro_events:
  monetary_policy:
    keywords:
      - "Federal Reserve"
      - "interest rate"
      # Ajoutez vos keywords ici
```

---

## 🚀 Utilisation

### 1. Test Rapide

```bash
python demo_hybrid_news.py
```

Collecte sur une courte période pour tester le système.

### 2. Collecte Complète

```python
from src.collectors.hybrid_news_collector import HybridNewsCollector

collector = HybridNewsCollector()

mapped_news = collector.collect_and_map(
    start_date="2023-01-01",
    end_date="2024-12-31",
    min_relevance_score=5.0,
    max_records_per_query=250,
    delay=2.0
)
```

### 3. Intégration au Pipeline

Le collecteur peut remplacer l'ancien `GDELTNewsCollector` dans `main_collect_historical.py`.

---

## 📊 Outputs

### 1. `hybrid_news_raw.csv`
News brutes collectées avec métadonnées:
- `title`, `url`, `date`, `source`
- `event_type`: Type d'événement détecté
- `event_category`: "macro" ou "sector"
- `base_impact_score`: Score d'impact de base

### 2. `hybrid_news_mapped.csv`
News mappées aux actifs:
- Toutes les colonnes de `raw`
- `asset`: Actif impacté
- `relevance_score`: Score de pertinence
- `matched_events`: Événements détectés

---

## 🎯 Avantages de l'Approche

### ✅ Avantages

1. **Indépendance** : Ne dépend pas de la mention directe des actifs
2. **Anticipation** : Capture les signaux macro avant impact
3. **Exhaustivité** : Couvre événements globaux + sectoriels
4. **Scoring intelligent** : Filtre les news pertinentes
5. **Configurable** : Keywords et sensibilités personnalisables

### 📈 Cas d'Usage

**Exemple 1**: Crise bancaire SVB (mars 2023)
- Événement macro: banking_financial_crisis
- Impact: TOUS les actifs tech/finance
- Aucune mention directe de AAPL, mais pertinence élevée

**Exemple 2**: Invasion Ukraine (2022)
- Événement macro: geopolitical_tensions
- Impact prioritaire: OIL, GAS, défense
- Impact secondaire: tous les indices

**Exemple 3**: AI Act européen (2024)
- Événement sectoriel: technology
- Impact ciblé: APPLE, AMAZON, TESLA
- Pas d'impact sur luxe ou énergie

---

## 🔧 Personnalisation

### Ajouter un Nouvel Actif

```yaml
# Dans config/news_strategy.yaml
assets:
  stocks:
    - name: "NOUVEAU"
      ticker: "NEW"
      sector: "technology"
      sensitivity: ["tech_regulation", "us_economy"]
```

### Ajouter un Nouveau Type d'Événement

```yaml
macro_events:
  nouveau_type:
    keywords:
      - "keyword1"
      - "keyword2"
    impact_score: 8
    affects: ["all"]  # ou liste d'actifs
```

### Ajuster le Scoring

Modifiez dans `news_impact_mapper.py`:
```python
# Ligne 152: Ajuster la formule
event_score = base_impact * keyword_count * VOTRE_FACTEUR
```

---

## 📚 Prochaines Évolutions

- [ ] Ajouter analyse de sentiment (FinBERT)
- [ ] Intégrer d'autres sources (NewsAPI, Finnhub)
- [ ] ML pour prédire l'impact réel
- [ ] Dashboard de visualisation
- [ ] Alertes temps réel

---

## 🐛 Troubleshooting

### Aucune news collectée
- Vérifier connexion Internet
- GDELT peut être temporairement indisponible
- Augmenter `max_records_per_query`
- Élargir la période

### Scores trop bas/élevés
- Ajuster `min_relevance_score`
- Modifier les `impact_score` dans la config
- Revoir les keywords (trop stricts/larges)

### Trop de faux positifs
- Augmenter `min_relevance_score`
- Affiner les keywords
- Ajouter des filtres sur sources

---

**Créé le**: 2026-01-14
**Auteur**: Claude Code
**Version**: 1.0
