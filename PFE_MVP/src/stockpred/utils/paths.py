from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def configs(self) -> Path:
        return self.root / "configs"

    @property
    def data_raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def reports(self) -> Path:
        return self.root / "reports"


def get_paths() -> ProjectPaths:
    # src/stockpred/utils/paths.py -> root = stock-mvp
    root = Path(__file__).resolve().parents[3]
    return ProjectPaths(root=root)
