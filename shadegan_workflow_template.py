"""Transparent template for the Shadegan restoration workflow.

The complete analysis requires Earth Engine assets and local management-plan
layers that are not distributed publicly. This template intentionally avoids
hard-coded personal paths and does not claim one-click reproducibility.

Important methodological note:
The restoration labels are expert/rule-derived from environmental and planning
variables. Random train/test splitting against those labels measures internal
consistency, not independent field validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ee


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path.name}. Copy config.example.json to config.json "
            "and replace the example asset identifiers."
        )
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def initialise_earth_engine(project_id: str) -> None:
    try:
        ee.Initialize(project=project_id)
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine initialisation failed. Authenticate with "
            "`earthengine authenticate` and verify the project ID."
        ) from exc


def load_required_assets(config: dict[str, Any]) -> dict[str, ee.ComputedObject]:
    assets = config["assets"]
    return {
        "aoi": ee.FeatureCollection(assets["aoi"]),
        "restoration_priority": ee.Image(assets["restoration_priority"]).rename(
            "restoration_priority"
        ),
        "land_cover": ee.Image(assets["land_cover_2024"]).rename("land_cover"),
    }


def create_distance_image(
    features: ee.FeatureCollection,
    name: str,
    maximum_distance_m: int = 50_000,
) -> ee.Image:
    painted = ee.Image(0).toByte().paint(features, 1)
    return (
        painted.distance(ee.Kernel.euclidean(maximum_distance_m, "meters"))
        .divide(1000)
        .rename(name)
    )


def build_rule_derived_strategy_labels(
    priority: ee.Image,
    land_cover: ee.Image,
    distance_to_water_km: ee.Image,
    distance_to_stressors_km: ee.Image,
    habitat_sensitivity: ee.Image,
    water_zoning: ee.Image,
) -> ee.Image:
    """Create site-specific expert/rule-derived training labels.

    Class coding:
        0 General Restoration
        1 Re-vegetation
        2 Water Management
        3 Pollution Control
        4 Conservation

    Thresholds below are placeholders mirroring the public workflow structure.
    They must be checked against the manuscript and management-plan definitions
    before execution.
    """
    strategy = ee.Image(0).rename("strategy")
    strategy = strategy.where(
        priority.eq(1)
        .And(distance_to_water_km.lt(2))
        .And(land_cover.neq(0)),
        1,
    )
    strategy = strategy.where(
        priority.eq(1).And(water_zoning.eq(2)).And(land_cover.eq(1)),
        2,
    )
    strategy = strategy.where(
        priority.eq(1).And(distance_to_stressors_km.lt(3)),
        3,
    )
    strategy = strategy.where(
        priority.eq(3).And(habitat_sensitivity.eq(3)),
        4,
    )
    return strategy


def main() -> None:
    config = load_config()
    initialise_earth_engine(config["earth_engine_project"])
    assets = load_required_assets(config)

    print("Earth Engine initialised.")
    print("Required core assets were referenced successfully.")
    print(
        "Next steps require local planning layers for habitat sensitivity, "
        "water zoning, freshwater sources, stressors, and administrative boundaries."
    )
    print(
        "This public template stops before model training to avoid presenting "
        "rule-derived internal validation as independent field validation."
    )


if __name__ == "__main__":
    main()
