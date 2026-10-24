# Tortura dei dati: che cosa regge e che cosa cade

Come è stato fatto, in breve. Le stagioni pari sono la **scoperta**, quelle dispari la **conferma**; le ipotesi sono scritte in `output/tortura_ipotesi.md` prima di guardare le dispari. Misura principale: ognuno dei 1,18 milioni di turni di battuta dentro una serie "perfetta finora" (battitori 1-27, 402.184 squadre al lancio) è una prova sì/no, "il battitore arriva in base?", con una regressione che tiene fisso stagione, numero del battitore e DH. Il risultato è un rapporto di probabilità (**OR**) con intervallo al 95%: sotto 1 le serie perfette durano di più, sopra 1 meno. Errori standard raggruppati per partita. Un risultato **sopravvive** solo se è significativo (p < 0,05) in tutte e due le metà con lo stesso segno. Programmi: `src/tortura_extract.py` (estrae i turni dai file Retrosheet, anche mano di battuta/lancio, punti, lanci), `src/tortura_lib.py`, `src/tortura.py`, `src/tortura_extra.py`, `src/tortura_check.py` (controlla che l'estrazione coincida con `streaks.csv`: eliminati e primo arrivato in base uguali su tutte le 402.184 squadre).

**Quante ipotesi.** 25 dichiarate in anticipo, più 4 varianti scritte dopo aver visto le pari (con la ragione, nel file delle ipotesi): 29 test, più le 3 verifiche (`verifiche.md`). Per sopravvivere servono due p < 0,05: se non ci fosse nulla, 29 test darebbero in media 29 x 0,05 x 0,05 = 0,07 falsi sopravvissuti. Sopravvivono 15 test (14 ipotesi distinte): 7 sono cose già note usate come controllo del metodo, 2 sono sopravvissute per una confusione (spiegate sotto), restano **5 risultati nuovi**: la squadra di casa al lancio, la temperatura, il primo lancio in gioco, il premio del primo battitore, e il primo lancio come momento della rottura.

## Cosa è sopravvissuto (dal più interessante)

Per la "quota che arriva a 18 battitori" applico l'OR a ogni battitore sul profilo medio dei dati: è un ordine di grandezza, non una previsione.

**1. Chi lancia in casa dura di più.** OR **0,915** [0,905-0,925] nelle pari (585.042 turni), **0,916** [0,906-0,926] nelle dispari. Già al primo battitore della partita il tasso di arrivo in base è 33,6% quando lancia la casa e 36,4% quando lancia la squadra in trasferta. Su tutta la serie, la probabilità di arrivare a 9 battitori eliminati è circa 1,28 volte, e quella di arrivare a 18 circa 1,6 volte. Non sparisce tenendo conto della forza dell'attacco e del lanciatore (OR 0,915) né dello stadio (0,914-0,916); c'è in ogni epoca (0,96 nel 1908-19, 0,90-0,93 dopo). I dati non dicono perché (vantaggio del campo, arbitri, il lanciatore ospite che aspetta mentre la sua squadra batte...); è la conferma più forte dopo i controlli.

**2. Più caldo, più battitori in base.** OR **1,019** [1,012-1,027] per +10 gradi Fahrenheit nelle pari (290.000 turni con temperatura nota, quasi tutti dal 1990), **1,020** [1,012-1,027] nelle dispari. Resta con stadio e giorno/notte (1,016), con stadio e mese (1,017-1,026) e dal 1995 (1,017-1,019): non è il clima del posto. Circa -10% sulla probabilità di arrivare a 18 battitori ogni +10 gradi: da 50 a 90 gradi, circa due terzi. (La scheda precedente aveva visto solo un'ombra, p = 0,03-0,04 su quattro fasce: con tutti i turni è chiara.)

**3. Più si va avanti, più il battitore tocca il primo lancio.** Dal 1988, nei battitori 1-9, 10-18, 19-27: il primo lancio è strike nel 50,1%, 49,0%, 47,2%; viene messo in gioco nel 9,0%, 11,6%, 13,0%; e le rotture che non sono basi su ball sono decise al primo lancio nel 13,0%, 15,9%, 20,2% dei casi. Primo lancio strike, profondi (10+) contro iniziali: OR **0,955** [0,915-0,997] pari, **0,938** [0,900-0,978] dispari. Rottura al primo lancio (tolte le basi su ball, perché hanno almeno 4 lanci): OR **1,30** [1,16-1,46] pari, **1,24** [1,11-1,39] dispari. Lettura prudente: la perfezione non cade con conteggi alti più spesso, cade più spesso per un colpo al primo lancio, mentre i battitori che rivedono il lanciatore diventano più impazienti.

**4. Il premio del primo battitore si è ridotto.** Il tasso di arrivo in base del primo battitore della partita (n = 1) sugli altri della prima parte (n = 2-8): rapporto 1,108 nel 1908-19, poi 1,029, 1,025, 1,014, 1,043, 1,025 (2000-25). OR per decennio **0,994** [0,990-0,998] pari, **0,993** [0,989-0,997] dispari: effetto piccolo ma coerente. Quanto spesso il primo battitore della partita rovina tutto: 38,7% nel 1908-19, 37,2%, 35,7%, 33,9%, 35,1%, 33,5% nel 2000-25. Il primo battitore non sta arrivando in base di più: cala come tutti.

**Controlli che confermano il metodo** (cose note, ritrovate con lo stesso OR nelle due metà: se il metodo non le avesse trovate non ci si poteva fidare):
- Forza del lanciatore in campo (stagione): OR 1,093 [1,087-1,100] pari, 1,095 [1,089-1,101] dispari per +1 deviazione standard; quota che arriva a 18 battitori circa x0,60. Carriera fino a quel giorno: 1,075 e 1,073 (x0,66). È di gran lunga il fattore più forte.
- Forza dell'attacco avversario (stagione): 1,044 e 1,046 per +1 deviazione standard (x0,78).
- Mano: battitore con la stessa mano del lanciatore: 0,921 [0,910-0,932] e 0,920 [0,909-0,931] (se tutti i battitori fossero della stessa mano rispetto a tutti della mano opposta, la quota che arriva a 18 sarebbe circa x1,57). La quota di "stessa mano" nella formazione iniziale, invece, non conta (vedi sotto).
- Monte abbassato nel 1969: 1,058 [1,022-1,096] e 1,064 [1,028-1,101].
- DH universale dal 2022, nel solo turno del lanciatore (battitori 9, 18, 27; variante scritta dopo le pari): OR 2,19 [1,24-3,86] e 2,19 [1,30-3,67]; stesso ordine di grandezza del 28,5% contro il 19,5% di `come_cala.md`.
- Errori tra le rotture, per decennio: 0,910 e 0,913 (dal 5,3% del 1908-45 al 2,3% dal 2009).

**Sopravvissuti per confusione, non per un effetto vero**
- *Prima volta che il partente affronta quella squadra* (T18): OR 1,036 e 1,029, segno contrario all'atteso: perché chi affronta una squadra una sola volta in stagione è mediamente più scarso. Con la variante controllata (solo chi la affronta 2+ volte, con la qualità del lanciatore nel modello): 1,000 [0,987-1,013] nelle pari e 0,979 [0,966-0,991] nelle dispari. Non c'è effetto "la prima volta".
- *Ricevitore* (T24): gli effetti dei ricevitori delle stagioni pari si ripetono nelle dispari (pendenza 0,27 [0,19-0,36], correlazione di rango 0,30, 493 ricevitori con 300+ turni in ogni metà). Ma tolto l'effetto squadra-stagione la pendenza scende a 0,10 ± 0,10 (correlazione 0,09) e tolto il lanciatore-stagione a 0,06 ± 0,10. I "buoni ricevitori" sono squadre e staff di lanciatori buoni, non un effetto della persona. (Questo controllo l'ho fatto dopo aver visto le dispari; non cambia quali ipotesi sono sopravvissute ma cambia come si leggono.)

## Provate e cadute (una riga ciascuna; pari poi dispari)

- Quota di battitori della stessa mano nella formazione iniziale (T05): OR per +1 deviazione standard 0,989 (p = 0,0004) poi 0,995 (p = 0,09): effetto minuscolo, già tutto nel singolo turno.
- DH nella Lega Americana dal 1973, su tutti i turni (T07): 0,935 (p = 0,04, segno opposto all'atteso) poi 0,968 (p = 0,32): il DH tocca 1 battitore su 9 e le due leghe non andavano in parallelo. Variante solo turno del lanciatore (T07r): 0,74 [0,39-1,39] poi 2,70 [1,42-5,12]: segni opposti su circa 1.000 turni, non vale.
- DH universale dal 2022, su tutti i turni (T08): 0,956 poi 1,049, nulla (la variante sul turno del lanciatore invece regge).
- Orologio dei lanci e divieto dello shift dal 2023 (T09): 0,957 (p = 0,04) poi 0,963 (p = 0,09): dopo il 2023 un po' meno arrivi in base, ma non confermato.
- Squadre di espansione al primo anno (T10): 1,075 (p = 0,15) poi 1,100 (p = 0,005): c'è solo nelle dispari (1961, 1969, 1977, 1993), non nelle pari (1962, 1998). Non conta.
- Integrazione, NL contro AL 1950-59 contro 1938-46 (T11): 0,996 poi 0,959, nulla.
- Seconda partita di un doppio incontro (T12): 1,013 poi 1,009, nulla.
- Diurna dopo notturna, squadra al bat (T13): 0,980 (p = 0,047) poi 0,984 (p = 0,12): stesso segno, non confermato.
- Il giorno dopo i supplementari (T14): 0,997 poi 1,000, nulla.
- Settembre-ottobre contro aprile-agosto (T15): 0,972 (p = 0,0001) nelle pari, 0,995 (p = 0,47) nelle dispari: sparito. Esempio perfetto di falso positivo.
- Vantaggio di 4+ punti, battitori 10+ (T16): 1,012 poi 0,942 (p = 0,13); solo 19+: 1,23 e 0,91 su 700-840 turni. Nessuna differenza tra partita chiusa e partita in bilico.
- Sfilacciamento dopo la prima rottura (T22): dopo la prima rottura, nei tre battitori successivi ne arrivano in base il 39,4% (rottura ai battitori 1-9), 38,1% (10-18), 36,7% (19-27); OR per rottura tardiva 0,94 [0,81-1,09] poi 0,87 [0,74-1,02]: le serie lunghe non "crollano" dopo la prima base, ma nemmeno tengono in modo dimostrabile. Descrizione (non un test): se la rottura non è un colpo (base su ball, errore, colpito), il no-hitter sopravvive nel 13,3% dei casi (16 su 120) quando cade tra i battitori 19-27, nell'1,6% tra il 10 e il 18, nello 0,1% prima; zero punti subiti nella partita: 43%, 18%, 7% (campione piccolo per il 19-27).

## Non ho provato (e perché)

- I conteggi a 3 palle come ipotesi a parte: le basi su ball sono già tutte nella verifica 2 e nella rottura al primo lancio (T20r).
- Arbitri dietro casa base: già nulli in `chicche.md` (294 arbitri, p = 0,96 e 0,31); non li ho rifatti.
- Ricevitori e lanciatori uno per uno: i campioni sono troppo piccoli per un nome; ho provato solo se l'effetto "ricevitore" si ripete (T24), ed è la squadra.
- "Ultime partite della stagione" come finestra a parte: coperto in parte da settembre-ottobre (T15), caduto.
