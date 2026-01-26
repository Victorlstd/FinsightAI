import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_ohlcv():
    rng = np.random.default_rng(123)
    n = 600
    idx = pd.bdate_range("2020-01-01", periods=n)

    base = 100 + np.cumsum(rng.normal(0, 1, size=n)) + np.linspace(0, 30, n)
    close = pd.Series(base, index=idx)

    spread = rng.normal(0, 0.8, size=n)
    open_ = close.shift(1).fillna(close.iloc[0]) + spread
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 1.0, size=n))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 1.0, size=n))
    vol = rng.integers(1_000_000, 5_000_000, size=n)

    df = pd.DataFrame(
        {"Open": open_.values, "High": high.values, "Low": low.values, "Close": close.values, "Volume": vol},
        index=idx,
    )
    return df
