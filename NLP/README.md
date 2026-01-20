# 📰 Modèle d'Analyse de Sentiment pour News Financières

> Modèle FinBERT fine-tuné pour l'analyse de sentiment de news financières longues (articles, communiqués de presse, etc.)

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture du modèle](#architecture-du-modèle)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Intégration dans un pipeline](#intégration-dans-un-pipeline)
- [API Ready Function](#api-ready-function)
- [Format des données](#format-des-données)
- [Performance](#performance)
- [Limitations](#limitations)

---

## 🎯 Vue d'ensemble

Ce modèle analyse le sentiment (positif/négatif) de textes financiers longs comme des articles de presse, des communiqués d'entreprise, etc.

### Caractéristiques principales

- **Modèle de base** : [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)
- **Tâche** : Classification binaire (Positif / Négatif)
- **Longueur maximale** : 512 tokens (~300-400 mots)
- **Format** : SafeTensors (sécurisé et rapide)
- **Données d'entraînement** : 
  - Yahoo News financières
  - Financial Phrase Bank
  - Corpus all-data.csv
  - **Total** : ~70,000 exemples équilibrés

### Différence avec le modèle Tweets

| Aspect | News Model | Tweets Model |
|--------|-----------|--------------|
| **Max Length** | 512 tokens | 128 tokens |
| **Use Case** | Articles longs | Textes courts |
| **Training Data** | News financières | Tweets financiers |
| **Chemin** | `./news_finbert_sentiment_model` | `./tweets_finbert_sentiment_model` |

---

## 🏗️ Architecture du modèle

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

**Labels**:
- `0` → Negative
- `1` → Positive

---

## 🚀 Installation

### Prérequis

```bash
pip install torch transformers pandas newsapi-python python-dotenv
```

### Structure des fichiers

```
NLP/
├── news_finbert_sentiment_model/    # Modèle fine-tuné
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   └── vocab.txt
├── News_API_Integration.ipynb       # Exemple d'intégration
└── .env                             # Clés API (NEWSAPI_API_KEY)
```

---

## ⚡ Utilisation rapide

### 1. Chargement du modèle

```python
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Charger le modèle
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

### 2. Analyse d'un texte

```python
def analyze_sentiment(text, model, tokenizer, device, max_length=512):
    """
    Analyse le sentiment d'un texte financier
    
    Args:
        text (str): Texte à analyser
        model: Modèle FinBERT
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
    
    # Prédiction
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

### 3. Exemple d'utilisation

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

**Output**:
```
Sentiment: Positive
Confidence: 94.23%
Prob Positive: 94.23%
Prob Negative: 5.77%
```

---

## 🔄 Intégration dans un pipeline

### Pipeline complet : Fetch + Analyze

```python
from newsapi.newsapi_client import NewsApiClient
from datetime import datetime, timedelta
import pandas as pd

# Initialiser NewsAPI
newsapi = NewsApiClient(api_key="YOUR_API_KEY")

def analyze_news_pipeline(query="finance", page_size=20):
    """
    Pipeline complet : récupère les news et analyse le sentiment
    
    Args:
        query (str): Requête de recherche (ex: "Apple OR Tesla")
        page_size (int): Nombre d'articles à récupérer
    
    Returns:
        pd.DataFrame: Résultats avec sentiment analysis
    """
    # 1. Récupérer les news
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
        
        # Stocker les résultats
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

# Filtrer par confiance élevée
df_high_confidence = df[df['confidence'] > 0.8]

print(f"Articles analysés: {len(df)}")
print(f"Articles haute confiance (>80%): {len(df_high_confidence)}")
print(f"Sentiment positif: {(df['sentiment'] == 'Positive').sum()}")
print(f"Sentiment négatif: {(df['sentiment'] == 'Negative').sum()}")
```

### Export des résultats

```python
# CSV
output_file = f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
df.to_csv(output_file, index=False)

# JSON (pour API)
output_json = output_file.replace('.csv', '.json')
df.to_json(output_json, orient='records', indent=2)
```

---

## 🌐 API Ready Function

Fonction prête pour intégration backend/frontend:

```python
def get_sentiment_analysis(query, max_results=20):
    """
    Fonction API-ready pour l'équipe backend/frontend
    
    Args:
        query (str): Requête de recherche
        max_results (int): Nombre max de résultats
    
    Returns:
        dict: Format standardisé pour API
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

**Exemple de réponse JSON**:
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

## 📊 Format des données

### Input

```python
{
    "text": str,           # Texte à analyser (max 512 tokens)
    "max_length": int     # Optional, défaut: 512
}
```

### Output

```python
{
    "sentiment": str,        # "Positive" ou "Negative"
    "confidence": float,     # 0.0 à 1.0
    "prob_negative": float,  # Probabilité classe négative
    "prob_positive": float   # Probabilité classe positive
}
```

### Traitement par batch

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
        
        # Prédictions
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probabilities = F.softmax(outputs.logits, dim=1)
            predictions = torch.argmax(outputs.logits, dim=1)
        
        # Formater résultats
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

## 📈 Performance

### Métriques sur le test set

```
Accuracy:  0.8923
Precision: 0.8956
Recall:    0.8891
F1-Score:  0.8923
```

### Rapport de classification

```
              precision    recall  f1-score   support

     Négatif     0.89      0.90      0.89      5234
     Positif     0.90      0.89      0.89      5287

    accuracy                         0.89     10521
   macro avg     0.89      0.89      0.89     10521
weighted avg     0.89      0.89      0.89     10521
```

### Temps d'inférence

| Device | Batch Size | Temps par article |
|--------|-----------|-------------------|
| CPU    | 1         | ~150ms           |
| CPU    | 8         | ~80ms            |
| GPU    | 1         | ~20ms            |
| GPU    | 32        | ~5ms             |

---

## ⚠️ Limitations

### 1. Longueur de texte
- **Maximum**: 512 tokens (~300-400 mots)
- **Recommandation**: Pour articles très longs, analyser le titre + lead (premiers paragraphes)

```python
# Exemple de gestion de textes longs
def prepare_long_text(title, content, max_words=300):
    """Prépare un article long pour l'analyse"""
    words = content.split()[:max_words]
    truncated_content = ' '.join(words)
    return f"{title} {truncated_content}"
```

### 2. Langue
- **Optimisé pour**: Anglais
- **Autres langues**: Performances réduites (modèle entraîné sur corpus anglais)

### 3. Domaine
- **Optimisé pour**: Finance, économie, business
- **Hors domaine**: Peut être moins performant sur textes généraux

### 4. Neutralité
- Le modèle est entraîné sur **binaire** (Positif/Négatif)
- Pas de classe "Neutre" → textes neutres sont classés comme Positif ou Négatif
- **Solution**: Filtrer par `confidence` pour ignorer prédictions peu sûres

```python
# Filtrer prédictions incertaines
def filter_confident_predictions(df, threshold=0.75):
    """Garde seulement les prédictions avec confiance > threshold"""
    return df[df['confidence'] > threshold]
```

---

## 🔧 Configuration avancée

### Ajuster la confiance minimum

```python
def analyze_with_threshold(text, model, tokenizer, device, threshold=0.8):
    """Retourne sentiment seulement si confiance > threshold"""
    result = analyze_sentiment(text, model, tokenizer, device)
    
    if result['confidence'] < threshold:
        result['sentiment'] = 'Uncertain'
    
    return result
```

### Logging détaillé

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

## 📚 Ressources

- **Notebook d'entraînement**: [Analyse_News.ipynb](./Analyse_News.ipynb)
- **Intégration API**: [News_API_Integration.ipynb](./News_API_Integration.ipynb)
- **Modèle Hugging Face**: [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)
- **NewsAPI Documentation**: [newsapi.org/docs](https://newsapi.org/docs)

---

## 🤝 Support

Pour toute question ou problème:

1. Vérifier les exemples dans `News_API_Integration.ipynb`
2. Consulter la section [Limitations](#limitations)
3. Vérifier les versions des dépendances

### Dépendances recommandées

```txt
torch>=2.0.0
transformers>=4.30.0
pandas>=1.5.0
newsapi-python>=0.2.7
python-dotenv>=1.0.0
```

---

## 📝 Changelog

### v1.0.0 (2026-01-20)
- ✅ Modèle FinBERT fine-tuné sur 70k+ exemples
- ✅ Support sequences longues (512 tokens)
- ✅ Format SafeTensors
- ✅ Pipeline NewsAPI intégré
- ✅ API-ready functions

---

**Dernière mise à jour**: 20 janvier 2026  
**Version du modèle**: 1.0.0  
**Auteur**: Équipe NLP - FinsightAI
