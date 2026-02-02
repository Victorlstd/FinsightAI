# 🎯 Guide des Filtres pour Cibler les Gros Crashs

## Objectif

Les filtres `--only-critical` et `--min-variation` permettent de se concentrer uniquement sur les **crashs les plus importants** (comme le COVID-19) sans gaspiller de requêtes NewsAPI sur des anomalies mineures.

## 📊 Filtres Disponibles

### 1. `--only-critical` : Anomalies Critical Uniquement

**Utilisation** :
```bash
python main.py --step correlate --only-critical --max-anomalies 20
```

**Ce qui est filtré** :
- ✅ Garde uniquement les anomalies classées "Critical"
- ❌ Supprime Minor, Moderate, Severe

**Classification des sévérités** :
- **Critical** : Variation < -15%
- **Severe** : -15% ≤ Variation < -8%
- **Moderate** : -8% ≤ Variation < -5%
- **Minor** : -5% ≤ Variation < -3%

**Exemple de résultat** :
```
🎯 Filtre: Anomalies Critical uniquement
   104 anomalies Critical trouvées
```

### 2. `--min-variation` : Seuil de Baisse Minimum

**Utilisation** :
```bash
python main.py --step correlate --min-variation -20 --max-anomalies 15
```

**Ce qui est filtré** :
- ✅ Garde uniquement les anomalies avec variation ≤ -20%
- ❌ Supprime toutes les anomalies avec variation > -20%

**Valeurs recommandées** :
- `-15` : Très gros crashs (COVID-19 niveau)
- `-20` : Crashs extrêmes uniquement
- `-25` : Crashs catastrophiques rares

**Exemple de résultat** :
```
🎯 Filtre: Variation <= -20.0%
   27 anomalies avec variation >= 20.0%
```

### 3. Combiner les Deux Filtres

**Utilisation** :
```bash
python main.py --step correlate --only-critical --min-variation -18 --max-anomalies 10
```

**Comportement** :
- Filtre d'abord sur Critical
- Puis filtre sur variation >= 18%
- Double sécurité pour cibler les crashs majeurs

## 🌍 Cas d'Usage : Analyser le COVID-19

### Étape 1 : Collecter 5 Ans de Données

Pour capturer la période COVID (Mars 2020), il faut des données sur au moins 5 ans :

```bash
python main.py --step historical --period 5y
```

**Résultat attendu** :
- Données de Janvier 2021 à Janvier 2026
- Capture la période COVID (Mars 2020 = anomalie majeure)

### Étape 2 : Détecter les Anomalies

```bash
python main.py --step detect
```

**Sur 5 ans, vous aurez** :
- ~2000-3000 anomalies au total
- ~200-300 anomalies Critical

### Étape 3 : Filtrer et Corréler

#### Option A : Uniquement Critical

```bash
python main.py --step correlate --only-critical --max-anomalies 20
```

**Avantages** :
- 20 requêtes NewsAPI (économique)
- Focus sur les crashs > 15%
- Inclut COVID-19 et autres crises majeures

#### Option B : Variation Minimale -15%

```bash
python main.py --step correlate --min-variation -15 --max-anomalies 15
```

**Avantages** :
- Très ciblé sur les crashs massifs
- COVID-19 clairement visible (SP500 a chuté de -34% en Mars 2020)
- Moins de bruit

#### Option C : Double Filtre (Recommandé)

```bash
python main.py --step correlate \
    --only-critical \
    --min-variation -18 \
    --max-anomalies 15
```

**Avantages** :
- Maximum de précision
- Uniquement les crashs les plus violents
- Dataset idéal pour ML

### Étape 4 : Visualiser les Résultats

```bash
open reports/anomaly_report.html
```

**Ce que vous verrez** :
- Anomalie COVID-19 (Mars 2020) avec news associées :
  - "WHO declares pandemic"
  - "Markets crash as lockdown announced"
  - "S&P 500 enters bear market"
- Autres crises majeures avec leurs news

## 📈 Exemple Concret : COVID-19

### Commande Complète

```bash
# Pipeline complet pour analyser COVID-19 sur S&P 500
python main.py --full --period 5y \
    --assets "SP 500" \
    --only-critical \
    --max-anomalies 20
```

### Résultat Attendu

**Anomalies détectées** :
```
Date: 2020-03-12
Asset: SP 500
Variation: -34.05% (30-day window)
Severity: Critical
```

**News associées** :
```
2020-03-11 | Score: 95/100 | 1 jour avant
Titre: WHO Declares COVID-19 a Pandemic
Description: The World Health Organization declared the coronavirus...
Source: Reuters
Lien: https://...

2020-03-11 | Score: 90/100 | 1 jour avant
Titre: Trump Announces Travel Ban From Europe
Description: President Trump announced sweeping travel restrictions...
Source: CNN
Lien: https://...

2020-03-12 | Score: 88/100 | Le jour même
Titre: S&P 500 Plunges Into Bear Market
Description: The stock market suffered its worst day since 1987...
Source: Bloomberg
Lien: https://...
```

### Vérification Visuelle

Dans le rapport HTML, vous verrez :
- ✅ Badge rouge "Critical" bien visible
- ✅ Variation -34% en gras
- ✅ News COVID très pertinentes (scores 85-95)
- ✅ Timing parfait (1 jour avant/jour même)

## 💡 Conseils d'Utilisation

### 1. Économiser les Requêtes NewsAPI

NewsAPI limite gratuite = **100 requêtes/jour**

**Stratégie recommandée** :
```bash
# Jour 1 : Collecter + Détecter (0 requête NewsAPI)
python main.py --step historical --period 5y
python main.py --step detect

# Jour 1 : Corréler Critical (20 requêtes)
python main.py --step correlate --only-critical --max-anomalies 20

# Jour 2 : Affiner avec variation minimale (10 requêtes)
python main.py --step correlate --min-variation -20 --max-anomalies 10
```

### 2. Tester sur Courte Période d'Abord

```bash
# Test rapide sur 1 an (pour valider le système)
python main.py --full --period 1y --only-critical --max-anomalies 5
```

→ 5 requêtes seulement, résultat en 2 minutes

### 3. Pipeline Complet Optimisé

```bash
# Une seule commande pour COVID-19
python main.py --full --period 5y \
    --assets "SP 500" CAC40 GER30 \
    --only-critical \
    --max-anomalies 25 \
    --window-before 3
```

**Paramètres expliqués** :
- `--period 5y` : Capture COVID-19 (Mars 2020)
- `--assets "SP 500" CAC40 GER30` : 3 indices majeurs
- `--only-critical` : Uniquement crashs > 15%
- `--max-anomalies 25` : ~8 anomalies par indice
- `--window-before 3` : 3 jours avant (capture les news pré-crash)

## 🎓 Cas Pédagogiques

### Crise COVID-19 (Mars 2020)

```bash
python main.py --full --period 5y \
    --threshold-1d -8.0 \
    --only-critical \
    --max-anomalies 15
```

### Guerre Ukraine (Février 2022)

```bash
python main.py --full --period 3y \
    --assets "SP 500" OIL GAS \
    --only-critical \
    --max-anomalies 20
```

### Crise Bancaire SVB (Mars 2023)

```bash
python main.py --full --period 2y \
    --assets "SP 500" SANOFI \
    --threshold-1d -5.0 \
    --min-variation -12 \
    --max-anomalies 15
```

## 📊 Comparaison Avant/Après Filtres

### SANS Filtre (Toutes Anomalies)

```bash
python main.py --step correlate --max-anomalies 20
```

**Résultat** :
- 20 anomalies variées (Minor, Moderate, Severe, Critical)
- Beaucoup de bruit (petites baisses quotidiennes)
- News moins pertinentes (score moyen 40-50)

### AVEC Filtre --only-critical

```bash
python main.py --step correlate --only-critical --max-anomalies 20
```

**Résultat** :
- 20 anomalies Critical uniquement (> 15%)
- Focus sur les crashs majeurs
- News très pertinentes (score moyen 60-80)
- COVID, guerre, crises bancaires visibles

### AVEC Filtre --min-variation -20

```bash
python main.py --step correlate --min-variation -20 --max-anomalies 15
```

**Résultat** :
- 15 anomalies extrêmes (> 20%)
- Dataset ultra-ciblé
- News excellentes (score moyen 70-90)
- Uniquement les événements historiques majeurs

## 🚨 Limitations

### 1. NewsAPI Free Tier

- **Limite** : 100 requêtes/jour
- **Historique** : 1 mois seulement avec clé gratuite
- **Solution** : Pour COVID-19 (Mars 2020), il faudrait un abonnement payant

⚠️ **Important** : NewsAPI gratuit ne peut pas récupérer les news de Mars 2020. Pour analyser le COVID avec news réelles, il faut :
- Soit un abonnement NewsAPI Developer/Business
- Soit utiliser GDELT (historique complet gratuit)

### 2. Seuils de Détection

Les seuils par défaut peuvent manquer certains crashs :
- Défaut : -3% (1j), -5% (5j), -10% (30j)
- COVID-19 : -34% sur 30 jours → détecté ✅
- Petits crashs sectoriels : peuvent être manqués

**Solution** : Ajuster les seuils
```bash
python main.py --step detect \
    --threshold-1d -2.0 \
    --threshold-5d -4.0 \
    --threshold-30d -8.0
```

## 📚 Résumé

**Pour analyser les gros crashs comme COVID-19** :

1. **Collecter sur longue période**
   ```bash
   python main.py --step historical --period 5y
   ```

2. **Détecter toutes les anomalies**
   ```bash
   python main.py --step detect
   ```

3. **Filtrer et corréler** (une des options) :
   ```bash
   # Option A : Critical uniquement
   python main.py --step correlate --only-critical --max-anomalies 20

   # Option B : Variation >= 15%
   python main.py --step correlate --min-variation -15 --max-anomalies 15

   # Option C : Double filtre (recommandé)
   python main.py --step correlate --only-critical --min-variation -18 --max-anomalies 10
   ```

4. **Visualiser**
   ```bash
   open reports/anomaly_report.html
   ```

**Résultat attendu** : Rapport HTML avec COVID-19 et autres crises majeures, chacune associée à ses news les plus pertinentes.

---

**Date** : 2026-01-23
**Version** : 2.1 (avec filtres gros crashs)
