"""Parte 2 della tortura: 25 ipotesi pre-dichiarate (output/tortura_ipotesi.md), provate sulle stagioni pari (scoperta)
e poi sulle stagioni dispari (conferma).

Uso:
  python -I tortura.py pari     <cartella_dati> <cartella_output>     # scoperta
  python -I tortura.py dispari  <cartella_dati> <cartella_output>     # conferma (da lanciare dopo aver scritto le ipotesi)
  python -I tortura.py riepilogo <cartella_dati> <cartella_output>    # confronto, Holm, effetto sulla profondita'
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tortura_lib as T  # noqa: E402

EXP = {1961: ['LAA', 'WS2'], 1962: ['NYN', 'HOU'], 1969: ['KCA', 'SE1', 'MON', 'SDN'], 1977: ['SEA', 'TOR'],
       1993: ['COL', 'FLO'], 1998: ['ARI', 'TBA']}


def yrs(a, b, par):
    return [y for y in range(a, b + 1) if y % 2 == par]


def row(id_, nome, r, extra=''):
    return dict(id=id_, nome=nome, fattore=r.fattore, OR=r.OR, lo=r.lo, hi=r.hi, p=r.p, righe=r.righe,
                eventi=r.eventi, nota=extra)


def main_row(df, y, fac, fes, id_, nome, which=None, wcol=None, extra=''):
    r = T.run_logit(df, y, fac, fes=fes, wcol=wcol)
    r = r.iloc[0] if which is None else r[r.fattore == which].iloc[0]
    return row(id_, nome, r, extra)


def prepare(data):
    s, P = T.load_pa(data)
    P, se = T.add_strength(P, s, data)
    P['month'] = P.date_dt.dt.month
    P['dh'] = P.bat_dh
    P['isday'] = (P.daynight == 'day').astype(int)
    ns = s.groupby(['season', 'starting_pitcher', 'batting_team']).size().rename('nstarts_vs')
    ks = s[['key', 'season', 'starting_pitcher', 'batting_team']].join(ns, on=['season', 'starting_pitcher', 'batting_team'])
    P = P.merge(ks[['key', 'nstarts_vs']], on='key', how='left')
    return s, P, se


def catcher_table(Q):
    X0, nfe = T.fe_design(Q, ['nd', 'season'])
    b, cov = T.fit_logit(X0, Q.r.to_numpy(), Q.g.to_numpy(), nfe)
    p = T.expit(X0 @ b)
    Q = Q.assign(p=p, v=p * (1 - p))
    Q = Q[Q.cat != '']
    g = Q.groupby('cat').agg(O=('r', 'sum'), E=('p', 'sum'), V=('v', 'sum'), N=('r', 'size'))
    g = g[g.N >= 300]
    g['logOR'] = (g.O - g.E) / g.V
    g['se'] = 1 / np.sqrt(g.V)
    return g


def run(par, data):
    t0 = time.time()
    s, P, se = prepare(data)
    print('dati pronti', len(P), f'{time.time()-t0:.0f}s')
    S = P[P.season % 2 == par]
    out = []

    def add(r):
        out.append(r)
        print(f"{r['id']} {r['nome'][:42]:42s} {r['fattore'][:26]:26s} OR {r['OR']:.3f} [{r['lo']:.3f}-{r['hi']:.3f}] p={r['p']:.3g} (righe {r['righe']}, eventi {r['eventi']}) {r['nota']}", flush=True)

    base = ('nd', 'season')
    # ---- T01-T03 forza dell'attacco e del lanciatore
    d = S[S.x_team.notna()]
    add(main_row(d, 'r', {'attacco +1 DS': 'x_team'}, base, 'T01', 'Forza dell\'attacco (stagione)'))
    d = S[S.x_pit_s.notna()]
    add(main_row(d, 'r', {'lanciatore stagione +1 DS': 'x_pit_s'}, base, 'T02', 'Forza del lanciatore, stagione'))
    d = S[S.x_pit_c.notna()]
    add(main_row(d, 'r', {'lanciatore carriera +1 DS': 'x_pit_c'}, base, 'T03', 'Forza del lanciatore, carriera'))
    # ---- T04-T05 mano
    d = S[S.same_hand.notna()]
    add(main_row(d, 'r', {'stessa mano': 'same_hand'}, base, 'T04', 'Mano: battitore come il lanciatore'))
    d = S[S.ls_z.notna()]
    add(main_row(d, 'r', {'quota stessa mano +1 DS': 'ls_z'}, base, 'T05', 'Formazione: quota stessa mano'))
    # ---- T06 monte 1969
    pre, post = yrs(1963, 1968, par), yrs(1969, 1974, par)
    d = P[P.season.isin(pre + post) & (P.bat_dh == 0) & P.league_file.isin(['A', 'N'])].copy()
    d['post'] = d.season.isin(post).astype(int)
    add(main_row(d, 'r', {'dopo il 1969': 'post'}, ('nd', 'league_file'), 'T06', 'Monte abbassato 1969', extra=f'pre {pre} post {post}'))
    # ---- T07 DH AL 1973
    pre, post = yrs(1967, 1972, par), yrs(1973, 1978, par)
    d = P[P.season.isin(pre + post) & P.league_file.isin(['A', 'N'])].copy()
    d['post'] = d.season.isin(post).astype(int)
    d['alxpost'] = ((d.league_file == 'A') & (d.post == 1)).astype(int)
    add(main_row(d, 'r', {'AL x dopo 1973': 'alxpost'}, ('nb', 'league_file', 'post'), 'T07', 'DH nella Lega Americana 1973', extra=f'pre {pre} post {post}'))
    d9 = d[d.n.isin([9, 18, 27])]
    add(main_row(d9, 'r', {'AL x dopo 1973': 'alxpost'}, ('nb', 'league_file', 'post'), 'T07r', 'DH Lega Americana 1973, solo posto del lanciatore (9/18/27)', extra=f'variante dopo le pari'))
    # ---- T08 DH universale 2022
    pre = [2016, 2018] if par == 0 else [2017, 2019, 2021]
    post = [2022, 2024] if par == 0 else [2023, 2025]
    d = P[P.season.isin(pre + post) & P.league_file.isin(['A', 'N'])].copy()
    d['post'] = d.season.isin(post).astype(int)
    d['nlxpost'] = ((d.league_file == 'N') & (d.post == 1)).astype(int)
    add(main_row(d, 'r', {'NL x dopo 2022': 'nlxpost'}, ('nb', 'league_file', 'post'), 'T08', 'DH universale 2022', extra=f'pre {pre} post {post}'))
    d9 = d[d.n.isin([9, 18, 27])]
    add(main_row(d9, 'r', {'NL x dopo 2022': 'nlxpost'}, ('nb', 'league_file', 'post'), 'T08r', 'DH universale 2022, solo posto del lanciatore (9/18/27)', extra='variante dopo le pari'))
    # ---- T09 regole 2023
    pre = [2016, 2018, 2022] if par == 0 else [2017, 2019, 2021]
    post = [2024] if par == 0 else [2023, 2025]
    d = P[P.season.isin(pre + post) & P.league_file.isin(['A', 'N'])].copy()
    d['post'] = d.season.isin(post).astype(int)
    add(main_row(d, 'r', {'dopo il 2023': 'post'}, ('nd', 'league_file'), 'T09', 'Orologio dei lanci e divieto dello shift', extra=f'pre {pre} post {post}'))
    # ---- T10 espansione
    ex = [y for y in EXP if y % 2 == par]
    d = P[P.season.isin(ex)].copy()
    d['exp_pit'] = [int(t in EXP[y]) for y, t in zip(d.season, d.pitching_team)]
    d['exp_bat'] = [int(t in EXP[y]) for y, t in zip(d.season, d.batting_team)]
    add(main_row(d, 'r', {'espansione al lancio': 'exp_pit', 'espansione al bat': 'exp_bat'}, base, 'T10', 'Squadre di espansione, primo anno', which='espansione al lancio', extra=f'stagioni {ex}'))
    r2 = T.run_logit(d, 'r', {'espansione al lancio': 'exp_pit', 'espansione al bat': 'exp_bat'}, fes=base)
    print('     (T10 anche: ' + T.fmt(r2.iloc[1]) + ' per espansione al bat)')
    # ---- T11 integrazione
    early, late = yrs(1938, 1946, par), yrs(1950, 1959, par)
    d = P[P.season.isin(early + late) & P.league_file.isin(['A', 'N'])].copy()
    d['late'] = d.season.isin(late).astype(int)
    d['nlxlate'] = ((d.league_file == 'N') & (d.late == 1)).astype(int)
    add(main_row(d, 'r', {'NL x 1950-59': 'nlxlate'}, ('nb', 'league_file', 'late'), 'T11', 'Integrazione: NL contro AL'))
    # ---- T12-T15 calendario
    d = S.assign(g2=(S.number == 2).astype(int), g1=(S.number == 1).astype(int))
    add(main_row(d, 'r', {'seconda partita': 'g2', 'prima partita (controllo)': 'g1'}, base, 'T12', 'Seconda partita del doppio incontro', which='seconda partita'))
    d = S[S.daynight.isin(['day', 'night'])]
    add(main_row(d, 'r', {'diurna dopo notturna': 'dayafternight', 'giorno': 'isday'}, base, 'T13', 'Diurna dopo notturna (attacco)', which='diurna dopo notturna'))
    add(main_row(S, 'r', {'dopo supplementari': 'afterextra'}, base, 'T14', 'Il giorno dopo i supplementari (attacco)'))
    d = S.assign(sett=(S.month >= 9).astype(int))
    add(main_row(d, 'r', {'settembre-ottobre': 'sett'}, base, 'T15', 'Settembre-ottobre'))
    # ---- T16 vantaggio
    d = S[S.n >= 10].assign(big=(S.lead >= 4).astype(int))
    add(main_row(d, 'r', {'avanti di 4+': 'big'}, base, 'T16', 'Vantaggio di 4+ punti (battitori 10+)'))
    d19 = S[S.n >= 19].assign(big=(S.lead >= 4).astype(int))
    r2 = T.run_logit(d19, 'r', {'avanti di 4+': 'big'}, fes=('nd',))
    print('     (T16 solo battitori 19+: ' + T.fmt(r2.iloc[0]) + f", {int(r2.iloc[0].righe)} turni)")
    # ---- T17 casa/trasferta
    add(main_row(S, 'r', {'lancia la casa': 'ps'}, base, 'T17', 'Squadra al lancio in casa'))
    # ---- T18 prima volta contro quella squadra
    d = S[S.is_starter == 1]
    add(main_row(d, 'r', {'prima volta in stagione': 'first_vs'}, base, 'T18', 'Prima volta del partente contro la squadra'))
    d = S[(S.is_starter == 1) & (S.nstarts_vs >= 2) & S.x_pit_s.notna()]
    add(main_row(d, 'r', {'prima volta in stagione': 'first_vs', 'qualità lanciatore': 'x_pit_s'}, base, 'T18r', 'Prima volta contro la squadra, solo chi la affronta 2+ volte e con la qualità del lanciatore', which='prima volta in stagione', extra='variante dopo le pari'))
    # ---- T19, T20 lanci
    pv = S[(S.season >= 1988) & (S.np > 0) & S.fp.isin(['S', 'B', 'X', 'H'])].copy()
    pv['deep'] = (pv.n >= 10).astype(int)
    pv['strike1'] = (pv.fp == 'S').astype(int)
    add(main_row(pv, 'strike1', {'profondo (10+)': 'deep'}, ('dh', 'season'), 'T19', 'Primo lancio strike, profondo contro iniziale'))
    pb = pv[pv.r == 1].assign(first=lambda x: (x.np == 1).astype(int))
    add(main_row(pb, 'first', {'profondo (10+)': 'deep'}, ('dh', 'season'), 'T20', 'Rottura al primo lancio, profondo contro iniziale'))
    pbn = pb[~pb.k.isin(['base_su_ball', 'base_intenzionale'])]
    add(main_row(pbn, 'first', {'profondo (10+)': 'deep'}, ('dh', 'season'), 'T20r', 'Rottura al primo lancio, escluse le basi su ball', extra='variante dopo le pari'))
    # ---- T21 leadoff
    d = S[S.n <= 8].assign(lx=lambda x: (x.n == 1) * (x.season - 1960) / 10)
    add(main_row(d, 'r', {'leadoff x decennio': 'lx'}, base, 'T21', 'Premio del leadoff per decennio'))
    # ---- T22 sfilacciamento
    Bk = S[S.r == 1][['key', 'g', 'season', 'n', 'bat_dh', 'k']].merge(se[['key', 'nxt_n', 'nxt_r']], on='key', how='left')
    Bk = Bk[Bk.nxt_n >= 1]
    ones = Bk.assign(y=1, w=Bk.nxt_r)
    zeros = Bk.assign(y=0, w=Bk.nxt_n - Bk.nxt_r)
    W = pd.concat([ones, zeros])
    W = W[W.w > 0].assign(deep=lambda x: (x.n >= 19).astype(int))
    add(main_row(W, 'y', {'rottura al 19+': 'deep'}, ('season', 'k', 'bat_dh'), 'T22', 'Dopo la prima rottura: arrivi nei 3 turni dopo', wcol='w',
                 extra=f'rotture tardive con dati {int((Bk.n>=19).sum())}'))
    # ---- T23 errori
    Bk2 = S[S.r == 1].copy()
    Bk2['err'] = (Bk2.k == 'errore').astype(int)
    Bk2['tr'] = (Bk2.season - 1960) / 10
    Bk2['nbg'] = np.where(Bk2.n <= 9, 0, np.where(Bk2.n <= 18, 1, 2))
    add(main_row(Bk2, 'err', {'per decennio': 'tr'}, ('dh', 'nbg'), 'T23', 'Errori tra le rotture, tendenza per decennio'))
    # ---- T24 ricevitore
    ct = catcher_table(S)
    chi = float(((ct.logOR / ct.se) ** 2).sum())
    pchi = float(stats.chi2.sf(chi, len(ct)))
    res = dict(id='T24', nome='Ricevitore: effetti che si ripetono', fattore='eterogeneità (pari)', OR=np.nan, lo=np.nan, hi=np.nan,
               p=pchi, righe=int(ct.N.sum()), eventi=int(ct.O.sum()), nota=f'ricevitori {len(ct)}, chi2 {chi:.0f}')
    if par == 1:
        ev = catcher_table(P[P.season % 2 == 0])
        j = ev.join(ct, lsuffix='_e', rsuffix='_o', how='inner')
        # regressione pesata dell'effetto nelle dispari su quello nelle pari (coefficiente = quota che si ripete)
        wgt = 1 / j.se_o ** 2
        x, yv = j.logOR_e.to_numpy(), j.logOR_o.to_numpy()
        sw = wgt.to_numpy()
        xm, ym = np.average(x, weights=sw), np.average(yv, weights=sw)
        slope = np.sum(sw * (x - xm) * (yv - ym)) / np.sum(sw * (x - xm) ** 2)
        resid = yv - ym - slope * (x - xm)
        se_s = np.sqrt(np.sum(sw ** 2 * (x - xm) ** 2 * resid ** 2) / np.sum(sw * (x - xm) ** 2) ** 2)   # robusto (sandwich)
        sp = stats.spearmanr(j.logOR_e, j.logOR_o)
        res.update(fattore='pendenza dispari su pari', OR=float(slope), lo=float(slope - 1.96 * se_s), hi=float(slope + 1.96 * se_s),
                   p=float(2 * stats.norm.sf(abs(slope / se_s))), righe=int(j.N_e.sum() + j.N_o.sum()),
                   nota=f'ricevitori in comune {len(j)}; Spearman {sp.statistic:.2f} (p={sp.pvalue:.2g}); eterogeneità dispari p={pchi:.2g}')
    add(res)
    # ---- T25 temperatura
    d = S[S.temp.notna() & (S.temp > 0)].assign(t10=lambda x: (x.temp - 70) / 10)
    add(main_row(d, 'r', {'+10 gradi F': 't10'}, base, 'T25', 'Temperatura'))
    pd.DataFrame(out).to_csv(os.path.join(sys.argv[3], 'tortura_' + ('pari' if par == 0 else 'dispari') + '.csv'), index=False)
    print(f'fatto in {time.time()-t0:.0f}s')


def riepilogo(outdir):
    a = pd.read_csv(os.path.join(outdir, 'tortura_pari.csv')).set_index('id')
    b = pd.read_csv(os.path.join(outdir, 'tortura_dispari.csv')).set_index('id')
    j = a.join(b, lsuffix='_p', rsuffix='_d')
    j['stesso_segno'] = np.sign(np.log(j.OR_p)) == np.sign(np.log(j.OR_d))
    j.loc['T24', 'stesso_segno'] = True
    j['sopravvive'] = (j.p_p < 0.05) & (j.p_d < 0.05) & j.stesso_segno
    j['holm_dispari'] = T.holm(j.p_d.to_numpy())
    cols = ['nome_p', 'OR_p', 'lo_p', 'hi_p', 'p_p', 'OR_d', 'lo_d', 'hi_d', 'p_d', 'stesso_segno', 'sopravvive', 'holm_dispari']
    j.to_csv(os.path.join(outdir, 'tortura_risultati.csv'))
    pd.set_option('display.width', 250)
    print(j[cols].round(4).to_string())
    print('sopravvissute:', list(j.index[j.sopravvive]), '| solo nelle dispari:', list(j.index[(j.p_d < 0.05) & ~j.sopravvive]))
    # effetto sulla quota di serie che arrivano a 18 battitori (hazard di base: tutti i lati)
    hz = pd.read_csv(os.path.join(outdir, 'come_cala_hazard.csv'))
    h = hz[hz.gruppo == 'tutti'].set_index('n').hazard.fillna(0).to_numpy()[:18]
    for i in j.index[j.sopravvive | (j.p_d < 0.05)]:
        if i in ('T19', 'T20', 'T22', 'T23', 'T24'):
            continue
        for lab, o in (('pari', j.OR_p[i]), ('dispari', j.OR_d[i])):
            h2 = o * h / (1 - h + o * h)
            print(f'  {i} {lab}: OR {o:.3f} -> quota che arriva a 18 battitori x{np.prod(1 - h2) / np.prod(1 - h):.2f}; a 9: x{np.prod(1 - h2[:9]) / np.prod(1 - h[:9]):.2f}')


if __name__ == '__main__':
    mode, data, outdir = sys.argv[1:4]
    if mode == 'pari':
        run(0, data)
    elif mode == 'dispari':
        run(1, data)
    else:
        riepilogo(outdir)
