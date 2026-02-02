#!/bin/bash

echo "🎯 Test des Filtres pour Gros Crashs"
echo "======================================"
echo ""

echo "📊 Test 1: Anomalies Critical uniquement (1 an)"
echo "------------------------------------------------"
python main.py --step correlate --only-critical --max-anomalies 5
echo ""

echo "📊 Test 2: Variation >= 20% uniquement (1 an)"
echo "-----------------------------------------------"
python main.py --step correlate --min-variation -20 --max-anomalies 5
echo ""

echo "📊 Test 3: Double filtre (Critical + Variation >= 18%)"
echo "--------------------------------------------------------"
python main.py --step correlate --only-critical --min-variation -18 --max-anomalies 5
echo ""

echo "✅ Tests terminés!"
echo "Ouvrez reports/anomaly_report.html pour voir les résultats"
