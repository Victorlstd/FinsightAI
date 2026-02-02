# 🔍 Prediction Anomalies

Détection automatique d'anomalies boursières (baisses significatives) et corrélation avec les actualités via NewsAPI.

## 🎯 Objectif

1. **Détecter** les baisses anormales dans les données historiques
2. **Corréler** avec les actualités pour identifier les causes
3. **Analyser** les relations événements-marchés

## 📊 Actifs Analysés

- **Indices** : SP 500, CAC40, GER30
- **Tech** : APPLE, AMAZON, TESLA
- **Pharma** : SANOFI
- **Défense/Aéro** : THALES, AIRBUS
- **Luxe** : LVMH
- **Énergie** : TOTALENERGIES, ENGIE, OIL, GAS
- **Autres** : STELLANTIS, INTERCONT HOTELS, GOLD

## 🚀 Installation Rapide (3 minutes)

```bash
cd prediction_Anomalies

# 1. Installer les dépendances
pip install -r requirements.txt --break-system-packages

# 2. Obtenir une clé NewsAPI gratuite
# → https://newsapi.org/register (limite: 100 requêtes/jour)

# 3. Configurer
cp .env.example .env
nano .env  # Ajouter: NEWSAPI_KEY=votre_cle

# 4. Tester
python quick_test.py
```

## 💻 Utilisation

### Option 1: Pipeline Complet (Recommandé)

```bash
# Analyse sur 1 an, 10 anomalies (10 requêtes API)
python main.py --full --period 1y --max-anomalies 10
```

**Résultat** : Données + Anomalies + News en ~3 minutes

### Option 2: Étape par Étape

```bash
# Étape 1: Récupérer les données historiques (2 min)
python main.py --step historical --period 3y

# Étape 2: Détecter les anomalies (< 1 min)
python main.py --step detect

# Étape 3: Corréler avec les news (1-2 min)
python main.py --step correlate --max-anomalies 20
```

### Option 3: Actifs Spécifiques

```bash
# Analyser uniquement certains actifs
python main.py --full --period 1y \
    --assets APPLE TESLA "SP 500" \
    --max-anomalies 15
```

## 🎨 Filtres Intelligents

Le système génère automatiquement des requêtes optimisées par actif :

**APPLE** → `"Apple Inc" OR "iPhone" OR "Tim Cook" OR "tech sector"`
**SP 500** → `"S&P 500" OR "US stock market" OR "economic crisis"`
**TESLA** → `"Tesla" OR "Elon Musk" OR "electric vehicle"`

Chaque news reçoit un **score de pertinence (0-100)** basé sur :
- Mots-clés spécifiques dans le titre : +30 pts
- Mots-clés sectoriels : +15 pts
- Compétiteurs mentionnés : +10 pts
- Contexte macro : +5 pts

## 📈 Méthode de Détection

**Anomalie détectée si :**
- Baisse **> 3%** sur 1 jour, OU
- Baisse **> 5%** sur 5 jours, OU
- Baisse **> 10%** sur 30 jours

**Classification de sévérité :**
| Niveau | Variation | Exemple |
|--------|-----------|---------|
| Minor | -3% à -5% | Correction technique |
| Moderate | -5% à -8% | Baisse sectorielle |
| Severe | -8% à -15% | Début de crise |
| Critical | < -15% | Crash majeur |

## 📁 Outputs Générés

```
data/
├── historical/
│   └── [ACTIF]_historical.csv         # Données OHLCV
├── anomalies/
│   └── anomalies_detected.csv         # Anomalies détectées
└── news/
    ├── anomalies_with_news_newsapi.csv      # Corrélations complètes
    └── correlations_analysis_newsapi.csv    # Export simplifié

reports/                                # 🆕 Rapports visuels
├── anomaly_report.html                 # Rapport interactif (RECOMMANDÉ)
└── anomaly_report.md                   # Rapport Markdown
```

### 🆕 Rapports Visuels

Les rapports sont **générés automatiquement** après l'étape de corrélation et présentent :

**Format HTML (Recommandé)** :
- ✅ Design professionnel avec couleurs
- ✅ Badges de sévérité colorés
- ✅ Liens cliquables vers les articles
- ✅ Navigation facile
- ✅ Parfait pour vérifier les corrélations

**Format Markdown** :
- ✅ Lisible dans un éditeur de texte
- ✅ Compatible avec GitHub/GitLab
- ✅ Facile à partager

**Génération manuelle** :
```bash
# Si vous voulez régénérer les rapports
python generate_report.py
```

## ⚙️ Paramètres Principaux

| Paramètre | Description | Défaut | Recommandé |
|-----------|-------------|--------|------------|
| `--period` | Période d'analyse | 3y | 1y (test), 3y (prod) |
| `--max-anomalies` | Limite de requêtes API | Aucune | 10-20 |
| `--threshold-1d` | Seuil 1 jour (%) | -3.0 | -2.5 (sensible), -5.0 (strict) |
| `--min-relevance` | Score minimum news | 20.0 | 30.0 (strict), 15.0 (large) |
| `--window-before` | Jours avant anomalie | 2 | 2-5 |
| `--window-after` | Jours après anomalie | 1 | 1-2 |
| `--only-critical` | Uniquement anomalies Critical | False | Activé pour gros crashs |
| `--min-variation` | Variation minimale (%) | Aucun | -15 ou -20 pour COVID |

## 🎯 Exemples d'Utilisation

### 1. Test Rapide

```bash
python main.py --full --period 1y --max-anomalies 10
```
→ 10 anomalies + news en 3 minutes

### 2. Analyse d'un Actif

```bash
python main.py --full --period 3y --assets APPLE --max-anomalies 30
```
→ Dataset complet APPLE

### 3. 🎯 Gros Crashs Uniquement (COVID, etc.)

```bash
# Analyse sur 5 ans avec filtre Critical
python main.py --full --period 5y \
    --only-critical \
    --max-anomalies 20
```
→ Uniquement les anomalies Critical (COVID-19, grandes crises)

```bash
# Variation minimale de -15% sur 5 ans
python main.py --full --period 5y \
    --min-variation -15 \
    --max-anomalies 15
```
→ Crashs > 15% seulement

### 4. Crises Macro

```bash
python main.py --full --period 5y \
    --assets "SP 500" CAC40 \
    --threshold-1d -5.0
```
→ COVID-19, grandes crises avec news

### 5. Secteur Tech

```bash
python main.py --full --period 2y \
    --assets APPLE AMAZON TESLA \
    --max-anomalies 40
```
→ Comparaison tech giants

## 📊 Comprendre les Résultats

### Terminal

```
📰 Collecte de news via NewsAPI...
  Recherche news pour APPLE...
    Requête: "Apple Inc" OR "iPhone"...
    ✓ 15 articles trouvés

✅ 45 corrélations établies
   Score moyen: 52.3

🔻 TOP 5 ANOMALIES CRITIQUES
━━━━━━━━━━━━━━━━━━━━━━━━
📉 APPLE - 2025-04-21
   Variation: -19.20% (Critical)
   📰 Top 3 news:
      2025-04-20 | Score: 95
      Apple Reports Weak iPhone Sales...
```

### Fichiers CSV

**anomalies_detected.csv** :
```csv
date,asset,variation_pct,severity,window
2025-04-21,APPLE,-19.2,Critical,30day
```

**anomalies_with_news_newsapi.csv** :
```csv
anomaly_date,asset,anomaly_variation,news_date,news_title,source,relevance_score
2025-04-21,APPLE,-19.2,2025-04-20,Apple Reports...,Reuters,95.0
```

## 🔧 Gestion du Quota NewsAPI

**Limite gratuite : 100 requêtes/jour**

### Stratégies

**1. Détecter d'abord, corréler ensuite**
```bash
# Voir combien d'anomalies
python main.py --step detect

# Limiter la corrélation
python main.py --step correlate --max-anomalies 20
```

**2. Seuils plus stricts**
```bash
# Moins d'anomalies = moins de requêtes
python main.py --full --threshold-1d -5.0
```

**3. Par lots sur plusieurs jours**
```bash
# Jour 1
python main.py --step historical --period 3y
python main.py --step detect

# Jour 2
python main.py --step correlate --max-anomalies 20

# Jour 3
# Éditer anomalies_detected.csv pour enlever les 20 premières lignes
python main.py --step correlate --max-anomalies 20
```

## 🐛 Troubleshooting

### Erreur: "NEWSAPI_KEY manquante"

```bash
# Vérifier le fichier .env
cat .env

# Doit contenir
NEWSAPI_KEY=abc123...
```

### Erreur: 429 Too Many Requests

**Cause** : 100 requêtes/jour dépassées

**Solutions** :
1. Attendre 24h
2. Utiliser `--max-anomalies` pour limiter
3. Créer un nouveau compte NewsAPI

### Peu de News Trouvées

```bash
# Élargir la fenêtre temporelle
python main.py --step correlate --window-before 5 --window-after 3

# Baisser le score minimum
python main.py --step correlate --min-relevance 10.0
```

### Noms d'Actifs avec Espaces

```bash
# ✅ Correct
python main.py --assets "SP 500" APPLE

# ❌ Incorrect
python main.py --assets SP500 APPLE
```

## 📁 Structure du Projet

```
prediction_Anomalies/
├── src/
│   ├── collectors/
│   │   ├── historical_data_collector.py   # Données yfinance
│   │   └── newsapi_collector.py           # News NewsAPI
│   ├── detectors/
│   │   └── anomaly_detector.py            # Détection seuils
│   └── correlators/
│       └── newsapi_correlator.py          # Corrélation
├── data/                                  # Outputs (généré)
├── main.py                                # Script principal
├── quick_test.py                          # Tests rapides
├── .env.example                           # Template config
└── README.md                              # Ce fichier
```

## 🎓 Cas d'Usage Avancés

### Analyse Post-Mortem COVID-19

```bash
python main.py --full --period 5y \
    --assets "SP 500" CAC40 \
    --threshold-1d -5.0
```

→ Mars 2020 : Anomalies critiques + news "pandemic", "lockdown", etc.

### Construction de Dataset ML

```bash
# Collecter beaucoup de données sur plusieurs jours
python main.py --step historical --period 5y
python main.py --step detect --threshold-1d -2.0

# Jour 1-5 : 20 anomalies/jour
python main.py --step correlate --max-anomalies 20
```

→ Dataset avec 100+ corrélations pour entraîner un modèle

### Backtesting de Stratégie

```bash
python main.py --full --period 10y \
    --assets "SP 500" \
    --threshold-1d -3.0
```

→ Identifier tous les crashs historiques et leur cause

## ⚡ Commandes Utiles

```bash
# Voir l'aide complète
python main.py --help

# Compter les anomalies détectées
wc -l data/anomalies/anomalies_detected.csv

# Voir les top anomalies
head -20 data/anomalies/anomalies_detected.csv

# Ouvrir les résultats
open data/news/correlations_analysis_newsapi.csv
```

## 📚 Ressources

- **NewsAPI** : https://newsapi.org/
- **yfinance** : https://github.com/ranaroussi/yfinance
- **Documentation NewsAPI** : https://newsapi.org/docs

## 📝 Notes Importantes

- **Corrélation ≠ Causalité** : Les résultats montrent des coïncidences temporelles
- **Limite NewsAPI** : 30 derniers jours uniquement (plan gratuit)
- **Qualité** : Dépend de la disponibilité des news dans NewsAPI
- **Rate Limiting** : Toujours utiliser `--max-anomalies` pour contrôler

## 🎉 Quick Start Final

```bash
# 1. Setup
cd prediction_Anomalies
pip install -r requirements.txt --break-system-packages
cp .env.example .env
# Ajouter NEWSAPI_KEY dans .env

# 2. Test
python quick_test.py

# 3. Analyse complète
python main.py --full --period 1y --max-anomalies 10

# 4. Explorer les résultats
open data/news/correlations_analysis_newsapi.csv
```

---

**Version** : 2.0 (Épurée)
**Date** : 2026-01-23
**Auteur** : Équipe PFE FinsightAI
