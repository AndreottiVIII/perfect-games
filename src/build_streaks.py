"""Legge i file evento di Retrosheet (stagione regolare) e per ogni partita e per
ogni squadra al lancio conta quanti battitori consecutivi sono stati eliminati
prima che il primo arrivasse in base. Raccoglie anche i campi info (arbitro, meteo, stadio),
i lanci e un conteggio di tutti i turni di battuta per stagione (data/pa_tally.csv, accanto al
file di uscita).

Uso:  python -I build_streaks.py <cartella_raw> <file_csv_uscita> [overrides.csv]
"""
import csv
import os
import re
import sys
from collections import Counter

# ---------------------------------------------------------------- classificazione
RE_HIT = re.compile(r'^(S|D(?!I)|T|H(?!P))')
NON_PA = ('NP', 'BK', 'CS', 'DI', 'OA', 'PB', 'WP', 'PO', 'SB', 'FLE')
# l'ordine conta: i prefissi piu' lunghi prima
unknown_codes = Counter()

# caratteri della stringa dei lanci Retrosheet che sono lanci veri (non pickoff, non modificatori)
PITCH_CHARS = frozenset('BCFHIKLMOPQRSTUVXY')
HIT_KINDS = ('singolo', 'doppio', 'triplo', 'fuoricampo')
INFO_FIELDS = ('umphome', 'temp', 'winddir', 'windspeed', 'daynight', 'site', 'attendance',
               'fieldcond', 'precip', 'sky', 'number')

# Correzioni manuali (file overrides.csv): (game_id, squadra al lancio) -> motivo
OVERRIDES = {}


def load_overrides(path):
    with open(path, encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            OVERRIDES[(r['game_id'].strip(), r['side'].strip())] = r['reason'].strip()


def classify(event):
    """Restituisce (e_un_turno_completato, battitore_in_base, tipo)."""
    ev = event.replace('!', '').replace('?', '').replace('#', '').strip()
    if '.' in ev:
        basic, adv = ev.split('.', 1)
    else:
        basic, adv = ev, ''
    main = basic.split('/')[0]
    mods = basic.split('/')[1:]
    head = main.split('+')[0]

    # --- eventi che non sono un turno di battuta
    if head.startswith(NON_PA) and not head.startswith('FC'):
        return False, False, 'nonpa'
    if head == '':
        return False, False, 'nonpa'

    # --- il battitore arriva in base per come e' scritta l'azione
    if head.startswith('HP'):
        return True, True, 'colpito'
    if RE_HIT.match(head):
        if head[0] == 'S':
            return True, True, 'singolo'
        if head[0] == 'D':
            return True, True, 'doppio'
        if head[0] == 'T':
            return True, True, 'triplo'
        return True, True, 'fuoricampo'
    if head.startswith('IW') or head == 'I':
        return True, True, 'base_intenzionale'
    if head.startswith('W'):
        return True, True, 'base_su_ball'
    if head == 'C' or (head.startswith('C') and not head.startswith('CS')):
        return True, True, 'interferenza_ricevitore'
    if head.startswith('E') and len(head) > 1 and head[1].isdigit():
        return True, True, 'errore'
    if head.startswith('FC'):
        return True, True, 'scelta_difensiva'

    # --- strikeout: terza strike persa solo se l'avanzamento sposta il battitore
    batter_adv_safe = re.search(r'(?:^|;)B-', adv) is not None
    if head.startswith('K'):
        if batter_adv_safe:
            return True, True, 'terza_strike_persa'
        return True, False, 'strikeout'

    # --- eliminazioni in campo (iniziano con un numero di ruolo)
    if head[0].isdigit():
        # errore dopo un tocco di un altro difensore (es. 6E3): il battitore e' salvo
        # anche se l'avanzamento B-1 e' sottinteso
        if re.search(r'E\d', head) and not re.search(r'(?:^|;)BX', adv):
            return True, True, 'errore'
        if batter_adv_safe:
            return True, True, 'altro_in_base'
        if 'FO' in mods and 'GDP' not in mods and 'GTP' not in mods:
            # forzato: il battitore resta salvo in prima (puo' succedere solo con corridori)
            return True, True, 'scelta_difensiva'
        return True, False, 'eliminato'

    unknown_codes[head[:4]] += 1
    return True, False, 'sconosciuto'


# ---------------------------------------------------------------- lettura partite
def parse_csv_line(line):
    return next(csv.reader([line]))


def decade_of(season):
    return season // 10 * 10


def process_file(path, deduced, filetype, writer, stats, tally):
    with open(path, encoding='latin-1', newline='') as fh:
        lines = fh.read().splitlines()

    game = None

    def finish(game):
        if game is None:
            return
        for side in (0, 1):   # side = squadra al lancio: 0 visitatori, 1 casa
            st = game['side'][side]
            last_inn = game['last_inn']
            if st['ended'] is not None:
                reason = st['ended']
            elif st['n'] >= 27:
                reason = 'perfetta'
            elif last_inn < 9:
                reason = 'partita_corta'
            else:
                reason = 'finita_senza_battere'
            game_status = 'completa' if last_inn >= 9 else 'abbreviata'
            row = {
                'game_id': game['id'],
                'date': game['date'],
                'season': game['season'],
                'decade': decade_of(game['season']),
                'pitching_team': game['teams'][side],
                'batting_team': game['teams'][1 - side],
                'pitching_side': 'casa' if side == 1 else 'ospite',
                'batters_retired': st['n'],
                'first_runner_event': st['ended'] if st['ended'] else 'nessuno',
                'censored': 0 if (st['ended'] or st['n'] >= 27) else 1,  # 1 = finita prima di poter arrivare a 27, senza battitori in base
                'ended_reason': reason,
                'game_status': game_status,
                'last_inning': last_inn,
                'deduced': int(deduced),
                'league_file': filetype,
                'dh': game['dh'],
                'breaker_slot': st['slot'],
                'breaker_pos': st['pos'],
                'breaker_player': st['player'],
                'breaker_pitcher': st['pitcher_at_break'],
                'starting_pitcher': st['start_pitcher'],
                'pitchers_before_break': len(st['pitchers']),
            }
            row.update({k: game['info'].get(k, '') for k in INFO_FIELDS})
            row.update(
                bat_dh=game['start_dh'][1 - side],      # la squadra al bat aveva un DH nella formazione iniziale
                hits_allowed=game['hits'][side],
                pitches_retired=st['pitches'], pa_with_pitches=st['pitch_pa'],
                pitches_all_valid=int(st['pitch_pa'] == st['n'] and st['n'] > 0),
                ks_retired=st['ks'],
                last_event=st['last_event'], last_count=st['last_count'],
                last_pa_pitches=st['last_pitches'], breaker_inning=st['break_inn'],
                last_pos=st['last_pos'], last_batter=st['last_batter'])
            row['batters_retired_raw'] = row['batters_retired']
            row['first_runner_event_raw'] = row['first_runner_event']
            row['override_reason'] = ''
            ov = OVERRIDES.get((game['id'], row['pitching_side']))
            if ov:
                # partita perfetta per scelta esplicita: 27 eliminati, nessun battitore in base
                row.update(batters_retired=27, first_runner_event='nessuno', censored=0,
                           ended_reason='perfetta', game_status='completa',
                           breaker_slot='', breaker_pos='', breaker_player='',
                           breaker_pitcher='', override_reason=ov)
                stats['override_applicati'] += 1
            writer.writerow(row)
            stats['rows'] += 1

    for line in lines:
        if not line:
            continue
        tag = line.split(',', 1)[0]
        if tag == 'id':
            finish(game)
            gid = line.split(',')[1].strip()
            game = {
                'id': gid, 'date': '', 'season': int(gid[3:7]), 'teams': ['', ''],
                'dh': '', 'last_inn': 0, 'info': {}, 'start_dh': [0, 0], 'pa': [0, 0],
                'hits': [0, 0], 'hi': [None, None, True],
                'pitcher': ['', ''],
                'lineup': [dict(), dict()],     # player -> (slot, pos)
                'side': [dict(n=0, ended=None, slot='', pos='', player='',
                              pitcher_at_break='', start_pitcher='', pitchers=[],
                              pitches=0, pitch_pa=0, ks=0, last_event='', last_count='',
                              last_pitches='', break_inn='', last_pos='', last_batter='')
                         for _ in range(2)],
            }
            stats['games'] += 1
            continue
        if game is None:
            continue
        if tag == 'info':
            f = parse_csv_line(line)
            if f[1] == 'visteam':
                game['teams'][0] = f[2]
            elif f[1] == 'hometeam':
                game['teams'][1] = f[2]
            elif f[1] == 'date':
                game['date'] = f[2].replace('/', '-')
            elif f[1] == 'usedh':
                game['dh'] = int(f[2].lower() == 'true')
            if f[1] in INFO_FIELDS:
                game['info'][f[1]] = f[2].strip()
        elif tag in ('start', 'sub'):
            f = parse_csv_line(line)
            pid, team, slot, pos = f[1], int(f[3]), int(f[4]), int(f[5])
            game['lineup'][team][pid] = (slot, pos)
            if tag == 'start' and pos == 10:
                game['start_dh'][team] = 1
            if pos == 1:
                # team = 0 visitatori: il suo lanciatore e' la squadra al lancio 0
                game['pitcher'][team] = pid
                if not game['side'][team]['start_pitcher']:
                    game['side'][team]['start_pitcher'] = pid
                if pid not in game['side'][team]['pitchers']:
                    game['side'][team]['pitchers'].append(pid)
        elif tag == 'play':
            f = parse_csv_line(line)
            inn, bat_side, batter, event = int(f[1]), int(f[2]), f[3], f[6]
            game['last_inn'] = max(game['last_inn'], inn)
            is_pa, reached, kind = classify(event)
            if not is_pa:
                continue
            pit_side = 1 - bat_side
            # --- conteggio di tutti i turni di battuta (per il modello "nullo" e i lanci medi)
            bslot, bpos = game['lineup'][bat_side].get(batter, ('', ''))
            game['pa'][bat_side] += 1
            tto = min((game['pa'][bat_side] - 1) // 9 + 1, 4)
            hi = game['hi']
            if hi[0] != inn or hi[1] != bat_side:
                hi[:] = [inn, bat_side, True]
            bases_empty = int(hi[2] and inn <= 9)    # nessuno e' ancora arrivato in base in questo mezzo inning
            pstr, count = f[5], f[4]
            npitch = sum(1 for c in pstr if c in PITCH_CHARS)
            pvalid = int(npitch > 0 and '?' not in pstr)
            t = tally.setdefault((game['season'], filetype, int(deduced), bslot or 0, int(bpos == 1), tto, bases_empty),
                                 [0, 0, 0, 0])
            t[0] += 1
            t[1] += int(reached)
            if pvalid:
                t[2] += 1
                t[3] += npitch
            if reached:
                hi[2] = False
                if kind in HIT_KINDS:
                    game['hits'][pit_side] += 1
            st = game['side'][pit_side]
            if st['ended'] is not None:
                continue
            if reached:
                st['ended'] = kind
                slot, pos = bslot, bpos
                st['slot'], st['pos'], st['player'] = slot, pos, batter
                st['pitcher_at_break'] = game['pitcher'][pit_side]
                st['break_inn'] = inn
            else:
                st['n'] += 1
                if pvalid:
                    st['pitch_pa'] += 1
                    st['pitches'] += npitch
                if kind == 'strikeout':
                    st['ks'] += 1
                st['last_event'], st['last_count'] = event[:14], count
                st['last_pitches'] = npitch if pvalid else ''
                st['last_pos'], st['last_batter'] = bpos, batter
                if kind == 'sconosciuto':
                    stats['unknown_events'] += 1
                if game['pitcher'][pit_side] not in st['pitchers']:
                    st['pitchers'].append(game['pitcher'][pit_side])
    finish(game)


COLUMNS = ['game_id', 'date', 'season', 'decade', 'pitching_team', 'batting_team',
           'pitching_side', 'batters_retired', 'first_runner_event', 'censored',
           'ended_reason', 'game_status', 'last_inning', 'deduced', 'league_file', 'dh',
           'breaker_slot', 'breaker_pos', 'breaker_player', 'breaker_pitcher',
           'starting_pitcher', 'pitchers_before_break',
           'batters_retired_raw', 'first_runner_event_raw', 'override_reason',
           'umphome', 'temp', 'winddir', 'windspeed', 'daynight', 'site', 'attendance',
           'fieldcond', 'precip', 'sky', 'number', 'bat_dh', 'hits_allowed',
           'pitches_retired', 'pa_with_pitches', 'pitches_all_valid', 'ks_retired',
           'last_event', 'last_count', 'last_pa_pitches', 'breaker_inning',
           'last_pos', 'last_batter']


def main():
    raw_dir, out_path = sys.argv[1], sys.argv[2]
    ov_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'overrides.csv')
    load_overrides(ov_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    stats = Counter()
    tally = {}
    files = []
    for root, _, names in os.walk(raw_dir):
        for n in names:
            m = re.match(r'^(\d{4}).{0,4}\.(E[A-Z][A-Z])$', n, re.I)
            if m:
                files.append((os.path.join(root, n), n.rsplit('.', 1)[1].upper()))
    files.sort()
    with open(out_path, 'w', newline='', encoding='utf-8') as out:
        w = csv.DictWriter(out, fieldnames=COLUMNS)
        w.writeheader()
        seen = set()
        for path, ext in files:
            key = (os.path.basename(path).upper(), os.path.getsize(path))
            if key in seen:               # 1908-09 compaiono in due archivi: leggere una volta sola
                stats['file_doppi_saltati'] += 1
                continue
            seen.add(key)
            if ext[1] not in 'VD':        # solo EV? (giocate) e ED? (dedotte)
                continue
            stats['files'] += 1
            stats['ext_' + ext] += 1
            process_file(path, ext[1] == 'D', ext[2], w, stats, tally)
    tally_path = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'pa_tally.csv')
    with open(tally_path, 'w', newline='', encoding='utf-8') as out:
        tw = csv.writer(out)
        tw.writerow(['season', 'league_file', 'deduced', 'slot', 'is_pitcher', 'tto', 'bases_empty',
                     'pa', 'reach', 'pa_pitch', 'pitches'])
        for k in sorted(tally):
            tw.writerow(list(k) + tally[k])
    print('file letti:', stats['files'], '| partite:', stats['games'],
          '| righe scritte:', stats['rows'])
    print('correzioni manuali applicate:', stats['override_applicati'])
    print('file doppi saltati:', stats['file_doppi_saltati'])
    print('estensioni:', {k[4:]: v for k, v in stats.items() if k.startswith('ext_')})
    print('turni di tipo sconosciuto (contati come eliminati):', stats['unknown_events'],
          dict(unknown_codes.most_common(10)))


if __name__ == '__main__':
    main()
