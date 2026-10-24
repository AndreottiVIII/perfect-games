"""Costruisce i dati del sito (cartella docs/, servita da GitHub Pages).

Uso (dalla cartella del progetto):  python src/build_site.py

Legge i risultati gia' calcolati in output/ e il file data/streaks.csv, e:
- scrive i file JSON in docs/data/ (curva.json, come_cala.json, grazia.json, stadi.json);
- inserisce gli stessi dati dentro le pagine HTML (tra i segnaposto <!-- build:NOME --> e
  <!-- /build:NOME -->), cosi' i grafici funzionano anche aprendo il file dal disco;
- genera le tabelle (le 21 partite, le quasi perfette, le epoche, come finisce, gli stadi).
Le pagine HTML sono scritte a mano: questo script cambia solo cio' che sta tra i segnaposto.

Stesse esclusioni degli altri script: solo Lega Americana, Nazionale e Federal League, niente
partite "dedotte" da box score, partita di Galarraga trattata come perfetta (src/overrides.csv).
I nomi degli stadi vengono da src/stadi_nomi.csv (scritto a mano: codice Retrosheet -> nome).
"""
import csv
import glob
import html
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ca_common import load  # noqa: E402
from curve import km  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'output')
DOCS = os.path.join(ROOT, 'docs')
RAW = os.path.join(ROOT, 'data', 'raw')

# Epoche per la pagina "La curva": sette periodi che il baseball riconosce, invece di 12 decenni
# quasi uguali. I confini sono cambi di gioco: fine della palla morta (1920), guerra (1942),
# espansione e "anni dei lanciatori" (1961), arrivo del DH in Lega Americana (1973), espansione
# e anni dei fuoricampo (1993), anni degli strikeout (2010).
EPOCHE = [
    (1908, 1919, 'palla morta'),
    (1920, 1941, 'palla viva, tra le due guerre'),
    (1942, 1960, 'guerra e dopoguerra'),
    (1961, 1972, 'anni dei lanciatori, senza DH'),
    (1973, 1992, 'arriva il DH in Lega Americana'),
    (1993, 2009, 'anni dei fuoricampo'),
    (2010, 2025, 'anni degli strikeout'),
]
MIN_IN_GIOCO = 30        # la linea di un'epoca si ferma quando restano meno squadre ancora perfette
MIN_RISCHIO = 100        # "Come cala": sotto questo numero di squadre a rischio il punto e' incerto
MIN_ATTESE_STADI = 50    # "Gli stadi": nel grafico solo gli stadi con almeno 50 serie attese
STADI_EVIDENZA = {'DEN02', 'BOS07', 'LOS03', 'NYC14'}

# Nomi: i file .ROS di Retrosheet sono senza accenti; qui si correggono quelli che li hanno.
ACCENTI = {
    'Felix Hernandez': 'Félix Hernández', 'Dennis Martinez': 'Dennis Martínez',
    'Pedro Martinez': 'Pedro Martínez', 'Domingo German': 'Domingo Germán',
    'Felix Mantilla': 'Félix Mantilla', 'Jose Tabata': 'José Tabata', 'Eddie Perez': 'Eddie Pérez',
    'Marwin Gonzalez': 'Marwin González', 'Gary Disarcina': 'Gary DiSarcina',
}
# Galarraga: per scelta di Davide il 27esimo battitore (Jason Donald, dichiarato salvo per errore
# dall'arbitro) conta come eliminato; nei dati l'ultimo eliminato resta il 26esimo.
GALARRAGA = 'DET201006020'
GALARRAGA_ULTIMO = 'donaj002'

MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
        'settembre', 'ottobre', 'novembre', 'dicembre']
EVENTI = {'singolo': 'singolo', 'doppio': 'doppio', 'triplo': 'triplo', 'fuoricampo': 'fuoricampo',
          'base_su_ball': 'base su ball', 'base_intenzionale': 'base su ball intenzionale',
          'colpito': 'colpito dal lancio', 'errore': 'errore della difesa',
          'interferenza_ricevitore': 'interferenza del ricevitore'}


# ---------------------------------------------------------------- piccoli aiuti
def it_int(n):
    return f'{int(round(n)):,}'.replace(',', '.')


def it_dec(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def it_pct(x, d=1):
    return it_dec(100 * x, d) + '%'


def uno_su(s):
    return '1 su ' + it_int(1 / s)


def it_data(s):
    y, m, d = s.split('-')
    return f'{int(d)} {MESI[int(m) - 1]} {y}'


def esc(s):
    return html.escape(str(s), quote=True)


def r4(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(f'{x:.6g}')


def table(head, rows, num=(), cls=None, wide=False):
    """Tabella HTML semplice; le colonne con indice in num sono numeri (allineati a destra)."""
    num = set(num)
    out = ['<div class="table-wrap"><table%s>' % (' class="wide"' if wide else ''), '<thead><tr>']
    out += [f'<th{" class=\"num\"" if i in num else ""}>{esc(h)}</th>' for i, h in enumerate(head)]
    out.append('</tr></thead><tbody>')
    for i, r in enumerate(rows):
        c = f' class="{cls[i]}"' if cls and cls[i] else ''
        out.append(f'<tr{c}>' + ''.join(
            f'<td{" class=\"num\"" if j in num else ""}>{v}</td>' for j, v in enumerate(r)) + '</tr>')
    out.append('</tbody></table></div>')
    return '\n'.join(out)


def json_block(id_, obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    return f'<script type="application/json" id="{id_}">{s.replace("</", "<" + chr(92) + "/")}</script>'


def inject(page, blocks):
    path = os.path.join(DOCS, page)
    with open(path, encoding='utf-8') as f:
        txt = f.read()
    for name, content in blocks.items():
        pat = re.compile(r'(<!-- build:%s -->)(.*?)(<!-- /build:%s -->)' % (name, name), re.S)
        if not pat.search(txt):
            raise SystemExit(f'segnaposto {name} mancante in {page}')
        txt = pat.sub(lambda m: m.group(1) + '\n' + content + '\n' + m.group(3), txt)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


def write_json(name, obj):
    os.makedirs(os.path.join(DOCS, 'data'), exist_ok=True)
    with open(os.path.join(DOCS, 'data', name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


# ---------------------------------------------------------------- nomi da Retrosheet
def player_names():
    names = {}
    for f in glob.glob(os.path.join(RAW, '*', '*.ROS')):
        with open(f, encoding='latin-1') as fh:
            for r in csv.reader(fh):
                if len(r) >= 3:
                    n = f'{r[2]} {r[1]}'.strip()
                    names[r[0]] = ACCENTI.get(n, n)
    return names


def team_names():
    teams = {}
    for f in glob.glob(os.path.join(RAW, '*', 'TEAM*')):
        year = int(os.path.basename(f)[4:8])
        with open(f, encoding='latin-1') as fh:
            for r in csv.reader(fh):
                if len(r) >= 4:
                    teams[(year, r[0])] = f'{r[2]} {r[3]}'
    # Retrosheet chiama "Indians" anche la Cleveland di Lajoie, che fino al 1914 si chiamava Naps
    for y in range(1903, 1915):
        if (y, 'CLE') in teams:
            teams[(y, 'CLE')] = 'Cleveland Naps'
    return teams


def park_names():
    p = pd.read_csv(os.path.join(HERE, 'stadi_nomi.csv'), encoding='utf-8')
    return {r.site: (r.nome, r.citta) for r in p.itertuples()}


# ---------------------------------------------------------------- 1. La curva
def build_curva(d):
    ov = pd.read_csv(os.path.join(OUT, 'curve_overall.csv')).set_index('n')
    tutte = {'s': [r4(ov.survival[n]) for n in range(28)], 'r': [int(ov.at_risk[n]) for n in range(28)]}
    epoche, righe = [], []
    for a, b, nome in EPOCHE:
        sub = d[d.season.between(a, b)]
        c = km(sub).set_index('n')
        s = [r4(c.survival[n]) if c.at_risk[n] >= MIN_IN_GIOCO or n == 0 else None for n in range(28)]
        # la linea si ferma al primo battitore con poche squadre in gioco (niente buchi in mezzo)
        if None in s:
            k = s.index(None)
            s = s[:k] + [None] * (28 - k)
        perf = int(((sub.batters_retired >= 27) & (sub.reach == 0)).sum())
        epoche.append(dict(id=f'{a}', label=f'{a}-{b}', nome=nome, lati=len(sub), s=s))
        righe.append([f'{a}-{b}', esc(nome), it_int(len(sub)), uno_su(c.survival[9]), uno_su(c.survival[18]), str(perf)])
    tab = table(['Epoca', 'Che baseball era', 'Squadre al lancio', 'Perfette dopo 9', 'Dopo 18', 'Perfect game'],
                righe, num=range(2, 6))
    obj = dict(tutte=tutte, epoche=epoche, min_in_gioco=MIN_IN_GIOCO)
    write_json('curva.json', obj)
    inject('index.html', {'dati-curva': json_block('dati-curva', obj), 'tabella-epoche': tab})
    print('La curva: dopo 9 %s, dopo 18 %s, dopo 27 %s; squadre %s' % (
        uno_su(ov.survival[9]), uno_su(ov.survival[18]), uno_su(ov.survival[27]), it_int(ov.at_risk[1])))
    for e, r in zip(EPOCHE, righe):
        print('   ', r[0], r[3], r[4], 'perfette', r[5])


# ---------------------------------------------------------------- 2. Come cala
def build_come_cala():
    hz = pd.read_csv(os.path.join(OUT, 'come_cala_hazard.csv'))

    def pts(g):
        t = hz[hz.gruppo == g].sort_values('n')
        return [dict(n=int(r.n), h=r4(r.hazard), lo=r4(r.lo), hi=r4(r.hi), r=int(r.at_risk), k=int(r.broken))
                for r in t.itertuples()]
    obj = dict(min_rischio=MIN_RISCHIO, senza_dh=pts('senza_dh'), con_dh=pts('con_dh'))
    write_json('come_cala.json', obj)

    ev = pd.read_csv(os.path.join(OUT, 'come_cala_eventi.csv'))
    cols = [('tutte le rotture', 'Tutte'), ('rotture al battitore 10-18', 'Dal 10° al 18°'),
            ('rotture al battitore 19-27', 'Dal 19° al 27°')]
    nomi = {'singolo': 'Singolo', 'doppio o triplo': 'Doppio o triplo', 'fuoricampo': 'Fuoricampo',
            'base su ball': 'Base su ball', 'colpito': 'Colpito dal lancio', 'errore': 'Errore della difesa',
            'altro': 'Altro (interferenza e simili)'}
    rows = []
    for e, lab in nomi.items():
        row = [lab]
        for c, _ in cols:
            r = ev[(ev.insieme == c) & (ev.evento == e)].iloc[0]
            row.append(it_pct(r.quota))
        rows.append(row)
    tot = ['<strong>Casi</strong>'] + [f'<strong>{it_int(ev[ev.insieme == c].tot.iloc[0])}</strong>' for c, _ in cols]
    tab = table(['Come arriva in base il primo'] + [h for _, h in cols], rows + [tot], num=(1, 2, 3))
    inject('come-cala.html', {'dati-come-cala': json_block('dati-come-cala', obj), 'tabella-eventi': tab})
    s, c = obj['senza_dh'], obj['con_dh']
    print('Come cala: n=1 %s / %s, n=9 %s / %s; a rischio <%d da n=%d (senza) e n=%d (con)' % (
        it_pct(s[0]['h']), it_pct(c[0]['h']), it_pct(s[8]['h']), it_pct(c[8]['h']), MIN_RISCHIO,
        min(p['n'] for p in s if p['r'] < MIN_RISCHIO), min(p['n'] for p in c if p['r'] < MIN_RISCHIO)))


# ---------------------------------------------------------------- 3. Giornata di grazia
def build_grazia(n_lati):
    t = pd.read_csv(os.path.join(OUT, 'come_cala_null.csv'))
    lo = t.ratio_N2 * np.exp(-1.96 * t.se_logS)
    hi = t.ratio_N2 * np.exp(1.96 * t.se_logS)
    punti = [dict(n=int(r.n), s=r4(r.survival), s0=r4(r.S0_N2), ratio=r4(r.ratio_N2), lo=r4(a), hi=r4(b))
             for r, a, b in zip(t.itertuples(), lo, hi)]
    obj = dict(punti=punti, reali_27=r4(n_lati * t.survival.iloc[26]), attese_27_N2=r4(n_lati * t.S0_N2.iloc[26]),
               attese_27_N3=r4(n_lati * t.S0_N3.iloc[26]))
    write_json('grazia.json', obj)
    inject('giornata-di-grazia.html', {'dati-grazia': json_block('dati-grazia', obj)})
    print('Grazia: reali %.1f, attese N2 %.1f, N3 %.1f; rapporto 3/9/12/18/27: %s' % (
        obj['reali_27'], obj['attese_27_N2'], obj['attese_27_N3'],
        ', '.join(f'{punti[n - 1]["ratio"]:.2f} [{punti[n - 1]["lo"]:.2f}-{punti[n - 1]["hi"]:.2f}]' for n in (3, 9, 12, 18, 27))))


# ---------------------------------------------------------------- 5. Le 21 partite
def last_out_kind(ev):
    ev = str(ev)
    if ev.startswith('K'):
        return 'strikeout'
    if re.search(r'/(F|P|L)', ev):
        return 'al volo'
    return 'a terra'


def build_partite(d, players, teams, parks):
    P = pd.read_csv(os.path.join(OUT, 'chicche_perfette.csv'), low_memory=False).sort_values('date')
    rows, cls = [], []
    for r in P.itertuples():
        y = int(r.season)
        gal = r.game_id == GALARRAGA
        nome = esc(players.get(r.starting_pitcher, r.starting_pitcher))
        if gal:
            nome += ' <span class="mark">*</span>'
        lanci = it_int(r.pitches_retired) if (y >= 1988 and r.pitches_all_valid == 1 and not gal) else '—'
        if gal:
            ultimo = esc(players[GALARRAGA_ULTIMO]) + ' (salvo per errore dell’arbitro)'
            come, ph = 'a terra', 'no'
        else:
            ultimo = esc(players.get(r.last_batter, r.last_batter))
            come = last_out_kind(r.last_event)
            ph = 'sì' if r.last_pos == 11 else 'no'
        stadio = parks.get(r.site, (r.site, ''))
        rows.append([it_data(r.date), nome,
                     esc(teams.get((y, r.pitching_team), r.pitching_team)),
                     esc(teams.get((y, r.batting_team), r.batting_team)),
                     esc(f'{stadio[0]}, {stadio[1]}'), str(int(r.ks_retired)), lanci, ultimo, come, ph])
        cls.append('special' if gal else '')
    tab = table(['Data', 'Lanciatore', 'Squadra', 'Avversario', 'Stadio', 'Strikeout', 'Lanci',
                 'Ultimo out', 'Come', 'Pinch hitter'], rows, num=(5, 6), cls=cls, wide=True)

    # quasi perfette: oltre 27 eliminati senza perfect game, e rotte proprio al 27esimo battitore
    q = d[(d.reach == 1) & (d.batters_retired >= 26)].sort_values('date')
    qrows = []
    for r in q.itertuples():
        y = int(r.season)
        ev = EVENTI.get(r.first_runner_event, r.first_runner_event.replace('_', ' '))
        qrows.append([it_data(r.date),
                      esc(players.get(r.starting_pitcher, r.starting_pitcher)),
                      esc(teams.get((y, r.pitching_team), r.pitching_team)),
                      esc(teams.get((y, r.batting_team), r.batting_team)),
                      str(int(r.batters_retired)),
                      esc(players.get(r.breaker_player, r.breaker_player)), esc(ev),
                      f'{int(r.breaker_inning)}°',
                      'sì' if r.breaker_pos == 11 else 'no',
                      'sì' if (r.hits_allowed == 0 and r.game_status == 'completa') else 'no'])
    qtab = table(['Data', 'Lanciatore', 'Squadra', 'Avversario', 'Eliminati di fila', 'Chi arriva in base',
                  'Come', 'Inning', 'Pinch hitter', 'Poi no-hitter'], qrows, num=(4, 7), wide=True)
    inject('partite.html', {'tabella-partite': tab, 'tabella-quasi': qtab})
    off = P[P.game_id != GALARRAGA]
    print(f'Partite: {len(P)} (ufficiali {len(off)}), pinch hitter ultimo out {int((off.last_pos == 11).sum())}; '
          f'strikeout medi {off.ks_retired.mean():.1f}; quasi perfette {len(q)} '
          f'(rotte al 27esimo {int((q.batters_retired == 26).sum())}, di cui pinch hitter {int(((q.batters_retired == 26) & (q.breaker_pos == 11)).sum())})')


# ---------------------------------------------------------------- 6. Gli stadi
def build_stadi(d, parks):
    p = pd.read_csv(os.path.join(OUT, 'chicche_parchi.csv'))
    anni = d.groupby('site').season.agg(['min', 'max'])
    stadi, rows = [], []
    for r in p.sort_values('ratio', ascending=False).itertuples():
        nome, citta = parks[r.site]
        a, b = int(anni.loc[r.site, 'min']), int(anni.loc[r.site, 'max'])
        anni_s = f'{a}-{b}' if a != b else str(a)
        item = dict(site=r.site, nome=nome, citta=citta, anni=anni_s, n=int(r.n), O=int(r.O), E=r4(r.E),
                    ratio=r4(r.ratio), evidenza=r.site in STADI_EVIDENZA)
        if r.E >= MIN_ATTESE_STADI:
            stadi.append(item)
        diff = r.ratio - 1
        rows.append([esc(nome), esc(citta), anni_s, it_int(r.n), it_int(r.O), it_dec(r.E, 0),
                     '0%' if round(abs(diff) * 100) == 0 else ('+' if diff > 0 else '−') + f'{abs(diff) * 100:.0f}%'])
    obj = dict(min_attese=MIN_ATTESE_STADI, stadi=stadi)
    write_json('stadi.json', obj)
    tab = table(['Stadio', 'Città', 'Anni', 'Squadre al lancio', 'Serie viste', 'Serie attese', 'Differenza'],
                rows, num=range(3, 7), wide=True)
    inject('stadi.html', {'dati-stadi': json_block('dati-stadi', obj), 'tabella-stadi': tab})
    print(f'Stadi: {len(stadi)} nel grafico (attese >= {MIN_ATTESE_STADI}), {len(rows)} in tabella')


def main():
    d = load(os.path.join(ROOT, 'data', 'streaks.csv'))
    players, teams, parks = player_names(), team_names(), park_names()
    missing = sorted(set(pd.read_csv(os.path.join(OUT, 'chicche_parchi.csv')).site) - set(parks))
    if missing:
        raise SystemExit(f'stadi senza nome in src/stadi_nomi.csv: {missing}')
    build_curva(d)
    build_come_cala()
    build_grazia(len(d))
    build_partite(d, players, teams, parks)
    build_stadi(d, parks)
    print('sito aggiornato in', DOCS)


if __name__ == '__main__':
    main()
