# Changements appliqués au système de filtrage des news

## Date: 2026-01-16

## Objectif
Élargir les critères de filtrage pour récupérer plus de news pertinentes que la collecte actuelle (289 associations).

---

## 1. Réduction du seuil de score minimum

**Fichier modifié:** `config/news_strategy.yaml` ligne 370

**Changement:**
```yaml
# AVANT
min_relevance_score: 5  # Score minimum pour conserver une news

# APRÈS
min_relevance_score: 3  # Score minimum pour conserver une news (réduit de 5 à 3 pour capturer plus de news)
```

**Impact:** Les news avec un score de pertinence entre 3.0 et 5.0 seront maintenant capturées (précédemment rejetées).

---

## 2. Enrichissement des keywords - Événements MACRO

### 2.1 monetary_policy
**Keywords ajoutés:**
- Bank of England, BoE, Fed
- interest rate hike, interest rate cut, rate decision
- QE, QT (quantitative tightening)
- FOMC, Federal Open Market Committee, ECB meeting
- central bank policy, central bank decision, policy rate
- hawkish, dovish
- monetary tightening, monetary easing

**Total:** 10 keywords → 29 keywords (+190%)

### 2.2 inflation_economy
**Keywords ajoutés:**
- inflation (forme courte)
- PPI, producer price index, PCE
- GDP (forme courte)
- jobless rate, employment data, nonfarm payrolls
- economic growth, economic contraction
- price surge, price increase, cost of living
- wage growth, labor market
- economic indicators, manufacturing PMI, services PMI

**Total:** 9 keywords → 26 keywords (+189%)

### 2.3 geopolitical_tensions
**Keywords ajoutés:**
- conflict (forme courte)
- Taiwan (sans "strait")
- geopolitical risk, international tensions
- diplomatic crisis, military action, armed conflict
- escalation, peace talks, ceasefire, invasion
- Ukraine war, Gaza, Israel, Iran, North Korea, South China Sea

**Total:** 9 keywords → 26 keywords (+189%)

### 2.4 trade_policy
**Keywords ajoutés:**
- tariff (singulier)
- trade deal, trade relations
- import tariff, export ban, trade barriers
- trade negotiations, bilateral trade, trade dispute
- dumping, subsidies

**Total:** 8 keywords → 17 keywords (+113%)

### 2.5 political_events
**Keywords ajoutés:**
- presidential election, midterm election
- vote, voting
- political instability, government collapse
- coalition, prime minister, president
- impeachment, political uncertainty

**Total:** 7 keywords → 15 keywords (+114%)

### 2.6 banking_financial_crisis
**Keywords ajoutés:**
- bank failure, financial crisis
- liquidity crisis, bank run, debt crisis
- bankruptcy, insolvency
- financial contagion, credit default, rescue package

**Total:** 8 keywords → 17 keywords (+113%)

### 2.7 pandemic_health
**Keywords ajoutés:**
- outbreak, contagion, quarantine
- health crisis, public health, vaccine rollout
- COVID, coronavirus, infectious disease

**Total:** 7 keywords → 15 keywords (+114%)

### 2.8 climate_energy_transition
**Keywords ajoutés:**
- carbon emissions, decarbonization, energy transition
- solar power, wind power, clean energy
- carbon neutral, ESG, sustainability
- Paris agreement, COP summit, green energy

**Total:** 8 keywords → 20 keywords (+150%)

---

## 3. Enrichissement des keywords - Événements SECTORIELS

### 3.1 technology
**Keywords ajoutés:**
- artificial intelligence, AI (formes courtes)
- chip shortage, chipmaker, silicon, TSMC
- tech regulation, GDPR, data protection
- tech earnings, software, hardware, smartphone
- machine learning, quantum computing

**Total:** 9 keywords → 24 keywords (+167%)

### 3.2 automotive
**Keywords ajoutés:**
- EV (forme courte)
- auto sales, vehicle production, car sales
- charging infrastructure, self-driving
- automotive industry, car maker, auto sector
- hybrid vehicle, lithium battery

**Total:** 8 keywords → 19 keywords (+138%)

### 3.3 luxury_consumer
**Keywords ajoutés:**
- luxury brand, luxury market
- consumer spending, discretionary spending
- high-end retail, luxury sector
- fashion, premium brand, consumer sentiment

**Total:** 7 keywords → 15 keywords (+114%)

### 3.4 energy_oil_gas
**Keywords ajoutés:**
- OPEC (forme courte)
- oil price, gas price, barrel, WTI, Brent
- oil demand, gas demand, refinery, petroleum
- drilling, fracking, shale oil, energy sector

**Total:** 9 keywords → 23 keywords (+156%)

### 3.5 healthcare_pharma
**Keywords ajoutés:**
- pharma (forme courte)
- drug development, medication, biotech
- pharmaceutical company, drug maker
- treatment, therapy, healthcare sector

**Total:** 8 keywords → 15 keywords (+88%)

### 3.6 defense_aerospace
**Keywords ajoutés:**
- military spending, defense sector, aerospace sector
- plane order, aircraft delivery, airline, aviation
- air travel, flight, weapons, missile

**Total:** 8 keywords → 17 keywords (+113%)

### 3.7 hospitality_travel
**Keywords ajoutés:**
- tourism, travel industry, hospitality sector
- hotel, vacation, tourist, hospitality
- booking, travel sector

**Total:** 6 keywords → 15 keywords (+150%)

---

## Résumé des statistiques

### Événements MACRO
- **Total keywords avant:** 66
- **Total keywords après:** 165
- **Augmentation:** +150%

### Événements SECTORIELS
- **Total keywords avant:** 55
- **Total keywords après:** 128
- **Augmentation:** +133%

### TOTAL GLOBAL
- **Keywords avant:** 121
- **Keywords après:** 293
- **Augmentation:** +142%

---

## Comment tester

### Option 1: Test rapide
```bash
source venv/bin/activate
python test_new_filters.py
```

Ce script compare automatiquement les résultats avec l'ancienne configuration.

### Option 2: Utiliser le script principal modifié
Modifier `demo_hybrid_news.py` ligne 56:
```python
# AVANT
min_relevance_score=5.0,

# APRÈS
min_relevance_score=3.0,
```

### Option 3: Collecte complète en production
```python
from src.collectors.hybrid_news_collector import HybridNewsCollector

collector = HybridNewsCollector()
mapped_news = collector.collect_and_map(
    start_date="2024-01-01",
    end_date="2024-01-31",
    min_relevance_score=3.0,  # ← Nouveau seuil
    max_records_per_query=250,
    delay=2.0
)
```

---

## Impact attendu

### Quantitatif
- **Augmentation attendue:** +40% à +100% de news capturées
- **Raison:** Seuil plus bas (3.0 vs 5.0) + plus de keywords pour matcher

### Qualitatif
- **Meilleure couverture** des événements avec formulations variées
- **Capture des acronymes** (Fed, ECB, AI, EV, etc.)
- **Détection des sujets émergents** (ESG, quantum computing, etc.)
- **Réduction des faux négatifs** (news pertinentes non détectées)

### Risques
- **Possible augmentation du bruit:** Quelques news moins pertinentes (score 3-5)
- **Mitigation:** Le score reste disponible pour filtrer a posteriori si nécessaire

---

## 3. Nouveau filtre: Top N garanti (IMPLÉMENTÉ)

### Fonctionnalité
Un nouveau paramètre `top_n_guaranteed` permet de **garantir la récupération des N news les plus importantes**, même si leur score est inférieur au seuil `min_relevance_score`.

### Comment ça marche

```python
collector.collect_and_map(
    start_date="2026-01-01",
    end_date="2026-01-16",
    min_relevance_score=3.0,      # Seuil standard
    top_n_guaranteed=100           # Garantir top 100
)
```

**Algorithme:**
1. Toutes les news sont évaluées et scorées
2. Les news sont triées par score décroissant
3. Le seuil effectif = `min(min_relevance_score, score_du_Nième_meilleur)`
4. Résultat: au minimum N news, possiblement plus si beaucoup dépassent le seuil

**Exemple concret:**
- `min_relevance_score = 3.0`
- `top_n_guaranteed = 100`
- Score de la 100ème meilleure news = 2.5

→ Seuil effectif = 2.5 (au lieu de 3.0)
→ Capture les 100 meilleures + toutes celles avec score ≥ 2.5

### Cas d'usage

**Utilisez `top_n_guaranteed=50-100` si:**
- Vous voulez GARANTIR un nombre minimum de news
- Vous acceptez des news avec score légèrement inférieur
- Vous préférez plus de couverture que de précision
- Vous faites de l'analyse de tendances (volume important nécessaire)

**Utilisez `top_n_guaranteed=0` (désactivé) si:**
- Vous voulez SEULEMENT les news pertinentes
- Vous préférez la qualité à la quantité
- Vous avez déjà assez de news avec le seuil actuel
- Vous faites du trading algorithmique (précision critique)

### Test
```bash
python test_top_n_filter.py
```

---

## Prochaines étapes possibles (non implémentées)

Si vous souhaitez aller encore plus loin:

1. **Augmenter gdelt_max_records** de 250 à 500-1000
2. **Ajouter de nouvelles catégories d'événements**
   - cryptocurrency / blockchain
   - real_estate / housing
   - supply_chain_disruption
3. **Assouplir le matching fuzzy** (50% au lieu de 60% pour phrases longues)
4. **Élargir la fenêtre temporelle** (72h au lieu de 48h)
5. **Ajouter plus de langues** (espagnol, italien, etc.)

---

## Fichiers modifiés

- ✅ `config/news_strategy.yaml` - Configuration principale (seuil + keywords)
- ✅ `src/collectors/hybrid_news_collector.py` - Ajout du filtre top_n_guaranteed
- ✅ `test_new_filters.py` - Script de test des nouveaux critères (créé)
- ✅ `test_top_n_filter.py` - Script de test du filtre top N (créé)
- ✅ `run_news_collection.py` - Script de collecte principal (créé)
- ✅ `demo_hybrid_news.py` - Mis à jour avec dates 2026 + seuil 3.0
- ✅ `CHANGEMENTS_FILTRAGE.md` - Ce document (créé)
