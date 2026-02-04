#!/usr/bin/env python3
"""
Script pour mettre à jour les données du jour (prix, puis optionnellement prédictions et patterns).
À lancer depuis la racine du projet : python update_daily_data.py

- Télécharge les derniers cours (PFE_MVP/data/raw/*.csv) via yfinance.
- Optionnel : entraîne les modèles, prédit, scanne les patterns (décommenter ou utiliser --full).
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Mise à jour des données pour le dashboard FinsightAI")
    parser.add_argument("--full", action="store_true", help="Fetch + train + predict + scan patterns (équivalent run_all.py --all)")
    args = parser.parse_args()

    if args.full:
        # Tout le pipeline
        cmd = [sys.executable, str(root / "run_all.py"), "--all"]
        print("Lancement du pipeline complet (fetch + train + predict + patterns)...")
    else:
        # Seulement fetch des prix (données du jour)
        cmd = [sys.executable, "-m", "stockpred.cli", "fetch", "--all"]
        print("Mise à jour des cours (fetch --all)...")
        # S'assurer que stockpred est importable depuis la racine
        pfe_mvp = root / "PFE_MVP"
        if (pfe_mvp / "pyproject.toml").exists():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(pfe_mvp)], cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                pass

    try:
        subprocess.check_call(cmd, cwd=str(root))
        print("Terminé.")
    except FileNotFoundError:
        print("Erreur: stockpred non trouvé. Depuis la racine du projet, exécutez:")
        print("  cd PFE_MVP && pip install -e . && cd ..")
        print("Puis relancez: python update_daily_data.py")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
