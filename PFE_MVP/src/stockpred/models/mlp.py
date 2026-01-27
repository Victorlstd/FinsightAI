from __future__ import annotations

from dataclasses import dataclass
from typing import List

import torch
import torch.nn as nn


@dataclass
class MLPConfig:
    input_dim: int
    hidden_sizes: List[int]
    dropout: float = 0.1


class MLPDirection(nn.Module):
    def __init__(self, cfg: MLPConfig):
        super().__init__()
        layers = []
        dim = cfg.input_dim
        for h in cfg.hidden_sizes:
            layers.append(nn.Linear(dim, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(cfg.dropout))
            dim = h
        layers.append(nn.Linear(dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)
