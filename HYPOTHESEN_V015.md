# Vaste cartridges v0.15 — 17 oktober 2026

Vastgelegd vóór de eerste historische uitvoering. Eigen hypotheses, geen claim van bewezen winstgevendheid. Geen parameterselectie of aanpassing na de eerste meting. Dezelfde topselectie, drie kalenderjaren gesloten uurcandles, kosten en risicolimieten. Historie is al bekeken; resultaten zijn geen ongezien bewijs.

## Behouden en uitbreiden

De v1.0.0-regels en ID's `momentum63` en `donchian55` blijven ongewijzigd voor bestaande resultaten en een automatische afzonderlijke LONG-referentie. Het hoofdscherm toont hun LONG + SHORT-uitbreidingen (v1.1.0). Beide accounts starten met hetzelfde kapitaal en gebruiken dezelfde candles, ook bij kostenstress en drie controleperioden. Bijdragen van LONG/SHORT binnen één account zijn geen afzonderlijke accounts; de LONG-referentie is dat wel.

- **Momentum 63:** ongewijzigde wekelijkse positieve LONG-keuze; SHORT bij negatief momentum en shortexit bij momentum >= 0, op maandag 00:00 UTC. Nul is cash. Stops/targets, warm-up en kalenderregels zoals v1.0.0.
- **Kanaal 55/20:** ongewijzigde LONG-regels; SHORT als de gesloten dag-close onder de laagste low van de vorige 55 dagen ligt; shortexit boven de hoogste high van de vorige 20 dagen. De beslisdag is uitgesloten. Bestaande 24-uurswachttijd en warm-up behouden.

## Vier vervangers

De oorspronkelijke EMA, RSI, breakout en pullback verdwijnen uit de primaire keuze, maar hun broncode en opgeslagen resultaten blijven voor het archief bestaan. Er zijn precies zes primaire cartridges.

Alle vier nieuwe hypotheses beslissen uitsluitend om 00:00 UTC op voltooide UTC-dagen, opgebouwd uit 24 gesloten uurcandles. Uitvoering gebeurt op de volgende uur-open. Onvoltooide eerste/laatste dagen tellen niet als volledige indicator-dagen. Intraday beschermende stops en targets werken op uurcandles. Eén LONG of SHORT tegelijk, geen hefboom; 100% shortonderpand. Geen dagelijkse automatische portefeuilleselectie.

1. **Supertrend 10 × 3:** dagelijkse Wilder-ATR(10), midden van dag-high/low ± 3 ATR. Definitieve bovenband wordt verlaagd naar de basisband als die lager is of vorige close boven de vorige bovenband lag; anders blijft de vorige band. Onderband spiegelbeeldig. Beginrichting LONG op de eerste geldige band. Richting draait SHORT bij close onder de definitieve onderband van de vorige richting, en LONG bij close boven de definitieve bovenband. Dagelijks instappen volgens toestand en sluiten bij tegengestelde toestand. Warm-up 30 volledige dagen. Stop 3× dag-ATR14, target 8×.
2. **Bollinger-herstel 20 × 2:** gemiddelde en populatiestandaardafwijking van de laatste 20 gesloten dag-closes. LONG als vorige close onder vorige onderband lag en huidige close weer boven huidige onderband komt; SHORT spiegelbeeldig vanaf bovenband. LONG sluiten bij close >= gemiddelde, SHORT bij <= gemiddelde. Warm-up 21 volledige dagen. Stop 2× dag-ATR14, target 4×.
3. **Keltner-uitbraak 20 × 2:** dagelijkse EMA20, kanaal ± 2× dag-ATR14. LONG op kruising close van <= vorige bovenband naar > huidige bovenband; SHORT spiegelbeeldig onder onderband. LONG sluiten bij close < EMA20, SHORT bij > EMA20. Warm-up 21 volledige dagen. Stop 3× dag-ATR14, target 8×.
4. **Mislukte uitbraak 20 + trend100:** LONG als dag-low onder de laagste low van de vorige 20 dagen komt maar close erboven eindigt, én close > EMA100; SHORT spiegelbeeldig bij high boven vorig highkanaal, close eronder en close < EMA100. Dag zelf uitgesloten van kanaal. LONG sluiten als close >= middelpunt van vorig 20-daags high/lowkanaal of < EMA100; SHORT spiegelbeeldig. Instap alleen als de strategie-exit op diezelfde beslisdag nog niet geldt. Warm-up 100 volledige dagen. Stop 2× dag-ATR14, target 4×.

Alle vier slaan na elke exit 24 volledige uurcandles over. Geen maximale positieduur; stop/target blijven op hun instapniveau. Geen trailing stop of intrabar daginformatie. De vier verschillen ook in hun signaalregels en deels in stopafstand; het is geen geïsoleerde test van één variabele.

## Kosten en vaste beoordeling

10.000 USDT per coin/account, fee 0,10% per zijde, slippage 0,05% per fill, shortleenproxy 0,02% per dag. Dubbele kosten verdubbelt alle drie; kan positieomvang en handelspad wijzigen. Gepland risico 0,25% per trade, maximaal 25% instapblootstelling, dagelijkse entry-stop 1%, permanente drawdown-entry-stop 10%. Geen wijziging van deze limieten of de minimumaantallen om een winnaar af te dwingen.

Dezelfde drie afzonderlijke controleperioden, elk met nieuw kapitaal en lege positie. Volledig positief, positief bij kostenstress, minstens 30 normale trades, drie perioden normaal én stress positief met elk minstens 5 trades, en geen permanente stop in de volledige normale of stresstest. Zeven van tien geselecteerde coins moeten voldoen voor een kandidaatlabel. Ook dan geen bewezen winstgevendheid of liveactivatie.

Spotprijzen zijn geen derivatenprijzen. Vaste leenproxy is geen echte funding of margin-liquidatie; historische beschikbaarheid van shorts is niet aangetoond. De huidige topselectie op oude markten introduceert selectie-/overlevingsbias; coins zijn onderling gecorreleerd. HYPE met te korte historie blijft een fout zonder vervanging.
