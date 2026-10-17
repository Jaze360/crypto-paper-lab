# AI Strategy Research — ontwerp voor versie 0.2

De huidige v0.1 bevat **geen actieve taalmodelintegratie**. In de volgende fase kan een model zoals GPT worden gebruikt als _research assistant_, uitsluitend voor het voorstellen van hypotheses, verklaren van prestaties en formuleren van falsificatietests. Het model krijgt geen orderrechten en wijzigt de risicobeperkingen niet.

## Begrensde onderzoeksworkflow

1. **Vraagstelling**: bepaal munt, timeframe, datakwaliteit, handelskosten en onderzoeksperiode.
2. **Hypothese**: AI schrijft één duidelijk toetsbaar voorstel in gestructureerde velden, inclusief nulhypothese.
3. **Regels reviewen**: mens keurt signalen, exits en parameters goed voordat code wordt aangepast.
4. **Backtest**: deterministische engine beoordeelt het voorstel uitsluitend op ontwikkelingsdata; elke parameterzoekactie wordt gelogd.
5. **Walk-forward**: nieuwe, onafhankelijke gegevens worden apart gehouden. Herhaald gebruik van dezelfde testset verandert die dataset in ontwikkelingsdata.
6. **Falsificatietests**: controleer hogere fees, meer slippage, transactiekosten in USD, gaps, liquiditeit, abnormale gebeurtenissen en meerdere regimes.
7. **Research-notitie**: AI beschrijft ook mogelijke redenen waarom een goed resultaat schijnbaar is en waarom het mogelijk niet in echte handel reproduceerbaar is.
8. **Paper-forward**: alleen door expliciete goedkeuring geactiveerde strategieën worden op nieuw binnenkomende, afgeronde candles geëvalueerd.
9. **Experimenteercontrole**: een nieuw voorstel krijgt een uniek experiment-ID en mag eerdere testuitkomsten niet heimelijk overschrijven.

## Vast outputcontract voor AI-researchvoorstellen

```
experiment_id: UUID
asset: bitcoin | ethereum | solana
candle_source: coingecko_ohlc | exchange_ohlcv
strategy_name: string
hypothesis: string
entry_rules: list[string]
exit_rules: list[string]
invalidation_rules: list[string]
parameters: dictionary
test_period: string
fee_assumption: number
slippage_assumption: number
known_data_gaps: list[string]
possible_failure_modes: list[string]
required_reviewer_approval: true
execution_mode: simulation_only
```

## Cursusregels (hardcoded buiten AI)

- 0,25% van actuele fictieve equity als maximaal gepland verlies per positie, inclusief veronderstelde fees en slippage.
- Max. 25% exposure in een long positie, één positie tegelijk.
- Geen geld lenen, geen leverage, geen shorts, geen direct of indirect live broker orderpad.
- Nieuwe trades worden geblokkeerd bij de voorgeschreven daglimiet of drawdownlimiet.
- Signalering uitsluitend op een **volledig gesloten candle**, entry vanaf de **volgende** candle; geen look-ahead of repainting.
- Geen trading op kunstmatig samengesteld volume.
- Geen winstclaims op kleine steekproeven of louter synthetische data.

## Als je straks CoinGecko toevoegt

1. API-plan en toegestane endpoints controleren.
2. OHLC en tijdstempels valideren. CoinGecko OHLC bevat geen volume per candle.
3. Candles lokaal duurzaam opslaan en alleen volledig nieuwe, gesloten candles doorsturen naar de engine.
4. Automatische forward paper scheduling **zonder** orders naar een exchange, en crash-safe, idempotente verwerking toevoegen.
5. Tests voor dubbele API-responses, late candles, netwerkfouten, serverrestart en gebrek aan data.
6. Data out-of-sample vergelijken met buy-and-hold en nulstrategie en kostenstress uitvoeren.

De AI beoordeelt resultaten; de engine berekent ze. Een hypothese die goed scoort op historische data is nog geen bewezen winstgevende strategie.
