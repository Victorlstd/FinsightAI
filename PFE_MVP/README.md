# PFE_MVP

Projet principal: prediction de direction (UP/DOWN) + visualisation.  
Sous-projet integre: detection de patterns de chart (stock-pattern).

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Si tu as deja un NumPy 2.x dans l'environnement, reinstalle proprement :
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```
Pour la detection de patterns:
```bash
pip install -r stock-pattern/requirements.txt
```

## Commandes prediction (stockpred)
### 1) Télécharger/mettre à jour les données
```bash
PYTHONPATH=src python -m stockpred.cli fetch --all
```

### 2) Entraîner un modèle (par ticker)
```bash
PYTHONPATH=src python -m stockpred.cli train --ticker AAPL
```

### 3) Prédire demain avec le modèle exporté (.safetensors)
```bash
PYTHONPATH=src python -m stockpred.cli predict --ticker AAPL
```

## Commandes patterns (stock-pattern)
### Scanner les patterns (tous les tickers de configs/tickers.yaml)
```bash
PYTHONPATH=src python -m stockpred.cli scan-patterns --tf daily --scan-all --summary
```

## Outputs prediction
- data/raw/<TICKER>.csv
- data/processed/<TICKER>_features.parquet
- models/<TICKER>/model.safetensors
- models/<TICKER>/meta.yaml
- models/<TICKER>/scaler.pkl
- reports/forecast/<TICKER>_next_day.png

## Outputs patterns
- stock-pattern/src/candles/<TICKER>_daily.json
- stock-pattern/src/patterns/<TICKER>_daily_patterns.json

## Configs
- configs/tickers.yaml: liste des tickers
- configs/watchlist.txt: watchlist pour stock-pattern
- configs/stock-pattern.json: config du scanner
