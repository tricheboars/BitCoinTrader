"""Asset and news catalogue loaders."""
from __future__ import annotations

from pathlib import Path

import yaml

from bitcointrader.market.model import Asset, NewsEvent

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_assets() -> dict[str, Asset]:
    assets: dict[str, Asset] = {}
    asset_dir = DATA_DIR / "assets"
    for path in sorted(asset_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        asset = Asset(**data)
        assets[asset.ticker] = asset
    return assets


def load_news() -> list[NewsEvent]:
    path = DATA_DIR / "news" / "events.yaml"
    data = yaml.safe_load(path.read_text())
    return [NewsEvent(**e) for e in data["events"]]
