# 🔗 Intégration Dashboard - Page Anomalies

Documentation pour l'intégration de la pipeline d'anomalies dans le dashboard Streamlit.

---

## 🎯 Objectif

Afficher les anomalies détectées et leurs actualités corrélées dans la page "Anomalies" du dashboard avec le style cohérent du site.

---

## 📊 Flux de Données

```
PFE_MVP/data/raw/*.csv
        ↓
main_local.py (pipeline complète)
        ↓
data/anomalies/anomalies_detected.csv
data/news/anomalies_with_news_newsapi.csv
        ↓
generate_anomalies_data.py
        ↓
reports/anomaly_report.json
        ↓
dashboard.py (page Anomalies)
        ↓
Interface utilisateur Streamlit
```

---

## 🚀 Utilisation

### 1. Exécuter la pipeline

```bash
cd Prediction_Anomalies

# Pipeline complète (génère automatiquement le JSON)
python main_local.py --full --period 3y --max-anomalies 30
```

**Résultat** :
- ✅ Détection des anomalies
- ✅ Corrélation avec NewsAPI
- ✅ Génération automatique du fichier JSON
- 📄 Fichier créé : `reports/anomaly_report.json`

---

### 2. Copier le JSON (si nécessaire)

Le fichier est automatiquement copié vers `../reports/anomaly_report.json` par la pipeline.

Si besoin manuel :

```bash
cp Prediction_Anomalies/reports/anomaly_report.json reports/
```

---

### 3. Lancer le dashboard

```bash
# Depuis la racine du projet
streamlit run dashboard.py
```

**Navigation** : Cliquer sur "Anomalies" dans la barre de navigation

---

## 📁 Structure du JSON

Le fichier `anomaly_report.json` contient :

```json
{
  "generated_at": "2026-02-02 16:08:38",
  "stats": {
    "Anomalies détectées": "736",
    "Avec news": "10",
    "News trouvées": "88",
    "Score moyen": "52.3/100"
  },
  "severity_breakdown": {
    "Severe": 255,
    "Moderate": 207,
    "Minor": 172,
    "Critical": 102
  },
  "anomalies": [
    {
      "title": "GAS - 2026-01-27",
      "severity": "Critical",
      "variation": "-45.25%",
      "news_count": 10,
      "top_news": [
        {
          "timing": "2026-01-26 | 1 jour(s) avant",
          "score": 90,
          "title": "India's LNG Buyers Stall Deals...",
          "description": "India's liquefied natural gas...",
          "source": "Financial Post",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

---

## 🎨 Style du Dashboard

La page Anomalies utilise le style global du dashboard :

### Couleurs principales

- **Fond** : `#ffffff` (blanc)
- **Bordures** : `#eff2f5` (gris clair)
- **Primaire** : `#3861fb` (bleu FINSIGHT AI)
- **Texte** : `#000000` (noir)
- **Badges sévérité** :
  - 🟡 Minor : `#f39c12`
  - 🟠 Moderate : `#e67e22`
  - 🔴 Severe : `#e74c3c`
  - ⚫ Critical : `#c0392b`

### Typographie

- **Police** : Inter (Google Fonts)
- **Poids** : 400 (normal), 600 (semi-bold), 700 (bold), 800 (extra-bold)

---

## 🔄 Mise à Jour Automatique

### Depuis main_local.py

La pipeline génère automatiquement le JSON à la fin :

```python
# Dans main_local.py (lignes 276-286)
print("\n📊 Génération du fichier JSON pour le dashboard...")
subprocess.run(["python", "generate_anomalies_data.py"])
```

### Manuellement si besoin

```bash
cd Prediction_Anomalies
python generate_anomalies_data.py
```

---

## 📊 Fonctionnalités de la Page Anomalies

### Statistiques globales

Affichées en haut de page :
- Total anomalies détectées
- Nombre avec news corrélées
- Total news trouvées
- Score moyen de pertinence

### Filtres disponibles

- **Par sévérité** : Minor, Moderate, Severe, Critical
- **Par nombre de news** : Slider min news (0-50)

### Cartes d'anomalies

Pour chaque anomalie :
- **Titre** : Asset - Date
- **Badge sévérité** : Couleur selon gravité
- **Variation** : Pourcentage de baisse
- **Meilleure news** : Titre, description, source, URL, score

---

## 🔧 Fichiers Modifiés

### 1. `dashboard.py`

**Fonction modifiée** : `_load_report()` (ligne 588)

```python
candidates = [
    Path("reports") / "anomaly_report.json",
    Path("anomaly_report.json"),
    Path("Prediction_Anomalies") / "reports" / "anomaly_report.json",
]
```

### 2. `main_local.py`

**Ajout** : Génération automatique JSON (lignes 276-286)

```python
import subprocess
subprocess.run(["python", "generate_anomalies_data.py"])
```

### 3. Nouveaux fichiers

- `generate_anomalies_data.py` : Convertit CSV → JSON
- `INTEGRATION_DASHBOARD.md` : Cette documentation

---

## 🎯 Workflow Complet

### Développement

```bash
# 1. Exécuter la pipeline
cd Prediction_Anomalies
python main_local.py --full --period 1y --max-anomalies 10

# 2. Vérifier le JSON
cat reports/anomaly_report.json | jq '.stats'

# 3. Lancer le dashboard
cd ..
streamlit run dashboard.py
```

### Production

```bash
# Pipeline complète avec copie automatique
cd Prediction_Anomalies
python main_local.py --full --period 3y --max-anomalies 50

# Le JSON est automatiquement copié vers ../reports/
# Le dashboard charge automatiquement la dernière version
```

---

## 🐛 Résolution de Problèmes

### Le dashboard affiche "0 anomalies"

**Cause** : Fichier JSON introuvable ou vide

**Solution** :
```bash
# Régénérer le JSON
cd Prediction_Anomalies
python generate_anomalies_data.py
cp reports/anomaly_report.json ../reports/
```

### Erreur "Can't find anomaly_report.json"

**Cause** : Chemins incorrects

**Solution** :
```bash
# Vérifier l'emplacement
find . -name "anomaly_report.json"

# Copier au bon endroit
cp Prediction_Anomalies/reports/anomaly_report.json reports/
```

### Les anomalies ne s'affichent pas

**Cause** : Format JSON incorrect

**Solution** :
```bash
# Valider le JSON
cat reports/anomaly_report.json | jq '.'

# Régénérer si nécessaire
cd Prediction_Anomalies
python generate_anomalies_data.py
```

---

## 📈 Améliorations Futures

### Court terme
- [ ] Refresh automatique du JSON toutes les heures
- [ ] Filtres avancés (par actif, par date)
- [ ] Graphiques de tendance par sévérité

### Long terme
- [ ] API REST pour requêtes dynamiques
- [ ] Système d'alertes en temps réel
- [ ] Export PDF des rapports
- [ ] Comparaison période N vs N-1

---

## ✅ Checklist d'Intégration

- [x] Pipeline génère CSV anomalies
- [x] Pipeline génère CSV news corrélées
- [x] Script `generate_anomalies_data.py` créé
- [x] JSON généré automatiquement par la pipeline
- [x] Dashboard charge le JSON correctement
- [x] Style cohérent avec le site
- [x] Filtres fonctionnels
- [x] Affichage optimisé (1 meilleure news par anomalie)
- [x] Documentation complète

---

**Version** : 1.0
**Date** : 2026-02-02
**Statut** : ✅ Intégration terminée

**🎉 La page Anomalies est prête à être utilisée !**
