# Crypto Paper Lab — v0.14

**Cartridge kiezen → Test cartridge.** Drie kalenderjaren, gesloten 1-uurscandles, top tien coins en kosten staan vast. Uitsluitend paper trading; geen echte orders.

## Starten

Gebruik Python 3.13 x64. Pak de repository uit en dubbelklik **START_WINDOWS.bat**. Het startscript maakt zo nodig de Python-omgeving aan en installeert ontbrekende pakketten. Laat het servervenster open. Het dashboard staat op http://127.0.0.1:8501.

Krijg je een fout over ontbrekende uvicorn? Start via START_WINDOWS.bat; voer de server niet uit vanuit een oude v0.1-omgeving. De launcher gebruikt zijn eigen .venv-313 en stopt bij installatiefouten. Installeer zo nodig Python via de officiële Windows-download van python.org.

## De enige testkeuze

1. Kies één cartridge.
2. Klik **Test cartridge**.
3. Bekijk één resultaatregel per coin. Open alleen **Details** als je de kosten, LONG/SHORT-bijdragen en controleperioden wilt zien.

De test gebruikt alleen de geselecteerde cartridge, met vaste standaardregels. Geen keuze voor timeframe, bron, dagen, parameteroptimalisatie, Botarena of kostenmodellen in het hoofdscherm. Opgeslagen gebruikersinstellingen uit de oude bediening kunnen de vaste test niet veranderen.

Iedere geselecteerde coin krijgt dezelfde exacte periode: drie kalenderjaren tot de laatste gesloten uurcandle, inclusief schrikkeldagen. Op 17 oktober 2026 zijn dat 26.304 candles. Ontbrekende of te korte historie geeft een fout voor die coin; geen kortere periode, opvulling, vervanging of demodata. De huidige top tien wordt gecombineerd gerangschikt op marketcap en volume; zie [selectieregel](TOPSELECTIE.md). Een huidige selectie op historische data geeft selectie- en overlevingsbias.

De drie samenvattingskaarten tellen coins: volledig getest, positief na kosten, positief bij dubbele kosten. Ze tonen geen gemiddeld of gezamenlijk rekeningrendement. Per coin staan rendement over de volledige drie jaar, drawdown, trades, kostenstress en controle. De drie gescheiden controleperioden draaien automatisch op de achtergrond, ieder met nieuw fictief kapitaal. De volledige driejaarstest start één keer met kapitaal en kan de bestaande permanente risicostop bereiken; dat blijft zichtbaar in de beoordeling.

Een positieve backtest is aanleiding voor nieuw paper-onderzoek, geen toestemming of garantie om met echt geld te handelen. Criteria en beperkingen staan uitklapbaar bij de test. Naast de vier oorspronkelijke cartridges zijn er twee nieuwe vaste hypotheses: **Langzaam momentum · 63 dagen** en **Kanaaluitbraak · 55/20 dagen**. Beide gebruiken LONG/cash, voltooide UTC-dagen voor signalen en volatiliteit, en uitvoering en beschermende stops op uurcandles. Hun [regels zijn vooraf vastgelegd](HYPOTHESEN_LANGZAAM_V1.md); geen parameters kiezen of optimaliseren.

De permanente risicostop krijgt voorrang in de beoordeling, inclusief de eerste datum. De rest van de historie wordt nog verwerkt, maar de strategie mag daarna niet meer instappen. Een resultaat over drie jaar betekent dus niet noodzakelijk drie jaar actief handelen. Oude opgeslagen resultaten krijgen dezelfde duidelijkere weergave; hun getallen worden niet veranderd.

## Vaste kosten en risico

Per coin 10.000 USDT fictief kapitaal, één positie tegelijk. De oorspronkelijke vier cartridges gebruiken LONG + SHORT; de twee nieuwe gebruiken alleen LONG/cash. Fee 0,10% per zijde, slippage 0,05% per fill, vaste shortleenproxy 0,02% per dag. Kostenstress verdubbelt alle drie. Gepland risico maximaal 0,25% per trade, instapblootstelling maximaal 25%, dagelijkse entry-stop 1%, permanente drawdownstop 10%. Geen hefboom.

Dit zijn Binance-spotprijzen met een vereenvoudigd shortonderpandmodel. Historische perpetual-funding, margin-liquidaties en werkelijke orderboekuitvoering ontbreken. De kosten zijn een scenario, geen bevestigd actueel accounttarief van een beurs. Een stop-loss garandeert geen maximaal verlies bij gaps.

## Bewaren en bijwerken

Alle tests worden automatisch lokaal opgeslagen, buiten de programmamap. Open **Opgeslagen tests & updates** om eerdere cartridgetests terug te lezen, CSV te downloaden of een update klaar te zetten. Sluit daarna het servervenster en start **START_WINDOWS.bat** opnieuw. Updates maken eerst een back-up. Persoonlijke resultaten en sleutels worden niet gepubliceerd.

CoinGecko verzorgt de actuele selectie. Zonder sleutel wordt publieke toegang geprobeerd. Bij bronproblemen kun je een sleutel lokaal instellen via de link naar de oude API-instellingen; geen sleutel in GitHub of in de chat zetten. Binance levert publieke historische candles zonder handelsaccount.

Oude onderzoeken en de oude bediening blijven apart beschikbaar via **Oude onderzoeken en API-instellingen**. Oude vieruursrapporten worden niet als nieuwe uurtests gepresenteerd. [Documentatie oude bediening](README_ARCHIEF.md).

## Ontwikkelen

Nieuwe handelsregels worden toegevoegd als [cartridge](CARTRIDGES.md). Broncode komt via de expliciete ingebouwde registry; geen willekeurige Python-upload of externe code-import. Het nieuwe testplan staat in simple_lab.py. Bestaande onderzoeks-API's blijven beschikbaar voor oudere resultaten, maar staan niet in de primaire bediening.

Tests: installeer de ontwikkeldependencies in requirements.txt en voer `python -m pytest -q` uit vanuit de projectmap. Tests controleren onder meer exacte tijdgrenzen, ontbrekende uren, geselecteerde cartridge, kostenstress, opslag, updater, herstartgedrag en bestaande handelsregels.
