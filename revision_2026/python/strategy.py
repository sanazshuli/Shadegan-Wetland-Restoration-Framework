import os
WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')  # folder holding the exported rasters and intermediate files
import numpy as np, json, pickle
from scipy import ndimage
R = WD
o = np.load(R + 'domain_outputs.npz'); dom = o['dom']; base = o['base']
occ, fw, ts, nmed = o['occ'], o['f_water'], o['ts'], o['ndvi_med']
L = np.load(R + 'layers_raster.npz')
S = np.load(R + 'stack.npy'); aoi = ~np.isnan(S[..., 0])
H, W = dom.shape; y0, dx = 31.573536448590882, 0.002245788210298804
lat = y0 - (np.arange(H) + .5) * dx; pa = (dx * 111.32) ** 2 * np.cos(np.deg2rad(lat))[:, None] * np.ones(W)
samp = (dx * 111.32, dx * 111.32 * np.cos(np.deg2rad(30.8)))
dist = lambda m: ndimage.distance_transform_edt(~m, sampling=samp)
sugar = np.load(R + 'sugarcane_candidate.npy')          # persistent July-green irrigated blocks (sugarcane proxy)
d_urban = dist(L['shahrha'] | L['railways'])            # cities + railways (admin boundaries are NOT stressors)
d_sugar = dist(sugar)
d_stress = np.minimum(d_urban, d_sugar)
d_river = dist(L['otherrivers'] | L['abeshirin'])
lost = dom & (occ >= 25) & (fw <= 0.2); vegdec = dom & (nmed >= 0.2) & (ts <= -0.005) & ~lost
prot = L['hefazatshode']
NAMES = {1: 'Water management', 2: 'Re-vegetation', 3: 'Pollution control', 4: 'Conservation', 5: 'Monitoring'}

def strategy(buf=3.0, flow=False, conserve_first=False, pc=True, drainage=True):
    s = np.full((H, W), np.nan)
    s[dom] = 5                                            # default: monitoring
    s[dom & (base == 3) & prot] = 4                       # stable & protected -> conservation
    s[lost] = 1; s[vegdec] = 2
    if flow:   # environmental-flow scenario: historically persistent water within reach of inflow re-wets passively
        s[lost & (occ >= 50) & (d_river <= 5)] = 4
    if pc:
        ds = d_stress if drainage else d_urban
        s[dom & (base != 3) & (ds <= buf)] = 3
    if conserve_first:
        s[dom & prot & (base != 1)] = 4
    return s

SC = {'S1 Baseline (3-km stressor buffer)': dict(),
      'S2 Environmental-flow allocation': dict(flow=True),
      'S3a Effective pollution control (no buffer)': dict(pc=False),
      'S3b Weak pollution control (5-km buffer)': dict(buf=5.0),
      'S4 Conservation-first': dict(conserve_first=True)}
res = {}; maps = {}
area = lambda m: float(pa[m].sum())
for k, kw in SC.items():
    s = strategy(**kw); maps[k] = s
    res[k] = {NAMES[c]: round(area(s == c), 1) for c in NAMES}
b1 = maps['S1 Baseline (3-km stressor buffer)']
res['agreement_with_S1_pct'] = {k: round(100 * float((maps[k][dom] == b1[dom]).mean()), 1) for k in SC}
# zones and counties (descriptive only)
zones = {'Freshwater (abeshirin)': L['abeshirin'], 'Brackish (labeabeshur)': L['labeabeshur'], 'Intertidal (jazromad)': L['jazromad'],
         'Protected area (hefazatshode)': prot}
res['S1_by_zone_km2'] = {z: {NAMES[c]: round(area((b1 == c) & m), 1) for c in NAMES} for z, m in zones.items()}
lay = pickle.load(open(R + 'layers.pkl', 'rb'))
from skimage.draw import polygon as skpoly
x0 = 48.284446521424286
cnt = {}
for i, r in enumerate(lay['shahrestanbnd'][0]):
    m = np.zeros((H, W), bool)
    for p in r:
        rr, cc = skpoly((y0 - p[:, 1]) / dx - .5, (p[:, 0] - x0) / dx - .5, (H, W)); m[rr, cc] ^= True
    cnt[lay['shahrestanbnd'][1][i]['Region_Nam']] = m
res['S1_by_county_km2'] = {n: {NAMES[c]: round(area((b1 == c) & m), 1) for c in NAMES} for n, m in cnt.items()}
# buffer sensitivity
res['pollution_buffer_sensitivity_km2'] = {f'{bf} km': round(area(strategy(buf=bf) == 3), 1) for bf in (1, 2, 3, 4, 5)}
res['domain_km2'] = round(area(dom), 1)
res['sugarcane_proxy_km2'] = round(area(sugar), 1)
res['drainage_effect'] = {'PC_with_drainage_km2': round(area(strategy() == 3), 1), 'PC_urban_rail_only_km2': round(area(strategy(drainage=False) == 3), 1),
    'PC_from_drainage_only_km2': round(area(dom & (base != 3) & (d_sugar <= 3) & (d_urban > 3)), 1),
    'agreement_with_without_pct': round(100 * float((strategy()[dom] == strategy(drainage=False)[dom]).mean()), 2)}
json.dump(res, open(R + 'results/results_strategy_scenarios.json', 'w'), indent=1, ensure_ascii=False)
np.savez_compressed(R + 'strategy_maps.npz', **{k.split()[0]: v for k, v in maps.items()})
print(json.dumps(res, indent=1, ensure_ascii=False))
