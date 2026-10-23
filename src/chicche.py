"""Parte B: cose sorprendenti sulle partite perfette e sulle lunghe serie perfette ("chicche").

Uso: python -I chicche.py <streaks.csv> <cartella_output>
Stampa un riepilogo corto (i testi sono in chicche.md, scritto a mano) e salva
output/chicche_perfette.csv (le 21 partite con i campi extra) e output/chicche_parchi.csv.

Attesi per ogni gruppo (stadio, arbitro, mese...): quota di lati con almeno k eliminati nella
stessa stagione e con lo stesso tipo di formazione (DH si/no), sommata sui lati del gruppo.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_common import load  # noqa: E402

pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 30)
rng = np.random.default_rng(1)


def add_expected(d, thr):
    d = d.copy()
    d['ev'] = (d.batters_retired >= thr).astype(int)
    d['E'] = d.groupby(['season', 'bat_dh']).ev.transform('mean')
    return d


def obs_exp(d, key, thr):
    x = add_expected(d, thr).groupby(key).agg(n=('ev', 'size'), O=('ev', 'sum'), E=('E', 'sum'))
    x['ratio'] = x.O / x.E
    x['z'] = (x.O - x.E) / np.sqrt(x.E)
    p = [stats.poisson.sf(o - 1, e) if o >= e else stats.poisson.cdf(o, e) for o, e in zip(x.O, x.E)]
    x['p'] = np.minimum(1, 2 * np.array(p))
    return x


def heterogeneity(x, minE=3):
    x = x[x.E >= minE]
    chi = ((x.O - x.E) ** 2 / x.E).sum()
    return len(x), chi, stats.chi2.sf(chi, len(x))


def main():
    src, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    d = load(src)
    for c in ('temp', 'windspeed', 'attendance'):
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['date_dt'] = pd.to_datetime(d.date)
    d['month'] = d.date_dt.dt.month
    d['weekday'] = d.date_dt.dt.day_of_week
    d['perfect'] = ((d.batters_retired >= 27) & (d.reach == 0)).astype(int)
    off = d[(d.perfect == 1) & d.override_reason.isna()]          # le 20 ufficiali nei dati
    P = d[d.perfect == 1]                                          # 21, con Galarraga
    P.drop(columns=['date_dt']).to_csv(os.path.join(outdir, 'chicche_perfette.csv'), index=False)
    print('perfette:', len(P), 'di cui ufficiali', len(off))

    # ---- 1. pinch hitter al 27esimo battitore
    near = d[(d.reach == 1) & (d.batters_retired == 26)]
    ph_p = int((off.last_pos == 11).sum())
    ph_n = int((near.breaker_pos == 11).sum())
    print(f'27esimo battitore pinch hitter: perfette {ph_p}/{len(off)}; mancate {ph_n}/{len(near)}; insieme {ph_p+ph_n}/{len(off)+len(near)}')
    print('  mancate: eventi', near.first_runner_event.value_counts().to_dict(), '| hits_allowed==0:', int((near.hits_allowed == 0).sum()),
          '| lanciatori in campo >1:', int((near.pitchers_before_break > 1).sum()))
    near_ph = near[near.breaker_pos == 11]
    print(f'  PH arrivati in base {len(near_ph)}/{(len(near_ph)+ph_p)} = {len(near_ph)/(len(near_ph)+ph_p):.0%}; '
          f'non PH {len(near)-len(near_ph)}/{len(near)-len(near_ph)+len(off)-ph_p}')
    # quota di pinch hitter tra i battitori n. 9, 18, 27 (retirati o arrivati in base)
    for n in (9, 18, 27):
        ret = d[(d.batters_retired == n)]            # l'n-esimo e' l'ultimo eliminato
        bro = d[(d.reach == 1) & (d.batters_retired == n - 1)]   # l'n-esimo e' quello che rompe
        ph_ret = int((ret.last_pos == 11).sum())
        ph_bro = int((bro.breaker_pos == 11).sum())
        tot = len(ret) + len(bro)
        print(f'  battitore n.{n}: pinch hitter {ph_ret+ph_bro}/{tot} = {(ph_ret+ph_bro)/tot:.1%}')
    f = stats.fisher_exact([[ph_n, len(near) - ph_n], [ph_p, len(off) - ph_p]])
    print('  fisher PH rompe vs non rompe p=%.2f' % f[1])

    # ---- 2. stadi
    tab = obs_exp(d, 'site', 9)
    tab = tab[tab.E >= 20]
    nk, chi, p = heterogeneity(tab, 20)
    tab.sort_values('z').to_csv(os.path.join(outdir, 'chicche_parchi.csv'))
    print(f'stadi (>=9 eliminati): {nk} con E>=20, chi2={chi:.0f} p={p:.2g}; soglia Bonferroni p<{0.05/nk:.4f}')
    print(tab.sort_values('z').head(4).round(3).to_string())
    print(tab.sort_values('z').tail(4).round(3).to_string())
    for thr in (12, 15, 18):
        t = obs_exp(d, 'site', thr).loc[['DEN02', 'BOS07', 'LOS03']]
        print(f' soglia {thr}:', {k: (int(r.O), round(r.E, 1)) for k, r in t.iterrows()})
    co = d[d.site == 'DEN02']
    rest = d[(d.season >= 1993) & (d.site != 'DEN02')]
    for lab, s in (('Coors', co), ('altri stadi 1993+', rest)):
        trials = (s.batters_retired + s.reach).sum()
        print(f'  {lab}: lati {len(s)}, rotture per battitore (prima della fine della serie) {s.reach.sum()/trials:.3f}')
    fb = d[d.site == 'BOS07']
    print(f"  Fenway: stagioni {fb.season.min()}-{fb.season.max()}, lati {len(fb)}")
    # stadi con piu' perfette e quanto sarebbe strano
    pc = P.site.value_counts()
    print('perfette per stadio:', pc.head(4).to_dict())
    share = d.site.value_counts(normalize=True)
    mx = [pd.Series(rng.choice(share.index.to_numpy(), size=len(P), p=share.to_numpy())).value_counts().iloc[0] for _ in range(5000)]
    print('  prob. che un solo stadio abbia >=3 delle 21 per puro caso:', np.mean(np.array(mx) >= 3))

    # ---- 3. arbitri, giorno/notte, mese, meteo
    u = d[d.umphome.notna() & ~d.umphome.isin(['', '(none)'])]
    for thr in (12, 15):
        x = obs_exp(u, 'umphome', thr)
        nk, chi, p = heterogeneity(x, 3)
        print(f'arbitri soglia {thr}: {nk} arbitri, chi2={chi:.0f}, p={p:.2f}; piu\' estremo p={x[x.E>=3].p.min():.4f} (soglia Bonferroni {0.05/nk:.4f})')
    for key in ('daynight', 'month', 'weekday'):
        x = obs_exp(d[d[key].notna() & (d[key] != '')], key, 15)
        nk, chi, p = heterogeneity(x, 3)
        print(f'{key} (>=15): chi2 p={p:.2f}; ' + ' '.join(f'{i}:{r.ratio:.2f}' for i, r in x.iterrows()))
    t = d[(d.season >= 1990) & d.temp.notna() & (d.temp > 0)].copy()
    t['tb'] = pd.cut(t.temp, [0, 60, 70, 80, 130])
    x = obs_exp(t, 'tb', 15)
    print('temperatura (>=15):', ' '.join(f'{i}:{r.ratio:.2f}(p={r.p:.2f})' for i, r in x.iterrows()))
    t = d[d.attendance.notna() & (d.attendance > 0)].copy()
    t['ab'] = pd.qcut(t.attendance, 6)
    x = obs_exp(t, 'ab', 15)
    print('pubblico (sestili, >=15): ' + ' '.join(f'{r.ratio:.2f}' for _, r in x.iterrows()), 'chi2 p=%.2f' % heterogeneity(x, 3)[2])
    w = d[(d.season >= 1990) & (d.winddir != 'unknown') & d.winddir.notna()]
    x = obs_exp(w, 'winddir', 15)
    print('vento (direzione, >=15): chi2 p=%.2f' % heterogeneity(x, 3)[2])
    for key in ('precip', 'sky', 'fieldcond'):
        x = obs_exp(d[(d.season >= 1990) & (d[key] != 'unknown') & d[key].notna()], key, 15)
        print(f'{key} (>=15): chi2 p={heterogeneity(x, 1)[2]:.2f}')

    # ---- 4. lanci e strikeout nelle partite perfette
    v = d[(d.pitches_all_valid == 1) & (d.season >= 1988)]
    base = v.groupby('season').apply(lambda g: g.pitches_retired.sum() / g.batters_retired.sum(), include_groups=False)
    Pv = off[(off.pitches_all_valid == 1) & (off.season >= 1988)].copy()
    Pv['pp'] = Pv.pitches_retired / 27
    Pv['b'] = Pv.season.map(base)
    tt = stats.ttest_1samp(Pv.pp - Pv.b, 0)
    print(f'lanci (1988+, {len(Pv)} perfette): totale medio {Pv.pitches_retired.mean():.1f} (min {Pv.pitches_retired.min()}, max {Pv.pitches_retired.max()}); '
          f'per battitore {Pv.pp.mean():.2f} contro {Pv.b.mean():.2f} nelle altre serie; t p={tt.pvalue:.2f}')
    ks = off.copy()
    kb = d.groupby('season').apply(lambda g: g.ks_retired.sum() / g.batters_retired.sum(), include_groups=False)
    ks['kexp'] = 27 * ks.season.map(kb)
    t2 = stats.ttest_1samp(ks.ks_retired - ks.kexp, 0)
    print(f'strikeout nelle {len(ks)} perfette: media {ks.ks_retired.mean():.1f} contro {ks.kexp.mean():.1f} attesi (stessa stagione); '
          f'min {ks.ks_retired.min()} max {ks.ks_retired.max()}; t p={t2.pvalue:.4f}')
    print('  strikeout come ultimo out:', int(off.last_event.str.startswith('K').sum()), 'su', len(off),
          '| ultimo out per tipo (conteggio finale 2-2 ecc.):', off.last_count.value_counts().to_dict())
    print('  lanci sull\'ultimo out (valide):', off.last_pa_pitches.dropna().astype(int).tolist())

    # ---- 5. specialisti: lanciatori con molte serie lunghe
    for thr, ks_ in ((15, (2, 3, 4, 5)), (18, (2, 3, 4))):
        a = add_expected(d, thr)
        g = a.groupby('starting_pitcher').agg(O=('ev', 'sum'), E=('E', 'sum'), starts=('ev', 'size'))
        print(f'lanciatori con serie >= {thr}:', {k: (int((g.O >= k).sum()), round(sum(stats.poisson.sf(k - 1, e) for e in g.E), 1)) for k in ks_}, '(osservati, attesi se tutti uguali)')
        if thr == 15:
            print(g.sort_values('O', ascending=False).head(8).round(2).to_string())

    # ---- 6. squadre che subiscono
    vic = P.batting_team.value_counts()
    sh = d.batting_team.value_counts(normalize=True)
    print('vittime delle 21:', vic.head(4).to_dict(), '| TBA quota lati %.3f attese %.2f' % (sh['TBA'], 21 * sh['TBA']))
    mx = [pd.Series(rng.choice(sh.index.to_numpy(), size=len(P), p=sh.to_numpy())).value_counts().iloc[0] for _ in range(5000)]
    print('  prob. che una sola squadra abbia >=3 delle 21 per caso:', np.mean(np.array(mx) >= 3))
    print('  prob. che una squadra QUALSIASI abbia >=3 (dato che e\' TBA la sola): vedi sopra; P(TBA>=3 | 21, %.3f)=%.4f' % (sh['TBA'], stats.binom.sf(2, 21, sh['TBA'])))
    # anni
    byy = P.groupby('season').size()
    print('perfette per anno con piu\' di una:', byy[byy > 1].to_dict())
    # quanto e' strano un gruppo di 6 in tre stagioni consecutive? simulazione: 21 partite sparse sulle stagioni
    # con il peso atteso dal modello nullo N2 (che tiene conto del decennio e del numero di lati)
    dec = pd.read_csv(os.path.join(outdir, 'come_cala_null_decenni.csv')).set_index('decade')
    ss = d.groupby('season').size()
    w = np.array([ss[s_] * dec.loc[s_ // 10 * 10, 'S27_N2'] for s_ in ss.index], float)
    w /= w.sum()
    seasons = ss.index.to_numpy()
    cnt = []
    for _ in range(20000):
        draw = rng.choice(len(seasons), size=len(P), p=w)
        c = np.bincount(draw, minlength=len(seasons))
        cnt.append(max(c[i:i + 3].sum() for i in range(len(c) - 2)))
    cnt = np.array(cnt)
    print('  simulazione: prob. che una qualsiasi finestra di 3 stagioni contenga >=6 delle 21: %.4f ; >=5: %.4f' % ((cnt >= 6).mean(), (cnt >= 5).mean()))
    sides_1012 = len(d[d.season.between(2010, 2012)])
    print('  lati 2010-12:', sides_1012, 'quota', sides_1012 / len(d), '| 6 perfette in 3 anni, attese a media storica', 21 * sides_1012 / len(d))

    # ---- 7. quando muore senza un colpo
    L = d[(d.batters_retired >= 18) & (d.reach == 1)]
    nonhit = L.first_runner_event.isin(['base_su_ball', 'base_intenzionale', 'colpito', 'errore', 'interferenza_ricevitore', 'scelta_difensiva'])
    comp = L.game_status == 'completa'
    s = L[nonhit & comp]
    print(f'rotte da >=18 eliminati senza un colpo (partita completa): {len(s)}; poi no-hitter (0 valide subite): {(s.hits_allowed==0).sum()}')
    s = L[~nonhit & comp]
    print(f'rotte con un colpo: {len(s)}; no-hitter: {(s.hits_allowed==0).sum()}')
    s26 = near[near.game_status == 'completa']
    print('mancate al 27esimo: per tipo ', near.first_runner_event.value_counts().to_dict())

    # ---- 8. lati 1/2: casa o ospite
    print('perfette: casa', int((off.pitching_side == 'casa').sum()), 'ospite', int((off.pitching_side == 'ospite').sum()))


if __name__ == '__main__':
    main()
