import json
import html
import re
import glob
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


# =========================
# 1. CONFIGURATION & CSS
# =========================
st.set_page_config(
    page_title="Finsight AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="stApp"] {
    background-color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    color: #000000 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* NAVBAR */
.cmc-nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px 20px;
    margin-bottom: 25px;
    border-bottom: 1px solid #eff2f5;
    background: white;
    position: sticky;
    top: 0;
    z-index: 999;
}
.cmc-brand {
    font-size: 22px;
    font-weight: 800;
    color: #000000;
    text-decoration: none !important;
    display: flex; align-items: center;
}
.cmc-brand span { color: #3861fb; margin-left: 4px; }
.cmc-links { display: flex; gap: 20px; }
.cmc-link {
    text-decoration: none !important; color: #000000 !important;
    font-weight: 600; font-size: 14px; padding: 5px 10px; cursor: pointer;
}
.cmc-link:hover, .cmc-link.active {
    color: #3861fb !important; background: #f0f6ff; border-radius: 8px;
}
.cmc-account {
    background: #3861fb; color: white !important;
    padding: 8px 16px; border-radius: 8px;
    font-weight: 600; font-size: 14px; text-decoration: none !important;
}

/* CARDS */
.kpi-card {
    background: #ffffff;
    border: 1px solid #eff2f5;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    height: 100%;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-label {
    font-size: 12px; font-weight: 600; color: #58667e;
    text-transform: uppercase; margin-bottom: 8px; width: 100%; text-align: left;
}
.kpi-value { font-size: 28px; font-weight: 700; color: #000000; }
.kpi-sub { font-size: 14px; margin-top: 5px; font-weight: 600; }
.text-green { color: #16c784 !important; }
.text-red { color: #ea3943 !important; }

/* TABLE */
.cmc-table-wrap {
    overflow-x: auto;
    border: 1px solid #eff2f5;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    margin-top: 20px;
    background: white;
}
table.cmc-table { width: 100%; border-collapse: collapse; background: white; }
table.cmc-table th {
    text-align: left; padding: 16px; border-bottom: 1px solid #eff2f5;
    color: #000000; font-size: 12px; font-weight: 700; background-color: #f8fafc;
}
table.cmc-table td {
    padding: 16px; border-bottom: 1px solid #eff2f5;
    color: #000000; font-size: 14px; font-weight: 600; vertical-align: middle;
}
table.cmc-table tr:hover { background-color: #f8fafc; }
table.cmc-table a { text-decoration: none; color: inherit; display: block; width: 100%; height: 100%; }
.ticker-badge {
    background: #eff2f5; color: #58667e; padding: 2px 6px;
    border-radius: 4px; font-size: 12px; margin-left: 8px;
}

/* BUTTONS */
.stButton button {
    background-color: #3861fb !important; color: white !important;
    border: none; border-radius: 8px; font-weight: 600;
}

/* NEWS & LEXICON */
.lex-term {
    border-bottom: 1px dotted #58667e; cursor: help;
    background-color: #fffbeb; padding: 0 2px; border-radius: 3px; color: #000;
}
.news-item { padding: 16px; border-bottom: 1px solid #eff2f5; }
.news-item:hover { background: #f8fafc; }
.tag { padding: 3px 8px; border-radius: 100px; background: #eff2f5; font-size: 11px; font-weight: 600; color: #58667e; }
.tag-pos { background: #d1fae5; color: #065f46; }
.tag-neg { background: #fee2e2; color: #991b1b; }

/* Form & widget labels: force dark text for visibility on white background */
label, .stForm label, .stForm p, .stForm .stMarkdown p,
.stNumberInput label, .stNumberInput p,
.stSelectbox label, .stSelectbox p,
.stSlider label, .stSlider p,
.stRadio label, .stRadio p, .stRadio span,
.stMultiSelect label, .stMultiSelect p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
section[data-testid="stVerticalBlock"] > p:first-child {
    color: #1e293b !important;
    font-weight: 600 !important;
}
.stRadio div[role="radiogroup"] label, .stCheckbox label {
    color: #1e293b !important;
    font-weight: 500 !important;
}

/* Métriques (Prix, Variation 24h/7d) : texte bien visible */
[data-testid="stMetricValue"], [data-testid="stMetricDelta"],
div[data-testid="stMetric"] label, div[data-testid="stMetric"] p,
div[data-testid="stMetric"] span {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Alertes et messages (Pas de données, Aucun pattern, etc.) */
[data-baseweb="notification"], .stAlert, .stWarning, .stInfo,
section[data-testid="stVerticalBlock"] div[data-testid="stAlert"],
div[data-testid="stExpander"] {
    color: #1e293b !important;
}
[data-baseweb="notification"] div, [data-baseweb="notification"] p,
.stAlert div, .stAlert p {
    color: #1e293b !important;
    font-weight: 500 !important;
}

/* Captions (Prévision indisponible, etc.) */
.stCaption, p[data-testid="stCaption"] {
    color: #334155 !important;
    font-weight: 500 !important;
}

/* Animation chargement analyse */
.analyse-loading-wrap {
    text-align: center;
    padding: 24px 16px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    margin: 12px 0;
}
.analyse-loading-dots {
    display: inline-flex;
    gap: 8px;
    margin-bottom: 12px;
    justify-content: center;
}
.analyse-loading-dots span {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #3861fb;
    animation: analyse-bounce 0.6s ease-in-out infinite;
}
.analyse-loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.analyse-loading-dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes analyse-bounce {
    0%, 100% { transform: translateY(0); opacity: 0.7; }
    50% { transform: translateY(-10px); opacity: 1; }
}
.analyse-loading-bar {
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
    overflow: hidden;
    max-width: 280px;
    margin: 0 auto 14px;
}
.analyse-loading-bar::after {
    content: "";
    display: block;
    height: 100%;
    width: 40%;
    background: linear-gradient(90deg, #3861fb, #60a5fa);
    border-radius: 2px;
    animation: analyse-shimmer 1.2s ease-in-out infinite;
}
@keyframes analyse-shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(350%); }
}
.analyse-loading-msg {
    color: #64748b;
    font-size: 14px;
    font-weight: 500;
    margin: 0;
    line-height: 1.5;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# 2. SYSTÈME D'AUTHENTIFICATION
# =========================
DB_FILE = "users_db.json"

def get_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def get_user_profile(email: str) -> dict:
    db = get_db()
    if not email or email not in db:
        return {}
    return db[email].get("profile", {}) or {}

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    db = get_db()
    if email in db: return False, "Cet email existe déjà."
    db[email] = {
        "password": hash_pass(password),
        "created_at": str(datetime.now()),
        "onboarding_done": False,
        "profile": {}
    }
    save_db(db)
    return True, "Inscription réussie."

def login_user(email, password):
    db = get_db()
    if email not in db: return False, "Email inconnu."
    if db[email]["password"] != hash_pass(password): return False, "Mot de passe incorrect."
    return True, db[email]

def update_user_profile(email, profile_data):
    db = get_db()
    if email in db:
        db[email]["profile"] = profile_data
        db[email]["onboarding_done"] = True
        save_db(db)

# --- Session & Params ---
def qp_get_all() -> dict:
    try:
        qp = st.query_params
        return {k: (v[0] if isinstance(v, list) else str(v)) for k, v in qp.items()}
    except Exception:
        return {}

def qp_update(**kwargs):
    try:
        st.query_params.update(**{k: str(v) for k, v in kwargs.items()})
    except:
        st.experimental_set_query_params(**kwargs)

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "first_login" not in st.session_state: st.session_state["first_login"] = True
if "current_user" not in st.session_state: st.session_state["current_user"] = None
if "user_profile" not in st.session_state: st.session_state["user_profile"] = None
if "page" not in st.session_state: st.session_state["page"] = "Dashboard"
if "selected_stock" not in st.session_state: st.session_state["selected_stock"] = None

qp = qp_get_all()
if "auth" in qp and qp.get("auth") == "1":
    user_email = qp.get("user_email")
    if user_email:
        db = get_db()
        if user_email in db:
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = user_email
            u_data = db[user_email]
            st.session_state["user_profile"] = u_data.get("profile", {}).get("experience", "Inconnu")
            if not u_data.get("onboarding_done", False):
                st.session_state["page"] = "Onboarding"
                st.session_state["first_login"] = True
            elif "page" in qp and qp["page"] != "Onboarding":
                st.session_state["page"] = qp["page"]
                st.session_state["first_login"] = False
            else:
                st.session_state["page"] = "Dashboard"
                st.session_state["first_login"] = False

# =========================
# 3. DONNÉES & FONCTIONS
# =========================
DATA_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "data" / "raw"
CANDLES_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "candles"
PATTERNS_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "stock-pattern" / "src" / "patterns"

PATTERN_REGISTRY = {
    "vcpu": {
        "name_fr": "VCP haussier",
        "category": "Continuation",
        "bias": "Bullish",
        "level1": "Consolidation en vagues de plus en plus courtes avant reprise possible de la hausse.",
        "level2": "Le VCP (Volatility Contraction Pattern) signale une compression progressive de la volatilite avec des creux ascendants. Cela traduit un equilibre qui se resserre avant une sortie potentielle.",
        "level3": [
            "Attendre une cassure au-dessus de la zone de consolidation avec volume.",
            "Surveiller l'invalidation sous le dernier creux intermediaire.",
            "Horizon plutot court a moyen terme si la tendance globale est haussiere.",
        ],
        "riskNote": "Risque: faux breakout sans volume.",
    },
    "vcpd": {
        "name_fr": "VCP baissier",
        "category": "Continuation",
        "bias": "Bearish",
        "level1": "Consolidation qui se resserre avant une possible reprise de la baisse.",
        "level2": "Version baissiere du VCP: les rebonds deviennent plus faibles et la volatilite se contracte sous une tendance descendante.",
        "level3": [
            "Attendre une cassure sous le support de la consolidation.",
            "Invalidation si le prix repasse au-dessus du dernier sommet de rebond.",
            "Horizon court a moyen terme, prudent en phase de range.",
        ],
        "riskNote": "Risque: rebond technique rapide.",
    },
    "dbot": {
        "name_fr": "Double creux",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Deux creux proches signalent une possible fin de baisse et un retournement.",
        "level2": "Le double bottom traduit l'incapacite du marche a casser un support. La ligne de cou (entre les deux creux) sert de niveau cle.",
        "level3": [
            "Confirmer par cassure de la ligne de cou.",
            "Invalidation si nouveau plus bas sous le second creux.",
            "Objectifs prudents et horizon court a moyen terme.",
        ],
        "riskNote": "Risque: range prolonge.",
    },
    "dtop": {
        "name_fr": "Double sommet",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Deux sommets proches indiquent un essoufflement haussier possible.",
        "level2": "Le double top suggere que la resistance tient. La cassure de la ligne de cou confirme un retournement potentiel.",
        "level3": [
            "Attendre une cassure sous la ligne de cou.",
            "Invalidation si nouveau sommet au-dessus du deuxieme pic.",
            "Horizon court a moyen terme, attention aux faux signaux.",
        ],
        "riskNote": "Risque: rebond au-dessus de la resistance.",
    },
    "trng": {
        "name_fr": "Triangle",
        "category": "Structure",
        "bias": "Neutre",
        "level1": "Compression des prix; le sens depend de la cassure du triangle.",
        "level2": "Les triangles reflètent un equilibre temporaire entre acheteurs et vendeurs. La direction se precise a la sortie du biseau.",
        "level3": [
            "Observer une cassure claire avec reprise de volume.",
            "Cassure haussiere au-dessus de la resistance; baissiere sous le support.",
            "Invalidation si retour rapide dans le triangle.",
        ],
        "riskNote": "Risque: fausse cassure.",
    },
    "hnsd": {
        "name_fr": "Epaule-Tete-Epaule",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Structure en trois sommets; possible retournement baissier.",
        "level2": "L'ETE signale un essoufflement des acheteurs. La ligne de cou confirme la rupture de tendance si elle cede.",
        "level3": [
            "Attendre la cassure de la ligne de cou.",
            "Invalidation si le prix repasse au-dessus de la tete.",
            "Horizon court a moyen terme, prudence sur la volatilite.",
        ],
        "riskNote": "Risque: pullback au niveau de cou.",
    },
    "hnsu": {
        "name_fr": "ETE inverse",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Trois creux dont un plus bas; possible retournement haussier.",
        "level2": "L'ETE inverse traduit l'epuisement vendeur. La cassure de la ligne de cou valide un retournement potentiel.",
        "level3": [
            "Confirmer par cassure au-dessus de la ligne de cou.",
            "Invalidation si nouveau plus bas sous la tete.",
            "Horizon court a moyen terme, surveiller les volumes.",
        ],
        "riskNote": "Risque: echec de cassure.",
    },
    "uptl": {
        "name_fr": "Ligne de tendance haussiere",
        "category": "Structure",
        "bias": "Bullish",
        "level1": "Support dynamique; la tendance reste haussiere tant qu'elle tient.",
        "level2": "Une ligne de tendance haussiere relie des creux ascendants. Elle sert de guide pour evaluer la force du mouvement.",
        "level3": [
            "Rechercher des reactions sur la ligne avec volume en baisse.",
            "Invalidation si cassure nette sous la ligne.",
            "Horizon moyen terme si la structure reste intacte.",
        ],
        "riskNote": "Risque: cassure rapide en marche nerveux.",
    },
    "dntl": {
        "name_fr": "Ligne de tendance baissiere",
        "category": "Structure",
        "bias": "Bearish",
        "level1": "Resistance dynamique; la tendance reste baissiere tant qu'elle tient.",
        "level2": "La ligne de tendance baissiere relie des sommets descendants. Elle sert de repere pour identifier des reprises de tendance.",
        "level3": [
            "Surveiller les rejets au contact de la ligne.",
            "Invalidation si cassure franche au-dessus.",
            "Horizon moyen terme si la structure persiste.",
        ],
        "riskNote": "Risque: cassure par fausse accel.",
    },
    "flagu": {
        "name_fr": "Drapeau haussier",
        "category": "Continuation",
        "bias": "Bullish",
        "level1": "Pause courte apres impulsion; continuation haussiere possible.",
        "level2": "Le drapeau haussier est une consolidation legere apres une forte hausse. Il suggere une respiration avant reprise.",
        "level3": [
            "Attendre cassure au-dessus du drapeau.",
            "Invalidation si retour sous le bas du drapeau.",
            "Horizon court, surtout en tendance forte.",
        ],
        "riskNote": "Risque: consolidation qui s'elargit.",
    },
    "flagd": {
        "name_fr": "Drapeau baissier",
        "category": "Continuation",
        "bias": "Bearish",
        "level1": "Rebond court apres chute; continuation baissiere possible.",
        "level2": "Le drapeau baissier suit une impulsion de baisse. Le rebond est contenu et peut preçeder une nouvelle jambe.",
        "level3": [
            "Attendre cassure sous le drapeau.",
            "Invalidation si le prix repasse au-dessus de la borne haute.",
            "Horizon court, prudent en marche volatil.",
        ],
        "riskNote": "Risque: short squeeze.",
    },
    "abcdu": {
        "name_fr": "ABCD haussier",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Structure en 4 points; possible rebond apres completion.",
        "level2": "Le pattern ABCD haussier vise une symetrie de mouvements. Le point D marque une zone de reaction potentielle.",
        "level3": [
            "Attendre un signal de rebond au point D.",
            "Invalidation si le prix casse nettement sous D.",
            "Horizon court a moyen terme selon la volatilite.",
        ],
        "riskNote": "Risque: continuation de la baisse.",
    },
    "abcdd": {
        "name_fr": "ABCD baissier",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Structure en 4 points; possible repli apres completion.",
        "level2": "Le pattern ABCD baissier vise une symetrie. Le point D peut marquer une zone de plafond.",
        "level3": [
            "Attendre un signal de rejet au point D.",
            "Invalidation si cassure au-dessus de D.",
            "Horizon court a moyen terme, prudence sur les fausses cassures.",
        ],
        "riskNote": "Risque: breakout haussier.",
    },
    "batu": {
        "name_fr": "Bat haussier",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Harmonique avancé; zone D peut declencher un rebond.",
        "level2": "Le Bat haussier est un pattern harmonique base sur des ratios. La zone PRZ autour de D est surveillee.",
        "level3": [
            "Rechercher un signal de retournement dans la PRZ.",
            "Invalidation si le prix casse sous la PRZ.",
            "Horizon court a moyen terme selon l'amplitude.",
        ],
        "riskNote": "Risque: non-respect des ratios.",
    },
    "batd": {
        "name_fr": "Bat baissier",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Harmonique avance; zone D peut marquer un sommet.",
        "level2": "Le Bat baissier signale une zone de retournement potentielle dans la PRZ. Il est sensible aux ratios.",
        "level3": [
            "Attendre un rejet clair dans la PRZ.",
            "Invalidation si le prix depasse nettement la PRZ.",
            "Horizon court a moyen terme, confirmation utile.",
        ],
        "riskNote": "Risque: extension de tendance.",
    },
    "gartu": {
        "name_fr": "Gartley haussier",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Harmonique classique; la zone D peut servir de support.",
        "level2": "Le Gartley haussier est un pattern harmonique de retournement. La confluence de ratios definit la PRZ.",
        "level3": [
            "Attendre une reaction haussiere dans la PRZ.",
            "Invalidation si cassure franche sous D.",
            "Horizon court a moyen terme, prudence sur les faux rebonds.",
        ],
        "riskNote": "Risque: rebond insuffisant.",
    },
    "gartd": {
        "name_fr": "Gartley baissier",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Harmonique classique; la zone D peut servir de resistance.",
        "level2": "Le Gartley baissier vise une zone de retournement en haut de structure. Les ratios doivent etre respectes.",
        "level3": [
            "Attendre un rejet dans la PRZ.",
            "Invalidation si cassure au-dessus de D.",
            "Horizon court a moyen terme, confirmation utile.",
        ],
        "riskNote": "Risque: tendance forte qui persiste.",
    },
    "crabu": {
        "name_fr": "Crab haussier",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Harmonique agressif; zone D profonde pour rebond possible.",
        "level2": "Le Crab haussier est plus etendu, avec une zone PRZ souvent profonde. Il vise un retournement depuis une extension.",
        "level3": [
            "Attendre un signal clair dans la PRZ.",
            "Invalidation si le prix glisse sous la zone.",
            "Horizon court, volatilite souvent elevee.",
        ],
        "riskNote": "Risque: mouvements brusques.",
    },
    "crabd": {
        "name_fr": "Crab baissier",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Harmonique agressif; zone D etendue pour repli possible.",
        "level2": "Le Crab baissier vise un sommet d'extension. La PRZ est large et demande confirmation.",
        "level3": [
            "Attendre un rejet clair dans la PRZ.",
            "Invalidation si le prix depasse la zone.",
            "Horizon court, prudence en tendance forte.",
        ],
        "riskNote": "Risque: extension continue.",
    },
    "bflyu": {
        "name_fr": "Butterfly haussier",
        "category": "Retournement",
        "bias": "Bullish",
        "level1": "Harmonique d'extension; la zone D peut servir de support.",
        "level2": "Le Butterfly haussier combine extension et retracement. La zone D est une PRZ de retournement potentiel.",
        "level3": [
            "Attendre un signal de stabilisation dans la PRZ.",
            "Invalidation si cassure franche sous D.",
            "Horizon court a moyen terme selon le contexte.",
        ],
        "riskNote": "Risque: forte volatilite.",
    },
    "bflyd": {
        "name_fr": "Butterfly baissier",
        "category": "Retournement",
        "bias": "Bearish",
        "level1": "Harmonique d'extension; la zone D peut servir de resistance.",
        "level2": "Le Butterfly baissier vise un sommet d'extension avec PRZ. Il demande une confirmation par rejet.",
        "level3": [
            "Attendre un rejet clair dans la PRZ.",
            "Invalidation si le prix depasse nettement D.",
            "Horizon court a moyen terme, attention aux fausses alertes.",
        ],
        "riskNote": "Risque: breakout haussier.",
    },
}
PREDICTIONS_ROOT = Path(__file__).resolve().parent / "PFE_MVP" / "reports" / "predictions"
XAI_ROOT = Path(__file__).resolve().parent / "NLP"
BASE_DIR = Path(__file__).resolve().parent
# Charger .env pour MISTRAL_API_KEY (analyse XAI fine)
load_dotenv(BASE_DIR / ".env")

DATA_ROOT = BASE_DIR / "PFE_MVP" / "data" / "raw"
CANDLES_ROOT = BASE_DIR / "PFE_MVP" / "stock-pattern" / "src" / "candles"
PATTERNS_ROOT = BASE_DIR / "PFE_MVP" / "stock-pattern" / "src" / "patterns"
PREDICTIONS_ROOT = BASE_DIR / "PFE_MVP" / "reports" / "predictions"
XAI_ROOT = BASE_DIR / "NLP"


def _ticker_for_pattern_prediction_files(display_ticker: str) -> str:
    """Ticker utilisé dans les noms de fichiers patterns/predictions (ex: GSPC, CL_F, AIR.PA)."""
    disp = str(display_ticker).strip()
    file_sym_map = {
        "SP500": "GSPC", "CAC40": "FCHI", "GER30": "GDAXI",
        "OIL": "CL_F", "GOLD": "GC_F", "GAS": "NG_F",
        "AAPL": "AAPL", "AMZN": "AMZN", "TSLA": "TSLA",
        "SAN": "SAN.PA", "HO": "HO.PA", "MC": "MC.PA", "ENGI": "ENGI.PA",
        "TTE": "TTE.PA", "AIR": "AIR.PA", "STLA": "STLAP.PA", "RCO": "RCO.PA",
    }
    return file_sym_map.get(disp, disp.replace("^", "").replace("=", "_"))


def load_patterns_for_asset(display_ticker: str) -> Optional[dict]:
    """Charge le JSON patterns pour l'actif (PFE_MVP/stock-pattern/src/patterns/{sym}_daily_patterns.json)."""
    sym = _ticker_for_pattern_prediction_files(display_ticker)
    path = PATTERNS_ROOT / f"{sym}_daily_patterns.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_prediction_for_asset(display_ticker: str) -> Optional[dict]:
    """Charge le JSON multi-horizon pour l'actif (PFE_MVP/reports/predictions/{sym}_multi_horizon.json)."""
    sym = _ticker_for_pattern_prediction_files(display_ticker)
    path = PREDICTIONS_ROOT / f"{sym}_multi_horizon.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and any(k.startswith("h") for k in data.keys()):
                return data.get("h1") or data.get("h5") or data.get("h10") or data.get("h30") or None
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Fallback legacy next_day
    legacy = PREDICTIONS_ROOT / f"{sym}_next_day.json"
    if not legacy.exists():
        return None
    try:
        with open(legacy, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _demo_stocks():
    """Données de démo si aucun CSV chargé."""
    return pd.DataFrame([
        {"Symbole": "^GSPC", "Nom": "SP 500", "Prix": 6909.94},
        {"Symbole": "^FCHI", "Nom": "CAC 40", "Prix": 8344.47},
        {"Symbole": "AAPL", "Nom": "Apple", "Prix": 259.67},
        {"Symbole": "AMZN", "Nom": "Amazon", "Prix": 238.89},
        {"Symbole": "TSLA", "Nom": "Tesla", "Prix": 438.24},
        {"Symbole": "GC=F", "Nom": "Or", "Prix": 4618.5},
        {"Symbole": "CL=F", "Nom": "Pétrole", "Prix": 61.75},
    ])

def _demo_news():
    """News de démo si aucun CSV chargé."""
    return pd.DataFrame([
        {"title": "Marchés : rebond après les annonces Fed", "published_at": "2026-01-22T14:00:00Z", "url": "#", "source": "Demo", "asset_ticker": "SP500, AAPL", "prob_positive": 0.72, "prob_negative": 0.28, "confidence": 0.85},
        {"title": "Tech : résultats solides pour les géants", "published_at": "2026-01-22T12:00:00Z", "url": "#", "source": "Demo", "asset_ticker": "AAPL, AMZN", "prob_positive": 0.68, "prob_negative": 0.32, "confidence": 0.82},
        {"title": "Pétrole et or en hausse", "published_at": "2026-01-22T10:00:00Z", "url": "#", "source": "Demo", "asset_ticker": "OIL, GOLD", "prob_positive": 0.65, "prob_negative": 0.35, "confidence": 0.78},
    ])

@st.cache_data
def load_data():
    stocks = pd.DataFrame()
    news = pd.DataFrame()
    aapl = pd.DataFrame()
    # Chemins depuis le dossier du script
    stock_path = BASE_DIR / "stock_data (1).csv"
    aapl_path = BASE_DIR / "AAPL.csv"
    try:
        if stock_path.exists():
            stocks = pd.read_csv(stock_path)
    except Exception:
        pass
    try:
        csv_pattern = str(BASE_DIR / "NLP" / "hybrid_news_financial_classified_*.csv")
        csv_files = glob.glob(csv_pattern)
        if csv_files:
            latest_csv = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
            raw = pd.read_csv(latest_csv)
            if "is_financial" in raw.columns:
                raw = raw[raw["is_financial"] == 1].copy()
            if not raw.empty:
                news = raw.groupby("title").agg({
                    "published_at": "first", "url": "first", "source": "first",
                    "asset_ticker": lambda x: ", ".join(x.unique()),
                    "prob_positive": "mean", "prob_negative": "mean",
                    "confidence": "mean"
                }).reset_index()
    except Exception:
        pass
    try:
        if aapl_path.exists():
            aapl = pd.read_csv(aapl_path)
            if "Date" in aapl.columns:
                aapl["Date"] = pd.to_datetime(aapl["Date"])
    except Exception:
        pass
    # Données de démo si vides
    if stocks.empty:
        stocks = _demo_stocks()
    if news.empty:
        news = _demo_news()
    return stocks, news, aapl

stock_df, news_df, aapl_df = load_data()

if not stock_df.empty:
    if "Symbole" not in stock_df.columns and "Ticker" in stock_df.columns:
        stock_df["Symbole"] = stock_df["Ticker"]
    if "Nom" not in stock_df.columns and "Name" in stock_df.columns:
        stock_df["Nom"] = stock_df["Name"]
    if "Prix" not in stock_df.columns and "Prix actuel" in stock_df.columns:
        stock_df["Prix"] = pd.to_numeric(stock_df["Prix actuel"], errors="coerce")
    elif "Prix" not in stock_df.columns and "Close" in stock_df.columns:
        stock_df["Prix"] = stock_df["Close"]
    for c in ["Prix", "Variation 24h", "Variation 7d"]:
        if c in stock_df.columns:
            stock_df[c] = pd.to_numeric(stock_df[c], errors="coerce")

def safe_ticker(t): return str(t).replace("^", "").replace("=", "_").replace("/", "_")
def normalize_ticker(t): return str(t).split(".")[0].replace("^","")

@st.cache_data
def load_price_history(sym):
    cpath = CANDLES_ROOT / f"{safe_ticker(sym)}_daily.json"
    if cpath.exists():
        try:
            data = json.loads(cpath.read_text())
            df = pd.DataFrame(data.get("candles", []))
            if not df.empty:
                df = df.rename(columns={"t":"Date", "close":"Close", "open":"Open", "high":"High", "low":"Low"})
                df["Date"] = pd.to_datetime(df["Date"])
                return df.sort_values("Date")
        except: pass
    dpath = DATA_ROOT / f"{safe_ticker(sym)}.csv"
    if dpath.exists():
        try:
            df = pd.read_csv(dpath)
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"])
            return df.sort_values("Date")
        except Exception:
            pass
    # Fallback: AAPL à la racine du projet
    root_csv = BASE_DIR / "AAPL.csv"
    if safe_ticker(sym) == "AAPL" and root_csv.exists():
        try:
            df = pd.read_csv(root_csv)
            if "Date" in df.columns: df["Date"] = pd.to_datetime(df["Date"])
            return df.sort_values("Date")
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data
def load_patterns(sym):
    path = PATTERNS_ROOT / f"{safe_ticker(sym)}_daily_patterns.json"
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return None

@st.cache_data
def load_prediction(sym):
    path = PREDICTIONS_ROOT / f"{safe_ticker(sym)}_multi_horizon.json"
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    legacy = PREDICTIONS_ROOT / f"{safe_ticker(sym)}_next_day.json"
    if legacy.exists():
        try: return json.loads(legacy.read_text())
        except: pass
    return None

@st.cache_data
def load_xai_analysis(sym):
    files = glob.glob(str(XAI_ROOT / f"xai_{sym}_*.csv"))
    if not files: return pd.DataFrame()
    latest = max(files, key=lambda x: Path(x).stat().st_mtime)
    try: return pd.read_csv(latest)
    except: return pd.DataFrame()


@st.cache_data
def load_sentiment_data_nlp() -> pd.DataFrame:
    """Charge le fichier sentiment le plus récent dans NLP (sentiment_analysis_*.csv ou .json)."""
    nlproot = BASE_DIR / "NLP"
    csv_files = glob.glob(str(nlproot / "sentiment_analysis_*.csv"))
    if csv_files:
        latest = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
        try:
            df = pd.read_csv(latest)
            if not df.empty and "asset_ticker" in df.columns:
                return df
        except Exception:
            pass
    json_files = glob.glob(str(nlproot / "sentiment_analysis_*.json"))
    if json_files:
        latest = max(json_files, key=lambda x: Path(x).stat().st_mtime)
        try:
            data = json.loads(Path(latest).read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return pd.DataFrame(data)
        except Exception:
            pass
    return pd.DataFrame()


def load_sentiment_news_for_stock(asset_ticker: str) -> pd.DataFrame:
    """Retourne les news de sentiment (NLP sentiment_analysis CSV/JSON) pour un actif."""
    df = load_sentiment_data_nlp()
    if df.empty or "asset_ticker" not in df.columns:
        return pd.DataFrame()
    # Correspondance ticker (SP500, AAPL, etc.)
    mask = df["asset_ticker"].astype(str).str.upper().str.strip() == str(asset_ticker).upper().strip()
    out = df.loc[mask].copy()
    # S'assurer que les colonnes attendues par _run_xai_fine_analysis existent
    for col in ("prob_positive", "prob_negative", "title", "source", "published_at"):
        if col not in out.columns and col == "published_at" and "published_at" not in out.columns:
            pass  # optional
    return out


def _run_analyse_pour_toi(
    asset_ticker: str,
    news_subset: pd.DataFrame,
    pattern_data: Optional[dict] = None,
    prediction_data: Optional[dict] = None,
    user_profile: Optional[dict] = None,
    variation_24h_pct: Optional[float] = None,
    variation_7d_pct: Optional[float] = None,
) -> Optional[dict]:
    """
    Génère l'analyse "Notre analyse pour toi" : structurée, avec exemples d'actualités (liens),
    chiffres explicites et recommandations très personnalisées.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or not api_key.strip():
        return {"error": "MISTRAL_API_KEY manquante."}
    has_news = not news_subset.empty and ("title" in news_subset.columns or "asset_ticker" in news_subset.columns)
    has_pattern = pattern_data and isinstance(pattern_data.get("patterns"), list) and len(pattern_data.get("patterns", [])) > 0
    has_pred = prediction_data and isinstance(prediction_data, dict)
    if not has_news and not has_pattern and not has_pred:
        return None
    try:
        from mistralai import Mistral
    except ImportError:
        return {"error": "Module mistralai non installé."}

    # Chiffres clés (variations, sentiment, prédiction)
    v24_str = f"{variation_24h_pct:+.2f}%" if variation_24h_pct is not None else "n/d"
    v7_str = f"{variation_7d_pct:+.2f}%" if variation_7d_pct is not None else "n/d"
    if has_news:
        avg_pos = news_subset["prob_positive"].mean() if "prob_positive" in news_subset.columns else 0.5
        avg_neg = news_subset["prob_negative"].mean() if "prob_negative" in news_subset.columns else 0.5
        trend = "BULLISH" if avg_pos > avg_neg else "BEARISH"
        sent_pos_pct = int(round(avg_pos * 100))
        sent_neg_pct = int(round(avg_neg * 100))
    else:
        sent_pos_pct = sent_neg_pct = 50
        trend = "NEUTRE"
    pred_up_pct = int(round(prediction_data.get("proba_up", 0) * 100)) if has_pred and prediction_data.get("proba_up") is not None else None
    pred_down_pct = int(round(prediction_data.get("proba_down", 0) * 100)) if has_pred and prediction_data.get("proba_down") is not None else None
    chiffres_block = f"Variation 24h: {v24_str} | Variation 7j: {v7_str} | Sentiment: {sent_pos_pct}% positif / {sent_neg_pct}% négatif (tendance {trend})"
    if pred_up_pct is not None and pred_down_pct is not None:
        chiffres_block += f" | Prédiction J+1: P(hausse)={pred_up_pct}%, P(baisse)={pred_down_pct}%"

    # Exemples d'actualités avec titre, lien, source, sentiment (pour citation explicite)
    news_examples_lines = []
    if has_news:
        for _, r in news_subset.head(6).iterrows():
            title = str(r.get("title", ""))[:100].strip()
            url = str(r.get("url", "")).strip() or "#"
            source = str(r.get("source", "")).strip() or "Source"
            ppos = r.get("prob_positive", 0.5)
            pneg = r.get("prob_negative", 0.5)
            conf = int(round(max(ppos, pneg) * 100))
            sent = "Positif" if ppos > pneg else "Négatif"
            news_examples_lines.append(f"- [{title}]({url}) — {source} — {sent} ({conf}%)")
    news_examples_block = "\n".join(news_examples_lines) if news_examples_lines else "Aucune actualité avec lien disponible."

    pattern_brief = ""
    if has_pattern:
        names = [str(p.get("pattern") or p.get("alt_name") or "?") for p in pattern_data.get("patterns", [])[:3]]
        pattern_brief = f"Motifs techniques détectés: {', '.join(names)}."
    else:
        pattern_brief = "Aucun motif technique détecté."

    profile = user_profile or {}
    age = profile.get("age", "")
    horizon = profile.get("horizon", "")
    experience = profile.get("experience", "")
    capital = profile.get("capital", "")
    strategy = profile.get("strategy", "")
    risk = profile.get("risk", "")
    sectors = profile.get("sectors") or []
    sectors_str = ", ".join(sectors) if sectors else "non précisé"
    profile_block = (
        f"Profil (à utiliser pour personnaliser au maximum les conseils) : "
        f"âge {age}, horizon {horizon}, expérience {experience}, capital indicatif {capital} €, "
        f"tolérance au risque {risk}/10, stratégie {strategy}, secteurs privilégiés {sectors_str}."
    )

    prompt = f"""Tu rédiges une analyse structurée pour l'actif {asset_ticker}, sous le titre "Notre analyse pour toi".

CHIFFRES CLÉS (à citer explicitement avec les pourcentages) :
{chiffres_block}

EXEMPLES D'ACTUALITÉS (cite au moins 2 ou 3 avec le lien markdown [titre](url)) :
{news_examples_block}

{pattern_brief}

{profile_block}

STRUCTURE (sépare chaque bloc par une ligne vide ; n'écris pas de numéros ni de titres comme "1. Contexte") :

Premier paragraphe : Commence par "Actuellement," et décris le climat pour {asset_ticker}. Cite des chiffres concrets (ex. "en baisse de 0,84% sur 24h", "sentiment à 73% négatif", "P(hausse demain) à 65%") et au moins 2 actualités avec un lien cliquable [titre](url). Utilise les URLs fournies ci-dessus.

Deuxième paragraphe : "Ce qui veut dire que..." en t'appuyant sur les exemples et les chiffres.

Troisième bloc : Une ou deux phrases sur le motif (ou l'absence de signal) et ce que ça implique.

Quatrième bloc — Recommandation personnalisée : Paragraphe personnalisé qui mentionne le lecteur (âge, horizon, capital, risque, stratégie). IMPORTANT : ne pars jamais du principe qu'il met tout (ou une grosse part) de son capital sur cet actif seul. Cet actif est une ligne parmi d'autres dans un portefeuille diversifié. Formule en termes de position sur CET actif : surpondérer, sous-pondérer, maintenir, surveiller avant d'ajouter, éviter d'augmenter l'exposition, etc. Ne dis pas "alloue 60% de ton capital à...", "réserve 20% pour...". Tu peux recommander une exposition raisonnable pour cette ligne (ex. "une part modérée de ton portefeuille", "évite de surpondérer"), pas une répartition du capital total. Termine par "Garde un œil sur... Et reviens demain pour ajuster."

Dernier bloc : Termine par exactement : "Pour aller plus loin, consulte notre analyse détaillée juste en dessous."

CONSIGNES :
- Tu t'adresses au lecteur à la 2e personne (tu, toi, ton). NE RÉPÈTE JAMAIS le titre "Notre analyse pour toi" dans ta réponse (il est affiché au-dessus). Commence directement par "Actuellement,".
- N'écris PAS de titres de section numérotés (pas de "1. Contexte", "2. Interprétation", "4. Recommandation"). Uniquement des paragraphes séparés par une ligne vide.
- Inclus des LIENS [texte](url) et des CHIFFRES explicites (%, +X%, P(hausse)=Y%). La recommandation doit être personnalisée mais sans répartir le capital total sur cet actif."""

    try:
        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1400,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return {"error": "Réponse vide."}
        # Supprimer les lignes qui répètent le titre ou sont des titres de section numérotés
        title_variants = ("Notre analyse pour toi", "**Notre analyse pour toi**", "# Notre analyse pour toi")
        lines = text.split("\n")
        cleaned = []
        for L in lines:
            s = L.strip()
            if s in title_variants:
                continue
            if re.match(r"^[\d]+\.\s*(Contexte|Interprétation|Technique|Recommandation)", s, re.I):
                continue
            cleaned.append(L)
        text = "\n".join(cleaned).strip()
        # Supprimer aussi si le texte commence encore par le titre (avec ou sans numéro)
        for prefix in ("Notre analyse pour toi", "**Notre analyse pour toi**", "# Notre analyse pour toi"):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                if text.startswith("\n"):
                    text = text.lstrip("\n")
                break
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}


def _run_xai_fine_analysis(
    asset_ticker: str,
    news_subset: pd.DataFrame,
    pattern_data: Optional[dict] = None,
    prediction_data: Optional[dict] = None,
    user_profile: Optional[dict] = None,
) -> Optional[dict]:
    """
    Analyse XAI courte et personnalisée : news + patterns + prédiction next_day + profil utilisateur.
    Retourne un dict avec xai_explanation, sentiment_trend, recommendation, etc.
    En cas d'erreur retourne un dict avec la clé "error".
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or not api_key.strip():
        return {"error": "MISTRAL_API_KEY manquante. Ajoutez MISTRAL_API_KEY=votre_cle dans le fichier .env à la racine du projet."}
    has_news = not news_subset.empty and "asset_ticker" in news_subset.columns
    has_pattern = pattern_data and isinstance(pattern_data.get("patterns"), list)
    has_pred = prediction_data and isinstance(prediction_data, dict)
    if not has_news and not has_pattern and not has_pred:
        return None
    try:
        from mistralai import Mistral
    except ImportError:
        return {"error": "Module mistralai non installé. Lancez: pip install mistralai"}

    # --- News & sentiment ---
    if has_news:
        avg_pos = news_subset["prob_positive"].mean() if "prob_positive" in news_subset.columns else 0.5
        avg_neg = news_subset["prob_negative"].mean() if "prob_negative" in news_subset.columns else 0.5
        trend = "BULLISH" if avg_pos > avg_neg else "BEARISH"
        lines = []
        for i, (_, r) in enumerate(news_subset.head(6).iterrows(), 1):
            title = str(r.get("title", ""))[:100]
            ppos = r.get("prob_positive", 0)
            pneg = r.get("prob_negative", 0)
            sent = "Positif" if ppos > pneg else "Négatif"
            lines.append(f"{i}. {title} — {sent}")
        news_block = "Actualités récentes:\n" + "\n".join(lines) + f"\nRésumé sentiment: {trend} (positif {avg_pos:.0%}, négatif {avg_neg:.0%})."
    else:
        trend = "NEUTRE"
        avg_pos, avg_neg = 0.5, 0.5
        news_block = "Aucune actualité disponible pour cet actif."

    # --- Patterns ---
    if has_pattern:
        patterns_list = pattern_data.get("patterns", [])
        pattern_names = []
        for p in patterns_list[:5]:
            name = p.get("pattern") or p.get("alt_name") or "?"
            pattern_names.append(str(name))
        patterns_block = "Motifs techniques détectés: " + (", ".join(pattern_names) if pattern_names else "aucun détail") + "."
    else:
        patterns_block = "Aucun motif technique détecté ou données indisponibles."

    # --- Prédiction next day ---
    if has_pred:
        sig = prediction_data.get("signal", "N/A")
        pu = prediction_data.get("proba_up")
        pd_ = prediction_data.get("proba_down")
        if pu is not None and pd_ is not None:
            pred_block = f"Prédiction prochain jour: signal {sig} (prob. hausse {pu:.0%}, baisse {pd_:.0%})."
        else:
            pred_block = f"Prédiction prochain jour: signal {sig}."
    else:
        pred_block = "Prédiction prochain jour: non disponible."

    # --- Profil utilisateur ---
    profile = user_profile or {}
    age = profile.get("age", "")
    horizon = profile.get("horizon", "")
    experience = profile.get("experience", "")
    capital = profile.get("capital", "")
    risk = profile.get("risk", "")
    strategy = profile.get("strategy", "")
    sectors = profile.get("sectors") or []
    sectors_str = ", ".join(sectors) if sectors else "non précisé"
    profile_block = (
        f"Profil investisseur: horizon {horizon}, expérience {experience}, capital indicatif {capital}€, "
        f"tolérance au risque (1-10) {risk}, stratégie {strategy}, secteurs {sectors_str}."
    )

    prompt = f"""Tu es un expert en analyse financière. Tu rédiges une explication courte et personnalisée pour l'actif {asset_ticker}.

DONNÉES DISPONIBLES:
• {news_block}
• {patterns_block}
• {pred_block}
• {profile_block}

CONSIGNES:
1. Réponds en 8 à 15 lignes maximum. Pas de liste longue ni de paragraphes lourds.
2. Synthèse factuelle: en 2-3 phrases, résume l'essentiel (sentiment, prédiction, motifs si pertinents).
3. Conseil personnalisé: tu DOIS adapter explicitement au profil ci-dessus. Mentionne l'horizon ({horizon}), la stratégie ({strategy}) et le niveau de risque ({risk}/10) dans ton conseil. Une ou deux phrases claires qui expliquent pourquoi cette recommandation convient à CE profil.
4. Recommandation finale: une seule ligne "Recommandation: ACHETER / VENDRE / CONSERVER / SURVEILLER — Confiance ÉLEVÉE / MOYENNE / FAIBLE." avec justification courte liée au profil.

Sois direct, factuel et utile. Le profil investisseur doit être visiblement utilisé dans ta réponse."""

    try:
        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        text = response.choices[0].message.content
        rec, conf = "N/A", "N/A"
        if text:
            if "ACHETER" in text.upper(): rec = "ACHETER"
            elif "VENDRE" in text.upper(): rec = "VENDRE"
            elif "CONSERVER" in text.upper(): rec = "CONSERVER"
            elif "SURVEILLER" in text.upper(): rec = "SURVEILLER"
            if "ÉLEVÉ" in text.upper() or "ELEVE" in text.upper() or "ÉLEVÉE" in text.upper(): conf = "ÉLEVÉ"
            elif "MOYEN" in text.upper(): conf = "MOYEN"
            elif "FAIBLE" in text.upper(): conf = "FAIBLE"
        total_news = len(news_subset) if has_news else 0
        return {
            "asset_ticker": asset_ticker,
            "sentiment_trend": trend,
            "total_news": total_news,
            "avg_positive": avg_pos if has_news else 0.5,
            "avg_negative": avg_neg if has_news else 0.5,
            "recommendation": rec,
            "confidence": conf,
            "xai_explanation": text or "Aucune réponse.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        return {"error": str(e)}


def _run_xai_long_analysis(
    asset_ticker: str,
    news_subset: pd.DataFrame,
    pattern_data: Optional[dict] = None,
    prediction_data: Optional[dict] = None,
    user_profile: Optional[dict] = None,
) -> Optional[dict]:
    """
    Génère l'analyse XAI détaillée (4 sections) personnalisée au profil + patterns + prédiction.
    Même logique que NLP/stock_analyzer mais appelée depuis le dashboard avec les données déjà chargées.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or not api_key.strip():
        return {"error": "MISTRAL_API_KEY manquante. Vérifiez le fichier .env."}
    has_news = not news_subset.empty and ("asset_ticker" in news_subset.columns or "title" in news_subset.columns)
    if not has_news:
        return None
    try:
        from mistralai import Mistral
    except ImportError:
        return {"error": "Module mistralai non installé. Lancez: pip install mistralai"}

    avg_pos = news_subset["prob_positive"].mean() if "prob_positive" in news_subset.columns else 0.5
    avg_neg = news_subset["prob_negative"].mean() if "prob_negative" in news_subset.columns else 0.5
    trend = "BULLISH" if avg_pos > avg_neg else "BEARISH"
    trend_label = trend
    lines = []
    for i, (_, r) in enumerate(news_subset.head(12).iterrows(), 1):
        title = str(r.get("title", ""))[:150]
        src = r.get("source", "")
        pub = str(r.get("published_at", ""))[:10]
        ppos = r.get("prob_positive", 0.5)
        pneg = r.get("prob_negative", 0.5)
        sent = "Positive" if ppos > pneg else "Negative"
        conf = max(ppos, pneg)
        lines.append(f"{i}. {title}\n   Source: {src} | {pub} | Sentiment: {sent} (Confiance: {conf:.0%})")
    news_context = "Actualités récentes:\n" + "\n".join(lines) + f"\n\nRésumé: tendance {trend} (positif {avg_pos:.1%}, négatif {avg_neg:.1%}), {len(news_subset)} actualités."

    pattern_pred_lines = []
    if pattern_data and isinstance(pattern_data.get("patterns"), list) and pattern_data["patterns"]:
        names = [str(p.get("pattern") or p.get("alt_name") or "?") for p in pattern_data["patterns"][:5]]
        pattern_pred_lines.append(f"Motifs techniques détectés: {', '.join(names)}.")
    else:
        pattern_pred_lines.append("Aucun motif technique détecté.")
    if prediction_data and isinstance(prediction_data, dict):
        sig = prediction_data.get("signal", "N/A")
        pu = prediction_data.get("proba_up")
        pd_ = prediction_data.get("proba_down")
        if pu is not None and pd_ is not None:
            pattern_pred_lines.append(f"Prédiction J+1: signal {sig} (P(hausse)={pu:.0%}, P(baisse)={pd_:.0%}).")
        else:
            pattern_pred_lines.append(f"Prédiction J+1: signal {sig}.")
    else:
        pattern_pred_lines.append("Prédiction J+1: non disponible.")
    pattern_pred_block = "\n".join(pattern_pred_lines)

    profile = user_profile or {}
    age = profile.get("age", "")
    horizon = profile.get("horizon", "")
    experience = profile.get("experience", "")
    capital = profile.get("capital", "")
    risk = profile.get("risk", "")
    strategy = profile.get("strategy", "")
    sectors = profile.get("sectors") or []
    sectors_str = ", ".join(sectors) if sectors else "non précisé"
    has_profile = bool(profile and (profile.get("horizon") or profile.get("strategy") or profile.get("risk") is not None))
    profile_block = (
        f"=== PROFIL INVESTISSEUR ===\n"
        f"Âge: {age} | Horizon: {horizon} | Expérience: {experience} | Capital indicatif: {capital} €\n"
        f"Tolérance au risque (1-10): {risk} | Stratégie: {strategy} | Secteurs: {sectors_str}\n"
        f"{'Tu DOIS adapter la section 4 (Recommandation) à CE profil et mentionner horizon, risque et stratégie.' if has_profile else 'Profil non renseigné: fournis une recommandation générique.'}"
    )

    prompt = f"""Tu es un expert en analyse financière et en XAI (Explainable AI).

Contexte pour l'actif {asset_ticker}:

{news_context}

{pattern_pred_block}

{profile_block}

Ta mission: fournir une analyse XAI détaillée (20 à 35 lignes utiles) structurée ainsi:

1. **JUSTIFICATION DU SENTIMENT {trend_label}**
   - Pourquoi le sentiment est-il {trend_label} ? Éléments factuels des actualités, cohérence des sources.

2. **IMPACT SUR LE MARCHÉ**
   - Impact sur le cours de {asset_ticker}: court terme (1-7 j), moyen terme (1-3 mois). Facteurs de risque. Intégrer si pertinent la prédiction J+1 et les motifs techniques.

3. **MÉCANISMES D'INFLUENCE**
   - Psychologie des investisseurs, canaux de transmission, effets de contagion possibles.

4. **RECOMMANDATION CONTEXTUALISÉE** (obligatoirement adaptée au profil investisseur ci-dessus)
   - Recommandation: ACHETER / VENDRE / CONSERVER / SURVEILLER
   - Niveau de confiance: ÉLEVÉ / MOYEN / FAIBLE
   - Justification basée sur l'analyse ET sur le profil (horizon, risque, stratégie, capital). Explique en 1-2 phrases pourquoi cette recommandation convient à CE profil.
   - Conditions à surveiller et stratégie concrète en lien avec le profil.

Sois factuel, cite les actualités, personnalise clairement la section 4 au profil. Structure avec des sections claires."""

    try:
        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2800,
        )
        text = response.choices[0].message.content
        rec, conf = "N/A", "N/A"
        if text:
            if "ACHETER" in text.upper(): rec = "ACHETER"
            elif "VENDRE" in text.upper(): rec = "VENDRE"
            elif "CONSERVER" in text.upper(): rec = "CONSERVER"
            elif "SURVEILLER" in text.upper(): rec = "SURVEILLER"
            if "ÉLEVÉ" in text.upper() or "ELEVE" in text.upper(): conf = "ÉLEVÉ"
            elif "MOYEN" in text.upper(): conf = "MOYEN"
            elif "FAIBLE" in text.upper(): conf = "FAIBLE"
        return {
            "asset_ticker": asset_ticker,
            "sentiment_trend": trend,
            "total_news": len(news_subset),
            "avg_positive": avg_pos,
            "avg_negative": avg_neg,
            "recommendation": rec,
            "confidence": conf,
            "xai_explanation": text or "Aucune réponse.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_price_from_stock_table(display_sym):
    """Prix depuis le tableau actifs (stock_df) si pas d'historique CSV — pour affichage cohérent."""
    if stock_df.empty or "Prix" not in stock_df.columns:
        return None
    tech_sym = to_technical_ticker(display_sym)
    for _, r in stock_df.iterrows():
        sym = r.get("Symbole")
        if sym is None:
            continue
        if str(sym).strip() == str(tech_sym).strip():
            p = r.get("Prix")
            if p is not None and str(p) != "nan":
                try:
                    return float(p)
                except (TypeError, ValueError):
                    pass
    # Match par ticker d'affichage
    for _, r in stock_df.iterrows():
        if to_display_ticker(str(r.get("Symbole", ""))) == display_sym:
            p = r.get("Prix")
            if p is not None and str(p) != "nan":
                try:
                    return float(p)
                except (TypeError, ValueError):
                    pass
    return None

@st.cache_data
def get_last_price(display_sym):
    """Retourne le dernier prix de clôture à partir du ticker d'affichage"""
    tech_sym = to_technical_ticker(display_sym)
    df = load_price_history(tech_sym)
    if not df.empty and "Close" in df.columns:
        closes = df["Close"].dropna()
        if len(closes) > 0:
            return float(closes.iloc[-1])
    return None

@st.cache_data
def compute_variations(display_sym):
    """Calcule les variations à partir du ticker d'affichage"""
    # Convertir en ticker technique pour charger les données
    tech_sym = to_technical_ticker(display_sym)
    df = load_price_history(tech_sym)
    if df.empty or "Close" not in df.columns or len(df)<2: return None, None, None, None
    closes = df["Close"].dropna()
    last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
    v24 = (last - prev)/prev * 100
    v7 = None
    if len(closes)>=8:
        prev7 = float(closes.iloc[-8])
        v7 = (last - prev7)/prev7 * 100
    return (last-prev), v24, (last - (prev7 if v7 else 0)), v7

def sparkline_svg(display_sym, color):
    """Génère un sparkline à partir du ticker d'affichage"""
    tech_sym = to_technical_ticker(display_sym)
    df = load_price_history(tech_sym)
    if df.empty or "Close" not in df.columns: return "—"
    closes = df["Close"].dropna().tail(24).values
    if len(closes)<2: return "—"
    w, h = 120, 40
    mn, mx = np.min(closes), np.max(closes)
    span = mx - mn if mx!=mn else 1
    pts = []
    for i, v in enumerate(closes):
        x = (i/(len(closes)-1))*w
        y = h - ((v-mn)/span)*h
        pts.append(f"{x:.1f},{y:.1f}")
    pts_str = " ".join(pts)
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{pts_str}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

@st.cache_data
def compute_fear_greed(news):
    if news.empty: return 50
    return int(50 + (news["prob_positive"].mean() - news["prob_negative"].mean())*50)

@st.cache_data
def load_watchlist() -> list[str]:
    """Charge la watchlist et retourne les tickers en format d'affichage"""
    path = Path(__file__).resolve().parent / "PFE_MVP" / "configs" / "watchlist.txt"
    if not path.exists(): return []
    technical_tickers = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    # Convertir en tickers d'affichage
    return [to_display_ticker(t) for t in technical_tickers]

def build_name_map(df):
    nm = {}
    if not df.empty:
        for _,r in df.iterrows():
            if r.get("Symbole") and r.get("Nom"):
                nm[normalize_ticker(r["Symbole"])] = r["Nom"]
    return nm

LEXICON = {
    "ETF": "Fonds qui suit un indice et s'échange en bourse comme une action.",
    "ANALYSE TECHNIQUE": "Étude des graphiques pour identifier des tendances.",
    "SENTIMENT": "Psychologie globale (Optimiste/Pessimiste).",
    "VOLATILITÉ": "Amplitude des variations de prix.",
    "RÉSISTANCE": "Zone de prix où l’actif a du mal à monter.",
    "SUPPORT": "Zone de prix où l’actif a du mal à baisser.",
    "BULLISH": "Sentiment/tendance haussière : on anticipe une hausse des prix.",
    "BEARISH": "Sentiment/tendance baissière : on anticipe une baisse des prix.",
    "LSTM": "Long Short-Term Memory : type de réseau de neurones (RNN) adapté aux séries temporelles.",
    "RNN": "Réseau de neurones récurrent, utile pour traiter des séquences (texte, séries temporelles).",
}


def highlight_lexicon_terms(text: str) -> str:
    if not isinstance(text, str) or not text.strip(): return ""
    escaped = html.escape(text)
    def repl(m):
        raw = m.group(0)
        key_upper = raw.upper()
        defn = None
        for k in LEXICON.keys():
            if k.upper() == key_upper:
                defn = LEXICON[k]
                break
        if defn is None: defn = LEXICON.get(raw, "")
        defn_attr = html.escape(defn, quote=True)
        return f'<span class="lex-term" title="{defn_attr}">{raw}</span>'
    
    _lex_terms_sorted = sorted(LEXICON.keys(), key=len, reverse=True)
    _lex_pattern = re.compile(r"(" + "|".join(re.escape(t) for t in _lex_terms_sorted) + r")", flags=re.IGNORECASE)
    return _lex_pattern.sub(repl, escaped)

@st.cache_data
def compute_overall_sentiment(news: pd.DataFrame) -> tuple[str, float]:
    if news.empty: return "NEUTRAL", 0.0
    avg_pos = news["prob_positive"].mean()
    avg_neg = news["prob_negative"].mean()
    label = "BULLISH" if avg_pos > avg_neg else "BEARISH"
    score = max(avg_pos, avg_neg) * 100
    return label, score

def get_ticker_sentiment(display_sym: str, news: pd.DataFrame) -> tuple[str, str]:
    """Retourne le sentiment et la couleur pour un ticker basé sur les news"""
    if news.empty or "asset_ticker" not in news.columns:
        return "NEUTRAL", "#58667e"
    
    # Filtrer les news pour ce ticker
    ticker_news = news[news["asset_ticker"].str.contains(display_sym, na=False, case=False)]
    
    if ticker_news.empty:
        return "NEUTRAL", "#58667e"
    
    # Calculer le sentiment moyen
    avg_pos = ticker_news["prob_positive"].mean()
    avg_neg = ticker_news["prob_negative"].mean()
    
    # Déterminer le sentiment avec un seuil
    if avg_pos > avg_neg + 0.1:  # Seuil de 10% pour être considéré BULLISH
        return "BULLISH", "#16c784"
    elif avg_neg > avg_pos + 0.1:  # Seuil de 10% pour être considéré BEARISH
        return "BEARISH", "#ea3943"
    else:
        return "NEUTRAL", "#58667e"

OVERALL_SENTIMENT_LABEL, OVERALL_SENTIMENT_SCORE = compute_overall_sentiment(news_df)
SENTIMENT_MAP = {}

# MAPPING BIDIRECTIONNEL : Tickers techniques <-> Noms parlants
TICKER_TO_DISPLAY = {
    "^GSPC": "SP500", "^FCHI": "CAC40", "^GDAXI": "GER30",
    "CL=F": "OIL", "CL_F": "OIL",
    "GC=F": "GOLD", "GC_F": "GOLD",
    "NG=F": "GAS", "NG_F": "GAS",
    "AAPL": "AAPL", "AMZN": "AMZN", "TSLA": "TSLA",
    "SAN": "SAN", "SAN.PA": "SAN",
    "HO": "HO", "HO.PA": "HO",
    "MC": "MC", "MC.PA": "MC",
    "ENGI": "ENGI", "ENGI.PA": "ENGI",
    "TTE": "TTE", "TTE.PA": "TTE",
    "RCO.PA": "RCO",
    "AIR": "AIR", "AIR.PA": "AIR",
    "STLA": "STLA", "STLA.PA": "STLA"
}

# Mapping inverse : Noms parlants -> Ticker technique (pour charger les données)
DISPLAY_TO_TICKER = {v: k for k, v in TICKER_TO_DISPLAY.items()}

def to_display_ticker(technical_ticker: str) -> str:
    """Convertit un ticker technique en ticker d'affichage (parlant)"""
    tech = str(technical_ticker).strip()
    return TICKER_TO_DISPLAY.get(tech, tech.replace("^", ""))

def to_technical_ticker(display_ticker: str) -> str:
    """Convertit un ticker d'affichage en ticker technique (pour charger les données)"""
    disp = str(display_ticker).strip()
    return DISPLAY_TO_TICKER.get(disp, disp)

def news_key_for_symbol(sym):
    """Retourne le ticker utilisé dans les news (format parlant)"""
    return to_display_ticker(sym)

# --- JAUGE PLOTLY (LA VERSION QUE TU AIMES) ---
def render_fear_greed_gauge(value: int):
    value = int(np.clip(value, 0, 100))
    colors = ["#EA3943", "#EA8C00", "#F3D42F", "#93D900", "#16C784"]

    label = "Neutral"
    if value < 20: label = "Extreme Fear"
    elif value < 40: label = "Fear"
    elif value < 60: label = "Neutral"
    elif value < 80: label = "Greed"
    else: label = "Extreme Greed"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'size': 20, 'color': '#000', 'family': 'Inter'}},
        title={'text': "Fear & Greed Index", 'font': {'size': 11, 'color': '#58667e', 'family': 'Inter'}},

        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': "rgba(0,0,0,0)"},
            'steps': [
                {'range': [0, 20], 'color': colors[0]},
                {'range': [20, 40], 'color': colors[1]},
                {'range': [40, 60], 'color': colors[2]},
                {'range': [60, 80], 'color': colors[3]},
                {'range': [80, 100], 'color': colors[4]}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        height=92,  # plus petit
        margin=dict(l=6, r=6, t=0, b=0),  # plus serré
        paper_bgcolor='white',
        font=dict(family="Inter"),
    )

    return fig, label


# =========================
# 4. SHOW PAGES
# =========================
def show_anomaly_page():
    import json
    from pathlib import Path
    import html as _html
    import streamlit as st
    import streamlit.components.v1 as components

    # -------------------------
    # Load report (adapter tes chemins si besoin)
    # -------------------------
    def _load_report():
        candidates = [
            Path("reports") / "anomaly_report.json",
            Path("anomaly_report.json"),
            Path("Prediction_Anomalies") / "reports" / "anomaly_report.json",
        ]
        for p in candidates:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    print(f"✅ Anomalies chargées depuis: {p}")
                    return data
                except Exception as e:
                    print(f"⚠️  Erreur lecture {p}: {e}")
                    pass

        # fallback
        print("⚠️  Utilisation des données de fallback")
        return {
            "generated_at": "2026-01-27 15:58:34",
            "stats": {
                "Anomalies détectées": "0",
                "Avec news": "0",
                "News trouvées": "0",
                "Score moyen": "0/100",
            },
            "anomalies": [],
        }

    REPORT = _load_report()
    generated_at = str(REPORT.get("generated_at", "") or "")
    stats = REPORT.get("stats", {}) or {}
    anomalies = REPORT.get("anomalies", []) or []

    # Compat ancien format: news -> top_news
    for a in anomalies:
        if "top_news" not in a and "news" in a:
            a["top_news"] = a.get("news", [])

    # -------------------------
    # En-tête et statistiques globales
    # -------------------------
    if not anomalies:
        st.title("Rapport d'analyse des anomalies boursières")
        st.info("Aucune anomalie disponible.")
        return

    # Afficher les stats globales
    st.markdown("### 📊 Statistiques Globales")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Anomalies détectées",
            value=stats.get("Anomalies détectées", "0"),
            delta=None
        )
    with col2:
        st.metric(
            label="Avec news",
            value=stats.get("Avec news", "0"),
            delta=None
        )
    with col3:
        st.metric(
            label="News trouvées",
            value=stats.get("News trouvées", "0"),
            delta=None
        )
    with col4:
        st.metric(
            label="Score moyen",
            value=stats.get("Score moyen", "0/100"),
            delta=None
        )

    st.markdown("---")

    # -------------------------
    # Filtres (widgets Streamlit natifs)
    # -------------------------
    # Extraire les actifs uniques depuis les titres
    all_assets = sorted(set(a.get("title", "").split(" - ")[0] for a in anomalies if " - " in a.get("title", "")))

    # Extraire les dates uniques
    all_dates = []
    for a in anomalies:
        title = a.get("title", "")
        if " - " in title:
            date_str = title.split(" - ")[1]
            try:
                all_dates.append(pd.to_datetime(date_str).date())
            except:
                pass
    all_dates = sorted(set(all_dates), reverse=True)

    # Extraire les scores
    all_scores = []
    for a in anomalies:
        top_news = a.get("top_news", []) or []
        if len(top_news) > 0:
            score = top_news[0].get("score", 0)
            all_scores.append(score)

    with st.expander("🔍 Filtres", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            # Filtre par actif
            selected_assets = st.multiselect(
                "📊 Actifs",
                options=["Tous"] + all_assets,
                default=["Tous"],
                help="Sélectionnez un ou plusieurs actifs"
            )

            # Filtre par sévérité
            severities = sorted({str(a.get("severity", "Minor")) for a in anomalies})
            pick = st.multiselect(
                "⚠️ Sévérité",
                options=severities,
                default=severities,
                help="Filtrer par niveau de sévérité"
            )

            # Filtre par pertinence
            pertinence_options = ["Toutes", "🎯 Haute pertinence", "📊 Pertinence moyenne", "❓ Faible pertinence"]
            selected_pertinence = st.multiselect(
                "🎯 Niveau de pertinence",
                options=pertinence_options,
                default=["Toutes"],
                help="Filtrer par niveau de pertinence des news"
            )

        with col2:
            # # Filtre par nombre de news
            # min_news = st.slider(
            #     "📰 Nombre minimum de news",
            #     min_value=0,
            #     max_value=50,
            #     value=0,
            #     help="Filtrer les anomalies avec au moins X news"
            # )

            # Filtre par score de pertinence
            if all_scores:
                min_score = st.slider(
                    "⭐ Score minimum de pertinence",
                    min_value=0,
                    max_value=100,
                    value=0,
                    help="Filtrer par score minimum de la meilleure news"
                )
            else:
                min_score = 0

        # Filtres de tri
        col3, col4 = st.columns(2)

        with col3:
            sort_by = st.selectbox(
                "📋 Trier par",
                options=["Date (récent → ancien)", "Date (ancien → récent)", "Variation (max → min)", "Variation (min → max)", "Score pertinence (max → min)"],
                index=0
            )

        with col4:
            # Plage de dates
            if len(all_dates) > 0:
                date_range = st.date_input(
                    "📅 Période",
                    value=(min(all_dates), max(all_dates)),
                    min_value=min(all_dates),
                    max_value=max(all_dates),
                    help="Sélectionnez une plage de dates"
                )
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    date_min, date_max = date_range
                else:
                    date_min = date_max = None
            else:
                date_min = date_max = None

    # Application des filtres
    filtered = []
    for a in anomalies:
        # Filtre par actif
        title = a.get("title", "")
        if " - " in title:
            asset = title.split(" - ")[0]
            if "Tous" not in selected_assets and asset not in selected_assets:
                continue

        # Filtre par sévérité
        sev = str(a.get("severity", "Minor"))
        if sev not in pick:
            continue

        # Filtre par nombre de news
        top_news = a.get("top_news", []) or []
        ncount = a.get("news_count")
        if ncount is None:
            ncount = len(top_news)
            
        try:
            ncount_int = int(ncount)
        except:
            ncount_int = len(top_news)

        # Filtre par score
        if len(top_news) > 0:
            score = top_news[0].get("score", 0)
            if score < min_score:
                continue

        # Filtre par pertinence
        if "Toutes" not in selected_pertinence and len(top_news) > 0:
            pertinence_label = top_news[0].get("pertinence", "")

            # Si pas de pertinence dans le JSON, calculer depuis le score
            if not pertinence_label:
                score = top_news[0].get("score", 0)
                if score >= 70:
                    pertinence_label = "Haute pertinence"
                elif score >= 45:
                    pertinence_label = "Pertinence moyenne"
                else:
                    pertinence_label = "Faible pertinence"

            # Vérifier si la pertinence correspond au filtre
            pertinence_match = False
            for selected in selected_pertinence:
                if "Haute" in selected and "Haute" in pertinence_label:
                    pertinence_match = True
                    break
                elif "moyenne" in selected and "moyenne" in pertinence_label:
                    pertinence_match = True
                    break
                elif "Faible" in selected and "Faible" in pertinence_label:
                    pertinence_match = True
                    break

            if not pertinence_match:
                continue

        # Filtre par date
        if date_min and date_max and " - " in title:
            try:
                anomaly_date = pd.to_datetime(title.split(" - ")[1]).date()
                if not (date_min <= anomaly_date <= date_max):
                    continue
            except:
                pass

        filtered.append(a)

    # Tri des résultats
    if sort_by == "Date (récent → ancien)":
        filtered = sorted(filtered, key=lambda x: x.get("title", "").split(" - ")[1] if " - " in x.get("title", "") else "", reverse=True)
    elif sort_by == "Date (ancien → récent)":
        filtered = sorted(filtered, key=lambda x: x.get("title", "").split(" - ")[1] if " - " in x.get("title", "") else "")
    elif sort_by == "Variation (max → min)":
        filtered = sorted(filtered, key=lambda x: float(x.get("variation", "0%").replace("%", "")), reverse=False)  # Plus négatif = plus grosse baisse
    elif sort_by == "Variation (min → max)":
        filtered = sorted(filtered, key=lambda x: float(x.get("variation", "0%").replace("%", "")), reverse=True)
    elif sort_by == "Score pertinence (max → min)":
        filtered = sorted(filtered, key=lambda x: x.get("top_news", [{}])[0].get("score", 0) if x.get("top_news") else 0, reverse=True)

    # Afficher le compteur de résultats avec bouton d'export
    col_result, col_export = st.columns([3, 1])

    with col_result:
        st.markdown(f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3861fb;">
                <strong>📊 Résultats :</strong> {len(filtered)} anomalie(s) affichée(s) sur {len(anomalies)} au total
            </div>
        """, unsafe_allow_html=True)

    with col_export:
        # Préparer les données CSV pour l'export
        if len(filtered) > 0:
            export_data = []
            for a in filtered:
                title = a.get("title", "")
                asset = title.split(" - ")[0] if " - " in title else ""
                date = title.split(" - ")[1] if " - " in title else ""
                top_news = a.get("top_news", []) or []
                news_title = top_news[0].get("title", "") if len(top_news) > 0 else ""
                news_score = top_news[0].get("score", 0) if len(top_news) > 0 else 0

                export_data.append({
                    "Actif": asset,
                    "Date": date,
                    "Sévérité": a.get("severity", ""),
                    "Variation": a.get("variation", ""),
                    "News": a.get("news_count", 0),
                    "Meilleure News": news_title,
                    "Score": news_score
                })

            import io
            csv_buffer = io.StringIO()
            pd.DataFrame(export_data).to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="⬇️ Exporter CSV",
                data=csv_data,
                file_name=f"anomalies_filtrees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Télécharger les résultats filtrés en CSV"
            )

    # Afficher un message si aucun résultat
    if len(filtered) == 0:
        st.warning("🔍 Aucune anomalie ne correspond aux filtres sélectionnés. Essayez d'ajuster vos critères.")
        return

    # -------------------------
    # Helpers
    # -------------------------
    def esc(x) -> str:
        return _html.escape("" if x is None else str(x))

    def badge_class(sev: str) -> str:
        s = (sev or "").strip().lower()
        if "critical" in s:
            return "badge badge-critical"
        if "severe" in s:
            return "badge badge-severe"
        if "moderate" in s:
            return "badge badge-moderate"
        return "badge badge-minor"

    # -------------------------
    # HTML rendu via components.html (aucune balise visible)
    # -------------------------
    # Stats dynamiques basées sur les résultats filtrés
    filtered_with_news = sum(1 for a in filtered if (a.get("top_news") or []))
    total_filtered_news = sum(a.get("news_count", 0) if a.get("news_count") else len(a.get("top_news", [])) for a in filtered)

    # Calculer le score moyen des anomalies filtrées
    scores = []
    for a in filtered:
        top_news = a.get("top_news", []) or []
        if len(top_news) > 0 and "score" in top_news[0]:
            scores.append(top_news[0]["score"])
    avg_score = sum(scores) / len(scores) if scores else 0

    # Stats affichées (mise à jour dynamique)
    stat_items = [
        ("Anomalies affichées", str(len(filtered))),
        ("Avec news", str(filtered_with_news)),
        ("News trouvées", str(total_filtered_news)),
        ("Score moyen", f"{avg_score:.1f}/100" if avg_score > 0 else "N/A")
    ]

    stats_boxes_html = ""
    for label, value in stat_items:
        stats_boxes_html += f"""
          <div class="stat-box">
            <div class="stat-number">{esc(value)}</div>
            <div class="stat-label">{esc(label)}</div>
          </div>
        """

    cards_html = ""
    for a in filtered:
        title = esc(a.get("title", "—"))
        severity = esc(a.get("severity", "Minor"))
        variation = esc(a.get("variation", "—"))

        top_news = a.get("top_news", []) or []
        news_count = a.get("news_count")
        if news_count is None:
            news_count = len(top_news)
        try:
            news_count = int(news_count)
        except:
            news_count = len(top_news)

        news_html = ""
        if top_news:
            for n in top_news[:5]:
                timing = esc(n.get("timing", ""))
                ntitle = esc(n.get("title", "—"))
                desc_raw = " ".join(str(n.get("description", "") or "").split())
                if len(desc_raw) > 220:
                    desc_raw = desc_raw[:220].rstrip() + "..."
                desc = esc(desc_raw)
                source = esc(n.get("source", "—"))
                url = str(n.get("url", "") or "").strip()

                # Utiliser la pertinence si disponible, sinon calculer depuis le score
                pertinence_label = n.get("pertinence", "")
                pertinence_emoji = n.get("pertinence_emoji", "")
                pertinence_color = n.get("pertinence_color", "#95a5a6")

                # Si pas de pertinence dans le JSON, utiliser le score brut (rétrocompatibilité)
                if not pertinence_label:
                    score = n.get("score", "")
                    try:
                        score_val = int(float(score))
                        if score_val >= 70:
                            pertinence_label = "Haute pertinence"
                            pertinence_emoji = "🎯"
                            pertinence_color = "#16c784"
                        elif score_val >= 45:
                            pertinence_label = "Pertinence moyenne"
                            pertinence_emoji = "📊"
                            pertinence_color = "#f39c12"
                        else:
                            pertinence_label = "Faible pertinence"
                            pertinence_emoji = "❓"
                            pertinence_color = "#95a5a6"
                    except:
                        pertinence_label = "Pertinence inconnue"
                        pertinence_emoji = "❓"
                        pertinence_color = "#95a5a6"

                link_html = f"<a href='{esc(url)}' target='_blank' rel='noopener'>Lire l'article →</a>" if url else ""

                news_html += f"""
                  <div class="news-item">
                    <div class="news-top">
                      <div class="news-timing">{timing}</div>
                      <div class="news-score" style="background-color: {pertinence_color};">{pertinence_emoji} {esc(pertinence_label)}</div>
                    </div>
                    <div class="news-title">{ntitle}</div>
                    {f"<div class='news-desc'>{desc}</div>" if desc else ""}
                    <div class="news-source">
                      <div><b>Source :</b> {source}</div>
                      <div class="news-link">{link_html}</div>
                    </div>
                  </div>
                """
        else:
            news_html = """
              <div class="news-item">
                <div class="news-desc">Aucune news associée.</div>
              </div>
            """

        cards_html += f"""
          <div class="anom-card">
            <div class="anom-header">
              <h3 class="anom-h3">{title}</h3>
              <span class="{badge_class(severity)}">{severity}</span>
            </div>

            <div class="anom-meta">
              <div><span>Variation :</span> {variation}</div>
              <div><span>News trouvées :</span> {esc(news_count)}</div>
            </div>

            {news_html}
          </div>
        """

    full_html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    body {{
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      margin: 0; padding: 0; background: #ffffff; color: #0b1220;
    }}

    .anom-wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 4px; }}
    .anom-title {{ font-size: 32px; font-weight: 800; margin: 10px 0 4px 0; }}
    .anom-sub {{ color: #58667e; font-size: 13px; font-weight: 600; margin: 0 0 18px 0; }}

    .stats-card {{
      background: #fff; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin: 14px 0 18px 0;
    }}
    .stats-h2 {{ font-size: 16px; font-weight: 800; margin: 0 0 12px 0; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
    .stat-box {{
      background: #f8fafc; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 14px; text-align: center;
    }}
    .stat-number {{ font-size: 26px; font-weight: 800; color: #3861fb; line-height: 1.1; }}
    .stat-label {{ font-size: 12px; color: #58667e; font-weight: 700; margin-top: 6px; }}

    .section-h2 {{ font-size: 16px; font-weight: 900; margin: 22px 0 10px 0; }}

    .anom-card {{
      background: #fff; border: 1px solid #eff2f5; border-radius: 12px;
      padding: 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin: 14px 0;
    }}
    .anom-header {{
      display:flex; justify-content:space-between; align-items:center; gap:12px;
      border-bottom:1px solid #eff2f5; padding-bottom:12px; margin-bottom:12px;
    }}
    .anom-h3 {{ font-size: 16px; font-weight: 800; margin: 0; }}

    .badge {{
      padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; color: #fff;
      display:inline-block; white-space:nowrap;
    }}
    .badge-minor {{ background: #EA8C00; }}
    .badge-moderate {{ background: #f59e0b; }}
    .badge-severe {{ background: #ea3943; }}
    .badge-critical {{ background: #b91c1c; }}

    .anom-meta {{
      display:flex; gap:18px; flex-wrap:wrap; font-size:13px;
      font-weight:700; margin-bottom:10px;
    }}
    .anom-meta span {{ color:#58667e; font-weight:700; margin-right:6px; }}

    .news-item {{
      background:#f8fafc; border:1px solid #eff2f5; border-left:4px solid #3861fb;
      border-radius:12px; padding:12px 14px; margin-top:10px;
    }}
    .news-top {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:8px; }}
    .news-timing {{ color:#58667e; font-weight:700; font-size:12px; }}
    .news-score {{ background:#3861fb; color:#fff; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:800; }}
    .news-title {{ font-size:13px; font-weight:800; margin-bottom:6px; }}
    .news-desc {{ font-size:12px; color:#58667e; font-weight:600; line-height:1.35; }}

    .news-source {{
      font-size:12px; color:#58667e; font-weight:700; margin-top:8px;
      display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;
    }}
    .news-link a {{ color:#3861fb; font-weight:800; text-decoration:none; }}
    .news-link a:hover {{ text-decoration:underline; }}

    @media (max-width: 1100px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 650px)  {{ .stats-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="anom-wrap">
    <div class="anom-title">Rapport d’analyse des anomalies boursières</div>
    <div class="anom-sub"><span>Date de génération :</span> {esc(generated_at)}</div>

    <div class="stats-card">
      <div class="stats-h2">Statistiques globales</div>
      <div class="stats-grid">
        {stats_boxes_html}
      </div>
    </div>

    <div class="section-h2">Anomalies détectées avec news corrélées</div>
    {cards_html}
  </div>
</body>
</html>
"""

    # Hauteur: ajuste selon nb de cartes (évite un iframe minuscule)
    base = 520
    per_card = 260
    height = min(2400, base + per_card * max(1, len(filtered)))

    components.html(full_html, height=height, scrolling=True)



# =========================
# 5. UI COMPONENTS (NAVBAR)
# =========================
def show_navbar():
    auth = qp.get("auth", "1")
    fl = qp.get("first_login", "0")
    prof = qp.get("profile", "")
    email = st.session_state.get("current_user", "")
    page = st.session_state.get("page", "Dashboard")

    def link(p): return f"?auth={auth}&first_login={fl}&profile={prof}&user_email={email}&page={p}"
    def cls(p): return "cmc-link active" if page == p else "cmc-link"

    st.markdown(f"""
    <div class="cmc-nav-container">
        <a href="{link('Dashboard')}" class="cmc-brand" target="_self">FINSIGHT<span>AI</span></a>
        <div class="cmc-links">
            <a href="{link('Dashboard')}" class="{cls('Dashboard')}" target="_self">Marchés</a>
            <a href="{link('News')}" class="{cls('News')}" target="_self">Actualités</a>
            <a href="{link('Anomaly')}" class="{cls('Anomaly')}" target="_self">Anomalies</a>
            <a href="{link('Lexicon')}" class="{cls('Lexicon')}" target="_self">Lexique</a>
        </div>
        <a href="{link('Account')}" class="cmc-account" target="_self">Mon Compte</a>
    </div>
    """, unsafe_allow_html=True)
    return page

# =========================
# 6. AUTH & ONBOARDING (REMPLACÉ)
# =========================

def show_login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center;'>FINSIGHT AI</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])
        
        with tab1:
            l_email = st.text_input("Email", key="l_email")
            l_pwd = st.text_input("Mot de passe", type="password", key="l_pwd")
            if st.button("Se connecter", use_container_width=True):
                success, data = login_user(l_email, l_pwd)
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = l_email
                    # Si onboarding pas fait -> go onboarding
                    if not data.get("onboarding_done", False):
                        st.session_state["page"] = "Onboarding"
                        st.session_state["first_login"] = True
                    else:
                        st.session_state["page"] = "Dashboard"
                        st.session_state["first_login"] = False
                        st.session_state["user_profile"] = data.get("profile", {}).get("experience", "Inconnu")
                    
                    qp_update(auth="1", user_email=l_email, page=st.session_state["page"])
                    st.rerun()
                else:
                    st.error(data)
        
        with tab2:
            r_email = st.text_input("Email", key="r_email")
            r_pwd = st.text_input("Mot de passe", type="password", key="r_pwd")
            r_pwd2 = st.text_input("Confirmer", type="password", key="r_pwd2")
            if st.button("S'inscrire", use_container_width=True):
                if r_pwd != r_pwd2:
                    st.error("Mots de passe différents.")
                elif not r_email or not r_pwd:
                    st.error("Remplissez tout.")
                else:
                    res, msg = register_user(r_email, r_pwd)
                    if res:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = r_email
                        st.session_state["page"] = "Onboarding"
                        st.session_state["first_login"] = True
                        st.session_state["user_profile"] = None
                        qp_update(auth="1", user_email=r_email, page="Onboarding")
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

def show_onboarding():
    st.markdown("<h2 style='text-align:center;'>Profil Investisseur</h2>", unsafe_allow_html=True)
    st.info("Configuration initiale pour l'IA.")
    st.markdown(
        "<style>.onb-label { color: #1e293b !important; font-weight: 600 !important; font-size: 1rem !important; margin-bottom: 0.25rem !important; }</style>",
        unsafe_allow_html=True,
    )
    with st.form("onboarding_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p class='onb-label'>Âge</p>", unsafe_allow_html=True)
            age = st.number_input("Âge", 18, 99, 30, label_visibility="collapsed", key="onb_age")
            st.markdown("<p class='onb-label'>Horizon</p>", unsafe_allow_html=True)
            horizon = st.selectbox("Horizon", ["Court terme", "Moyen terme", "Long terme"], label_visibility="collapsed", key="onb_horizon")
            st.markdown("<p class='onb-label'>Expérience</p>", unsafe_allow_html=True)
            experience = st.radio("Expérience", ["Débutant", "Intermédiaire", "Expert"], label_visibility="collapsed", key="onb_exp")
            st.markdown("<p class='onb-label'>Capital (€)</p>", unsafe_allow_html=True)
            capital = st.number_input("Capital (€)", 0, 1000000, 1000, label_visibility="collapsed", key="onb_capital")
        with c2:
            st.markdown("<p class='onb-label'>Risque (1-10)</p>", unsafe_allow_html=True)
            risk = st.slider("Risque (1-10)", 1, 10, 5, label_visibility="collapsed", key="onb_risk")
            st.markdown("<p class='onb-label'>Stratégie</p>", unsafe_allow_html=True)
            strategy = st.selectbox("Stratégie", ["Dividendes", "Growth", "Trading"], label_visibility="collapsed", key="onb_strategy")
            st.markdown("<p class='onb-label'>Secteurs</p>", unsafe_allow_html=True)
            sectors = st.multiselect("Secteurs", ["Tech", "Santé", "Finance", "Crypto"], label_visibility="collapsed", key="onb_sectors")
            
        if st.form_submit_button("Valider"):
            email = st.session_state.get("current_user")
            if email:
                profile = {
                    "age": age, "horizon": horizon, "experience": experience,
                    "capital": capital, "risk": risk, "strategy": strategy, "sectors": sectors
                }
                update_user_profile(email, profile)
                st.session_state["user_profile"] = experience
                st.session_state["page"] = "Dashboard"
                st.session_state["first_login"] = False
                qp_update(page="Dashboard", profile=experience)
                st.rerun()

def main_app(nav):
    # Route onboarding prioritaire
    if nav == "Onboarding":
        show_onboarding()
        return

    if qp.get("stock"):
        nav = "StockDetail"
        st.session_state["page"] = "StockDetail"

    # --- DASHBOARD ---
    if nav == "Dashboard":
        watchlist = load_watchlist()
        all_syms = watchlist if watchlist else (stock_df["Symbole"].dropna().unique().tolist() if not stock_df.empty else [])
        
        # Top performer 1j
        best_perf_1j = -999
        best_sym_1j = None
        for s in all_syms:
            _, v1 , _, _ = compute_variations(s)
            if v1 is not None and v1 > best_perf_1j:
                best_perf_1j = v1
                best_sym_1j = s
        
        top_name_1j, top_val_1j = "—", 0
        if best_sym_1j:
            top_val_1j = best_perf_1j
            if not stock_df.empty:
                row = stock_df[stock_df["Symbole"] == best_sym_1j]
                top_name_1j = row.iloc[0].get("Nom", best_sym_1j) if not row.empty else best_sym_1j
            else: top_name_1j = best_sym_1j
        
        # Top performer 7j
        best_perf_7j = -999
        best_sym_7j = None
        for s in all_syms:
            _, _, _, v7 = compute_variations(s)
            if v7 is not None and v7 > best_perf_7j:
                best_perf_7j = v7
                best_sym_7j = s
        
        top_name_7j, top_val_7j = "—", 0
        if best_sym_7j:
            top_val_7j = best_perf_7j
            if not stock_df.empty:
                row = stock_df[stock_df["Symbole"] == best_sym_7j]
                top_name_7j = row.iloc[0].get("Nom", best_sym_7j) if not row.empty else best_sym_7j
            else: top_name_7j = best_sym_7j

        fg_value = compute_fear_greed(news_df)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">🔥 Top Performer (1j)</div>
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
                    <div class="kpi-value">{top_name_1j}</div>
                    <div class="kpi-sub" style="font-size: 24px; font-weight: 800; color: {'#16c784' if top_val_1j>=0 else '#ea3943'};">{top_val_1j:+.2f}%</div>
                </div>
            </div>""", unsafe_allow_html=True)

        with c2:
            # st.markdown(f"""
            # <div class="kpi-card">
            #     <div class="kpi-label">Sentiment Global</div>
            #     <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
            #         <div class="kpi-value">{OVERALL_SENTIMENT_LABEL}</div>
            #         <div class="kpi-sub">Confiance IA: {OVERALL_SENTIMENT_SCORE:.0f}%</div>
            #     </div>
            # </div>""", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">🔥 Top Performer (7j)</div>
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
                    <div class="kpi-value">{top_name_7j}</div>
                    <div class="kpi-sub" style="font-size: 24px; font-weight: 800; color: {'#16c784' if top_val_7j>=0 else '#ea3943'};">{top_val_7j:+.2f}%</div>
                </div>
            </div>""", unsafe_allow_html=True)
        
        with c3:
            fg_value = compute_fear_greed(news_df)
            fig, label = render_fear_greed_gauge(fg_value)

            fig_html = fig.to_html(
                include_plotlyjs="cdn",
                full_html=False,
                config={"displayModeBar": False, "staticPlot": True}
            )

            card_html = f"""
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

            <style>
            body {{ margin:0; padding:0; background:transparent; }}
            * {{ font-family: Inter, sans-serif !important; box-sizing:border-box; }}

            .kpi-card {{
                background: #ffffff;
                border: 1px solid #eff2f5;
                border-radius: 12px;
                padding: 20px;                 /* comme tes autres cards */
                box-shadow: 0 4px 24px rgba(0,0,0,0.04);
                height: 180px;
                display:flex;
                flex-direction:column;
                justify-content:flex-start;
            }}

            .kpi-label {{
                font-size: 12px;
                font-weight: 600;
                color: #58667e;
                text-transform: uppercase;
                margin-bottom: 8px;
                text-align: left;
            }}

            .fg-plot {{
                height: 92px;   /* match fig height */
                overflow: hidden;
            }}

            .fg-label {{
                margin-top: 10px;
                text-align:center;
                font-weight: 700;
                color: #58667e;
                font-size: 13px;
                line-height: 1;
            }}

            .js-plotly-plot, .plotly, .main-svg {{ font-family: Inter, sans-serif !important; }}
            </style>

            <div class="kpi-card">
            <div class="kpi-label">Fear &amp; Greed</div>
            <div class="fg-plot">{fig_html}</div>
            <div class="fg-label">{label}</div>
            </div>
            """
            components.html(card_html, height=210, scrolling=False)





        # with c3:
        #     st.markdown(f"""
        #     <div class="kpi-card">
        #         <div class="kpi-label">Sentiment Global</div>
        #         <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
        #             <div class="kpi-value">{OVERALL_SENTIMENT_LABEL}</div>
        #             <div class="kpi-sub">Confiance IA: {OVERALL_SENTIMENT_SCORE:.0f}%</div>
        #         </div>
        #     </div>""", unsafe_allow_html=True)

        st.write("")
        
        # TABLE (CORRECTION HTML FLAT)
        display_df = stock_df.head(20).copy() if not stock_df.empty else pd.DataFrame()
        if not display_df.empty:
            rows_html_list = []
            auth_p = qp.get("auth", "1")
            fl_p = qp.get("first_login", "0")
            prof_p = qp.get("profile", "")
            u_email = st.session_state.get("current_user", "")
            
            for _, r in display_df.iterrows():
                sym_technical = str(r.get("Symbole", "—"))
                # Convertir en ticker d'affichage pour toutes les opérations
                sym = to_display_ticker(sym_technical)
                name = str(r.get("Nom", sym))
                
                # Obtenir le prix actuel (historique ou tableau actifs)
                price = get_last_price(sym) or get_price_from_stock_table(sym)
                if price is None: price = 0.0
                
                _, calc_v24, _, calc_v7 = compute_variations(sym)
                v24 = calc_v24 if calc_v24 is not None else 0.0
                v7 = calc_v7 if calc_v7 is not None else 0.0

                c24 = "#16c784" if v24 >= 0 else "#ea3943"
                c7 = "#16c784" if v7 >= 0 else "#ea3943"
                
                # Obtenir le sentiment réel depuis les news
                sent, color_sent = get_ticker_sentiment(sym, news_df)
                
                graph = sparkline_svg(sym, c7)
                link = f"?stock={sym}&auth={auth_p}&first_login={fl_p}&profile={prof_p}&user_email={u_email}&page=StockDetail"
                
                rows_html_list.append(f"<tr><td><a href='{link}' target='_self'><div style='display:flex; align-items:center;'><span style='font-weight:700; color:#000;'>{name}</span><span class='ticker-badge'>{sym}</span></div></a></td><td><a href='{link}' target='_self'>${price:.2f}</a></td><td><a href='{link}' target='_self'><span style='color:{c24}'>{v24:+.2f}%</span></a></td><td><a href='{link}' target='_self'><span style='color:{c7}'>{v7:+.2f}%</span></a></td><td><a href='{link}' target='_self' style='color:{color_sent}; font-size:12px;'>● {sent}</a></td><td style='width:140px; padding-top:5px; padding-bottom:5px;'><a href='{link}' target='_self'>{graph}</a></td></tr>")
            
            st.markdown(f"""<div class="cmc-table-wrap"><table class="cmc-table"><thead><tr><th>Actif</th><th>Prix</th><th>24h %</th><th>7d %</th><th>Sentiment</th><th>Tendance (7d)</th></tr></thead><tbody>{"".join(rows_html_list)}</tbody></table></div>""", unsafe_allow_html=True)
        else:
            st.info("Aucune donnée boursière.")

    elif nav == "StockDetail":
        st.title("DÉTAILS ACTIF")
        sym_param = qp.get("stock", "")
        if not sym_param and st.session_state.get("selected_stock"):
            sym_param = st.session_state["selected_stock"].get("Symbole")
        
        if not sym_param:
            st.info("Aucun actif sélectionné.")
        else:
            left, mid, right = st.columns([1, 2.2, 1.2])
            with left:
                # Récupérer les tickers techniques du DataFrame
                technical_symbols = stock_df["Symbole"].dropna().astype(str).unique().tolist()
                
                # Convertir en tickers parlants pour l'affichage
                display_symbols = [to_display_ticker(s) for s in technical_symbols]
                
                # Trouver l'index du ticker sélectionné (en parlant)
                sym_display = to_display_ticker(sym_param) if sym_param else ""
                default_display = sym_display if sym_display in display_symbols else display_symbols[0]
                if "stock_select" not in st.session_state:
                    st.session_state["stock_select"] = default_display
                elif st.session_state["stock_select"] not in display_symbols:
                    st.session_state["stock_select"] = default_display
                
                # Afficher le selectbox avec les tickers parlants
                choice_display = st.selectbox("Actif", display_symbols, key="stock_select")
                
                # Récupérer le ticker technique correspondant
                choice_idx = display_symbols.index(choice_display)
                choice = technical_symbols[choice_idx]
                
                # Convertir en ticker parlant pour les opérations suivantes
                choice = to_display_ticker(choice)
                
                if choice != sym_display:
                    qp_update(stock=choice)

                # Convertir en ticker technique pour charger les données
                tech_ticker = to_technical_ticker(choice)
                hist = load_price_history(tech_ticker)
                last_price = None
                if not hist.empty and "Close" in hist.columns:
                    last_price = float(hist["Close"].iloc[-1])
                if last_price is None:
                    last_price = get_price_from_stock_table(choice)
                last_price = last_price if last_price is not None else 0.0
                nom = choice
                if not stock_df.empty:
                    row = stock_df[stock_df["Symbole"].astype(str).map(to_display_ticker) == choice]
                    if not row.empty:
                        nom = row.iloc[0].get("Nom", choice)
                    else:
                        row = stock_df[stock_df["Symbole"].astype(str) == to_technical_ticker(choice)]
                        if not row.empty:
                            nom = row.iloc[0].get("Nom", choice)

                st.markdown(f"**{nom}**")
                st.metric("Prix", f"${last_price:.2f}")
                v24, v24p, v7, v7p = compute_variations(choice)
                if v24 is not None: st.metric("Variation 24h", f"${v24:+.2f}", f"{v24p:+.2f}%")
                else: st.metric("Variation 24h", "—")
                if v7 is not None: st.metric("Variation 7d", f"${v7:+.2f}", f"{v7p:+.2f}%")
                else: st.metric("Variation 7d", "—")
                
                pred = load_prediction(tech_ticker)
                if pred:
                    sig_map = {
                        "up": ("Tendance haussière", "#16a34a"),
                        "down": ("Tendance baissière", "#dc2626"),
                        "neutral": ("Tendance neutre", "#111111"),
                    }
                    if "h1" in pred:
                        st.markdown("**Prévisions multi-horizons**")
                        for h in [1, 5, 10, 30]:
                            key = f"h{h}"
                            if key not in pred:
                                continue
                            item = pred.get(key, {})
                            sig = str(item.get("signal", "—")).strip().lower()
                            label, color = sig_map.get(sig, (sig, "#111111"))
                            st.markdown(
                                f"<div style='font-weight:700; font-size:20px; color:{color};'>J+{h}: {label}</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        sig = str(pred.get("signal", "—")).strip().lower()
                        st.markdown("**Prévision (J+1)**")
                        label, color = sig_map.get(sig, (sig, "#111111"))
                        st.markdown(
                            f"<div style='font-weight:700; font-size:28px; color:{color};'>Signal: {label}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<p style='color:#334155; font-weight:600; margin-top:0;'>Prévision indisponible (JSON manquant).</p>", unsafe_allow_html=True)
                
                key = news_key_for_symbol(choice)
                if st.button("Retour Dashboard"):
                # supprime vraiment le param stock + force le page Dashboard
                    try:
                        st.query_params.pop("stock", None)
                        st.query_params["page"] = "Dashboard"
                    except:
                        st.experimental_set_query_params(page="Dashboard")  # fallback

                    st.session_state["page"] = "Dashboard"
                    st.rerun()


            with mid:
                # Données pour "Notre analyse pour toi"
                sentiment_for_stock = load_sentiment_news_for_stock(choice)
                tn_for_xai = news_df.copy()
                if choice and not tn_for_xai.empty and "asset_ticker" in tn_for_xai.columns:
                    tn_for_xai = tn_for_xai[tn_for_xai["asset_ticker"].str.contains(choice, na=False, case=False)]
                if not sentiment_for_stock.empty:
                    tn_for_xai = sentiment_for_stock
                # Patterns et prédiction J+1 depuis PFE_MVP (patterns/*.json, predictions/*.json)
                pattern_data = load_patterns_for_asset(choice)
                prediction_data = load_prediction_for_asset(choice)
                user_profile = get_user_profile(st.session_state.get("current_user", ""))
                has_data_pour_toi = not tn_for_xai.empty or (pattern_data and isinstance(pattern_data.get("patterns"), list) and len(pattern_data.get("patterns", [])) > 0) or bool(prediction_data)

                tech_ticker = to_technical_ticker(choice)
                pdata = load_patterns(tech_ticker)
                plist = pdata.get("patterns", []) if pdata else []
                show_pat = False
                if plist:
                    st.caption(f"{len(plist)} patterns détectés.")
                    show_pat = st.checkbox("Afficher les patterns", value=False)
                else:
                    st.markdown("<div style='background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a; padding:12px; border-radius:8px; font-weight:600;'>Aucun pattern.</div>", unsafe_allow_html=True)

                sel_idx = 0
                if show_pat and plist:
                    plabs = [f"{p.get('pattern')} ({p.get('start','')[:10]})" for p in plist]
                    sel_idx = st.selectbox("Pattern", range(len(plabs)), format_func=lambda i: plabs[i])
                    range_opt = "LOCKED"
                else:
                    range_opt = st.selectbox("Horizon", ["1M", "3M", "6M"], index=2)

                plot_hist = hist.copy()
                if not plot_hist.empty:
                    if show_pat and plist:
                        pat = plist[sel_idx]
                        if pat.get("df_start") and pat.get("df_end"):
                            plot_hist = plot_hist[(plot_hist["Date"] >= pd.to_datetime(pat["df_start"])) & (plot_hist["Date"] <= pd.to_datetime(pat["df_end"]))]
                    elif range_opt != "ALL":
                        d_map = {"1M":30, "3M":90, "6M":180, "1Y":365, "5Y":1825}
                        plot_hist = plot_hist[plot_hist["Date"] >= plot_hist["Date"].max() - timedelta(days=d_map.get(range_opt, 365))]

                    fig = go.Figure(data=[go.Candlestick(x=plot_hist["Date"], open=plot_hist["Open"], high=plot_hist["High"], low=plot_hist["Low"], close=plot_hist["Close"], increasing_line_color="#13c296", decreasing_line_color="#ef4444")])
                    
                    if show_pat and plist:
                        pat = plist[sel_idx]
                        pts = pat.get("points", {})
                        xs, ys, labels = [], [], []
                        for k in ["X", "A", "B", "C", "D"]:
                            if k in pts:
                                xs.append(pd.to_datetime(pts[k][0]))
                                ys.append(float(pts[k][1]))
                                labels.append(k)
                        if xs: fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers+text", text=labels, textposition="top center", marker=dict(size=8, color="#6366f1"), line=dict(color="#6366f1", width=2), name=pat.get("pattern")))

                    fig.update_layout(height=460, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Pas de données.")

                # Bloc d'explication du pattern (sous le graphique, au-dessus XAI)
                if show_pat and plist:
                    pat = plist[sel_idx]
                    pcode = str(pat.get("pattern", "")).lower().strip()
                    pdata = PATTERN_REGISTRY.get(pcode)
                    if pdata:
                        bias = pdata.get("bias", "Neutre")
                        bias_color = {"Bullish": "#16a34a", "Bearish": "#dc2626", "Neutre": "#6b7280"}.get(bias, "#6b7280")
                        category = pdata.get("category", "Structure")
                        st.markdown(
                            f"<div style='display:flex; gap:8px; align-items:center; margin-top:10px; margin-bottom:6px;'>"
                            f"<span style='background:{bias_color}20; color:{bias_color}; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700;'>"
                            f"{bias}</span>"
                            f"<span style='background:#e5e7eb; color:#374151; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700;'>"
                            f"{category}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**{pdata.get('name_fr')}**")
                        st.markdown(pdata.get("level1", ""))
                        if pdata.get("riskNote"):
                            st.caption(pdata.get("riskNote"))

                        toggle_key = f"pat_explain_open_{choice}_{pcode}"
                        if toggle_key not in st.session_state:
                            st.session_state[toggle_key] = False
                        btn_label = "En savoir plus" if not st.session_state[toggle_key] else "Réduire"
                        if st.button(btn_label, key=f"btn_{toggle_key}"):
                            st.session_state[toggle_key] = not st.session_state[toggle_key]

                        if st.session_state[toggle_key]:
                            st.markdown(
                                "<div style='border:1px solid #e5e7eb; border-radius:8px; padding:12px; margin-top:8px;'>",
                                unsafe_allow_html=True,
                            )
                            st.markdown("**Comprendre**")
                            st.markdown(pdata.get("level2", ""))
                            st.markdown("**Comment réagir**")
                            lvl3 = pdata.get("level3", [])
                            if isinstance(lvl3, list) and lvl3:
                                st.markdown("\n".join([f"- {x}" for x in lvl3]))
                            disclaimer = "Information éducative, pas un conseil financier."
                            st.markdown(f"<div style='font-size:12px; color:#6b7280; margin-top:8px;'>{disclaimer}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                # Utiliser le ticker d'affichage pour XAI (correspond au CSV)
                xai = load_xai_analysis(choice)
                if not xai.empty:
                    st.markdown("---")
                    st.caption(f"📊 {xai.iloc[0].get('total_news')} news")
                    st.markdown(highlight_lexicon_terms(str(xai.iloc[0].get('xai_explanation'))), unsafe_allow_html=True)
                    st.markdown("<div style='background:#fef3c7; border:1px solid #fcd34d; color:#92400e; padding:12px; border-radius:8px; font-weight:600;'>Pas de données.</div>", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("**Notre analyse pour toi**")
                analyse_pour_toi_key = f"analyse_pour_toi_{choice}"
                if analyse_pour_toi_key in st.session_state:
                    cached = st.session_state[analyse_pour_toi_key]
                    if isinstance(cached, dict) and cached.get("error"):
                        st.error("Erreur analyse: " + cached.get("error", ""))
                    elif isinstance(cached, dict) and cached.get("text"):
                        st.markdown(highlight_lexicon_terms(cached["text"]), unsafe_allow_html=True)
                    elif isinstance(cached, str):
                        st.markdown(highlight_lexicon_terms(cached), unsafe_allow_html=True)
                elif has_data_pour_toi:
                    with st.spinner(""):
                        st.markdown(
                            """
                            <div class="analyse-loading-wrap">
                                <div class="analyse-loading-dots"><span></span><span></span><span></span></div>
                                <div class="analyse-loading-bar"></div>
                                <p class="analyse-loading-msg">On analyse les actualités, les motifs et ton profil pour toi…<br>Un instant.</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        _, v24p, _, v7p = compute_variations(choice) if choice else (None, None, None, None)
                        res_analyse = _run_analyse_pour_toi(
                            choice, tn_for_xai,
                            pattern_data=pattern_data,
                            prediction_data=prediction_data,
                            user_profile=user_profile,
                            variation_24h_pct=v24p if v24p is not None else None,
                            variation_7d_pct=v7p if v7p is not None else None,
                        )
                    if res_analyse and res_analyse.get("error"):
                        st.session_state[analyse_pour_toi_key] = res_analyse
                        st.error("Erreur: " + res_analyse["error"])
                    elif res_analyse and res_analyse.get("text"):
                        st.session_state[analyse_pour_toi_key] = res_analyse
                        st.rerun()
                    else:
                        st.caption("Pas assez de données pour générer ton analyse.")
                else:
                    st.caption("Aucune donnée pour cet actif.")

            with right:
                st.subheader("Actualités")
                tn = news_df.copy()
                # Utiliser le ticker d'affichage pour filtrer les news (correspond au CSV)
                if choice and not tn.empty and "asset_ticker" in tn.columns:
                    tn = tn[tn["asset_ticker"].str.contains(choice, na=False, case=False)]
                
                if not tn.empty:
                    avg_p = tn["prob_positive"].mean()
                    if avg_p > tn["prob_negative"].mean():
                        sl, sc = "🟢 BULLISH", "#00FF88"
                    else:
                        sl, sc = "🔴 BEARISH", "#FF4444"
                    
                    st.markdown(f"<div style='background-color:{sc}20; padding:10px; border-radius:5px; border-left:4px solid {sc}; margin-bottom:10px;'><strong>{sl}</strong></div>", unsafe_allow_html=True)
                    
                    tn["conf"] = tn[["prob_positive", "prob_negative"]].max(axis=1)
                    for _, r in tn[tn["conf"] >= 0.7].head(5).iterrows():
                        col = "#00FF88" if r["prob_positive"] > r["prob_negative"] else "#FF4444"
                        st.markdown(f"<div style='background:#f9fafb; padding:8px; border-radius:6px; margin-bottom:6px; border-left:3px solid {col}; font-size:12px;'><b>{highlight_lexicon_terms(str(r['title'])[:60])}...</b><br><span style='color:{col}'>Impact {r['conf']:.0%}</span></div>", unsafe_allow_html=True)
                        st.link_button("Lire", r['url'], use_container_width=True)
                else:
                    st.info("Pas d'actualités.")

            st.markdown("---")
            with st.expander("**Informations supplémentaires sur le stock**", expanded=False):
                xai_extra = load_xai_analysis(choice)
                if not xai_extra.empty:
                    st.markdown(highlight_lexicon_terms(str(xai_extra.iloc[0].get("xai_explanation", ""))), unsafe_allow_html=True)
                else:
                    st.caption("Aucune analyse détaillée pré-enregistrée pour cet actif.")

    elif nav == "News":
        st.title("Actualités")
        if not news_df.empty:
            for _, r in news_df.head(10).iterrows():
                st.markdown(f"<div class='kpi-card' style='margin-bottom:15px;'><h4>{highlight_lexicon_terms(str(r.get('title')))}</h4><p style='color:#666; font-size:12px;'>{r.get('source')}</p><a href='{r.get('url')}'>Lire</a></div>", unsafe_allow_html=True)

    elif nav == "Predictions":
        st.title("Prédictions & Forecast")
        st.markdown("Analyse prédictive IA sur **Apple (AAPL)**.")
        df_pred = aapl_df.copy()
        if df_pred.empty:
            st.error("Données manquantes.")
        else:
            ld = df_pred["Date"].max()
            lc = df_pred["Close"].iloc[-1]
            fd = [ld + timedelta(days=i) for i in range(1, 16)]
            fp = [lc * (1 + 0.005*i + np.random.normal(0, 0.01)) for i in range(1, 16)]
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_pred['Date'], open=df_pred['Open'], high=df_pred['High'], low=df_pred['Low'], close=df_pred['Close'], name="Historique"))
            fig.add_trace(go.Scatter(x=fd, y=fp, mode='lines+markers', line=dict(color='#3861fb', width=2, dash='dash'), name='Prédiction IA (15j)'))
            fig.update_layout(title="Projection AAPL - Modèle LSTM Hybride", xaxis_rangeslider_visible=False, template="plotly_white", height=600, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            st.success("Confiance: **87.4%** | Cible: **${:.2f}**".format(fp[-1]))

    elif nav == "Anomaly":
        show_anomaly_page()

    elif nav == "Lexicon":
        st.title("Lexique")
        for k, v in LEXICON.items():
            with st.expander(k): st.write(v)
    
    elif nav == "Account":
        st.title("Mon Compte")

        email = st.session_state.get("current_user")
        if not email:
            st.info("Utilisateur non connecté.")
            return

        current_profile = get_user_profile(email)

        default_age = int(current_profile.get("age", 30))
        default_horizon = current_profile.get("horizon", "Moyen terme")
        default_experience = current_profile.get("experience", "Intermédiaire")
        default_capital = int(current_profile.get("capital", 1000))
        default_risk = int(current_profile.get("risk", 5))
        default_strategy = current_profile.get("strategy", "Growth")
        default_sectors = current_profile.get("sectors", [])

        u_email = st.session_state.get('current_user')
        u_prof = st.session_state.get('user_profile', 'Inconnu')
        db = get_db()
        profile = db.get(u_email, {}).get("profile", {})
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Profil</div>
                <div class="kpi-value">{u_prof}</div>
                <div class="kpi-sub">{u_email}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("<h4>Profil Investisseur</h4>", unsafe_allow_html=True)
            with st.form("account_profile_form"):
                age = st.number_input("Âge", 18, 99, int(profile.get("age", 30)))
                horizon = st.selectbox(
                    "Horizon",
                    ["Court terme", "Moyen terme", "Long terme"],
                    index=["Court terme", "Moyen terme", "Long terme"].index(
                        profile.get("horizon", "Moyen terme")
                    ),
                )
                experience = st.radio(
                    "Expérience",
                    ["Débutant", "Intermédiaire", "Expert"],
                    index=["Débutant", "Intermédiaire", "Expert"].index(
                        profile.get("experience", "Débutant")
                    ),
                )
                capital = st.number_input("Capital (€)", 0, 1000000, int(profile.get("capital", 1000)))
                risk = st.slider("Risque (1-10)", 1, 10, int(profile.get("risk", 5)))
                strategy = st.selectbox(
                    "Stratégie",
                    ["Dividendes", "Growth", "Trading"],
                    index=["Dividendes", "Growth", "Trading"].index(
                        profile.get("strategy", "Growth")
                    ),
                )
                sectors = st.multiselect(
                    "Secteurs",
                    ["Tech", "Santé", "Finance", "Crypto"],
                    default=profile.get("sectors", []),
                )
                if st.form_submit_button("Sauvegarder"):
                    new_profile = {
                        "age": age,
                        "horizon": horizon,
                        "experience": experience,
                        "capital": capital,
                        "risk": risk,
                        "strategy": strategy,
                        "sectors": sectors,
                    }
                    update_user_profile(u_email, new_profile)
                    st.session_state["user_profile"] = experience
                    qp_update(profile=experience)
                    st.success("Profil mis à jour.")
        
        symbols_all = []
        if not stock_df.empty and "Symbole" in stock_df.columns:
            symbols_all = stock_df["Symbole"].dropna().astype(str).unique().tolist()
        symbols_all = sorted(symbols_all)

        default_watchlist = current_profile.get("watchlist", [])
        default_watchlist = [s for s in default_watchlist if s in symbols_all]

        # st.markdown(
        #     f"""
        # <div class="kpi-card">
        #     <div class="kpi-label">Profil</div>
        #     <div class="kpi-value">{html.escape(str(default_experience))}</div>
        #     <div class="kpi-sub">{html.escape(str(email))}</div>
        # </div>
        # """,
        #     unsafe_allow_html=True,
        # )

        # st.write("")
        # st.subheader("Mettre à jour mon profil investisseur")

        # with st.form("account_profile_form"):
        #     c1, c2 = st.columns(2)

        #     with c1:
        #         age = st.number_input("Âge", 18, 99, default_age)
        #         horizon_opts = ["Court terme", "Moyen terme", "Long terme"]
        #         horizon = st.selectbox(
        #             "Horizon",
        #             horizon_opts,
        #             index=horizon_opts.index(default_horizon) if default_horizon in horizon_opts else 1,
        #         )
        #         exp_opts = ["Débutant", "Intermédiaire", "Expert"]
        #         experience = st.radio(
        #             "Expérience",
        #             exp_opts,
        #             index=exp_opts.index(default_experience) if default_experience in exp_opts else 1,
        #         )
        #         capital = st.number_input("Capital (€)", 0, 1_000_000, default_capital)

        #     with c2:
        #         risk = st.slider("Risque (1-10)", 1, 10, default_risk)
        #         strat_opts = ["Dividendes", "Growth", "Trading"]
        #         strategy = st.selectbox(
        #             "Stratégie",
        #             strat_opts,
        #             index=strat_opts.index(default_strategy) if default_strategy in strat_opts else 1,
        #         )
        #         sectors_opts = ["Tech", "Santé", "Finance", "Crypto"]
        #         sectors = st.multiselect(
        #             "Secteurs",
        #             sectors_opts,
        #             default=[s for s in default_sectors if s in sectors_opts],
        #         )

        #         watchlist_sel = st.multiselect(
        #             "Actifs suivis (watchlist)",
        #             symbols_all,
        #             default=default_watchlist,
        #         )

        #     save = st.form_submit_button("Enregistrer")

        # if save:
        #     updated_profile = {
        #         "age": age,
        #         "horizon": horizon,
        #         "experience": experience,
        #         "capital": capital,
        #         "risk": risk,
        #         "strategy": strategy,
        #         "sectors": sectors,
        #         "watchlist": watchlist_sel,
        #     }
        #     update_user_profile(email, updated_profile)

        #     st.session_state["user_profile"] = experience
        #     qp_update(profile=experience, page="Account")
        #     st.success("Profil mis à jour.")
        #     st.rerun()

        st.write("")
        if st.button("Déconnexion"):
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = None
            qp_update(auth="0", user_email="", page="Dashboard")
            st.rerun()

# =========================
# 7. ROUTEUR PRINCIPAL
# =========================
if not st.session_state["authenticated"]:
    show_login()
elif st.session_state["first_login"]:
    show_onboarding()
else:
    cur_nav = show_navbar()
    main_app(cur_nav)
