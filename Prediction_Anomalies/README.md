# 🔍 Pipeline de Détection d'Anomalies Boursières

Détection automatique d'anomalies boursières (baisses significatives) et corrélation avec les actualités via NewsAPI.

---

## 🎯 Objectif

1. **Détecter** les baisses anormales dans les données historiques
2. **Corréler** avec les actualités pour identifier les causes
3. **Générer** des rapports visuels (HTML + Markdown)

---

## 📊 Actifs Analysés (17 actifs)

| Catégorie | Actifs |
|-----------|--------|
| **Indices** | SP 500, CAC40, GER30 |
| **Tech** | APPLE, AMAZON, TESLA |
| **Énergie** | TOTALENERGIES, ENGIE, OIL, GAS |
| **Luxe/Industrie** | LVMH, AIRBUS, STELLANTIS |
| **Pharma** | SANOFI |
| **Hôtellerie** | INTERCONT HOTELS |
| **Défense** | THALES |
| **Matières premières** | GOLD |

---

## ⚡ Installation (3 minutes)

### Prérequis

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Obtenir une clé NewsAPI gratuite
# → https://newsapi.org/register (limite: 100 requêtes/jour)

# 3. Configurer la clé API
cp .env.example .env
echo "NEWSAPI_KEY=votre_clé_api" > .env
```

---

## 🚀 Utilisation

### Deux versions disponibles

#### Version 1 : Avec yfinance (téléchargement)

```bash
# Pipeline complète (télécharge les données)
python main.py --full --period 1y --max-anomalies 10
```

**Caractéristiques** :
- ✅ Données temps réel
- ✅ Nouveaux actifs possibles
- ⏱️ ~2m 30s (17 actifs, 3 ans)

---

#### Version 2 : Avec données locales (recommandé) ⭐

```bash
# Pipeline complète (utilise PFE_MVP/data/raw)
python main_local.py --full --period 3y --max-anomalies 20
```

**Caractéristiques** :
- ✅ **9x plus rapide** pour la collecte
- ✅ Cohérent avec le projet (même source de données)
- ✅ Fonctionne offline (sauf NewsAPI)
- ✅ Historique complet (~10 ans, 2016-2026)
- ⏱️ ~1m 05s (17 actifs, 3 ans)

---

## 📖 Exemples d'Utilisation

### Test rapide (1 actif, 1 an)

```bash
python main_local.py --full --period 1y --assets APPLE --max-anomalies 5
```

**Résultat** : ~30 secondes, ~30-40 anomalies détectées

---

### Analyse complète (tous actifs, 3 ans)

```bash
python main_local.py --full --period 3y
```

**Résultat** : ~2 minutes, ~500-1000 anomalies détectées

---

### Anomalies critiques uniquement

```bash
python main_local.py --full --only-critical --max-anomalies 20
```

**Résultat** : Uniquement les baisses > -15%

---

### Actifs spécifiques par secteur

```bash
# Secteur tech
python main_local.py --full --assets APPLE AMAZON TESLA

# Secteur énergie
python main_local.py --full --assets TOTALENERGIES ENGIE OIL GAS

# Indices européens
python main_local.py --full --assets CAC40 GER30
```

---

### Exécution par étapes

```bash
# Étape 1 : Charger les données (CSV locaux ou yfinance)
python main_local.py --step historical --period 1y

# Étape 2 : Détecter les anomalies
python main_local.py --step detect

# Étape 3 : Corréler avec NewsAPI
python main_local.py --step correlate --max-anomalies 10
```

---

### Seuils personnalisés

```bash
# Seuils plus stricts (moins d'anomalies)
python main_local.py --full \
  --threshold-1d -5.0 \
  --threshold-5d -8.0 \
  --threshold-30d -15.0

# Seuils plus permissifs (plus d'anomalies)
python main_local.py --full \
  --threshold-1d -2.0 \
  --threshold-5d -3.0 \
  --threshold-30d -8.0
```

---

## 🧠 Méthode de Détection

### Critères de détection

**Une anomalie est détectée si :**
- Baisse **≥ 3%** sur 1 jour, OU
- Baisse **≥ 5%** sur 5 jours, OU
- Baisse **≥ 10%** sur 30 jours

### Classification de sévérité

| Niveau | Variation | Signification |
|--------|-----------|---------------|
| 🟡 **Minor** | -3% à -5% | Correction technique |
| 🟠 **Moderate** | -5% à -8% | Baisse sectorielle |
| 🔴 **Severe** | -8% à -15% | Début de crise |
| ⚫ **Critical** | < -15% | Crash majeur |

---

## 🎨 Corrélation avec les Actualités

### Requêtes intelligentes par actif

Le système génère automatiquement des requêtes NewsAPI optimisées :

| Actif | Requête NewsAPI |
|-------|-----------------|
| **APPLE** | `"Apple Inc" OR "iPhone" OR "Tim Cook" OR "tech sector"` |
| **TESLA** | `"Tesla" OR "Elon Musk" OR "TSLA" OR "EV market"` |
| **SP 500** | `"S&P 500" OR "US stock market" OR "economic crisis"` |

### Score de pertinence (0-100)

Chaque article reçoit un score basé sur :

| Critère | Points |
|---------|--------|
| Mots-clés spécifiques dans titre/description | +30 pts |
| Mots-clés sectoriels | +15 pts |
| Compétiteurs mentionnés | +10 pts |
| Contexte macro-économique | +5 pts |
| **Bonus si dans le titre** | **×1.5** |

**Filtrage** : Seuls les articles avec un score ≥ 20/100 sont conservés.

---

## 📂 Architecture de la Pipeline

### Flux de données (Version Locale)

```
PFE_MVP/data/raw/*.csv
        ↓
LocalDataCollector (lecture + calculs)
        ↓
data/historical/*_historical.csv
        ↓
AnomalyDetector (détection par seuils)
        ↓
data/anomalies/anomalies_detected.csv
        ↓
NewsAPICorrelator (requêtes + scoring)
        ↓
data/news/anomalies_with_news_newsapi.csv
        ↓
AnomalyReportGenerator
        ↓
reports/anomaly_report.html + .md
```

### Structure des fichiers

```
Prediction_Anomalies/
├── main.py                          # Version yfinance
├── main_local.py                    # Version locale ⭐
├── src/
│   ├── collectors/
│   │   ├── historical_data_collector.py  # yfinance
│   │   └── local_data_collector.py       # CSV locaux
│   ├── detectors/
│   │   └── anomaly_detector.py           # Détection anomalies
│   ├── correlators/
│   │   ├── newsapi_correlator.py         # NewsAPI
│   │   └── newsapi_collector.py
│   └── reporters/
│       └── anomaly_report_generator.py   # Rapports HTML/MD
├── data/
│   ├── historical/                       # Données chargées
│   ├── anomalies/                        # Anomalies détectées
│   └── news/                             # Corrélations
├── reports/
│   ├── anomaly_report.html               # Rapport visuel
│   └── anomaly_report.md                 # Rapport texte
├── .env                                  # Configuration (NEWSAPI_KEY)
├── requirements.txt
└── README.md                             # Ce fichier
```

---

## 📊 Formats de Sortie

### 1. Données historiques enrichies

**Fichier** : `data/historical/*_historical.csv`

```csv
date,open,high,low,close,volume,daily_return,daily_variation,return_5d,return_30d,symbol,name
2026-01-30,255.17,261.90,252.18,259.48,92352600,0.52,1.35,-2.10,-5.80,AAPL,APPLE
```

### 2. Anomalies détectées

**Fichier** : `data/anomalies/anomalies_detected.csv`

```csv
date,asset,symbol,close_price,window,variation_pct,severity,severity_level
2025-04-21,APPLE,AAPL,145.50,1day,-19.2,Critical,CRITICAL
```

### 3. Corrélations avec actualités

**Fichier** : `data/news/anomalies_with_news_newsapi.csv`

```csv
anomaly_date,asset,anomaly_variation,anomaly_severity,date,title,description,url,source,relevance_score,days_before_anomaly,query_used
```

### 4. Rapports visuels

- **`reports/anomaly_report.html`** : Rapport interactif avec badges colorés
- **`reports/anomaly_report.md`** : Rapport texte formaté

---

## ⚙️ Options de Configuration

### Paramètres de collecte

| Option | Valeurs | Description |
|--------|---------|-------------|
| `--period` | 1y, 3y, 5y, 10y, max | Période historique |
| `--assets` | APPLE, TESLA, ... | Actifs spécifiques (défaut: tous) |
| `--input-dir` | Chemin | Source des CSV (pour `main_local.py`) |

### Paramètres de détection

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `--threshold-1d` | float | -3.0 | Seuil baisse 1 jour (%) |
| `--threshold-5d` | float | -5.0 | Seuil baisse 5 jours (%) |
| `--threshold-30d` | float | -10.0 | Seuil baisse 30 jours (%) |

### Paramètres de corrélation

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `--window-before` | int | 2 | Jours avant anomalie (recherche news) |
| `--window-after` | int | 1 | Jours après anomalie (recherche news) |
| `--min-relevance` | float | 20.0 | Score minimum de pertinence (0-100) |
| `--max-anomalies` | int | None | Limite requêtes NewsAPI |

### Filtres

| Option | Description |
|--------|-------------|
| `--only-critical` | Anomalies Critical uniquement (> -15%) |
| `--min-variation` | Variation minimale en % (ex: -15) |

---

## ⚡ Comparaison des Versions

| Critère | `main.py` (yfinance) | `main_local.py` (CSV) |
|---------|----------------------|-----------------------|
| **Source données** | yfinance API | PFE_MVP/data/raw |
| **Vitesse collecte (17 actifs)** | ~90s | ~10s ⚡ (9x plus rapide) |
| **Temps total (3 ans)** | ~2m 30s | ~1m 05s ⚡ (57% plus rapide) |
| **Connexion requise** | Yahoo Finance + NewsAPI | NewsAPI uniquement |
| **Historique max** | ~3-5 ans | ~10 ans (2016-2026) |
| **Cohérence projet** | Variable | 100% (même source) |
| **Nouveaux actifs** | ✅ Immédiat | ⚠️ Nécessite CSV |
| **Données récentes** | ✅ Temps réel | ⚠️ Dernière màj PFE_MVP |

**🏆 Recommandation : Utiliser `main_local.py` en production**

---

## 🔧 Résolution de Problèmes

### Erreur : "Répertoire source introuvable"

```bash
# Vérifier que PFE_MVP/data/raw existe
ls ../PFE_MVP/data/raw/

# Ou spécifier manuellement
python main_local.py --full --input-dir /chemin/vers/data/raw
```

### Erreur : "NEWSAPI_KEY non trouvée"

```bash
# Créer le fichier .env
echo "NEWSAPI_KEY=votre_clé" > .env
```

### Aucune anomalie détectée

```bash
# Essayer des seuils plus permissifs
python main_local.py --full --threshold-1d -2.0 --threshold-5d -3.0
```

### Limite NewsAPI atteinte (100 requêtes/jour)

```bash
# Limiter le nombre d'anomalies
python main_local.py --full --max-anomalies 20
```

---

## 🚀 Intégration dans le Projet Global

### Utilisation dans `run_all.py`

```python
from Prediction_Anomalies.main_local import AnomalyDetectionPipelineLocal
import os

def run_anomaly_detection():
    """Exécute la détection d'anomalies avec données locales."""
    print("\n" + "="*70)
    print("DÉTECTION D'ANOMALIES BOURSIÈRES")
    print("="*70)

    pipeline = AnomalyDetectionPipelineLocal(
        period="3y",
        threshold_1day=-3.0,
        threshold_5day=-5.0,
        threshold_30day=-10.0,
        newsapi_key=os.getenv('NEWSAPI_KEY')
    )

    success = pipeline.run_full_pipeline(max_anomalies=30)

    if success:
        print("✅ Détection d'anomalies terminée")
        print(f"   Rapports : Prediction_Anomalies/reports/")

    return success
```

---

## 📈 Performance

### Temps d'exécution moyens (17 actifs, 3 ans)

| Étape | `main.py` | `main_local.py` | Gain |
|-------|-----------|-----------------|------|
| Collecte données | ~90s | ~10s | **9x** ⚡ |
| Détection anomalies | ~8s | ~8s | = |
| Corrélation NewsAPI (20) | ~45s | ~45s | = |
| **TOTAL** | **~2m 30s** | **~1m 05s** | **57%** ⚡ |

---

## 📚 Documentation Technique

### Collectors

#### `HistoricalDataCollector` (yfinance)
- Télécharge les données depuis Yahoo Finance
- Calcule les variations (1j, 5j, 30j)
- Sauvegarde dans `data/historical/`

#### `LocalDataCollector` (CSV locaux) ⭐
- Lit les CSV depuis `PFE_MVP/data/raw/`
- Détecte automatiquement les 17 actifs
- Mapping symboles → noms conviviaux
- Même format de sortie que `HistoricalDataCollector`

### Detectors

#### `AnomalyDetector`
- Applique les seuils configurables
- Classifie par sévérité (Minor/Moderate/Severe/Critical)
- Export vers `data/anomalies/anomalies_detected.csv`

### Correlators

#### `NewsAPICorrelator`
- Génère des requêtes intelligentes par actif
- Fenêtre temporelle configurable (avant/après anomalie)
- Calcule un score de pertinence (0-100)
- Déduplique les articles
- Rate limiting (0.5s entre requêtes)

### Reporters

#### `AnomalyReportGenerator`
- Génère rapport HTML interactif
- Génère rapport Markdown formaté
- Top 5 news par anomalie
- Badges colorés par sévérité

---

## 🎓 Cas d'Usage

### Production : Pipeline quotidienne

```bash
# Cron job quotidien
0 8 * * * cd /path/to/Prediction_Anomalies && python main_local.py --full --period 3y --max-anomalies 50
```

### Recherche : Analyse historique

```bash
# Analyse sur 10 ans, anomalies critiques uniquement
python main_local.py --full --period max --only-critical
```

### Surveillance : Actifs spécifiques

```bash
# Suivre uniquement les indices
python main_local.py --full --assets "SP 500" CAC40 GER30
```

### Développement : Tests rapides

```bash
# Test avec 1 actif
python main_local.py --full --period 1y --assets APPLE --max-anomalies 5
```

---

## 🔮 Améliorations Futures

### Court terme
- Cache intelligent (éviter rechargement CSV)
- Parallélisation du chargement
- API REST pour intégration dashboard

### Long terme
- ML pour seuils adaptatifs
- Analyse de sentiment des articles
- Alertes temps réel via webhooks
- Support multi-langue pour les news

---

## 📄 Licence

Identique au projet principal FinsightAI.

---

## 👥 Contribution

Pour ajouter un nouvel actif :

1. Ajouter le CSV dans `PFE_MVP/data/raw/`
2. Mettre à jour `SYMBOL_TO_NAME` dans `src/collectors/local_data_collector.py`
3. Exécuter la pipeline

---

## ✅ Checklist

- [ ] Données CSV présentes dans `PFE_MVP/data/raw/`
- [ ] Clé NewsAPI configurée dans `.env`
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Test réussi : `python main_local.py --full --period 1y --assets APPLE --max-anomalies 5`
- [ ] Rapports générés dans `reports/`

---

**Version** : 2.0
**Date** : 2026-02-02
**Statut** : ✅ Production Ready

**🚀 Prêt à analyser les anomalies boursières avec les données locales !**
