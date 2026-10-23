"""Funzioni comuni per le analisi (hazard, intervalli, caricamento dati).
Modulo usato da come_cala.py e chicche.py (con python -I va aggiunta la cartella src al percorso,
cosa che gli script fanno da soli).
"""
import numpy as np
import pandas as pd


def load(path):
    d = pd.read_csv(path, low_memory=False)
    d = d[d.league_file.isin(['A', 'N', 'F']) & (d.deduced == 0)].copy()
    d['reach'] = (d.first_runner_event != 'nessuno').astype(int)
    d['bat_dh'] = d.bat_dh.astype(int)
    return d


def wilson(k, n, z=1.96):
    k = np.asarray(k, float)
    n = np.asarray(n, float)
    with np.errstate(divide='ignore', invalid='ignore'):
        p = k / n
        den = 1 + z * z / n
        c = (p + z * z / (2 * n)) / den
        h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return np.clip(c - h, 0, 1), np.clip(c + h, 0, 1)


def risk_table(sub, nmax=27):
    """Per n = 1..nmax: lati a rischio, lati che cadono proprio all'n-esimo battitore, hazard."""
    d = sub.batters_retired.to_numpy().astype(int)
    e = sub.reach.to_numpy().astype(bool)
    rows = []
    for n in range(1, nmax + 1):
        at_risk = int((e & (d >= n - 1)).sum() + (~e & (d >= n)).sum())
        broken = int((e & (d == n - 1)).sum())
        lo, hi = wilson(broken, at_risk) if at_risk else (np.nan, np.nan)
        rows.append(dict(n=n, slot=(n - 1) % 9 + 1, tto=(n - 1) // 9 + 1, at_risk=at_risk,
                         broken=broken, hazard=broken / at_risk if at_risk else np.nan,
                         lo=float(lo), hi=float(hi)))
    t = pd.DataFrame(rows)
    t['survival'] = (1 - t.hazard.fillna(0)).cumprod()
    return t
