# Wijzigingen

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
