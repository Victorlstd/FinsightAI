from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import torch
from safetensors.torch import load_file

from stockpred.models.mlp import MLPConfig, MLPDirection


@dataclass
class Prediction:
    proba_up: float
    proba_down: float
    signal: str


def load_model_bundle(model_dir: Path) -> Dict:
    meta_path = model_dir / "meta.yaml"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.yaml in {model_dir}")

    import yaml
    with meta_path.open("r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    scaler_path = model_dir / "scaler.pkl"
    with scaler_path.open("rb") as f:
        scaler = pickle.load(f)

    weights = load_file(str(model_dir / "model.safetensors"))

    input_dim = int(meta["lookback"]) * len(meta["feature_cols"])
    model = MLPDirection(
        MLPConfig(input_dim=input_dim, hidden_sizes=list(meta["hidden_sizes"]), dropout=float(meta["dropout"]))
    )
    model.load_state_dict(weights)
    model.eval()

    return {"meta": meta, "scaler": scaler, "model": model}


def predict_next_day(df_feat: pd.DataFrame, bundle: Dict) -> Prediction:
    meta = bundle["meta"]
    scaler = bundle["scaler"]
    model = bundle["model"]

    lookback = int(meta["lookback"])
    feature_cols = list(meta["feature_cols"])

    if len(df_feat) < lookback + 5:
        raise ValueError("Not enough rows for prediction")

    tail = df_feat[feature_cols].tail(lookback).values.astype(np.float32)
    if not np.isfinite(tail).all():
        raise ValueError("NaN/inf in latest window")

    x = tail.reshape(1, -1)
    x = scaler.transform(x)
    x_t = torch.tensor(x, dtype=torch.float32)

    with torch.no_grad():
        logits = model(x_t).item()
        proba_up = float(torch.sigmoid(torch.tensor(logits)).item())

    proba_down = 1.0 - proba_up
    if proba_up >= 0.55:
        signal = "UP"
    elif proba_up <= 0.45:
        signal = "DOWN"
    else:
        signal = "NEUTRAL"

    return Prediction(proba_up=proba_up, proba_down=proba_down, signal=signal)
