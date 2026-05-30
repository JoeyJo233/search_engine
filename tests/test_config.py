"""Phase 0 sanity: the package imports and config exposes the expected paths."""
from pathlib import Path

import furnsearch
from furnsearch import config


def test_package_importable():
    assert furnsearch is not None


def test_data_paths_are_under_project_root():
    cfg = config.settings
    # All data paths live inside the project's data/ directory.
    assert cfg.data_dir == cfg.project_root / "data"
    assert cfg.raw_dir == cfg.data_dir / "raw"
    assert cfg.processed_dir == cfg.data_dir / "processed"
    assert cfg.index_dir == cfg.data_dir / "index"


def test_paths_are_path_objects():
    cfg = config.settings
    for p in (cfg.project_root, cfg.data_dir, cfg.raw_dir,
              cfg.processed_dir, cfg.index_dir):
        assert isinstance(p, Path)


def test_default_model_names_present():
    cfg = config.settings
    assert cfg.text_model  # sentence-transformers model id
    assert cfg.clip_model   # open_clip model id
