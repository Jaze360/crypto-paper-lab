# Vooraf vastgelegd onderzoek — trend-pullback v1

Vastgelegd op 17 oktober 2026, vóór uitvoering van dit nieuwe protocol. De eerdere BTC- en SOL-resultaten zijn al bekeken. Dit is nieuwe strategieontwikkeling op bekende historische markten, geen ongezien bewijs.

## Referenties

De bestaande EMA 8/21, RSI 14:30/55 en breakout 20 × volume 1,5 blijven de v0.9-referenties. BOTH, ATR14 stop 1,5×, target 3×, geen wachttijd, geen trendfilter, geen maximale duur. Budgetten blijven 0,25% gepland risico, 25% instapblootstelling, 1% dagelijkse entry-stop en 10% permanente drawdownstop. Er worden geen bestaande opgeslagen uitkomsten overschreven.

## Eén nieuwe hypothese

Een terugval binnen een aanhoudende trend kan een ander instapmoment geven dan een snelle EMA-kruising. Dit is een hypothese, geen aanname van winst.

- LONG: vorige gesloten candle sluit boven EMA200, EMA50 ligt boven EMA200 en EMA200 ligt hoger dan twintig candles eerder. Close heroverde op die candle EMA20 na een close op of onder EMA20.
- SHORT: alle voorwaarden gespiegeld.
- Instap op de volgende candle-open. Eén positie tegelijk, 100% onderpand voor shorts, geen hefboom.
- ATR14 stop 2,5× en target 5× vanaf de werkelijke instapfill. Stop-first als stop en target in dezelfde candle vallen.
- Signaalexit na close voorbij EMA50 tegen de positie in, uitgevoerd op de volgende open. Gapregels behouden voorrang.
- Maximaal dertig actieve candles; daarna exit op de volgende open. Twaalf volledige candles wachten na iedere exit.
- Geen parameteroptimalisatie, extra kandidaten of wijziging van deze regels na de resultaten.

## Vast testontwerp

BTC, ETH en SOL, drie jaar publieke Binance-SPOTcandles van vier uur. Eerste 60% is ontwikkelcontext, daarna twee gescheiden vensters van 10% en laatste 20%. Iedere combinatie start met nieuw fictief kapitaal en zonder positie. Alle coins, verliezende varianten, lage tradeaantallen en datafouten blijven zichtbaar. De coins zijn vooraf gekozen, geen willekeurige steekproef.

Per periode: rendement na kosten, drawdown, aantallen per richting, kosten, stopredenen, positieduur, blootstelling, risicoblokkades, benchmark 25% en dubbele kosten. Rendementen worden niet opgeteld tot een fictieve portefeuille. Minder dan dertig trades blijft onvoldoende bewijs; meer trades geven geen garantie.

## Kostencontrole voor shorts

Gecontroleerd op 17 oktober 2026:

- [Binance fee-uitleg](https://www.binance.com/en/support/faq/detail/360033544231) gebruikt als **hypothetisch rekenvoorbeeld** 0,02% maker en 0,05% taker. Het actuele [account-/producttarief](https://www.binance.com/en/fee/futureFee) is niet vastgesteld. Geen kortingsprogramma aangenomen.
- [Kraken fee schedule](https://www.kraken.com/features/fee-schedule): Futures tier 1 toont 0,02% maker en 0,05% taker. Spot-margin kent [extra openings- en rolloverkosten](https://support.kraken.com/articles/206161568-what-are-the-fees-opening-and-rollover-for-trading-using-margin-); die zijn niet gelijk aan futureskosten.
- [Coinbase International Exchange](https://help.coinbase.com/en/international-exchange/trading-deposits-withdrawals/international-exchange-fees): public tier 10 perpetuals toont 0,020% maker en 0,040% taker. Dit is geen Coinbase Advanced-spot of US-futures. Producttoegang hangt van land en account af.

Alle strategieën krijgen dezelfde kostenbasis: het ingestelde huidige model (eerder 0,10% per zijde, 0,05% slippage, 0,02% per dag shortproxy), plus feegevoeligheid op 0,05% en 0,04%. Slippage en shortproxy blijven daarbij gelijk. Iedere combinatie krijgt ook dubbele fee, slippage en shortproxy, binnen de bestaande modelgrenzen.

Deze scenario's zijn **geen backtests van de genoemde derivatenbeurzen**. De koersbron blijft Binance spot in USDT; fundinggeschiedenis, basis tussen spot en perpetual, liquidaties, margin-openingskosten, orderboeken en regionale toegang zijn niet gereconstrueerd. [Perpetual funding](https://help.coinbase.com/en/global-exchange/funding/what-is-the-funding-fee) kan zowel LONG als SHORT laten betalen of ontvangen en is niet hetzelfde als een vaste shortleenproxy. De gebruikte tarieven mogen dus niet als volledige werkelijke kosten worden gepresenteerd.

De protocolversie, volledige parameters, hashes van engine/strategieën/protocol en de candlehash worden bij ieder rapport opgeslagen. Nieuwe data zijn nodig voor werkelijk toekomstige toetsing. Er wordt geen winnaar geactiveerd.
