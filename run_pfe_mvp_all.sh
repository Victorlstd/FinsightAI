#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PFE_DIR="${ROOT_DIR}/PFE_MVP"
export PYTHONPATH="${PFE_DIR}/src:${PYTHONPATH:-}"

PFE_DIR="${PFE_DIR}" python - <<'PY'
import importlib.util
import os
import sys
from pathlib import Path

pfe_dir = Path(os.environ["PFE_DIR"]).resolve()
spec = importlib.util.find_spec("stockpred")
if spec is None or spec.origin is None:
    sys.exit(1)
try:
    origin = Path(spec.origin).resolve()
    sys.exit(0 if str(pfe_dir) in str(origin) else 1)
except Exception:
    sys.exit(1)
PY
if [ $? -ne 0 ]; then
  python -m pip install -e "${PFE_DIR}"
fi

python -m stockpred.cli fetch --all
python PFE_MVP/scripts/run_multihorizon.py --horizons 1,5,10,30 --out PFE_MVP/runs/eval_oral --seed 42
python PFE_MVP/scripts/predict_multi_horizon.py --horizons 1,5,10,30 --models_root PFE_MVP/runs/eval_oral --out_dir PFE_MVP/reports/predictions --delete_next_day
python - <<'PY'
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
pfe_dir = root / "PFE_MVP"
sys.path.insert(0, str(pfe_dir / "src"))
from stockpred import cli as sp_cli

cfg_path = pfe_dir / "configs" / "stock-pattern.json"
sp_cli.scan_patterns(tf="daily", sym=None, summary=True, config=cfg_path)
PY
