from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch

from stockpred.config import flatten_tickers, load_configs, save_yaml
from stockpred.data.yahoo import load_raw
from stockpred.features.dataset import make_windowed_dataset
from stockpred.features.ta import compute_ta_features
from stockpred.models.train import train_direction_model
from stockpred.utils.paths import get_paths


def _set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _build_features(cfg_model: dict, df_raw):
    df_feat = compute_ta_features(df_raw)
    df = df_feat.copy()
    if cfg_model["features"].get("dropna", True):
        df.dropna(inplace=True)
    return df


def _get_feature_cols(df):
    drop_cols = {"Adj Close"}
    feature_cols = [c for c in df.columns if c not in drop_cols]
    price_cols = {"Open", "High", "Low", "Close", "Volume"}
    return [c for c in feature_cols if c not in price_cols]


def _split_counts(n: int, valid_ratio: float, test_ratio: float) -> Dict[str, int]:
    n_valid = int(n * valid_ratio)
    n_test = int(n * test_ratio)
    n_train = n - n_valid - n_test
    return {"train": n_train, "valid": n_valid, "test": n_test}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/eval multiple horizons.")
    parser.add_argument("--horizons", type=str, default="1,5,10,30,60")
    parser.add_argument("--out", type=str, default="runs/eval_oral")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    horizons = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
    out_root = Path(args.out)
    cfg = load_configs()
    tickers = sorted(set(flatten_tickers(cfg["tickers"]).values()))

    for h in horizons:
        try:
            _set_seeds(args.seed)
            print(f"\n[info]Training new model from scratch for horizon {h}")

            # Prepare per-horizon config
            model_cfg = cfg["model"].copy()
            model_cfg["features"] = dict(model_cfg["features"])
            model_cfg["features"]["horizon"] = h
            model_cfg["seed"] = args.seed

            out_dir = out_root / f"h{h}"
            models_dir = out_dir / "models"
            out_dir.mkdir(parents=True, exist_ok=True)
            models_dir.mkdir(parents=True, exist_ok=True)

            config_path = out_dir / "model.yaml"
            save_yaml(config_path, model_cfg)

            counts = {"train": 0, "valid": 0, "test": 0}

            for ticker in tickers:
                df_raw = load_raw(ticker)
                if df_raw.empty:
                    print(f"[warn]No cached data for {ticker}. Skipping.")
                    continue

                if len(df_raw) < int(model_cfg["data"]["min_rows"]):
                    print(f"[warn]Not enough rows for {ticker}: {len(df_raw)}. Skipping.")
                    continue

                df_feat = _build_features(model_cfg, df_raw)
                feature_cols = _get_feature_cols(df_feat)

                ds = make_windowed_dataset(
                    df=df_feat,
                    feature_cols=feature_cols,
                    lookback=int(model_cfg["features"]["lookback"]),
                    horizon=int(model_cfg["features"]["horizon"]),
                )

                if len(ds.X) == 0:
                    print(f"[warn]No usable samples for {ticker}. Skipping.")
                    continue

                split_counts = _split_counts(
                    len(ds.X),
                    valid_ratio=float(model_cfg["train"]["valid_ratio"]),
                    test_ratio=0.1,
                )
                counts["train"] += split_counts["train"]
                counts["valid"] += split_counts["valid"]
                counts["test"] += split_counts["test"]

                train_direction_model(
                    ticker=ticker,
                    df_feat=df_feat,
                    feature_cols=feature_cols,
                    lookback=int(model_cfg["features"]["lookback"]),
                    horizon=int(model_cfg["features"]["horizon"]),
                    hidden_sizes=list(model_cfg["model"]["hidden_sizes"]),
                    dropout=float(model_cfg["model"]["dropout"]),
                    epochs=int(model_cfg["train"]["epochs"]),
                    batch_size=int(model_cfg["train"]["batch_size"]),
                    lr=float(model_cfg["train"]["lr"]),
                    weight_decay=float(model_cfg["train"]["weight_decay"]),
                    valid_ratio=float(model_cfg["train"]["valid_ratio"]),
                    early_stop_patience=int(model_cfg["train"]["early_stop_patience"]),
                    out_dir=models_dir,
                    seed=int(model_cfg["seed"]),
                )

            print("\n" + "=" * 60)
            print(f"HORIZON J+{h}")
            print("=" * 60)
            print(
                f"Samples | train={counts['train']} valid={counts['valid']} test={counts['test']}"
            )
        except Exception as exc:
            print(f"[error]Horizon {h} failed: {exc}")
            continue


if __name__ == "__main__":
    main()
