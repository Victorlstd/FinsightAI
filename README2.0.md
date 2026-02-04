# FinsightAI – Lancement rapide

## 1. Environnement

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux  |  sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

À la racine du projet, créez un fichier `.env` avec :
```
MISTRAL_API_KEY=votre_cle_mistral
```

## 2. Données et prédictions

```bash
python run_all.py
```

## 3. Dashboard

```bash
python -m streamlit run dashboard.py
```

Ouvrir l’URL affichée (ex. http://localhost:8501).
