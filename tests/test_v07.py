import pytest
from market_data import demo_candles
from research import bot_arena,research
from fastapi.testclient import TestClient
import app,storage


def test_arena_has_nine_fixed_profiles_and_matches_individual_research():
    df=demo_candles('bitcoin');df.attrs['volume_is_actual']=True
    params={'rsi_period':21,'trade_mode':'short'}
    a=bot_arena(df,10000,.001,.0005,params)
    assert len(a['bots'])==9
    assert len({b['id'] for b in a['bots']})==9
    assert a['base_parameters']['trade_mode']=='short'
    for direction in ('long','short','both'):
        reference=research(df,10000,.001,.0005,dict(params,trade_mode=direction))
        rows=[b for b in a['bots'] if b['direction']==direction]
        assert [b['strategy'] for b in rows]==['ema','rsi','breakout']
        for bot,original in zip(rows,reference['strategies']):
            assert bot['test']==original['test']
            assert bot['parameters']['rsi_period']==21
            assert bot['parameters']['trade_mode']==direction
            assert len(bot['folds'])==3
            sides=bot['test']['direction_breakdown']['sides'].values()
            assert bot['closed_costs']==pytest.approx(sum(x['total_costs'] for x in sides),abs=1e-5)
            if direction=='long':assert bot['test']['short_trades']==0
            if direction=='short':assert bot['test']['long_trades']==0


def test_missing_volume_keeps_all_skipped_bots_visible():
    df=demo_candles('bitcoin');df.attrs['volume_is_actual']=False
    a=bot_arena(df,10000,.001,.0005)
    assert len(a['bots'])==9
    assert len([b for b in a['bots'] if b.get('skipped')])==3
    assert all(b['strategy']=='breakout' for b in a['bots'] if b.get('skipped'))


def test_arena_background_job_persists_reopenable_profiles(monkeypatch):
    monkeypatch.setattr(app,'get_data',lambda p,progress=None:demo_candles(p.coin))
    request=app.ResearchJob(mode='arena',params={'source':'demo'})
    app._jobs['arena-test']={'status':'running'}
    app.execute_job('arena-test',request)
    state=app._jobs.pop('arena-test')
    assert state['status']=='done'
    client=TestClient(app.app)
    r=client.get('/api/runs/'+str(state['run_id']))
    assert r.status_code==200
    row=r.json();assert row['kind']=='arena'
    assert len(row['payload']['arena']['bots'])==9
    assert row['payload']['params']['source']=='demo'
    assert 'api_key' not in row['payload']['params']
