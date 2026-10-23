"""Confronta le partite perfette trovate con l'elenco ufficiale MLB (dal 1904 in poi).
Uso: python -I validate.py <streaks.csv>
"""
import sys
import pandas as pd

# (data, cognome, id Retrosheet del lanciatore partente). Young 1904 e Larsen 1956 (World Series) non
# sono nei file della stagione regolare 1908-2025.
UFFICIALI = [
    ('1904-05-05', 'Cy Young', None), ('1908-10-02', 'Addie Joss', 'jossa101'),
    ('1922-04-30', 'Charlie Robertson', 'robec101'), ('1956-10-08', 'Don Larsen (World Series)', None),
    ('1964-06-21', 'Jim Bunning', 'bunnj101'), ('1965-09-09', 'Sandy Koufax', 'koufs101'),
    ('1968-05-08', 'Catfish Hunter', 'huntj101'), ('1981-05-15', 'Len Barker', 'barkl001'),
    ('1984-09-30', 'Mike Witt', 'wittm001'), ('1988-09-16', 'Tom Browning', 'browt001'),
    ('1991-07-28', 'Dennis Martinez', 'martd001'), ('1994-07-28', 'Kenny Rogers', 'rogek001'),
    ('1998-05-17', 'David Wells', 'welld001'), ('1999-07-18', 'David Cone', 'coned001'),
    ('2004-05-18', 'Randy Johnson', 'johnr005'), ('2009-07-23', 'Mark Buehrle', 'buehm001'),
    ('2010-05-09', 'Dallas Braden', 'bradd002'), ('2010-05-29', 'Roy Halladay', 'hallr001'),
    ('2012-04-21', 'Philip Humber', 'humbp001'), ('2012-06-13', 'Matt Cain', 'cainm001'),
    ('2012-08-15', 'Felix Hernandez', 'hernf002'), ('2023-06-28', 'Domingo German', 'germd001'),
    ('2010-06-02', 'Armando Galarraga (override di Davide)', 'galaa002'),
]

d = pd.read_csv(sys.argv[1], low_memory=False)
d = d[d.league_file.isin(['A', 'N', 'F'])]
found = d[(d.batters_retired >= 27) & (d.first_runner_event == 'nessuno') & (d.game_status == 'completa')]
print('Lati con >=27 eliminati e nessun battitore in base, partita completa:', len(found))
ok = 0
for date, name, pid in UFFICIALI:
    hit = found[(found.date == date) & (found.starting_pitcher == pid)] if pid else found.iloc[0:0]
    if len(hit):
        ok += 1
        print('  TROVATA ', date, name)
    else:
        print('  MANCANTE', date, name, '' if pid else '(fuori dai dati: non e\' nella stagione regolare 1908-2025)')
extra = found[~found.starting_pitcher.isin([u[2] for u in UFFICIALI if u[2]])]
print('Trovate in piu\' rispetto all\'elenco:', len(extra))
if len(extra):
    print(extra[['game_id', 'date', 'pitching_team', 'starting_pitcher']].to_string(index=False))
print('Deduced fra le perfette trovate:', int(found.deduced.sum()))
print('\nCasi vicini (>=26 eliminati, poi un battitore in base) - le piu\' lunghe:')
near = d[(d.batters_retired >= 26) & (d.first_runner_event != 'nessuno')].sort_values('batters_retired', ascending=False)
print(near[['date', 'pitching_team', 'starting_pitcher', 'batters_retired', 'batters_retired_raw',
            'first_runner_event', 'last_inning', 'breaker_slot']].head(15).to_string(index=False))
h = d[(d.date == '1959-05-26') & (d.pitching_team == 'PIT')]
print('\nHaddix 26/5/1959:', h[['batters_retired', 'first_runner_event', 'last_inning']].to_dict('records'))
