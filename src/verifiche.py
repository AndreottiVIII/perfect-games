"""Parte 1 della tortura: verifica delle tre chicche "da verificare".

Uso: python -I verifiche.py <cartella_dati> <cartella_output>

V1: il gruppo 2010-12 (statistica di scansione sulle finestre di 3 stagioni; tutta la curva nel 2010-12).
V2: nelle serie lunghe le rotture sono meno spesso basi su ball, anche controllando slot, ruolo, DH, stagione e lanciatore?
V3: stadi, stagioni pari (scoperta) contro dispari (conferma).
Stampa un riepilogo corto; i testi sono in verifiche.md (scritto a mano).
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tortura_lib as T  # noqa: E402
from ca_common import load, risk_table  # noqa: E402
from come_cala import null_matrices, expected_hazard  # noqa: E402

rng = np.random.default_rng(20251024)
pd.set_option('display.width', 200)


def window_max(counts, w=3):
    c = np.cumsum(np.concatenate([np.zeros(counts.shape[:-1] + (1,)), counts], axis=-1), axis=-1)
    return (c[..., w:] - c[..., :-w]).max(axis=-1)


def scan_prob(weights, total, obs_max, sims=200000, poisson=False):
    w = np.asarray(weights, float)
    w = w / w.sum()
    if poisson:
        c = rng.poisson(w * total, size=(sims, len(w)))
    else:
        c = rng.multinomial(total, w, size=sims)
    m = window_max(c)
    return float((m >= obs_max).mean())


def curve_vs_null(sub, P2):
    t = risk_table(sub)
    h0, expb, ar = expected_hazard(sub, P2)
    S0 = np.cumprod(1 - np.nan_to_num(h0))
    h = t.hazard.fillna(0).to_numpy()
    arr = t.at_risk.to_numpy().astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        gw = np.cumsum(np.where(arr > t.broken.to_numpy(), h / (arr * (1 - h)), 0))
    se = np.sqrt(gw)
    ratio = t.survival.to_numpy() / S0
    return t, S0, ratio, se, expb


def v1(d, tally):
    print('\n===== V1: cluster 2010-12 =====')
    d = d.reset_index(drop=True)
    p1, p2 = null_matrices(d, tally)
    q = np.prod(1 - p2, axis=1)               # probabilita' nulla (N2) di restare perfetti per 27 battitori
    d['q'] = q
    perf = d[(d.batters_retired >= 27) & (d.reach == 0)]
    seasons = np.arange(1908, 2026)
    Es = d.groupby('season').q.sum().reindex(seasons, fill_value=0).to_numpy()
    obs = perf.groupby('season').size().reindex(seasons, fill_value=0).to_numpy()
    print('perfette', len(perf), '| attese N2 in totale', round(Es.sum(), 2), '| rapporto', round(len(perf) / Es.sum(), 2))
    i10 = list(seasons).index(2010)
    for lab, o, tot in (('con Galarraga', obs, 21), ('senza Galarraga', obs - np.eye(len(seasons))[i10] * 1, 20)):
        mx = window_max(o.astype(float))
        print(f'  {lab}: finestra di 3 stagioni con piu\' perfette = {int(mx)}; 2010-12 = {int(o[i10:i10+3].sum())}')
    sides = d.groupby('season').size().reindex(seasons).to_numpy()
    res = {}
    for lab, o_max, tot in (('con Galarraga', 6, 21), ('senza Galarraga', 5, 20)):
        for wl, w in (('peso N2', Es), ('peso lati (storia piatta)', sides)):
            res[(lab, wl, 'multinomiale')] = scan_prob(w, tot, o_max)
            res[(lab, wl, 'poisson')] = scan_prob(w * tot / w.sum(), tot, o_max, poisson=True)
    # pesi dalla quota osservata di serie lunghe (un'altra definizione di "era favorevole")
    for k in (12, 15, 18):
        wk = d[d.batters_retired >= k].groupby('season').size().reindex(seasons, fill_value=0).to_numpy().astype(float)
        wk = wk + 0.5                                   # piccolo smorzamento per le stagioni senza casi
        res[('con Galarraga', f'peso serie >= {k} ({int(wk.sum())} lati)', 'multinomiale')] = scan_prob(wk, 21, 6)
        res[('senza Galarraga', f'peso serie >= {k}', 'multinomiale')] = scan_prob(wk, 20, 5)
    for k, v in res.items():
        print('  P(finestra >= osservato)', k, f'{v:.4f}')
    # finestre di lunghezza libera (1..5 stagioni): statistica = il p piu' piccolo tra le lunghezze
    for lab, tot, o in (('con Galarraga', 21, obs.astype(float)), ('senza Galarraga', 20, obs - np.eye(len(seasons))[i10] * 1)):
        wts = Es / Es.sum()
        sims = 100000
        c = rng.multinomial(tot, wts, size=sims)
        lens = (1, 2, 3, 4, 5)
        dist = {w_: np.sort(window_max(c.astype(float), w_)) for w_ in lens}
        def pw_(val, w_):
            return 1 - np.searchsorted(dist[w_], val, side='left') / sims
        pobs = min(pw_(window_max(o, w_), w_) for w_ in lens)
        best = [(w_, int(window_max(o, w_)), round(pw_(window_max(o, w_), w_), 4)) for w_ in lens]
        pmin = np.minimum.reduce([1 - np.searchsorted(dist[w_], window_max(c.astype(float), w_), side='left') / sims for w_ in lens])
        print(f'  {lab}: finestre da 1 a 5 stagioni (lunghezza, massimo osservato, p della singola): {best}; p che il minimo tra le lunghezze sia così piccolo: {(pmin <= pobs).mean():.4f}')
    # probabilita' del solo triennio 2010-12 (non scelto a posteriori), per riferimento
    pw = Es[i10:i10 + 3].sum() / Es.sum()
    print(f'  attese N2 nel 2010-12: {Es[i10:i10+3].sum():.2f} su {Es.sum():.1f} ({pw:.1%}); P(>=6 delle 21 in quelle 3 stagioni, scelte prima) = {stats.binom.sf(5, 21, pw):.5f}')
    # tutta la curva nel 2010-12
    msk = d.season.between(2010, 2012).to_numpy()
    print('\n  Tutta la curva nel 2010-12 (S/S0 N2, intervallo 95%):')
    for lab, m in (('2010-12', msk), ('tutto il resto', ~msk), ('2000-09', d.season.between(2000, 2009).to_numpy()),
                   ('2013-25', (d.season >= 2013).to_numpy())):
        sub = d[m].reset_index(drop=True)
        t, S0, ratio, se, expb = curve_vs_null(sub, p2[m])
        txt = []
        for n in (9, 12, 15, 18):
            lo, hi = ratio[n - 1] * np.exp(-1.96 * se[n - 1]), ratio[n - 1] * np.exp(1.96 * se[n - 1])
            txt.append(f'n={n}: {ratio[n-1]:.2f} [{lo:.2f}-{hi:.2f}] (S reale 1/{1/t.survival[n-1]:.0f}, a rischio {int(t.at_risk[n-1])})')
        oe = t.broken[:17].sum() / expb[:17].sum()
        print(f'   {lab:15s} lati {len(sub):6d}; rotture/attese batt. 1-17 = {oe:.3f}; ' + '; '.join(txt))
    # 2010-12 contro tutte le altre finestre di 3 stagioni: rotture/attese nei battitori 1-17 e 9-17
    rows = []
    for y in range(1908, 2024):
        m = d.season.between(y, y + 2).to_numpy()
        sub = d[m].reset_index(drop=True)
        t, S0, ratio, se, expb = curve_vs_null(sub, p2[m])
        rows.append(dict(y=y, oe=t.broken[:17].sum() / expb[:17].sum(), oe9=t.broken[8:17].sum() / expb[8:17].sum(),
                         n=int(t.broken[:17].sum()), n9=int(t.broken[8:17].sum()), r12=ratio[11], r15=ratio[14]))
    w = pd.DataFrame(rows)
    for col in ('oe', 'oe9', 'r12', 'r15'):
        r = int(w[col].rank(ascending=True)[w.y == 2010].iloc[0])
        print(f"   finestra 2010-12 per {col}: valore {w[col][w.y==2010].iloc[0]:.3f}, posto {r} su {len(w)} (1 = il piu' basso; in alto = sopra il modello nullo = migliore per il lanciatore: posto {len(w)+1-r} dall'alto)")
    print('   finestre piu\' basse in rotture/attese (battitori 1-17):', w.sort_values('oe').head(5)[['y', 'oe']].round(3).to_dict('records'))
    # raw: quota dei lati che raggiungono 9/15/18
    for lab, m in (('2010-12', msk), ('2000-09', d.season.between(2000, 2009).to_numpy()), ('2013-25', (d.season >= 2013).to_numpy())):
        sub = d[m]
        print(f'   {lab}: lati {len(sub)}; quota con >=9: {(sub.batters_retired>=9).mean():.4f}, >=15: {(sub.batters_retired>=15).mean()*1000:.2f} per mille, >=18: {(sub.batters_retired>=18).mean()*10000:.2f} per 10 mila')
    return Es


def v2(P, s):
    print('\n===== V2: basi su ball nelle rotture tardive =====')
    B = P[P.r == 1].copy()
    B['walk'] = B.k.isin(['base_su_ball', 'base_intenzionale']).astype(int)
    B['late'] = (B.n >= 19).astype(int)
    B['mid'] = B.n.between(10, 18).astype(int)
    B['slotc'] = B.bs.fillna(0).astype(int)
    B['role'] = np.where(B.bp == 11, 2, np.where(B.bp == 1, 1, 0))
    B['bbl'] = np.log(B.bbshare / (1 - B.bbshare))
    B['bbl'] = B.bbl - B.bbl.mean()
    B['dh'] = B.bat_dh
    B['g'] = B.g.astype(str)
    B['all1'] = 1
    print('rotture', len(B), '| quota basi su ball: 1-9 %.3f, 10-18 %.3f, 19-27 %.3f (n=%d)' % (
        B[B.n <= 9].walk.mean(), B[B.mid == 1].walk.mean(), B[B.late == 1].walk.mean(), B.late.sum()))
    steps = [('grezzo', ('all1',), []), ('+ slot, ruolo (PH/lanciatore), DH', ('slotc', 'role', 'dh'), []),
             ('+ stagione', ('slotc', 'role', 'dh', 'season'), []),
             ('+ tendenza del lanciatore a regalare basi', ('slotc', 'role', 'dh', 'season'), ['bbl']),
             ]
    for lab, fes, extra in steps:
        fac = {'medio (10-18)': 'mid', 'tardivo (19-27)': 'late'}
        for e in extra:
            fac[e] = e
        r = T.run_logit(B, 'walk', fac, fes=fes)
        print(f'  [{lab}]', ' | '.join(f"{x.fattore}: {T.fmt(x)}" for x in r.itertuples()))
    # per epoca
    for lab, m in (('1908-45', B.season < 1946), ('1946-92', B.season.between(1946, 1992)), ('1993+', B.season >= 1993)):
        b = B[m]
        r = T.run_logit(b, 'walk', {'tardivo (19-27)': 'late', 'medio': 'mid', 'bbl': 'bbl'}, fes=('slotc', 'role', 'dh', 'season'))
        print(f'  epoca {lab} (rotture {len(b)}, tardive {int(b.late.sum())}):', ' | '.join(f"{x.fattore}: {T.fmt(x)}" for x in r.itertuples()))
    for lab, m in (('pari', B.season % 2 == 0), ('dispari', B.season % 2 == 1)):
        b = B[m]
        r = T.run_logit(b, 'walk', {'tardivo (19-27)': 'late', 'medio': 'mid', 'bbl': 'bbl'}, fes=('slotc', 'role', 'dh', 'season'))
        print(f'  stagioni {lab} (rotture {len(b)}, tardive {int(b.late.sum())}, modello completo):', ' | '.join(f"{x.fattore}: {T.fmt(x)}" for x in r.itertuples()))
    # sensibilita': solo battitori non PH e non lanciatori
    b = B[B.role == 0]
    r = T.run_logit(b, 'walk', {'tardivo (19-27)': 'late', 'medio': 'mid', 'bbl': 'bbl'}, fes=('slotc', 'dh', 'season'))
    print('  solo battitori normali:', ' | '.join(f"{x.fattore}: {T.fmt(x)}" for x in r.itertuples()), f'(rotture {len(b)}, tardive {int(b.late.sum())})')
    # quanti avrebbero dovuto essere basi su ball in base alla sola tendenza del lanciatore (somma delle quote attese)
    late = B[B.late == 1]
    print('  tardive: basi su ball osservate %d su %d (%.1f%%); attese dal solo lanciatore (bbshare medio) %.1f%%' % (
        late.walk.sum(), len(late), 100 * late.walk.mean(), 100 * late.bbshare.mean()))
    print('  tutte le rotture: bbshare medio %.1f%%, osservato %.1f%%' % (100 * B.bbshare.mean(), 100 * B.walk.mean()))
    # quota di PH tra le rotture tardive per tipo
    print('  ruolo del battitore che rompe: tardive PH %.1f%%, lanciatore %.1f%%; resto PH %.1f%%' % (
        100 * (late.role == 2).mean(), 100 * (late.role == 1).mean(), 100 * (B[B.late == 0].role == 2).mean()))
    print('  quota basi su ball per ruolo:', B.groupby('role').walk.agg(['mean', 'size']).round(3).to_dict('index'))


def site_table(P, sites):
    X0, nfe = T.fe_design(P, ['nd', 'season'])
    b, cov = T.fit_logit(X0, P.r.to_numpy(), P.g.to_numpy(), nfe)
    p = T.expit(X0 @ b)
    P = P.assign(p=p, v=p * (1 - p))
    g = P.groupby('site').agg(O=('r', 'sum'), E=('p', 'sum'), V=('v', 'sum'), N=('r', 'size'))
    g['logOR'] = (g.O - g.E) / g.V
    g['se'] = 1 / np.sqrt(g.V)
    g['z'] = g.logOR / g.se
    g['p'] = 2 * stats.norm.sf(np.abs(g.z))
    return g


def v3(P, outdir):
    print('\n===== V3: stadi, pari (scoperta) contro dispari (conferma) =====')
    ev = site_table(P[P.season % 2 == 0], None)
    od = site_table(P[P.season % 2 == 1], None)
    j = ev.join(od, lsuffix='_p', rsuffix='_d', how='outer')
    names = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stadi_nomi.csv')).set_index('site').nome
    j['nome'] = names.reindex(j.index)
    j.to_csv(os.path.join(outdir, 'verifiche_stadi.csv'))
    keep = (j.V_p >= 15) & (j.V_d >= 15)
    k = j[keep].copy()
    print('stadi con abbastanza dati in entrambi gli insiemi (varianza >= 15):', len(k), 'di', len(j))
    for nm in ('DEN02', 'BOS07', 'ARL02', 'NYC14', 'LOS03', 'TOR01'):
        if nm in j.index:
            r = j.loc[nm]
            f = lambda lo, se: f'OR {np.exp(lo):.3f} [{np.exp(lo-1.96*se):.3f}-{np.exp(lo+1.96*se):.3f}]'
            print(f'  {nm} {r.nome}: pari {f(r.logOR_p, r.se_p)} p={r.p_p:.3g} (O {r.O_p:.0f} E {r.E_p:.0f}) | dispari {f(r.logOR_d, r.se_d)} p={r.p_d:.3g} (O {r.O_d:.0f} E {r.E_d:.0f})')
    for lab, col in (('pari', 'p_p'), ('dispari', 'p_d')):
        chi = ((k['logOR_' + col[-1]] / k['se_' + col[-1]]) ** 2).sum()
        print(f'  eterogeneita\' degli stadi nelle {lab}: chi2 {chi:.0f} su {len(k)} gradi, p={stats.chi2.sf(chi, len(k)):.2g}')
    sig = k[k.p_p < 0.05]
    rep = sig[(np.sign(sig.logOR_p) == np.sign(sig.logOR_d)) & (sig.p_d < 0.05)]
    print(f'  stadi con p<0,05 nelle pari: {len(sig)}; di questi si ripetono nelle dispari (stesso segno, p<0,05): {len(rep)}')
    bon = k[k.p_p < 0.05 / len(k)]
    print(f'  soglia di Bonferroni nelle pari ({0.05/len(k):.5f}): {len(bon)} stadi; ripetuti: {int(((np.sign(bon.logOR_p)==np.sign(bon.logOR_d)) & (bon.p_d<0.05)).sum())}')
    for nm, r in bon.iterrows():
        print(f'    Bonferroni {nm} {r.nome}: pari OR {np.exp(r.logOR_p):.3f} (p={r.p_p:.2g}) -> dispari OR {np.exp(r.logOR_d):.3f} (p={r.p_d:.2g})')
    r_ = stats.spearmanr(k.logOR_p, k.logOR_d)
    w = 1 / (k.se_p ** 2 + k.se_d ** 2)
    print(f'  correlazione tra stime pari e dispari: Spearman {r_.statistic:.2f} (p={r_.pvalue:.2g}), n={len(k)}')
    print('  stadi ripetuti (pari->dispari):')
    for nm, r in rep.sort_values('logOR_p').iterrows():
        print(f'    {nm} {r.nome}: pari OR {np.exp(r.logOR_p):.2f} (p={r.p_p:.2g}), dispari OR {np.exp(r.logOR_d):.2f} (p={r.p_d:.2g}), turni {r.N_p+r.N_d:.0f}')
    return j


def main():
    data, outdir = sys.argv[1:3]
    d = load(os.path.join(data, 'streaks.csv'))
    v1(d, os.path.join(data, 'pa_tally.csv'))
    s, P = T.load_pa(data)
    P, se = T.add_strength(P, s, data)
    v2(P, s)
    v3(P, outdir)


if __name__ == '__main__':
    main()
