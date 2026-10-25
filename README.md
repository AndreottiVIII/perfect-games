# Perfect games: how many stay perfect, batter by batter

Every baseball game starts out as a potential perfect game. For each pitching side in every
game, this project counts **how many opposing batters were retired in a row before the first
one reached base**, and turns that into a survival curve: how many sides are still "perfect"
after 1, 2, 3 ... 27 batters.

Website: https://andreottiviii.github.io/perfect-games/

## The data

- Source: Retrosheet "event files" (play-by-play), regular season, 1908-2025, downloaded
  from the per-decade file pages.
- Two rows per game (one for each pitching side). The file `data/streaks.csv` has about
  413,000 rows. It also contains the Negro Leagues (`league_file` = R) and the Federal
  League (F), but the charts use only the American and National Leagues (plus the Federal League).
- Games that Retrosheet "deduced" (rebuilt from box scores rather than from a real
  play-by-play) are flagged in the `deduced` column and **left out** of the base curve.
- If a side lets nobody reach base and the game ends before 27 batters (a shortened game,
  or a home team that wins without batting in the ninth), the case is "censored": the
  curve counts it as still perfect up to the last batter faced, and no further.

## How to rebuild everything

You need Python 3.12, pandas and matplotlib. From the project folder:

```
python -I src/build_streaks.py data/raw data/streaks.csv
python -I src/validate.py data/streaks.csv
python -I src/curve.py data/streaks.csv output
python -I src/chart.py output/curve_by_decade.csv output/curve_overall.csv output
```

The Retrosheet zip files go in `data/raw/` (13 files, `1900seve.zip` ... `2020seve.zip`,
from https://www.retrosheet.org/game.htm), each unzipped into its own subfolder.
`validate.py` checks the perfect games it finds against MLB's official list.

Results: `output/curve_overall.csv`, `output/curve_by_decade.csv` (which also has the
conditional probability `hazard` that batter n is the first to reach base),
`output/curve_by_decade.png` and `.svg`.

### The follow-up analyses

```
python -I src/come_cala.py data/streaks.csv data/pa_tally.csv output
python -I src/come_cala_chart.py output/come_cala_hazard.csv output
python -I src/chicche.py data/streaks.csv output
```

- `src/come_cala.py`: how the curve falls batter by batter (with and without a DH), the
  "every batter independent" model, and how perfect games end. Writes `output/come_cala_*.csv`;
  write-up in `output/come_cala.md`. `data/pa_tally.csv` is created by `build_streaks.py`.
- `src/come_cala_chart.py`: the chart `output/come_cala.png` / `.svg`.
- `src/chicche.py`: the hidden statistics (pinch hitters, ballparks, specialists...). Writes
  `output/chicche_perfette.csv` and `output/chicche_parchi.csv`; write-up in `output/chicche.md`.
  Also needs scipy.
- `src/ca_common.py`: shared functions (loading the data with the exclusions, intervals).

### The torture test

```
python -I src/tortura_extract.py data/raw data
python -I src/tortura_check.py data
python -I src/verifiche.py data output
python -I src/tortura.py pari data output
python -I src/tortura.py dispari data output
python -I src/tortura.py riepilogo data output
python -I src/tortura_extra.py data output
```

- `src/tortura_extract.py` re-reads the Retrosheet files and writes `data/pa_streak.csv` (one plate appearance per row inside perfect runs), `side_extra.csv`, `pitcher_game.csv`, `team_game.csv`. The rest (`tortura_lib.py`, `verifiche.py`, `tortura.py`, `tortura_extra.py`, `tortura_check.py`) use them.
- Rule: even seasons = discovery, odd seasons = confirmation; the hypotheses are in `output/tortura_ipotesi.md`. Results: `output/verifiche.md`, `output/tortura.md` and `output/tortura_risultati.csv`.
- The working reports in `output/*.md` and the code comments are in Italian.

## The website

The site lives in the `docs/` folder (GitHub Pages: main branch, /docs folder). Seven pages:
The curve, How it falls, Grace days, Hidden gems, The 21 games, Ballparks, Torture test.
The old Italian addresses (`come-cala.html`, `giornata-di-grazia.html`, `chicche.html`,
`partite.html`, `stadi.html`) are small pages that redirect to the new ones.

- The HTML pages (`docs/*.html`), the style sheet (`docs/style.css`) and the charts (`docs/charts.js`,
  plain JavaScript, no libraries) are written by hand.
- `src/build_site.py` reads the results in `output/` and `data/streaks.csv`, writes the chart
  data to `docs/data/*.json` and inserts it into the pages together with the tables (the 21
  games, the near misses, the eras, the ballparks) and the Torture test chart data. It only
  changes what sits between the `<!-- build:... -->` and `<!-- /build:... -->` markers, so any
  text inside those blocks has to be changed in `build_site.py`.
- `src/stadi_nomi.csv`: ballpark names by Retrosheet code (written by hand).

To rebuild the site after re-running the analyses:

```
python src\build_site.py
```

## Note: Galarraga's game

On June 2, 2010 Armando Galarraga (Detroit, against Cleveland) retired 26 batters; on the
27th, umpire Jim Joyce called Jason Donald safe on a ground ball, but the call was wrong
and Joyce admitted it after the game. **Counting it as a perfect game is Davide's choice**:
MLB does not officially recognise it as a perfect game. In the code it is an explicit manual
correction (`src/overrides.csv`): that pitching side is treated as 27 retired, nobody on base,
complete game. The original values remain visible in the `batters_retired_raw` and
`first_runner_event_raw` columns of `data/streaks.csv`; the curve and the validation use the
corrected value. To remove it, just empty `src/overrides.csv`.

## Retrosheet

The information used here was obtained free of charge from and is copyrighted by Retrosheet.
Interested parties may contact Retrosheet at "www.retrosheet.org".
