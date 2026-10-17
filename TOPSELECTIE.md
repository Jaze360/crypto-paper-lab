# Top 5 / 10 volgens marketcap en volume

Het standaardonderzoek **Cartridges testen · top 5 / 10 coins** kiest tien coins, of vijf via de enige extra keuzelijst. Dit voert het vaste protocol uit op vier bestaande cartridges in BOTH, elk met een eigen fictief account. Dezelfde kosten, perioden en risicolimieten gelden voor iedereen. Individuele tests en het oorspronkelijke vaste BTC/ETH/SOL-protocol blijven beschikbaar.

## Exacte selectieregel

1. Haal de eerste honderd coins op uit [CoinGecko coins/markets](https://docs.coingecko.com/reference/coins-markets), gesorteerd op marketcap in USD. Haal ook de stablecoincategorie op.
2. Sluit stablecoins uit via die categorie, plus verpakte/gestakete varianten via naamfilter en expliciete bekende IDs. Ontbrekende, niet-positieve of ongeldige marketcap/volumegegevens worden uitgesloten. De classificatie is afhankelijk van de bron en kan onvolledig zijn.
3. Rangschik geldige kandidaten afzonderlijk op marketcap en gerapporteerd 24-uursvolume. Beide tellen even zwaar: score = cap-rang + volume-rang. Kleinste som eerst. Bij gelijke som wint hogere marketcap; daarna de coin-ID. Dit is een gecombineerde selectie, niet noodzakelijk de afzonderlijke wereldwijde top tien van beide maatstaven.
4. Neem de eerste vijf of tien. Beschikbaarheid van historische data heeft geen invloed op de rangschikking. Een geselecteerde coin zonder ondersteunde markt of voldoende data blijft als fout staan; er komt geen gunstiger vervanger voor in de plaats.

Een lokaal versleutelde CoinGecko-sleutel wordt gebruikt als die aanwezig is. Zonder sleutel wordt de publieke marktgegevensroute geprobeerd. Bij onbereikbaarheid volgt een zichtbare fout; er is geen verzonnen vaste top. De bronsnapshot wordt maximaal tien minuten gecachet. Het oorspronkelijke ophaaltijdstip blijft zichtbaar.

De selectie, rule-ID, alle geldige kandidaten met scores, uitgesloten IDs met redenen, de bronvelden en bron-updatetijden worden bij het onderzoek opgeslagen. De geselecteerde coins met bedragen en rangen zijn uitklapbaar in het dashboard. De resultaat-CSV bevat ook mislukte coins. Historische marktdata blijven afzonderlijk lokaal gecachet; rapporten worden niet naar de openbare repository gepubliceerd.

## Eerlijke vergelijkbaarheid

Tot drie jaar 4-uurscandles van Binance spot in USDT. De coin-identiteiten worden via een expliciete ID/symbooltabel gekoppeld, niet door willekeurige tickers aan elkaar te plakken. Een mapping is geen garantie van actuele notering of shortbeschikbaarheid. Nieuwe coins kunnen minder historie hebben; minimaal 1.200 gesloten candles per coin is vereist. Geen recente data betekent een fout. De overblijvende beschikbare coins worden op gezamenlijke begin- en eindtijden begrensd; de feitelijke periode staat in iedere grafiek. Individuele datagaten kunnen aantallen en exacte splits nog laten verschillen. Ook een rapport waarin alle coins falen wordt bewaard, met de selectie en alle fouten.

Het betreft de **huidige** grote/liquide coins die achteraf op historische data worden getest. Dit veroorzaakt selectie- en overlevingsbias. We reconstrueren geen historische top per maand en noemen dit geen onaangeroerd bewijs. De ranglijst is geen voorspellend signaal. Gerapporteerd totaalvolume is geen geverifieerde orderboekdiepte van één beurs.

Iedere periode en ieder kostenscenario start met nieuw fictief kapitaal. Dit is geen gezamenlijke portefeuille en rendementen mogen niet worden opgeteld. Alle vier cartridges en normale/dubbele kosten blijven zichtbaar, zonder automatische winnaar. De eerdere beperkingen voor funding, echte margin en liquidaties blijven van toepassing. Paper-only, geen hefboom of live orders.
