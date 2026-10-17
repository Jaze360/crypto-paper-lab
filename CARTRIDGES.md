# Strategiecartridges — v0.11

Een cartridge bevat beslisregels, een stabiele ID, eigen versie, uitleg, relevante parameters, warm-up, LONG/SHORT-signalen, instapreden en eventuele vaste regels of volumevereisten. Alle cartridges gebruiken dezelfde PaperEngine. Posities, kosten, onderpand, stops, risicobudget en opslag blijven gedeeld.

## Gebruik

Klik **Cartridges** bovenaan het dashboard. Kies EMA, RSI of breakout voor een volgende afzonderlijke test. De keuze verandert de geselecteerde strategie en toont alleen haar relevante strategieparameters. Je bestaande instellingen worden niet gereset en er start niets automatisch. Klik daarna **Start onderzoek**. De vaste trend-pullbackcartridge opent het bestaande BTC/ETH/SOL-protocol; die regels blijven vast.

De drie referenties blijven dezelfde drie referenties en de Botarena blijft negen profielen bevatten. Het verplaatsen van code maakt geen strategie winstgevender. Twaalf volledige LONG/SHORT/BOTH-uitkomsten zijn vergeleken met vóór de omzetting vastgelegde v0.10-uitkomsten en blijven identiek.

Nieuwe resultaten bewaren cartridge-ID, versie en hashes van de cartridge, interface, registry, indicatoren en engine in hun metrics. Die metadata komen ook mee in vergelijkingen en kostenstress. De detailanalyse toont de versie. Oude opgeslagen rapporten krijgen geen achteraf verzonnen versie.

Een nieuwe replay met vastgelegde vingerafdruk wordt niet hervat als cartridge of engine sindsdien is gewijzigd. Het oude resultaat opent als bewaard resultaat zonder door te spelen; start een nieuwe replay voor nieuwe code. Oudere replays zonder vingerafdruk behouden hun bestaande compatibiliteitsgedrag, maar hun bronversie kan niet achteraf worden bewezen. Dit systeem archiveert geen uitvoerbare oude engineversies.

## Structuur voor ontwikkelaars

- `cartridge_api.py`: vast interfacecontract.
- `cartridge_ema.py`, `cartridge_rsi.py`, `cartridge_breakout.py`, `cartridge_pullback.py`: afzonderlijke regels.
- `cartridges.py`: expliciete ingebouwde registry en vingerafdrukken.
- `strategies.py`: gedeelde parametercontrole, causale indicatoren en warm-upmaskering.
- `engine.py`: uitvoering op de volgende candle-open, risico en boekhouding.

Een nieuwe cartridge definieert één `Cartridge` en wordt expliciet geïmporteerd en geregistreerd in `cartridges.py`. De normale API-keuze en bibliotheek worden uit de registry afgeleid. Een nieuwe cartridge met bestaande indicatoren hoeft de engine niet te veranderen. Nieuwe indicatoren vereisen uitbreiding van de gedeelde indicatorlaag en causaliteitstests. Nieuwe instelbare parameters vereisen een gecontroleerde schema- en formulieruitbreiding. Kostenmodellen, multi-assetposities en derivatenfunding zijn afzonderlijke enginewijzigingen; een cartridge kan die niet declaratief toevoegen.

De referentievergelijking, Botarena en bestaande optimizer blijven bewust begrensd tot hun vooraf vastgelegde cartridges. Nieuwe cartridges gaan daar niet automatisch in mee. Er is geen automatische cartridgekeuze op basis van testwinst.

Bij gewijzigde handelsregels: verhoog de cartridgeversie, voeg LONG/SHORT-, causaliteits- en uitvoeringscontroles toe en leg het onderzoeksplan vast vóór de test. Laat code via de bestaande repo-update binnenkomen en herstart de server om die te laden. Er is geen automatische mapscan, URL-import, willekeurige Python-upload of externe pluginmarktplaats. Deze ingebouwde Python-modules zijn vertrouwde applicatiecode, geen sandbox voor onbekende scripts. Bestaande updater, back-up en rollback ondersteunen de modules als gewone bronbestanden.

Dit is een eigen modulaire implementatie naar het cartridge-idee. Geen claim van identieke werking of broncode van Rubicon. Paper-only; geen live orders of hefboom toegevoegd.
