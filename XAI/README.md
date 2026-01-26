# 📊 XAI - Système d'Analyse Explicable des News Financières

Système XAI (Explainable AI) pour analyser l'impact des actualités financières sur les actifs et générer des explications détaillées sur le sentiment bullish/bearish.

## 🎯 Objectif

Transformer les données de sentiment des news en analyses explicables qui :
- **Justifient** pourquoi le sentiment est bullish ou bearish
- **Expliquent** l'impact sur le marché et le comportement attendu
- **Détaillent** les mécanismes d'influence sur les investisseurs
- **Recommandent** des actions (ACHETER/VENDRE/CONSERVER/SURVEILLER)

## 🚀 Installation

```bash
pip install pandas mistralai python-dotenv
```

## 📁 Structure

- `stock_fetcher.py` - Récupère les news avec sentiment depuis les CSV NLP
- `stock_analyzer.py` - Génère les explications XAI via l'API Mistral
- `xai_integration.py` - Module d'intégration pour le dashboard Streamlit
- `README.md` - Documentation complète

## 💻 Utilisation

### 1. Récupération des news d'un actif

```bash
# Récupérer toutes les news d'Apple
python stock_fetcher.py AAPL

# Résultat affiché:
# 📊 RÉSUMÉ SENTIMENT - AAPL
# Total: 15 news | Tendance: BULLISH
# Positif: 67.5% | Négatif: 32.5%
```

### 2. Analyse XAI complète

```bash
# Analyser l'impact des news sur Tesla
python stock_analyzer.py TSLA

# Génère une analyse détaillée avec:
# - Justification du sentiment
# - Impact sur le marché
# - Mécanismes d'influence
# - Recommandation d'action
```

### 3. Intégration dans Streamlit

```python
import sys
sys.path.append('./XAI')
from xai_integration import (
    get_xai_explanation_for_asset,
    get_sentiment_for_asset,
    format_xai_for_display
)

# Sentiment rapide (sans API)
sentiment = get_sentiment_for_asset("AAPL")
st.metric("Tendance", sentiment['sentiment_trend'])

# Analyse XAI complète (avec API Mistral)
if st.button("Analyser avec XAI"):
    analysis = get_xai_explanation_for_asset("AAPL")
    st.markdown(format_xai_for_display(analysis))
```


## ⚙️ Configuration

1. Créer un fichier `.env` dans le dossier `XAI/` :
```bash
touch .env
```

2. Ajouter votre clé API Mistral :
```env
MISTRAL_API_KEY=votre_clé_api_mistral_ici
```

3. Vérifier que les fichiers de sentiment existent dans `../NLP/` :
```
NLP/sentiment_analysis_YYYYMMDD_HHMMSS.csv
```

## 📊 Analyse XAI - Sections générées

L'analyse XAI comprend 5 sections principales :

### 1. JUSTIFICATION DU SENTIMENT
- Pourquoi le sentiment est bullish/bearish
- Éléments factuels des actualités
- Cohérence entre les sources

### 2. IMPACT SUR LE MARCHÉ
- Impact court terme (1-7 jours)
- Impact moyen terme (1-3 mois)
- Facteurs de risque identifiés

### 3. MÉCANISMES D'INFLUENCE
- Psychologie des investisseurs
- Canaux de transmission
- Effets de contagion possibles

### 4. INDICATEURS CLÉS
- Indicateurs techniques affectés
- Volume, volatilité attendus
- Niveaux de support/résistance

### 5. RECOMMANDATION
- Action: ACHETER / VENDRE / CONSERVER / SURVEILLER
- Confiance: ÉLEVÉ / MOYEN / FAIBLE
- Conditions à surveiller

## 🔗 API Disponibles

### stock_fetcher.py
```python
load_latest_sentiment_data()  # Charge le CSV le plus récent
fetch_news_for_asset(ticker)  # Récupère les news d'un actif
get_sentiment_summary(ticker)  # Calcule le résumé du sentiment
export_asset_news(ticker)      # Exporte les news en CSV
```

### stock_analyzer.py
```python
analyze_asset_news(ticker)           # Analyse complète avec XAI
analyze_multiple_assets(tickers)     # Analyse de plusieurs actifs
display_xai_analysis(analysis)       # Affiche l'analyse formatée
```

### xai_integration.py (Pour Streamlit)
```python
get_xai_explanation_for_asset(ticker)  # Analyse XAI complète (avec API)
get_sentiment_for_asset(ticker)        # Sentiment uniquement (sans API)
format_xai_for_display(analysis)       # Formatte pour Streamlit
get_news_list_for_asset(ticker)        # Liste des news
check_mistral_api()                    # Vérifie la config API
```

## 🎨 Exemple d'intégration complète dans le Dashboard

```python
# Dans dashboard.py
import sys
sys.path.append('./XAI')
from xai_integration import *

# Dans la section News
st.title("ACTUALITÉS IA")

# Filtre actif
selected_asset = st.selectbox("Actif", options=all_assets)

# Afficher sentiment rapide
sentiment = get_sentiment_for_asset(selected_asset)
col1, col2, col3 = st.columns(3)
col1.metric("Tendance", sentiment['sentiment_trend'])
col2.metric("News", sentiment['total_news'])
col3.metric("Positif", f"{sentiment['avg_positive']:.1%}")

# Bouton pour analyse XAI détaillée
if st.button("🔍 Analyse XAI Détaillée"):
    with st.spinner("Génération de l'analyse explicable..."):
        analysis = get_xai_explanation_for_asset(selected_asset)
    
    if analysis and "error" not in analysis:
        st.success(f"Recommandation: {analysis['recommendation']}")
        st.markdown(format_xai_for_display(analysis))
    else:
        st.error("Analyse non disponible")

# Afficher les news
news_list = get_news_list_for_asset(selected_asset, limit=10)
for news in news_list:
    with st.expander(f"{'🟢' if news['sentiment']=='Positive' else '🔴'} {news['title']}"):
        st.write(news['description'])
        st.write(f"**Confiance:** {news['confidence']:.1%}")
        st.link_button("Lire l'article", news['url'])
```

## 🐛 Troubleshooting

| Problème | Solution |
|----------|----------|
| "MISTRAL_API_KEY non trouvée" | Créer `.env` avec votre clé API |
| "Aucun fichier de sentiment" | Vérifier que les CSV existent dans `../NLP/` |
| "Aucune news trouvée" | Vérifier le ticker (AAPL, TSLA, etc.) |
| Analyse trop lente | Utiliser `get_sentiment_for_asset()` au lieu de l'XAI complète |

## 📝 Notes importantes

- ⚡ **Performance** : `get_sentiment_for_asset()` est instantané, `get_xai_explanation_for_asset()` appelle l'API Mistral (~2-5s)
- 💰 **Coût** : Chaque analyse XAI consomme des tokens Mistral (~1500 tokens)
- 🔄 **Mise à jour** : Les analyses utilisent le fichier CSV le plus récent dans `NLP/`
- 🎯 **Précision** : La qualité dépend de la qualité des données de sentiment en entrée

## 📚 Exemples de tickers supportés

```
Indices: SP500, CAC40, GER30
Actions: AAPL, TSLA, AMZN, MSFT, GOOGL
Entreprises FR: SAN (Sanofi), AIR (Airbus), MC (LVMH), TTE (Total)
Matières: OIL, GOLD, GAS
```

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
