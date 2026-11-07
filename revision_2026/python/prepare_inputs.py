"""Convert the Earth Engine exports and the planning shapefiles into the arrays used by the other scripts.

Inputs (in SHADEGAN_WORKDIR, default work/):
  Shadegan_priority_versions_stack.tif   (from gee/01_rerun_archived_versions_V0_V2.js)
  Shadegan_domain_inputs.tif             (from gee/02_wetland_domain_inputs.js)
  Shadegan_holdout_2025_2026.tif         (from gee/03_holdout_2025_2026_and_ERA5.js)
  shapefiles/*.shp                       (digitized 2011 management-plan layers; not redistributed)
Outputs: stack.npy, domain.npy, holdout.npy (+ *_bands.txt), layers.pkl, layers_raster.npz, sugarcane_candidate.npy
"""
import os, sys, glob, pickle
import numpy as np
from matplotlib.path import Path
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiffread2 import read_stack
from shpread import read_shp, read_dbf, lcc_inverse, utm_inverse

WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')
ORIGIN_LON, ORIGIN_LAT, RES = 48.284446521424286, 31.573536448590882, 0.002245788210298804

# 1. rasters -> npy
for tif, stem in [('Shadegan_priority_versions_stack.tif', 'stack'), ('Shadegan_domain_inputs.tif', 'domain'),
                  ('Shadegan_holdout_2025_2026.tif', 'holdout')]:
    p = WD + tif
    if os.path.exists(p):
        arr, names, _ = read_stack(p)
        np.save(WD + stem + '.npy', arr); open(WD + stem + '_bands.txt', 'w').write('\n'.join(names))
        print(stem, arr.shape)
S = np.load(WD + 'stack.npy'); NR, NC = S.shape[:2]

# 2. shapefiles -> lon/lat (coordinate system detected from the coordinate range when no .prj is present)
def to_lonlat(xy, prj):
    x, y = xy[:, 0], xy[:, 1]
    if 'UTM' in prj or (prj == '' and x.min() > 1e5 and y.min() > 3e6):
        return np.column_stack(utm_inverse(x, y, 39))
    if 'Lambert' in prj or 'lamiran' in prj or (prj == '' and abs(x).max() > 1e3):
        return np.column_stack(lcc_inverse(x, y))
    return xy
layers = {}
for shp in sorted(glob.glob(WD + 'shapefiles/*.shp')):
    name = os.path.basename(shp)[:-4]
    prjf = shp[:-4] + '.prj'; prj = open(prjf).read() if os.path.exists(prjf) else ''
    parts = [[to_lonlat(p, prj) for p in rec] for rec in read_shp(shp)]
    attrs = read_dbf(shp[:-4] + '.dbf') if os.path.exists(shp[:-4] + '.dbf') else []
    layers[name] = (parts, attrs)
pickle.dump(layers, open(WD + 'layers.pkl', 'wb'))

# 3. rasterize on the analysis grid (cell centres inside polygons; cells touched by lines/points)
lon_c = ORIGIN_LON + (np.arange(NC) + 0.5) * RES; lat_c = ORIGIN_LAT - (np.arange(NR) + 0.5) * RES
LON, LAT = np.meshgrid(lon_c, lat_c); centres = np.column_stack([LON.ravel(), LAT.ravel()])
LINES = {'karoonriver', 'otherrivers', 'railways'}
rast = {}
for name, (parts, _) in layers.items():
    m = np.zeros(NR * NC, bool)
    if name in LINES or name == 'shahrha' and all(len(p) == 1 for rec in parts for p in rec):
        for rec in parts:
            for p in rec:
                seg = [p]
                if len(p) > 1:   # densify to ~1/4 cell
                    d = np.hypot(*np.diff(p, axis=0).T); n = np.maximum(1, (d / (RES / 4)).astype(int))
                    seg = [np.linspace(p[i], p[i + 1], n[i] + 1) for i in range(len(p) - 1)]
                q = np.vstack(seg); c = ((q[:, 0] - ORIGIN_LON) / RES).astype(int); r = ((ORIGIN_LAT - q[:, 1]) / RES).astype(int)
                ok = (r >= 0) & (r < NR) & (c >= 0) & (c < NC); m[r[ok] * NC + c[ok]] = True
    else:
        for rec in parts:
            inside = np.zeros(NR * NC, bool)
            for p in rec:   # even-odd rule handles holes
                inside ^= Path(p).contains_points(centres)
            m |= inside
    rast[name] = m.reshape(NR, NC)
np.savez_compressed(WD + 'layers_raster.npz', **rast)

# 4. summer-irrigated field blocks (drainage-source proxy): cropland outside the wetland domain,
#    July NDVI > 0.4 in at least 8 of 10 years (2015-2024), connected blocks >= 4 km2
D = np.load(WD + 'domain.npy'); dn = open(WD + 'domain_bands.txt').read().split('\n'); b = {k: D[..., i] for i, k in enumerate(dn)}
dom = np.load(WD + 'domain_outputs.npz')['dom'] if os.path.exists(WD + 'domain_outputs.npz') else None
green = sum((b[f'NDVI_{y}'] > 0.4).astype(int) for y in range(2015, 2025))
cand = (b['frac_wc40'] >= 0.5) & (green >= 8)
if dom is not None: cand &= ~dom.astype(bool)
lab, n = ndimage.label(cand)                                   # 4-connected blocks
sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
keep = np.isin(lab, np.where(sizes >= 64)[0] + 1)             # >= 4 km2 at the nominal 250 x 250 m cell size
cell_km2 = (RES * 111.32) ** 2 * np.cos(np.deg2rad(lat_c))[:, None] * np.ones((1, NC))
np.save(WD + 'sugarcane_candidate.npy', keep)
print('layers', list(rast), 'sugarcane proxy km2', round(float(cell_km2[keep].sum()), 1))
