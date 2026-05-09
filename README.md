# A Spatially Explicit Decision Support Framework for Wetland Resilience

## Shadegan Wetland, Iran

> Integrating Random Forest, Google Earth Engine (GEE), and Administrative Boundaries to Guide Restoration (2015–2024)

---

## 📌 Project Overview

This project presents a data-driven, spatially explicit decision-support framework for the restoration of Shadegan Wetland — the largest wetland in Iran and the Middle East (a Ramsar site). Using multi-temporal Landsat 8/9 imagery and ERA5-Land climate data in Google Earth Engine, combined with Random Forest modeling and local expert knowledge (habitat sensitivity + water zoning), we developed an **Optimal Restoration Strategies Map** to prioritize interventions.

**Model Accuracy**: 98.1% (Kappa = 0.971)

---

## 🗺️ Maps

### Optimal Restoration Strategies Map (Main Result)
![Optimal Restoration Strategies Map](Optimal_Restoration_Strategies_Map.png)

### Methodology Workflow
![Methodology Workflow](Methodology_Workflow.png)

### Other Key Maps
![Land Cover Classification](Land_Cover_Classification_Map.png)  
![Hydrological Risk Prioritization](Hydrological_Risk_Prioritization_Map.png)  
![Hydrological Regimes](Hydrological_Regimes_Map.png)

---

## 📊 Key Results

| Class                  | Accuracy | Kappa | Dominant Predictors          |
|------------------------|----------|-------|------------------------------|
| Very High / High       | 98.1%    | 0.971 | Habitat sensitivity          |
| Overall Model          | 98.1%    | 0.971 | Water zoning + sensitivity   |

**Significant decline** in water and vegetation cover + rising turbidity (2015–2024)

---

## 🔑 Key Findings

- Synergistic impact of drought, upstream diversions, and pollution
- Very High and High habitat sensitivity are the strongest spatial predictors
- Clear north-south gradient in degradation
- Model successfully integrates remote sensing with local planning data for actionable zoning

---

## ⚙️ Methodology

All analysis performed in **Google Earth Engine** + **Random Forest / SVM**

### Ecological Indices
- NDVI, NDWI, Turbidity Index (NDTI)

### Weighted Overlay / Model Formula (Random Forest)
```python
Restoration_Priority = f(Habitat_Sensitivity, Water_Zoning, NDVI_trend, NDWI_trend, Turbidity)
