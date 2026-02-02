#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


def _ensure_stockpred_installed(root: Path) -> None:
    if importlib.util.find_spec("stockpred") is not None:
        return
    pfe_dir = root / "PFE_MVP"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(pfe_dir)])


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PFE_MVP pipeline (fetch/train/predict + patterns)")
    parser.add_argument("--ticker", help="Yahoo ticker, ex: AAPL")
    parser.add_argument("--all", action="store_true", help="Run for all tickers in configs")
    parser.add_argument("--skip-train", action="store_true", help="Skip training after fetch")
    parser.add_argument("--skip-predict", action="store_true", help="Skip predictions after train")
    parser.add_argument("--tf", default="daily", help="Timeframe: daily/weekly/monthly")
    parser.add_argument("--summary", action="store_true", default=True, help="Print pattern scan summary")
    parser.add_argument("--no-summary", dest="summary", action="store_false", help="Disable pattern scan summary")
    return parser.parse_args()


def main() -> int:
    root = Path(__file__).resolve().parent
    _ensure_stockpred_installed(root)
    args = _parse_args()
    if not args.all and not args.ticker:
        args.all = True
    from stockpred import cli as sp_cli
    sp_cli.run_all(
        ticker=args.ticker,
        all_=args.all,
        skip_train=args.skip_train,
        skip_predict=args.skip_predict,
        tf=args.tf,
        summary=args.summary,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
