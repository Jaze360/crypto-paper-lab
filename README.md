# Crypto Paper Lab — v0.2

Nederlandstalig lokaal onderzoeksdashboard. **Uitsluitend paper trading**: geen echte orders, exchange-accountkoppeling, shorts of hefboom.

## Nieuw in v0.2

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
| Eigen CSV | Dezelfde coinselector; maximaal 50.000 rijen / 8 MB | Vaste intervallen, echte door jou aangeleverde OHLCV. USD-prijzen en bronkwaliteit moet je zelf controleren |

Kraken levert ongeveer maximaal 30 dagen op 1 uur, 120 dagen op 4 uur of 719 dagen op 1 dag; de periodekeuze in deze versie gaat tot 365 dagen. De grafiek toont steeds de **feitelijk ontvangen** periode. Nieuwe of ontbrekende markten kunnen minder data opleveren of een duidelijke fout geven. Geen stilzwijgende terugval op demodata.

CSV-kolommen: `time,open,high,low,close,volume`. Tijd is candle-start in UTC (ISO-8601); candles moeten zonder gaten aansluiten. Ontbrekende tijdzone wordt als UTC behandeld. De laatste candle wordt alleen meegenomen als het volledige interval voorbij is. Geen fictief volume toevoegen om de volumestrategie te kunnen gebruiken.

Officiële broninformatie:
- CoinGecko: https://docs.coingecko.com/reference/coins-id-ohlc
- Kraken: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
- GitHub CLI: https://cli.github.com/manual/gh_auth_login

## Strategietests lezen

De vaste strategieën blijven **EMA 8/21**, **RSI(14) herstel** en **20-bar breakout + volume**. Meer strategieën of parameters leveren op zichzelf geen beter handelsresultaat op.

- **70/30-split**: eerste deel ontwikkeling, laatste deel test; kapitaal en posities worden tussen segmenten gereset.
- **Drie tijdvensters**: vaste regels getest op achtereenvolgens 40–60%, 60–80% en 80–100% van de dataset, met eerdere candles uitsluitend als indicator-warmup. Geen parameteroptimalisatie of volledige walk-forward-optimalisatie.
- Deze vensters overlappen elkaar niet, maar overlappen wel deels met de 30%-test. Ze zijn geen onafhankelijke bevestigingen.
- **Dubbele kosten**: fees en slippage verdubbeld, tot de bestaande modelgrenzen van 1% fee en 2% slippage per zijde.
- **Kopen-en-vasthouden**: hetzelfde 30%-testsegment, met kosten aan beide zijden; zowel 100% als 25% initiële blootstelling. Het risicoprofiel is anders dan dat van de strategieën.
- Bij minder dan 30 trades staat expliciet dat er te weinig bewijs is. Meerdere strategieën of coins vergelijken verhoogt het risico op toevallige winnaars.

Long-only, één positie. Maximaal 0,25% gepland risico per trade en 25% blootstelling; blokkade op nieuwe entries na 1% dagverlies of 10% drawdown. Gaps kunnen meer verlies veroorzaken dan gepland. Daglimieten worden op candle-open getoetst; er is geen professionele realtime risicobewaking. Bij stop en target in dezelfde candle geldt conservatief stop-first.

Historische candle-replay is geen autonome forward paper engine. Posities, rendementen, kosten en uitvoering blijven simulaties. Er is geen AI-API of live orderfunctie aangesloten.

## Testen

```powershell
.\\.venv-313\\Scripts\\python.exe -m pytest -q
```

Tests gebruiken eigen tijdelijke opslag en fictieve sleutels. Ze controleren onder meer exact hervatten van replays, opslag, CSV-validatie, verwijderen van onvoltooide candles, publieke data-cache, benchmarkkosten, updatecontrole, back-up, herstel bij onderbreking en Windows-versleuteling.

**Geen bewijs van winstgevendheid of financieel advies.** De app helpt strategieën eerlijker onderzoeken, niet resultaten winstgevend laten lijken.

