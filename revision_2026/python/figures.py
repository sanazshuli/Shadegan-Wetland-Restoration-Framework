import os
WD = os.environ.get('SHADEGAN_WORKDIR', 'work/')  # folder holding the exported rasters and intermediate files
"""Publication figures following Springer artwork rules:
Arial-metric sans-serif (Liberation Sans), 8 pt lettering, lines >= 0.3 pt, widths <= 174 mm,
no titles inside artwork, lowercase bold panel labels, legends/colour bars outside map frames,
600-dpi TIFF (combination art) + vector PDF.
Colour scheme: every categorical palette is ordered by CIE L* (>= 13 units apart, also from the white
background) and bar charts carry hatching, so all classes remain separable in greyscale print;
continuous maps use monotone-lightness colour maps."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

R = WD; OUT = R + 'figures/'
MM = 1 / 25.4; W2 = 174 * MM
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8,
                     'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
                     'lines.linewidth': 1.0, 'hatch.linewidth': 0.4, 'pdf.fonttype': 42, 'ps.fonttype': 42, 'savefig.dpi': 600})

S = np.load(R + 'stack.npy'); sn = open(R + 'stack_bands.txt').read().split('\n'); B = {k: S[..., i] for i, k in enumerate(sn)}
AOI = ~np.isnan(B['NDVI']); H, Wd = AOI.shape
X0, Y0, DX = 48.284446521424286, 31.573536448590882, 0.002245788210298804
EXT = [X0, X0 + Wd * DX, Y0 - H * DX, Y0]
CEXT = [EXT[0], EXT[1], EXT[3], EXT[2]]
ASPECT = 1 / np.cos(np.deg2rad(30.8))
O = np.load(R + 'domain_outputs.npz'); DOM = O['dom']

# --- palettes (L* in brackets) ---
PRI = ['#7a2a04', '#e0701a', '#f7d36a']                    # High (29) / Medium (59) / Low (86)
PRI_N = ['High', 'Medium', 'Low']
STR = {1: ('Water management', '#0b2a5c', ''),           # 18
       3: ('Pollution control', '#b2182b', 'xxxx'),      # 38
       2: ('Re-vegetation', '#1f7a3a', '////'),          # 58 (hatched in bars)
       4: ('Conservation', '#a990d0', '....'),           # 64
       5: ('Monitoring', '#efefef', '')}                 # 94
EDGE = '#1a1a1a'
META = {'Author': 'Sanaz Shuli', 'Subject': 'Shadegan Wetland restoration screening (revision of WELA-D-26-00390)'}

def save(fig, name, title):
    fig.savefig(OUT + name + '.pdf', bbox_inches='tight', metadata=dict(META, Title=title))
    fig.savefig(OUT + name + '.tif', dpi=600, bbox_inches='tight', pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(OUT + name + '.png', dpi=200, bbox_inches='tight')
    plt.close(fig)

def label(ax, t, x=-0.02, y=1.02):
    ax.text(x, y, t, transform=ax.transAxes, fontweight='bold', fontsize=9, va='bottom', ha='left')

def basemap(ax, scalebar=True):
    ax.imshow(np.where(AOI, 1.0, np.nan), cmap='gray', vmin=0, vmax=1, extent=EXT, interpolation='nearest')
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3]); ax.set_aspect(ASPECT)
    ax.set_xticks([48.5, 49.0, 49.5]); ax.set_yticks([30.25, 30.75, 31.25])
    ax.set_xticklabels(['48.5°E', '49.0°E', '49.5°E']); ax.set_yticklabels(['30.25°N', '30.75°N', '31.25°N'])
    if scalebar:   # top-left corner lies outside the basin
        km = 25; deg = km / (111.32 * np.cos(np.deg2rad(31.4)))
        x, y = 48.47, 31.47
        ax.plot([x, x + deg], [y, y], color='k', lw=1.2, solid_capstyle='butt')
        ax.text(x + deg / 2, y - 0.03, f'{km} km', ha='center', va='top', fontsize=7)
        ax.annotate('', xy=(48.40, 31.40), xytext=(48.40, 31.22),
                    arrowprops=dict(arrowstyle='-|>,head_width=0.25,head_length=0.5', lw=0.8, color='k'))
        ax.text(48.40, 31.42, 'N', ha='center', va='bottom', fontsize=7, fontweight='bold')

def outlines(ax, domain=False):
    if domain:
        ax.contour(DOM.astype(float), [0.5], colors='#7f7f7f', linewidths=0.3, extent=CEXT)
    ax.contour(AOI.astype(float), [0.5], colors='#333333', linewidths=0.5, extent=CEXT)

def show(ax, arr, cmap, vmin, vmax):
    return ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax, extent=EXT, interpolation='nearest')

def patch(c, n, h=''):
    return Patch(facecolor=c, edgecolor=EDGE, linewidth=0.4, hatch=h, label=n)

def colorbar(fig, im, rect, lab):
    cax = fig.add_axes(rect); cb = fig.colorbar(im, cax=cax, orientation='horizontal')
    cb.set_label(lab); cb.outline.set_linewidth(0.4); cb.ax.tick_params(width=0.5, length=2.5)

# ---------------- annual series ----------------
def fig_annual():
    an = pd.read_csv(R + 'results/annual_scenes_and_areas.csv')
    fig, ax = plt.subplots(3, 1, figsize=(129 * MM, 150 * MM), sharex=True)
    for a in ax:
        a.axvspan(2024.5, 2026.5, facecolor='#f2f2f2', edgecolor='none', zorder=0)
        a.spines[['top', 'right']].set_visible(False)
    for c, l, st, mk, col in (('water_ndwi_gt_0_km2', 'NDWI > 0', '-', 'o', '#08306b'),
                              ('water_ndwi_gt_0p1_km2', 'NDWI > 0.1', '--', 's', '#2171b5'),
                              ('water_ndwi_gt_0p2_km2', 'NDWI > 0.2', ':', '^', '#6baed6')):
        ax[0].plot(an.year, an[c], st, marker=mk, ms=3, mfc='white' if mk != 'o' else col, mec=col, mew=0.7, color=col, label=l)
    ax[0].set_ylabel('July open water (km²)'); ax[0].set_ylim(0, 1000)
    ax[0].legend(frameon=False, loc='lower left', bbox_to_anchor=(0, 0.98), ncol=3, borderaxespad=0, handlelength=2.8)
    ax[1].bar(an.year, an.wet_season_precip_mm, color='#9ecae1', edgecolor=EDGE, linewidth=0.4, width=0.7)
    ax[1].text(2025.5, 575, 'hold-out', ha='center', va='top', fontsize=7, color='#404040')
    ax[1].set_ylabel('Oct–Apr precipitation (mm)'); ax[1].set_ylim(0, 600)
    ax[2].bar(an.year - 0.18, an.scenes_L8_all, 0.36, color='#e0e0e0', edgecolor=EDGE, linewidth=0.4, hatch='////', label='Landsat 8 scenes')
    ax[2].bar(an.year + 0.18, an.scenes_L9_all, 0.36, color='#4d4d4d', edgecolor=EDGE, linewidth=0.4, label='Landsat 9 scenes')
    a2 = ax[2].twinx()
    a2.plot(an.year, an.mean_clear_obs_per_pixel, '-', color='k', marker='D', ms=3, mfc='white', mew=0.7, label='Clear observations per pixel')
    a2.set_ylim(0, 7); a2.set_ylabel('Clear observations per pixel'); a2.spines[['top']].set_visible(False)
    ax[2].set_ylim(0, 14); ax[2].set_ylabel('July scenes'); ax[2].set_xticks(an.year); ax[2].tick_params(axis='x', rotation=90)
    h1, l1 = ax[2].get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
    ax[2].legend(h1 + h2, l1 + l2, frameon=False, loc='lower left', bbox_to_anchor=(0, 0.98), ncol=3, borderaxespad=0)
    for a, t in zip(ax, 'abc'): label(a, t, x=-0.13, y=1.08)
    fig.align_ylabels(ax); plt.tight_layout(h_pad=1.2)
    save(fig, 'Fig_annual_water_precip_scenes', 'July open water, wet-season precipitation and scene availability, 2015-2026')

# ---------------- archived rule versions ----------------
def fig_versions():
    fig, ax = plt.subplots(1, 3, figsize=(W2, 68 * MM))
    for i, (a, k) in enumerate(zip(ax, ('V0_direct', 'V1_direct', 'V2_direct'))):
        basemap(a, scalebar=(i == 0)); show(a, np.floor(B[k] + .5), ListedColormap(PRI), 1, 3); outlines(a); label(a, 'abc'[i])
        if i: a.set_yticklabels([])
    fig.legend(handles=[patch(c, n) for c, n in zip(PRI, PRI_N)], loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
    plt.tight_layout(rect=(0, 0.12, 1, 1)); save(fig, 'Fig_archived_rule_versions', 'Archived priority rule versions V0-V2')

# ---------------- archived vs revised priority ----------------
def fig_priority():
    fig, ax = plt.subplots(1, 3, figsize=(W2, 72 * MM))
    basemap(ax[0]); show(ax[0], np.floor(B['V0_rf_smooth'] + .5), ListedColormap(PRI), 1, 3); outlines(ax[0])
    basemap(ax[1], False); show(ax[1], O['base'], ListedColormap(PRI), 1, 3); outlines(ax[1], True)
    basemap(ax[2], False); im = show(ax[2], np.where(DOM, O['prob'][0], np.nan), 'YlOrBr', 0, 1); outlines(ax[2], True)
    for i, a in enumerate(ax):
        label(a, 'abc'[i])
        if i: a.set_yticklabels([])
    fig.legend(handles=[patch(c, n) for c, n in zip(PRI, PRI_N)], loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.36, 0.02))
    plt.tight_layout(rect=(0, 0.13, 1, 1))
    colorbar(fig, im, [0.70, 0.10, 0.25, 0.03], 'Probability of High (500 draws)')
    save(fig, 'Fig_priority_archived_vs_revised', 'Archived and revised restoration-priority screens')

# ---------------- uncertainty and domain ----------------
def fig_uncert():
    fig, ax = plt.subplots(1, 2, figsize=(W2 * 0.75, 76 * MM))
    basemap(ax[0]); im0 = show(ax[0], np.where(DOM, O['prob'].max(0), np.nan), 'cividis', 0.34, 1); outlines(ax[0], True)
    basemap(ax[1], False); im1 = show(ax[1], np.where(DOM, O['occ'], np.nan), 'Blues', 0, 100); outlines(ax[1], True); ax[1].set_yticklabels([])
    for a, t in zip(ax, 'ab'): label(a, t)
    plt.tight_layout(rect=(0, 0.14, 1, 1))
    for a, im, l in ((ax[0], im0, 'Share of draws in modal class'), (ax[1], im1, 'Long-term water occurrence 1984–2021 (%)')):
        p = a.get_position(); colorbar(fig, im, [p.x0 + 0.1 * p.width, 0.10, 0.8 * p.width, 0.03], l)
    save(fig, 'Fig_uncertainty_and_domain', 'Threshold uncertainty and wetland domain')

# ---------------- strategy and scenarios ----------------
def fig_strategy():
    m = np.load(R + 'strategy_maps.npz'); r = json.load(open(R + 'results/results_strategy_scenarios.json'))
    cmap = ListedColormap([STR[c][1] for c in (1, 2, 3, 4, 5)])
    fig = plt.figure(figsize=(W2, 80 * MM)); gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.1], wspace=0.95)
    ax = fig.add_subplot(gs[0]); basemap(ax); show(ax, m['S1'], cmap, 0.5, 5.5); outlines(ax, True); label(ax, 'a')
    ax2 = fig.add_subplot(gs[1]); sc = [k for k in r if k[:2] in ('S1', 'S2', 'S3', 'S4') and '_' not in k]
    lab = ['S1 Baseline', 'S2 Environmental flow', 'S3a Strong pollution control', 'S3b Weak pollution control', 'S4 Conservation first']
    order = (1, 3, 2, 4, 5); left = np.zeros(len(sc))
    for c in order:
        n, col, h = STR[c]
        v = np.array([r[k][n] for k in sc])
        hc = 'white' if c in (1, 3) else EDGE
        ax2.barh(lab, v, left=left, color=col, edgecolor=hc, linewidth=0, hatch=h, height=0.6)
        ax2.barh(lab, v, left=left, color='none', edgecolor=EDGE, linewidth=0.4, height=0.6)
        left += v
    ax2.invert_yaxis(); ax2.set_xlabel('Area within wetland domain (km²)'); ax2.spines[['top', 'right']].set_visible(False)
    label(ax2, 'b', x=-0.72, y=1.0)
    fig.legend(handles=[patch(STR[c][1], STR[c][0], STR[c][2]) for c in order], loc='lower center', ncol=5, frameon=False,
               bbox_to_anchor=(0.5, 0.0), handlelength=2.2, handleheight=1.2)
    plt.subplots_adjust(bottom=0.2, left=0.08, right=0.98)
    save(fig, 'Fig_strategy_scenarios', 'Restoration-strategy layer and scenario comparison')

if __name__ == '__main__':
    fig_annual(); fig_versions(); fig_priority(); fig_uncert(); fig_strategy(); print('ok')


# ---------------- study area (vector layers) ----------------
def fig_study_area():
    import pickle
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.collections import PatchCollection
    L = pickle.load(open(R + 'layers.pkl', 'rb'))
    def polys(name, sel=None):
        out = []
        for i, rec in enumerate(L[name][0]):
            if sel is not None and i not in sel: continue
            for p in rec:
                if len(p) > 2: out.append(MPoly(p, closed=True))
        return out
    def add(ax, name, fc, ec, hatch='', lw=0.4, z=2, sel=None, alpha=1):
        pc = PatchCollection(polys(name, sel), facecolor=fc, edgecolor=ec, hatch=hatch, linewidth=lw, zorder=z, alpha=alpha)
        ax.add_collection(pc)
    def lines(ax, name, col, lw, ls='-', z=4):
        for rec in L[name][0]:
            for p in rec: ax.plot(p[:, 0], p[:, 1], color=col, lw=lw, ls=ls, zorder=z, solid_capstyle='butt')
    sea_sel = None
    fig = plt.figure(figsize=(W2, 118 * MM)); ax = fig.add_axes([0.07, 0.17, 0.58, 0.80])
    add(ax, 'darya', '#cfe3f2', '#6b8fb3', z=1)
    add(ax, 'hozejarahi', '#ffffff', '#333333', lw=0.7, z=1)
    ax.imshow(np.where(DOM, 1, np.nan), cmap=ListedColormap(['#bdbdbd']), extent=EXT, interpolation='nearest', zorder=1.5)
    add(ax, 'abeshirin', '#2e8b57', '#1a1a1a', hatch='\\\\\\', z=2, alpha=0.55)
    add(ax, 'labeabeshur', '#e8a33d', '#1a1a1a', hatch='////', z=2, alpha=0.75)
    add(ax, 'jazromad', '#8c6d46', '#1a1a1a', hatch='....', z=2, alpha=0.8)
    add(ax, 'hefazatshode', 'none', '#7a0177', lw=1.0, z=3)
    lines(ax, 'shahrestanbnd', '#555555', 0.6, '--', z=3)
    lines(ax, 'otherrivers', '#2166ac', 0.6, '-', z=4)
    lines(ax, 'railways', '#000000', 0.8, (0, (4, 1.5)), z=4)
    sug = np.load(R + 'sugarcane_candidate.npy')
    ax.contourf(np.flipud(sug.astype(float)), [0.5, 1.5], colors='none', hatches=['xxxx'], extent=CEXT, origin='lower', zorder=5)
    ax.contour(np.flipud(sug.astype(float)), [0.5], colors='k', linewidths=0.4, extent=CEXT, origin='lower', zorder=5)
    for rec in L['shahrha'][0]:
        for p in rec:
            c = p.mean(0)
            if EXT[0] < c[0] < EXT[1] and EXT[2] < c[1] < EXT[3]:
                ax.plot(*c, marker='s', ms=3.2, mfc='white', mec='k', mew=0.7, zorder=6)
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2] - 0.08, EXT[3]); ax.set_aspect(ASPECT)
    ax.set_xticks([48.5, 49.0, 49.5]); ax.set_yticks([30.25, 30.75, 31.25])
    ax.set_xticklabels(['48.5°E', '49.0°E', '49.5°E']); ax.set_yticklabels(['30.25°N', '30.75°N', '31.25°N'])
    km = 25; deg = km / (111.32 * np.cos(np.deg2rad(30.0)))
    ax.plot([48.33, 48.33 + deg], [29.99, 29.99], color='k', lw=1.2, solid_capstyle='butt', zorder=7)
    ax.text(48.33 + deg / 2, 30.01, f'{km} km', ha='center', va='bottom', fontsize=7, zorder=7)
    ax.annotate('', xy=(49.70, 31.50), xytext=(49.70, 31.32), arrowprops=dict(arrowstyle='-|>,head_width=0.25,head_length=0.5', lw=0.8, color='k'))
    ax.text(49.70, 31.52, 'N', ha='center', va='bottom', fontsize=7, fontweight='bold')
    ax.text(49.25, 30.02, 'Persian Gulf /\nKhor Musa', fontsize=7, style='italic', ha='center', va='center', color='#2b4c6f')
    h = [Patch(facecolor='white', edgecolor='#333333', lw=0.7, label='Study area (Shadegan sub-basin)'),
         Patch(facecolor='#bdbdbd', edgecolor='none', label='Wetland domain (this study)'),
         Patch(facecolor='#2e8b57', alpha=0.55, edgecolor=EDGE, lw=0.4, hatch='\\\\\\', label='Freshwater zone'),
         Patch(facecolor='#e8a33d', alpha=0.75, edgecolor=EDGE, lw=0.4, hatch='////', label='Brackish zone'),
         Patch(facecolor='#8c6d46', alpha=0.8, edgecolor=EDGE, lw=0.4, hatch='....', label='Intertidal zone'),
         Patch(facecolor='#cfe3f2', edgecolor='#6b8fb3', lw=0.4, label='Sea'),
         Patch(facecolor='none', edgecolor='#7a0177', lw=1.0, label='Protected area'),
         Patch(facecolor='white', edgecolor=EDGE, lw=0.4, hatch='xxxx', label='Summer-irrigated field blocks'),
         Line2D([], [], color='#2166ac', lw=0.6, label='Rivers'),
         Line2D([], [], color='k', lw=0.8, ls=(0, (4, 1.5)), label='Railways'),
         Line2D([], [], color='#555555', lw=0.6, ls='--', label='County boundaries'),
         Line2D([], [], marker='s', ls='none', ms=3.2, mfc='white', mec='k', mew=0.7, label='Cities')]
    fig.legend(handles=h, loc='center left', bbox_to_anchor=(0.67, 0.55), frameon=False, handlelength=2.2, handleheight=1.1, labelspacing=0.7)
    save(fig, 'Fig_study_area', 'Study area, hydrological zones and planning layers')

# ---------------- framework diagram ----------------
def fig_workflow():
    from matplotlib.patches import FancyBboxPatch
    fig = plt.figure(figsize=(W2, 92 * MM)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 174); ax.set_ylim(0, 92); ax.axis('off')
    cols = [('1  Audit', '#e8e8e8', ['Recover archived code', 'Rerun on the archived grid', 'Isolate each error (V0–V2)', 'Document provenance']),
            ('2  Rebuild', '#cfcfcf', ['Define wetland domain', 'Indicators with stated units', 'Direct, documented rules', 'No learned surrogate']),
            ('3  Test', '#b5b5b5', ['Threshold Monte Carlo', 'Scale and proxy checks', 'Hold-out years 2025–2026', 'External comparison']),
            ('4  Use', '#9a9a9a', ['Assign evidence level', 'Low-risk uses only', 'Field verification protocol', 'Update when data arrive'])]
    x0, w, gap = 4, 38, 4.7
    for i, (t, fc, items) in enumerate(cols):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 22), w, 62, boxstyle='round,pad=0.4,rounding_size=1.5', fc=fc, ec=EDGE, lw=0.6))
        ax.text(x + w / 2, 79, t, ha='center', va='center', fontsize=8.5, fontweight='bold')
        for j, it in enumerate(items):
            ax.add_patch(FancyBboxPatch((x + 2, 63 - j * 12.5), w - 4, 9, boxstyle='round,pad=0.2,rounding_size=1', fc='white', ec=EDGE, lw=0.4))
            ax.text(x + w / 2, 67.5 - j * 12.5, it, ha='center', va='center', fontsize=7)
        if i < 3:
            ax.annotate('', xy=(x + w + gap - 0.6, 53), xytext=(x + w + 0.6, 53), arrowprops=dict(arrowstyle='-|>', lw=0.9, color='k'))
    ax.annotate('', xy=(x0 + 6, 20.5), xytext=(x0 + 3 * (w + gap) + w - 6, 20.5),
                arrowprops=dict(arrowstyle='-|>', lw=0.8, color='#333333', ls=(0, (3, 2)), connectionstyle='arc3,rad=-0.1'))
    ax.text(87, 4, 'New field, hydrological or expert evidence re-enters the audit (adaptive management loop)', ha='center', va='center', fontsize=7, style='italic')
    save(fig, 'Fig_workflow', 'Audit-rebuild-test-use framework')

if __name__ == '__main__':
    fig_study_area(); fig_workflow(); print('ok2')
