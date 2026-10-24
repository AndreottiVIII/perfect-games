"""Controlli sui dati estratti per la tortura (confronto con streaks.csv, punti per partita, mani).
Uso: python -I tortura_check.py <cartella_dati>"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tortura_lib as T  # noqa: E402

t0 = time.time()
data = sys.argv[1]
s, P = T.load_pa(data)
print('righe PA', len(P), 'lati', len(s), f'{time.time()-t0:.0f}s')
# coerenza con streaks.csv: eliminati (max 27) e arrivo in base
g = P.groupby('key').agg(ret=('r', lambda x: int((1 - x).sum())), reach=('r', 'max'), nmax=('n', 'max'))
m = s.set_index('key')[['batters_retired', 'reach']].join(g, how='left', rsuffix='_pa')
m['ret'] = m.ret.fillna(0)
m['reach_pa'] = m.reach_pa.fillna(0)
exp_ret = np.minimum(m.batters_retired, 27)
print('lati senza righe:', int(m.nmax.isna().sum()), '| eliminati diversi:', int((exp_ret != m.ret).sum()),
      '| arrivo diverso (solo se n<=27):', int(((m.reach != m.reach_pa) & (m.batters_retired < 27)).sum()))
# punti: media per squadra e partita, per stagione (confronto con valori noti)
sd = pd.read_csv(os.path.join(data, 'side_extra.csv'), keep_default_na=False, dtype={'g': str})
sd['season'] = sd.g.str[3:7].astype(int)
sd = sd[sd.g.isin(set(s.game_id))]
r = sd.groupby('season').runs_scored.mean()
print('punti per squadra e partita:', {y: round(r[y], 2) for y in (1908, 1930, 1968, 1987, 2000, 2010, 2019, 2023) if y in r.index},
      '(noti: 1930 ~5.7, 1968 ~3.4, 2000 ~5.1, 2010 ~4.4, 2019 ~4.8, 2023 ~4.6)')
print('mani note: battitore', float(P.bh.isin(['R', 'L', 'B']).mean()), 'lanciatore', float(P.ph.isin(['R', 'L']).mean()))
for c in ('x_team',):
    pass
P2, se = T.add_strength(P, s, data)
print('righe dopo covariate', len(P2), f'{time.time()-t0:.0f}s')
print(P2[['x_team', 'x_pit_s', 'x_pit_c', 'bbshare', 'ls_z', 'same_hand', 'dayafternight', 'afterextra', 'first_vs']].describe().loc[['count', 'mean', 'std']].round(3).to_string())
print('lead >=1:', float((P2.lead > 0).mean()), ' lead medio', float(P2.lead.mean()))
