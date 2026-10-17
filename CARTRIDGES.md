# Strategiecartridges — v0.15

Een cartridge bevat beslisregels, een stabiele ID, eigen versie, uitleg, relevante parameters, warm-up, LONG/SHORT-signalen, instapreden en eventuele vaste regels of volumevereisten. Alle cartridges gebruiken dezelfde PaperEngine. Posities, kosten, onderpand, stops, risicobudget en opslag blijven gedeeld.

## Gebruik

Kies op het hoofdscherm één van zes LONG/SHORT-cartridges en klik **Test cartridge**. Alle cartridges gebruiken hetzelfde vaste plan: drie kalenderjaren, uurcandles, top tien en kostenstress. Er zijn geen instelbare parameters in deze bediening. De nieuwe cartridges zijn alleen beschikbaar in dit vaste plan. De oude bediening op `/archief` behoudt de vier oorspronkelijke cartridges en haar eerdere onderzoeksfuncties.

`PRIMARY_IDS` bepaalt de zes zichtbare keuzes; de volledige registry bewaart ook de zes oude implementaties voor referentie en oude rapporten. `cartridge_slow_both.py` breidt de twee v1.0 LONG-cartridges uit zonder hun bestanden te veranderen. `long_reference` verklaart de afzonderlijk te testen oorspronkelijke LONG-cartridge. De vier nieuwe modules bevatten ieder een eigen `Cartridge`: Supertrend, Bollinger, Keltner en mislukte uitbraak. [Vaste regels v0.15](HYPOTHESEN_V015.md).

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

Het optionele `prepare`-contract voegt causale features toe vóór het maken van signalen. `dependencies` neemt aanvullende bronmodules op in de vingerafdruk; `directions` beschrijft ondersteunde richtingen. De twee nieuwe modules gebruiken `slow_features.py`: alleen volledige UTC-dagen, bekend na het sluiten van hun laatste uurcandle. Hun ATR is een dagelijkse Wilder-ATR(14); uitvoering blijft op het volgende uur. De vier bestaande cartridges gebruiken deze hook niet en behouden hun uurindicatoren en handelsregels. Zie [vaste hypothesen](HYPOTHESEN_LANGZAAM_V1.md).

De referentievergelijking, Botarena en bestaande optimizer blijven bewust begrensd tot hun vooraf vastgelegde cartridges. Nieuwe cartridges gaan daar niet automatisch in mee. Er is geen automatische cartridgekeuze op basis van testwinst.

Bij gewijzigde handelsregels: verhoog de cartridgeversie, voeg LONG/SHORT-, causaliteits- en uitvoeringscontroles toe en leg het onderzoeksplan vast vóór de test. Laat code via de bestaande repo-update binnenkomen en herstart de server om die te laden. Er is geen automatische mapscan, URL-import, willekeurige Python-upload of externe pluginmarktplaats. Deze ingebouwde Python-modules zijn vertrouwde applicatiecode, geen sandbox voor onbekende scripts. Bestaande updater, back-up en rollback ondersteunen de modules als gewone bronbestanden.

Dit is een eigen modulaire implementatie naar het cartridge-idee. Geen claim van identieke werking of broncode van Rubicon. Paper-only; geen live orders of hefboom toegevoegd.
