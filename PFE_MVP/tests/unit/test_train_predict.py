from pathlib import Path

from stockpred.features.ta import compute_ta_features
from stockpred.models.train import train_direction_model
from stockpred.models.predict import load_model_bundle, predict_next_day


def test_train_and_predict_roundtrip(tmp_path: Path, synthetic_ohlcv):
    df_feat = compute_ta_features(synthetic_ohlcv).dropna()
    df = df_feat.dropna()

    price_cols = {"Open", "High", "Low", "Close", "Volume"}
    feature_cols = [c for c in df.columns if c not in price_cols and c != "Adj Close"]
    assert len(feature_cols) > 5

    train_direction_model(
        ticker="TEST",
        df_feat=df,
        feature_cols=feature_cols,
        lookback=30,
        horizon=1,
        hidden_sizes=[64, 32],
        dropout=0.1,
        epochs=3,
        batch_size=128,
        lr=1e-3,
        weight_decay=1e-4,
        valid_ratio=0.2,
        early_stop_patience=2,
        out_dir=tmp_path,
        seed=123,
    )

    bundle = load_model_bundle(tmp_path / "TEST")
    pred = predict_next_day(df, bundle)

    assert 0.0 <= pred.proba_up <= 1.0
    assert 0.0 <= pred.proba_down <= 1.0
    assert abs((pred.proba_up + pred.proba_down) - 1.0) < 1e-6
    assert pred.signal in {"UP", "DOWN", "NEUTRAL"}
