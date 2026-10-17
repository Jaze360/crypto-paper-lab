"""One cartridge, three years of closed hourly data. No user-tuned test settings."""
import hashlib
from pathlib import Path
import pandas as pd
from cartridges import get_cartridge,manifest
from strategies import StrategyConfig
from engine import PaperEngine
from market_data import HistoricalProvider,DataError
from universe import snapshot

PLAN_ID='cartridge-hourly-3y-v1'
YEARS=3
INTERVAL=60
CAPITAL=10000.
FEE=.001
SLIP=.0005

def fixed_plan(cartridge,cutoff=None):
    c=get_cartridge(cartridge)
    end=pd.Timestamp.now(tz='UTC').floor('h') if cutoff is None else pd.Timestamp(cutoff)
    if end.tzinfo is None or end!=end.floor('h') or end>pd.Timestamp.now(tz='UTC').floor('h'):
        raise DataError('Ongeldige testgrens.')
    end=end.tz_convert('UTC');start=end-pd.DateOffset(years=YEARS);days=(end-start).days
    parameters=StrategyConfig(trade_mode='both').model_dump()
    parameters.update(dict(c.fixed))
    plan={'id':PLAN_ID,'cartridge':manifest(cartridge),'parameters':parameters,'days':days,'interval_minutes':INTERVAL,
            'from':start.isoformat(),'until_exclusive':end.isoformat(),'expected_candles':days*24,
            'capital':CAPITAL,'fee_pct':FEE*100,'slippage_pct':SLIP*100,'short_borrow_daily_pct':.02,
            'source':'Binance SPOT OHLCV in USDT','directions':{'long':'LONG / cash','short':'SHORT / cash','both':'LONG + SHORT'}[parameters['trade_mode']],'universe_size':10,
            'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if c.long_reference:plan['long_reference']=manifest(c.long_reference)
    return plan

def prepare(candles,plan):
    if not candles.attrs.get('volume_is_actual'):raise DataError('Echt candlevolume ontbreekt.')
    start=pd.Timestamp(plan['from']);end=pd.Timestamp(plan['until_exclusive'])
    d=candles[(candles.time>=start)&(candles.time<end)].reset_index(drop=True)
    expected=pd.date_range(start=start,end=end,inclusive='left',freq='h')
    actual=pd.DatetimeIndex(d.time)
    if not actual.equals(expected):
        missing=len(expected.difference(actual))
        raise DataError(f'Geen volledige drie jaar uurdata: {len(d):,} van {len(expected):,} candles; {missing:,} ontbrekend. Geen kortere vervangtest.')
    if len(d)!=plan['expected_candles']:raise DataError('Candleaantal wijkt af van het vaste testplan.')
    d.attrs.update(candles.attrs)
    return d

def evaluate(df,plan,progress=None):
    strategy=plan['cartridge']['id'];n=len(df);p=plan['parameters']
    def run(left,right,stress=False):
        params=dict(p)
        if stress:params['short_borrow_daily_pct']=min(1,params['short_borrow_daily_pct']*2)
        return PaperEngine(df,strategy,CAPITAL,FEE*(2 if stress else 1),SLIP*(2 if stress else 1),
                           start=left,end=right,parameters=params).finish(record=False)['metrics']
    if progress:progress('Drie jaar doorrekenen')
    full=run(0,n);stress=run(0,n,True);periods=[]
    bounds=[round(n*i/3) for i in range(4)]
    for i,(left,right) in enumerate(zip(bounds,bounds[1:]),1):
        if progress:progress('Controleperiode '+str(i)+'/3')
        periods.append({'label':'Periode '+str(i),'from':df.iloc[left].time.isoformat(),'to':df.iloc[right-1].time.isoformat(),
                        'metrics':run(left,right),'stress':run(left,right,True)})
    checks={'positive_full':full['return_pct']>0,'positive_stress':stress['return_pct']>0,
            'enough_trades':full['trades']>=30,
            'all_periods_positive':all(x['metrics']['return_pct']>0 and x['stress']['return_pct']>0 for x in periods),
            'period_sample':all(x['metrics']['trades']>=5 and x['stress']['trades']>=5 for x in periods),
            'risk_stop_not_hit':not full['loss_analysis']['first_risk_lock'] and not stress['loss_analysis']['first_risk_lock']}
    consistent=all(checks.values())
    reason=('Verder paper-onderzoek' if consistent else 'Risicostop bereikt' if not checks['risk_stop_not_hit'] else 'Negatief na kosten' if not checks['positive_full'] else
            'Verdwijnt bij dubbele kosten' if not checks['positive_stress'] else 'Te weinig trades' if not checks['enough_trades'] else
            'Risicostop bereikt' if not checks['risk_stop_not_hit'] else 'Niet stabiel over perioden' if not checks['all_periods_positive'] else 'Weinig trades per periode')
    result={'metrics':full,'stress':stress,'periods':periods,'consistent':consistent,'checks':checks,'assessment':reason,
            'candles':n,'from':df.iloc[0].time.isoformat(),'to':df.iloc[-1].time.isoformat(),
            'data_sha256':hashlib.sha256(df[['time','open','high','low','close','volume']].to_json(orient='records',date_format='iso',date_unit='ms').encode()).hexdigest()}
    if plan.get('long_reference'):
        if progress:progress('Afzonderlijke oorspronkelijke LONG-referentie doorrekenen')
        reference=fixed_plan(plan['long_reference']['id'],plan['until_exclusive'])
        result['long_reference']=evaluate(df,reference)
    return result

def run_test(cartridge,progress=None,*,cutoff=None,universe=None,fetch=None):
    plan=fixed_plan(cartridge,cutoff)
    if progress:progress('Top tien volgens marketcap en volume ophalen')
    universe=snapshot(10) if universe is None else universe
    if universe.get('size')!=10 or len(universe.get('selected',[]))!=10:raise DataError('Het vaste plan vereist tien geselecteerde coins.')
    results=[];provider=HistoricalProvider();fetch=fetch or provider.candles
    end_ms=int(pd.Timestamp(plan['until_exclusive']).timestamp()*1000)-1
    for i,coin in enumerate(universe['selected'],1):
        def report(text):
            if progress:progress(f'{i}/10 · {coin["name"]}: {text}')
        try:
            report('Uurdata laden')
            df=prepare(fetch(coin['id'],plan['days'],INTERVAL,report,end_ms=end_ms),plan)
            result=evaluate(df,plan,report)
            results.append({'coin':coin['id'],'name':coin['name'],'symbol':coin['symbol'],**result})
        except (ValueError,DataError) as exc:
            results.append({'coin':coin['id'],'name':coin['name'],'symbol':coin['symbol'],'error':str(exc)})
    valid=[x for x in results if not x.get('error')];consistent=sum(x['consistent'] for x in valid)
    return {'plan':plan,'universe':universe,'results':results,
            'summary':{'tested':len(valid),'selected':10,'positive':sum(x['metrics']['return_pct']>0 for x in valid),
                       'stress_positive':sum(x['stress']['return_pct']>0 for x in valid),'consistent':consistent,
                       'assessment':'Kandidaat voor nieuw paper-onderzoek' if len(valid)>=5 and consistent>=7 else
                                    'Geen volledige tests beschikbaar' if not valid else 'Nog geen overtuigend voordeel'},
            'notes':['Eén cartridge met vaste regels. Geen parameterzoektocht of automatische winnaarselectie.',
                     'Drie kalenderjaren aan gesloten uurcandles; iedere coin krijgt dezelfde begin- en eindtijd, inclusief schrikkeldagen. Ontbrekende uren worden niet opgevuld.',
                     'Per coin een afzonderlijk fictief account; percentages zijn geen gezamenlijke portefeuille.',
                     'Controle gebruikt drie gescheiden perioden van elk een derde. Iedere periode herstart kapitaal en posities; eerdere candles warmen indicatoren op. Perioderendementen niet optellen.',
                     'Verder paper-onderzoek vereist positief volledig resultaat en kostenstress, minimaal 30 trades, alle drie controleperioden positief bij beide kostenmodellen met minstens vijf trades per periode, en geen permanente risicostop in de volledige tests. Deze drempels bewijzen geen betrouwbaarheid.',
                     'Samenvatting vraagt minimaal vijf volledige coins en minstens zeven van de tien geselecteerde coins door de controle. Een ontbrekende coin telt niet als succes.',
                     'De huidige top tien is geen historische top per testdatum: selectie- en overlevingsbias. Bekende historische markten zijn geen ongezien toekomstbewijs.',
                     'Spotprijzen, 100% shortonderpand en een vaste leenproxy; echte perpetual-funding, liquidaties en beursuitvoering ontbreken. Geen hefboom of live orders.']}
