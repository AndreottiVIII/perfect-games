"""Estrazione per la "tortura": un secondo passaggio sui file evento di Retrosheet.

Uso: python -I tortura_extract.py <cartella_raw> <cartella_dati>

Scrive in <cartella_dati>:
  pa_streak.csv     una riga per turno di battuta dentro la serie "perfetta finora" (n = 1..27), per squadra al lancio:
                    g (game_id), ps (0 = lancia la squadra ospite, 1 = lancia la casa), n, b (battitore), bs (slot),
                    bp (ruolo difensivo del battitore: 11 = pinch hitter, 1 = lanciatore), bh (mano di battuta R/L/B/?),
                    pit (lanciatore in campo), ph (mano del lanciatore), cat (ricevitore), inn, lead (punti di vantaggio
                    della squadra al lancio), r (1 = arriva in base), k (tipo di arrivo), np (lanci del turno, -1 se non
                    validi), fp (primo lancio: S strike, B ball, X in gioco, H colpito, U altro), bl (ball nel conteggio finale)
  side_extra.csv    una riga per squadra al lancio: g, ps, nxt_n, nxt_r (arrivi nei 3 turni DOPO la prima rottura),
                    runs_allowed, runs_scored, ls_same/ls_known (battitori della formazione iniziale avversaria
                    con la stessa mano del lanciatore partente, tra quelli con mano nota; i bilaterali contano come opposti)
  pitcher_game.csv  g, date, season, pit, team, pa, reach, bb  (tutti i turni di ogni lanciatore, per forza del lanciatore)
  team_game.csv     g, date, season, team, pa, reach          (tutti i turni di ogni squadra al bat, per forza dell'attacco)
Salta le partite dedotte e la lega R. Applica nulla delle correzioni: la correzione di Galarraga si fa in analisi.
"""
import csv
import glob
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_streaks import classify, PITCH_CHARS, parse_csv_line  # noqa: E402

STRIKES = frozenset('CFKLMOQRST')
BALLS = frozenset('BIPV')
RE_ADV_H = re.compile(r'^([123B])-H')


def runs_on_play(event):
    ev = event.replace('!', '').replace('?', '').replace('#', '').strip()
    if '.' in ev:
        basic, adv = ev.split('.', 1)
    else:
        basic, adv = ev, ''
    head = basic.split('/')[0].split('+')[0]
    r = 0
    hr = bool(re.match(r'^H(?!P)', head))
    if hr:
        r += 1
    if adv:
        for a in adv.split(';'):
            m = RE_ADV_H.match(a.strip())
            if m and not (hr and m.group(1) == 'B'):
                r += 1
    return r


def load_rosters(raw):
    cnt = {}
    for f in glob.glob(os.path.join(raw, '*', '*.ROS')):
        with open(f, encoding='latin-1') as fh:
            for line in fh:
                p = line.rstrip('\n').split(',')
                if len(p) >= 5:
                    cnt.setdefault(p[0], Counter())[(p[3], p[4])] += 1
    return {k: v.most_common(1)[0][0] for k, v in cnt.items()}


def process_file(path, rost, w_pa, w_side, w_pit, w_team):
    with open(path, encoding='latin-1', newline='') as fh:
        lines = fh.read().splitlines()
    g = None

    def finish(g):
        if g is None:
            return
        for ps in (0, 1):
            st = g['side'][ps]
            sp = [pid for (slot, pid, pos) in g['starters'][ps] if pos == 1]
            ph0 = rost.get(sp[0], ('?', '?'))[1] if sp else '?'
            same = known = 0
            for (slot, pid, pos) in g['starters'][1 - ps]:
                if pos == 1:
                    continue
                bh0 = rost.get(pid, ('?', '?'))[0]
                if bh0 in 'RL' and ph0 in 'RL' and bh0 != '?':
                    known += 1
                    same += int(bh0 == ph0)
            w_side.writerow([g['id'], ps, len(st['after']), sum(st['after']), g['runs'][1 - ps], g['runs'][ps], same, known])
        for (pit, team), v in g['pit'].items():
            w_pit.writerow([g['id'], g['date'], g['season'], pit, team, v[0], v[1], v[2]])
        for team_side in (0, 1):
            v = g['team'][team_side]
            w_team.writerow([g['id'], g['date'], g['season'], g['teams'][team_side], v[0], v[1]])

    for line in lines:
        if not line:
            continue
        tag = line.split(',', 1)[0]
        if tag == 'id':
            finish(g)
            gid = line.split(',')[1].strip()
            g = {'id': gid, 'season': int(gid[3:7]), 'date': '', 'teams': ['', ''],
                 'pos': [dict(), dict()], 'slotof': [dict(), dict()], 'runs': [0, 0],
                 'starters': [[], []], 'pa': [0, 0], 'pit': {}, 'team': [[0, 0], [0, 0]],
                 'side': [dict(n=0, ended=None, after=[]) for _ in range(2)]}
            continue
        if g is None:
            continue
        if tag == 'info':
            f = parse_csv_line(line)
            if f[1] == 'visteam':
                g['teams'][0] = f[2]
            elif f[1] == 'hometeam':
                g['teams'][1] = f[2]
            elif f[1] == 'date':
                g['date'] = f[2].replace('/', '-')
        elif tag in ('start', 'sub'):
            f = parse_csv_line(line)
            pid, team, slot, pos = f[1], int(f[3]), int(f[4]), int(f[5])
            g['pos'][team][pos] = pid
            g['slotof'][team][pid] = (slot, pos)
            if tag == 'start':
                g['starters'][team].append((slot, pid, pos))
        elif tag == 'play':
            f = parse_csv_line(line)
            inn, bat_side, batter, count, pstr, event = int(f[1]), int(f[2]), f[3], f[4], f[5], f[6]
            pit_side = 1 - bat_side
            run = runs_on_play(event)
            is_pa, reached, kind = classify(event)
            lead_before = g['runs'][pit_side] - g['runs'][bat_side]
            if run:
                g['runs'][bat_side] += run
            if not is_pa:
                continue
            pit = g['pos'][pit_side].get(1, '')
            cat = g['pos'][pit_side].get(2, '')
            # statistiche di tutti i turni (forza dei lanciatori e degli attacchi)
            pv = g['pit'].setdefault((pit, g['teams'][pit_side]), [0, 0, 0])
            pv[0] += 1
            pv[1] += int(reached)
            pv[2] += int(kind in ('base_su_ball', 'base_intenzionale'))
            tv = g['team'][bat_side]
            tv[0] += 1
            tv[1] += int(reached)
            st = g['side'][pit_side]
            if st['ended'] is not None:
                if len(st['after']) < 3:
                    st['after'].append(int(reached))
                continue
            if st['n'] >= 27:
                continue
            n = st['n'] + 1
            bslot, bpos = g['slotof'][bat_side].get(batter, ('', ''))
            seq = [c for c in pstr if c in PITCH_CHARS]
            valid = bool(seq) and '?' not in pstr
            fp = ''
            if valid:
                c0 = seq[0]
                fp = 'S' if c0 in STRIKES else 'B' if c0 in BALLS else 'X' if c0 in 'XY' else 'H' if c0 == 'H' else 'U'
            bl = int(count[0]) if len(count) == 2 and count[0].isdigit() else -1
            bh, _ = rost.get(batter, ('?', '?'))
            _, ph = rost.get(pit, ('?', '?'))
            w_pa.writerow([g['id'], pit_side, n, batter, bslot, bpos, bh, pit, ph, cat, inn, lead_before,
                           int(reached), kind if reached else '', len(seq) if valid else -1, fp, bl])
            if reached:
                st['ended'] = kind
            else:
                st['n'] = n
    finish(g)


def main():
    raw, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    rost = load_rosters(raw)
    print('giocatori nei roster:', len(rost))
    files = []
    for root, _, names in os.walk(raw):
        for nme in names:
            m = re.match(r'^(\d{4}).{0,4}\.(E[A-Z][A-Z])$', nme, re.I)
            if m:
                files.append((os.path.join(root, nme), nme.rsplit('.', 1)[1].upper()))
    files.sort()
    seen = set()
    nfiles = 0
    with open(os.path.join(outdir, 'pa_streak.csv'), 'w', newline='', encoding='utf-8') as a, \
            open(os.path.join(outdir, 'side_extra.csv'), 'w', newline='', encoding='utf-8') as b, \
            open(os.path.join(outdir, 'pitcher_game.csv'), 'w', newline='', encoding='utf-8') as c, \
            open(os.path.join(outdir, 'team_game.csv'), 'w', newline='', encoding='utf-8') as d:
        w_pa, w_side, w_pit, w_team = csv.writer(a), csv.writer(b), csv.writer(c), csv.writer(d)
        w_pa.writerow('g ps n b bs bp bh pit ph cat inn lead r k np fp bl'.split())
        w_side.writerow('g ps nxt_n nxt_r runs_allowed runs_scored ls_same ls_known'.split())
        w_pit.writerow('g date season pit team pa reach bb'.split())
        w_team.writerow('g date season team pa reach'.split())
        for path, ext in files:
            key = (os.path.basename(path).upper(), os.path.getsize(path))
            if key in seen:
                continue
            seen.add(key)
            if ext[1] != 'V' or ext[2] == 'R':      # solo giocate vere (EV?), non dedotte, non leghe afroamericane
                continue
            nfiles += 1
            process_file(path, rost, w_pa, w_side, w_pit, w_team)
    print('file letti:', nfiles)


if __name__ == '__main__':
    main()
