# 📊 Guide des Rapports Visuels

## 🎯 Objectif

Les rapports visuels vous permettent de **vérifier rapidement** les corrélations entre anomalies et news dans un format lisible et professionnel.

## 📄 Formats Disponibles

### 1. Rapport HTML (Recommandé ⭐)

**Fichier** : `reports/anomaly_report.html`

**Avantages** :
- ✅ Design professionnel avec couleurs
- ✅ Badges de sévérité colorés (Minor, Moderate, Severe, Critical)
- ✅ Liens cliquables vers les articles originaux
- ✅ Navigation facile entre anomalies
- ✅ Parfait pour présenter les résultats

**Ouvrir** :
```bash
open reports/anomaly_report.html
# ou
firefox reports/anomaly_report.html
```

### 2. Rapport Markdown

**Fichier** : `reports/anomaly_report.md`

**Avantages** :
- ✅ Lisible dans un éditeur de texte
- ✅ Compatible avec GitHub/GitLab
- ✅ Facile à partager par email
- ✅ Versionnable avec Git

**Ouvrir** :
```bash
cat reports/anomaly_report.md
# ou
code reports/anomaly_report.md
```

## 📊 Contenu des Rapports

### Section 1: Statistiques Globales

```
Total d'anomalies détectées : 38
Anomalies avec news : 10
Total de news trouvées : 45
Score de pertinence moyen : 52.3/100

Répartition par sévérité:
• Critical : 3
• Severe : 9
• Moderate : 7
• Minor : 19
```

### Section 2: Anomalies avec News

Pour chaque anomalie, le rapport affiche :

**Informations de l'anomalie :**
- Actif concerné (ex: APPLE)
- Date de l'anomalie
- Variation en % (ex: -19.20%)
- Sévérité (Minor, Moderate, Severe, Critical)

**Top 5 des news les plus pertinentes :**
- Date de publication
- Score de pertinence (0-100)
- Timing (X jours avant/après)
- Titre de l'article
- Description
- Source (Reuters, Bloomberg, etc.)
- Lien vers l'article original

**Exemple** :

```
APPLE - 2025-04-21
Sévérité : Critical
Variation : -19.20%

Top 5 des news les plus pertinentes:

2025-04-20 | Score: 95/100 | 1 jour(s) avant
Titre : Apple Reports Weak iPhone Sales, Shares Plunge
Description : Apple's quarterly earnings missed expectations...
Source : Reuters
Lien : https://reuters.com/...
```

### Section 3: Anomalies Sans News

Liste les anomalies pour lesquelles aucune news pertinente n'a été trouvée.

Utile pour identifier :
- Les anomalies techniques (sans cause externe)
- Les gaps dans la couverture NewsAPI
- Les événements locaux non couverts

## 🚀 Génération des Rapports

### Automatique (Recommandé)

Les rapports sont générés **automatiquement** après l'étape de corrélation :

```bash
# Pipeline complet
python main.py --full --period 1y --max-anomalies 10

# Ou étape par étape
python main.py --step correlate --max-anomalies 10
```

**Output** :
```
📝 Génération des rapports visuels...
✅ Rapport Markdown généré: reports/anomaly_report.md
✅ Rapport HTML généré: reports/anomaly_report.html

💡 Ouvrir le rapport: open reports/anomaly_report.html
```

### Manuelle

Si vous voulez régénérer les rapports à partir des données existantes :

```bash
python generate_report.py
```

## 🎨 Design du Rapport HTML

### Codes Couleurs

**Badges de sévérité** :
- 🟠 **Minor** : Orange (#f39c12)
- 🟠 **Moderate** : Orange foncé (#e67e22)
- 🔴 **Severe** : Rouge (#e74c3c)
- 🔴 **Critical** : Rouge foncé (#c0392b)

**News** :
- Fond gris clair pour chaque article
- Bordure bleue à gauche
- Score en badge bleu
- Source en gris discret

### Structure

```
┌─────────────────────────────────────┐
│  Titre du Rapport                   │
│  Date de génération                 │
├─────────────────────────────────────┤
│  📈 Statistiques Globales           │
│  [Boxes avec chiffres clés]        │
├─────────────────────────────────────┤
│  🔍 Anomalies Détectées             │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ APPLE - 2025-04-21   [Critical]│ │
│  │ Variation: -19.20%             │ │
│  │                                │ │
│  │ Top 5 des news:                │ │
│  │ ┌─────────────────────────┐   │ │
│  │ │ 2025-04-20 | Score: 95  │   │ │
│  │ │ Titre de l'article...   │   │ │
│  │ │ Source: Reuters         │   │ │
│  │ └─────────────────────────┘   │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 💡 Cas d'Usage

### 1. Vérification des Corrélations

Après avoir lancé le pipeline, ouvrez le rapport HTML pour :
- ✅ Vérifier que les news ont du sens pour chaque anomalie
- ✅ Valider les scores de pertinence
- ✅ Identifier les fausses corrélations

**Exemple** :
```
Anomalie: APPLE -19.2% le 21 avril 2025
News trouvées:
  • "Apple Reports Weak Earnings" (Score: 95) ✅ Pertinent
  • "Tech Sector Selloff" (Score: 75) ✅ Pertinent
  • "Inflation Concerns" (Score: 35) ⚠️ Moins pertinent
```

### 2. Présentation des Résultats

Le rapport HTML est parfait pour :
- Présenter à votre équipe
- Intégrer dans un rapport de stage/projet
- Partager avec des analystes financiers
- Documentation du projet

### 3. Analyse Post-Mortem

Utilisez les rapports pour analyser des crises passées :

```bash
# Analyse COVID-19 (Mars 2020)
python main.py --full --period 5y \
    --assets "SP 500" \
    --threshold-1d -5.0 \
    --max-anomalies 20

# Ouvrir le rapport
open reports/anomaly_report.html
```

**Résultat attendu** :
- Anomalie Critical en Mars 2020
- News: "WHO declares pandemic", "Lockdown measures", etc.
- Corrélations évidentes

### 4. Construction de Dataset

Utilisez le rapport pour :
- Valider la qualité des données avant ML
- Identifier les anomalies mal corrélées
- Filtrer les données bruitées

## 🔧 Personnalisation

### Modifier le Nombre de News Affichées

Éditez `src/reporters/anomaly_report_generator.py` :

```python
# Ligne ~XXX
top_news = group.nlargest(5, 'relevance_score')  # Changer 5 en 10
```

### Ajouter des Filtres

Vous pouvez filtrer avant de générer le rapport :

```python
from src.reporters.anomaly_report_generator import AnomalyReportGenerator
import pandas as pd

# Charger les données
correlations_df = pd.read_csv('data/news/anomalies_with_news_newsapi.csv')
anomalies_df = pd.read_csv('data/anomalies/anomalies_detected.csv')

# Filtrer uniquement Critical et Severe
correlations_df = correlations_df[
    correlations_df['anomaly_severity'].isin(['Critical', 'Severe'])
]

# Générer le rapport filtré
generator = AnomalyReportGenerator()
generator.generate_both_reports(correlations_df, anomalies_df)
```

## 📈 Exemples de Rapports

### Rapport avec Peu d'Anomalies

```bash
python main.py --full --period 1y \
    --threshold-1d -5.0 \
    --max-anomalies 5
```

**Résultat** :
- 5 anomalies majeures
- Rapport concis et focused
- Idéal pour présentation

### Rapport Exhaustif

```bash
python main.py --full --period 3y \
    --threshold-1d -2.0 \
    --max-anomalies 50
```

**Résultat** :
- 30-50 anomalies
- Rapport détaillé
- Idéal pour analyse approfondie

### Rapport Secteur Spécifique

```bash
python main.py --full --period 2y \
    --assets APPLE AMAZON TESLA \
    --max-anomalies 20
```

**Résultat** :
- Focus sur les tech giants
- Comparaison inter-entreprises
- Événements sectoriels

## ⚡ Commandes Rapides

```bash
# Générer un rapport à partir des données existantes
python generate_report.py

# Ouvrir le rapport HTML
open reports/anomaly_report.html

# Lire le rapport Markdown
cat reports/anomaly_report.md | less

# Convertir Markdown en PDF (optionnel)
pandoc reports/anomaly_report.md -o reports/anomaly_report.pdf
```

## 🐛 Troubleshooting

### Rapport Vide

**Cause** : Pas de corrélations générées

**Solution** :
```bash
# Générer des corrélations d'abord
python main.py --step correlate --max-anomalies 10
# Puis régénérer le rapport
python generate_report.py
```

### Peu de News dans le Rapport

**Cause** : Score de pertinence trop élevé

**Solution** :
```bash
# Baisser le score minimum
python main.py --step correlate \
    --min-relevance 15.0 \
    --max-anomalies 10
```

### Rapport HTML Ne S'Affiche Pas

**Cause** : Problème de chemin ou de navigateur

**Solution** :
```bash
# Vérifier que le fichier existe
ls -lh reports/anomaly_report.html

# Essayer avec un navigateur spécifique
firefox reports/anomaly_report.html
# ou
google-chrome reports/anomaly_report.html
```

## 📚 Résumé

**3 étapes pour obtenir un rapport visuel :**

1. **Collecter & Détecter** :
   ```bash
   python main.py --step historical --period 1y
   python main.py --step detect
   ```

2. **Corréler** :
   ```bash
   python main.py --step correlate --max-anomalies 10
   ```

3. **Visualiser** :
   ```bash
   open reports/anomaly_report.html
   ```

**✨ Le rapport est généré automatiquement à l'étape 2 !**

---

**Version** : 2.1 (avec rapports visuels)
**Date** : 2026-01-23
**Format** : HTML (interactif) + Markdown (portable)
