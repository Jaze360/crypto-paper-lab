# Vaste hypothesen en risicoscenario's v0.16 — 17 oktober 2026

Vóór de eerste marktmeting vastgelegd. Geen optimalisatie of regelwijziging op basis van deze resultaten. Supertrend en Keltner blijven ongewijzigd, evenals momentum en kanaaluitbraak. Bollinger en mislukte uitbraak verdwijnen uit de primaire keuze; broncode en opgeslagen uitkomsten blijven behouden.

## Gemeenschappelijke basis

Exact de tien coins en 2023-10-17 18:00 UTC tot 2026-10-17 18:00 UTC exclusief uit de bewaarde v0.15-test: 26.304 gesloten uurcandles per volledige coin. Hashes moeten overeenkomen. HYPE met onvolledige historie blijft een fout. Geen vervangcoin of kortere test.

Beide nieuwe cartridges gebruiken LONG + SHORT, één positie tegelijk. Dagindicatoren uitsluitend uit volledige gesloten UTC-dagen van 24 uurcandles; signalen om 00:00 UTC na sluiten van de beslisdag, uitvoering op de volgende uur-open. Deels aanwezige dagen zijn uitgesloten van dagindicatoren. Geen toekomstige data of intraday kennis van de uiteindelijke dag-close. Stops en targets blijven op uurcandles, met bestaande gap- en stop-firstregels.

Bij instap stop 3× dagelijkse Wilder-ATR14, target 8×, beide daarna vast. Na elke exit 24 volledige uurcandles overslaan. Geen maximale positieduur, geen extra EMA200-filter. Dezelfde fee 0,10% per zijde, slippage 0,05% per fill, shortleenproxy 0,02% per dag; dubbele kosten verdubbelt alle drie. Basisrisico 0,25% per trade, maximaal 25% instapblootstelling, dagelijkse entry-stop 1%, permanente drawdown-entry-stop 10%. Geen hefboom of echte orders.

## Aroon-trend 25

Het venster bevat de laatste 26 volledige dagen: de huidige beslisdag plus 25 eerdere dagen. Dagen sinds hoogste high / laagste low zijn 0..25. Gelijke uitersten kiezen de meest recente dag. Aroon-Up = 100×(25−dagen sinds high)/25, Down spiegelbeeldig. Dit legt de venster- en tieconventie expliciet vast.

- LONG bij Up >= 70 en Down <= 30; SHORT bij Down >= 70 en Up <= 30.
- LONG-exit bij Up < 50 of Down > 50; SHORT-exit bij Down < 50 of Up > 50.
- Dagelijkse toestandssignalen: na stop/target en wachttijd mag een nog geldige toestand opnieuw instappen. Warm-up 26 volledige dagen.

## KAMA adaptieve trend 10/2/30

Dagelijkse Efficiency Ratio ER = absolute koersverandering over 10 dagen / som van de 10 absolute dagveranderingen. Zonder beweging ER=0. Smoothing = [ER×(2/3−2/31)+2/31]². Eerste KAMA is het gemiddelde van de eerste tien volledige dag-closes; daarna KAMA(t)=KAMA(t−1)+smoothing(t)×[close(t)−KAMA(t−1)].

- LONG bij close die van <= vorige KAMA naar > huidige KAMA kruist, stijgende KAMA én ER >= 0,30.
- SHORT spiegelbeeldig: van >= naar < KAMA, dalende KAMA en ER >= 0,30.
- LONG-exit bij close < KAMA, SHORT-exit bij close > KAMA. Herinstap vereist een nieuwe kruising, ook na een stop/target.
- Warm-up 31 volledige dagen. Geen extra minimumafstand of achteraf gekozen parameters.

## Risicovergelijking

Naast het basisresultaat draait iedere primaire test automatisch twee afzonderlijke volledige driejaarsaccounts: 0,50% en 1,00% gepland risico per instap. De normale en dubbele kosten worden voor elk scenario opnieuw met de engine doorgerekend; rendementen worden niet simpelweg vermenigvuldigd. Het bestaande basisaccount van 0,25% wordt hergebruikt als eerste vergelijkingsrij.

Stopafstand, target, 25%-instaplimiet, volledig shortonderpand, dagelijkse 1%-entry-stop en permanente 10%-drawdownstop veranderen niet. Meer gepland risico betekent grotere posities voor zover de instaplimiet en beschikbare cash dat toelaten. Slippage en fees groeien mee, lenen wordt op de grotere shortpositie berekend. Het handelspad kan veranderen door risicostops, afronding en minimale ordergrootte. Gaps en langdurige leenkosten kunnen het geplande verlies overschrijden.

Vergelijking toont netto/stressrendement, drawdown, trades, gemiddelde blootstelling en permanente stop. De twee hogere scenario's hebben alleen volledige tests en kostenstress; geen nieuwe drieperiodenbeoordeling of extra winnaarselectie. De drie controleperioden en alle bestaande geschiktheidscriteria blijven uitsluitend voor het standaardrisico gelden. Geen automatische overname van een hoger risico, geen nieuwe instelknoppen, geen wijziging van de standaard van 0,25%. De oorspronkelijke LONG-referentie blijft ook op standaardrisico.

Eerste v0.16-vergelijking: beide nieuwe cartridges plus de ongewijzigde Supertrend en Keltner, op dezelfde bewaarde selectie en candles als v0.15. De andere twee blijven behouden en krijgen de risicovergelijking bij een volgende normale test.

## Onderbouwing en grenzen

[TradingView over Aroon](https://www.tradingview.com/support/solutions/43000501801-aroon-indicator/) beschrijft de tijd sinds uitersten. [StockCharts over KAMA](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/kaufmans-adaptive-moving-average-kama) beschrijft de adaptieve smoothing. De hier vastgelegde entries, exits, filters, stops en beoordeling zijn eigen onderzoekshypothesen; de bronnen bewijzen geen voordeel voor deze configuratie.

[CME over positiegrootte](https://www.cmegroup.com/education/courses/trade-and-risk-management/proper-position-size) koppelt de positie aan account-risico en stopafstand. Meer risico creëert geen beter signaal; het kan positieve en negatieve uitkomsten vergroten. Onze vergelijking is een simulatie, geen advies om een gekozen percentage met echt geld te gebruiken.

Huidige topselectie op oude data geeft selectie- en overlevingsbias. Herhaald bekeken markten en meerdere strategieën zijn geen ongezien bewijs. Coins zijn gecorreleerd. Spotprijzen met een vaste leenproxy modelleren geen echte funding, uitleenbaarheid of liquidatie. Accounts per coin zijn geen gecombineerde portefeuille.
