"""Grafico: quota di partite ancora perfette dopo n battitori, una linea per decennio.
Uso: python -I chart.py <curve_by_decade.csv> <curve_overall.csv> <cartella_output>
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
# rampa ordinale blu della palette di riferimento, passi 250 -> 700 (decennio piu' vecchio = piu' chiaro)
RAMP = ['#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab',
        '#184f95', '#104281', '#0d366b']


def ramp_colors(k):
    rgb = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in RAMP], float)
    pos = np.linspace(0, len(RAMP) - 1, k)
    cols = [[np.interp(p, range(len(RAMP)), rgb[:, c]) for c in range(3)] for p in pos]
    return ['#%02x%02x%02x' % tuple(int(round(v)) for v in c) for c in cols]


def pct(v, _):
    s = f'{v * 100:g}'
    return s + '%'


def main():
    dec_path, ov_path, outdir = sys.argv[1:4]
    dec = pd.read_csv(dec_path)
    ov = pd.read_csv(ov_path)
    decades = sorted(dec.decade.unique())
    cols = ramp_colors(len(decades))

    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    MIN_CASI = 25   # le linee dei decenni si fermano quando i lati ancora "a rischio" sono meno di 25
    names = {1900: '1908-09'}
    ends = {}
    for dcd, col in zip(decades, cols):
        g = dec[(dec.decade == dcd) & (dec.survival > 0) & (dec.at_risk >= MIN_CASI) & (dec.n <= 27)]
        ax.plot(g.n, g.survival, color=col, lw=1.8, solid_capstyle='round', zorder=3)
        last = g.iloc[-1]
        ax.plot([last.n], [last.survival], 'o', ms=4, color=col, mec=SURFACE, mew=1, zorder=4)
        ends[dcd] = (last.n, last.survival, col)

    # etichette dirette: primo e ultimo decennio, a fine linea
    for dcd, dy, dx in ((decades[0], 1.7, -0.3), (decades[-1], 0.2, 0.9)):
        n, sv, col = ends[dcd]
        ax.annotate(names.get(dcd, f'{int(dcd)}s'), xy=(n, sv), xytext=(n + dx, sv * dy),
                    color=INK, fontsize=10, fontweight='bold', va='center', ha='left',
                    arrowprops=dict(arrowstyle='-', color=col, lw=1, shrinkA=0, shrinkB=3))

    g = ov[(ov.survival > 0) & (ov.n <= 27)]
    ax.plot(g.n, g.survival, color=INK, lw=2.8, zorder=5)
    n27 = g[g.n == 27].iloc[0]
    ax.plot([27], [n27.survival], 'o', ms=7, color=INK, mec=SURFACE, mew=1.5, zorder=6)
    NL = chr(10)
    ax.annotate(NL.join(['All games: still perfect after 27 batters, 1 in 17,500', '(21 perfect games, plus Haddix and Martinez, who lost it later)']),
                xy=(27, n27.survival), xytext=(26.3, n27.survival * 0.32),
                color=INK, fontsize=9.5, va='top', ha='right', zorder=7,
                arrowprops=dict(arrowstyle='-', color=INK, lw=1, shrinkA=0, shrinkB=4))
    ax.annotate('All games', xy=(9, ov[ov.n == 9].survival.iloc[0]),
                xytext=(10.3, ov[ov.n == 9].survival.iloc[0] * 4),
                color=INK, fontsize=10.5, fontweight='bold', va='center', ha='left',
                arrowprops=dict(arrowstyle='-', color=INK, lw=1, shrinkA=0, shrinkB=3))

    # legenda dei decenni (rampa chiara = piu' vecchio, scura = piu' recente)
    lx, ly0 = 0.60, 0.93
    ax.text(lx, ly0 + 0.002, 'Decade (darker = more recent)', transform=ax.transAxes,
            color=INK2, fontsize=9.5, va='bottom', ha='left')
    for i, (dcd, col) in enumerate(zip(decades, cols)):
        r, c = i % 7, i // 7
        x, y = lx + c * 0.17, ly0 - 0.045 - r * 0.045
        ax.plot([x, x + 0.025], [y, y], transform=ax.transAxes, color=col, lw=3, solid_capstyle='butt')
        ax.text(x + 0.032, y, names.get(dcd, f'{int(dcd)}s'), transform=ax.transAxes,
                color=INK2, fontsize=9.5, va='center', ha='left')

    ax.set_yscale('log')
    ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5])
    ax.set_xlim(0, 28.5)
    ax.set_ylim(4e-6, 1.3)
    ax.axvline(27, color=INK2, lw=1, ls=(0, (4, 3)), zorder=2)
    ax.text(27, 1.45, '27 = perfect game', ha='center', va='bottom', color=INK2, fontsize=9.5)

    ax.yaxis.set_major_locator(FixedLocator([1, 1e-1, 1e-2, 1e-3, 1e-4]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(pct))
    ax.set_xticks(range(0, 28, 3))
    ax.set_xticks([27], minor=True)
    ax.grid(axis='y', color=GRID, lw=0.8, zorder=0)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=10, length=0)
    ax.tick_params(axis='x', which='both', length=3)
    ax.set_xlabel('Batters faced (all retired so far)', color=INK2, fontsize=11)
    ax.set_ylabel('Games still perfect (log scale)', color=INK2, fontsize=11)

    fig.text(0.07, 0.975, 'Every game starts out perfect. Almost none stay that way',
             fontsize=15, fontweight='bold', color=INK, ha='left', va='top')
    fig.text(0.07, 0.92, 'Pitching sides that have not yet let a single batter reach base, '
             'after n batters faced. MLB regular season, 1908-2025.',
             fontsize=10, color=INK2, ha='left', va='top')
    fig.text(0.07, 0.012, 'Source: Retrosheet (retrosheet.org); games rebuilt from box scores are left out.' + chr(10) +
             'Decade lines stop when fewer than 25 sides are still perfect: past that point there are too few cases.',
             fontsize=8.5, color=INK2, ha='left', va='bottom')
    fig.subplots_adjust(left=0.085, right=0.93, top=0.82, bottom=0.14)

    os.makedirs(outdir, exist_ok=True)
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(outdir, f'curve_by_decade.{ext}'), facecolor=SURFACE)
    print('grafico salvato in', outdir)


if __name__ == '__main__':
    main()
