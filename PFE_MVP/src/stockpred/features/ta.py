from __future__ import annotations

import numpy as np
import pandas as pd

from ta.volatility import AverageTrueRange, BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volume import OnBalanceVolumeIndicator


def compute_ta_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: OHLCV indexed by date, columns: Open High Low Close Volume
    Output: dataframe with engineered features, aligned on same index
    """
    x = df.copy()

    x["ret_1"] = x["Close"].pct_change(1)
    x["logret_1"] = np.log(x["Close"]).diff(1)

    x["vol_10"] = x["logret_1"].rolling(10).std()
    x["vol_20"] = x["logret_1"].rolling(20).std()

    # ATR
    atr = AverageTrueRange(high=x["High"], low=x["Low"], close=x["Close"], window=14)
    x["atr_14"] = atr.average_true_range()

    # RSI
    rsi = RSIIndicator(close=x["Close"], window=14)
    x["rsi_14"] = rsi.rsi()

    # MACD
    macd = MACD(close=x["Close"], window_slow=26, window_fast=12, window_sign=9)
    x["macd"] = macd.macd()
    x["macd_signal"] = macd.macd_signal()
    x["macd_diff"] = macd.macd_diff()

    # Bollinger Bands
    bb = BollingerBands(close=x["Close"], window=20, window_dev=2)
    x["bb_mavg"] = bb.bollinger_mavg()
    x["bb_hband"] = bb.bollinger_hband()
    x["bb_lband"] = bb.bollinger_lband()
    x["bb_pband"] = bb.bollinger_pband()
    x["bb_wband"] = bb.bollinger_wband()

    # Stochastic
    st = StochasticOscillator(high=x["High"], low=x["Low"], close=x["Close"], window=14, smooth_window=3)
    x["stoch_k"] = st.stoch()
    x["stoch_d"] = st.stoch_signal()

    # OBV
    obv = OnBalanceVolumeIndicator(close=x["Close"], volume=x["Volume"])
    x["obv"] = obv.on_balance_volume()

    # SMA/EMA
    x["sma_20"] = SMAIndicator(close=x["Close"], window=20).sma_indicator()
    x["sma_50"] = SMAIndicator(close=x["Close"], window=50).sma_indicator()
    x["ema_20"] = EMAIndicator(close=x["Close"], window=20).ema_indicator()
    x["ema_50"] = EMAIndicator(close=x["Close"], window=50).ema_indicator()

    x["trend_sma_20_50"] = (x["sma_20"] - x["sma_50"]) / (x["atr_14"] + 1e-9)

    x.replace([np.inf, -np.inf], np.nan, inplace=True)
    return x
