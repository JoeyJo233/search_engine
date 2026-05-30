"""Central configuration: paths, model names, and hyperparameters.

All other modules read from `config.settings` so paths and defaults live in one place.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Project root = two levels up from this file (src/furnsearch/config.py -> project/)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    # --- paths ---
    project_root: Path = _PROJECT_ROOT
    data_dir: Path = field(default=_PROJECT_ROOT / "data")
    raw_dir: Path = field(default=_PROJECT_ROOT / "data" / "raw")
    processed_dir: Path = field(default=_PROJECT_ROOT / "data" / "processed")
    index_dir: Path = field(default=_PROJECT_ROOT / "data" / "index")

    # --- model names ---
    text_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    clip_model: str = "ViT-B-32"

    # --- retrieval/ranking defaults ---
    top_k: int = 50


settings = Settings()
