# Wijzigingen

## 0.2.0
- Lokale SQLite-opslag buiten de installatie; instellingen, runhistorie, CSV-datasets en replayvoortgang.
- Exacte candleopslag zonder verlies van floatprecisie; replay opnieuw opbouwen na herstart.
- Optionele Windows DPAPI-opslag van CoinGecko-sleutel.
- Publieke updates zonder login, private updater via GitHub CLI; commit vastgezet bij downloaden, pad- en checksumcontrole, back-up en herstel van onderbroken bestandstransacties.
- Nieuwe launcher past updates toe vóór dependencycontrole en start de browser pas na succesvolle serverstart.
- 12 geselecteerde USD-markten, publieke Kraken OHLCV en historische CSV-import; CoinGecko-perioden tot 365 dagen afhankelijk van toegang.
- Vaste strategievergelijking met drie chronologische vensters, kostenstress en twee buy-and-hold-benchmarks.
- Candle-uitvoering gecorrigeerd: geen instap op eerdere open na een intrabar uitstap.
- Alleen lokale webaanvragen kunnen instellingen, resultaten en updates wijzigen; geen live orderfuncties.

