"""Theil–Sen slopes, 95% CIs, bootstrap and leave-one-year-out ranges for the 2015–2024 July series.

Input: annual means of the archived series (Table 5 of the submitted manuscript) and rerun areas.
Output: results/trend_theilsen_bootstrap.json
No p-values are computed (n = 10).
"""
import json, os
import numpy as np
from scipy.stats import theilslopes

R = os.environ.get('SHADEGAN_WORKDIR', 'work/')
years = np.arange(2015, 2025)
series = {
    'mean_NDVI': [0.090, 0.097, 0.086, 0.084, 0.087, 0.098, 0.103, 0.101, 0.096, 0.092],
    'mean_NDWI': [-0.195, -0.197, -0.183, -0.191, -0.184, -0.192, -0.205, -0.209, -0.192, -0.183],
    'SR_B2': [0.107, 0.102, 0.099, 0.108, 0.098, 0.096, 0.104, 0.110, 0.096, 0.092],
}
# areas from the rerun (results/annual_scenes_and_areas.csv): vegetation NDVI > 0.25, open water NDWI > 0.1
import csv
rows = [r for r in csv.DictReader(open(R + 'results/annual_scenes_and_areas.csv')) if 2015 <= int(r['year']) <= 2024]
series['veg_km2'] = [float(r['veg_ndvi_gt_0p25_km2']) for r in rows]
series['water_km2'] = [float(r['water_ndwi_gt_0p1_km2']) for r in rows]
rng = np.random.default_rng(42)
out = {}
for k, v in series.items():
    y = np.array(v, float)
    s, _, lo, hi = theilslopes(y, years, 0.95)
    boot = []
    for _ in range(5000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(years[i])) > 1:
            boot.append(theilslopes(y[i], years[i])[0])
    loo = [theilslopes(np.delete(y, j), np.delete(years, j))[0] for j in range(len(y))]
    out[k] = {'sen': round(float(s), 6), 'sen_ci': [round(float(lo), 6), round(float(hi), 6)],
              'boot_ci': [round(float(np.percentile(boot, 2.5)), 6), round(float(np.percentile(boot, 97.5)), 6)],
              'loo_range': [round(float(min(loo)), 6), round(float(max(loo)), 6)],
              'sign_stable_loo': bool(np.all(np.sign(loo) == np.sign(s))) if s != 0 else False,
              'ci_includes_zero': bool(lo <= 0 <= hi)}
os.makedirs(R + 'results', exist_ok=True)
json.dump(out, open(R + 'results/trend_theilsen_bootstrap.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
