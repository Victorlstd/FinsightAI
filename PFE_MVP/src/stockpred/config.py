from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from stockpred.utils.paths import get_paths


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False)


def load_configs() -> dict:
    p = get_paths()
    tickers = load_yaml(p.configs / "tickers.yaml")
    model = load_yaml(p.configs / "model.yaml")
    return {"tickers": tickers, "model": model}


def flatten_tickers(tickers_cfg: dict) -> dict:
    out = {}
    for group, mapping in tickers_cfg.items():
        if isinstance(mapping, dict):
            for name, ticker in mapping.items():
                out[name] = ticker
    return out
