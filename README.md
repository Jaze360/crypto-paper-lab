# Crypto Paper Lab — v0.1

**Nederlandstalige, lokale crypto trading-onderzoeksomgeving. 100% paper trading.** Geen beurs-, wallet- of brokerkoppelingen, geen echte orders, geen shorts of hefboom.

## Functionaliteit

- Drie deterministische strategieën uit de principes van de tradingcursus: **EMA 8/21**, **RSI(14) mean reversion**, **20-bar breakout + volume**.
- Reproduceerbare **synthetische demonstratiedata** om de code en de interface zonder API-key te testen. Dit zijn GEEN historische marktdata.
- **Backtests** met vaste, niet-geoptimaliseerde parameters; 70% ontwikkeling / 30% onaangeroerde testperiode, met reset van fictief kapitaal tussen de segmenten. De indicatoren gebruiken uitsluitend informatie uit hun verleden.
- Long-only, maximaal **0,25% gepland verlies per trade**, maximaal 25% kapitaal per positie, blokkade op nieuwe entries na 1% dagverlies of 10% piek-tot-dal drawdown. Een gap kan *meer* verlies veroorzaken dan 0,25%.
- Inbegrepen transactiekosten en slippage bij instap én uitstap; conservatieve stop-first aanname als stop en target binnen dezelfde OHLC-candle geraakt worden.
- Interactieve **historische candle-replay**, statistieken, winrate, profit factor, expectancy in R en CSV-export van trades.
- **CoinGecko API-adapter** met Demo- en Pro-authenticatie via omgevingsvariabelen, foutafhandeling voor 429/rate limiting, timeout en caching.

## Starten op Windows

Gebruik voor v0.1 **Python 3.13 (Windows x64, standaard CPython)**. Python 3.15 wordt niet ondersteund door deze dependencyset. Open PowerShell in deze map. Met Python Install Manager kun je Python 3.13 installeren via `py install 3.13`; anders via https://www.python.org/downloads/windows/.

```powershell
py -3.13 -m venv .venv-313
.\.venv-313\Scripts\python.exe -m pip install --upgrade pip
.\.venv-313\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv-313\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8501
```

Open **http://127.0.0.1:8501**.

**Makkelijkste optie op Windows:** dubbelklik op `START_WINDOWS.bat`. Het script gebruikt een aparte Python 3.13-omgeving (`.venv-313`), controleert bij elke start de dependencies en opent daarna automatisch je lokale dashboard. Laat het zwarte venster open zolang je de app gebruikt.

### Installatiefout bij pandas / ontbrekende uvicorn

Als pandas om Visual Studio of `vswhere.exe` vraagt, probeert pip uit broncode te bouwen. Gebruik bovenstaande Python 3.13-instructies met `--only-binary=:all:`. Een oude `.venv` met Python 3.15 mag blijven staan: de nieuwe omgeving heet `.venv-313`. De fout `No module named uvicorn` is een gevolg van de afgebroken installatie. Installeer alle requirements succesvol voordat je de app start.

### macOS / Linux

Gebruik ook hier Python 3.13 (`python3.13` in plaats van `python3` hieronder).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8501
```

## CoinGecko API koppelen (later)

1. Gebruik alleen een **read-only CoinGecko-data-API-key**. Een CoinGecko-key is geen exchangesleutel en heeft geen koop/verkooprechten.
2. Kies in PowerShell (alleen geldig voor dit PowerShell-venster):

```powershell
$env:COINGECKO_PLAN = "demo"
$env:COINGECKO_API_KEY = "JOUW_SLEUTEL"
python -m uvicorn app:app --host 127.0.0.1 --port 8501
```

3. Selecteer **CoinGecko API** in de interface. De backend gebruikt `x-cg-demo-api-key` met `api.coingecko.com` of `x-cg-pro-api-key` met `pro-api.coingecko.com`. Stuur de key **niet via de browser** en commit hem nooit naar Git. Een `.env.example` is alleen een sjabloon; de app laadt zelf geen `.env`-bestand (gebruik systeemomgevingsvariabelen of een environment loader).

### Belangrijke CoinGecko-datarestricties

- `/coins/{id}/ohlc` geeft **OHLC**, geen exacte handelsvolumes per candle. De **breakout + volume**-strategie blokkeert daarom expliciet met CoinGecko OHLC. Een apart bronbestand met echte, op dezelfde candles afgestemde OHLCV is hiervoor nodig.
- De CoinGecko Demo-granulariteit is automatisch en hangt af van het aantal opgevraagde dagen. De app beperkt de keuze voorlopig tot 7/14/30 dagen; met weinig testcandles kunnen indicatoren en betrouwbaarheidsanalyses ontoereikend zijn.
- CoinGecko aggregeert koersdata uit meerdere bronnen; een gesimuleerde uitvoering op geaggregeerde OHLC kan geen echte orderboekuitvoering op een specifieke beurs representeren.
- Voor historisch verder teruggaande of fijnere data kan een ander CoinGecko-abonnement of een extra databron nodig zijn.
- De API staat voor deze MVP nog niet onder een **echte autonome forward scheduler**. Historische replay is géén live forward paper trading.

Officiële docs: https://docs.coingecko.com/reference/coins-id-ohlc en https://docs.coingecko.com/reference/coins-id-market-chart.

## Testen

```bash
python -m pytest -q
```

## Ontwerp en grenzen

- `market_data.py`: synthetische data + CoinGecko-adapter, controle van candles.
- `strategies.py`: vaste indicatoren en signalen op **gesloten** candles.
- `engine.py`: backtest/replay, risicoregels, conservatieve kosten en transactielog.
- `app.py`: FastAPI, lokale webinterface + JSON endpoints, tijdelijke sessie.
- `static/`: Nederlandstalig dashboard zonder trackers/CDN.
- `tests/`: unit- en integratietests.

Meer informatie over het latere AI-onderzoek: `AI_STRATEGIE_ONDERZOEK.md`.

**Beperkingen v0.1**

1. De bot is een **lokale onderzoekstool**, niet een production-ready 24/7-automatisering. Replay kan worden hervat zolang het proces actief is; na herstart wordt het geheugen gewist. Exporteer resultaten naar CSV.
2. Er is geen AI-API aangesloten. De strategieën zijn expliciete regels, geen oncontroleerbare AI-voorspellingen. AI kan later als **research assistant** hypothesen formuleren, maar krijgt geen handelstoegang.
3. Geen strategie-optimalisatie, monte-carlo of bewijs voor rendabiliteit. Bij weinig trades wordt dat zichtbaar gemeld.
4. Alleen long, één open positie, drie vooraf gekozen coins (Bitcoin, Ethereum, Solana). Geen cross-coin portfolio of FX-conversie.
5. Prijsvermelding en fictief kapitaal staan in **USD**, geen EUR. Belastingen zijn niet in de trading-P&L opgenomen.
6. De max drawdown-blokkade voorkomt nieuwe entries, maar liquideert een bestaande positie niet gedwongen. Fictieve cijfers kunnen daardoor meer dalen.
7. Daglimiet toetst op bar-open en kan bij intrabar verlies te laat reageren. Bij 4u-candles is dat een illustratie, geen professioneel risicosysteem.
8. Grafiek laat een afsluitkoers-lijn zien, geen volledige candle-chart. Dit kan later worden uitgebreid.
9. OHLC-backsimulatieresultaten benaderen geen echte orderboekdiepte, funding, spread of belastingen. Gemodelleerde commissies/slippage zijn vereenvoudigingen.
10. Volume in de DEMO is uitsluitend synthetisch. Niet gebruiken om prestaties te claimen.

### Volgende implementatiefase

- Verifieer API-key en beschikbaar historisch tijdsbereik.
- Bouw caching naar SQLite, timestamp-geregelde **forward paper engine** en een scheduler die uitsluitend nieuwe definitief gesloten candles verwerkt.
- Voeg echte OHLCV-databron toe indien gewenst, anders alleen EMA/RSI/prijsuitbraak.
- Voeg portfolio- en kill-switchmonitoring, een duurzaam journal, parametrische research met gescheiden walk-forward-data en AI als *niet-uitvoerende* hypothese-generator toe.

**Geen financieel advies.** Dit project dient uitsluitend om de basis uit de 100-dagencursus te oefenen en strategieën te weerleggen of voorlopig te ondersteunen; het is niet bedoeld om automatisch live trading te starten.
