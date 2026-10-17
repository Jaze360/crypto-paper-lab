# Wijzigingen

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

