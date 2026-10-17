import pandas as pd,numpy as np,pytest
from fastapi.testclient import TestClient
import app,simple_lab,storage
from market_data import DataError,HistoricalProvider

def frame(plan):
    times=pd.date_range(plan['from'],periods=plan['expected_candles'],freq='h')
    d=pd.DataFrame({'time':times,'open':100.,'high':102.,'low':98.,'close':100.,'volume':100.})
    d.attrs.update(volume_is_actual=True,quote='USDT');return d

def universe():
    return {'size':10,'selected':[{'id':'coin-'+str(i),'name':'Coin '+str(i),'symbol':'C'+str(i)} for i in range(10)]}

def test_plan_is_frozen_and_cartridge_fixed_rules_apply():
    a=simple_lab.fixed_plan('ema','2026-01-01T00:00:00Z')
    assert a['days']==1096 and a['interval_minutes']==60 and a['expected_candles']==26304
    assert a['parameters']['trade_mode']=='both' and a['fee_pct']==.1 and a['slippage_pct']==.05
    assert a['from']=='2023-01-01T00:00:00+00:00'
    b=simple_lab.fixed_plan('pullback','2026-01-01T00:00:00Z')
    assert b['parameters']['ema_fast']==20 and b['parameters']['max_holding_bars']==30
    with pytest.raises(DataError):simple_lab.fixed_plan('ema','2026-01-01T00:30:00Z')

def test_hourly_data_cannot_silently_be_shorter_or_have_gaps():
    p=simple_lab.fixed_plan('ema','2026-01-01T00:00:00Z');d=frame(p)
    assert len(simple_lab.prepare(d,p))==26304
    for altered in [d.iloc[1:],d.drop(index=2000),d.iloc[::4]]:
        with pytest.raises(DataError,match='Geen volledige drie jaar'):simple_lab.prepare(altered,p)
    d.attrs['volume_is_actual']=False
    with pytest.raises(DataError,match='volume'):simple_lab.prepare(d,p)

def test_only_selected_cartridge_is_run_with_stress_and_fixed_windows(monkeypatch):
    p=simple_lab.fixed_plan('rsi','2026-01-01T00:00:00Z');d=frame(p);calls=[]
    class Engine:
        def __init__(self,df,strategy,capital,fee,slip,start,end,parameters):
            calls.append((strategy,capital,fee,slip,start,end,parameters))
        def finish(self,record):
            assert record is False
            return {'metrics':{'return_pct':1.,'trades':40,'loss_analysis':{'first_risk_lock':None}}}
    monkeypatch.setattr(simple_lab,'PaperEngine',Engine)
    result=simple_lab.evaluate(d,p)
    assert len(calls)==8 and all(x[0]=='rsi' for x in calls)
    assert calls[0][4:6]==(0,26304) and calls[2][4:6]==(0,8768) and calls[-1][4:6]==(17536,26304)
    assert calls[1][2:4]==(.002,.001) and calls[1][-1]['short_borrow_daily_pct']==.04
    assert result['consistent'] and len(result['periods'])==3

def test_all_coins_get_same_pinned_cutoff_and_failures_are_kept(monkeypatch):
    cutoff='2026-01-01T00:00:00Z';p=simple_lab.fixed_plan('ema',cutoff);d=frame(p);calls=[]
    def fetch(coin,days,interval,progress,end_ms):
        calls.append((coin,days,interval,end_ms))
        if coin=='coin-1':return d.iloc[100:]
        return d
    monkeypatch.setattr(simple_lab,'evaluate',lambda *a,**kw:{'metrics':{'return_pct':1},'stress':{'return_pct':-1},'consistent':False})
    r=simple_lab.run_test('ema',cutoff=cutoff,universe=universe(),fetch=fetch)
    assert len(r['results'])==10 and r['summary']['tested']==9 and r['summary']['stress_positive']==0
    assert r['results'][1]['error'] and len({x[3] for x in calls})==1
    assert all(x[1:3]==(1096,60) for x in calls)
    assert r['summary']['assessment']=='Nog geen overtuigend voordeel'

def test_primary_api_has_only_a_cartridge_choice_and_saves_results(monkeypatch):
    monkeypatch.setattr(app,'_jobs',{})
    seen=[]
    def run(cartridge,progress):
        seen.append(cartridge);return {'plan':simple_lab.fixed_plan(cartridge),'results':[],'summary':{'tested':0}}
    monkeypatch.setattr(app,'run_cartridge_test',run)
    monkeypatch.setattr(app._pool,'submit',lambda fn,*args:fn(*args))
    client=TestClient(app.app)
    for body in [{'cartridge':'ema','interval':240},{'cartridge':'ema','days':30},{'cartridge':'missing'},{'cartridge':'../../x'}]:
        assert client.post('/api/lab/start',json=body).status_code==422
    response=client.post('/api/lab/start',json={'cartridge':'pullback'})
    assert response.status_code==200 and seen==['pullback']
    state=client.get('/api/research/jobs/'+response.json()['id']).json()
    assert state['status']=='done'
    saved=storage.get_run(state['run_id'])
    assert saved['params']['interval']==60 and saved['params']['days']==simple_lab.fixed_plan('pullback')['days'] and saved['kind']=='cartridge_test'
    assert client.get('/api/lab/runs').json()[0]['id']==saved['id']
    main=client.get('/').text
    assert '/static/lab.js' in main and 'id="testType"' not in main
    assert 'id="testType"' in client.get('/archief').text

def test_second_test_is_blocked_until_active_test_finishes(monkeypatch):
    monkeypatch.setattr(app,'_jobs',{'existing':{'status':'running'}})
    assert TestClient(app.app).post('/api/lab/start',json={'cartridge':'ema'}).status_code==409

def test_historical_provider_rejects_future_or_unaligned_cutoffs():
    for end in [int(pd.Timestamp.now(tz='UTC').timestamp()*1000)+86400000,1,True]:
        with pytest.raises(DataError,match='eindtijd'):HistoricalProvider().candles(end_ms=end)

def test_updater_requires_all_primary_screen_assets():
    import updater
    from test_v02 import archive
    version={'version.json':b'{"version":"0.13.0","paper_only":true}'}
    with pytest.raises(ValueError,match='cartridgelab'):updater.archive_files(archive(version))
    for name in ['simple_lab.py','protocol.py','universe.py','cartridges.py','cartridge_api.py','cartridge_ema.py',
                 'cartridge_rsi.py','cartridge_breakout.py','cartridge_pullback.py','static/lab.html','static/lab.js','static/lab.css']:
        version[name]=b'# test fixture'
    assert 'static/lab.html' in updater.archive_files(archive(version))
