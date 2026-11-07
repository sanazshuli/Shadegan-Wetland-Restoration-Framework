import os
WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')  # folder holding the exported rasters and intermediate files
import sys, json, glob, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from tiffread import read_geotiff

S = np.load(WD + 'stack.npy')
names = open(WD + 'stack_bands.txt').read().split('\n')
B = {n: S[..., i] for i, n in enumerate(names)}
res = {}

# ---- align archived exports (stack origin is 1 px west and 1 px north) ----
arch = {}
for f in sorted(glob.glob(WD + 'archived_exports/*.tif')):
    k = 'Copy' if 'Copy' in f else f.split('Final')[-1].replace('.tif', '')
    if k == '-5':  # byte-identical to -3
        continue
    a, _ = read_geotiff(f)
    al = np.full(S.shape[:2], np.nan); al[1:1 + a.shape[0], 1:1 + a.shape[1]] = a[:S.shape[0] - 1, :S.shape[1] - 1]
    arch[k] = al
cls = lambda x: np.where(np.isnan(x), np.nan, np.floor(x + 0.5))  # 1.5 -> 2, 2.5 -> 3 (rare edge medians)
V = {k: cls(B[k]) for k in names if k.startswith('V') and not k.endswith('overlap')}
A = {k: cls(v) for k, v in arch.items()}
valid = np.ones(S.shape[:2], bool)
for x in list(V.values()) + list(A.values()):
    valid &= ~np.isnan(x)
res['n_common_valid'] = int(valid.sum())

def agree(x, y): return float(100 * (x[valid] == y[valid]).mean())
def shares(x):
    v = x[valid]; return {c: round(float(100 * (v == c).mean()), 2) for c in (1, 2, 3)}

res['archived_pairwise'] = {f'{a} vs {b}': round(agree(A[a], A[b]), 2) for a, b in itertools.combinations(A, 2)}
stackA = np.stack([A[k][valid] for k in A]); res['archived_unanimous'] = round(float(100 * (stackA == stackA[0]).all(0).mean()), 2)
res['V0rerun_vs_archived'] = {k: round(agree(V['V0_rf_smooth'], A[k]), 2) for k in A}
allfive = np.vstack([stackA, V['V0_rf_smooth'][valid][None]])
res['unanimous_archived_plus_rerun'] = round(float(100 * (allfive == allfive[0]).all(0).mean()), 2)

res['shares'] = {k: shares(v) for k, v in V.items()}
res['shares']['archived_mean'] = {c: round(float(np.mean([shares(a)[c] for a in A.values()])), 2) for c in (1, 2, 3)}
res['rf_vs_direct'] = {v: round(agree(V[f'{v}_rf'], V[f'{v}_direct']), 2) for v in ('V0', 'V1', 'V2')}
res['rf_smooth_vs_direct'] = {v: round(agree(V[f'{v}_rf_smooth'], V[f'{v}_direct']), 2) for v in ('V0', 'V1', 'V2')}
res['overlap_high_and_low_pct'] = {v: round(float(100 * B[f'{v}_overlap'][valid].mean()), 2) for v in ('V0', 'V1', 'V2')}
for kind in ('rf_smooth', 'direct'):
    res[f'agreement_{kind}'] = {'V0_vs_V1': round(agree(V[f'V0_{kind}'], V[f'V1_{kind}']), 2),
                                'V1_vs_V2': round(agree(V[f'V1_{kind}'], V[f'V2_{kind}']), 2),
                                'V0_vs_V2': round(agree(V[f'V0_{kind}'], V[f'V2_{kind}']), 2)}
def transition(x, y):
    m = np.zeros((3, 3), int)
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            m[i - 1, j - 1] = int(((x[valid] == i) & (y[valid] == j)).sum())
    return m.tolist()
res['transition_V0rf_to_V2direct'] = transition(V['V0_rf_smooth'], V['V2_direct'])
res['transition_V0direct_to_V1direct'] = transition(V['V0_direct'], V['V1_direct'])

lc = B['LandCover'][valid]
u, c = np.unique(lc[~np.isnan(lc)], return_counts=True)
res['landcover_pct'] = {int(k): round(float(100 * n / c.sum()), 2) for k, n in zip(u, c)}

# ---- what the archived NDVI/NDWI rule actually selected (raw index means) ----
for v, hi in (('V0', B['NDVI_norm'].__lt__), ('V2', B['NDVI_norm'].__gt__)):
    pass
nd, nw = B['NDVI_norm'][valid], B['NDWI_norm'][valid]
rv, rw = B['NDVI'][valid], B['NDWI'][valid]
sel_v0 = (nd < 0.53) & (nw < 0.53); sel_v2 = (nd > 0.47) & (nw > 0.47)
res['spectral_high_clause'] = {
    'V0_selected_pct': round(float(100 * sel_v0.mean()), 2), 'V0_mean_raw_NDVI': round(float(np.nanmean(rv[sel_v0])), 3), 'V0_mean_raw_NDWI': round(float(np.nanmean(rw[sel_v0])), 3),
    'V2_selected_pct': round(float(100 * sel_v2.mean()), 2), 'V2_mean_raw_NDVI': round(float(np.nanmean(rv[sel_v2])), 3), 'V2_mean_raw_NDWI': round(float(np.nanmean(rw[sel_v2])), 3),
    'AOI_mean_raw_NDVI': round(float(np.nanmean(rv)), 3), 'AOI_mean_raw_NDWI': round(float(np.nanmean(rw)), 3)}

json.dump(res, open(WD + 'results/results_archived_versions.json', 'w'), indent=1)
np.save(WD + 'valid_mask.npy', valid)
print(json.dumps(res, indent=1))
