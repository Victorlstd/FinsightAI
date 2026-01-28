from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import torch
from safetensors.torch import save_file
from sklearn.preprocessing import StandardScaler

from stockpred.config import save_yaml
from stockpred.features.dataset import make_windowed_dataset
from stockpred.models.mlp import MLPConfig, MLPDirection
from stockpred.utils.logging import console


@dataclass
class TrainArtifacts:
    model_dir: Path
    model_path: Path
    scaler_path: Path
    meta_path: Path


def _train_valid_split(X: np.ndarray, y: np.ndarray, valid_ratio: float) -> Tuple:
    n = len(X)
    n_valid = int(n * valid_ratio)
    n_train = n - n_valid
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train_direction_model(
    ticker: str,
    df_feat: pd.DataFrame,
    feature_cols: List[str],
    lookback: int,
    horizon: int,
    hidden_sizes: List[int],
    dropout: float,
    epochs: int,
    batch_size: int,
    lr: float,
    weight_decay: float,
    valid_ratio: float,
    early_stop_patience: int,
    out_dir: Path,
    seed: int = 42,
) -> TrainArtifacts:
    torch.manual_seed(seed)
    np.random.seed(seed)

    ds = make_windowed_dataset(df_feat, feature_cols, lookback=lookback, horizon=horizon)
    if len(ds.X) < 200:
        raise ValueError(f"Not enough training samples for {ticker}: {len(ds.X)}")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(ds.X)

    X_train, y_train, X_valid, y_valid = _train_valid_split(X_scaled, ds.y, valid_ratio=valid_ratio)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    console.print(f"[info]Training on {device} | samples train={len(X_train)} valid={len(X_valid)}[/info]")

    model = MLPDirection(MLPConfig(input_dim=X_train.shape[1], hidden_sizes=hidden_sizes, dropout=dropout)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    best_val = float("inf")
    best_state = None
    patience = 0

    def batches(X: np.ndarray, y: np.ndarray):
        n = len(X)
        idx = np.arange(n)
        np.random.shuffle(idx)
        for i in range(0, n, batch_size):
            j = idx[i : i + batch_size]
            yield X[j], y[j]

    for ep in range(1, epochs + 1):
        model.train()
        tr_losses = []
        for xb, yb in batches(X_train, y_train):
            xb_t = torch.tensor(xb, dtype=torch.float32, device=device)
            yb_t = torch.tensor(yb, dtype=torch.float32, device=device)

            opt.zero_grad(set_to_none=True)
            logits = model(xb_t)
            loss = loss_fn(logits, yb_t)
            loss.backward()
            opt.step()
            tr_losses.append(loss.item())

        model.eval()
        with torch.no_grad():
            xv = torch.tensor(X_valid, dtype=torch.float32, device=device)
            yv = torch.tensor(y_valid, dtype=torch.float32, device=device)
            val_loss = loss_fn(model(xv), yv).item()

        console.print(f"[dim]epoch {ep:02d} | train={np.mean(tr_losses):.4f} | valid={val_loss:.4f}[/dim]")

        if val_loss < best_val - 1e-4:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= early_stop_patience:
                console.print("[warn]Early stopping[/warn]")
                break

    if best_state is None:
        best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    model_dir = out_dir / ticker
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "model.safetensors"
    save_file(best_state, str(model_path))

    scaler_path = model_dir / "scaler.pkl"
    with scaler_path.open("wb") as f:
        pickle.dump(scaler, f)

    meta = {
        "ticker": ticker,
        "lookback": lookback,
        "horizon": horizon,
        "hidden_sizes": hidden_sizes,
        "dropout": dropout,
        "feature_cols": feature_cols,
        "valid_loss": float(best_val),
        "device_trained": str(device),
    }
    meta_path = model_dir / "meta.yaml"
    save_yaml(meta_path, meta)

    console.print(f"[ok]Saved model: {model_path}[/ok]")
    return TrainArtifacts(model_dir=model_dir, model_path=model_path, scaler_path=scaler_path, meta_path=meta_path)
