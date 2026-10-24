# Tortura: le ipotesi, scritte prima di guardare le stagioni dispari

Regola: **scoperta = stagioni pari** (si può guardare, esplorare, correggere la definizione); **conferma = stagioni dispari** (si guardano solo dopo che l'ipotesi è scritta qui, una volta sola). Un risultato "sopravvive" solo se è significativo (p < 0,05, bilaterale) in tutti e due gli insiemi e con lo stesso segno. Gli esperimenti naturali (regole cambiate in un anno preciso) usano finestre di anni pari per la scoperta e finestre di anni dispari per la conferma, indicate sotto.

**Misura di base.** Ogni turno di battuta dentro una serie "perfetta finora" (battitori n = 1..27, file `data/pa_streak.csv`) è una prova sì/no: il battitore arriva in base? Modello logistico con effetto della stagione, effetto di n (raggruppato: 1..18 singoli, 19-21, 22-24, 25-27) per partita con/senza DH, più il fattore in esame. Errori standard raggruppati per partita. Il risultato è un **rapporto di probabilità (odds ratio, OR) sull'arrivo in base**: OR sotto 1 = serie più lunghe. Per gli esperimenti naturali l'effetto della stagione è tolto (è il fattore stesso) e si tiene solo n × DH più gli indicatori di lega/periodo.
Il trattamento della partita di Galarraga (perfetta) e le esclusioni (partite dedotte, leghe afroamericane) sono quelli del resto del progetto.

## Verifiche (Parte 1)

- V1. Gruppo 2010-12: probabilità di una finestra di 3 stagioni con >= 6 (o >= 5 senza Galarraga) delle 21 perfette, scansionando tutte le finestre 1908-2025, con pesi per stagione dal modello nullo N2; poi con pesi dalla quota osservata di serie lunghe. E: nel 2010-12 tutta la curva (profondità 9, 12, 15, 18) è sopra il modello nullo N2? Test: rapporto S/S0 con intervallo di Greenwood, 2010-12 contro il resto e contro le altre finestre di 3 anni.
- V2. Le serie lunghe finiscono con meno basi su ball: regressione logistica sulle rotture (variabile: base su ball sì/no), con "rottura al battitore 19-27" contro "1-18", controllando slot, pinch hitter/lanciatore, DH, stagione e la tendenza a regalare basi del lanciatore (le sue altre partite).
- V3. Stadi: per ogni stadio OR sull'arrivo in base (base: stagione + n x DH), stagioni pari e stagioni dispari separate. Coors, Fenway, Arlington, Polo Grounds, più tutti gli altri stadi per vedere quanti si ripetono.

## Ipotesi della tortura (Parte 2)

Ognuna è un coefficiente sul modello di base, salvo dove scritto. "Pari" = scoperta, "dispari" = conferma.

- T01. Forza dell'attacco: tasso di arrivo in base della squadra al bat nella stagione (senza la partita in esame), meno la media della lega, in unità di deviazione standard. Atteso OR > 1.
- T02. Forza del lanciatore, stagione: tasso di arrivo in base concesso dal lanciatore in campo in quella stagione (senza la partita in esame, ridotto verso la media con 100 turni di peso), in deviazione standard. Atteso OR > 1.
- T03. Forza del lanciatore, carriera fino a quel giorno: scarto tra arrivi concessi e attesi in tutti i turni PRIMA della data della partita, ridotto con 300 turni di peso, in deviazione standard. Atteso OR > 1.
- T04. Mano: battitore con la stessa mano del lanciatore (destro contro destro, mancino contro mancino; bilaterale = mano opposta; mano ignota esclusa) contro mano opposta. Atteso OR < 1.
- T05. Formazione: quota di battitori della formazione iniziale avversaria (esclusi lanciatori) con la stessa mano del lanciatore partente, in deviazione standard. Atteso OR < 1.
- T06. Monte abbassato nel 1969: partite senza DH; scoperta prima = 1964, 1966, 1968, dopo = 1970, 1972, 1974; conferma prima = 1963, 1965, 1967, dopo = 1969, 1971, 1973. Fattore: dopo. Atteso OR > 1.
- T07. DH nella Lega Americana dal 1973 (differenza nelle differenze con la Nazionale): scoperta prima = 1968, 1970, 1972, dopo = 1974, 1976, 1978; conferma prima = 1967, 1969, 1971, dopo = 1973, 1975, 1977. Fattore: AL x dopo. Atteso OR > 1.
- T08. DH universale dal 2022 (differenza nelle differenze, NL contro AL): scoperta prima = 2016, 2018, dopo = 2022, 2024; conferma prima = 2017, 2019, 2021, dopo = 2023, 2025 (2020 escluso, DH ovunque). Fattore: NL x dopo. Atteso OR > 1.
- T09. Orologio dei lanci e divieto dello shift dal 2023, tutta la MLB, con il DH nel modello: scoperta prima = 2016, 2018, 2022, dopo = 2024; conferma prima = 2017, 2019, 2021, dopo = 2023, 2025. Fattore: dopo. Segno non dichiarato.
- T10. Squadre di espansione nel primo anno (LAA e WS2 1961; NYN e HOU 1962; KCA, SE1, MON, SDN 1969; SEA e TOR 1977; COL e FLO 1993; ARI e TBA 1998): fattore = la squadra al lancio è in espansione al primo anno; con stagione nel modello. Scoperta: espansioni del 1962 e 1998; conferma: 1961, 1969, 1977, 1993. Atteso OR > 1.
- T11. Integrazione: la Nazionale (più veloce) contro l'Americana, 1950-59 contro 1938-46; differenza nelle differenze; stagioni pari/dispari dentro le stesse finestre. Segno atteso OR > 1.
- T12. Seconda partita di un doppio incontro (campo `number` = 2) contro tutte le altre. Segno non dichiarato.
- T13. Partita diurna dopo una notturna (squadra al bat: partita precedente di notte il giorno prima): fattore, con indicatore giorno/notte nel modello. Segno non dichiarato (stanchezza: OR < 1 per l'attacco).
- T14. Partita del giorno prima finita ai supplementari (squadra al bat). Segno atteso OR < 1.
- T15. Settembre e ottobre contro aprile-agosto. Segno non dichiarato.
- T16. Vantaggio: la squadra al lancio è avanti di 4 o più punti contro 0-3, solo per battitori n >= 10. Segno non dichiarato.
- T17. Squadra al lancio in casa contro in trasferta. Segno non dichiarato.
- T18. Prima volta in stagione che il lanciatore partente affronta quella squadra, contro le volte successive; solo turni contro il partente. Atteso OR < 1.
- T19. Primo lancio strike (dal 1988, con lanci validi): quota di primi lanci strike per battitori n >= 10 contro n <= 9, con stagione e DH. Atteso: più strike nel profondo.
- T20. Tra le rotture dal 1988: quota di quelle decise al primo lancio (turno di 1 lancio) per battitori n >= 10 contro n <= 9. Segno non dichiarato.
- T21. Leadoff: tendenza per decennio del vantaggio del primo battitore (n = 1) sugli n = 2..8 nel tasso di arrivo in base; fattore: n=1 x (stagione - 1960)/10, con effetti di stagione e n. Segno atteso: premio in crescita (OR > 1).
- T22. "Sfilacciamento": dopo la prima rottura, quota di arrivi nei tre turni successivi, per rotture al battitore >= 19 contro <= 9. Atteso OR < 1 (i profondi non crollano).
- T23. Difesa: quota degli errori tra le rotture, tendenza per decennio. Atteso: in calo (OR < 1).
- T24. Ricevitore: gli effetti dei ricevitori (>= 300 turni in ogni insieme) stimati sulle stagioni pari si ripetono in quelle dispari (correlazione di rango positiva, p < 0,05)? Scoperta: eterogeneità dei ricevitori nelle pari (chi quadrato); conferma: correlazione pari/dispari.
- T25. Temperatura (partite con temperatura nota, Fahrenheit): OR per +10 gradi. Segno non dichiarato.

Totale: 25 ipotesi di tortura + 3 verifiche. Eventuali modifiche scritte dopo aver visto le stagioni pari sono nella sezione finale.

## Modifiche scritte dopo aver visto le stagioni pari (e prima di guardare le dispari)

Nelle pari le 25 ipotesi sono state provate tali e quali. Quattro avevano un difetto di impostazione, non un risultato scomodo da cambiare: le versioni originali restano nella tabella e si provano anche nelle dispari; le varianti sono quattro test in più (totale 29 test, tutti contati nella correzione di Holm).

- T07r (variante di T07). Il DH cambia solo il turno del lanciatore (1 battitore su 9), e la differenza nelle differenze su tutti i turni lo dilui nel rumore (nelle pari: OR 0,935, segno opposto all'atteso, p = 0,038). Variante: stessa impostazione ma solo sui turni al posto del lanciatore (battitori 9, 18, 27).
- T08r (variante di T08). Stessa ragione; solo battitori 9, 18, 27.
- T18r (variante di T18). Nelle pari "prima volta" dava OR 1,04, segno opposto all'atteso: confusione evidente, perché i lanciatori che affrontano una squadra una volta sola sono mediamente peggiori. Variante: solo partenti che affrontano quella squadra almeno 2 volte nella stagione, con la qualità del lanciatore (T02) nel modello.
- T20r (variante di T20). Le basi su ball richiedono almeno 4 lanci, quindi meno basi su ball tra le rotture profonde (V2) alza meccanicamente la quota di rotture al primo lancio. Variante: escluse le basi su ball.

Nota sulla direzione: le "ipotesi con segno atteso" non cambiano nulla ai fini della regola: sopravvive solo ciò che ha p < 0,05 e lo stesso segno in tutte e due le metà.

## Dopo aver visto le dispari

Nessuna ipotesi è stata cambiata. Ho aggiunto solo controlli di robustezza sui sopravvissuti (`src/tortura_extra.py`: T17 con forza di attacco, lanciatore e stadio; T25 con stadio, giorno/notte e mese; T24 con squadra-stagione e lanciatore-stagione) e descrizioni (leadoff per epoca, lanci per profondità, no-hitter dopo la rottura). Non sono ipotesi nuove; il controllo su T24 è stato fatto dopo aver visto le dispari.
