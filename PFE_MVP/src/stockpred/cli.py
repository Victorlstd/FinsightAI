from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from stockpred.config import load_configs, flatten_tickers
from stockpred.data.yahoo import fetch_and_cache, load_raw
from stockpred.features.ta import compute_ta_features
from stockpred.models.train import train_direction_model
from stockpred.models.predict import load_model_bundle, predict_next_day
from stockpred.utils.logging import console
from stockpred.utils.paths import get_paths


def _run_stock_pattern(args: list[str]) -> None:
    import runpy
    sp_init = get_paths().root / "stock-pattern" / "src" / "init.py"
    if not sp_init.exists():
        console.print(f"[err]stock-pattern not found: {sp_init}[/err]")
        return
    sp_src = sp_init.parent
    prev_argv = sys.argv[:]
    prev_sys_path = sys.path[:]
    sys.argv = ["init.py", *args]
    try:
        # Ensure stock-pattern/src is importable for "import utils" etc.
        sys.path.insert(0, str(sp_src))
        runpy.run_path(str(sp_init), run_name="__main__")
    finally:
        sys.argv = prev_argv
        sys.path = prev_sys_path

app = typer.Typer(add_completion=False)


def _ticker_list(cfg: dict) -> list[str]:
    flat = flatten_tickers(cfg["tickers"])
    return sorted(set(flat.values()))


def _safe_ticker_dir_name(ticker: str) -> str:
    return ticker.replace("^", "").replace("=", "_").replace("/", "_")


def _build_features(cfg: dict, df_raw: pd.DataFrame) -> pd.DataFrame:
    df_feat = compute_ta_features(df_raw)
    df = df_feat.copy()

    if cfg["model"]["features"].get("dropna", True):
        df.dropna(inplace=True)

    return df


def _train_one(cfg: dict, ticker: str) -> bool:
    mc = cfg["model"]
    paths = get_paths()

    df_raw = load_raw(ticker)
    if df_raw.empty:
        console.print(f"[warn]No cached data for {ticker}. Run fetch first.[/warn]")
        return False

    if len(df_raw) < mc["data"]["min_rows"]:
        console.print(f"[warn]Not enough rows for {ticker}: {len(df_raw)}[/warn]")
        return False

    df = _build_features(cfg, df_raw)

    drop_cols = {"Adj Close"}
    feature_cols = [c for c in df.columns if c not in drop_cols]

    price_cols = {"Open", "High", "Low", "Close", "Volume"}
    model_features = [c for c in feature_cols if c not in price_cols]

    lookback = int(mc["features"]["lookback"])
    horizon = int(mc["features"]["horizon"])

    train_direction_model(
        ticker=ticker,
        df_feat=df,
        feature_cols=model_features,
        lookback=lookback,
        horizon=horizon,
        hidden_sizes=list(mc["model"]["hidden_sizes"]),
        dropout=float(mc["model"]["dropout"]),
        epochs=int(mc["train"]["epochs"]),
        batch_size=int(mc["train"]["batch_size"]),
        lr=float(mc["train"]["lr"]),
        weight_decay=float(mc["train"]["weight_decay"]),
        valid_ratio=float(mc["train"]["valid_ratio"]),
        early_stop_patience=int(mc["train"]["early_stop_patience"]),
        out_dir=paths.models,
        seed=int(mc["seed"]),
    )

    safe = _safe_ticker_dir_name(ticker)
    outp = paths.data_processed / f"{safe}_features.parquet"
    outp.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(outp)
    console.print(f"[ok]Saved features: {outp}[/ok]")
    return True


def _predict_one(cfg: dict, ticker: str) -> bool:
    paths = get_paths()

    df_raw = load_raw(ticker)
    if df_raw.empty:
        console.print(f"[warn]No cached data for {ticker}. Run fetch first.[/warn]")
        return False

    df = _build_features(cfg, df_raw)

    model_dir = paths.models / ticker
    if not model_dir.exists():
        console.print(f"[warn]No model for {ticker}. Run train first.[/warn]")
        return False

    bundle = load_model_bundle(model_dir)
    pred = predict_next_day(df, bundle)

    console.print(f"[info]{ticker}[/info]")
    console.print(f"[ok]P(UP)={pred.proba_up:.3f} | P(DOWN)={pred.proba_down:.3f} | signal={pred.signal}[/ok]")

    safe = _safe_ticker_dir_name(ticker)
    # Minimal pipeline: prediction is printed only (no plots, no JSON).
    return True


@app.command()
def fetch(
    ticker: Optional[str] = typer.Option(None, help="Yahoo ticker, ex: AAPL"),
    all_: bool = typer.Option(False, "--all", help="Fetch all tickers from configs/tickers.yaml"),
):
    cfg = load_configs()
    period = cfg["model"]["data"]["period"]
    interval = cfg["model"]["data"]["interval"]

    # Fallback in case CLI parsing fails to set --all in some environments
    if not all_ and "--all" in sys.argv:
        all_ = True

    if all_:
        tickers = _ticker_list(cfg)
    elif ticker:
        tickers = [ticker]
    else:
        raise typer.BadParameter("Provide --ticker or --all")

    ok = 0
    for t in tickers:
        path = fetch_and_cache(t, period=period, interval=interval)
        if path is None:
            console.print(f"[warn]No data for {t}[/warn]")
        else:
            console.print(f"[ok]Fetched {t} -> {path}[/ok]")
            ok += 1

    console.print(f"[info]Done. fetched={ok}/{len(tickers)}[/info]")


@app.command()
def train(
    ticker: str = typer.Option(..., help="Yahoo ticker, ex: AAPL"),
):
    cfg = load_configs()
    mc = cfg["model"]
    paths = get_paths()

    df_raw = load_raw(ticker)
    if df_raw.empty:
        raise typer.BadParameter(f"No cached data for {ticker}. Run fetch first.")

    if len(df_raw) < mc["data"]["min_rows"]:
        raise typer.BadParameter(f"Not enough rows for {ticker}: {len(df_raw)}")

    df = _build_features(cfg, df_raw)

    drop_cols = {"Adj Close"}
    feature_cols = [c for c in df.columns if c not in drop_cols]

    price_cols = {"Open", "High", "Low", "Close", "Volume"}
    model_features = [c for c in feature_cols if c not in price_cols]

    lookback = int(mc["features"]["lookback"])
    horizon = int(mc["features"]["horizon"])

    train_direction_model(
        ticker=ticker,
        df_feat=df,
        feature_cols=model_features,
        lookback=lookback,
        horizon=horizon,
        hidden_sizes=list(mc["model"]["hidden_sizes"]),
        dropout=float(mc["model"]["dropout"]),
        epochs=int(mc["train"]["epochs"]),
        batch_size=int(mc["train"]["batch_size"]),
        lr=float(mc["train"]["lr"]),
        weight_decay=float(mc["train"]["weight_decay"]),
        valid_ratio=float(mc["train"]["valid_ratio"]),
        early_stop_patience=int(mc["train"]["early_stop_patience"]),
        out_dir=paths.models,
        seed=int(mc["seed"]),
    )

    safe = _safe_ticker_dir_name(ticker)
    outp = paths.data_processed / f"{safe}_features.parquet"
    outp.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(outp)
    console.print(f"[ok]Saved features: {outp}[/ok]")


@app.command()
def predict(
    ticker: str = typer.Option(..., help="Yahoo ticker, ex: AAPL"),
):
    cfg = load_configs()
    if not _predict_one(cfg, ticker):
        raise typer.BadParameter(f"Prediction failed for {ticker}")


@app.command()
def bootstrap(
    ticker: Optional[str] = typer.Option(None, help="Yahoo ticker, ex: AAPL"),
    all_: bool = typer.Option(False, "--all", "-A", "--all-tickers", help="Run for all tickers from configs/tickers.yaml"),
    skip_train: bool = typer.Option(False, "--skip-train", help="Skip training after fetch"),
    skip_predict: bool = typer.Option(False, "--skip-predict", help="Skip predictions after train"),
):
    cfg = load_configs()
    period = cfg["model"]["data"]["period"]
    interval = cfg["model"]["data"]["interval"]

    # Fallback in case CLI parsing fails to set --all in some environments
    if not all_ and "--all" in sys.argv:
        all_ = True

    if all_:
        tickers = _ticker_list(cfg)
    elif ticker:
        tickers = [ticker]
    else:
        raise typer.BadParameter("Provide --ticker or --all")

    console.print(f"[info]Bootstrap start | tickers={len(tickers)}[/info]")

    fetched = 0
    for t in tickers:
        path = fetch_and_cache(t, period=period, interval=interval)
        if path is None:
            console.print(f"[warn]No data for {t}[/warn]")
        else:
            console.print(f"[ok]Fetched {t} -> {path}[/ok]")
            fetched += 1

    if not skip_train:
        for t in tickers:
            try:
                _train_one(cfg, t)
            except Exception as exc:
                console.print(f"[warn]Train failed for {t}: {exc}[/warn]")

    if not skip_predict:
        for t in tickers:
            try:
                _predict_one(cfg, t)
            except Exception as exc:
                console.print(f"[warn]Predict failed for {t}: {exc}[/warn]")

    console.print(f"[info]Bootstrap done | fetched={fetched}/{len(tickers)}[/info]")


@app.command("scan-patterns")
def scan_patterns(
    tf: str = typer.Option("daily", "--tf", help="Timeframe: daily/weekly/monthly"),
    sym: Optional[list[str]] = typer.Option(None, "--sym", help="Space separated list of symbols"),
    scan_all: bool = typer.Option(True, "--scan-all", help="Scan all patterns"),
    summary: bool = typer.Option(True, "--summary", help="Print summary"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to stock-pattern config"),
):
    cfg = load_configs()
    watchlist_path = get_paths().root / "configs" / "watchlist.txt"
    if sym is None:
        tickers = [_safe_ticker_dir_name(t) for t in _ticker_list(cfg)]
        watchlist_path.write_text("\n".join(tickers) + "\n", encoding="utf-8")
    cfg_path = config or (get_paths().root / "configs" / "stock-pattern.json")
    args: list[str] = ["--tf", tf, "--config", str(cfg_path)]
    if sym:
        args.extend(["--sym", *sym])
    if scan_all:
        args.append("--scan-all")
    if summary:
        args.append("--summary")
    _run_stock_pattern(args)


@app.command("run-all")
def run_all(
    ticker: Optional[str] = typer.Option(None, help="Yahoo ticker, ex: AAPL"),
    all_: bool = typer.Option(False, "--all", help="Run for all tickers from configs/tickers.yaml"),
    skip_train: bool = typer.Option(False, "--skip-train", help="Skip training after fetch"),
    skip_predict: bool = typer.Option(False, "--skip-predict", help="Skip predictions after train"),
    tf: str = typer.Option("daily", "--tf", help="Timeframe: daily/weekly/monthly"),
    summary: bool = typer.Option(True, "--summary", help="Print pattern scan summary"),
):
    bootstrap(ticker=ticker, all_=all_, skip_train=skip_train, skip_predict=skip_predict)
    cfg_path = get_paths().root / "configs" / "stock-pattern.json"
    scan_patterns(tf=tf, sym=None, summary=summary, config=cfg_path)


def main():
    try:
        app()
    except ModuleNotFoundError as e:
        if "stockpred" in str(e):
            console.print("[err]Install with: pip install -e . (from PFE_MVP) then run python -m stockpred.cli ...[/err]")
        raise


if __name__ == "__main__":
    main()
