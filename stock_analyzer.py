import pandas as pd
import os
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY non trouvée. Créez un fichier .env avec MISTRAL_API_KEY=votre_cle")
MISTRAL_MODEL = "mistral-large-latest"

def load_stock_data(csv_file: str = "stock_data.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_file)
        df = df.sort_values('Timestamp').groupby('Nom').last().reset_index()
        return df
    except FileNotFoundError:
        print(f"❌ Fichier {csv_file} non trouvé")
        return pd.DataFrame()

def format_stock_data(row: pd.Series) -> str:
    def clean_value(val):
        if pd.isna(val) or val == "N/A" or val == "":
            return "Non disponible"
        return str(val)
    
    prix_ouverture = clean_value(row.get('Prix d\'ouverture', 'N/A'))
    prix_actuel = clean_value(row.get('Prix actuel', 'N/A'))
    prix_cloture = clean_value(row.get('Prix de clôture précédent', 'N/A'))
    plus_haut_jour = clean_value(row.get('Plus haut (jour)', 'N/A'))
    plus_bas_jour = clean_value(row.get('Plus bas (jour)', 'N/A'))
    plus_haut_52 = clean_value(row.get('Plus haut (52 sem)', 'N/A'))
    plus_bas_52 = clean_value(row.get('Plus bas (52 sem)', 'N/A'))
    volume = clean_value(row.get('Volume', 'N/A'))
    variation = clean_value(row.get('Variation', 'N/A'))
    variation_pct = clean_value(row.get('Variation %', 'N/A'))
    
    return f"""
=== {row['Nom']} ({row['Symbole']}) ===
Catégorie: {row['Catégorie']}
Prix actuel: {prix_actuel}
Prix d'ouverture: {prix_ouverture}
Prix de clôture précédent: {prix_cloture}
Plus haut (jour): {plus_haut_jour}
Plus bas (jour): {plus_bas_jour}
Plus haut (52 semaines): {plus_haut_52}
Plus bas (52 semaines): {plus_bas_52}
Volume: {volume}
Variation: {variation}
Variation %: {variation_pct}
"""

def analyze_stock_with_mistral(client: Mistral, stock_info: str, stock_name: str) -> Dict:
    prompt = f"""Tu es un analyste financier expert. Analyse les données boursières suivantes et donne une recommandation d'investissement.

{stock_info}

Considère les éléments suivants pour ton analyse :
1. La tendance actuelle du prix (hausse/baisse)
2. La position du prix par rapport aux plus hauts/bas (52 semaines)
3. Le volume d'échanges (liquidité)
4. La volatilité et les variations récentes
5. Le contexte général du marché et l'actualité économique récente
6. Les perspectives à court et moyen terme

Fournis une analyse structurée avec :
- **Résumé** : Bref résumé de la situation (2-3 phrases)
- **Points positifs** : 2-3 points favorables
- **Points négatifs** : 2-3 points défavorables
- **Recommandation** : ACHETER / VENDRE / CONSERVER / SURVEILLER
- **Niveau de confiance** : ÉLEVÉ / MOYEN / FAIBLE
- **Justification** : Explication détaillée de la recommandation (3-4 phrases)
- **Perspective** : Horizon temporel recommandé (court/moyen/long terme)

Sois précis, factuel et équilibré dans ton analyse. reste concis pas plus de 10 lignes par stocks
cite des sources si tu as des informations sur les news ou des liens de news"""

    try:
        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        analysis_text = response.choices[0].message.content
        
        recommendation = "N/A"
        confidence = "N/A"
        
        if "ACHETER" in analysis_text.upper():
            recommendation = "ACHETER"
        elif "VENDRE" in analysis_text.upper():
            recommendation = "VENDRE"
        elif "CONSERVER" in analysis_text.upper():
            recommendation = "CONSERVER"
        elif "SURVEILLER" in analysis_text.upper():
            recommendation = "SURVEILLER"
        
        if "ÉLEVÉ" in analysis_text.upper() or "ELEVE" in analysis_text.upper():
            confidence = "ÉLEVÉ"
        elif "MOYEN" in analysis_text.upper():
            confidence = "MOYEN"
        elif "FAIBLE" in analysis_text.upper():
            confidence = "FAIBLE"
        
        return {
            "stock": stock_name,
            "recommendation": recommendation,
            "confidence": confidence,
            "analysis": analysis_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"❌ Erreur {stock_name}: {str(e)}")
        return {
            "stock": stock_name,
            "recommendation": "ERREUR",
            "confidence": "N/A",
            "analysis": f"Erreur: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def analyze_all_stocks(csv_file: str = "stock_data.csv", output_file: str = "stock_analysis.csv") -> pd.DataFrame:
    print("📊 Chargement des données...")
    df = load_stock_data(csv_file)
    
    if df.empty:
        return pd.DataFrame()
    
    print(f"✅ {len(df)} stocks chargés")
    print("🤖 Initialisation API Mistral...")
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    print("✅ API initialisée\n")
    print("🔍 Analyse en cours...\n")
    
    analyses = []
    
    for idx, row in df.iterrows():
        stock_name = row['Nom']
        print(f"📈 {stock_name}...", end=" ")
        
        stock_info = format_stock_data(row)
        analysis = analyze_stock_with_mistral(client, stock_info, stock_name)
        analyses.append(analysis)
        
        print(f"✓ {analysis['recommendation']} ({analysis['confidence']})")
    
    analysis_df = pd.DataFrame(analyses)
    analysis_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Analyses sauvegardées dans {output_file}")
    
    return analysis_df

def display_analysis_summary(analysis_df: pd.DataFrame):
    if analysis_df.empty:
        return
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    recommendations = analysis_df['recommendation'].value_counts()
    print("\n📈 Recommandations:")
    for rec, count in recommendations.items():
        print(f"   {rec}: {count}")
    
    print("\n📋 Détail:")
    for recommendation in ["ACHETER", "CONSERVER", "SURVEILLER", "VENDRE"]:
        stocks = analysis_df[analysis_df['recommendation'] == recommendation]
        if not stocks.empty:
            print(f"\n   {recommendation}:")
            for _, row in stocks.iterrows():
                print(f"      • {row['stock']} ({row['confidence']})")
    
    print("\n" + "="*60)

def analyze_single_stock(stock_name: str, csv_file: str = "stock_data.csv"):
    df = load_stock_data(csv_file)
    
    if df.empty:
        return
    
    stock_row = df[df['Nom'].str.upper() == stock_name.upper()]
    
    if stock_row.empty:
        print(f"❌ Stock '{stock_name}' non trouvé")
        print(f"   Disponibles: {', '.join(df['Nom'].tolist())}")
        return
    
    print(f"🔍 Analyse de {stock_name}...\n")
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    stock_info = format_stock_data(stock_row.iloc[0])
    analysis = analyze_stock_with_mistral(client, stock_info, stock_name)
    
    print("="*60)
    print(f"📊 {analysis['stock']}")
    print("="*60)
    print(f"\n🎯 Recommandation: {analysis['recommendation']}")
    print(f"📊 Confiance: {analysis['confidence']}")
    print(f"\n📝 Analyse:\n")
    print(analysis['analysis'])
    print("\n" + "="*60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        analyze_single_stock(sys.argv[1])
    else:
        analysis_df = analyze_all_stocks()
        if not analysis_df.empty:
            display_analysis_summary(analysis_df)
