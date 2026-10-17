# Dashboardreferentie en grenzen van de reconstructie

Bronnen: [botexperiment](https://www.youtube.com/watch?v=4IJl6e4m7sQ) en [tutorial](https://www.youtube.com/watch?v=ce9lJz45bWM). Onderzocht op 17 oktober 2026. Installatiestappen zijn geen onderdeel van de implementatie.

## Zichtbaar en overgenomen

- Botexperiment, rond 3:13–4:47: compacte lijst van gesloten trades met positieve/negatieve kleur en uitklapbare details. Het lab toont echte journalgegevens, opgeslagen stop/target, kosten, duur, instapregel en exitreden. De kleuren en donkere panelen benaderen het zichtbare rapport.
- Vermogensweergave, statistieken en verliesanalyse gebruiken de eigen engine-uitkomsten. Geen opbrengsten uit de video overgenomen.
- Tutorial rond 44:05–47:44: strategie-instructies en bewaarde toestand. Het lab gebruikt expliciete gevalideerde parameters, bewaart die bij ieder onderzoek en kan replays hervatten.
- Tutorial rond 50:34–52:42: strategieën vergelijken en verbeteren. De lokale automatische afstelling probeert maximaal twaalf vastgelegde varianten en bewaart de selectieredenen; dit is geen LLM-agent of vrije broncodeherschrijving.

## Geen volledige 1-op-1-kopie

Het botexperiment toont rond 6:51–7:40 een apart toekomstig platform met traderkeuze en een deployscherm met budget, sessieduur, risicokeuze en Paper/Real. De volledige onderliggende app en gedrag van alle bedieningselementen zijn niet uit de video beschikbaar. Dat scherm is niet als volledig werkende kopie geïmplementeerd in v0.9. Het lab heeft een eigen instelpaneel voor bestaande onderzoeken.

De tutorial beschrijft vanaf 51:55 en 53:50 premium dashboards, strategie-assets en OpenClaw-agenten. De video bevat geen volledige broncode, oorspronkelijke grafische assets of reproduceerbare definitie van alle agents. V0.9 bevat geen OpenClaw-integratie, autonome multi-agentwerkers, Telegram-heartbeats, onbeheerde live forward-trading, modelwisseling of nieuws/funding-scans. Het handelslog is een historisch paperjournal, geen live exchangefeed.

Voor volledige scherm- en gedragsovereenkomst zijn toegang tot een werkende demo of de oorspronkelijke bronbestanden/assets en verdere verificatie nodig. De getoonde ontwerpkeuzes mogen niet worden opgevat als bewijs dat alle achterliggende functies gelijk zijn.

## Blijvende grenzen

Het lab blijft paper-only. Er is geen Real-schakelaar, order-API, leverage-engine of walletbeheer toegevoegd. Automatische parameterselectie geeft geen winstgarantie. Een voorstel overschrijft geen bestaande instellingen en slecht scorende kandidaten blijven zichtbaar.
