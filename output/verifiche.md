# Verifiche: le tre chicche "da verificare"

Dati Retrosheet, stagione regolare 1908-2025, 402.184 squadre al lancio (partite dedotte e leghe afroamericane escluse, Galarraga contata come perfetta salvo dove scritto). Intervalli al 95%. Programma: `src/verifiche.py`. "OR" è il rapporto di probabilità (odds ratio) sull'arrivo in base di un battitore: sopra 1 i battitori arrivano in base più spesso, sotto 1 meno spesso.

## 1. Il grappolo 2010-12 (6 perfette su 21 in 3 anni)

**Verdetto: ancora incerta, ma la spiegazione "era favorevole ai lanciatori" è smentita.** Il grappolo è raro, non rarissimo, e dipende dalla scelta su Galarraga.

**Quanto è raro.** Il modello nullo N2 (ogni battitore arriva in base con la frequenza della sua stagione, dello slot, del giro) prevede 10,0 perfette in tutta la storia e solo 0,46 nel 2010-12 (4,5% del totale: il 2010-12 era già un'epoca di pochi punti segnati). Se avessimo scelto quei tre anni in anticipo, vedere 6 delle 21 lì dentro avrebbe probabilità 0,03%: ma li abbiamo scelti guardando i dati. Il calcolo giusto è la statistica di scansione, cioè la probabilità che *una qualsiasi* finestra di tre stagioni consecutive (116 finestre, 1908-2025) contenga 6 o più delle 21 (simulazione, 200.000 prove):

| Pesi per stagione | con Galarraga (6 su 21) | senza Galarraga (5 su 20) |
|---|---|---|
| modello nullo N2 (il riferimento) | 1,0% (Poisson 1,6%) | 5,5% (Poisson 7,2%) |
| solo numero di partite (storia piatta) | 0,24% | 1,9% |
| quota osservata di serie da 12, 15 o 18 battitori | 0,4-0,6% | 3,0-3,7% |
| finestra di lunghezza libera, da 1 a 5 stagioni | 0,7% | 3,8% |

Con Galarraga il caso lo spiega raramente (circa 1 volta su 100); senza, circa 1 volta su 20: la stessa conclusione "dipende da Galarraga" della scheda precedente, ma con numeri più stabili.

**Era favorevole?** No. Se il 2010-12 fosse stato un'epoca dove i lanciatori reggono di più su tutta la curva, la quota di squadre che arrivano a 9, 12, 15, 18 battitori dovrebbe essere sopra il modello nullo più del solito. È il contrario (rapporto reale/nullo della quota ancora perfetta):

| Battitori | 2010-12 | tutto il resto | 2013-25 |
|---|---|---|---|
| 9 | 1,01 [0,93-1,10] | 1,07 [1,05-1,09] | 1,06 [1,02-1,11] |
| 12 | 1,05 [0,90-1,24] | 1,13 [1,09-1,17] | 1,14 [1,06-1,22] |
| 15 | 1,13 [0,85-1,51] | 1,26 [1,19-1,34] | 1,25 [1,10-1,41] |
| 18 | 1,26 [0,79-2,00] | 1,43 [1,31-1,56] | 1,27 [1,03-1,56] |

Le rotture reali sono il 99,2% di quelle attese nei battitori 1-17 (nel resto della storia 99,4%): tra tutte le 116 finestre di tre stagioni il 2010-12 sta al 42esimo posto dal basso, cioè a metà. Le quote grezze sono più alte che nel 2000-09 (serie da 15+ battitori: 3,2 per mille di squadre contro 2,7) ma più basse che nel 2013-25 (4,2): seguono semplicemente la discesa dei punti segnati, che il modello nullo già conta. Quindi niente effetto di epoca: o è fortuna, o è un addensamento che compare solo in cima alla curva (27 battitori), e con questi dati le due cose non si separano.

## 2. Nelle serie lunghe le rotture sono meno spesso basi su ball

**Verdetto: confermata, e non è un effetto del battitore (slot, pinch hitter) né del lanciatore (quanti ne regala di solito).**

Quota di basi su ball tra le rotture: **25,7%** quando la perfezione cade ai battitori 1-9 (402.159 rotture in tutto), **21,0%** ai battitori 10-18, **17,0%** ai battitori 19-27 (79 su 465). Rapporto di probabilità di una base su ball, rispetto a 1-9:

| Modello | 10-18 | 19-27 |
|---|---|---|
| grezzo | 0,77 [0,74-0,80] | 0,59 [0,47-0,76] |
| + slot del battitore, ruolo (pinch hitter / lanciatore), DH | 0,77 [0,74-0,80] | 0,59 [0,46-0,75] |
| + stagione | 0,78 [0,74-0,81] | 0,59 [0,46-0,75] |
| + tendenza del lanciatore a regalare basi (dalle sue altre partite) | 0,80 [0,76-0,84] | 0,63 [0,49-0,80] |

- **Battitori in fondo alla formazione o pinch hitter?** No. Tra le rotture tardive i pinch hitter sono il 2,6% e i lanciatori lo 0,2%; i pinch hitter prendono la base su ball nel 23,7% dei casi, come gli altri (25,5%). Tenendo solo i battitori normali il risultato è lo stesso (0,62 [0,49-0,80]).
- **Lanciatori più forti?** Solo in minima parte. La tendenza del lanciatore a regalare basi (dalle sue altre partite, ridotta verso la media) prevede il 21,5% di basi su ball nelle rotture tardive contro il 22,4% in generale: spiega circa un punto degli 8,5 punti di differenza, e porta il rapporto da 0,59 a 0,63.
- **Lanciatori stanchi?** Se fosse stanchezza le basi su ball dovrebbero aumentare, non calare.
- **Stesso segno in ogni epoca**: 1908-45 0,38 [0,21-0,70]; 1946-92 0,77 [0,54-1,08]; dal 1993 0,62 [0,41-0,94].
- **Scoperta contro conferma**: stagioni pari 0,53 [0,37-0,76] (241 rotture tardive); stagioni dispari 0,73 [0,52-1,01] (224), p = 0,055: stesso segno, ma da sola la metà dispari manca di poco la soglia. Il tratto 10-18 invece è solidissimo in tutte e due le metà (0,77 e 0,83), e la discesa è graduale (25,7 poi 21,0 poi 17,0%), il che rende credibile il 19-27.
- **Che cosa resta?** Un effetto "della giornata": chi è arrivato così avanti è quasi sempre un lanciatore con il controllo del giorno, e quando la perfezione cade, cade più spesso per un colpo vero o per un errore. Con questi dati non si può dire di più.

## 3. Gli stadi

**Verdetto: confermata.** Per ogni stadio ho stimato il rapporto di probabilità di arrivare in base (stesso confronto con stagione e posto in formazione) separatamente nelle stagioni pari e dispari. File: `output/verifiche_stadi.csv`.

| Stadio | stagioni pari | stagioni dispari |
|---|---|---|
| Coors Field | 1,18 [1,12-1,25] | 1,21 [1,15-1,27] |
| Fenway Park | 1,08 [1,05-1,11] | 1,08 [1,05-1,11] |
| Arlington (The Ballpark) | 1,06 [1,00-1,12], p = 0,045 | 1,13 [1,08-1,20] |
| Polo Grounds | 0,93 [0,89-0,96] | 0,94 [0,90-0,97] |
| Dodger Stadium | 0,95 [0,92-0,98] | 0,95 [0,92-0,98] |

Sopra 1 = parco che aiuta i battitori (serie perfette più corte), sotto 1 = parco che aiuta il lanciatore. Tutti e quattro quelli citati dal sito (e Dodger Stadium) hanno stesso segno e p < 0,05 in tutte e due le metà; Arlington è il più debole nelle pari (p appena sotto 0,05). Quello che i dati non possono dire è se la causa sia il campo o la squadra di casa (le squadre di casa pesano la metà dei turni).

La verifica sistematica, più importante dei singoli stadi (91 stadi con abbastanza dati in entrambe le metà):
- Gli stadi differiscono davvero tra loro: chi quadrato 280 su 91 gradi nelle pari (p = 4e-21) e 315 nelle dispari.
- Stadi con p < 0,05 nelle pari: 18; di questi 9 si ripetono nelle dispari con stesso segno e p < 0,05 (per caso se ne aspetterebbe meno di uno). Correlazione tra le stime pari e dispari: 0,45 (p = 6e-6).
- Con la soglia di Bonferroni sulle sole pari (p < 0,00055): 6 stadi, di cui 4 si ripetono (Coors, Fenway, Polo Grounds, League Park di Cleveland); non si ripetono Shea Stadium (OR 0,93 poi 0,96, p = 0,07) e Oakland Coliseum (0,93 poi 0,97, p = 0,13).
- Gli altri stadi che si ripetono: Candlestick Park (0,95 e 0,95), Tiger Stadium (1,04 e 1,04), South End Grounds di Boston (1,11 e 1,16).

Nota: i nomi dei quattro stadi vennero scelti guardando tutte le stagioni, quindi per loro la "conferma" nelle dispari non è indipendente; la parte indipendente è la verifica sistematica qui sopra, fatta con la regola pari/dispari.
