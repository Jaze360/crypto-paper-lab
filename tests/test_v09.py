import pytest
import numpy as np
from research import auto_tune,tuning_candidates
import research,app
from market_data import demo_candles
from fastapi.testclient import TestClient


def candles():return demo_candles('solana',1500)


def test_bounded_candidates_preserve_direction_and_risk_parameters():
    p={'trade_mode':'short','stop_atr':2,'target_atr':4,'short_borrow_daily_pct':.03}
    for strategy in ('ema','rsi','breakout'):
        options=tuning_candidates(strategy,p)
        assert 1<=len(options)<=12
        assert all(x['trade_mode']=='short' and x['stop_atr']==2 and x['target_atr']==4 and x['short_borrow_daily_pct']==.03 for x in options)
        assert len({str(x) for x in options})==len(options)


def fake_run(df,strategy,capital,fee,slip,left,right,p):
    return {'metrics':{'trades':40 if left==0 else 10,'return_pct':2.,'max_drawdown_pct':.5}}


def test_final_prices_cannot_change_choice_and_choice_precedes_final_runs(monkeypatch):
    calls=[]
    def record(*args):
        calls.append((args[5],args[6]));return fake_run(*args)
    monkeypatch.setattr(research,'run',record)
    d=candles();a=auto_tune(d,'rsi',10000,.001,.0005)
    assert a['selected']['id']==1 and a['shortlist_ids']==[1,2,3]
    assert len(a['trials'])<=12
    hold=a['split']['final_start']
    first_final=next(i for i,c in enumerate(calls) if c[0]==hold)
    assert all(left>=hold for left,right in calls[first_final:])
    later=d.copy();later.loc[hold:,'close']*=3
    b=auto_tune(later,'rsi',10000,.001,.0005)
    assert a['selected']['parameters']==b['selected']['parameters']


def test_failed_training_yields_no_proposal_or_fake_validation(monkeypatch):
    def fail(*args):
        r=fake_run(*args);r['metrics']['return_pct']=-1;return r
    monkeypatch.setattr(research,'run',fail)
    r=auto_tune(candles(),'ema',10000,.001,.0005)
    assert r['selected'] is None and r['shortlist_ids']==[]
    assert all(t['reasons'] and t['validation'] is None for t in r['trials'])


def test_validation_cost_failure_rejects_all_candidates(monkeypatch):
    def fail(*args):
        r=fake_run(*args)
        if 0<args[5]<1200 and args[3]>.001:r['metrics']['return_pct']=-.1
        return r
    monkeypatch.setattr(research,'run',fail)
    r=auto_tune(candles(),'ema',10000,.001,.0005)
    assert r['selected'] is None
    assert len([t for t in r['trials'] if t['validation']])==3


def test_tuning_saved_without_changing_settings(monkeypatch):
    import storage
    monkeypatch.setattr(app,'get_data',lambda p,progress=None:candles())
    monkeypatch.setattr(research,'run',fake_run)
    storage.save_settings({'coingecko_plan':'demo'})
    app._jobs['tune-test']={'status':'running'}
    app.execute_job('tune-test',app.ResearchJob(mode='tune',params={'source':'demo'}))
    state=app._jobs.pop('tune-test');assert state['status']=='done'
    r=TestClient(app.app).get('/api/runs/'+state['run_id']).json()
    assert r['kind']=='tune' and r['payload']['tuning']['selected']
    assert storage.settings()=={'coingecko_plan':'demo'}
    with pytest.raises(ValueError):auto_tune(demo_candles('bitcoin',600),'ema',10000,.001,.0005)


def test_trade_cards_receive_real_stop_target_and_entry_rule():
    from engine import PaperEngine
    e=PaperEngine(candles(),parameters={'trade_mode':'both'})
    s=e.finish()
    assert s['trades']
    for t in s['trades']:
        assert t['stop']>0 and t['target']>0
        assert 'EMA' in t['entry_reason'] and t['side'].upper() in t['entry_reason']
