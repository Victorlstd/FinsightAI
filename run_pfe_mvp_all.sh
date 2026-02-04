#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PFE_DIR="${ROOT_DIR}/PFE_MVP"

if python - <<'PY'
import importlib.util
import sys
spec = importlib.util.find_spec("stockpred")
sys.exit(0 if spec is not None else 1)
PY
then
  :
else
  python -m pip install -e "${PFE_DIR}"
fi

python -m stockpred.cli fetch --all
python PFE_MVP/scripts/run_multihorizon.py --horizons 1,5,10,30 --out PFE_MVP/runs/eval_oral --seed 42
python PFE_MVP/scripts/predict_multi_horizon.py --horizons 1,5,10,30 --models_root PFE_MVP/runs/eval_oral --out_dir PFE_MVP/reports/predictions --delete_next_day
python -m stockpred.cli scan-patterns --tf daily --summary
