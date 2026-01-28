import yfinance as yf
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List

SYMBOLS = {
    "Indices": {
        "SP 500": "^GSPC",
        "CAC40": "^FCHI",
        "GER30": "^GDAXI"
    },
    "Entreprises": {
        "APPLE": "AAPL",
        "AMAZON": "AMZN",
        "SANOFI": "SAN.PA",
        "THALES": "HO.PA",
        "LVMH": "MC.PA",
        "ENGIE": "ENGI.PA",
        "TOTALENERGIES": "TTE.PA",
        "INTERCONT HOTELS": "RCO.PA",
        "AIRBUS": "AIR.PA",
        "STELLANTIS": "STLA.PA",
        "TESLA": "TSLA"
    },
    "Matières premières": {
        "OIL": "CL=F",
        "GOLD": "GC=F",
        "GAS": "NG=F"
    }
}

def fetch_stock_data(symbol: str, name: str, category: str) -> Dict:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        data = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Catégorie": category,
            "Nom": name,
            "Symbole": symbol,
            "Prix actuel": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", "N/A"),
            "Prix d'ouverture": info.get("open") or info.get("regularMarketOpen", "N/A"),
            "Prix de clôture précédent": info.get("previousClose", "N/A"),
            "Plus haut (jour)": info.get("dayHigh") or info.get("regularMarketDayHigh", "N/A"),
            "Plus bas (jour)": info.get("dayLow") or info.get("regularMarketDayLow", "N/A"),
            "Plus haut (52 sem)": info.get("fiftyTwoWeekHigh", "N/A"),
            "Plus bas (52 sem)": info.get("fiftyTwoWeekLow", "N/A"),
            "Volume": info.get("volume") or info.get("regularMarketVolume", "N/A"),
            "Variation": info.get("regularMarketChange", "N/A"),
            "Variation %": info.get("regularMarketChangePercent", "N/A")
        }
        
        if data["Variation %"] != "N/A" and isinstance(data["Variation %"], (int, float)):
            data["Variation %"] = f"{data['Variation %']:.2f}%"
        
        return data
        
    except Exception as e:
        print(f"❌ Erreur {name} ({symbol}): {str(e)}")
        return {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Catégorie": category,
            "Nom": name,
            "Symbole": symbol,
            "Erreur": str(e)
        }

def fetch_all_data() -> List[Dict]:
    all_data = []
    
    for category, symbols in SYMBOLS.items():
        for name, symbol in symbols.items():
            data = fetch_stock_data(symbol, name, category)
            all_data.append(data)
            time.sleep(0.5)
    
    return all_data

def update_csv(filename: str = "stock_data.csv"):
    data = fetch_all_data()
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    return df

def run_continuous_update(interval_seconds: int = 60, filename: str = "stock_data.csv"):
    print(f"🚀 Mise à jour toutes les {interval_seconds}s")
    print(f"📁 Fichier: {filename}")
    print("⏹️  Ctrl+C pour arrêter\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Mise à jour #{iteration}")
            
            df = update_csv(filename)
            print(f"✅ {len(df)} stocks mis à jour\n")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Arrêt")
        print(f"✅ Dernières données sauvegardées dans {filename}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        run_continuous_update(interval)
    else:
        print("🔄 Mise à jour des données...")
        df = update_csv()
        print(f"✅ {len(df)} stocks mis à jour dans stock_data.csv")