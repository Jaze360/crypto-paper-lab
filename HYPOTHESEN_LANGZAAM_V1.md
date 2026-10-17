# Twee nieuwe vaste cartridges — 17 oktober 2026

Regels vastgelegd vóór de eerste uitvoering. Dit zijn eigen hypothesen, geen gerepliceerde optimale instellingen uit een paper. De bekende 2023–2026-markten zijn al bekeken. Deze meting is ontwikkeling en vergelijking op bekende historische data, geen ongezien winstbewijs.

## Gelijke testbasis

Eén cartridge, drie kalenderjaren gesloten uurcandles, dezelfde tien vooraf geselecteerde coins, kosten en risicolimieten als v0.13. Voor de eerste vergelijking worden de coinselectie en exacte eindtijd van de bestaande cartridgetests vastgezet. Ontbrekende historie blijft een fout, zonder vervanging. Er wordt geen parameterzoektocht uitgevoerd en geen achteraf beste variant gekozen.

De twee nieuwe cartridges gebruiken LONG/cash. SHORT wordt niet automatisch aan een nieuwe hypothese toegevoegd; de bestaande vier LONG/SHORT-cartridges blijven als referenties beschikbaar. Een positief longresultaat bewijst niets over een shortvariant.

## Gezamenlijke regels van beide nieuwe cartridges

Prijsuitvoering, stops en targets blijven op de uurcandles in dezelfde paper-engine. Alleen signalen en ATR gebruiken volledige gesloten UTC-dagen die uit die uurcandles worden opgebouwd. Een dag vereist exact 24 uurcandles. De eerste gedeeltelijke kalenderdag wordt uitgesloten van dagindicatoren. Onvoltooide dagen worden nooit vooruit ingevuld.

Op een uurcandle die om 23:00 opent zijn alle daggegevens pas na haar sluiting bekend; een daaruit afgeleid signaal wordt op de volgende open om 00:00 uitgevoerd. Historische daggegevens worden uitsluitend vanaf hun werkelijke beschikbaarheid aan de uurcandles gekoppeld. Geen dag-high of dag-close gebruiken tijdens dezelfde nog onvoltooide dag.

ATR14 wordt op volledige gesloten dagen met Wilder-smoothing berekend. De beschermende stop ligt bij instap 3× deze dag-ATR onder de fill; target 8× erboven. Ze worden daarna niet verplaatst. Dit zijn brede beschermingen, geen op de uitkomsten afgestemde parameters. Een kanaal- of momentumexit kan eerder sluiten. Intrabar stoptargets volgen de bestaande gap- en stop-first-regels. Maximaal 0,25% gepland account-risico en 25% instapblootstelling; de grotere stopafstand verkleint de positie automatisch. Geen hefboom, maximaal één positie, geen onbeperkt herinvesteren.

## Langzaam momentum · 63 dagen

- Iedere maandag om 00:00 UTC een beslissing, gebaseerd op de net gesloten zondag.
- Momentum = laatst gesloten dag-close / dag-close 63 volledige dagen eerder − 1.
- Bij positief momentum mag een leeg account LONG instappen. Bij momentum nul of negatief wordt een bestaande positie gesloten. Anders cash of de bestaande long aanhouden.
- Na een stop/target mag de eerstvolgende wekelijkse positieve beslissing opnieuw instappen. Geen intraday herinstap en geen afzonderlijke wachttijd. Geen maximale positieduur.
- Minimaal 64 volledige gesloten dagen voor een geldig momentumsignaal. De volledige driejaarsperiode begint als leeg fictief account; de eerste dagen dienen als warm-up.

## Kanaaluitbraak · 55/20 dagen

- Iedere dag om 00:00 UTC een beslissing op de net gesloten dag.
- LONG als de dag-close strikt boven de hoogste high van de voorafgaande 55 gesloten dagen ligt. Die 55 dagen sluiten de beslisdag zelf uit.
- Exit als de dag-close strikt onder de laagste low van de voorafgaande twintig gesloten dagen ligt, eveneens exclusief beslisdag.
- Na een exit worden 24 volledige uurcandles overgeslagen. Daarna kan een nieuwe dagelijkse uitbraak opnieuw instappen. Geen maximale positieduur.
- Minimaal 56 volledige gesloten dagen voor de eerste breakoutbeslissing.

## Kosten, beoordeling en rapportage

10.000 USDT fictief kapitaal per coin; fee 0,10% per zijde en slippage 0,05% per fill. Dubbele kosten gebruikt dezelfde engine met verdubbelde kosten; het handelspad en de positiegrootte kunnen veranderen. De shortleenproxy wordt in deze twee LONG/cash-cartridges niet toegepast, want er zijn geen shorts.

De bestaande volledige test en drie afzonderlijke controleperioden blijven ongewijzigd. Iedere controleperiode herstart kapitaal en posities. Tradeaantallen, slechte perioden en afwijzingen blijven zichtbaar. Dezelfde minimumaantallen en kostenstresscriteria blijven gelden, ook als langzaam handelen minder trades oplevert. Er wordt niets automatisch voor livehandel geactiveerd.

De 10%-drawdownstop blijft behouden en blokkeert nieuwe entries permanent. Het account en eventuele open positie worden verder gevolgd. De stopdatum wordt zichtbaar gemaakt; de volledige periode aan data betekent dus niet dat een afgekeurde strategie drie jaar nieuwe posities blijft openen. Historische uitkomsten worden niet overschreven.

## Onderbouwing en beperking

[Liu & Tsyvinski, Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877) onderzoekt historische momentumvoorspelbaarheid. [Le & Ruthbah, Monash, Trend-following strategies for crypto investors](https://www.monash.edu/business/mcfs/our-research/all-projects/investment-strategy/trend-following-strategies-for-crypto-investors) bespreekt trendvolgen en de invloed van transactiekosten. Deze bronnen onderbouwen de onderzoeksrichting; ze bewijzen deze exacte 63-daagse en 55/20-regels met onze stops en kosten niet. Ook kostenbesparing is pas na de meting een uitkomst, geen garantie.

Huidige coinselectie, spotprijzen, beperkte blootstelling en herhaald gebruik van dezelfde historische markten beperken conclusies. Voor een toekomstige handelsstrategie is nieuw paper-forwardonderzoek nodig nadat de regels zijn vastgezet. Deze release blijft paper-only.
