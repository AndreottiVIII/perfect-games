"""Controlli di robustezza sui risultati sopravvissuti e descrizioni (non sono nuove ipotesi).
Uso: python -I tortura_extra.py <cartella_dati> <cartella_output>"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tortura_lib as T  # noqa: E402
from tortura import prepare  # noqa: E402

data, outdir = sys.argv[1:3]
s, P, se = prepare(data)
P['site'] = P.site.fillna('?')
P['era'] = pd.cut(P.season, [1907, 1919, 1939, 1959, 1979, 1999, 2025], labels=['1908-19', '1920-39', '1940-59', '1960-79', '1980-99', '2000-25'])


def show(lab, r):
    print('  ' + lab + ': ' + ' | '.join(f'{x.fattore}: {T.fmt(x, 3)}' for x in r.itertuples()))


print('--- T17 (lancia la casa): robustezza')
for par in (0, 1, None):
    S = P if par is None else P[P.season % 2 == par]
    nm = 'tutte' if par is None else ('pari' if par == 0 else 'dispari')
    base = T.run_logit(S, 'r', {'casa': 'ps'}, fes=('nd', 'season'))
    c1 = T.run_logit(S.dropna(subset=['x_team', 'x_pit_c']), 'r', {'casa': 'ps', 'attacco': 'x_team', 'lanciatore': 'x_pit_c'}, fes=('nd', 'season'))
    c2 = T.run_logit(S, 'r', {'casa': 'ps'}, fes=('nd', 'season', 'site'))
    show(f'{nm} base', base)
    show(f'{nm} + forza attacco e lanciatore', c1.iloc[:1])
    show(f'{nm} + stadio', c2)
S = P
for era, g in S.groupby('era', observed=True):
    r = T.run_logit(g, 'r', {'casa': 'ps'}, fes=('nd', 'season'))
    print(f'  era {era}: ' + T.fmt(r.iloc[0], 3), f'(turni {len(g)})')
print('  tasso di arrivo in base per n=1..3 (primo giro): lancia casa', round(float(P[(P.ps == 1) & (P.n <= 3)].r.mean()), 4), 'trasferta', round(float(P[(P.ps == 0) & (P.n <= 3)].r.mean()), 4))
print('  lancia la casa, hazard per n=1,2,3,4,10:', {n: (round(float(P[(P.ps == 1) & (P.n == n)].r.mean()), 3), round(float(P[(P.ps == 0) & (P.n == n)].r.mean()), 3)) for n in (1, 2, 3, 4, 10)})
print('--- T25 (temperatura): robustezza')
for par in (0, 1, None):
    S = P if par is None else P[P.season % 2 == par]
    S = S[S.temp.notna() & (S.temp > 0)].assign(t10=lambda x: (x.temp - 70) / 10)
    nm = 'tutte' if par is None else ('pari' if par == 0 else 'dispari')
    show(f'{nm} base', T.run_logit(S, 'r', {'t10': 't10'}, fes=('nd', 'season')))
    show(f'{nm} + stadio + giorno/notte', T.run_logit(S, 'r', {'t10': 't10', 'giorno': 'isday'}, fes=('nd', 'season', 'site')).iloc[:1])
    show(f'{nm} + stadio + mese', T.run_logit(S, 'r', {'t10': 't10'}, fes=('nd', 'season', 'site', 'month')))
    S2 = S[S.season >= 1995]
    show(f'{nm} dal 1995 + stadio', T.run_logit(S2, 'r', {'t10': 't10'}, fes=('nd', 'season', 'site')))
print('--- T19/T20 (lanci): descrizione')
pv = P[(P.season >= 1988) & (P.np > 0) & P.fp.isin(['S', 'B', 'X', 'H'])]
for lab, m in (('n 1-9', pv.n <= 9), ('n 10-18', pv.n.between(10, 18)), ('n 19-27', pv.n >= 19)):
    g = pv[m]
    b = g[g.r == 1]
    bn = b[~b.k.isin(['base_su_ball', 'base_intenzionale'])]
    print(f'  {lab}: primo lancio strike {g.fp.eq("S").mean():.3f}, palla {g.fp.eq("B").mean():.3f}, in gioco {g.fp.eq("X").mean():.3f} (turni {len(g)}); rotture al primo lancio {b.np.eq(1).mean():.3f} (rotture {len(b)}), escluse basi su ball {bn.np.eq(1).mean():.3f} ({len(bn)})')
print('  quota di turni con il primo lancio in gioco tra i turni iniziali (n<=9) e profondi (10+), con arrivo in base:',
      round(float(pv[(pv.n <= 9) & (pv.fp == 'X')].r.mean()), 3), round(float(pv[(pv.n >= 10) & (pv.fp == 'X')].r.mean()), 3))
print('--- Leadoff (n=1) per epoca: hazard n=1, n=2..8, rapporto')
for era, g in P[P.n <= 8].groupby('era', observed=True):
    a, b = g[g.n == 1].r, g[(g.n >= 2)].r
    print(f'  {era}: n=1 {a.mean():.3f} (turni {len(a)}), n=2-8 {b.mean():.3f}, rapporto {a.mean()/b.mean():.3f}')
print('--- Sfilacciamento: dopo la prima rottura')
B = P[P.r == 1][['key', 'g', 'season', 'n', 'k']].merge(se[['key', 'nxt_n', 'nxt_r']], on='key').merge(s[['key', 'hits_allowed', 'game_status']], on='key')
B = B[B.nxt_n >= 1]
B['bucket'] = pd.cut(B.n, [0, 9, 18, 27], labels=['1-9', '10-18', '19-27'])
sd = se.set_index('key').runs_allowed
B['runs_allowed'] = B.key.map(sd)
for bk, g in B.groupby('bucket', observed=True):
    comp = g[g.game_status == 'completa']
    print(f'  rottura al battitore {bk}: sides {len(g)}; arrivi nei 3 turni dopo {g.nxt_r.sum()/g.nxt_n.sum():.3f}; prossimo battitore (se noto) -; completa: no-hitter {comp.hits_allowed.eq(0).mean():.4f}, zero punti subiti {comp.runs_allowed.eq(0).mean():.4f} (n={len(comp)})')
nh = B[(~B.k.isin(['singolo', 'doppio', 'triplo', 'fuoricampo'])) & (B.game_status == 'completa')]
for bk, g in nh.groupby('bucket', observed=True):
    print(f'  rottura senza colpo al battitore {bk}: n={len(g)}, no-hitter {g.hits_allowed.eq(0).mean():.3f}, zero punti {g.runs_allowed.eq(0).mean():.3f}')
print('--- T24 (ricevitori): i loro effetti restano tolta la squadra-stagione e il lanciatore?')
from scipy import stats  # noqa: E402


def ctab(Q, fes):
    X0, nfe = T.fe_design(Q, fes)
    b, cov = T.fit_logit(X0, Q.r.to_numpy(), Q.g.to_numpy(), nfe)
    p = T.expit(X0 @ b)
    Q = Q.assign(p=p, v=p * (1 - p))
    Q = Q[Q.cat != '']
    g = Q.groupby('cat').agg(O=('r', 'sum'), E=('p', 'sum'), V=('v', 'sum'), N=('r', 'size'))
    g = g[g.N >= 300]
    g['logOR'] = (g.O - g.E) / g.V
    g['se'] = 1 / np.sqrt(g.V)
    return g


P['tseason'] = P.pitching_team + P.season.astype(str)
P['pitseason'] = P.pit + P.season.astype(str)
for lab, fes in (('base', ('nd', 'season')), ('+ squadra-stagione', ('nd', 'tseason')), ('+ lanciatore-stagione', ('nd', 'pitseason'))):
    e, o = ctab(P[P.season % 2 == 0], fes), ctab(P[P.season % 2 == 1], fes)
    j = e.join(o, lsuffix='_e', rsuffix='_o', how='inner')
    w = 1 / j.se_o ** 2
    x, y = j.logOR_e.to_numpy(), j.logOR_o.to_numpy()
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    sl = np.sum(w * (x - xm) * (y - ym)) / np.sum(w * (x - xm) ** 2)
    resid = y - ym - sl * (x - xm)
    se_s = np.sqrt(np.sum(w ** 2 * (x - xm) ** 2 * resid ** 2) / np.sum(w * (x - xm) ** 2) ** 2)
    chi_e = ((e.logOR / e.se) ** 2).sum()
    print(f'  {lab}: ricevitori in comune {len(j)}, pendenza {sl:.3f} ± {1.96*se_s:.3f}, Spearman {stats.spearmanr(x, y).statistic:.2f}; eterogeneità pari chi2 {chi_e:.0f} su {len(e)} (p={stats.chi2.sf(chi_e, len(e)):.2g})')
