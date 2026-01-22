import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("✓ Bibliothèques importées avec succès")
print(f"✓ PyTorch version: {torch.__version__}")
print(f"✓ Device disponible: {'GPU' if torch.cuda.is_available() else 'CPU'}")

NEWS_CSV_PATH = Path("../Pipeline_Recup_Donnees/data/raw/news/hybrid_news_mapped.csv")

# Chargement du fichier CSV
print(f"📂 Chargement des news depuis: {NEWS_CSV_PATH}")
df_news = pd.read_csv(NEWS_CSV_PATH)
df_news.head()

# Vérification des données manquantes dans les colonnes clés
print("🔍 Vérification des valeurs manquantes:")
missing_data = df_news[['title', 'url', 'asset', 'event_type']].isnull().sum()
print(missing_data)

# Dédupliquer par URL pour avoir des news uniques
print(f"\n📰 Avant déduplication: {len(df_news)} entrées")
df_news_unique = df_news.drop_duplicates(subset=['url']).copy()
print(f"📰 Après déduplication: {len(df_news_unique)} news uniques")

# Configuration du device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  Device: {device}")

# Chemin du modèle
MODEL_PATH = "./news_finbert_sentiment_model"

# Chargement du modèle et du tokenizer
print(f"\n📥 Chargement du modèle depuis: {MODEL_PATH}")
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    num_labels=2,
    use_safetensors=True
)
model.to(device)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

print("✓ Modèle FinBERT chargé et prêt")
print(f"✓ Configuration: {model.config.num_labels} labels (0=Negative, 1=Positive)")


def analyze_sentiment(text, model, tokenizer, device, max_length=512):
    """
    Analyse le sentiment d'un texte avec le modèle FinBERT
    
    Args:
        text: Texte à analyser (titre de la news)
        model: Modèle FinBERT
        tokenizer: Tokenizer
        device: CPU ou GPU
        max_length: Longueur maximale (512 pour FinBERT)
    
    Returns:
        dict avec sentiment, confiance, et probabilités
    """
    
    # Gestion des textes vides ou null
    if not text or pd.isna(text) or len(str(text).strip()) == 0:
        return {
            'sentiment': 'Unknown',
            'confidence': 0.0,
            'prob_negative': 0.5,
            'prob_positive': 0.5
        }
    
    # Tokenization
    encoding = tokenizer(
        str(text),
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
    
    # Labels: 0=Negative, 1=Positive
    sentiment_label = "Positive" if prediction == 1 else "Negative"
    
    return {
        'sentiment': sentiment_label,
        'confidence': confidence,
        'prob_negative': probabilities[0].item(),
        'prob_positive': probabilities[1].item()
    }

print("✓ Fonction analyze_sentiment définie")



print("="*80)
print("🤖 DÉBUT DE L'ANALYSE DE SENTIMENT")
print("="*80)

# Préparer les listes pour stocker les résultats
sentiments = []
confidences = []
prob_negatives = []
prob_positives = []

total_news = len(df_news_unique)
print(f"\n📰 Analyse de {total_news} news uniques...\n")

# Analyser chaque news
for idx, row in df_news_unique.iterrows():
    # Utiliser le titre pour l'analyse
    title = row['title']
    
    # Analyser le sentiment
    result = analyze_sentiment(title, model, tokenizer, device)
    
    # Stocker les résultats
    sentiments.append(result['sentiment'])
    confidences.append(result['confidence'])
    prob_negatives.append(result['prob_negative'])
    prob_positives.append(result['prob_positive'])
    
    # Afficher la progression tous les 10%
    progress = (len(sentiments) / total_news) * 100
    if len(sentiments) % max(1, total_news // 10) == 0:
        print(f"   ⏳ Progression: {progress:.0f}% ({len(sentiments)}/{total_news})")

# Ajouter les colonnes au DataFrame
df_news_unique['sentiment'] = sentiments
df_news_unique['confidence'] = confidences
df_news_unique['prob_negative'] = prob_negatives
df_news_unique['prob_positive'] = prob_positives

print(f"\n✓ Analyse terminée pour {total_news} news")
print("="*80)

# Afficher un aperçu des résultats
print("\n📊 Aperçu des résultats:")
print(df_news_unique[['title', 'sentiment', 'confidence', 'asset']].head(10))