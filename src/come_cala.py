"""Parte A: come cala la curva delle partite perfette.

Uso: python -I come_cala.py <streaks.csv> <pa_tally.csv> <cartella_output>

Produce (in output/): come_cala_hazard.csv, come_cala_null.csv, come_cala_null_decenni.csv,
come_cala_eventi.csv e stampa un riepilogo corto. I testi sono in come_cala.md (scritto a mano).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_common import load, risk_table, wilson  # noqa: E402


def pois_ci(k, z=1.96):
    """Intervallo approssimato (Byar) per un conteggio di Poisson."""
    k = np.asarray(k, float)
    lo = k * (1 - 1 / (9 * k) - z / (3 * np.sqrt(k))) ** 3 if k > 0 else 0.0
    kk = k + 1
    hi = kk * (1 - 1 / (9 * kk) + z / (3 * np.sqrt(kk))) ** 3
    return lo, hi


# ---------------------------------------------------------------- regressione logistica a gruppi
def grouped_logit(X, k, n, iters=50):
    beta = np.zeros(X.shape[1])
    beta[0] = np.log((k.sum() / n.sum()) / (1 - k.sum() / n.sum()))
    for _ in range(iters):
        eta = X @ beta
        p = 1 / (1 + np.exp(-eta))
        w = n * p * (1 - p)
        z = eta + (k - n * p) / np.maximum(w, 1e-12)
        XtW = X.T * w
        new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.abs(new - beta).max() < 1e-9:
            beta = new
            break
        beta = new
    p = 1 / (1 + np.exp(-(X @ beta)))
    w = n * p * (1 - p)
    cov = np.linalg.inv((X.T * w) @ X)
    with np.errstate(divide='ignore', invalid='ignore'):
        dev = 2 * np.nansum(np.where(k > 0, k * np.log(k / (n * p)), 0)
                            + np.where(n - k > 0, (n - k) * np.log((n - k) / (n * (1 - p))), 0))
    return beta, np.sqrt(np.diag(cov)), dev


def slot_tto_model(t, drop_slot9=False):
    t = t[t.at_risk > 0]
    if drop_slot9:
        t = t[t.slot != 9]
    cols = ['icpt'] + [f'slot{s}' for s in range(2, 10) if (t.slot == s).any()] + ['tto2', 'tto3']
    X = np.column_stack([np.ones(len(t))] +
                        [(t.slot == s).astype(float) for s in range(2, 10) if (t.slot == s).any()] +
                        [(t.tto == 2).astype(float), (t.tto == 3).astype(float)])
    beta, se, dev = grouped_logit(X, t.broken.to_numpy(float), t.at_risk.to_numpy(float))
    out = {}
    for c, b, s in zip(cols, beta, se):
        out[c] = (np.exp(b), np.exp(b - 1.96 * s), np.exp(b + 1.96 * s))
    return out, dev, len(t) - len(cols)


# ---------------------------------------------------------------- modello nullo
def build_rates(tally_path, d):
    """Probabilita' di arrivare in base per turno di battuta, per lega/decennio/slot/lanciatore/giro,
    solo nei mezzi inning ancora 'puliti' (nessuno in base), riscalate sul livello della stagione."""
    t = pd.read_csv(tally_path)
    t = t[(t.deduced == 0) & t.league_file.isin(['A', 'N', 'F'])].copy()
    t['decade'] = t.season // 10 * 10
    allpa = t.groupby(['season', 'league_file'])[['pa', 'reach']].sum()
    p_all_season = allpa.reach / allpa.pa
    dec = t.groupby(['decade', 'league_file'])[['pa', 'reach']].sum()
    p_all_dec = dec.reach / dec.pa
    be = t[t.bases_empty == 1].groupby(['decade', 'league_file', 'slot', 'is_pitcher', 'tto'])[['pa', 'reach']].sum()
    p_cell = (be.reach / be.pa).to_dict()
    # casella di riserva (senza distinguere la lega) per le rare combinazioni vuote
    any_lg = t[t.bases_empty == 1].groupby(['decade', 'slot', 'is_pitcher', 'tto'])[['pa', 'reach']].sum()
    p_cell_any = (any_lg.reach / any_lg.pa).to_dict()
    return p_all_season.to_dict(), p_all_dec.to_dict(), (p_cell, p_cell_any)


def null_matrices(d, tally_path):
    p_s, p_d, (p_cell, p_cell_any) = build_rates(tally_path, d)
    N = len(d)
    season = d.season.to_numpy()
    dec = (season // 10 * 10)
    lg = d.league_file.to_numpy()
    dh = d.bat_dh.to_numpy()
    # N1: un solo numero per lato = tasso della stagione (tutti i turni, tutte le situazioni)
    p1 = np.array([p_s[(s, l)] for s, l in zip(season, lg)])
    # N2: stesso tasso ma per slot / lanciatore alla battuta / giro / basi vuote
    scale = np.array([p_s[(s, l)] / p_d[(c, l)] for s, l, c in zip(season, lg, dec)])
    p2 = np.zeros((N, 27))
    keys = pd.DataFrame({'dec': dec, 'lg': lg, 'dh': dh, 'scale': scale})
    ug = keys.drop_duplicates(['dec', 'lg', 'dh'])
    for _, r in ug.iterrows():
        m = ((keys.dec == r.dec) & (keys.lg == r.lg) & (keys.dh == r.dh)).to_numpy()
        row = np.zeros(27)
        for n in range(1, 28):
            slot, tto = (n - 1) % 9 + 1, min((n - 1) // 9 + 1, 3)
            is_p = int(slot == 9 and r.dh == 0)
            v = p_cell.get((r.dec, r.lg, slot, is_p, tto))
            if v is None:
                v = p_cell_any[(r.dec, slot, is_p, tto)]
            row[n - 1] = v
        p2[m] = row
    assert not np.isnan(p2).any()
    p2 = np.clip(p2 * scale[:, None], 0.02, 0.95)
    return p1, p2


def pitcher_ratio(d, min_exp=30):
    """Quanto e' 'forte' il lanciatore partente (carriera intera), stimato dalle sue ALTRE partenze
    (si toglie la partita in esame) e ridotto verso la media. Restituisce, per ogni lato, il rapporto
    tra la probabilita' di far arrivare in base di quel lanciatore e quella media della stagione.
    Si usano i turni osservati prima della fine della serie: eliminati + il primo arrivato in base."""
    trials = (d.batters_retired + d.reach).to_numpy(float)
    br = d.reach.to_numpy(float)
    g = pd.DataFrame({'season': d.season.to_numpy(), 'lg': d.league_file.to_numpy(),
                      'pit': d.starting_pitcher.to_numpy(), 'T': trials, 'B': br})
    league = g.groupby(['season', 'lg'])[['T', 'B']].sum()
    pbar = (league['B'] / league['T']).to_dict()
    g['E'] = g['T'] * np.array([pbar[(s, l)] for s, l in zip(g.season, g.lg)])   # rotture attese a livello medio
    tot = g.groupby('pit')[['B', 'E']].transform('sum')
    # peso del prior (metodo dei momenti): var(B/E) = tau^2 + 1/E
    agg = g.groupby('pit')[['B', 'E']].sum()
    agg = agg[agg.E >= min_exp]
    r_ = (agg.B / agg.E).to_numpy()
    w = agg.E.to_numpy()
    var_obs = np.average((r_ - np.average(r_, weights=w)) ** 2, weights=w)
    var_samp = np.average(1 / w, weights=w)
    tau2 = max(var_obs - var_samp, 1e-4)
    m = 1 / tau2                                  # forza del prior, in rotture attese
    Bm = tot['B'].to_numpy() - g.B.to_numpy()
    Em = tot['E'].to_numpy() - g.E.to_numpy()
    return (Bm + m) / (Em + m), m, np.sqrt(tau2)


def expected_hazard(d, P):
    """Hazard atteso sotto il modello nullo, pesato sui lati realmente a rischio all'n-esimo battitore."""
    dd = d.batters_retired.to_numpy().astype(int)
    e = d.reach.to_numpy().astype(bool)
    h0 = np.zeros(27)
    exp_b = np.zeros(27)
    ar = np.zeros(27)
    for n in range(1, 28):
        a = (e & (dd >= n - 1)) | (~e & (dd >= n))
        ar[n - 1] = a.sum()
        pn = P[:, n - 1] if P.ndim == 2 else P
        exp_b[n - 1] = pn[a].sum()
        h0[n - 1] = exp_b[n - 1] / ar[n - 1] if ar[n - 1] else np.nan
    return h0, exp_b, ar


def null_table(d, t, Ps):
    out = t[['n', 'slot', 'tto', 'at_risk', 'broken', 'hazard', 'survival']].copy()
    # errore standard di log S (Greenwood)
    h = t.hazard.fillna(0).to_numpy()
    ar = t.at_risk.to_numpy().astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        gw = np.cumsum(np.where(ar > t.broken.to_numpy(), h / (ar * (1 - h)), 0))
    out['se_logS'] = np.sqrt(gw)
    for name, P in Ps.items():
        h0, exp_b, _ = expected_hazard(d, P)
        out[f'h0_{name}'] = h0
        out[f'exp_broken_{name}'] = exp_b
        out[f'S0_{name}'] = np.cumprod(1 - np.nan_to_num(h0))
        out[f'ratio_{name}'] = out.survival / out[f'S0_{name}']
        out[f'z_{name}'] = np.log(out.survival / out[f'S0_{name}']) / out.se_logS
    return out


# ---------------------------------------------------------------- eventi di rottura
GROUPS = {'singolo': 'singolo', 'doppio': 'doppio o triplo', 'triplo': 'doppio o triplo',
          'fuoricampo': 'fuoricampo', 'base_su_ball': 'base su ball', 'base_intenzionale': 'base su ball',
          'colpito': 'colpito', 'errore': 'errore'}
ORDER = ['singolo', 'doppio o triplo', 'fuoricampo', 'base su ball', 'colpito', 'errore', 'altro']


def era_of(s):
    if s < 1946:
        return '1908-1945'
    if s < 1973:
        return '1946-1972'
    if s < 1993:
        return '1973-1992'
    if s < 2009:
        return '1993-2008'
    return '2009-2025'


def main():
    src, tally, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    d = load(src)
    print('lati:', len(d), '| con DH nella squadra al bat:', int(d.bat_dh.sum()))

    # ---------- 1. hazard per battitore, senza DH / con DH
    tabs = {'tutti': risk_table(d), 'senza_dh': risk_table(d[d.bat_dh == 0]), 'con_dh': risk_table(d[d.bat_dh == 1])}
    hz = pd.concat([t.assign(gruppo=k) for k, t in tabs.items()])
    hz.to_csv(os.path.join(outdir, 'come_cala_hazard.csv'), index=False)
    for k, t in tabs.items():
        print(f'[{k}] S(9)=1/{1/t.survival[8]:.1f} S(18)=1/{1/t.survival[17]:.0f} S(27)=1/{1/t.survival[26]:,.0f}')
    for k in ('senza_dh', 'con_dh'):
        t = tabs[k]
        s9 = t[t.slot == 9]
        r8 = t[t.slot != 9]
        # hazard medio nei battitori 9/18/27 contro gli altri, pesato sui lati a rischio
        print(f'[{k}] hazard slot 9 = {s9.broken.sum()}/{s9.at_risk.sum()} = {s9.broken.sum()/s9.at_risk.sum():.4f};'
              f' slot 1-8 = {r8.broken.sum()}/{r8.at_risk.sum()} = {r8.broken.sum()/r8.at_risk.sum():.4f}')
        # prima e dopo il 1973 per i soli lati senza DH
    nodh = d[d.bat_dh == 0]
    for lab, sub in (('senza DH fino al 1972', nodh[nodh.season <= 1972]), ('senza DH dal 1973', nodh[nodh.season >= 1973])):
        t = risk_table(sub)
        s9 = t[(t.slot == 9) & (t.n <= 27)]
        print(f'[{lab}] lati {len(sub):,} hazard n=9: {t.hazard[8]:.3f} (n={t.at_risk[8]}) ; slot9 tot {s9.broken.sum()/s9.at_risk.sum():.3f}; altri {t[t.slot!=9].broken.sum()/t[t.slot!=9].at_risk.sum():.3f}')

    # ---------- 2. slot contro giro
    for k in ('senza_dh', 'con_dh'):
        out, dev, dof = slot_tto_model(tabs[k])
        print(f'[logit {k}] devianza {dev:.1f} su {dof} gradi: ' + '; '.join(
            f'{c} OR {v[0]:.2f} [{v[1]:.2f}-{v[2]:.2f}]' for c, v in out.items() if c in ('slot9', 'slot8', 'slot2', 'tto2', 'tto3')))
    out, dev, dof = slot_tto_model(tabs['senza_dh'], drop_slot9=True)
    print('[logit senza DH, senza slot 9] ' + '; '.join(f'{c} OR {v[0]:.2f} [{v[1]:.2f}-{v[2]:.2f}]' for c, v in out.items() if c.startswith('tto')))
    for k in ('senza_dh', 'con_dh'):
        t = tabs[k]
        piv = t.pivot(index='slot', columns='tto', values='hazard').round(3)
        cnt = t.pivot(index='slot', columns='tto', values='at_risk')
        print(f'hazard per slot (righe) e giro (colonne), {k}:\n{piv.to_string()}\n a rischio:\n{cnt.to_string()}')
    # chi rompe al battitore 9/18/27
    brk = d[d.reach == 1].copy()
    brk['n_b'] = brk.batters_retired + 1
    for lab, sub in (('senza DH', brk[brk.bat_dh == 0]), ('con DH', brk[brk.bat_dh == 1])):
        s9 = sub[sub.n_b.isin([9, 18, 27])]
        print(f'[{lab}] rotture al 9/18/27: {len(s9)}; con lanciatore alla battuta (pos=1): {(s9.breaker_pos==1).sum()} ({(s9.breaker_pos==1).mean():.1%}); pinch hitter (pos=11): {(s9.breaker_pos==11).sum()}')

    # ---------- 3. modello nullo
    p1, p2 = null_matrices(d, tally)
    ratio, m, tau = pitcher_ratio(d)
    p3 = np.clip(p2 * ratio[:, None], 0.02, 0.95)
    print(f'lanciatori: peso del prior m={m:.0f} rotture attese, deviazione standard del talento (in rapporto) tau={tau:.3f}; rapporto min/max {ratio.min():.2f}/{ratio.max():.2f}')
    Ps = {'N1': p1, 'N2': p2, 'N3': p3}
    nt = null_table(d, tabs['tutti'], Ps)
    nt.to_csv(os.path.join(outdir, 'come_cala_null.csv'), index=False)
    N = len(d)
    for nm in Ps:
        print(f'  {nm}: S0(9)=1/{1/nt[f"S0_{nm}"][8]:.1f}  S0(18)=1/{1/nt[f"S0_{nm}"][17]:,.0f}  S0(27)=1/{1/nt[f"S0_{nm}"][26]:,.0f}'
              f'  -> attese {N*nt[f"S0_{nm}"][26]:.2f} partite perfette (equivalenti) contro {N*nt.survival[26]:.1f} reali')
    # blocchi
    blocks = [(1, 3), (4, 8), (9, 9), (10, 17), (18, 18), (19, 27), (1, 27), (1, 9), (10, 18), (19, 27)]
    print('blocchi di battitori: osservati / attesi (N1 | N2 | N3)')
    for a, b in blocks:
        s = nt[(nt.n >= a) & (nt.n <= b)]
        ob = s.broken.sum()
        print(f'  n={a}-{b}: rotture {ob}  attese ' + ' | '.join(f'{s[f"exp_broken_{k}"].sum():.0f}' for k in Ps) +
              '   rapporto ' + ' | '.join(f'{ob/s[f"exp_broken_{k}"].sum():.3f}' for k in Ps))
    print('S/S0 (N2) per n=3,6,9,12,15,18,21,24,27:', {int(n): round(float(r), 2) for n, r in zip(nt.n, nt.ratio_N2) if n % 3 == 0})
    print('S/S0 (N3):', {int(n): round(float(r), 2) for n, r in zip(nt.n, nt.ratio_N3) if n % 3 == 0})
    print('z (N3):', {int(n): round(float(r), 1) for n, r in zip(nt.n, nt.z_N3) if n % 3 == 0})
    # per decennio
    rows = []
    d['decade'] = d.season // 10 * 10
    for dcd, sub in d.groupby('decade'):
        sub = sub.reset_index(drop=True)
        mask = (d.decade == dcd).to_numpy()
        t = risk_table(sub)
        r = dict(decade=dcd, sides=len(sub), perfect=int(((sub.batters_retired >= 27) & (sub.reach == 0)).sum()))
        for nm, P in Ps.items():
            h0, _, _ = expected_hazard(sub, P[mask])
            S0 = np.cumprod(1 - np.nan_to_num(h0))
            for n in (9, 18, 27):
                r[f'S{n}_real'] = t.survival[n - 1]
                r[f'S{n}_{nm}'] = S0[n - 1]
        for n in (9, 18, 27):
            r[f'att{n}'] = len(sub) * t.survival[n - 1]
        rows.append(r)
    dt = pd.DataFrame(rows)
    dt.to_csv(os.path.join(outdir, 'come_cala_null_decenni.csv'), index=False)
    show = dt.copy()
    show['real_27_eq'] = show.sides * show.S27_real
    for nm in ('N1', 'N2', 'N3'):
        show[f'att_27_{nm}'] = show.sides * show[f'S27_{nm}']
        show[f'r18_{nm}'] = show.S18_real / show[f'S18_{nm}']
    print('per decennio: lati, perfette, reali(equiv.), attese N1/N2/N3 a 27; rapporto a 18 N1/N2/N3')
    print(show[['decade', 'sides', 'perfect', 'real_27_eq', 'att_27_N1', 'att_27_N2', 'att_27_N3', 'r18_N1', 'r18_N2', 'r18_N3']].round(2).to_string(index=False))

    # ---------- 4. come finisce il sogno
    brk = d[d.reach == 1].copy()
    brk['gruppo'] = brk.first_runner_event.map(GROUPS).fillna('altro')
    brk['era'] = brk.season.map(era_of)
    brk['n_b'] = brk.batters_retired + 1
    rows = []

    def add(label, sub):
        c = sub.gruppo.value_counts()
        for g in ORDER:
            k = int(c.get(g, 0))
            lo, hi = wilson(k, len(sub))
            rows.append(dict(insieme=label, evento=g, n=k, tot=len(sub), quota=k / len(sub), lo=float(lo), hi=float(hi)))
    add('tutte le rotture', brk)
    for e, sub in brk.groupby('era'):
        add(f'era {e}', sub)
    add('rotture al battitore 10-18', brk[(brk.n_b >= 10) & (brk.n_b <= 18)])
    add('rotture al battitore 19-27', brk[(brk.n_b >= 19) & (brk.n_b <= 27)])
    add('rotture al battitore 27', brk[brk.n_b == 27])
    ev = pd.DataFrame(rows)
    ev.to_csv(os.path.join(outdir, 'come_cala_eventi.csv'), index=False)
    piv = ev.pivot(index='evento', columns='insieme', values='quota').loc[ORDER]
    cols = ['tutte le rotture'] + [c for c in piv.columns if c.startswith('era')] + [c for c in piv.columns if c.startswith('rotture')]
    print((piv[cols] * 100).round(1).to_string())
    print('totali:', ev.drop_duplicates('insieme').set_index('insieme').tot.to_dict())
    late = ev[ev.insieme == 'rotture al battitore 19-27'].set_index('evento')
    base = ev[ev.insieme == 'tutte le rotture'].set_index('evento')
    print('19-27 vs tutte (quota, CI):', {g: (round(late.quota[g] * 100, 1), round(late.lo[g] * 100, 1), round(late.hi[g] * 100, 1), round(base.quota[g] * 100, 1)) for g in ORDER})


if __name__ == '__main__':
    main()
