"""
Page Streamlit pour l'analyse de sentiment des news financières
Utilise le modèle FinBERT pour analyser le sentiment des news mappées aux assets

Cette page est conçue pour être facilement intégrable dans un projet Streamlit plus large.
"""

import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')


# ==================== CONFIGURATION ====================
NEWS_CSV_PATH = Path("../Pipeline_Recup_Donnees/data/raw/news/hybrid_news_mapped.csv")
MODEL_PATH = "./news_finbert_sentiment_model"


# ==================== FONCTIONS UTILITAIRES ====================

@st.cache_resource
def load_model(model_path):
    """Charge le modèle FinBERT et le tokenizer (avec cache)"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        num_labels=2,
        use_safetensors=True
    )
    model.to(device)
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    return model, tokenizer, device


@st.cache_data
def load_news_data(csv_path):
    """Charge et déduplique les données de news"""
    df = pd.read_csv(csv_path)
    df_unique = df.drop_duplicates(subset=['url']).copy()
    return df_unique


def analyze_sentiment(text, model, tokenizer, device, max_length=512):
    """
    Analyse le sentiment d'un texte avec le modèle FinBERT
    
    Returns:
        dict avec sentiment, confiance, et probabilités
    """
    if not text or pd.isna(text) or len(str(text).strip()) == 0:
        return {
            'sentiment': 'Unknown',
            'confidence': 0.0,
            'prob_negative': 0.5,
            'prob_positive': 0.5
        }
    
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


def analyze_all_news(df, model, tokenizer, device):
    """Analyse le sentiment de toutes les news du DataFrame"""
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(df)
    
    for idx, row in df.iterrows():
        result = analyze_sentiment(row['title'], model, tokenizer, device)
        results.append(result)
        
        # Mise à jour de la progression
        progress = len(results) / total
        progress_bar.progress(progress)
        status_text.text(f"Analyse en cours: {len(results)}/{total} news")
    
    progress_bar.empty()
    status_text.empty()
    
    # Ajouter les résultats au DataFrame
    df['sentiment'] = [r['sentiment'] for r in results]
    df['confidence'] = [r['confidence'] for r in results]
    df['prob_negative'] = [r['prob_negative'] for r in results]
    df['prob_positive'] = [r['prob_positive'] for r in results]
    
    return df


# ==================== INTERFACE STREAMLIT ====================

def main():
    """Fonction principale pour l'interface Streamlit"""
    
    st.set_page_config(
        page_title="Analyse de Sentiment - News Financières",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Analyse de Sentiment des News Financières")
    st.markdown("---")
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"**Modèle:** FinBERT\n\n**Device:** {'GPU 🚀' if torch.cuda.is_available() else 'CPU 💻'}")
        
        # Option pour rafraîchir les données
        if st.button("🔄 Recharger les données"):
            st.cache_data.clear()
            st.rerun()
    
    # Chargement du modèle
    with st.spinner("Chargement du modèle FinBERT..."):
        try:
            model, tokenizer, device = load_model(MODEL_PATH)
            st.success("✅ Modèle chargé avec succès")
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du modèle: {e}")
            return
    
    # Chargement des données
    with st.spinner("Chargement des données..."):
        try:
            df_news = load_news_data(NEWS_CSV_PATH)
            st.success(f"✅ {len(df_news)} news uniques chargées")
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données: {e}")
            return
    
    # Bouton pour lancer l'analyse
    if st.button("🚀 Lancer l'analyse de sentiment", type="primary"):
        with st.spinner("Analyse en cours..."):
            df_analyzed = analyze_all_news(df_news, model, tokenizer, device)
            st.session_state['df_analyzed'] = df_analyzed
            st.success("✅ Analyse terminée!")
    
    # Afficher les résultats si disponibles
    if 'df_analyzed' in st.session_state:
        df_analyzed = st.session_state['df_analyzed']
        
        st.markdown("---")
        st.header("📊 Résultats de l'analyse")
        
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        
        total_news = len(df_analyzed)
        positive_count = len(df_analyzed[df_analyzed['sentiment'] == 'Positive'])
        negative_count = len(df_analyzed[df_analyzed['sentiment'] == 'Negative'])
        avg_confidence = df_analyzed['confidence'].mean()
        
        col1.metric("Total News", total_news)
        col2.metric("Positives", positive_count, f"{positive_count/total_news*100:.1f}%")
        col3.metric("Négatives", negative_count, f"{negative_count/total_news*100:.1f}%")
        col4.metric("Confiance Moyenne", f"{avg_confidence:.2%}")
        
        # Graphiques
        st.markdown("### 📈 Visualisations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des sentiments
            sentiment_counts = df_analyzed['sentiment'].value_counts()
            fig_pie = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                title="Distribution des Sentiments",
                color=sentiment_counts.index,
                color_discrete_map={'Positive': '#00CC96', 'Negative': '#EF553B'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Sentiment par asset
            sentiment_by_asset = df_analyzed.groupby(['asset', 'sentiment']).size().reset_index(name='count')
            fig_bar = px.bar(
                sentiment_by_asset,
                x='asset',
                y='count',
                color='sentiment',
                title="Sentiment par Asset",
                barmode='group',
                color_discrete_map={'Positive': '#00CC96', 'Negative': '#EF553B'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Distribution de la confiance
        st.markdown("### 🎯 Distribution de la Confiance")
        fig_hist = px.histogram(
            df_analyzed,
            x='confidence',
            nbins=50,
            title="Distribution de la Confiance des Prédictions",
            labels={'confidence': 'Confiance', 'count': 'Nombre de news'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Tableau des résultats
        st.markdown("### 📋 Tableau des Résultats")
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            sentiment_filter = st.multiselect(
                "Filtrer par sentiment",
                options=['Positive', 'Negative'],
                default=['Positive', 'Negative']
            )
        with col2:
            assets = df_analyzed['asset'].unique().tolist()
            asset_filter = st.multiselect(
                "Filtrer par asset",
                options=assets,
                default=assets[:5] if len(assets) > 5 else assets
            )
        
        # Appliquer les filtres
        df_filtered = df_analyzed[
            (df_analyzed['sentiment'].isin(sentiment_filter)) &
            (df_analyzed['asset'].isin(asset_filter))
        ]
        
        # Colonnes à afficher (vérifier leur existence)
        display_columns = ['title', 'asset', 'sentiment', 'confidence']
        optional_columns = ['event_type', 'date', 'source', 'relevance_score']
        
        for col in optional_columns:
            if col in df_filtered.columns:
                display_columns.append(col)
        
        # Afficher le tableau
        st.dataframe(
            df_filtered[display_columns].sort_values('confidence', ascending=False),
            use_container_width=True,
            height=400
        )
        
        # Téléchargement des résultats
        st.markdown("### 💾 Télécharger les résultats")
        csv = df_analyzed.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name=f"sentiment_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


# ==================== FONCTIONS POUR INTÉGRATION ====================

def render_sentiment_analysis_page():
    """
    Fonction d'entrée pour intégrer cette page dans un autre projet Streamlit.
    Appelez simplement cette fonction dans votre application principale.
    """
    main()


# ==================== POINT D'ENTRÉE ====================

if __name__ == "__main__":
    main()
