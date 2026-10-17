# Crypto Paper Lab — v0.6

Nederlandstalig lokaal onderzoeksdashboard. **Uitsluitend paper trading**: geen echte orders of exchange-accountkoppeling. Longs en shorts zijn alleen fictieve posities.

## Nieuw in v0.6: een rustigere werkplek

Eén startknop met keuze van onderzoekstype. Kosten, strategieparameters, CSV-import, opgeslagen onderzoeken en onderhoud zijn uitklapbaar. Resultaten staan bovenaan; methodetoelichtingen en long-/shortdetails open je wanneer nodig. Nieuwe paarse accenten, helderdere typografie en een indeling die meebeweegt op kleinere schermen. Bestaande instellingen, opslag, tests en paper-only-regels blijven behouden.

## Nieuw in v0.5: long-/shortuitsplitsing

Per onderzoeksperiode toont het dashboard gesloten trades afzonderlijk voor LONG en SHORT: bruto resultaat vóór kosten, slippage, handelskosten, shortleenkosten, netto P&L, bijdrage aan het volledige startkapitaal en winrate. Een tweede tabel groepeert de werkelijke exitredenen per richting. Beide tabellen zijn samen als CSV te exporteren.

Kies de periode boven de tabel: backtest, replay, strategievergelijking, walk-forwardvenster of laatste test, inclusief beschikbare kostenstressvarianten. Open posities vallen buiten deze uitsplitsing. Slippage zit al in uitvoeringsprijzen en wordt niet opnieuw afgetrokken. De handelsregels en parameterselectie veranderen niet.

Oude backtests/replays met een journal krijgen de beschikbare uitsplitsing bij openen; onbekende historische slippage blijft leeg. Voor oude vergelijkingen/walk-forwardrapporten zonder tradejournal voer je het onderzoek opnieuw uit. Bestaande resultaten worden niet overschreven.

## Nieuw in v0.4: paper-shorts

Kies **Handelsrichting**: alleen LONG, alleen SHORT of LONG + SHORT. Er blijft maximaal één fictieve positie tegelijk open. De richting wordt bij instellingen en resultaten bewaard en blijft tijdens parameterselectie vast.

### Shortregels

- EMA: neerwaartse kruising voor shortinstap; uitstap zodra de snelle EMA boven de trage staat.
- RSI: gespiegeld ten opzichte van de longdrempels. Standaard een neerwaartse kruising van 70 voor instap en RSI ≤45 voor uitstap (longinstellingen 30/55).
- Breakout: neerwaartse uitbraak onder de voorafgaande lows, met voldoende echt candlevolume. CoinGecko zonder volume blijft hiervoor geblokkeerd.
- Shortstop boven de instap; target eronder. Een target op of onder nul wordt geweigerd.
- Signalering gebruikt uitsluitend gesloten eerdere candles. Bij een tegengesteld signaal kan de positie op de volgende open worden gesloten en omgedraaid, met kosten voor beide transacties. Nooit een instap op een eerdere open na een latere intrabar uitstap.

### Onderpand, kosten en grenzen

Het model reserveert **100% van de instapnotional** uit vrije cash als shortonderpand. De opbrengst van de shortverkoop is niet beschikbaar als nieuw handelskapitaal. Short-equity is vrije cash + onderpand + ongerealiseerde winst/verlies. Bij sluiting komen onderpand en netto koerswinst/verlies vrij, minus uitstapkosten. De bestaande blootstellingslimiet van 25% geldt bij instap.

**Short-leenkosten (% per dag)** is een door jou ingestelde simulatieparameter (standaard 0,02%), geen actueel markttarief. Per candle met een shortpositie wordt instapnotional × dagtarief × kalenderduur afgetrokken. Ook bij een intrabar stop/target wordt conservatief de hele candle gerekend. Een gapuitstap op de open rekent geen nieuwe candlekosten. Kostenstress verdubbelt naast fee/slippage ook het leentarief, tot de modelgrens van 1% per dag.

De positiegrootte reserveert maximaal 0,25% gepland risico inclusief instap-/stopuitvoeringskosten en één candle leenkosten. Langere looptijd en koersgaps kunnen dit geplande risico overschrijden. Grote shortgaps mogen in de simulatie negatief accountvermogen tonen; dit wordt niet kunstmatig op nul afgekapt en blokkeert verdere entries.

Er is **geen echte margin-, funding-, borrowbeschikbaarheids- of liquidatie-engine**. Geen hefboominstelling, brokeraccount of live orderroute. Het vaste onderpandmodel voorspelt dus niet hoe een echte beurs een positie zou behandelen. De benchmark blijft long kopen-en-vasthouden, ook bij shortonderzoek.

Het journal en CSV bevatten richting, leenkosten en aangehouden candles. Vergelijkingen tonen aantallen long- en shorttrades; de blootstelling is de absolute positiewaarde ten opzichte van accountvermogen.

### Bestaande resultaten en replays

Oude backtests en rapporten blijven leesbaar. Replays uit het oudere long-only-model openen als bewaard resultaat, maar worden niet stilzwijgend met de nieuwe boekhouding herberekend. Start daarvoor een nieuwe replay. Nieuwe long/short-replays kunnen wel exact worden hervat.

## Functies uit v0.3

- Meerjarige publieke OHLCV-historie (Binance data-only), tot 5 jaar op 1 uur / 4 uur / 1 dag. Prijzen in **USDT**; Kraken, CoinGecko en CSV blijven in USD.
- EMA-, RSI-, breakout-, volume- en ATR-stop/targetparameters instelbaar. De bestaande risicolimieten blijven vast.
- Tijd in markt, gemiddelde en maximale kapitaalblootstelling en gemiddelde positieduur.
- **Walk-forward + laatste 20% testen**: maximaal vier vooraf gedefinieerde parameterkandidaten per strategie; selectie op eerdere data, drie volgende testvensters, daarna een laatste test buiten alle selecties.
- Dezelfde test op maximaal vier coins. Mislukte markten blijven zichtbaar; dit vormt geen portfolio en geen winnaarselectie.
- Lange downloads en onderzoeken lopen op de achtergrond, met voortgang. Afgeronde resultaten worden bewaard; een onafgeronde taak stopt bij serverherstart.
- Snellere candle-uitvoering voor grote datasets; dashboardbestanden worden opnieuw geladen om oude browserinhoud te voorkomen.

### Nieuwe onderzoeken gebruiken

1. Installeer via **Controleren op updates > Update klaarzetten**, sluit de server en start **START_WINDOWS.bat** opnieuw.
2. Kies **Meerjarige OHLCV — publiek, USDT**, bijvoorbeeld **3 jaar** en **4 uur**.
3. Kies je strategie. Optioneel: open **Strategieparameters**. De handmatig gekozen parameters gelden voor een gewone backtest en vaste vergelijking, en vormen de basis voor walk-forward.
4. Klik **Walk-forward + laatste 20% testen**. De voortgang staat in de statusbalk; laat de server draaien.
5. Onder **Vergelijk meerdere coins** kun je maximaal vier coins selecteren en dezelfde walk-forward-procedure uitvoeren.
6. Open resultaten later via **Opgeslagen onderzoeken**.

De historische bron vereist geen sleutel of beursaccount. Een regio-, markt- of netwerkbeperking wordt als fout getoond; gebruik dan een eigen CSV. Er is geen wisselkoersconversie tussen USD en USDT. De grafiek toont de feitelijke dataperiode; die kan korter zijn dan gevraagd door de noteringsdatum. Per aanvraag maximaal 50 pagina's van 1.000 candles; de download wordt een uur lokaal gecachet.

### Hoe de parameterkeuze werkt

De eerste 40% vormt de eerste ontwikkelperiode. Daarna volgen drie aaneengesloten testvensters tot 80%. Voor elk venster worden parameters opnieuw geselecteerd op uitsluitend de eerdere candles. De laatste 20% wordt niet gebruikt in deze selecties. De parameters voor die laatste test worden vastgezet op basis van de eerste 80%.

De vooraf vastgelegde score is netto rendement minus maximale drawdown, met minimaal vijf trainingstrades. Zonder geldige kandidaat blijven de basisparameters behouden. Dit is een beperkte, uitlegbare selectie; geen uitputtende optimalisatie en geen bewijs voor een handelsvoordeel. De gekozen parameters staan bij ieder venster.

Vensters beginnen elk met nieuw fictief kapitaal en een lege positie. Indicatoren gebruiken eerdere candles als warmup. Rendementen uit de vensters vormen geen doorlopende samengestelde rekening. Door dezelfde laatste periode herhaald te bekijken, wordt die voor jou niet meer ongezien.

Marktperiodes worden **achteraf** beschreven als stijgend (>5% prijsstijging), dalend (<-5%) of zijwaarts. Die indeling stuurt de handel niet. De laatste test toont ook dubbele kosten en benchmarks met 25% en 100% blootstelling.

**Tijd in markt** telt candles met een positie na beslissingen op candle-open; een stop binnen die candle telt als actieve candle. Dit is geen exacte intrabar verblijfsduur. **Gemiddelde blootstelling** is positiewaarde gedeeld door accountvermogen op candle-open, gemiddeld over alle candles inclusief lege posities. Lage blootstelling kan lage rendementen en lage drawdown verklaren. Een koersstijging kan de gemeten blootstelling boven de oorspronkelijke instaplimiet laten uitkomen.

### Bestaande functies uit v0.2

- Instellingen, CSV-datasets, backtests, vergelijkingen en replays worden lokaal bewaard in SQLite.
- Een replay hervatten na herstart gebruikt dezelfde opgeslagen candles en voortgang.
- CoinGecko-sleutel optioneel lokaal opslaan met Windows DPAPI; de sleutel verschijnt nooit in status- of resultatenresponses.
- GitHub-updater voor publieke en private repositories: controleren, klaarzetten, afsluiten en bij volgende start installeren. Eerst een back-up van de vervangen bronbestanden.
- 12 USD-markten; publieke Kraken OHLCV zonder API-sleutel naast CoinGecko.
- Historische perioden van 7 tot 365 dagen; instelbaar Kraken-interval van 1 uur, 4 uur of 1 dag.
- Eigen OHLCV-CSV importeren voor langere datasets.
- Alle drie vaste strategieën vergelijken: 70/30-split, drie chronologische testvensters, dubbele kosten/slippage en kopen-en-vasthouden.
- Correctie van candle-uitvoering: na een intrabar stop wordt nooit achteraf op de eerdere candle-open opnieuw ingestapt.

## Starten op Windows

Gebruik **standaard Python 3.13 x64**. De dependencyset ondersteunt Python 3.15 niet.

1. Installeer zo nodig Python 3.13: `py install 3.13` (Python Install Manager), of via https://www.python.org/downloads/windows/.
2. Pak alle bestanden uit en dubbelklik op **START_WINDOWS.bat**.
3. Laat het servervenster open. Het dashboard opent op http://127.0.0.1:8501.

Het startscript maakt indien nodig `.venv-313`, installeert ontbrekende pakketten met kant-en-klare wheels en stopt bij installatiefouten. Installeren/herstellen van dependencies vereist internet. Start steeds via het startscript om klaargezette updates toe te passen.

### Eenmalig overstappen vanuit v0.1

De oude versie heeft nog geen updater. Download eenmaal de nieuwe ZIP via **Code > Download ZIP** op de repository.

1. Exporteer gewenste v0.1-journals naar CSV: die oude resultaten staan alleen in het geheugen.
2. Sluit het draaiende servervenster.
3. Pak de ZIP uit. Kopieer de inhoud van `crypto-paper-lab-main` naar je bestaande programmamap en vervang bronbestanden. Behoud `.venv-313` en persoonlijke bestanden.
4. Start de nieuwe **START_WINDOWS.bat**.
5. Bewaar onderzoeksinstellingen met **Instellingen bewaren**. Nieuwe resultaten worden automatisch opgeslagen.

Een API-sleutel uit een oud PowerShell-venster is alleen beschikbaar als je vanuit diezelfde omgeving start. Je kunt hem in het nieuwe dashboard opnieuw invoeren en lokaal versleuteld bewaren. Je hoeft de sleutel nooit in GitHub of deze chat te zetten.

## Updates vanuit het dashboard

Je ChatGPT-GitHub-plugin is niet automatisch beschikbaar voor een los Windows-programma. Voor de huidige openbare repository haalt de updater rechtstreeks data op via de GitHub API, zonder login of token. Alleen bij een private repository of een bereikte publieke API-limiet gebruikt hij de officiële **GitHub CLI** en jouw bestaande GitHub-account, zonder token in de broncode.

Alleen indien private toegang nodig is, eenmalige inrichting:

```powershell
winget install --id GitHub.cli -e
```

Open daarna een nieuw venster en voer `gh auth login --hostname github.com --web --git-protocol https` uit. Kies het account met toegang tot **Jaze360/crypto-paper-lab**. Je kunt ook **UPDATE_SETUP_WINDOWS.bat** openen nadat GitHub CLI is geïnstalleerd. Authenticeer alleen op GitHub; voer geen token in het dashboard in.

Daarna:

1. Klik **Controleren op updates**.
2. Klik **Update klaarzetten**. De updater downloadt exact de gecontroleerde commit.
3. Sluit het servervenster en dubbelklik opnieuw op **START_WINDOWS.bat**.
4. De bronbestanden worden eerst geback-upt en daarna vervangen; instellingen en resultaten blijven buiten de programmamap.

Een nieuw gedownloade ZIP heeft nog geen geregistreerde commit. De eerste controle kan daarom dezelfde versie als update aanbieden. Na één toepassing kent de updater de geïnstalleerde commit.

De updater accepteert uitsluitend bronbestanden uit de vaste repository, controleert paden, bestandstypen, omvang en het paper-only-versiemanifest en bewaart de downloadchecksum. Hij weigert geheime bestanden, binaire programma's, symlinks en padtraversal. Updates zijn niet onafhankelijk ondertekend: ze vertrouwen op jouw GitHub-repository en toegang. Pas updates alleen toe met de app afgesloten.

Bij een schrijffout of onderbroken bestandstransactie wordt de vorige code hersteld. Een functionele fout of dependency-installatiefout na een geslaagde vervanging vraagt zo nodig handmatig terugzetten van de bronbestanden uit de back-upmap. Databasewijzigingen in v0.2 zijn alleen toevoegingen.

## Bewaarlocatie en sleutel

Standaard: **%LOCALAPPDATA%\\CryptoPaperLab**.

- `lab.sqlite3`: instellingen, resultaten, CSV-datasets en tijdelijke marktdata-cache.
- `coingecko.dpapi`: optioneel versleutelde CoinGecko-sleutel, gebonden aan je Windows-account.
- `backups/`: broncode van vóór updates.
- `pending-update.json` en `update.zip`: een klaargezette update.

Sluit de app voordat je deze map kopieert als eigen back-up. Een versleutelde sleutel is niet zomaar overdraagbaar naar een andere Windows-account. De opgeslagen sleutel heeft voorrang op een omgevingsvariabele. Zonder opgeslagen sleutel gebruikt de app `COINGECKO_API_KEY`; het plan komt uit `COINGECKO_PLAN` of de bewaarde instellingen.

Alleen de expliciete actie **Instellingen bewaren** bewaart je onderzoeksselecties. Backtests, vergelijkingen en replays bewaren hun resultaten automatisch. **Opgeslagen onderzoeken** opent eerdere resultaten of hervat een replay. Exports volgen het geopende resultaat; zonder selectie het nieuwste resultaat van dat type.

Geavanceerd/testen: `PAPER_LAB_DATA_DIR` wijzigt de bewaarlocatie. Gebruik één serverproces per bewaarlocatie. De app luistert standaard alleen lokaal en weigert schrijfacties afkomstig van andere websites.

## Gegevensbronnen en echte grenzen

| Bron | Coins / periode | Volume en grenzen |
|---|---|---|
| Demo | BTC, ETH, SOL; 360 synthetische 4-uurscandles | Verzonnen OHLCV, alleen om de werking te testen |
| CoinGecko | 12 geselecteerde coin-ID's; 7/14/30/90/180/365 dagen | OHLC zonder candlevolume; volume-breakout wordt geblokkeerd. Beschikbaarheid hangt van je abonnement af; langere periodes gebruiken grovere candles |
| Kraken publiek | BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, LINK, DOT, LTC, BCH, UNI, alle in USD | Echt candlevolume, maximaal 719 gesloten candles. De actuele onvoltooide candle wordt verwijderd |
| Meerjarige bron | Dezelfde 12 markten, 7 dagen tot 5 jaar; 1u/4u/1d | Binance data-only, USDT, gesloten candles; paginering tot 50.000 candles |\n| Eigen CSV | Dezelfde coinselector; maximaal 50.000 rijen / 8 MB | Vaste intervallen, echte door jou aangeleverde OHLCV. USD-prijzen en bronkwaliteit moet je zelf controleren |

Kraken levert ongeveer maximaal 30 dagen op 1 uur, 120 dagen op 4 uur of 719 dagen op 1 dag; de periodekeuze in deze versie gaat tot 365 dagen. De grafiek toont steeds de **feitelijk ontvangen** periode. Nieuwe of ontbrekende markten kunnen minder data opleveren of een duidelijke fout geven. Geen stilzwijgende terugval op demodata.

CSV-kolommen: `time,open,high,low,close,volume`. Tijd is candle-start in UTC (ISO-8601); candles moeten zonder gaten aansluiten. Ontbrekende tijdzone wordt als UTC behandeld. De laatste candle wordt alleen meegenomen als het volledige interval voorbij is. Geen fictief volume toevoegen om de volumestrategie te kunnen gebruiken.

Officiële broninformatie:\n- Binance publieke data-only endpoints: https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only\n- Binance historische candles: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints
- CoinGecko: https://docs.coingecko.com/reference/coins-id-ohlc
- Kraken: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
- GitHub CLI: https://cli.github.com/manual/gh_auth_login

## Vaste strategievergelijking lezen (apart van walk-forward)

De standaardstrategieën blijven **EMA 8/21**, **RSI(14) herstel** en **20-bar breakout + volume**. De parameters zijn nu instelbaar; meer parameters leveren op zichzelf geen beter handelsresultaat op.

- **70/30-split**: eerste deel ontwikkeling, laatste deel test; kapitaal en posities worden tussen segmenten gereset.
- **Drie tijdvensters**: vaste regels getest op achtereenvolgens 40–60%, 60–80% en 80–100% van de dataset, met eerdere candles uitsluitend als indicator-warmup. Geen parameteroptimalisatie of volledige walk-forward-optimalisatie.
- Deze vensters overlappen elkaar niet, maar overlappen wel deels met de 30%-test. Ze zijn geen onafhankelijke bevestigingen.
- **Dubbele kosten**: fees en slippage verdubbeld, tot de bestaande modelgrenzen van 1% fee en 2% slippage per zijde.
- **Kopen-en-vasthouden**: hetzelfde 30%-testsegment, met kosten aan beide zijden; zowel 100% als 25% initiële blootstelling. Het risicoprofiel is anders dan dat van de strategieën.
- Bij minder dan 30 trades staat expliciet dat er te weinig bewijs is. Meerdere strategieën of coins vergelijken verhoogt het risico op toevallige winnaars.

Eén positie tegelijk, met de gekozen long/short-richting. Maximaal 0,25% gepland risico per trade en 25% blootstelling; blokkade op nieuwe entries na 1% dagverlies of 10% drawdown. Gaps kunnen meer verlies veroorzaken dan gepland. Daglimieten worden op candle-open getoetst; er is geen professionele realtime risicobewaking. Bij stop en target in dezelfde candle geldt conservatief stop-first.

Historische candle-replay is geen autonome forward paper engine. Posities, rendementen, kosten en uitvoering blijven simulaties. Er is geen AI-API of live orderfunctie aangesloten.

## Testen

```powershell
.\\.venv-313\\Scripts\\python.exe -m pytest -q
```

Tests gebruiken eigen tijdelijke opslag en fictieve sleutels. Ze controleren onder meer exact hervatten van replays, opslag, CSV-validatie, verwijderen van onvoltooide candles, publieke data-cache, benchmarkkosten, updatecontrole, back-up, herstel bij onderbreking en Windows-versleuteling.

**Geen bewijs van winstgevendheid of financieel advies.** De app helpt strategieën eerlijker onderzoeken, niet resultaten winstgevend laten lijken.



