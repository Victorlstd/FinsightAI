# FinsightAI

Projet principal de collecte, traitement et analyse de donnees financieres, avec prediction de direction (UP/DOWN), detection de patterns, pipeline de news et modele NLP de sentiment.

## Sommaire
- [PFE_MVP](#pfe_mvp)
- [Pipeline de Recuperation de Donnees](#pipeline-de-recuperation-de-donnees)
- [Modele NLP - Analyse de Sentiment](#modele-nlp---analyse-de-sentiment)

---

## PFE_MVP

Projet principal: prediction de direction (UP/DOWN) + visualisation.
Sous-projet integre: detection de patterns de chart (stock-pattern).

### Setup (dans PFE_MVP)
```bash
pip install -r requirements.txt
cd PFE_MVP
pip install -e .
```
Si tu as deja un NumPy 2.x dans l'environnement, reinstalle proprement :
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

### Commande universelle (recommande)
Une seule commande pour tout faire: telecharger les donnees, entrainer, predire, puis scanner les patterns.
```bash
python run_all.py
```
La commande installe automatiquement le package editable si besoin.

Options utiles:
```bash
python run_all.py --all --skip-train
python run_all.py --all --skip-predict
```

Options utiles:
```bash
python -m stockpred.cli run-all --all --skip-train
python -m stockpred.cli run-all --all --skip-predict
```

### Commandes detaillees (si besoin)
0) Telecharger/mettre a jour les donnees
```bash
python -m stockpred.cli fetch --all
```

1) Entrainer un modele (par ticker)
```bash
python -m stockpred.cli train --ticker AAPL
```

2) Predire demain avec le modele exporte (.safetensors)
```bash
python -m stockpred.cli predict --ticker AAPL
```

3) Scanner les patterns (tous les tickers de configs/tickers.yaml)
```bash
python -m stockpred.cli scan-patterns --tf daily --scan-all --summary
```

### Outputs prediction
- data/raw/<TICKER>.csv
- data/processed/<TICKER>_features.parquet
- models/<TICKER>/model.safetensors
- models/<TICKER>/meta.yaml
- models/<TICKER>/scaler.pkl
- reports/forecast/<TICKER>_next_day.png

Ces dossiers sont ignores par git et doivent etre regeneres localement via les commandes ci-dessus.

### Outputs patterns
- stock-pattern/src/candles/<TICKER>_daily.json
- stock-pattern/src/patterns/<TICKER>_daily_patterns.json

Ces fichiers sont ignores par git et doivent etre regeneres localement.

### Configs
- configs/tickers.yaml: liste des tickers
- configs/watchlist.txt: watchlist pour stock-pattern
- configs/stock-pattern.json: config du scanner

---

## Pipeline de Recuperation de Donnees

Pipeline de collecte et traitement de donnees pour l'analyse d'impact des evenements sur les marches financiers.

### 🎯 Objectif

Collecter des evenements macro-economiques et sectoriels qui peuvent impacter les actifs financiers sans les mentionner directement, puis les correler avec les mouvements de marche.

### 📊 Actifs Surveilles

#### Indices (3)
- SP500 (US)
- CAC40 (France)
- GER30 (Allemagne)

#### Actions (12)
- Tech: APPLE, AMAZON, TESLA, CASIC
- Pharma: SANOFI
- Defense/Aerospatial: THALES, AIRBUS
- Luxe: LVMH
- Energie: TOTALENERGIES, ENGIE
- Hotellerie: INTERCONT_HOTELS
- Automobile: STELLANTIS

#### Matieres Premieres (3)
- OIL (Petrole)
- GOLD (Or)
- GAS (Gaz)

### 🚀 Installation

```bash
# Creer l'environnement virtuel
python -m venv venv

# Activer l'environnement
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate  # Windows

# Installer les dependances
pip install -r requirements.txt
```

### 📁 Structure du Projet

```
Pipeline recup Donnees/
├── config/
│   ├── config.yaml              # Configuration generale
│   └── news_strategy.yaml       # Strategie de collecte de news
├── src/
│   ├── collectors/
│   │   ├── financial_data_collector.py
│   │   ├── news_collector.py    # Ancien collecteur (deprecie)
│   │   ├── hybrid_news_collector.py  # Nouveau collecteur hybride
│   │   ├── news_impact_mapper.py     # Systeme de scoring
│   │   └── social_media_collector.py
│   ├── processors/
│   │   └── correlator.py
│   ├── storage/
│   │   └── database.py
│   └── utils/
│       ├── config_loader.py
│       └── logger.py
├── data/
│   ├── raw/news/
│   │   ├── hybrid_news_raw.csv       # News brutes
│   │   └── hybrid_news_mapped.csv    # News mappees aux actifs
│   └── processed/
├── main_collect_historical.py   # Pipeline principal
├── test_pipeline.py
├── demo_hybrid_news.py          # Demonstration du nouveau systeme
└── STRATEGIE_NEWS.md            # Documentation complete de la strategie

```

### 🎯 Nouveau Systeme de Collecte de News (Approche Hybride)

#### Principe

Au lieu de chercher des news mentionnant directement "Apple" ou "SP500", le systeme collecte :
- Evenements macro : Decisions Fed, inflation, geopolitique, etc.
- Evenements sectoriels : Regulations tech, consommation luxe, prix energie, etc.

Puis mappe intelligemment chaque news aux actifs qu'elle peut impacter.

#### Exemple Concret

News collectee :
> "Federal Reserve raises interest rates to combat inflation"

Mapping automatique :
- SP500 -> Score: 20.0 (impact macro fort)
- CAC40 -> Score: 20.0
- APPLE -> Score: 20.0
- GOLD -> Score: 26.0 (+ bonus sensibilite)
- ... (tous les actifs impactes)

Avantage : La news ne mentionne ni Apple ni SP500, mais le systeme detecte l'impact potentiel !

### 🚀 Utilisation

#### 1. Tester le nouveau systeme de news

```bash
source venv/bin/activate
python demo_hybrid_news.py
```

Cela collecte des news sur une courte periode pour demonstration.

#### 2. Collecte complete

Pour lancer une collecte sur une longue periode :

```python
from src.collectors.hybrid_news_collector import HybridNewsCollector

collector = HybridNewsCollector()

# Collecte + mapping automatique
mapped_news = collector.collect_and_map(
    start_date="2023-01-01",
    end_date="2024-12-31",
    min_relevance_score=5.0,
    max_records_per_query=250,
    delay=2.0
)
```

#### 3. Tester la pipeline

```bash
python test_pipeline.py
```

### 📊 Outputs

#### News Brutes
`data/raw/news/hybrid_news_raw.csv`
- Titre, URL, date, source
- Type d'evenement (monetary_policy, geopolitical_tensions, etc.)
- Categorie (macro ou sector)

#### News Mappees
`data/raw/news/hybrid_news_mapped.csv`
- Toutes les colonnes des news brutes
- asset : Actif impacte
- relevance_score : Score de pertinence (5-100)
- matched_events : Evenements detectes

### ⚙️ Configuration

#### Personnaliser les evenements surveilles

Editer `config/news_strategy.yaml` :

```yaml
macro_events:
  monetary_policy:
    keywords:
      - "Federal Reserve"
      - "interest rate"
      # Ajoutez vos keywords
    impact_score: 10
    affects: ["all"]
```

#### Ajuster le scoring

Dans `src/collectors/news_impact_mapper.py`, modifier la formule de scoring.

### 📚 Documentation

- STRATEGIE_NEWS.md - Documentation complete de la strategie hybride
- demo_hybrid_news.py - Code commente avec exemples

### 🛠️ Technologies

- Python 3.12
- GDELT - Collecte de news globales
- yfinance - Donnees financieres
- pandas - Traitement de donnees
- SQLAlchemy - Stockage base de donnees

### 📈 Resultats de Demonstration

Sur une periode de test de 5 jours (15-20 janvier 2024) :
- 58 news uniques collectees
- 660 associations news-actifs creees
- 18 actifs impactes
- Score moyen : 10-12 par actif

Types d'evenements detectes :
1. Sante/Pandemie - 324 associations
2. Evenements politiques - 162 associations
3. Politique monetaire - 126 associations
4. Consommation luxe - 48 associations

### 📝 Notes

- Le systeme gere automatiquement le rate-limiting de GDELT
- Les news sont dedupliquees par URL
- Le delai entre requetes est configurable (defaut: 2 secondes)

### 🤝 Contribution

Pour modifier ou ameliorer :
1. Ajuster les keywords dans `config/news_strategy.yaml`
2. Modifier le scoring dans `news_impact_mapper.py`
3. Tester avec `demo_hybrid_news.py`

---

## Modele NLP - Analyse de Sentiment

> Modele FinBERT fine-tune pour l'analyse de sentiment de news financieres longues (articles, communiques de presse, etc.)

### 📋 Table des matieres

- [Vue d'ensemble](#vue-densemble)
- [Architecture du modele](#architecture-du-modele)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Integration dans un pipeline](#integration-dans-un-pipeline)
- [API Ready Function](#api-ready-function)
- [Format des donnees](#format-des-donnees)
- [Performance](#performance)
- [Limitations](#limitations)

---

### 🎯 Vue d'ensemble

Ce modele analyse le sentiment (positif/negatif) de textes financiers longs comme des articles de presse, des communiques d'entreprise, etc.

#### Caracteristiques principales

- Modele de base : ProsusAI/finbert
- Tache : Classification binaire (Positif / Negatif)
- Longueur maximale : 512 tokens (~300-400 mots)
- Format : SafeTensors (securise et rapide)
- Donnees d'entrainement :
  - Yahoo News financieres (https://github.com/TobeyYang/Yahoo-News-Dataset)
  - Financial Phrase Bank (https://huggingface.co/datasets/takala/financial_phrasebank)
  - Corpus all-data.csv (https://www.kaggle.com/datasets/ankurzin/sentiment-analysis-for-financial-news)
  - Total : ~70,000 exemples equilibres

#### Difference avec le modele Tweets

| Aspect | News Model | Tweets Model |
|--------|-----------|--------------|
| Max Length | 512 tokens | 128 tokens |
| Use Case | Articles longs | Textes courts |
| Training Data | News financieres | Tweets financiers |
| Chemin | ./news_finbert_sentiment_model | ./tweets_finbert_sentiment_model |

---

### 🏗️ Architecture du modele

```
Input Text (max 512 tokens)
        ↓
   Tokenization (FinBERT Tokenizer)
        ↓
   BERT Encoder (12 layers)
        ↓
   Classification Head (2 classes)
        ↓
   Output: [Negative, Positive] probabilities
```

Labels:
- 0 -> Negative
- 1 -> Positive

---

### 🚀 Installation

#### Prerequis

```bash
pip install -r requirements.txt
```

#### Structure des fichiers

```
NLP/
├── news_finbert_sentiment_model/    # Modele fine-tune
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   └── vocab.txt
├── News_API_Integration.ipynb       # Exemple d'integration
└── .env                             # Cles API (NEWSAPI_API_KEY)
```

---

### ⚡ Utilisation rapide

#### 1. Chargement du modele

```python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Charger le modele
MODEL_PATH = "./news_finbert_sentiment_model"
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    num_labels=2,
    use_safetensors=True
)
model.to(device)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
```

#### 2. Analyse d'un texte

```python
def analyze_sentiment(text, model, tokenizer, device, max_length=512):
    """
    Analyse le sentiment d'un texte financier
    
    Args:
        text (str): Texte a analyser
        model: Modele FinBERT
        tokenizer: Tokenizer FinBERT
        device: torch.device
        max_length (int): Longueur max (512 pour news)
    
    Returns:
        dict: {
            'sentiment': 'Positive' ou 'Negative',
            'confidence': float (0-1),
            'prob_negative': float,
            'prob_positive': float
        }
    """
    if not text or len(text.strip()) == 0:
        return {
            'sentiment': 'Unknown',
            'confidence': 0.0,
            'prob_negative': 0.5,
            'prob_positive': 0.5
        }
    
    # Tokenization
    encoding = tokenizer(
        text,
        add_special_tokens=True,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    
    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)
    
    # Prediction
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        probabilities = F.softmax(logits, dim=1)[0]
        
        prediction = torch.argmax(logits, dim=1).item()
        confidence = probabilities[prediction].item()
    
    sentiment_label = "Positive" if prediction == 1 else "Negative"
    
    return {
        'sentiment': sentiment_label,
        'confidence': confidence,
        'prob_negative': probabilities[0].item(),
        'prob_positive': probabilities[1].item()
    }
```

#### 3. Exemple d'utilisation

```python
# Texte d'exemple
text = """
Apple Inc. reported record-breaking quarterly earnings, exceeding analyst 
expectations. Revenue grew 28% year-over-year, driven by strong iPhone sales 
and expanding services business. The company announced a $90 billion share 
buyback program and raised its dividend by 7%.
"""

# Analyser
result = analyze_sentiment(text, model, tokenizer, device)

print(f"Sentiment: {result['sentiment']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Prob Positive: {result['prob_positive']:.2%}")
print(f"Prob Negative: {result['prob_negative']:.2%}")
```

Output:
```
Sentiment: Positive
Confidence: 94.23%
Prob Positive: 94.23%
Prob Negative: 5.77%
```

---

### 🔄 Integration dans un pipeline

#### Pipeline complet : Fetch + Analyze

```python
from newsapi.newsapi_client import NewsApiClient
from datetime import datetime, timedelta
import pandas as pd

# Initialiser NewsAPI
newsapi = NewsApiClient(api_key="YOUR_API_KEY")

def analyze_news_pipeline(query="finance", page_size=20):
    """
    Pipeline complet : recupere les news et analyse le sentiment
    
    Args:
        query (str): Requete de recherche (ex: "Apple OR Tesla")
        page_size (int): Nombre d'articles a recuperer
    
    Returns:
        pd.DataFrame: Resultats avec sentiment analysis
    """
    # 1. Recuperer les news
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    articles = newsapi.get_everything(
        q=query,
        language='en',
        from_param=from_date,
        sort_by='publishedAt',
        page_size=page_size
    )
    
    # 2. Analyser chaque article
    results = []
    for article in articles.get('articles', []):
        # Combiner titre + description
        full_text = f"{article['title']} {article.get('description', '')}"
        
        # Analyser le sentiment
        sentiment_result = analyze_sentiment(full_text, model, tokenizer, device)
        
        # Stocker les resultats
        results.append({
            'title': article['title'],
            'source': article['source']['name'],
            'published_at': article['publishedAt'],
            'sentiment': sentiment_result['sentiment'],
            'confidence': sentiment_result['confidence'],
            'prob_negative': sentiment_result['prob_negative'],
            'prob_positive': sentiment_result['prob_positive'],
            'url': article['url']
        })
    
    return pd.DataFrame(results)

# Utilisation
df = analyze_news_pipeline(query="stocks OR market", page_size=50)

# Filtrer par confiance elevee
df_high_confidence = df[df['confidence'] > 0.8]

print(f"Articles analyses: {len(df)}")
print(f"Articles haute confiance (>80%): {len(df_high_confidence)}")
print(f"Sentiment positif: {(df['sentiment'] == 'Positive').sum()}")
print(f"Sentiment negatif: {(df['sentiment'] == 'Negative').sum()}")
```

#### Export des resultats

```python
# CSV
output_file = f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df.to_csv(output_file, index=False)

# JSON (pour API)
output_json = output_file.replace('.csv', '.json')
df.to_json(output_json, orient='records', indent=2)
```

---

### 🌐 API Ready Function

Fonction prete pour integration backend/frontend:

```python
def get_sentiment_analysis(query, max_results=20):
    """
    Fonction API-ready pour l'equipe backend/frontend
    
    Args:
        query (str): Requete de recherche
        max_results (int): Nombre max de resultats
    
    Returns:
        dict: Format standardise pour API
    """
    df = analyze_news_pipeline(query=query, page_size=max_results)
    
    if df.empty:
        return {
            "status": "error",
            "message": "No news found",
            "data": []
        }
    
    return {
        "status": "success",
        "query": query,
        "total_articles": len(df),
        "positive_count": int((df['sentiment'] == 'Positive').sum()),
        "negative_count": int((df['sentiment'] == 'Negative').sum()),
        "average_confidence": float(df['confidence'].mean()),
        "timestamp": datetime.now().isoformat(),
        "articles": df.to_dict('records')
    }

# Exemple
result = get_sentiment_analysis("cryptocurrency", max_results=10)
print(f"Status: {result['status']}")
print(f"Total articles: {result['total_articles']}")
print(f"Average confidence: {result['average_confidence']:.2%}")
```

Exemple de reponse JSON:
```json
{
  "status": "success",
  "query": "cryptocurrency",
  "total_articles": 10,
  "positive_count": 6,
  "negative_count": 4,
  "average_confidence": 0.87,
  "timestamp": "2026-01-20T14:30:00",
  "articles": [
    {
      "title": "Bitcoin reaches new all-time high",
      "source": "CoinDesk",
      "published_at": "2026-01-20T10:00:00Z",
      "sentiment": "Positive",
      "confidence": 0.94,
      "prob_positive": 0.94,
      "prob_negative": 0.06,
      "url": "https://..."
    }
  ]
}
```

---

### 📊 Format des donnees

#### Input

```python
{
    "text": str,           # Texte a analyser (max 512 tokens)
    "max_length": int     # Optional, defaut: 512
}
```

#### Output

```python
{
    "sentiment": str,        # "Positive" ou "Negative"
    "confidence": float,     # 0.0 a 1.0
    "prob_negative": float,  # Probabilite classe negative
    "prob_positive": float   # Probabilite classe positive
}
```

#### Traitement par batch

```python
def analyze_batch(texts, model, tokenizer, device, batch_size=8):
    """Analyse un batch de textes pour meilleure performance"""
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize batch
        encodings = tokenizer(
            batch_texts,
            add_special_tokens=True,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        input_ids = encodings['input_ids'].to(device)
        attention_mask = encodings['attention_mask'].to(device)
        
        # Predictions
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probabilities = F.softmax(outputs.logits, dim=1)
            predictions = torch.argmax(outputs.logits, dim=1)
        
        # Formater resultats
        for j, pred in enumerate(predictions):
            results.append({
                'sentiment': 'Positive' if pred.item() == 1 else 'Negative',
                'confidence': probabilities[j][pred.item()].item(),
                'prob_negative': probabilities[j][0].item(),
                'prob_positive': probabilities[j][1].item()
            })
    
    return results
```

---

### 📈 Performance

#### Metriques sur le test set

```
Accuracy:  0.8923
Precision: 0.8956
Recall:    0.8891
F1-Score:  0.8923
```

#### Rapport de classification

```
              precision    recall  f1-score   support

     Negatif     0.89      0.90      0.89      5234
     Positif     0.90      0.89      0.89      5287

    accuracy                         0.89     10521
   macro avg     0.89      0.89      0.89     10521
weighted avg     0.89      0.89      0.89     10521
```

#### Temps d'inference

| Device | Batch Size | Temps par article |
|--------|-----------|-------------------|
| CPU    | 1         | ~150ms           |
| CPU    | 8         | ~80ms            |
| GPU    | 1         | ~20ms            |
| GPU    | 32        | ~5ms             |

---

### ⚠️ Limitations

#### 1. Longueur de texte
- Maximum: 512 tokens (~300-400 mots)
- Recommandation: Pour articles tres longs, analyser le titre + lead (premiers paragraphes)

```python
# Exemple de gestion de textes longs
def prepare_long_text(title, content, max_words=300):
    """Prepare un article long pour l'analyse"""
    words = content.split()[:max_words]
    truncated_content = ' '.join(words)
    return f"{title} {truncated_content}"
```

#### 2. Langue
- Optimise pour: Anglais
- Autres langues: Performances reduites (modele entraine sur corpus anglais)

#### 3. Domaine
- Optimise pour: Finance, economie, business
- Hors domaine: Peut etre moins performant sur textes generaux

#### 4. Neutralite
- Le modele est entraine sur binaire (Positif/Negatif)
- Pas de classe "Neutre" -> textes neutres sont classes comme Positif ou Negatif
- Solution: Filtrer par `confidence` pour ignorer predictions peu sures

```python
# Filtrer predictions incertaines
def filter_confident_predictions(df, threshold=0.75):
    """Garde seulement les predictions avec confiance > threshold"""
    return df[df['confidence'] > threshold]
```

---

### 🔧 Configuration avancee

#### Ajuster la confiance minimum

```python
def analyze_with_threshold(text, model, tokenizer, device, threshold=0.8):
    """Retourne sentiment seulement si confiance > threshold"""
    result = analyze_sentiment(text, model, tokenizer, device)
    
    if result['confidence'] < threshold:
        result['sentiment'] = 'Uncertain'
    
    return result
```

#### Logging detaille

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_with_logging(text, model, tokenizer, device):
    """Version avec logging pour debugging"""
    logger.info(f"Analyzing text (length: {len(text)} chars)")
    
    result = analyze_sentiment(text, model, tokenizer, device)
    
    logger.info(f"Prediction: {result['sentiment']} (conf: {result['confidence']:.2%})")
    
    return result
```

---

### 📚 Ressources

- Notebook d'entrainement: Analyse_News.ipynb
- Integration API: News_API_Integration.ipynb
- Modele Hugging Face: ProsusAI/finbert
- NewsAPI Documentation: newsapi.org/docs

---

### 🤝 Support

Pour toute question ou probleme:

1. Verifier les exemples dans `News_API_Integration.ipynb`
2. Consulter la section Limitations
3. Verifier les versions des dependances

#### Dependances recommandees

```txt
torch>=2.0.0
transformers>=4.30.0
pandas>=1.5.0
newsapi-python>=0.2.7
python-dotenv>=1.0.0
```

---

### 📝 Changelog

#### v1.0.0 (2026-01-20)
- Modele FinBERT fine-tune sur 70k+ exemples
- Support sequences longues (512 tokens)
- Format SafeTensors
- Pipeline NewsAPI integre
- API-ready functions

Derniere mise a jour: 20 janvier 2026
Version du modele: 1.0.0
Auteur: Equipe NLP - FinsightAI
