"""Loads config/assumptions.toml and config/regions.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


def load_assumptions(path: Path | None = None) -> dict:
    with open(path or CONFIG_DIR / "assumptions.toml", "rb") as f:
        return tomllib.load(f)


def load_regions(path: Path | None = None) -> list[dict]:
    with open(path or CONFIG_DIR / "regions.toml", "rb") as f:
        return tomllib.load(f)["region"]
