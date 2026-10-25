"""Grafico di 'come cala': a ogni battitore, probabilita' che una squadra ancora perfetta perda la
partita perfetta proprio li', separando le squadre al bat senza DH (batte il lanciatore) da quelle con DH.
Uso: python -I come_cala_chart.py <come_cala_hazard.csv> <cartella_output>
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE = '#2a78d6', '#eb6834'      # slot 1 e 2 della palette categorica di riferimento
BAND = '#efeeea'
MIN_RISCHIO = 100                         # sotto questo numero di squadre a rischio: punto vuoto, niente barre


def pct(v, _):
    return f'{v * 100:g}%'


def main():
    hz = pd.read_csv(sys.argv[1])
    outdir = sys.argv[2]
    nodh = hz[hz.gruppo == 'senza_dh'].set_index('n')
    dh = hz[hz.gruppo == 'con_dh'].set_index('n')

    fig, ax = plt.subplots(figsize=(11, 6.6), dpi=160)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    for n in (9, 18, 27):                 # il 9° della formazione (tocca al lanciatore se non c'è il DH)
        ax.axvspan(n - 0.5, n + 0.5, color=BAND, zorder=0, lw=0)
    ax.text(18, 0.46, 'batters 9, 18, 27 = the No. 9 spot in the lineup', ha='center', va='bottom',
            color=INK2, fontsize=9.5)

    for t, col, off in ((nodh, BLUE, -0.12), (dh, ORANGE, 0.12)):
        x = t.index.to_numpy()
        big = t.at_risk >= MIN_RISCHIO
        ax.plot(x, t.hazard, color=col, lw=1.8, zorder=3, solid_capstyle='round')
        ax.vlines(x[big] + off * 0, t.lo[big], t.hi[big], color=col, lw=1.1, alpha=0.45, zorder=2)
        ax.plot(x[big], t.hazard[big], 'o', ms=5.5, color=col, mec=SURFACE, mew=1, zorder=4)
        ax.plot(x[~big], t.hazard[~big], 'o', ms=5.5, mfc=SURFACE, mec=col, mew=1.3, zorder=4)

    # etichette dirette (a sinistra, dove le linee sono vicine ma distinguibili)
    ax.annotate('No DH: the pitcher bats', xy=(5, nodh.hazard[5]), xytext=(2.6, 0.405),
                color=INK, fontsize=10.5, fontweight='bold', ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color=BLUE, lw=1.2, shrinkA=0, shrinkB=4))
    ax.annotate('With DH', xy=(12, dh.hazard[12]), xytext=(12.2, 0.205),
                color=INK, fontsize=10.5, fontweight='bold', ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color=ORANGE, lw=1.2, shrinkA=0, shrinkB=4))
    ax.annotate(f'{nodh.hazard[9] * 100:.1f}%', xy=(9, nodh.hazard[9]), xytext=(7.0, 0.165),
                color=INK, fontsize=10, ha='center', va='center',
                arrowprops=dict(arrowstyle='-', color=INK2, lw=0.9, shrinkA=0, shrinkB=4))
    ax.annotate(f'{dh.hazard[9] * 100:.1f}%', xy=(9, dh.hazard[9]), xytext=(10.4, 0.215),
                color=INK, fontsize=10, ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color=INK2, lw=0.9, shrinkA=0, shrinkB=4))

    # legenda (due serie: sempre presente)
    lx, ly = 0.40, 0.17
    for i, (lab, col) in enumerate((('Batting side without a DH (pitcher in the lineup)', BLUE),
                                    ('Batting side with a DH', ORANGE))):
        y = ly - i * 0.055
        ax.plot([lx, lx + 0.03], [y, y], transform=ax.transAxes, color=col, lw=3, solid_capstyle='butt')
        ax.text(lx + 0.04, y, lab, transform=ax.transAxes, color=INK2, fontsize=9.5, va='center', ha='left')
    ax.plot([lx + 0.015], [ly - 0.11], 'o', transform=ax.transAxes, ms=5.5, mfc=SURFACE, mec=INK2, mew=1.3)
    ax.text(lx + 0.04, ly - 0.11, f'Fewer than {MIN_RISCHIO} sides still perfect: shaky number',
            transform=ax.transAxes, color=INK2, fontsize=9.5, va='center', ha='left')

    ax.set_xlim(0.3, 27.7)
    ax.set_ylim(0, 0.5)
    ax.set_xticks(range(1, 28, 2))
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.yaxis.set_major_formatter(FuncFormatter(pct))
    ax.grid(axis='y', color=GRID, lw=0.8, zorder=0)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=10, length=0)
    ax.tick_params(axis='x', length=3)
    ax.set_xlabel('Batter faced (everyone before him retired)', color=INK2, fontsize=11)
    ax.set_ylabel('Chance the perfect game ends at that batter', color=INK2, fontsize=11)

    fig.text(0.07, 0.975, 'About a 1-in-3 chance at almost every batter. It drops only when the pitcher bats',
             fontsize=14.5, fontweight='bold', color=INK, ha='left', va='top')
    fig.text(0.07, 0.915, 'Among pitching sides still perfect, the share that loses it exactly at batter n. '
             'MLB regular season, 1908-2025;' + chr(10) + 'thin bars are 95% confidence intervals.',
             fontsize=10, color=INK2, ha='left', va='top')
    fig.text(0.07, 0.012, 'Source: Retrosheet (retrosheet.org); games rebuilt from box scores are left out. '
             '"With DH" = the batting side had a designated hitter in its starting lineup.',
             fontsize=8.5, color=INK2, ha='left', va='bottom')
    fig.subplots_adjust(left=0.085, right=0.96, top=0.82, bottom=0.14)

    os.makedirs(outdir, exist_ok=True)
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(outdir, f'come_cala.{ext}'), facecolor=SURFACE)
    print('grafico salvato in', outdir)


if __name__ == '__main__':
    main()
