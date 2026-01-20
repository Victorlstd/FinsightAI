# Guide de Résolution des Problèmes - Collecte de News

## ⚠️ Erreurs Fréquentes et Solutions

### 1. Erreur: "Expecting value: line 1 column 1 (char 0)"

**Symptôme** :
```
ERROR | Erreur GDELT: Expecting value: line 1 column 1 (char 0)
```

**Cause** :
- GDELT retourne une réponse vide (pas de données pour cette requête)
- Les keywords sont trop spécifiques ou ne matchent aucune news
- Période de collecte trop courte

**Solutions** :

1. **Augmenter la période de collecte**
   ```python
   # Au lieu de 5 jours
   start_date="2024-01-15"
   end_date="2024-01-20"

   # Utiliser une période plus longue
   start_date="2023-01-01"
   end_date="2024-12-31"
   ```

2. **Simplifier les keywords** dans `config/news_strategy.yaml`
   ```yaml
   # Trop spécifique (peut échouer)
   keywords:
     - "European Central Bank monetary policy decision"

   # Mieux (plus de chances de match)
   keywords:
     - "ECB"
     - "monetary policy"
     - "interest rate"
   ```

3. **Augmenter max_records**
   ```python
   collector.collect_and_map(
       max_records_per_query=250  # Au lieu de 50
   )
   ```

4. **C'est normal !**
   - Certaines requêtes ne retournent pas de résultats
   - Le système continue automatiquement
   - Tant que QUELQUES requêtes réussissent, c'est OK

---

### 2. Erreur: "429 Client Error: Too Many Requests"

**Symptôme** :
```
ERROR | Erreur GDELT: 429 Client Error: Too Many Requests
```

**Cause** :
- GDELT limite le nombre de requêtes par minute
- Trop de requêtes en peu de temps

**Solutions** :

1. **Augmenter le délai entre requêtes**
   ```python
   collector.collect_and_map(
       delay=3.0  # Au lieu de 2.0 secondes
   )
   ```

2. **Réduire le nombre de requêtes**
   - Éditer `config/news_strategy.yaml`
   - Supprimer les événements moins importants
   - Regrouper les keywords similaires

3. **Collecte par lots**
   ```python
   # Collecter macro puis attendre
   macro_df = collector.fetch_macro_news(...)
   time.sleep(60)  # Attendre 1 minute

   # Puis collecter sectoriel
   sector_df = collector.fetch_sector_news(...)
   ```

4. **Utiliser d'autres sources**
   - NewsAPI (payant mais plus fiable)
   - Finnhub (limité mais stable)
   - RSS feeds directs

---

### 3. Peu de News Collectées

**Symptôme** :
```
16 news uniques collectées (au lieu de 200+ attendues)
```

**Causes** :
- Période de collecte trop courte
- Keywords trop spécifiques
- Beaucoup de requêtes échouent

**Solutions** :

1. **Période plus longue**
   ```python
   # Test court (16 news)
   start_date="2024-01-15"
   end_date="2024-01-20"  # 5 jours

   # Collecte réelle (beaucoup plus)
   start_date="2023-01-01"
   end_date="2024-12-31"  # 2 ans
   ```

2. **Keywords plus génériques**
   ```yaml
   # Dans config/news_strategy.yaml
   monetary_policy:
     keywords:
       - "Fed"  # Court et fréquent
       - "ECB"
       - "interest"
       - "inflation"
   ```

3. **Réduire min_relevance_score**
   ```python
   collector.collect_and_map(
       min_relevance_score=3.0  # Au lieu de 5.0
   )
   ```

---

## 🎯 Configuration Optimale

### Pour Tests Rapides (comme demo)
```python
collector.collect_and_map(
    start_date="2024-01-01",
    end_date="2024-01-31",  # 1 mois
    min_relevance_score=5.0,
    max_records_per_query=50,  # Réduit
    delay=2.0
)
```

### Pour Collecte Réelle
```python
collector.collect_and_map(
    start_date="2023-01-01",
    end_date="2024-12-31",  # 2 ans
    min_relevance_score=4.0,  # Plus permissif
    max_records_per_query=250,  # Maximum
    delay=3.0  # Plus de délai
)
```

### Pour Production (très stable)
```python
# Collecter par morceaux de 1 mois
import pandas as pd
from datetime import datetime, timedelta

all_news = []
start = datetime(2023, 1, 1)
end = datetime(2024, 12, 31)

current = start
while current < end:
    next_month = current + timedelta(days=30)

    print(f"Collecte: {current.date()} → {next_month.date()}")

    news = collector.collect_and_map(
        start_date=current.strftime("%Y-%m-%d"),
        end_date=next_month.strftime("%Y-%m-%d"),
        min_relevance_score=4.0,
        max_records_per_query=250,
        delay=3.0
    )

    if not news.empty:
        all_news.append(news)

    # Pause entre chaque mois
    time.sleep(120)  # 2 minutes

    current = next_month

# Combiner tout
final_df = pd.concat(all_news, ignore_index=True)
```

---

## 📊 Interpréter les Résultats

### Résultats Normaux
```
Total articles collectés: 200
  - Événements macro: 150
  - Événements sectoriels: 50
Doublons supprimés: 50
Articles uniques finaux: 150
```

✅ C'est OK ! Même avec des erreurs, on a des résultats.

### Résultats Préoccupants
```
Total articles collectés: 5
Doublons supprimés: 0
Articles uniques finaux: 5
```

❌ Très peu de données. Actions à prendre :
1. Augmenter la période
2. Simplifier les keywords
3. Réduire min_relevance_score
4. Vérifier la connexion Internet

---

## 🔧 Diagnostics

### Vérifier si GDELT fonctionne
```python
import requests

# Test manuel
response = requests.get(
    "https://api.gdeltproject.org/api/v2/doc/doc",
    params={
        'query': 'inflation',
        'mode': 'artlist',
        'maxrecords': 10,
        'format': 'json',
        'startdatetime': '20240101000000',
        'enddatetime': '20240131000000'
    }
)

print(f"Status: {response.status_code}")
print(f"Contenu: {response.text[:200]}")
```

### Vérifier les keywords
```python
from src.collectors.news_impact_mapper import NewsImpactMapper

mapper = NewsImpactMapper()

# Combien de requêtes ?
macro = mapper.get_macro_event_queries()
sector = mapper.get_sector_event_queries()

print(f"Requêtes macro: {len(macro)}")
print(f"Requêtes sectorielles: {len(sector)}")
print(f"Total: {len(macro) + len(sector)}")

# Si > 50, c'est beaucoup pour GDELT
```

---

## 💡 Recommandations

### Pour votre projet

1. **Phase de test** (maintenant)
   - Période courte (1-3 mois)
   - Vérifier que ça marche
   - Ajuster keywords et scores

2. **Collecte historique** (ensuite)
   - 2-3 ans de données
   - Par morceaux de 1 mois
   - Sauvegarder après chaque mois

3. **Production** (long terme)
   - Collecte quotidienne automatique
   - Monitoring des erreurs
   - Alerte si trop d'échecs

### Keywords à Privilégier

**❌ Éviter** (trop spécifiques) :
```yaml
- "European Central Bank interest rate decision announcement"
- "Federal Reserve quantitative easing policy meeting"
```

**✅ Préférer** (génériques) :
```yaml
- "ECB"
- "Fed"
- "interest rate"
- "inflation"
```

---

## 📝 Notes Importantes

1. **Les erreurs sont normales** : GDELT est gratuit et instable. 30-50% d'erreurs est acceptable.

2. **Qualité > Quantité** : 50 news pertinentes valent mieux que 500 news non pertinentes.

3. **Diversifier les sources** : Ne pas dépendre uniquement de GDELT. Envisager :
   - NewsAPI (payant)
   - Finnhub (limité gratuit)
   - RSS feeds directs
   - Web scraping de sites spécifiques

4. **Patience** : Une collecte sur 2 ans peut prendre 2-3 heures à cause des délais.

---

**Dernière mise à jour** : 2026-01-14
