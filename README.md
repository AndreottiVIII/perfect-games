# Partite perfette: quante restano tali, battitore dopo battitore

Ogni partita di baseball parte come una potenziale partita perfetta. Questo progetto conta,
per ogni squadra al lancio in ogni partita, **quanti battitori avversari consecutivi sono
stati eliminati prima che il primo arrivasse in base**, e ne ricava la curva di
sopravvivenza: quante squadre sono ancora "perfette" dopo 1, 2, 3 ... 27 battitori.

## I dati

- Fonte: i file "evento" di Retrosheet (cronaca azione per azione), stagione regolare,
  1908-2025, scaricati dalle pagine dei file per decennio.
- Due righe per partita (una per squadra al lancio). Il file `data/streaks.csv` ha circa
  413.000 righe. Dentro ci sono anche le leghe afroamericane (`league_file` = R) e la
  Federal League (F), ma i grafici usano solo Lega Americana e Nazionale (e Federal League).
- Le partite "dedotte" da Retrosheet (ricostruite da box score, non da una cronaca vera)
  sono segnate nella colonna `deduced` e **escluse** dalla curva di base.
- Se una squadra non fa arrivare nessuno in base e la partita finisce prima di 27 battitori
  (partita accorciata, o vittoria in casa senza battere nel nono), il caso e' "censurato":
  la curva li conta come ancora perfetti fino all'ultimo battitore affrontato, non oltre.

## Come rifare tutto

Servono Python 3.12, pandas e matplotlib. Dalla cartella del progetto:

```
python -I src/build_streaks.py data/raw data/streaks.csv
python -I src/validate.py data/streaks.csv
python -I src/curve.py data/streaks.csv output
python -I src/chart.py output/curve_by_decade.csv output/curve_overall.csv output
```

I file zip di Retrosheet vanno messi in `data/raw/` (13 file `1900seve.zip` ... `2020seve.zip`
da https://www.retrosheet.org/game.htm) e decompressi ciascuno nella propria sottocartella.
`validate.py` confronta le partite perfette trovate con l'elenco ufficiale MLB.

Risultati: `output/curve_overall.csv`, `output/curve_by_decade.csv` (con anche la probabilita'
condizionata `hazard` che l'n-esimo battitore sia il primo a salire in base),
`output/curve_by_decade.png` e `.svg`.

### Le analisi successive

```
python -I src/come_cala.py data/streaks.csv data/pa_tally.csv output
python -I src/come_cala_chart.py output/come_cala_hazard.csv output
python -I src/chicche.py data/streaks.csv output
```

- `src/come_cala.py`: come cala la curva battitore per battitore (con e senza DH), il modello
  "ogni battitore indipendente" e come finisce la perfezione. Scrive `output/come_cala_*.csv`;
  testo dei risultati in `output/come_cala.md`. `data/pa_tally.csv` lo crea `build_streaks.py`.
- `src/come_cala_chart.py`: il grafico `output/come_cala.png` / `.svg`.
- `src/chicche.py`: le statistiche nascoste (pinch hitter, stadi, specialisti...). Scrive
  `output/chicche_perfette.csv` e `output/chicche_parchi.csv`; testo in `output/chicche.md`.
  Serve anche scipy.
- `src/ca_common.py`: funzioni comuni (caricamento dei dati con le esclusioni, intervalli).

### La tortura dei dati

```
python -I src/tortura_extract.py data/raw data
python -I src/tortura_check.py data
python -I src/verifiche.py data output
python -I src/tortura.py pari data output
python -I src/tortura.py dispari data output
python -I src/tortura.py riepilogo data output
python -I src/tortura_extra.py data output
```

- `src/tortura_extract.py` rilegge i file Retrosheet e scrive `data/pa_streak.csv` (un turno per riga nelle serie perfette), `side_extra.csv`, `pitcher_game.csv`, `team_game.csv`. Il resto (`tortura_lib.py`, `verifiche.py`, `tortura.py`, `tortura_extra.py`, `tortura_check.py`) li usa.
- Regola: stagioni pari = scoperta, dispari = conferma; le ipotesi sono in `output/tortura_ipotesi.md`. Risultati: `output/verifiche.md` e `output/tortura.md`.

## Il sito

Il sito sta nella cartella `docs/` (GitHub Pages: ramo main, cartella /docs). Sei pagine:
La curva, Come cala, Giornata di grazia, Chicche, Le 21 partite, Gli stadi.

- Le pagine HTML (`docs/*.html`), lo stile (`docs/style.css`) e i grafici (`docs/charts.js`,
  JavaScript semplice, nessuna libreria) sono scritti a mano.
- `src/build_site.py` legge i risultati in `output/` e `data/streaks.csv`, scrive i dati dei
  grafici in `docs/data/*.json` e li inserisce nelle pagine insieme alle tabelle (le 21 partite,
  le quasi perfette, le epoche, gli stadi). Cambia solo cio' che sta tra i segnaposto
  `<!-- build:... -->` e `<!-- /build:... -->`.
- `src/stadi_nomi.csv`: nomi degli stadi per codice Retrosheet (scritto a mano).

Per rifare il sito dopo aver rifatto le analisi:

```
python src\build_site.py
```

## Nota: la partita di Galarraga

Il 2 giugno 2010 Armando Galarraga (Detroit, contro Cleveland) eliminò 26 battitori; al 27esimo
l'arbitro Jim Joyce dichiarò salvo Jason Donald su una battuta a terra, ma la chiamata era
sbagliata e l'arbitro lo ammise a fine partita. **Considerarla perfetta e' una scelta di
Davide**: l'MLB non la riconosce ufficialmente come partita perfetta. Nel codice e' una
correzione manuale esplicita (`src/overrides.csv`): quella squadra al lancio e' trattata come
27 eliminati, nessuno in base, partita completa. I valori originali restano visibili nelle
colonne `batters_retired_raw` e `first_runner_event_raw` di `data/streaks.csv`; la curva e la
validazione usano il valore corretto. Per toglierla basta svuotare `src/overrides.csv`.

## Retrosheet

The information used here was obtained free of charge from and is copyrighted by Retrosheet.
Interested parties may contact Retrosheet at "www.retrosheet.org".
