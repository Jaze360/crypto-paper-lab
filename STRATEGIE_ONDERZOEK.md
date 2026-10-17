# Strategieonderzoek — 17 oktober 2026

Doel: andere kandidaten vinden dan steeds meer EMA/RSI-parameters zoeken. Dit is literatuuronderzoek, geen nieuw winstbewijs en geen claim dat onderstaande regels ons lab al verslaan. De drie bevroren referenties en trend-pullback blijven beschikbaar. De kandidaten hieronder zijn nog niet geïmplementeerd of door ons getest.

## 1. Langzamer momentum per coin — eerste prioriteit

Gebruik een koersverandering over meerdere weken/maanden, met bijvoorbeeld een wekelijkse beslissing op dagcandles. Onderzoek LONG/cash afzonderlijk van LONG/SHORT. Dit verschilt van onze snelle EMA-kruisingen. Minder geplande beslismomenten kan omzet en kosten verlagen; daadwerkelijke trades moeten worden gemeten.

[Liu & Tsyvinski, Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877) vindt historische time-series-momentumvoorspelbaarheid. [Han, Kang & Ryu, Comprehensive Analysis under Realistic Assumptions](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) vindt sterkere aanwijzingen voor momentum per coin dan tussen coins, maar veel winst komt uit LONG; shorts, kosten en liquidaties kunnen uitkomsten sterk verslechteren. De auteurs noemen hun vele onderzochte instellingen een bron van selectiebias. Dit ondersteunt onderzoek, geen winstbelofte voor 2026.

Een mogelijk vooraf vast te leggen prototype: 63-daags momentum, wekelijkse beslissing, LONG bij positief momentum en anders cash. Een afzonderlijke shortvariant mag niet stilzwijgend dezelfde bewijsstatus krijgen. Deze getallen zijn een ontwerpsuggestie, geen uit de papers afgeleide optimale instellingen.

## 2. Langzame prijsuitbraak — tweede prioriteit

Een dagcandle-uitbraak boven de voorafgaande 55 dagen; exit beneden een korter kanaal, bijvoorbeeld twintig dagen. SHORT gespiegeld en apart beoordeeld. Beide kanalen sluiten de besliscandle uit; uitvoering op de volgende open. Dit is een langere horizon dan onze huidige volume-breakout en gebruikt een andere exit. De voorgestelde getallen zijn eigen kandidaten, geen bewezen combinatie.

[Hudson & Urquhart, Technical trading and cryptocurrencies](https://hull-repository.worktribe.com/output/2328042/technical-trading-and-cryptocurrencies) onderzoekt technische regelfamilies en rapporteert historische voorspelbaarheid, inclusief controles op meerdere vergelijkingen. Daartegenover vindt [A reality check on trading rule performance](https://www.sciencedirect.com/science/article/pii/S1544612320304414) zelden statistisch significante positieve meeropbrengsten na correcties voor selectie en marktfricties. De literatuur is dus niet eensgezind. Geen reden om een kanaaluitbraak als bewezen winnaar toe te voegen.

## 3. Trend met begrensde volatiliteitsblootstelling — derde prioriteit

Combineer een langzame trend met een lagere positie bij hoge gerealiseerde volatiliteit en een minimumverandering voordat wordt geherbalanceerd. Geen hefboom; maximaal dezelfde instapblootstelling en hetzelfde risicobudget. Dit is vooral een risicolaag, geen onafhankelijke bron van koersvoorspelling. De herbalanceerdrempel moet vooraf vaststaan; anders kan het verlagen van risico juist veel kleine kostbare orders opleveren.

[Le & Ruthbah, Monash, Trend-following Strategies for Crypto Investors (2023)](https://www.monash.edu/__data/assets/pdf_file/0011/3744821/Trend-following-Strategies-for-Crypto-Investors.pdf) onderzoekt momentum, volatiliteit en drawdowngestuurde strategieën op onder meer BTC en ETH. De resultaten over hun historische steekproef ondersteunen nader onderzoek, maar laten ook een substantiële invloed van transactiekosten zien. Hun oudere steekproef en blootstelling zijn niet hetzelfde als ons accountmodel. Vergelijk ook met een benchmark met vergelijkbare blootstelling; louter minder verlies door minder beleggen is geen bewezen handelsvoordeel.

## 4. Relatief momentum en pairs trading — later

Relatief momentum rangschikt coins en koopt relatief sterke coins, eventueel met shorts op zwakke coins. Dat is een portefeuillemodel en vereist een historisch belegbaar universum inclusief verdwenen/noteringen van coins. Alleen huidige winnaars kiezen geeft overlevingsbias. Han e.a. hierboven waarschuwt juist voor zwakkere cross-sectionele resultaten en schadelijke shortbenen.

Pairs trading handelt in een prijsverhouding tussen twee coins, met tegengestelde posities. [Pairs Trading in Cryptocurrency Markets, IEEE Access (2020)](https://ieeexplore.ieee.org/document/9200323/) rapporteert onderpresteren tegenover klassieke benchmarks in hun tests en sterke gevoeligheid voor kosten en uitvoering. Correlatie alleen bewijst geen stabiele evenwichtsrelatie. Beide vormen vereisen meerdere gelijktijdige posities, gezamenlijke kosten en portefeuillelimieten; onze huidige één-positie-engine is hiervoor onvoldoende. Daarom niet als goedkope extra cartridge presenteren.

## 5. Spot/futures carry — ander soort kandidaat

Koop spot en short een corresponderend futurescontract om een basisverschil te onderzoeken. Bij perpetuals hangt de opbrengst af van werkelijk ontvangen/betaalde funding; funding is variabel en geen vaste rente. [BIS, Crypto carry](https://www.bis.org/publications/working-paper-1087-crypto-carry) beschrijft economische kansen én beperkingen door margin en liquidatie. Geen risicoloze opbrengst.

Hiervoor zijn gesynchroniseerde spot- en derivatenprijzen, historische funding, contractregels, twee handelsbenen, collateral en basisrisico nodig. Onze huidige spotcandles met vaste shortleenproxy kunnen deze strategie niet eerlijk beoordelen. Eerst data en engine uitbreiden, daarna pas vergelijken. Een lagere futuresfee maakt deze datavereisten niet overbodig.

## Testontwerp vóór implementatie van kandidaten

Leg maximaal één vaste kandidaat per familie vast, inclusief exits, risicolimieten en kosten. Start met de eerste twee kandidaten en een afzonderlijke risicolaag; laat shortresultaten apart zien. Geen duizenden varianten en geen winnaar achteraf uitroepen omdat één coin groen is.

Gebruik gescheiden chronologische perioden, meerdere vooraf gekozen liquide coins en blootstelling-/risicobewuste benchmarks. Bewaar ook afwijzingen en alle gemaakte keuzes. Toon normaal en kostenstress, bruto/netto, funding zodra relevant, drawdown, omzet, duur en concentratie van winst in enkele trades. Corrigeer de bewijswaardering voor alle onderzochte strategieën en parameters; samenhangende coins of overlappende vensters zijn geen onafhankelijke bevestigingen.

De reeds bekeken 2023–2026-data zijn ontwikkel-/replicatiemateriaal, geen nieuw onaangeroerd bewijs. Zet na het vastleggen van regels een nieuw paper-forwardvenster open, beoordeel pas op een vooraf afgesproken datum en laat een laag tradeaantal als onvoldoende bewijs staan. Verlaag criteria niet alleen omdat alle kandidaten falen. Machine learning kan later onderzocht worden, maar lost een ontbrekend voordeel of onvolledige kostenmodellering niet vanzelf op.
