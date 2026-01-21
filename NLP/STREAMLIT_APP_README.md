# 📈 Application Streamlit - Analyse de Sentiment

Application Streamlit pour l'analyse de sentiment des news financières utilisant le modèle FinBERT.

## 🚀 Lancement de l'application

### En tant qu'application standalone

```bash
cd NLP
streamlit run streamlit_sentiment_app.py
```

L'application sera accessible sur `http://localhost:8501`

## 🔧 Intégration dans un projet Streamlit existant

Cette page a été conçue pour être facilement intégrable dans un projet Streamlit plus large.

### Méthode 1: Import direct de la fonction

```python
# Dans votre app principale (ex: main_app.py)
import streamlit as st
from NLP.streamlit_sentiment_app import render_sentiment_analysis_page

# Créer une page dans votre navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", ["Accueil", "Analyse de Sentiment", "Autre Page"])
    
    if page == "Analyse de Sentiment":
        render_sentiment_analysis_page()
    elif page == "Accueil":
        st.write("Page d'accueil")
    # ... autres pages
```

### Méthode 2: Avec st.navigation (Streamlit Multi-Page Apps)

Structure du projet:
```
votre_projet/
├── main.py
└── pages/
    ├── 1_sentiment_analysis.py
    └── 2_autre_page.py
```

Dans `pages/1_sentiment_analysis.py`:
```python
from NLP.streamlit_sentiment_app import render_sentiment_analysis_page

render_sentiment_analysis_page()
```

Puis lancez: `streamlit run main.py`

### Méthode 3: Copier le fichier dans votre projet

1. Copiez `streamlit_sentiment_app.py` dans le dossier `pages/` de votre projet
2. Renommez-le en `1_📈_Sentiment_Analysis.py` (le chiffre définit l'ordre)
3. Streamlit détectera automatiquement la page

## 📦 Dépendances requises

```bash
pip install streamlit pandas numpy torch transformers plotly
```

Ou ajoutez à votre `requirements.txt`:
```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
torch>=2.0.0
transformers>=4.35.0
plotly>=5.18.0
```

## ⚙️ Configuration

Modifiez les constantes en haut du fichier si nécessaire:

```python
NEWS_CSV_PATH = Path("../Pipeline_Recup_Donnees/data/raw/news/hybrid_news_mapped.csv")
MODEL_PATH = "./news_finbert_sentiment_model"
```

## 🎯 Fonctionnalités

- ✅ Chargement automatique du modèle FinBERT (avec cache)
- ✅ Analyse de sentiment sur toutes les news
- ✅ Visualisations interactives (Plotly)
- ✅ Filtres par sentiment et asset
- ✅ Export des résultats en CSV
- ✅ Interface responsive et intuitive
- ✅ Barre de progression en temps réel
- ✅ Métriques globales

## 📊 Captures d'écran

L'application affiche:
- Métriques globales (total, positives, négatives, confiance moyenne)
- Graphique en camembert de la distribution des sentiments
- Graphique en barres du sentiment par asset
- Histogramme de la distribution de la confiance
- Tableau filtrable et triable des résultats
- Bouton de téléchargement CSV

## 🔒 Bonnes pratiques

- Le modèle est chargé une seule fois grâce à `@st.cache_resource`
- Les données sont mises en cache avec `@st.cache_data`
- Interface modulaire pour faciliter l'intégration
- Code bien documenté et structuré
- Gestion des erreurs pour une meilleure UX

## 🐛 Troubleshooting

### Le modèle ne se charge pas
- Vérifiez que le dossier `news_finbert_sentiment_model` existe
- Vérifiez les permissions d'accès

### Les données ne se chargent pas
- Vérifiez le chemin vers `hybrid_news_mapped.csv`
- Assurez-vous que le fichier contient les colonnes nécessaires

### Problème de mémoire
- L'analyse peut consommer beaucoup de RAM pour un grand nombre de news
- Envisagez d'analyser par batch si nécessaire

## 📞 Support

Pour toute question ou problème, consultez le code source ou modifiez selon vos besoins.
