import numpy as np
import pandas as pd
import pytest
import app,protocol,research
from strategies import add_indicators,signals,short_signals,config,REFERENCE_STRATEGIES
from engine import PaperEngine
from fastapi.testclient import TestClient


def frame(n=1300):
    c=np.linspace(100,230,n)
    d=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=n,freq='4h',tz='UTC'),'open':c,'high':c+.3,'low':c-.3,'close':c,'volume':100.})
    d.attrs.update(volume_is_actual=True,quote='USDT',timeframe='240 min',source='TEST')
    return d


def test_references_do_not_expand_old_arena_or_change_rules():
    assert list(REFERENCE_STRATEGIES)==['ema','rsi','breakout']
    assert protocol.reference_params()['max_holding_bars']==0
    assert protocol.reference_params()['trade_mode']=='both'
    for strategy in REFERENCE_STRATEGIES:
        a=PaperEngine(frame(),strategy,parameters={}).finish()
        p=protocol.reference_params();p['trade_mode']='long'
        b=PaperEngine(frame(),strategy,parameters=p).finish()
        assert a['trades']==b['trades'] and a['equity']==b['equity']


def test_pullback_is_frozen_and_signals_use_only_history():
    d=frame();d.loc[500,'close']-=7;d.loc[500,'low']=d.loc[500,'close']-.3
    p=protocol.hypothesis_params();ind=add_indicators(d,p);enter,_=signals(ind,'pullback')
    assert enter[501]
    future=d.copy();future.loc[700:,'close']*=2
    b,_=signals(add_indicators(future,p),'pullback')
    assert np.array_equal(enter[:700],b[:700])
    assert not enter[:220].any()
    e=PaperEngine(d,'pullback',parameters={'ema_fast':3,'stop_atr':.5,'max_holding_bars':1})
    assert e.parameters.ema_fast==20 and e.parameters.ema_slow==50
    assert e.parameters.stop_atr==2.5 and e.parameters.max_holding_bars==30
    with pytest.raises(ValueError):research.tuning_candidates('pullback')


def test_pullback_short_is_mirrored():
    d=frame();c=np.linspace(230,100,len(d));d['open']=c;d['close']=c;d['high']=c+.3;d['low']=c-.3
    d.loc[500,'close']+=7;d.loc[500,'high']=d.loc[500,'close']+.3
    e,_=short_signals(add_indicators(d,protocol.hypothesis_params()),'pullback')
    assert e[501] and not e[:220].any()


def test_maximum_duration_exits_on_open_after_thirty_active_candles():
    e=PaperEngine(frame(),'pullback',start=300,end=335,fee=0,slip=0)
    e.entry_signals[:]=False;e.short_entry_signals[:]=False;e.exit_signals[:]=False
    e.short_exit_signals[:]=False;e.entry_signals[299]=True
    e.step(1)
    e.position.stop=1.;e.position.target=1000.
    e.step(30)
    assert e.trades[0]['reason']=='Maximale positieduur'
    assert e.trades[0]['holding_bars']==30
    assert e.trades[0]['exit_time']==e.rows[330].time.isoformat()


def test_protocol_reports_all_periods_and_scenarios_with_fingerprints(monkeypatch):
    calls=[]
    def fake(df,strategy,capital,fee,slip,left,right,p):
        calls.append((strategy,left,right,dict(p)))
        return {'metrics':{'trades':0,'return_pct':0,'max_drawdown_pct':0}}
    monkeypatch.setattr(protocol,'run',fake)
    r=protocol.protocol_coin(frame(),10000,.1,.05)
    assert len(r['rows'])==48
    assert len(r['data_sha256'])==64
    assert all(len(x)==64 for x in r['code_sha256'].values())
    assert {x['strategy'] for x in r['rows']}=={'ema','rsi','breakout','pullback'}
    assert len(calls)==96
    for strategy in ['ema','rsi','breakout','pullback']:
        for scenario in ['huidig','fee0.05','fee0.04']:
            rows=[x for x in r['rows'] if x['strategy']==strategy and x['scenario']==scenario]
            assert [x['period'] for x in rows]==[0,1,2,3]
    assert 'funding' in ' '.join(r['costs']['limits']).lower()
    bad=frame();bad.attrs['volume_is_actual']=False
    with pytest.raises(ValueError):protocol.protocol_coin(bad,10000,.1,.05)
    bad=frame();bad['time']=pd.date_range('2024-01-01',periods=len(bad),freq='h',tz='UTC')
    with pytest.raises(ValueError):protocol.protocol_coin(bad,10000,.1,.05)


def test_protocol_background_preserves_failures_and_fixed_cohort(monkeypatch):
    def data(p,progress=None):
        if p.coin=='ethereum':raise ValueError('Bewuste onbeschikbare markt')
        assert p.days==1095 and p.interval==240 and p.source=='historical'
        return frame()
    monkeypatch.setattr(app,'get_data',data)
    monkeypatch.setattr(app,'protocol_coin',lambda *a,**k:{'protocol':protocol.PROTOCOL_ID,'rows':[],'notes':[]})
    app._jobs['protocol-test']={'status':'running'}
    app.execute_job('protocol-test',app.ResearchJob(mode='protocol',params={'source':'demo','days':30}))
    state=app._jobs.pop('protocol-test');assert state['status']=='done'
    r=TestClient(app.app).get('/api/runs/'+state['run_id']).json()
    assert r['kind']=='protocol' and r['params']['interval']==240
    assert [x['coin'] for x in r['payload']['protocol_batch']]==list(protocol.COHORT)
    assert 'error' in r['payload']['protocol_batch'][1]
