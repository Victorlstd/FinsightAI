from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from stockpred.config import flatten_tickers, load_configs
from stockpred.data.yahoo import load_raw
from stockpred.features.ta import compute_ta_features
from stockpred.models.predict import load_model_bundle, predict_next_day


def _safe_ticker_dir_name(ticker: str) -> str:
    return ticker.replace("^", "").replace("=", "_").replace("/", "_")


def _build_features(cfg: dict, df_raw: pd.DataFrame) -> pd.DataFrame:
    df_feat = compute_ta_features(df_raw)
    df = df_feat.copy()
    if cfg["model"]["features"].get("dropna", True):
        df.dropna(inplace=True)
    return df


def _horizon_label(h: int) -> str:
    if h == 1:
        return "next_day"
    return f"next_{h}_days"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build multi-horizon prediction JSONs.")
    parser.add_argument("--horizons", type=str, default="1,5,10,30")
    parser.add_argument("--models_root", type=str, default="runs/eval_oral")
    parser.add_argument("--out_dir", type=str, default="reports/predictions")
    parser.add_argument("--tickers", type=str, default="", help="Comma-separated tickers (optional)")
    parser.add_argument("--delete_next_day", action="store_true", help="Remove *_next_day.json after writing multi-horizon file")
    args = parser.parse_args()

    cfg = load_configs()
    horizons = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
    models_root = Path(args.models_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.tickers.strip():
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = sorted(set(flatten_tickers(cfg["tickers"]).values()))

    now = datetime.now().isoformat(timespec="seconds")

    for ticker in tickers:
        df_raw = load_raw(ticker)
        if df_raw.empty:
            print(f"[warn]No cached data for {ticker}. Skipping.")
            continue

        df_feat = _build_features(cfg, df_raw)
        safe = _safe_ticker_dir_name(ticker)
        last_date = df_raw.index.max().date().isoformat()

        payload: dict[str, dict] = {}

        for h in horizons:
            model_dir = models_root / f"h{h}" / "models" / ticker
            if not model_dir.exists():
                print(f"[warn]Missing model for {ticker} at {model_dir}. Skipping h{h}.")
                continue

            bundle = load_model_bundle(model_dir)
            pred = predict_next_day(df_feat, bundle)

            payload[f"h{h}"] = {
                "ticker": ticker,
                "safe_ticker": safe,
                "signal": pred.signal,
                "proba_up": pred.proba_up,
                "proba_down": pred.proba_down,
                "last_date": last_date,
                "generated_at": now,
                "horizon": _horizon_label(h),
            }

        if not payload:
            print(f"[warn]No horizons produced for {ticker}.")
            continue

        out_path = out_dir / f"{safe}_multi_horizon.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[ok]Saved multi-horizon prediction: {out_path}")

        if args.delete_next_day:
            next_day_path = out_dir / f"{safe}_next_day.json"
            if next_day_path.exists():
                next_day_path.unlink()
                print(f"[ok]Deleted legacy file: {next_day_path}")


if __name__ == "__main__":
    main()
