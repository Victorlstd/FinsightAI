# 🔍 Pipeline de Détection d'Anomalies Boursières

Détection automatique d'anomalies boursières (baisses significatives) et corrélation avec les actualités via NewsAPI.

---

## 🎯 Objectif

1. **Détecter** les baisses anormales dans les données historiques (17 actifs)
2. **Corréler** avec les actualités pour identifier les causes
3. **Générer** des rapports visuels (HTML + Markdown + JSON pour dashboard)

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

**Source** : Données locales depuis `PFE_MVP/data/raw/*.csv` (~10 ans d'historique)

---

## ⚡ Installation Rapide

### Prérequis

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Obtenir une clé NewsAPI gratuite
# → https://newsapi.org/register (limite: 100 requêtes/jour)

# 3. Configurer la clé API
echo "NEWSAPI_KEY=votre_clé_api" > .env
```

---

## 🚀 Utilisation

### Pipeline Complète (Recommandé)

```bash
# Exécution complète avec données locales
python main_local.py --full --period 3y --max-anomalies 30
```

**Résultat** :
- ✅ Chargement des données locales (10 secondes)
- ✅ Détection des anomalies
- ✅ Corrélation avec NewsAPI
- ✅ Génération des rapports (HTML, Markdown, JSON)
- 📄 Fichiers générés :
  - `reports/anomaly_report.html` - Rapport visuel
  - `reports/anomaly_report.md` - Rapport markdown
  - `reports/anomaly_report.json` - Pour le dashboard

### Paramètres Utiles

```bash
# Analyser une période spécifique
python main_local.py --full --period 1y

# Actifs spécifiques
python main_local.py --full --assets APPLE TESLA

# Uniquement les anomalies critiques
python main_local.py --full --only-critical --min-variation -15
```

### Étapes Individuelles

```bash
# 1. Charger les données
python main_local.py --step historical --period 3y

# 2. Détecter les anomalies
python main_local.py --step detect

# 3. Corréler avec les news
python main_local.py --step correlate --max-anomalies 10
```

---

## 🎨 Système de Pertinence

Les news corrélées sont classées en **3 catégories** pour une meilleure lisibilité :

| Catégorie | Badge | Seuil de Score | Signification |
|-----------|-------|----------------|---------------|
| **Haute pertinence** | 🎯 Vert | ≥ 70 | News très pertinente |
| **Pertinence moyenne** | 📊 Orange | 45-69 | News moyennement pertinente |
| **Faible pertinence** | ❓ Gris | < 45 | Corrélation incertaine |

**Distribution réelle** : ~15% Haute, ~60% Moyenne, ~25% Faible

---

## 📊 Intégration Dashboard

### 1. Générer les Données

La pipeline génère automatiquement le JSON pour le dashboard :

```bash
python main_local.py --full --period 3y
# Génère automatiquement: reports/anomaly_report.json
```

### 2. Lancer le Dashboard

```bash
cd ..
streamlit run dashboard.py
```

### 3. Utiliser les Filtres

Le dashboard offre **9 filtres interactifs** :

1. **📊 Actifs** - Sélection des actifs à afficher
2. **⚠️ Sévérité** - Minor, Moderate, Severe, Critical
3. **🎯 Niveau de pertinence** - Haute, Moyenne, Faible (NOUVEAU)
4. **⭐ Score minimum** - Slider 0-100
5. **📅 Période** - Plage de dates
6. **📋 Trier par** - Date, Variation, Score
7. **📰 Nombre de news** - Minimum de news
8. **🔍 Export CSV** - Exporter les résultats filtrés

#### Exemple : Voir uniquement les meilleures corrélations

```
Filtre Pertinence : [🎯 Haute pertinence]
Résultat : Anomalies avec news très pertinentes (score ≥ 70)
```

---

## 📁 Structure du Projet

```
Prediction_Anomalies/
├── main_local.py              # Pipeline complète (recommandé)
├── generate_anomalies_data.py # Génération JSON dashboard
├── requirements.txt           # Dépendances Python
│
├── src/
│   ├── collectors/
│   │   └── local_data_collector.py  # Lecture CSV locaux
│   ├── detectors/
│   │   └── anomaly_detector.py      # Détection d'anomalies
│   ├── correlators/
│   │   └── newsapi_correlator.py    # Corrélation NewsAPI
│   └── reporters/
│       ├── anomaly_report_generator.py    # Génération rapports
│       └── pertinence_classifier.py       # Classification pertinence
│
├── data/                      # Données générées
│   ├── historical/            # CSV historiques
│   ├── anomalies/             # Anomalies détectées
│   └── news/                  # News corrélées
│
└── reports/                   # Rapports générés
    ├── anomaly_report.html    # Rapport visuel
    ├── anomaly_report.md      # Rapport markdown
    └── anomaly_report.json    # JSON pour dashboard
```

---

## 🔧 Configuration

### Seuils de Détection

Les seuils par défaut sont optimisés pour détecter les baisses significatives :

| Période | Seuil par défaut | Paramètre |
|---------|------------------|-----------|
| 1 jour | -3% | `--threshold-1d` |
| 5 jours | -5% | `--threshold-5d` |
| 30 jours | -10% | `--threshold-30d` |

**Exemple** : Détecter uniquement les grosses baisses
```bash
python main_local.py --full --threshold-1d -5.0 --threshold-5d -10.0
```

### Fenêtre de Recherche News

```bash
# Chercher les news 3 jours avant et 2 jours après l'anomalie
python main_local.py --full --window-before 3 --window-after 2
```

---

## 📊 Exemples de Sorties

### Rapport HTML

```html
┌────────────────────────────────────────────────┐
│ APPLE - 2026-01-23              🔴 Severe      │
├────────────────────────────────────────────────┤
│ 📉 Variation : -10.51%                         │
│ 📰 News trouvées : 11                          │
│                                                │
│ 🏆 News la plus pertinente                     │
│ ┌──────────────────────────────────────────┐   │
│ │ 2026-01-22 | Le même jour                 │   │
│ │ 📊 Pertinence moyenne                     │   │
│ │                                           │   │
│ │ Motorola Edge 70 vs. iPhone Air           │   │
│ │ The Motorola Edge 70 and iPhone Air...    │   │
│ │                                           │   │
│ │ Source : Android Central                  │   │
│ └──────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

### JSON Dashboard

```json
{
  "generated_at": "2026-02-03 10:30:00",
  "stats": {
    "Anomalies détectées": "736",
    "Avec news": "10",
    "News trouvées": "88",
    "Score moyen": "52.3/100"
  },
  "anomalies": [
    {
      "title": "APPLE - 2026-01-23",
      "severity": "Severe",
      "variation": "-10.51%",
      "news_count": 11,
      "top_news": [
        {
          "timing": "2026-01-22 | Le même jour",
          "score": 67,
          "pertinence": "Pertinence moyenne",
          "pertinence_emoji": "📊",
          "pertinence_color": "#f39c12",
          "title": "Motorola Edge 70 vs. iPhone Air",
          "description": "...",
          "source": "Android Central",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

---

## 🐛 Dépannage

### Erreur : "NEWSAPI_KEY non trouvée"

**Solution** :
```bash
echo "NEWSAPI_KEY=votre_clé_api" > .env
```

### Erreur : "Aucune donnée historique"

**Cause** : Fichiers CSV manquants dans `PFE_MVP/data/raw/`

**Solution** :
```bash
# Vérifier les fichiers
ls ../PFE_MVP/data/raw/*.csv
```

### Le dashboard affiche "0 anomalies"

**Solution** :
```bash
# Régénérer le JSON
python generate_anomalies_data.py

# Vérifier le fichier
cat reports/anomaly_report.json | head -20
```

### Limite NewsAPI atteinte

**Solution** :
```bash
# Limiter le nombre d'anomalies analysées
python main_local.py --full --max-anomalies 10
```

---

## 📈 Performance

| Opération | Temps | Détails |
|-----------|-------|---------|
| Chargement données | ~10s | 17 actifs, 10 ans d'historique |
| Détection anomalies | ~5s | 736 anomalies détectées |
| Corrélation NewsAPI | ~30s | 10 anomalies avec news |
| Génération rapports | ~2s | HTML + Markdown + JSON |
| **Total** | **~50s** | Pipeline complète |

**Note** : 9x plus rapide que la version avec téléchargement yfinance (90s → 10s)

---

## 🎯 Workflow Recommandé

### 1. Développement / Test
```bash
# Analyse rapide avec peu d'anomalies
python main_local.py --full --period 1y --max-anomalies 5
```

### 2. Production
```bash
# Analyse complète pour le dashboard
python main_local.py --full --period 3y --max-anomalies 30

# Lancer le dashboard
cd .. && streamlit run dashboard.py
```

### 3. Analyse Spécifique
```bash
# Focus sur un actif
python main_local.py --full --assets APPLE --period 2y

# Ouvrir le rapport
open reports/anomaly_report.html
```

---

## 🔄 Mise à Jour des Données

```bash
# 1. Pipeline complète
python main_local.py --full --period 3y

# 2. Le JSON est généré automatiquement
# 3. Rafraîchir le dashboard (F5 dans le navigateur)
```

---

## 📚 Ressources

- **NewsAPI** : https://newsapi.org/docs
- **Streamlit** : https://docs.streamlit.io
- **Pandas** : https://pandas.pydata.org/docs

---

## 🆕 Nouveautés v2.1 (2026-02-03)

- ✅ **Système de classification de pertinence** (3 catégories)
- ✅ **Badges colorés** dans les rapports HTML/Markdown
- ✅ **Nouveau filtre dashboard** : Niveau de pertinence
- ✅ **Rétrocompatibilité** avec anciens JSON
- ✅ **9 filtres interactifs** au total

---

## 📄 Licence

MIT License - Voir LICENSE pour détails

---

**Version** : 2.1
**Dernière mise à jour** : 2026-02-03
**Status** : ✅ Production Ready
