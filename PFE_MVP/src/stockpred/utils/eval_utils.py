from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class ThresholdReport:
    best_threshold: float
    balanced_acc_at_0_5: float
    balanced_acc_at_best: float
    f1_at_0_5: float
    f1_at_best: float


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def compute_metrics(
    logits: np.ndarray, probs: np.ndarray, y_true: np.ndarray, threshold: float
) -> Dict[str, object]:
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        brier_score_loss,
        confusion_matrix,
        precision_recall_fscore_support,
        roc_auc_score,
    )

    y_pred = (probs >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, pos_label=1, average="binary", zero_division=0
    )
    try:
        roc_auc = roc_auc_score(y_true, probs)
    except ValueError:
        roc_auc = float("nan")
    brier = brier_score_loss(y_true, probs)

    cm = confusion_matrix(y_true, y_pred)

    return {
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "brier": brier,
        "cm": cm,
    }


def optimize_threshold(
    probs: np.ndarray,
    y_true: np.ndarray,
    metric: str = "balanced_accuracy",
    min_thr: float = 0.05,
    max_thr: float = 0.95,
    step: float = 0.01,
) -> ThresholdReport:
    from sklearn.metrics import balanced_accuracy_score, f1_score

    thresholds = np.arange(min_thr, max_thr + 1e-9, step)
    best_thr = 0.5
    best_metric = -np.inf

    for thr in thresholds:
        y_pred = (probs >= thr).astype(int)
        if metric == "f1":
            score = f1_score(y_true, y_pred, zero_division=0)
        else:
            score = balanced_accuracy_score(y_true, y_pred)
        if score > best_metric:
            best_metric = score
            best_thr = float(thr)

    y_pred_05 = (probs >= 0.5).astype(int)
    y_pred_best = (probs >= best_thr).astype(int)

    bal_05 = balanced_accuracy_score(y_true, y_pred_05)
    bal_best = balanced_accuracy_score(y_true, y_pred_best)
    f1_05 = f1_score(y_true, y_pred_05, zero_division=0)
    f1_best = f1_score(y_true, y_pred_best, zero_division=0)

    return ThresholdReport(
        best_threshold=best_thr,
        balanced_acc_at_0_5=float(bal_05),
        balanced_acc_at_best=float(bal_best),
        f1_at_0_5=float(f1_05),
        f1_at_best=float(f1_best),
    )


def expected_calibration_error(
    probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10
) -> Tuple[float, List[Dict[str, float]]]:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(probs, bins) - 1
    bin_ids = np.clip(bin_ids, 0, n_bins - 1)

    ece = 0.0
    table = []
    n = len(probs)

    for b in range(n_bins):
        mask = bin_ids == b
        if not np.any(mask):
            table.append(
                {
                    "bin": b,
                    "count": 0,
                    "mean_proba": float("nan"),
                    "frac_pos": float("nan"),
                }
            )
            continue
        p_bin = probs[mask]
        y_bin = y_true[mask]
        mean_proba = float(p_bin.mean())
        frac_pos = float(y_bin.mean())
        weight = len(p_bin) / n
        ece += weight * abs(mean_proba - frac_pos)
        table.append(
            {
                "bin": b,
                "count": int(len(p_bin)),
                "mean_proba": mean_proba,
                "frac_pos": frac_pos,
            }
        )

    return float(ece), table


def baseline_always_up(y_true: np.ndarray) -> Dict[str, float]:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, brier_score_loss

    y_pred = np.ones_like(y_true)
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    try:
        roc_auc = roc_auc_score(y_true, y_pred)
    except ValueError:
        roc_auc = float("nan")
    brier = brier_score_loss(y_true, y_pred.astype(float))
    return {
        "accuracy": float(acc),
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc_auc),
        "brier": float(brier),
    }


def baseline_random(y_true: np.ndarray, pos_rate: float, seed: int = 42) -> Dict[str, float]:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, brier_score_loss

    rng = np.random.default_rng(seed)
    y_pred = (rng.random(len(y_true)) < pos_rate).astype(int)
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    try:
        roc_auc = roc_auc_score(y_true, y_pred)
    except ValueError:
        roc_auc = float("nan")
    brier = brier_score_loss(y_true, y_pred.astype(float))
    return {
        "accuracy": float(acc),
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc_auc),
        "brier": float(brier),
    }


def baseline_log_reg(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    y_eval: np.ndarray,
) -> Dict[str, float]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, brier_score_loss

    clf = LogisticRegression(max_iter=200, n_jobs=None)
    clf.fit(X_train, y_train)
    probs = clf.predict_proba(X_eval)[:, 1]
    y_pred = (probs >= 0.5).astype(int)
    acc = accuracy_score(y_eval, y_pred)
    bal_acc = balanced_accuracy_score(y_eval, y_pred)
    roc_auc = roc_auc_score(y_eval, probs)
    brier = brier_score_loss(y_eval, probs)
    return {
        "accuracy": float(acc),
        "balanced_accuracy": float(bal_acc),
        "roc_auc": float(roc_auc),
        "brier": float(brier),
    }


def strategy_stats(
    probs: np.ndarray,
    returns_next: np.ndarray,
    threshold: float,
    positioning: str,
) -> Dict[str, float]:
    if positioning == "long_short":
        position = np.where(probs >= threshold, 1.0, -1.0)
    else:
        position = np.where(probs >= threshold, 1.0, 0.0)

    strat_ret = position * returns_next
    equity = (1.0 + strat_ret).cumprod()
    total_ret = float(equity[-1] - 1.0) if len(equity) else 0.0

    if len(equity) > 0:
        ann = float((1.0 + total_ret) ** (252.0 / len(equity)) - 1.0)
    else:
        ann = float("nan")

    roll_max = np.maximum.accumulate(equity)
    drawdown = (equity / roll_max) - 1.0
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0

    return {
        "total_return": total_ret,
        "annualized_return": ann,
        "max_drawdown": max_dd,
        "equity": equity,
    }


def aggregate_equity_curves(
    curves: List[Tuple[pd.DatetimeIndex, np.ndarray]],
    method: str = "union_ffill",
) -> Dict[str, object]:
    if not curves:
        return {
            "method": method,
            "total_return": float("nan"),
            "max_drawdown": float("nan"),
            "series": None,
        }

    series_list = []
    for idx, equity in curves:
        s = pd.Series(equity, index=idx).sort_index()
        series_list.append(s)

    if method == "intersection":
        common = series_list[0].index
        for s in series_list[1:]:
            common = common.intersection(s.index)
        aligned = [s.reindex(common) for s in series_list]
        eq = pd.concat(aligned, axis=1).mean(axis=1)
    else:
        all_idx = series_list[0].index
        for s in series_list[1:]:
            all_idx = all_idx.union(s.index)
        aligned = [s.reindex(all_idx).ffill() for s in series_list]
        eq = pd.concat(aligned, axis=1).mean(axis=1)

    eq = eq.dropna()
    if eq.empty:
        return {
            "method": method,
            "total_return": float("nan"),
            "max_drawdown": float("nan"),
            "series": None,
        }

    total_ret = float(eq.iloc[-1] - 1.0)
    roll_max = eq.cummax()
    drawdown = (eq / roll_max) - 1.0
    max_dd = float(drawdown.min())
    return {
        "method": method,
        "total_return": total_ret,
        "max_drawdown": max_dd,
        "series": eq,
    }
