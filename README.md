# Shadegan Wetland Restoration Framework

## Spatially Explicit Decision Support System using Google Earth Engine & Random Forest

> Development of a data-driven framework for wetland restoration prioritization and optimal strategy mapping in Shadegan Wetland, Iran.

---

## 📌 Project Overview

Shadegan Wetland, one of the largest and most important wetlands in Iran, faces significant hydrological and ecological challenges.  

This project develops a **spatially explicit decision support framework** using:
- Google Earth Engine (GEE)
- Multi-temporal Landsat 8/9 imagery
- Random Forest classification (98.1% accuracy, Kappa 0.971)
- Integration of hydrological risk, land cover, and ecological indices (NDVI, NDWI, NDTI)

The final output is a prioritized restoration strategy map to support evidence-based management.

---

## 📊 Key Results

**Model Performance:**
- **Overall Accuracy**: 98.1%
- **Kappa Coefficient**: 0.971

The model provides reliable classification of restoration priority zones and optimal strategies.

---

## 🗺️ Key Visualizations

### Optimal Restoration Strategies Map (Main Result)
![Optimal Restoration Strategies Map](Optimal_Restoration_Strategies_Map.png)

### Methodology Workflow
![Methodology Workflow](Methodology_Workflow.png)

### Land Cover Classification
![Land Cover Classification](Land_Cover_Classification.png)

### Hydrological Risk Prioritization Map
![Hydrological Risk Prioritization](Hydrological_Risk_Prioritization_Map.png)

### Spatio-Temporal Trends
![Spatio-Temporal Vegetation Index](Spatio_Temporal_Distribution_maps_of_Vegetation_index.png)
![Spatio-Temporal Water Body Index](Spatio_Temporal_Distribution_maps_of_waterBody_index.png)
![Spatio-Temporal Turbidity Index](Spatio_Temporal_Distribution_maps_of_Turbidity_index.png)

---

## ⚙️ Methodology Summary

- **Data**: Landsat 8/9 (2015–2024), ERA5-Land climate data, SRTM DEM
- **Indices**: NDVI, NDWI, NDTI
- **Model**: Supervised Random Forest classification
- **Output**: 5-class optimal restoration strategy map (Conservation, Re-vegetation, Water Management, Pollution Control, Full Restoration)

---

## 💻 Code & Scripts

All analysis scripts are available in the [`scripts/`](scripts/) folder.

### 🚀 Live Demo
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sanazshuli/Shadegan-Wetland-Restoration-Framework/blob/main/notebooks/Shadegan_Wetland_Restoration_Demo.ipynb)

**Try the full restoration framework demo directly in Google Colab** 👆

### Main Script:
- **`shadegan_restoration_analysis.py`** → Complete GEE processing, Random Forest training, and strategy map generation

**How to run:**
1. Open the [Demo Notebook](https://colab.research.google.com/github/sanazshuli/Shadegan-Wetland-Restoration-Framework/blob/main/notebooks/Shadegan_Wetland_Restoration_Demo.ipynb)
2. Install dependencies: `pip install -r requirements.txt`
3. Run the script

---

## 📁 Repository Structure

```bash
├── README.md
├── requirements.txt
├── scripts/
│   └── shadegan_restoration_analysis.py
├── notebooks/
│   └── Shadegan_Wetland_Restoration_Demo.ipynb
├── Optimal_Restoration_Strategies_Map.png
├── Methodology_Workflow.png
├── Land_Cover_Classification.png
├── Hydrological_Risk_Prioritization_Map.png
├── Spatio_Temporal_Distribution_maps_of_*.png
├── HoorAlAzim_Digital_Twin_Report.pdf
└── LICENSE
