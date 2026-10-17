"""Current cap/volume snapshot, never a claim of a point-in-time historical universe."""
import math,re
from datetime import datetime,timezone
import requests
from market_data import CoinGeckoProvider,DataError,BINANCE_SYMBOLS
from storage import cache_get,cache_put

RULE='cap-volume-rank-sum-v1'
def select(markets,stablecoins,size=10):
    if size not in (5,10):raise DataError('Kies vijf of tien coins.')
    if not isinstance(markets,list) or not isinstance(stablecoins,list) or not stablecoins:raise DataError('Ranglijst of stablecoinclassificatie ontbreekt of heeft een ongeldig formaat.')
    stable={x.get('id') for x in stablecoins if isinstance(x,dict)}
    rows=[];excluded=[];seen=set()
    for x in markets:
        if not isinstance(x,dict):continue
        ident=x.get('id','');name=x.get('name','');symbol=x.get('symbol','')
        if not isinstance(ident,str) or not re.fullmatch('[a-z0-9-]{1,80}',ident) or ident in seen:continue
        seen.add(ident)
        reason=''
        if ident in stable:reason='Stablecoin (CoinGecko-categorie)'
        elif re.search(r'\b(wrapped|bridged|staked|restaked)\b',str(name),re.I) or ident in {'weth','rocket-pool-eth','lido-staked-ether','wrapped-steth'}:reason='Verpakte/gestakete variant'
        values=[x.get('market_cap'),x.get('total_volume')]
        if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>0 for v in values):reason=reason or 'Marktkapitalisatie/volume ontbreekt'
        row={'id':ident,'name':str(name),'symbol':str(symbol).upper(),'market_cap_usd':values[0],
             'volume_24h_usd':values[1],'market_cap_rank_global':x.get('market_cap_rank'),'source_updated':x.get('last_updated')}
        if reason:excluded.append({'id':ident,'reason':reason});continue
        rows.append(row)
    for field,rank in [('market_cap_usd','cap_rank'),('volume_24h_usd','volume_rank')]:
        for i,row in enumerate(sorted(rows,key=lambda x:(-x[field],x['id'])),1):row[rank]=i
    for row in rows:
        row['score']=row['cap_rank']+row['volume_rank']
        row['historical_symbol']=BINANCE_SYMBOLS.get(row['id'])
    ranked=sorted(rows,key=lambda x:(x['score'],x['cap_rank'],x['id']))
    if len(ranked)<size:raise DataError('Te weinig geldige coins om de gekozen top te vullen; geen vaste vervanglijst gebruikt.')
    return {'rule':RULE,'size':size,'selected':ranked[:size],'ranked_candidates':ranked,'excluded':excluded,
            'source':'CoinGecko /coins/markets, eerste 100 op market_cap_desc; USD',
            'rule_text':'Na uitsluitingen: rang marktkapitalisatie + rang 24u-volume, beide even zwaar. Laagste som eerst; gelijke som kiest hoogste marketcap.',
            'limits':['Huidige selectie toegepast op historische candles: selectiebias en overlevingsbias; geen historische top per testdatum.',
                      'Volume is gemeld totaalvolume over beurzen, geen geverifieerde orderboekdiepte of shortbeschikbaarheid.',
                      'Niet-ondersteunde of mislukte coins blijven staan zonder vervanging. Stablecategorie en naamfilter zijn afhankelijk van de bronclassificatie.',
                      'Een recent genoteerde coin kan de gezamenlijke testperiode inkorten. Gaten en te korte perioden blijven expliciet zichtbaar.']}

def snapshot(size=10):
    if size not in (5,10):raise DataError('Kies vijf of tien coins.')
    raw=cache_get('universe-markets-v1',ttl=600)
    if raw is None:
        provider=CoinGeckoProvider()
        def get(params):
            if provider.key:return provider._get('/coins/markets',params)
            try:
                r=requests.get('https://api.coingecko.com/api/v3/coins/markets',params=params,timeout=20,
                               headers={'Accept':'application/json','User-Agent':'CryptoPaperLab/0.12'})
                r.raise_for_status();value=r.json()
                if not isinstance(value,list):raise ValueError('Ongeldige ranglijst')
                return value
            except (requests.RequestException,ValueError) as exc:
                raise DataError('Actuele ranglijst niet bereikbaar. Probeer later of stel je CoinGecko-sleutel lokaal in; geen verzonnen top gebruikt.') from exc
        params={'vs_currency':'usd','order':'market_cap_desc','per_page':100,'page':1,'sparkline':'false'}
        markets=get(params);stable=get(dict(params,category='stablecoins',per_page=250))
        # Validate before caching; no credentials are included.
        select(markets,stable,size)
        raw={'markets':markets,'stablecoins':stable,'fetched_at':datetime.now(timezone.utc).isoformat()}
        cache_put('universe-markets-v1',raw)
    return dict(select(raw['markets'],raw['stablecoins'],size),fetched_at=raw['fetched_at'],cache_max_age_seconds=600)
