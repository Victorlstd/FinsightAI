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

python -m stockpred.cli run-all --all
