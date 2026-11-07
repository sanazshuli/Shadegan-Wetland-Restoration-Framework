# Shadegan Wetland Restoration Framework

**Audit, rebuild and test of a satellite-based restoration screen for Shadegan Wetland, Iran**

This repository accompanies the manuscript *"Auditing and rebuilding a satellite-based restoration screen for Shadegan Wetland, Iran: reproducibility, uncertainty and conditional management scenarios"* (Shuli & Sharghi, under revision at *Wetlands*, manuscript WELA-D-26-00390).

It contains two parts:

| Folder | Content |
|---|---|
| [`revision_2026/`](revision_2026) | **Current analysis.** Earth Engine scripts, Python code, result tables and figures of the revised manuscript (November 2026). |
| [`archive_2025_submission/`](archive_2025_submission) and the files in the repository root (`scripts/`, `notebooks/`, `data/`, `*.png`) | **Archived workflow** of the original submission (2025). Kept unchanged so that the audit can be checked. See the corrections listed below before using any of it. |

## Corrections to the archived workflow

The revision recovered and reran the archived Earth Engine code ([`archive_2025_submission/Codes_project_Shadegan_archived_2025.ipynb`](archive_2025_submission)). The audit established that:

- The land-cover classifier used the official ESA WorldCover codes (80 water, 90 herbaceous wetland, 40 cropland, 50 built-up). The wrong codes (10, 70 and 100) occur only in the **priority rules**. Correcting them changes 2.0% of cells.
- The NDVI/NDWI clause of the priority rules was written in the inverted direction. Writing it as intended raises the High class from 45% to 86% of the study area.
- The NDVI-trend transformation is recoverable: inverted min–max scaling over the study area (`revision_2026/results/normalization_minmax.csv`). The High clause corresponds to a raw slope below 3.4 × 10⁻⁴ yr⁻¹.
- **Only a Random Forest** was used for land cover. The statement in the earlier README and manuscript that RF and SVM were compared was an error.
- The strategy class "General Restoration" had no training samples. The reported 98.1% accuracy (Kappa 0.971) measures agreement with rule-derived labels and is not evidence of ecological accuracy. The revised analysis therefore maps the rules directly and does not use a classifier.

## Revised workflow (`revision_2026/`)

```text
revision_2026/
├── gee/                                   Google Earth Engine Code Editor scripts (JavaScript)
│   ├── 01_rerun_archived_versions_V0_V2.js     rerun of the archived screen: V0 archived, V1 WorldCover fixed, V2 direction fixed
│   ├── 02_wetland_domain_inputs.js             WorldCover/JRC fractions and annual July NDVI, NDWI, SR_B2 (2015–2024)
│   └── 03_holdout_2025_2026_and_ERA5.js         hold-out years 2025–2026, scene counts, ERA5-Land precipitation
├── python/
│   ├── prepare_inputs.py      exports and shapefiles -> arrays on the 250-m grid; sugarcane drainage-source proxy
│   ├── analyse_versions.py    reproduction test against the archived exports; effect of each correction
│   ├── trends.py              Theil–Sen slopes, bootstrap and leave-one-year-out ranges (no p-values)
│   ├── domain_screen.py       wetland domain, revised screen, Monte Carlo threshold analysis (500 draws), scale
│   ├── holdout.py             persistence of the screen in 2025 and 2026
│   ├── strategy.py            decision-tree strategy layer and scenarios S1–S4
│   ├── sensitivity_map.py     digitization of the management-plan habitat-sensitivity map and cross-tabulation
│   ├── figures.py             journal figures (PDF, 600-dpi TIFF, PNG)
│   └── shpread.py, tiffread.py, tiffread2.py   readers and projections (no GDAL needed)
├── results/                   all numbers reported in the manuscript (CSV / JSON)
├── figures/                   manuscript figures (PDF and PNG)
└── data/Shadegan_AOI_from_export.geojson   study-area polygon (250-m grid footprint)
```

### Run order

1. In the [Earth Engine Code Editor](https://code.earthengine.google.com), run the three scripts in `gee/` and start the export tasks. Exports go to the Google Drive folder `Shadegan_revision_2026`.
2. Put the exported GeoTIFFs in a working folder, for example `work/`. Put the management-plan shapefiles in `work/shapefiles/` and the five archived exports in `work/archived_exports/`.
3. Run:

```bash
pip install -r requirements.txt
export SHADEGAN_WORKDIR=work/
python revision_2026/python/prepare_inputs.py
python revision_2026/python/analyse_versions.py
python revision_2026/python/trends.py
python revision_2026/python/domain_screen.py
python revision_2026/python/holdout.py
python revision_2026/python/strategy.py
python revision_2026/python/sensitivity_map.py work/p-45.png   # page image of the plan's Appendix 2, 300 dpi
python revision_2026/python/figures.py
```

`results/` is written into the working folder. Running the scripts on the exports used for the manuscript reproduces the files in `revision_2026/results/` exactly, with one exception. Rasterizing the shapefiles in `prepare_inputs.py` can differ by single cells from the rasters used for the manuscript, which shifts strategy-class areas by at most about 5 km² (0.2% of the wetland domain).

### Software

Python ≥ 3.10 with `numpy`, `scipy`, `pandas`, `matplotlib`, `tifffile` and `pillow` (see `requirements.txt`). The analysis was run with Python 3.13, numpy 2, scipy 1.18 and matplotlib 3.10. No GIS library is required. A Google Earth Engine account is needed only for step 1.

## Data availability

| Data | Availability |
|---|---|
| Landsat 8/9 C2 L2, JRC Global Surface Water v1.4, ESA WorldCover v100, ERA5-Land monthly aggregates, SRTM | Public, through Google Earth Engine; accessed by the scripts in `gee/` |
| Result tables and figures | This repository (`revision_2026/results`, `revision_2026/figures`) |
| Study-area polygon | This repository (`revision_2026/data`) |
| Planning layers digitized from the 2011 Shadegan Wetland integrated management plan (sub-basin, protected area, hydrological zones, rivers, railways, cities, counties) and the digitized habitat-sensitivity map | Not redistributed (source restrictions). Available from the corresponding author on reasonable request, with permission of the Khuzestan Department of Environment. The scripts document exactly how they were used. |
| Archived priority exports (five GeoTIFFs, 2025) | Available from the corresponding author |

Contact: Sanaz Shuli — sanazshuli@gmail.com

## Citation

See [`CITATION.cff`](CITATION.cff). Please cite the article once it is published.
