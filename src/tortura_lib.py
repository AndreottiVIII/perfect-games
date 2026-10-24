"""Funzioni comuni per la "tortura" dei dati: caricamento dei turni di battuta nelle serie perfette,
covariate (forza di attacco e lanciatori, calendario), regressione logistica con errori standard
raggruppati per partita.

Non si esegue da solo: lo importano verifiche.py e tortura.py (che aggiungono la cartella src al percorso).
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_common import load, wilson  # noqa: E402

M_TEAM = 0          # nessuna riduzione per l'attacco: ha migliaia di turni
M_PIT_SEASON = 100  # peso (in turni) della media nella stima del lanciatore nella stagione
M_PIT_CAREER = 300  # idem, carriera fino a quel giorno
M_BB = 20           # peso (in arrivi in base) della media nella tendenza a regalare basi


# ---------------------------------------------------------------- motore logistico
def onehot(codes, drop_first=True):
    codes = np.asarray(codes)
    u, inv = np.unique(codes, return_inverse=True)
    m = sparse.csr_matrix((np.ones(len(codes)), (np.arange(len(codes)), inv)), shape=(len(codes), len(u)))
    return m[:, 1:] if drop_first else m


def fit_logit(X, y, cluster, nfe, off=None, wt=None, ridge=1e-3, maxit=40, tol=1e-9):
    """IRLS con piccola penalita' sui primi nfe coefficienti (effetti fissi); SE robusti per cluster; pesi opzionali."""
    n, k = X.shape
    X = X.tocsr()
    off = np.zeros(n) if off is None else off
    wt = np.ones(n) if wt is None else np.asarray(wt, float)
    y = y.astype(float)
    b = np.zeros(k)
    pen = np.zeros(k)
    pen[:nfe] = ridge
    dev_old = np.inf
    for _ in range(maxit):
        eta = X @ b + off
        p = expit(eta)
        pq = np.clip(p * (1 - p), 1e-10, None)
        z = eta - off + (y - p) / pq
        W = wt * pq
        H = (X.T @ sparse.diags(W) @ X).toarray() + np.diag(pen)
        g = X.T @ (W * z)
        b = np.linalg.solve(H, g)
        pc = np.clip(expit(X @ b + off), 1e-12, 1 - 1e-12)
        dev = -2 * np.sum(wt * (y * np.log(pc) + (1 - y) * np.log(1 - pc)))
        if abs(dev_old - dev) < tol * abs(dev) + 1e-9:
            break
        dev_old = dev
    eta = X @ b + off
    p = expit(eta)
    W = wt * np.clip(p * (1 - p), 1e-10, None)
    H = (X.T @ sparse.diags(W) @ X).toarray() + np.diag(pen)
    A = np.linalg.inv(H)
    cl, inv = np.unique(cluster, return_inverse=True)
    G = sparse.csr_matrix((np.ones(n), (inv, np.arange(n))), shape=(len(cl), n))
    S = G @ sparse.diags(wt * (y - p)) @ X
    meat = (S.T @ S).toarray()
    cov = A @ meat @ A * len(cl) / max(len(cl) - 1, 1)
    return b, cov


def fe_design(df, fes):
    """fes: elenco di nomi di colonne intere/stringa -> matrice di effetti fissi (con intercetta)."""
    parts = [sparse.csr_matrix(np.ones((len(df), 1)))]
    for f in fes:
        if f is None:
            continue
        parts.append(onehot(df[f].to_numpy()))
    X = sparse.hstack(parts).tocsr()
    return X, X.shape[1]


def run_logit(df, ycol, factors, fes=('nd', 'season'), cluster='g', off=None, wcol=None):
    """factors: dict nome -> vettore (array/Serie) o colonna; restituisce una tabella OR/IC/p per i fattori."""
    X0, nfe = fe_design(df, fes)
    cols = []
    for nm, v in factors.items():
        vv = df[v].to_numpy(float) if isinstance(v, str) else np.asarray(v, float)
        cols.append(sparse.csr_matrix(vv.reshape(-1, 1)))
    X = sparse.hstack([X0] + cols).tocsr() if cols else X0
    y = df[ycol].to_numpy()
    wt = df[wcol].to_numpy(float) if wcol else None
    b, cov = fit_logit(X, y, df[cluster].to_numpy(), nfe, off=off, wt=wt)
    rows = []
    for i, nm in enumerate(factors):
        j = nfe + i
        se = float(np.sqrt(cov[j, j]))
        z = b[j] / se if se > 0 else np.nan
        rows.append(dict(fattore=nm, beta=float(b[j]), se=se, OR=float(np.exp(b[j])),
                         lo=float(np.exp(b[j] - 1.96 * se)), hi=float(np.exp(b[j] + 1.96 * se)),
                         p=float(2 * stats.norm.sf(abs(z))) if se > 0 else np.nan,
                         righe=len(df), eventi=int((y * (wt if wt is not None else 1)).sum())))
    return pd.DataFrame(rows)


def fmt(r, digits=2):
    return f"OR {r.OR:.{digits}f} [{r.lo:.{digits}f}-{r.hi:.{digits}f}] p={r.p:.3g}"


# ---------------------------------------------------------------- caricamento e covariate
def nbucket(n):
    n = np.asarray(n)
    return np.where(n <= 18, n, 19 + (n - 19) // 3)


def load_pa(data_dir):
    sp = os.path.join(data_dir, 'streaks.csv')
    s = load(sp)
    s['ps'] = (s.pitching_side == 'casa').astype(int)
    s['key'] = s.game_id + '|' + s.ps.astype(str)
    s['date_dt'] = pd.to_datetime(s.date)
    s['number'] = pd.to_numeric(s.number, errors='coerce').fillna(0).astype(int)
    s['temp'] = pd.to_numeric(s.temp, errors='coerce')

    pa = pd.read_csv(os.path.join(data_dir, 'pa_streak.csv'), keep_default_na=False,
                     dtype={'g': str, 'b': str, 'pit': str, 'ph': str, 'cat': str, 'k': str, 'fp': str, 'bh': str,
                            'bs': str, 'bp': str})
    pa['key'] = pa.g + '|' + pa.ps.astype(str)
    pa = pa[pa.key.isin(set(s.key))].copy()
    # la correzione di Galarraga: il 27esimo battitore e' trattato come eliminato
    ov = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(data_dir)), 'src', 'overrides.csv'))
    for _, o in ov.iterrows():
        m = (pa.g == o.game_id) & (pa.ps == int(o.side == 'casa')) & (pa.n == 27)
        pa.loc[m, 'r'] = 0
        pa.loc[m, 'k'] = ''
    pa['bs'] = pd.to_numeric(pa.bs, errors='coerce')
    pa['bp'] = pd.to_numeric(pa.bp, errors='coerce')
    pa['season'] = pa.g.str[3:7].astype(int)
    cols = ['key', 'bat_dh', 'league_file', 'number', 'daynight', 'site', 'date_dt', 'temp', 'pitching_team',
            'batting_team', 'starting_pitcher', 'last_inning']
    P = pa.merge(s[cols], on='key', how='left')
    P['nd'] = nbucket(P.n.to_numpy()) * 2 + P.bat_dh.to_numpy()
    P['nb'] = nbucket(P.n.to_numpy())
    return s, P


def add_strength(P, s, data_dir):
    """Forza dell'attacco, dei lanciatori (stagione e carriera) e calendario."""
    tg = pd.read_csv(os.path.join(data_dir, 'team_game.csv'), keep_default_na=False, dtype={'g': str, 'team': str})
    tg = tg[tg.g.isin(set(s.game_id))]
    t_season = tg.groupby(['season', 'team'])[['pa', 'reach']].sum().rename(columns=lambda c: c + '_s')
    lg = tg.groupby('season')[['pa', 'reach']].sum()
    lg_rate = (lg.reach / lg.pa).rename('lg')
    tg = tg.join(t_season, on=['season', 'team']).join(lg_rate, on='season')
    tg['x_team'] = (tg.reach_s - tg.reach) / (tg.pa_s - tg.pa) - tg.lg
    sd = tg.x_team.std()
    tg['x_team'] = tg.x_team / sd
    P = P.merge(tg[['g', 'team', 'x_team']].rename(columns={'team': 'batting_team'}), on=['g', 'batting_team'], how='left')

    pg = pd.read_csv(os.path.join(data_dir, 'pitcher_game.csv'), keep_default_na=False,
                     dtype={'g': str, 'pit': str, 'team': str})
    pg = pg[pg.g.isin(set(s.game_id))].copy()
    pg['date_dt'] = pd.to_datetime(pg.date)
    pg = pg.join(lg_rate, on='season')
    ps_ = pg.groupby(['season', 'pit'])[['pa', 'reach']].sum().rename(columns=lambda c: c + '_s')
    pg = pg.join(ps_, on=['season', 'pit'])
    pa_l, re_l = pg.pa_s - pg.pa, pg.reach_s - pg.reach
    pg['x_pit_s'] = (re_l + M_PIT_SEASON * pg.lg) / (pa_l + M_PIT_SEASON) - pg.lg
    pg['x_pit_s'] = pg.x_pit_s / pg.x_pit_s.std()
    # carriera fino a quel giorno (turni di partite con data precedente)
    pg = pg.sort_values(['pit', 'date_dt', 'g']).reset_index(drop=True)
    pg['exp'] = pg.pa * pg.lg
    grp = pg.groupby('pit')
    cum_pa, cum_re, cum_ex = grp.pa.cumsum() - pg.pa, grp.reach.cumsum() - pg.reach, grp.exp.cumsum() - pg.exp
    # le partite dello stesso giorno (doppi incontri) non devono contare come passate
    same_day = pg.groupby(['pit', 'date_dt'])[['pa', 'reach', 'exp']].transform('sum')
    first_idx = pg.groupby(['pit', 'date_dt']).cumcount() == 0
    # semplice: sottrae i turni di partite precedenti nello stesso giorno
    cd_pa = pg.groupby(['pit', 'date_dt']).pa.cumsum() - pg.pa
    cd_re = pg.groupby(['pit', 'date_dt']).reach.cumsum() - pg.reach
    cd_ex = pg.groupby(['pit', 'date_dt']).exp.cumsum() - pg.exp
    cum_pa, cum_re, cum_ex = cum_pa - cd_pa, cum_re - cd_re, cum_ex - cd_ex
    pg['x_pit_c'] = (cum_re - cum_ex) / (cum_pa + M_PIT_CAREER)
    pg['pa_prior'] = cum_pa
    pg['x_pit_c'] = pg.x_pit_c / pg.x_pit_c.std()
    # tendenza a regalare basi (tutta la carriera, senza la partita in esame): basi su ball su arrivi in base
    tot = pg.groupby('pit')[['reach', 'bb']].transform('sum')
    p0 = pg.bb.sum() / pg.reach.sum()
    pg['bbshare'] = (tot.bb - pg.bb + M_BB * p0) / (tot.reach - pg.reach + M_BB)
    P = P.merge(pg[['g', 'pit', 'x_pit_s', 'x_pit_c', 'pa_prior', 'bbshare']], on=['g', 'pit'], how='left')

    # calendario: partita precedente della squadra al bat
    t1 = s[['game_id', 'date_dt', 'number', 'pitching_team', 'daynight', 'last_inning', 'season']].rename(
        columns={'pitching_team': 'team'})
    t2 = s[['game_id', 'date_dt', 'number', 'batting_team', 'daynight', 'last_inning', 'season']].rename(
        columns={'batting_team': 'team'})
    sch = pd.concat([t1, t2]).drop_duplicates(['game_id', 'team']).sort_values(['team', 'date_dt', 'number', 'game_id'])
    gb = sch.groupby('team')
    sch['prev_date'] = gb.date_dt.shift()
    sch['prev_dn'] = gb.daynight.shift()
    sch['prev_li'] = gb.last_inning.shift()
    sch['prev_season'] = gb.season.shift()
    sch['gap'] = (sch.date_dt - sch.prev_date).dt.days.where(sch.prev_season == sch.season)
    sch['dayafternight'] = ((sch.daynight == 'day') & (sch.prev_dn == 'night') & (sch.gap == 1)).astype(int)
    sch['afterextra'] = ((sch.prev_li >= 10) & (sch.gap == 1)).astype(int)
    P = P.merge(sch[['game_id', 'team', 'dayafternight', 'afterextra']].rename(
        columns={'game_id': 'g', 'team': 'batting_team'}), on=['g', 'batting_team'], how='left')

    # prima volta del partente contro quella squadra nella stagione
    ss = s.sort_values(['season', 'starting_pitcher', 'batting_team', 'date_dt', 'number', 'game_id']).copy()
    ss['first_vs'] = (ss.groupby(['season', 'starting_pitcher', 'batting_team']).cumcount() == 0).astype(int)
    P = P.merge(ss[['key', 'first_vs']], on='key', how='left')
    P['is_starter'] = (P.pit == P.starting_pitcher).astype(int)

    se = pd.read_csv(os.path.join(data_dir, 'side_extra.csv'), keep_default_na=False, dtype={'g': str})
    se['key'] = se.g + '|' + se.ps.astype(str)
    se['ls_share'] = np.where(se.ls_known >= 7, se.ls_same / se.ls_known.replace(0, np.nan), np.nan)
    sdv = se.ls_share.std()
    se['ls_z'] = (se.ls_share - se.ls_share.mean()) / sdv
    P = P.merge(se[['key', 'ls_z']], on='key', how='left')
    P['same_hand'] = np.where(P.bh.isin(['R', 'L']) & P.ph.isin(['R', 'L']), (P.bh == P.ph).astype(float), np.nan)
    return P, se


def holm(ps):
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    m = len(ps)
    adj = np.empty(m)
    run = 0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * ps[i])
        adj[i] = min(1, run)
    return adj
