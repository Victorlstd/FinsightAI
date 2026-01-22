# 📊 Système d'Analyse Boursière avec IA

Système automatisé pour récupérer les données boursières en temps réel et générer des recommandations d'investissement via l'IA Mistral.

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 📁 Structure

- `stock_fetcher.py` - Récupère les données boursières et met à jour le CSV
- `stock_analyzer.py` - Analyse les données avec l'API Mistral et génère des recommandations
- `stock_data.csv` - Données boursières (généré automatiquement)
- `stock_analysis.csv` - Analyses et recommandations (généré automatiquement)

## 💻 Utilisation

### Récupération des données

```bash
# Mise à jour unique
python3 stock_fetcher.py

# Mise à jour continue (toutes les 60 secondes)
python3 stock_fetcher.py --continuous

# Mise à jour toutes les 30 secondes
python3 stock_fetcher.py --continuous 30
```

### Analyse des stocks

```bash
# Analyser tous les stocks
python3 stock_analyzer.py

# Analyser un stock spécifique
python3 stock_analyzer.py APPLE
python3 stock_analyzer.py TESLA
```

## ⚙️ Configuration

1. Copier le fichier d'exemple :
```bash
cp env.example .env
```

2. Éditer `.env` et ajouter votre clé API Mistral :
```
MISTRAL_API_KEY=votre_cle_api
```

⚠️ **Important** : Le fichier `.env` est ignoré par Git et ne sera jamais commité. Ne partagez jamais votre clé API.

## 📊 Symboles suivis

### Indices
- SP 500 (^GSPC)
- CAC40 (^FCHI)
- GER30 (^GDAXI)

### Entreprises
- APPLE, AMAZON, TESLA
- SANOFI, THALES, LVMH
- ENGIE, TOTALENERGIES
- INTERCONT HOTELS, AIRBUS, STELLANTIS

### Matières premières
- OIL (CL=F)
- GOLD (GC=F)
- GAS (NG=F)

## 📝 Notes

- Les fichiers CSV sont générés automatiquement
- Le fichier `stock_data.csv` est réécrit à chaque mise à jour (pas d'historique)
- Les analyses sont sauvegardées dans `stock_analysis.csv`
- ⚠️ Les recommandations sont générées par IA et ne constituent pas des conseils financiers
