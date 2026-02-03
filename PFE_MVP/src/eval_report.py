from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

from stockpred.config import load_configs, load_yaml
from stockpred.data.yahoo import load_raw
from stockpred.features.dataset import make_windowed_dataset
from stockpred.features.ta import compute_ta_features
from stockpred.models.predict import load_model_bundle
from stockpred.utils.paths import get_paths
from stockpred.utils.eval_utils import (
    baseline_always_up,
    baseline_log_reg,
    baseline_random,
    compute_metrics,
    expected_calibration_error,
    optimize_threshold,
    sigmoid,
    strategy_stats,
    aggregate_equity_curves,
)


@dataclass
class EvalSplit:
    name: str
    X: np.ndarray
    y: np.ndarray
    index: pd.DatetimeIndex


def _set_seeds(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)


def _format_date(dt) -> str:
    if hasattr(dt, "date"):
        return dt.date().isoformat()
    return str(dt)


def _format_table(headers: List[str], rows: List[List[object]]) -> str:
    try:
        from tabulate import tabulate

        return tabulate(rows, headers=headers, tablefmt="github")
    except Exception:
        # Manual fallback for aligned columns
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def fmt_row(row_vals: Iterable[object]) -> str:
            return " | ".join(
                str(val).ljust(col_widths[i]) for i, val in enumerate(row_vals)
            )

        lines = [fmt_row(headers), "-+-".join("-" * w for w in col_widths)]
        for row in rows:
            lines.append(fmt_row(row))
        return "\n".join(lines)


def _build_features(cfg_model: dict, df_raw: pd.DataFrame) -> pd.DataFrame:
    df_feat = compute_ta_features(df_raw)
    df = df_feat.copy()
    if cfg_model["features"].get("dropna", True):
        df.dropna(inplace=True)
    return df


def _get_feature_cols(df: pd.DataFrame) -> List[str]:
    drop_cols = {"Adj Close"}
    feature_cols = [c for c in df.columns if c not in drop_cols]
    price_cols = {"Open", "High", "Low", "Close", "Volume"}
    model_features = [c for c in feature_cols if c not in price_cols]
    return model_features


def _split_all(
    X: np.ndarray,
    y: np.ndarray,
    index: pd.DatetimeIndex,
    valid_ratio: float,
    test_ratio: float,
) -> Dict[str, EvalSplit]:
    n = len(X)
    n_valid = int(n * valid_ratio)
    n_test = int(n * test_ratio)
    n_train = n - n_valid - n_test

    if n_train <= 0:
        raise ValueError("Not enough samples for train after applying split ratios.")

    train = EvalSplit(
        name="train",
        X=X[:n_train],
        y=y[:n_train],
        index=index[:n_train],
    )
    valid = EvalSplit(
        name="valid",
        X=X[n_train : n_train + n_valid],
        y=y[n_train : n_train + n_valid],
        index=index[n_train : n_train + n_valid],
    )
    test = EvalSplit(
        name="test",
        X=X[n_train + n_valid :],
        y=y[n_train + n_valid :],
        index=index[n_train + n_valid :],
    )

    return {"train": train, "valid": valid, "test": test}


def _bucket_analysis(
    probs: np.ndarray,
    returns_next: np.ndarray,
    y_true: np.ndarray,
    buckets: int,
) -> List[Dict[str, object]]:
    df = pd.DataFrame(
        {
            "proba": probs,
            "ret_next": returns_next,
            "y": y_true,
        }
    )
    try:
        df["bucket"] = pd.qcut(df["proba"], q=buckets, duplicates="drop")
    except ValueError:
        # fallback to a single bucket if not enough unique values
        df["bucket"] = "all"

    out = []
    for bucket, grp in df.groupby("bucket", sort=True):
        out.append(
            {
                "bucket": str(bucket),
                "n": len(grp),
                "mean_ret": float(grp["ret_next"].mean()) if len(grp) else float("nan"),
                "hit_rate": float(grp["y"].mean()) if len(grp) else float("nan"),
            }
        )
    return out


def _bce_loss(logits: np.ndarray, y_true: np.ndarray) -> float:
    loss_fn = torch.nn.BCEWithLogitsLoss()
    return float(
        loss_fn(
            torch.tensor(logits, dtype=torch.float32),
            torch.tensor(y_true, dtype=torch.float32),
        ).item()
    )




def _plot_outputs(
    out_dir: Path,
    ticker: str,
    dates: pd.DatetimeIndex,
    close: pd.Series,
    probs: np.ndarray,
    returns_next: np.ndarray,
    threshold: float,
    positioning: str,
) -> Dict[str, Path]:
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    safe = ticker.replace("^", "").replace("=", "_").replace("/", "_")

    # Close with markers
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, close.values, linewidth=1.5, color="#1f3b4d")
    buy_idx = probs >= threshold
    sell_idx = probs < threshold
    ax.scatter(dates[buy_idx], close.values[buy_idx], marker="^", color="green", s=30, label="Buy")
    ax.scatter(dates[sell_idx], close.values[sell_idx], marker="v", color="red", s=30, label="Sell")
    ax.set_title(f"{safe} Close with Signals")
    ax.legend(loc="best")
    p1 = out_dir / f"{safe}_close_signals.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=150)
    plt.close(fig)

    # Probabilities over time
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(dates, probs, color="#2a7ab0", linewidth=1.5)
    ax.axhline(threshold, color="#888", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_title(f"{safe} P(UP) over Time")
    p2 = out_dir / f"{safe}_proba_up.png"
    fig.tight_layout()
    fig.savefig(p2, dpi=150)
    plt.close(fig)

    # Equity curve
    if positioning == "long_short":
        position = np.where(probs >= threshold, 1.0, -1.0)
    else:
        position = np.where(probs >= threshold, 1.0, 0.0)
    equity = (1.0 + position * returns_next).cumprod()
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(dates, equity, color="#3a7c3a", linewidth=1.5)
    ax.set_title(f"{safe} Strategy Equity Curve")
    p3 = out_dir / f"{safe}_equity_curve.png"
    fig.tight_layout()
    fig.savefig(p3, dpi=150)
    plt.close(fig)

    return {"close_signals": p1, "proba": p2, "equity": p3}


def _load_model_for_ticker(ticker: str, ckpt: Optional[Path], models_dir: Optional[Path] = None) -> Dict:
    if ckpt is not None:
        model_dir = ckpt.parent
        return load_model_bundle(model_dir)

    if models_dir is not None:
        model_dir = models_dir / ticker
    else:
        paths = get_paths()
        model_dir = paths.models / ticker
    if not model_dir.exists():
        raise FileNotFoundError(f"Missing model directory: {model_dir}")
    return load_model_bundle(model_dir)


def _collect_returns_for_index(
    df_feat: pd.DataFrame, sample_index: pd.DatetimeIndex, horizon: int
) -> np.ndarray:
    close = df_feat["Close"].astype(float)
    ret_next = close.shift(-horizon) / close - 1.0
    aligned = ret_next.loc[sample_index]
    return aligned.values.astype(np.float32)


def _print_section(title: str) -> None:
    line = "=" * len(title)
    print(f"\n{title}\n{line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval report for oral justification.")
    parser.add_argument("--config", type=str, default=None, help="Path to model.yaml")
    parser.add_argument("--tickers_config", type=str, default=None, help="Path to tickers.yaml")
    parser.add_argument("--ticker", type=str, default=None, help="Single ticker (ex: AAPL)")
    parser.add_argument("--all", action="store_true", help="Use all tickers from config")
    parser.add_argument("--split", type=str, default="valid", choices=["valid", "test"])
    parser.add_argument("--test_ratio", type=float, default=0.1, help="Used only for split=test")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--threshold_metric", type=str, default="balanced_accuracy", choices=["balanced_accuracy", "f1"])
    parser.add_argument("--calibration_bins", type=int, default=10)
    parser.add_argument("--bucket", type=int, default=10, help="Deciles=10, Quintiles=5")
    parser.add_argument("--out_dir", type=str, default="runs/eval_oral")
    parser.add_argument("--plots", action="store_true", help="Save plots to out_dir")
    parser.add_argument("--plot_limit", type=int, default=3, help="Max tickers to plot when --all")
    parser.add_argument("--positioning", type=str, default="long_only", choices=["long_only", "long_short"])
    parser.add_argument("--ckpt", type=str, default=None, help="Path to model.safetensors (optional)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json_out", type=str, default="eval_report.json", help="Output JSON file (relative to repo root if not absolute)")
    parser.add_argument("--models_dir", type=str, default=None, help="Override models directory (per-horizon)")
    parser.add_argument("--oral_mode", action="store_true", help="Print detailed diagnostics to terminal")

    args = parser.parse_args()
    _set_seeds(args.seed)

    cfg = load_configs()
    model_cfg = cfg["model"]
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.is_file():
            cfg_path = get_paths().root / cfg_path
        model_cfg = load_yaml(cfg_path)
    tickers_cfg = cfg["tickers"]
    if args.tickers_config:
        tcfg_path = Path(args.tickers_config)
        if not tcfg_path.is_file():
            tcfg_path = get_paths().root / tcfg_path
        tickers_cfg = load_yaml(tcfg_path)

    if args.all:
        from stockpred.config import flatten_tickers

        tickers = sorted(set(flatten_tickers(tickers_cfg).values()))
    elif args.ticker:
        tickers = [args.ticker]
    else:
        raise SystemExit("Provide --ticker or --all.")

    lookback = int(model_cfg["features"]["lookback"])
    horizon = int(model_cfg["features"]["horizon"])
    valid_ratio = float(model_cfg["train"]["valid_ratio"])
    min_rows = int(model_cfg["data"]["min_rows"])

    out_dir = Path(args.out_dir)
    plot_count = 0

    global_logits = []
    global_probs = []
    global_y = []
    per_symbol_scores = []
    equity_curves = []
    per_ticker_returns = []
    results = {
        "config": {
            "split": args.split,
            "threshold": args.threshold,
            "threshold_metric": args.threshold_metric,
            "calibration_bins": args.calibration_bins,
            "bucket": args.bucket,
            "positioning": args.positioning,
            "lookback": lookback,
            "horizon": horizon,
            "valid_ratio": valid_ratio,
            "test_ratio": args.test_ratio,
            "seed": args.seed,
            "models_dir": args.models_dir,
        },
        "tickers": [],
        "global": None,
    }

    for ticker in tickers:
        df_raw = load_raw(ticker)
        if df_raw.empty:
            print(f"[warn]No cached data for {ticker}. Skipping.")
            continue

        if len(df_raw) < min_rows:
            print(f"[warn]Not enough rows for {ticker}: {len(df_raw)}. Skipping.")
            continue

        df_feat = _build_features(model_cfg, df_raw)
        feature_cols = _get_feature_cols(df_feat)

        ds = make_windowed_dataset(
            df=df_feat,
            feature_cols=feature_cols,
            lookback=lookback,
            horizon=horizon,
        )

        if len(ds.X) == 0:
            print(f"[warn]No usable samples for {ticker}. Skipping.")
            continue

        splits = _split_all(
            X=ds.X,
            y=ds.y,
            index=ds.index,
            valid_ratio=valid_ratio,
            test_ratio=args.test_ratio,
        )
        split = splits[args.split]
        train_split = splits["train"]

        models_dir = Path(args.models_dir) if args.models_dir else None
        bundle = _load_model_for_ticker(ticker, Path(args.ckpt) if args.ckpt else None, models_dir=models_dir)
        scaler = bundle["scaler"]
        model = bundle["model"]
        model.eval()

        X_scaled = scaler.transform(split.X)
        x_t = torch.tensor(X_scaled, dtype=torch.float32)
        with torch.no_grad():
            logits = model(x_t).detach().cpu().numpy().reshape(-1)
        probs = sigmoid(logits)

        if len(probs) != len(split.y):
            raise ValueError("Prediction size mismatch with labels.")

        returns_next = _collect_returns_for_index(df_feat, split.index, horizon=horizon)

        metrics = compute_metrics(logits, probs, split.y, args.threshold)
        loss = _bce_loss(logits, split.y)
        metrics["loss"] = loss
        threshold_report = optimize_threshold(
            probs,
            split.y,
            metric=args.threshold_metric,
            min_thr=0.05,
            max_thr=0.95,
            step=0.01,
        )
        ece, reliability = expected_calibration_error(
            probs, split.y, n_bins=args.calibration_bins
        )

        pos_rate_train = float(train_split.y.mean()) if len(train_split.y) else 0.0
        baseline_metrics = {
            "always_up": baseline_always_up(split.y),
            "random_stratified": baseline_random(split.y, pos_rate_train, seed=args.seed),
        }
        scaler_baseline = StandardScaler()
        scaler_baseline.fit(train_split.X)
        X_train_bl = scaler_baseline.transform(train_split.X)
        X_eval_bl = scaler_baseline.transform(split.X)
        baseline_metrics["log_reg"] = baseline_log_reg(
            X_train_bl, train_split.y, X_eval_bl, split.y
        )

        global_logits.append(logits)
        global_probs.append(probs)
        global_y.append(split.y)
        per_symbol_scores.append(
            (ticker, metrics["balanced_accuracy"], metrics["f1"], metrics["roc_auc"])
        )

        pct_above_05 = float((probs >= 0.5).mean()) * 100.0
        pct_above_thr = float((probs >= args.threshold).mean()) * 100.0

        buckets = _bucket_analysis(probs, returns_next, split.y, buckets=args.bucket)
        strat = strategy_stats(probs, returns_next, args.threshold, args.positioning)
        equity_curves.append((split.index, strat["equity"]))
        per_ticker_returns.append(float(strat["total_return"]))

        plot_paths = {}
        if args.plots and plot_count < args.plot_limit:
            close = df_feat["Close"].loc[split.index]
            plot_paths = _plot_outputs(
                out_dir=out_dir / ticker,
                ticker=ticker,
                dates=split.index,
                close=close,
                probs=probs,
                returns_next=returns_next,
                threshold=args.threshold,
                positioning=args.positioning,
            )
            plot_count += 1

        if args.oral_mode:
            _print_section(f"TICKER: {ticker} | SPLIT: {split.name.upper()}")
            print(
                f"Samples: {len(split.y)} | "
                f"Period: {_format_date(split.index.min())} -> {_format_date(split.index.max())}"
            )

            _print_section("METRICS")
            rows = [
                ["BCE Loss", f"{metrics['loss']:.4f}"],
                ["Accuracy", f"{metrics['accuracy']:.4f}"],
                ["Balanced Acc", f"{metrics['balanced_accuracy']:.4f}"],
                ["Precision (class=1)", f"{metrics['precision']:.4f}"],
                ["Recall (class=1)", f"{metrics['recall']:.4f}"],
                ["F1 (class=1)", f"{metrics['f1']:.4f}"],
                ["ROC-AUC", f"{metrics['roc_auc']:.4f}"],
                ["Brier", f"{metrics['brier']:.4f}"],
                ["ECE", f"{ece:.4f}"],
            ]
            print(_format_table(["Metric", "Value"], rows))

            _print_section("THRESHOLD OPTIMIZATION")
            thr_rows = [
                ["Best Threshold", f"{threshold_report.best_threshold:.2f}"],
                ["BalAcc @ 0.5", f"{threshold_report.balanced_acc_at_0_5:.4f}"],
                ["BalAcc @ Best", f"{threshold_report.balanced_acc_at_best:.4f}"],
                ["F1 @ 0.5", f"{threshold_report.f1_at_0_5:.4f}"],
                ["F1 @ Best", f"{threshold_report.f1_at_best:.4f}"],
            ]
            print(_format_table(["Item", "Value"], thr_rows))

            _print_section("BASELINES")
            base_rows = [
                ["Always Up", baseline_metrics["always_up"]["accuracy"], baseline_metrics["always_up"]["balanced_accuracy"], baseline_metrics["always_up"]["roc_auc"], baseline_metrics["always_up"]["brier"]],
                ["Random (strat)", baseline_metrics["random_stratified"]["accuracy"], baseline_metrics["random_stratified"]["balanced_accuracy"], baseline_metrics["random_stratified"]["roc_auc"], baseline_metrics["random_stratified"]["brier"]],
                ["LogReg", baseline_metrics["log_reg"]["accuracy"], baseline_metrics["log_reg"]["balanced_accuracy"], baseline_metrics["log_reg"]["roc_auc"], baseline_metrics["log_reg"]["brier"]],
            ]
            print(_format_table(["Baseline", "Accuracy", "BalAcc", "ROC-AUC", "Brier"], base_rows))

            _print_section(f"STRATEGY ({args.positioning.upper()})")
            strat_rows = [
                ["Total Return", f"{strat['total_return']:.4f}"],
                ["Annualized Return", f"{strat['annualized_return']:.4f}"],
                ["Max Drawdown", f"{strat['max_drawdown']:.4f}"],
            ]
            print(_format_table(["Item", "Value"], strat_rows))

        results["tickers"].append(
            {
                "ticker": ticker,
                "split": split.name,
                "samples": int(len(split.y)),
                "period": {
                    "start": _format_date(split.index.min()),
                    "end": _format_date(split.index.max()),
                },
                "metrics": {
                    "bce_loss": float(metrics["loss"]),
                    "accuracy": float(metrics["accuracy"]),
                    "balanced_accuracy": float(metrics["balanced_accuracy"]),
                    "precision_pos1": float(metrics["precision"]),
                    "recall_pos1": float(metrics["recall"]),
                    "f1_pos1": float(metrics["f1"]),
                    "roc_auc": float(metrics["roc_auc"]),
                    "brier": float(metrics["brier"]),
                },
                "threshold_optimization": {
                    "best_threshold": threshold_report.best_threshold,
                    "balanced_acc_at_0_5": threshold_report.balanced_acc_at_0_5,
                    "balanced_acc_at_best": threshold_report.balanced_acc_at_best,
                    "f1_at_0_5": threshold_report.f1_at_0_5,
                    "f1_at_best": threshold_report.f1_at_best,
                },
                "calibration": {
                    "ece": float(ece),
                    "reliability_table": reliability,
                },
                "baselines": baseline_metrics,
                "confusion_matrix": {
                    "tn": int(metrics["cm"][0, 0]),
                    "fp": int(metrics["cm"][0, 1]),
                    "fn": int(metrics["cm"][1, 0]),
                    "tp": int(metrics["cm"][1, 1]),
                },
                "proba_stats": {
                    "min": float(probs.min()),
                    "mean": float(probs.mean()),
                    "max": float(probs.max()),
                    "pct_ge_0_5": float(pct_above_05),
                    "pct_ge_threshold": float(pct_above_thr),
                },
                "bucket_analysis": buckets,
                "strategy": {
                    "total_return": float(strat["total_return"]),
                    "annualized_return": float(strat["annualized_return"]),
                    "max_drawdown": float(strat["max_drawdown"]),
                },
                "plots": {k: str(v) for k, v in plot_paths.items()},
            }
        )

    if len(global_y) > 1:
        g_logits = np.concatenate(global_logits)
        g_probs = np.concatenate(global_probs)
        g_y = np.concatenate(global_y)
        g_metrics = compute_metrics(g_logits, g_probs, g_y, args.threshold)
        g_loss = _bce_loss(g_logits, g_y)
        g_metrics["loss"] = g_loss

        per_symbol_scores_sorted = sorted(
            per_symbol_scores, key=lambda x: (x[1], x[2]), reverse=True
        )
        best = per_symbol_scores_sorted[:5]
        worst = list(reversed(per_symbol_scores_sorted[-5:]))

        mean_ret = float(np.mean(per_ticker_returns)) if per_ticker_returns else float("nan")
        median_ret = float(np.median(per_ticker_returns)) if per_ticker_returns else float("nan")
        pct_positive = (
            float(np.mean([r > 0 for r in per_ticker_returns])) * 100.0
            if per_ticker_returns
            else float("nan")
        )
        agg = aggregate_equity_curves(equity_curves, method="union_ffill")

        results["global"] = {
            "metrics": {
                "bce_loss": float(g_metrics["loss"]),
                "accuracy": float(g_metrics["accuracy"]),
                "balanced_accuracy": float(g_metrics["balanced_accuracy"]),
                "precision_pos1": float(g_metrics["precision"]),
                "recall_pos1": float(g_metrics["recall"]),
                "f1_pos1": float(g_metrics["f1"]),
                "roc_auc": float(g_metrics["roc_auc"]),
                "brier": float(g_metrics["brier"]),
            },
            "strategy": {
                "total_return": float(agg["total_return"]),
                "annualized_return": float("nan"),
                "max_drawdown": float(agg["max_drawdown"]),
            },
            "strategy_aggregation": {
                "mean_return": mean_ret,
                "median_return": median_ret,
                "pct_positive": pct_positive,
                "portfolio_equal_weight_total_return": float(agg["total_return"]),
                "portfolio_equal_weight_max_drawdown": float(agg["max_drawdown"]),
                "method": agg["method"],
            },
            "top_5": [
                {"ticker": t, "balanced_accuracy": float(bal), "f1": float(f1), "roc_auc": float(auc)}
                for t, bal, f1, auc in best
            ],
            "bottom_5": [
                {"ticker": t, "balanced_accuracy": float(bal), "f1": float(f1), "roc_auc": float(auc)}
                for t, bal, f1, auc in worst
            ],
        }

        if args.oral_mode:
            _print_section("GLOBAL STRATEGY AGGREGATION")
            agg_rows = [
                ["Mean Return", f"{mean_ret:.4f}"],
                ["Median Return", f"{median_ret:.4f}"],
                ["% Positive Tickers", f"{pct_positive:.2f}%"],
                ["EQ-Weight Total Return", f"{agg['total_return']:.4f}"],
                ["EQ-Weight Max DD", f"{agg['max_drawdown']:.4f}"],
                ["Aggregation Method", str(agg["method"])],
            ]
            print(_format_table(["Item", "Value"], agg_rows))

    json_path = Path(args.json_out)
    if not json_path.is_absolute():
        json_path = get_paths().root / json_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json

    json_path.write_text(_json.dumps(results, indent=2), encoding="utf-8")
    print(f"[ok]Wrote JSON report: {json_path}")


if __name__ == "__main__":
    main()
