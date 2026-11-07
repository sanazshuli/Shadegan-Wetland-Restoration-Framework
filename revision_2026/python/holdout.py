import os
WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')  # folder holding the exported rasters and intermediate files
import numpy as np, json
R = WD
o = np.load(R + 'domain_outputs.npz'); dom = o['dom']; base = o['base']; prob = o['prob']
D = np.load(R + 'domain.npy'); dn = open(R + 'domain_bands.txt').read().split('\n'); b = {k: D[..., i] for i, k in enumerate(dn)}
Hh = np.load(R + 'holdout.npy'); hn = open(R + 'holdout_bands.txt').read().split('\n'); h = {k: Hh[..., i] for i, k in enumerate(hn)}
occ, fw, ts, nmed = o['occ'], o['f_water'], o['ts'], o['ndvi_med']
lost = dom & (occ >= 25) & (fw <= 0.2)                       # High: hydrological loss clause
vegdec = dom & (nmed >= 0.2) & (ts <= -0.005)
stable_w = dom & (fw >= 0.8)
res = {}
for y in (2025, 2026):
    for tag in ('', '89'):
        wet = h[f'NDWI{tag}_{y}'] > 0; ndvi = h[f'NDVI{tag}_{y}']
        k = f'{y}{"_L8L9" if tag else "_L8"}'
        res[k] = {
            'High_lost_water_still_dry_pct': round(100 * float((~wet[lost]).mean()), 1),
            'Low_stable_water_still_wet_pct': round(100 * float(wet[stable_w].mean()), 1),
            'Medium_wet_pct': round(100 * float(wet[dom & (base == 2)].mean()), 1),
            'domain_wet_pct': round(100 * float(wet[dom].mean()), 1),
            'High_robust_P80_still_dry_pct': round(100 * float((~wet[dom & (prob[0] >= .8)]).mean()), 1),
            'veg_decline_cells_NDVI_below_their_2015_2024_median_pct': round(100 * float((ndvi[vegdec] < nmed[vegdec]).mean()), 1),
        }
# baseline expectation: share of lost-water cells dry in an average 2015-2024 July
NDWI = np.stack([b[f'NDWI_{y}'] for y in range(2015, 2025)])
res['2015_2024_mean_High_lost_dry_pct'] = round(100 * float((NDWI[:, lost] <= 0).mean()), 1)
res['2015_2024_mean_Low_stable_wet_pct'] = round(100 * float((NDWI[:, stable_w] > 0).mean()), 1)
# does extending the window to 2015-2026 change the screen?
NDWI12 = np.concatenate([NDWI, np.stack([h['NDWI_2025'], h['NDWI_2026']])])
NDVI12 = np.concatenate([np.stack([b[f'NDVI_{y}'] for y in range(2015, 2025)]), np.stack([h['NDVI_2025'], h['NDVI_2026']])])
fw12 = (NDWI12 > 0).mean(0); nmed12 = np.nanmedian(NDVI12, 0)
t = np.arange(2015, 2027, dtype=float); pairs = [(i, j) for i in range(12) for j in range(i + 1, 12)]
ts12 = np.nanmedian(np.stack([(NDVI12[j] - NDVI12[i]) / (t[j] - t[i]) for i, j in pairs]), 0)
veg12 = nmed12 >= 0.2
high12 = ((occ >= 25) & (fw12 <= 0.2)) | (veg12 & (ts12 <= -0.005)); low12 = (fw12 >= 0.8) | (veg12 & (ts12 >= 0))
s12 = np.where(high12, 1, np.where(low12, 3, 2)).astype(float)
res['window_2015_2026_agreement_with_2015_2024_pct'] = round(100 * float((s12[dom] == base[dom]).mean()), 2)
res['window_2015_2026_shares_pct'] = {c: round(100 * float((s12[dom] == c).mean()), 1) for c in (1, 2, 3)}
json.dump(res, open(R + 'results/results_holdout_2025_2026.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
