from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pandas.tseries.offsets import BDay


@dataclass
class ForecastResult:
    next_date: pd.Timestamp
    last_close: float
    pred_close: float
    ci_low: float
    ci_high: float


_Z_BY_CONFIDENCE = {
    0.90: 1.645,
    0.95: 1.96,
    0.99: 2.576,
}


def _expected_return(
    returns: pd.Series,
    proba_up: float,
    proba_down: float,
) -> float:
    up = returns[returns > 0]
    down = returns[returns < 0]
    if len(up) >= 3 and len(down) >= 3:
        return float(proba_up * up.mean() + proba_down * down.mean())
    return float(returns.mean())


def build_forecast(
    df_raw: pd.DataFrame,
    proba_up: float,
    proba_down: float,
    lookback_days: int = 60,
    confidence: float = 0.95,
) -> ForecastResult:
    if "Close" not in df_raw.columns:
        raise ValueError("Close column missing for forecast")

    closes = df_raw["Close"].dropna()
    if closes.empty:
        raise ValueError("No close prices for forecast")

    returns = closes.pct_change().dropna().tail(lookback_days)
    if returns.empty:
        raise ValueError("Not enough data to build forecast")

    mean_ret = _expected_return(returns, proba_up, proba_down)
    std = float(returns.std(ddof=1))
    if not np.isfinite(std):
        std = 0.0

    last_close = float(closes.iloc[-1])
    z = _Z_BY_CONFIDENCE.get(confidence, _Z_BY_CONFIDENCE[0.95])
    pred_close = last_close * (1.0 + mean_ret)
    ci_low = last_close * (1.0 + mean_ret - z * std)
    ci_high = last_close * (1.0 + mean_ret + z * std)

    ci_low = max(ci_low, 0.0)
    ci_high = max(ci_high, 0.0)

    next_date = closes.index[-1] + BDay(1)
    return ForecastResult(
        next_date=next_date,
        last_close=last_close,
        pred_close=pred_close,
        ci_low=ci_low,
        ci_high=ci_high,
    )


def save_forecast_plot(
    df_raw: pd.DataFrame,
    proba_up: float,
    proba_down: float,
    out_path: Path,
    last_days: int = 15,
    lookback_days: int = 60,
    confidence: float = 0.95,
) -> ForecastResult:
    result = build_forecast(
        df_raw=df_raw,
        proba_up=proba_up,
        proba_down=proba_down,
        lookback_days=lookback_days,
        confidence=confidence,
    )

    if "Close" not in df_raw.columns:
        raise ValueError("Close column missing for plot")

    closes = df_raw["Close"].dropna()
    tail = closes.tail(last_days)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(tail.index, tail.values, color="#0B3C5D", linewidth=2.0, label="Close (last 15 days)")

    ax.plot(
        [tail.index[-1], result.next_date],
        [tail.values[-1], result.pred_close],
        color="#1F8A70",
        linestyle="--",
        linewidth=1.5,
        label="Forecast path",
    )
    ax.scatter([result.next_date], [result.pred_close], color="#1F8A70", s=50, zorder=3, label="Next day forecast")

    yerr = [
        [max(0.0, result.pred_close - result.ci_low)],
        [max(0.0, result.ci_high - result.pred_close)],
    ]
    ax.errorbar(
        [result.next_date],
        [result.pred_close],
        yerr=yerr,
        fmt="none",
        ecolor="#D95F02",
        elinewidth=2.0,
        capsize=6,
        label=f"{int(confidence * 100)}% confidence interval",
        zorder=2,
    )

    ax.set_title("Forecast with Confidence Interval", fontsize=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Close")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    ax.legend(frameon=False, fontsize=9, loc="best")
    fig.autofmt_xdate()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)

    return result
