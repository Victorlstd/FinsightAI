# Diagnostic complet – FinsightAI & Dashboard

## 1. Vue d’ensemble du projet

| Composant | Rôle |
|-----------|------|
| **app.py** | App Streamlit légère : login/inscription bidon + onboarding + lien vers tableau de bord |
| **dashboard.py** | Dashboard principal : KPIs, actifs, sentiment, graphiques, patterns, prédictions, XAI, anomalies |
| **run_all.py** | Pipeline PFE_MVP : fetch → train → predict → scan patterns (une commande pour tout) |
| **PFE_MVP** | Prédiction de direction (UP/DOWN), modèles ML, stock-pattern (candles + patterns) |
| **Pipeline_Recup_Donnees** | Collecte news (GDELT, hybride) + données de marché |
| **NLP** | Sentiment (FinBERT), classification financière des news |
| **XAI** | Explicabilité des prédictions |
| **Prediction_Anomalies** | Détection d’anomalies |

Le **dashboard en local** est servi par **Streamlit** via **dashboard.py** (ou **app.py** pour la version simplifiée).

---

## 2. Dépendances (requirements.txt)

- **Streamlit** + **Plotly** pour l’UI et les graphiques  
- **pandas**, **numpy**, **scikit-learn**, **yfinance**, **ta**, **mplfinance** pour les données et la prédiction  
- **transformers**, **torch**, **safetensors** pour le NLP  
- **sqlalchemy**, **pyyaml**, **typer**, **loguru**, etc. pour le reste  

Contraintes notables :
- `numpy>=1.26.4,<2.0` (pas de NumPy 2.x)
- `pandas` selon la version de Python (2.0.3 / 2.2.2 / 2.2.3)
- Python recommandé : 3.11+ (PFE_MVP exige `>=3.11`)

---

## 3. Fichiers et dossiers utilisés par le dashboard

### 3.1 Fichiers obligatoires (sinon données vides ou erreurs)

| Fichier / Dossier | Usage |
|-------------------|--------|
| `users_db.json` | Auth (comptes, profils). Créé à la volée si absent. |
| `stock_data (1).csv` | Liste d’actifs pour le tableau (colonnes type Symbole/Nom/Prix ou Ticker/Name/Close). **Présent à la racine.** |
| `AAPL.csv` | Historique de prix AAPL (fallback). **Présent à la racine.** |
| `NLP/hybrid_news_financial_classified_*.csv` | News avec sentiment + `is_financial`. **Présent** (`hybrid_news_financial_classified_20260129_143644.csv`). |

### 3.2 Données PFE_MVP (optionnelles mais enrichissent le dashboard)

Ces chemins sont **relatifs à la racine du projet** (où se trouve `dashboard.py`).

| Chemin | Usage |
|--------|--------|
| `PFE_MVP/data/raw/<TICKER>.csv` | Historique de prix par ticker. **Dossier `data/` absent** : à créer via `run_all.py` ou `fetch --all`. |
| `PFE_MVP/stock-pattern/src/candles/<TICKER>_daily.json` | Chandeliers par symbole. **Dossier non listé** : créé par `scan-patterns`. |
| `PFE_MVP/stock-pattern/src/patterns/<TICKER>_daily_patterns.json` | Patterns détectés. **Idem.** |
| `PFE_MVP/reports/predictions/<TICKER>_next_day.json` | Prédiction prochain jour. **Créé par `predict`.** |
| `NLP/xai_<SYM>_*.csv` | Explicabilité XAI. **Présents** dans `NLP/`. |
| `reports/anomaly_report.json` ou `Prediction_Anomalies/reports/anomaly_report.json` | Rapport d’anomalies. **reports/anomaly_report.json présent.** |

### 3.3 Config PFE_MVP

| Fichier | Rôle |
|---------|------|
| `PFE_MVP/configs/tickers.yaml` | Liste des tickers Yahoo (indices, equities, commodities). |
| `PFE_MVP/configs/watchlist.txt` | Liste des symboles pour le dashboard et stock-pattern (ex. AAPL, GSPC, …). **Présent.** |

---

## 4. État actuel du dépôt (diagnostic)

- **OK** – `stock_data (1).csv`, `AAPL.csv` à la racine → le tableau peut afficher des actifs et un historique minimal.  
- **OK** – `NLP/hybrid_news_financial_classified_*.csv` → news et sentiment disponibles.  
- **OK** – `users_db.json` présent → auth et profils utilisables.  
- **OK** – `NLP/xai_*.csv` pour plusieurs symboles → onglet XAI utilisable.  
- **OK** – `reports/anomaly_report.json` → section anomalies utilisable.  
- **Manquant** – `PFE_MVP/data/` (données brutes par ticker) : pas de `data/raw/<TICKER>.csv` → prix détaillés par actif viennent du CSV racine ou de stock-pattern une fois générés.  
- **À générer** – `PFE_MVP/stock-pattern/src/candles/` et `patterns/` : créés par `run_all.py` ou `scan-patterns` après un fetch.  
- **À générer** – `PFE_MVP/reports/predictions/` : créé par `run_all.py` ou `predict` après entraînement.

En résumé : **le dashboard peut déjà tourner en local** avec les fichiers actuels ; pour avoir **tous les graphiques, patterns et prédictions par actif**, il faut exécuter le pipeline PFE_MVP (voir ci‑dessous).

---

## 5. Bug repéré dans dashboard.py

Dans `qp_get_all()` (lignes 198–227) : le bloc `except` construit `news_processed` mais **ne fait aucun `return`**. En cas d’exception sur `st.query_params`, la fonction renvoie donc `None`, et `qp = qp_get_all()` puis `if "auth" in qp` peuvent provoquer une erreur. À corriger en retournant par exemple `{}` ou un dict par défaut dans le `except`.

---

## 6. Que lancer pour avoir le dashboard en local

### Étape 1 : Environnement Python

```bash
cd /Users/hugofouan/Documents/ECE/PFE
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### Étape 2 : Installer les dépendances

**Important :** monte d’abord pip (évite les erreurs avec `pyproject.toml` et l’install éditable) :

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
cd PFE_MVP && pip install -e . && cd ..
```

Tu dois rester **à la racine du projet** pour les commandes suivantes. Si tu es déjà dans `PFE_MVP`, fais d’abord `cd ..` pour revenir à la racine.

Si tu as NumPy 2.x ou des conflits :

```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

### Étape 3 : Lancer le dashboard

**Option A – Dashboard complet (recommandé)**  
Depuis la **racine du projet** (`/Users/hugofouan/Documents/ECE/PFE`) :

```bash
streamlit run dashboard.py
```

**Option B – Version simplifiée (login + onboarding + lien vers dashboard)**  
```bash
streamlit run app.py
```

Le navigateur s’ouvre en général sur `http://localhost:8501`. Si un autre port est utilisé, Streamlit l’affiche dans le terminal.

### Étape 4 (optionnel) : Données complètes pour graphiques / patterns / prédictions

Pour générer `PFE_MVP/data/raw/*.csv`, candles, patterns et prédictions, exécute **depuis la racine du projet** (où se trouve `run_all.py`) :

```bash
cd /Users/hugofouan/Documents/ECE/PFE
python run_all.py --all
```

Ou en détaillé :

```bash
python -m stockpred.cli fetch --all
python -m stockpred.cli train --ticker AAPL   # ou tous les tickers
python -m stockpred.cli predict --ticker AAPL
python -m stockpred.cli scan-patterns --tf daily --scan-all --summary
```

Après ça, le dashboard pourra charger historiques, patterns et prédictions pour les tickers configurés.

---

## 7. Résumé des commandes utiles

| Objectif | Commande |
|----------|----------|
| Dashboard en local (complet) | `streamlit run dashboard.py` |
| Dashboard simple (app) | `streamlit run app.py` |
| Tout régénérer (données + modèles + patterns) | `python run_all.py --all` |
| Seulement fetch des données | `python -m stockpred.cli fetch --all` |
| **Mise à jour des données du jour** (prix uniquement) | `python update_daily_data.py` |
| Mise à jour complète (fetch + train + predict + patterns) | `python update_daily_data.py --full` |
| Seulement patterns (avec données déjà présentes) | `python -m stockpred.cli scan-patterns --tf daily --scan-all --summary` |

Toutes les commandes ci‑dessus sont à exécuter depuis la **racine du projet** (`/Users/hugofouan/Documents/ECE/PFE`), avec le venv activé.

---

## 8. Checklist rapide

- [ ] Venv créé et activé  
- [ ] `pip install -r requirements.txt`  
- [ ] `cd PFE_MVP && pip install -e . && cd ..`  
- [ ] Lancer `streamlit run dashboard.py`  
- [ ] (Optionnel) `python run_all.py --all` pour données complètes  

Si tout est coché, le dashboard est utilisable en local ; avec `run_all.py --all`, graphiques, patterns et prédictions seront pleinement alimentés.

### Mise à jour des données du jour

- **Prix uniquement** (rapide) : `python update_daily_data.py` — télécharge les derniers cours pour tous les tickers (PFE_MVP/data/raw).
- **Tout** (fetch + modèles + prédictions + patterns) : `python update_daily_data.py --full` ou `python run_all.py --all`.
- Les news sont dans `NLP/hybrid_news_financial_classified_*.csv` ; pour les rafraîchir, utiliser le pipeline dans `Pipeline_Recup_Donnees` et le script NLP de classification.
