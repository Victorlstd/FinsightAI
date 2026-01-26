from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd


@dataclass
class WindowedDataset:
    X: np.ndarray
    y: np.ndarray
    feature_names: List[str]
    index: pd.DatetimeIndex


def make_windowed_dataset(
    df: pd.DataFrame,
    feature_cols: List[str],
    lookback: int,
    horizon: int = 1,
) -> WindowedDataset:
    if "Close" not in df.columns:
        raise ValueError("df must contain Close")

    x = df[feature_cols].values.astype(np.float32)
    close = df["Close"].values.astype(np.float32)
    idx = df.index

    N = len(df)
    samples = []
    labels = []
    sample_index = []

    for t in range(lookback - 1, N - horizon):
        window = x[t - lookback + 1 : t + 1]
        if not np.isfinite(window).all():
            continue
        y = 1.0 if close[t + horizon] > close[t] else 0.0
        samples.append(window.reshape(-1))
        labels.append(y)
        sample_index.append(idx[t])

    X = np.array(samples, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)
    return WindowedDataset(X=X, y=y, feature_names=feature_cols, index=pd.DatetimeIndex(sample_index))
