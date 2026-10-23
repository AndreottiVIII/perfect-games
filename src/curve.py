"""Curva di sopravvivenza (Kaplan-Meier) delle partite ancora perfette dopo n battitori.

S(n) = quota di lati al lancio con i primi n battitori tutti eliminati.
hazard(n) = probabilita' condizionata che proprio l'n-esimo battitore sia il primo a
arrivare in base, sapendo che i primi n-1 erano stati eliminati.

Un lato senza battitori in base (partita perfetta o finita prima) esce dal rischio dopo
l'ultimo battitore affrontato ma conta come "sopravvissuto" fino a li'.

Uso: python -I curve.py <streaks.csv> <cartella_output>
Di base: solo Lega Americana/Nazionale/Federale (non Negro Leagues), senza partite
"dedotte" (ricostruite da box score). Con --con-dedotte si include anche quelle.
"""
import os
import sys

import numpy as np
import pandas as pd


def km(sub, nmax=None):
    d = sub.batters_retired.to_numpy()
    e = (sub.first_runner_event != 'nessuno').to_numpy()
    if nmax is None:
        nmax = max(int(d.max()) + 1, 27)
    rows = [dict(n=0, at_risk=len(d), broken_at_n=0, hazard=np.nan, survival=1.0, se=0.0)]
    s, green = 1.0, 0.0
    for k in range(1, nmax + 1):
        at_risk = int((e & (d >= k - 1)).sum() + (~e & (d >= k)).sum())
        if at_risk == 0:
            if k > 27:
                break
            # nessuno arriva fin qui: la curva empirica e' ferma (a 0 se tutti sono caduti prima)
            rows.append(dict(n=k, at_risk=0, broken_at_n=0, hazard=np.nan,
                             survival=s, se=0.0))
            continue
        broken = int((e & (d == k - 1)).sum())
        h = broken / at_risk
        s *= 1 - h
        if at_risk > broken:
            green += broken / (at_risk * (at_risk - broken))
        rows.append(dict(n=k, at_risk=at_risk, broken_at_n=broken, hazard=h,
                         survival=s, se=s * np.sqrt(green)))
    out = pd.DataFrame(rows)
    out['ci_low'] = (out.survival - 1.96 * out.se).clip(lower=0)
    out['ci_high'] = out.survival + 1.96 * out.se
    return out


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    with_ded = '--con-dedotte' in sys.argv
    d = pd.read_csv(src, low_memory=False)
    d = d[d.league_file.isin(['A', 'N', 'F'])]
    if not with_ded:
        d = d[d.deduced == 0]
    os.makedirs(outdir, exist_ok=True)

    overall = km(d)
    overall.to_csv(os.path.join(outdir, 'curve_overall.csv'), index=False)

    parts = []
    for dec, sub in d.groupby('decade'):
        c = km(sub)
        c.insert(0, 'sides', len(sub))
        c.insert(0, 'decade', dec)
        parts.append(c)
    pd.concat(parts).to_csv(os.path.join(outdir, 'curve_by_decade.csv'), index=False)

    print('lati usati:', len(d), '| partite dedotte', 'incluse' if with_ded else 'escluse')
    for n in (3, 9, 18, 27):
        r = overall[overall.n == n].iloc[0]
        print(f'  S({n}) = {r.survival:.6f}  (1 su {1/r.survival:,.0f})  a rischio {int(r.at_risk)}')
    print('  S(27) per decennio:')
    for c in parts:
        r = c[c.n == 27]
        if len(r):
            print(f'    {int(c.decade.iloc[0])}s: {r.survival.iloc[0]:.6f}  (lati {c.sides.iloc[0]:,})')


if __name__ == '__main__':
    main()
