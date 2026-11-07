# Reproducibility note (revision, November 2026)

## What can be reproduced from public data

- Every satellite and climate input of the revised analysis can be reproduced: Landsat, JRC, WorldCover, ERA5-Land and SRTM through the Earth Engine scripts in `revision_2026/gee/`.
- The rerun of the archived priority screen (V0) and its corrected versions (V1, V2).
- The annual July series (2015–2026), scene counts, Theil–Sen trends and the precipitation comparison.
- The wetland domain, the revised screen, the Monte Carlo threshold analysis, the scale assessment and the 2025–2026 hold-out test. These use public data only.

## What needs non-public inputs

- The strategy layer and scenarios (S1–S4), because they use the protected-area boundary and the stressor layers (cities, railways) from the 2011 management plan.
- The zone and county summaries.
- The comparison with the habitat-sensitivity map.

These inputs are available on request (see README). With them, `prepare_inputs.py` → `strategy.py` → `sensitivity_map.py` reproduce the reported values. Strategy-class areas may differ by at most about 5 km² because of cell-level rasterization differences.

## Checks performed

- The rerun of the archived script agrees with the four distinct archived exports in 98.80–99.21% of cells.
- Running the Python scripts in this repository on the exports reproduced `results_archived_versions.json`, `results_wetland_domain_screen.json`, `results_holdout_2025_2026.json` and `results_sensitivity_map_comparison.json` exactly.
- Every number in the manuscript was checked against the files in `revision_2026/results/`.

## Evidence levels

Each output is labelled in the manuscript with an evidence level (E1 direct observation, E2 documented satellite indicator, E3 proxy or external product, E4 normative assumption). No output of this repository currently reaches E1, because no field data are available yet. Section 5.4 of the manuscript proposes a field and expert protocol for obtaining such data.
