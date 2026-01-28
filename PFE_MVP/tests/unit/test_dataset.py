import numpy as np

from stockpred.features.ta import compute_ta_features
from stockpred.features.dataset import make_windowed_dataset


def test_make_windowed_dataset_shapes(synthetic_ohlcv):
    df_feat = compute_ta_features(synthetic_ohlcv).dropna()

    feature_cols = [c for c in df_feat.columns if c.startswith("rsi_") or c.startswith("vol_") or c.startswith("trend_")]
    assert len(feature_cols) >= 2

    lookback = 30
    horizon = 1
    ds = make_windowed_dataset(df_feat, feature_cols=feature_cols, lookback=lookback, horizon=horizon)

    assert ds.X.ndim == 2
    assert ds.y.ndim == 1
    assert ds.X.shape[0] == ds.y.shape[0]
    assert ds.X.shape[1] == lookback * len(feature_cols)

    assert set(np.unique(ds.y)).issubset({0.0, 1.0})