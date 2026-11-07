import os
WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')  # folder holding the exported rasters and intermediate files
import numpy as np, json
from scipy import ndimage
D = np.load(WD + 'domain.npy'); dn = open(WD + 'domain_bands.txt').read().split('\n')
b = {k: D[..., i] for i, k in enumerate(dn)}
S = np.load(WD + 'stack.npy'); sn = open(WD + 'stack_bands.txt').read().split('\n')
s = {k: S[..., i] for i, k in enumerate(sn)}
years = list(range(2015, 2025))
NDVI = np.stack([b[f'NDVI_{y}'] for y in years]); NDWI = np.stack([b[f'NDWI_{y}'] for y in years]); B2 = np.stack([b[f'B2_{y}'] for y in years])
aoi = ~np.isnan(s['NDVI'])

# ---------- 1. wetland domain ----------
wcw = b['frac_wc80'] + b['frac_wc90']
dom = aoi & ((wcw >= 0.5) | (b['frac_jrc_max_extent'] >= 0.5))
dom = ndimage.binary_closing(dom, iterations=1) & aoi
lab, n = ndimage.label(dom); sizes = ndimage.sum(dom, lab, range(1, n + 1))
keep = np.isin(lab, 1 + np.where(sizes >= 16)[0])          # drop patches < 1 km2 (16 px)
dom = ndimage.binary_fill_holes(keep) & aoi
PX_KM2 = 0.0625 * np.cos(np.deg2rad(30.8))**1 * (111.32**2 / 111.32**2)  # approx; exact area below
lat = 31.573536448590882 - (np.arange(S.shape[0]) + 0.5) * 0.002245788210298804
px_km2 = (0.002245788210298804 * 111.32) ** 2 * np.cos(np.deg2rad(lat))[:, None] * np.ones(S.shape[1])
area = lambda m: float((px_km2 * m).sum())

# ---------- 2. indicators ----------
f_water = (NDWI > 0).mean(0)                                 # share of July composites with open-water response
occ = b['jrc_occurrence_mean']                               # long-term (1984-2021) water occurrence, %
ndvi_med = np.nanmedian(NDVI, 0)
# Theil-Sen slope of annual NDVI
t = np.array(years, float); pairs = [(i, j) for i in range(10) for j in range(i + 1, 10)]
slopes = np.stack([(NDVI[j] - NDVI[i]) / (t[j] - t[i]) for i, j in pairs]); ts = np.nanmedian(slopes, 0)
b2_med = np.nanmedian(B2, 0)

def screen(p, turb=False):
    veg = ndvi_med >= p['veg']
    lost_water = (occ >= p['occ']) & (f_water <= p['f_dry'])
    veg_decline = veg & (ts <= p['slope'])
    high = lost_water | veg_decline
    low = (f_water >= p['f_wet']) | (veg & (ts >= 0))
    if turb:
        wet = f_water >= 0.5
        thr = np.nanpercentile(b2_med[dom & wet], p['b2_pct'])
        high = high | (wet & (b2_med >= thr))
    out = np.where(high, 1, np.where(low, 3, 2)).astype(float)
    out[~dom] = np.nan
    return out

BASE = dict(occ=25, f_dry=0.2, slope=-0.005, veg=0.2, f_wet=0.8, b2_pct=90)
base = screen(BASE)
res = {'domain_km2': round(area(dom), 1), 'aoi_km2': round(area(aoi), 1), 'domain_px': int(dom.sum())}
sh = lambda x: {c: round(100 * float(np.nansum(px_km2 * (x == c)) / area(dom)), 2) for c in (1, 2, 3)}
res['base_shares_pct'] = sh(base)
res['base_with_turbidity_shares_pct'] = sh(screen(BASE, turb=True))
res['turbidity_effect_pct_changed'] = round(100 * float(((screen(BASE, True) != base) & dom).sum() / dom.sum()), 2)
# clause contributions
veg = ndvi_med >= BASE['veg']
res['clauses_pct_of_domain'] = {
    'lost_water': round(100 * float(((occ >= 25) & (f_water <= .2) & dom).sum() / dom.sum()), 2),
    'veg_decline': round(100 * float((veg & (ts <= -0.005) & dom).sum() / dom.sum()), 2),
    'stable_water': round(100 * float(((f_water >= .8) & dom).sum() / dom.sum()), 2),
    'veg_stable_or_greening': round(100 * float((veg & (ts >= 0) & dom).sum() / dom.sum()), 2)}
# archived V0 inside the domain
v0 = np.floor(s['V0_rf_smooth'] + .5)
res['V0_archived_rerun_in_domain_shares'] = sh(np.where(dom, v0, np.nan))
res['agreement_V0_vs_new_in_domain_pct'] = round(100 * float((v0[dom] == base[dom]).mean()), 2)

# ---------- 3. Monte Carlo threshold uncertainty ----------
rng = np.random.default_rng(42); N = 500
R = dict(occ=(15, 35), f_dry=(0.1, 0.3), slope=(-0.010, -0.002), veg=(0.15, 0.25), f_wet=(0.7, 0.9))
cnt = np.zeros((3,) + base.shape); shares = []
for k in range(N):
    p = {key: rng.uniform(*R[key]) for key in R}; p['b2_pct'] = 90
    m = screen(p)
    for c in (1, 2, 3): cnt[c - 1] += (m == c)
    shares.append([sh(m)[c] for c in (1, 2, 3)])
prob = cnt / N; pmax = prob.max(0); modal = prob.argmax(0) + 1.0; modal[~dom] = np.nan
shares = np.array(shares)
res['mc_draws'] = N; res['mc_ranges'] = R
res['mc_share_mean_and_95CI'] = {c: [round(float(shares[:, i].mean()), 2), round(float(np.percentile(shares[:, i], 2.5)), 2), round(float(np.percentile(shares[:, i], 97.5)), 2)] for i, c in enumerate(('High', 'Medium', 'Low'))}
res['mc_pixels_stable_ge80pct'] = round(100 * float((pmax[dom] >= 0.8).mean()), 2)
res['mc_pixels_stable_ge95pct'] = round(100 * float((pmax[dom] >= 0.95).mean()), 2)
res['mc_modal_equals_base_pct'] = round(100 * float((modal[dom] == base[dom]).mean()), 2)
res['mc_robust_high_km2'] = round(area(dom & (prob[0] >= 0.8)), 1)

# ---------- 4. scale (R2.6) ----------
mixed = dom & (wcw > 0.1) & (wcw < 0.9)
res['scale_mixed_cells_pct_of_domain'] = round(100 * float(mixed.sum() / dom.sum()), 2)
tot_wet = float((px_km2 * wcw)[aoi].sum())
lost = float((px_km2 * wcw)[aoi & (wcw < 0.5)].sum())
res['scale_10m_water_wetland_area_km2'] = round(tot_wet, 1)
res['scale_share_in_cells_below_50pct'] = round(100 * lost / tot_wet, 2)

json.dump(res, open(WD + 'results/results_wetland_domain_screen.json', 'w'), indent=1)
np.savez_compressed(WD + 'domain_outputs.npz', dom=dom, base=base, prob=prob, modal=modal, f_water=f_water, ts=ts, ndvi_med=ndvi_med, occ=occ)
print(json.dumps(res, indent=1))
