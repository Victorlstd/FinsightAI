#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _ensure_stockpred_installed(root: Path) -> None:
    if importlib.util.find_spec("stockpred") is not None:
        return
    pfe_dir = root / "PFE_MVP"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(pfe_dir)])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run PFE_MVP pipeline (fetch + multi-horizon + predictions + patterns)"
    )
    parser.add_argument("--horizons", default="1,5,10,30", help="Comma-separated horizons, ex: 1,5,10,30")
    parser.add_argument("--tf", default="daily", help="Timeframe: daily/weekly/monthly")
    parser.add_argument("--summary", action="store_true", default=True, help="Print pattern scan summary")
    parser.add_argument("--no-summary", dest="summary", action="store_false", help="Disable pattern scan summary")
    return parser.parse_args()


def main() -> int:
    root = Path(__file__).resolve().parent
    _ensure_stockpred_installed(root)
    args = _parse_args()
    pfe_dir = root / "PFE_MVP"

    env = dict(**os.environ)
    src_path = str((pfe_dir / "src").resolve())
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH','')}"

    sys.path.insert(0, src_path)
    from stockpred import cli as sp_cli
    sp_cli.fetch(ticker=None, all_=True)
    subprocess.check_call(
        [
            sys.executable,
            str(pfe_dir / "scripts" / "run_multihorizon.py"),
            "--horizons",
            args.horizons,
            "--out",
            str(pfe_dir / "runs" / "eval_oral"),
            "--seed",
            "42",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            sys.executable,
            str(pfe_dir / "scripts" / "predict_multi_horizon.py"),
            "--horizons",
            args.horizons,
            "--models_root",
            str(pfe_dir / "runs" / "eval_oral"),
            "--out_dir",
            str(pfe_dir / "reports" / "predictions"),
            "--delete_next_day",
        ],
        env=env,
    )
    cfg_path = pfe_dir / "configs" / "stock-pattern.json"
    sp_cli.scan_patterns(tf=args.tf, sym=None, summary=args.summary, config=cfg_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
