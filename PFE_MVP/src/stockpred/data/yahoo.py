from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from stockpred.utils.paths import get_paths


@dataclass
class YahooFetchParams:
    period: str = "10y"
    interval: str = "1d"
    auto_adjust: bool = False


def fetch_ohlcv(ticker: str, params: YahooFetchParams) -> pd.DataFrame:
    df = yf.download(
        tickers=ticker,
        period=params.period,
        interval=params.interval,
        auto_adjust=params.auto_adjust,
        progress=False,
        group_by="column",
        threads=True,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance can return a 2-level MultiIndex: (Price, Ticker)
        if ticker in df.columns.get_level_values(-1):
            df = df.xs(ticker, axis=1, level=-1, drop_level=True)
        else:
            df.columns = df.columns.droplevel(-1)
    df.columns = [str(c) for c in df.columns]
    keep = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df.columns]
    df = df[keep].copy()

    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]

    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df.dropna(how="all", inplace=True)
    return df


def raw_path_for(ticker: str) -> Path:
    p = get_paths()
    safe = ticker.replace("^", "").replace("=", "_").replace("/", "_")
    return p.data_raw / f"{safe}.csv"


def load_raw(ticker: str) -> pd.DataFrame:
    path = raw_path_for(ticker)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["Date"], index_col="Date")


def save_raw(ticker: str, df: pd.DataFrame) -> Path:
    path = raw_path_for(ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.index.name = "Date"
    out.to_csv(path)
    return path


def fetch_and_cache(ticker: str, period: str, interval: str) -> Optional[Path]:
    df = fetch_ohlcv(ticker, YahooFetchParams(period=period, interval=interval))
    if df.empty:
        return None
    return save_raw(ticker, df)
