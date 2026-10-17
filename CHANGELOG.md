# Wijzigingen

## 0.11.0
- Vier ingebouwde strategieën als afzonderlijke cartridges met expliciete registry en interface.
- Cartridgebibliotheek, keuze voor volgende test en alleen relevante strategieparameters zichtbaar.
- Versie en bronvingerafdruk per nieuw resultaat; gewijzigde nieuwe replays worden bij hervatten geweigerd.
- Twaalf volledige uitkomsten blijven identiek aan de vastgelegde v0.10-resultaten.
- Literatuuronderzoek naar vijf strategierichtingen, inclusief tegenbewijs, kosten en benodigde engine-uitbreidingen.

## 0.10.0
- Vast trend-pullbackprotocol naast drie bevroren referenties op BTC, ETH en SOL, met gemeenschappelijke datagrenzen.
- Vier gescheiden perioden en drie kostenscenario's, elk met dubbele kosten, opgeslagen vingerafdrukken en expliciete datafouten.
- Periode- en kostenkeuze, CSV-export en volledige verliesanalyse per combinatie.
- Officiële kostensources voor Binance, Kraken en Coinbase International met expliciet onvolledig shortkostenmodel.
- Maximaal dertig actieve candles voor de vaste hypothese; bestaande strategieën en replays behouden standaard geen tijdslimiet.
- 107 tests geslaagd; nieuwe tests dekken vaste referenties, eerdere-candle-signalen, shortspiegeling, tijdsexit, scenario's en opslag.

## 0.9.0
- Begrensde automatische parameterselectie: maximaal twaalf varianten, ontwikkeling, twee validatievensters en laatste test.
- Expliciete afwijzingen en kostenstress; geen instellingsovername als niemand voldoet.
- Dashboard met instelpaneel en uitklapbare echte paper-trades.
- Stop/target opgeslagen bij nieuwe gesloten trades.

## 0.8.0
- Verliesanalyse met bruto/netto, kosten, stopfrequentie, duur en accountaansluiting.
- Eerste permanente entry-stop en dagelijkse/permanente blokkades plus geblokkeerde instapsignalen zichtbaar.
- Vaste vergelijking van basis, twaalf candles wachttijd en wachttijd + EMA200-trendfilter.
- Ontwikkelcontext, drie testvensters, laatste 20% en kostenstress zonder parameterselectie.
- Filters optioneel bij overige tests; bestaande regels standaard behouden.
- Richting zichtbaar in lijst van opgeslagen onderzoeken.

## 0.7.0
- Botarena met negen vaste profielen, gelijke data en expliciete kosten.
- Resultaten, regels en profielhergebruik zonder automatische winnaarselectie.
- Bewaarde arena’s en uitsplitsing per deelnemer.
- Bronverantwoording van 30 YouTube-zoekresultaten via transcripties.

## 0.6.0
- Vereenvoudigde bediening met één startknop en keuze van onderzoekstype.
- Geavanceerde instellingen, onderhoud en resultaatdetails uitklapbaar.
- Vernieuwde responsieve vormgeving en resultaatkaarten bovenaan.
- Bestaande berekeningen en opslag behouden.

## 0.5.0
- Gesloten-traderesultaten uitgesplitst naar LONG/SHORT en exitreden.
- Bruto vóór kosten, slippage, commissies, shortleenkosten en netto bijdrage apart zichtbaar.
- Periodekeuze en CSV-export bij backtest, replay, vergelijking en walk-forward.
- Bestaande journals leesbaar zonder geschatte historische slippage of herberekening.
- Handelsregels en paper-only-grenzen behouden; 83 tests geslaagd.

## 0.4.0
- Paper LONG, SHORT of beide richtingen, met één positie tegelijk.
- Gespiegelde EMA-/RSI- en volume-breakdownsignalen voor shorts.
- Gereserveerd shortonderpand, directionele P&L, slippage en commissies.
- Instelbare vaste shortleenkosten en stressvariant.
- Stop/target, gaps, kapitaalblokkades en negatieve equity correct doorgerekend voor shorts.
- Richting, leenkosten en positieduur in rapporten en CSV; exacte hervatting van nieuwe replays.
- Oude long-only-replays blijven als opgeslagen resultaat beschikbaar.

## 0.3.0
- Meerjarige publieke OHLCV met paginering, data-only endpoint en uurcache; tot 5 jaar op 1u/4u/1d, in USDT.
- Instelbare strategieparameters met bereik- en volgordevalidatie; risicobudgetten blijven vast.
- Tijd in markt, gemiddelde/maximale blootstelling en positieduur in resultaten.
- Uitbreidende walk-forward-vensters met beperkte parameterkeuze en laatste 20% buiten alle selecties.
- Vergelijking per coin over maximaal vier coins; ook fouten blijven in het rapport staan.
- Achtergrondtaken met voortgang en opgeslagen resultaten.
- Candle-engine versneld; geen gebruik van toekomstige candles bij parameterkeuze of signalen.
- Dashboard zonder browsercache; oudere resultaten blijven leesbaar.

## 0.2.0
- Lokale opslag, private/publieke updater, Windows-sleutelversleuteling, Kraken OHLCV en CSV-import.
- Vaste strategievergelijking met kostenstress, tijdvensters en benchmarks.
- Herstel van intrabar uitvoeringsvolgorde; uitsluitend paper trading.

