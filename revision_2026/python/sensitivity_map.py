"""Digitize the four-level habitat-sensitivity map (Appendix 2 of the 2011 Shadegan integrated management plan)
and cross-tabulate it with the revised priority screen and the S1 strategy layer.

Input : page image of Appendix 2 rendered at 300 dpi (e.g. `pdftoppm -png -r 300 -f 45 -l 45 plan.pdf p`);
        the plan is not redistributed. Pixel positions of the UTM 39N grid lines below refer to that rendering.
Output: results/sensitivity_grid.npy (0 = unmapped, 1 very high, 2 high, 3 medium, 4 low)
        results/results_sensitivity_map_comparison.json
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from shpread import utm_inverse

R = os.environ.get('SHADEGAN_WORKDIR', 'work/')
page = sys.argv[1] if len(sys.argv) > 1 else R + 'p-45.png'
X0, Y0, PX_E, PX_N = 837, 1226, 659, 661          # pixel of E 250000 / N 3400000 and pixels per 50 km
ORIGIN_LON, ORIGIN_LAT, RES = 48.284446521424286, 31.573536448590882, 0.002245788210298804
COLS = {1: (246, 8, 9), 2: (246, 129, 156), 3: (247, 246, 15), 4: (114, 214, 13)}   # legend colours

im = np.array(Image.open(page).convert('RGB')).astype(float)
H, W, _ = im.shape
cls = np.zeros((H, W), np.uint8); best = np.full((H, W), 1e9)
for k, c in COLS.items():
    d = np.sqrt(((im - np.array(c)) ** 2).sum(-1)); m = (d < 60) & (d < best); cls[m] = k; best[m] = d[m]
yy, xx = np.mgrid[0:H, 0:W]
inside = (xx > 531) & (xx < 2114) & (yy > 498) & (yy < 2660)                       # map frame
inside &= ~((xx < 1060) & (yy > 2030)); inside &= ~((xx > 1500) & (yy > 2330)); inside &= ~((xx > 1780) & (yy < 840))  # legend, title, inset
cls[~inside] = 0
E = 250000 + (xx - X0) * 50000 / PX_E; N = 3400000 - (yy - Y0) * 50000 / PX_N
sel = cls > 0
lon, lat = utm_inverse(E[sel], N[sel], 39)

o = np.load(R + 'domain_outputs.npz'); dom = o['dom'].astype(bool); base = o['base']; pH = o['prob'][0]
S1 = np.load(R + 'strategy_maps.npz')['S1']
prot = np.load(R + 'layers_raster.npz')['hefazatshode'].astype(bool)
nr, nc = dom.shape
c = np.floor((lon - ORIGIN_LON) / RES).astype(int); r = np.floor((ORIGIN_LAT - lat) / RES).astype(int)
ok = (r >= 0) & (r < nr) & (c >= 0) & (c < nc)
cnt = np.zeros((5, nr, nc), np.int32); np.add.at(cnt, (cls[sel][ok], r[ok], c[ok]), 1)
S = np.argmax(cnt[1:], 0) + 1; S[cnt[1:].sum(0) == 0] = 0
os.makedirs(R + 'results', exist_ok=True); np.save(R + 'results/sensitivity_grid.npy', S)

# registration check: overlap with the protected-area layer under small shifts
iou = lambda a, b: (a & b).sum() / (a | b).sum()
shifts = {(dy, dx): iou(np.roll(np.roll(S > 0, dy, 0), dx, 1), prot) for dy in range(-8, 9, 2) for dx in range(-8, 9, 2)}

lat_c = ORIGIN_LAT - (np.arange(nr) + 0.5) * RES
a = (RES * 111.32) ** 2 * np.cos(np.deg2rad(lat_c))[:, None] * np.ones((1, nc))
names = {1: 'Very high', 2: 'High', 3: 'Medium', 4: 'Low', 0: 'Outside map'}
lab = {1: 'WM', 2: 'RV', 3: 'PC', 4: 'CS', 5: 'MO'}
out = {'sens_area_km2': {names[k]: round(float(a[S == k].sum()), 1) for k in [1, 2, 3, 4]},
       'sens_total_km2': round(float(a[S > 0].sum()), 1),
       'domain_in_sens_pct': round(float(a[dom & (S > 0)].sum() / a[dom].sum() * 100), 1),
       'IoU_sens_protected': round(float(shifts[(0, 0)]), 2),
       'best_shift_cells': [int(v) for v in max(shifts, key=shifts.get)]}
out['priority_by_sensitivity'] = {}
for k in [1, 2, 3, 4, 0]:
    m = dom & (S == k); t = a[m].sum()
    out['priority_by_sensitivity'][names[k]] = {'domain_km2': round(float(t), 1),
        **{p: round(float(a[m & (base == v)].sum() / t * 100), 1) for v, p in [(1, 'High%'), (2, 'Medium%'), (3, 'Low%')]},
        'robustHigh_km2': round(float(a[m & (pH >= 0.8)].sum()), 1)}
out['S1_strategy_km2_by_sensitivity'] = {names[k]: {lab[v]: round(float(a[dom & (S == k) & (S1 == v)].sum()), 1) for v in lab} for k in [1, 2, 3, 4, 0]}
vhh = (S == 1) | (S == 2)
for v in [1, 3, 4, 5]:
    mm = dom & (S1 == v); out[f'{lab[v]}_in_VH_or_H_pct'] = round(float(a[mm & vhh].sum() / a[mm].sum() * 100), 1)
out['robustHigh_in_VH_or_H_pct'] = round(float(a[dom & (pH >= 0.8) & vhh].sum() / a[dom & (pH >= 0.8)].sum() * 100), 1)
json.dump(out, open(R + 'results/results_sensitivity_map_comparison.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
