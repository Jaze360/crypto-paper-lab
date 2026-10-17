import numpy as np
import pandas as pd
import pytest
from engine import PaperEngine
from research import filter_experiment
from strategies import add_indicators,StrategyConfig
from market_data import demo_candles
import app
from fastapi.testclient import TestClient


def trending(n=700):
    close=np.linspace(100,200,n)
    d=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=n,freq='h',tz='UTC'),'open':close,'high':close+.2,'low':close-.2,'close':close,'volume':100.})
    d.attrs['volume_is_actual']=True
    return d


def forced(side='long',cooldown=0,trend=False):
    e=PaperEngine(trending(),start=230,end=260,fee=0,slip=0,parameters={'trade_mode':side,'cooldown_bars':cooldown,'trend_filter':trend})
    e.entry_signals[:]=side=='long';e.short_entry_signals[:]=side=='short'
    e.exit_signals[:]=True;e.short_exit_signals[:]=True
    return e


def test_cooldown_skips_twelve_full_candles_after_exit():
    e=forced(cooldown=12);s=e.finish()
    assert e.trades[0]['exit_time']==e.rows[231].time.isoformat()
    assert e.trades[1]['entry_time']==e.rows[244].time.isoformat()
    assert s['metrics']['loss_analysis']['risk_counts']['blocked_cooldown']>0
    assert len(e.trades)<len(forced().finish()['trades'])


def test_trend_only_uses_previous_closed_candle_and_has_warmup():
    e=forced('short',trend=True);s=e.finish()
    assert s['metrics']['trades']==0
    assert s['metrics']['loss_analysis']['risk_counts']['blocked_trend']==30
    assert forced('long',trend=True).finish()['metrics']['trades']>0
    d=trending();later=d.copy();later.loc[500:,'close']*=4
    a=add_indicators(d);b=add_indicators(later)
    assert np.allclose(a.trend_ema[:500],b.trend_ema[:500],equal_nan=True)
    assert np.isnan(a.trend_slope.iloc[218]) and np.isfinite(a.trend_slope.iloc[219])
    e=PaperEngine(d,start=50,end=60,parameters={'trend_filter':True});e.entry_signals[:]=True
    assert e.finish()['metrics']['trades']==0


@pytest.mark.parametrize('mode',['long','short','both'])
def test_cost_and_account_reconciliation_including_open_positions(mode):
    e=PaperEngine(trending(),start=230,end=270,parameters={'trade_mode':mode})
    e.entry_signals[:]=mode!='short';e.short_entry_signals[:]=mode=='short'
    e.step(1);s=e.snapshot();d=s['metrics']['loss_analysis']
    assert abs(d['account_pnl']-d['closed_net']-d['open_net_marked'])<.001
    s=e.finish();d=s['metrics']['loss_analysis']
    assert d['open_net_marked']==0
    assert abs(d['closed_gross_before_costs']-d['closed_total_costs']-d['closed_net'])<.002
    assert abs(d['reconciliation_gap'])<.002


def test_gap_records_first_risk_stop_and_counts_blocked_signals():
    d=trending();d.loc[1,['open','high','low','close']]=[40,41,39,40]
    e=PaperEngine(d,end=4,fee=0,slip=0);e._entry(0,d.iloc[0].time.isoformat(),100,.001)
    e.idx=1;e.entry_signals[:]=True;e.step(2)
    a=e.snapshot()['metrics']['loss_analysis']
    assert a['first_risk_lock']['time']==d.iloc[1].time.isoformat()
    assert a['risk_counts']['blocked_permanent']>=1
    assert a['risk_counts']['permanent_block_bars']==2
    assert a['stop_trades']==1


def test_experiment_fixed_variants_disjoint_windows_and_no_input_mutation():
    params={'trade_mode':'both','trend_filter':True,'cooldown_bars':50}
    r=filter_experiment(trending(),'ema',10000,.001,.0005,params)
    assert params['cooldown_bars']==50
    assert [(v['parameters']['trend_filter'],v['parameters']['cooldown_bars']) for v in r['variants']]==[(False,0),(False,12),(True,12)]
    for v in r['variants']:
        periods=v['periods'];assert len(periods)==5
        assert all(a['end']==b['start'] for a,b in zip(periods,periods[1:]))
        assert periods[-1]['start']==560 and periods[-1]['end']==700
        assert all('loss_analysis' in p['stress'] for p in periods)
    with pytest.raises(ValueError):filter_experiment(trending(500),'ema',10000,.001,.0005)


def test_filter_job_is_saved_and_reopenable(monkeypatch):
    monkeypatch.setattr(app,'get_data',lambda p,progress=None:trending())
    app._jobs['filters-test']={'status':'running'}
    app.execute_job('filters-test',app.ResearchJob(mode='filters',params={'source':'demo'}))
    state=app._jobs.pop('filters-test');assert state['status']=='done'
    r=TestClient(app.app).get('/api/runs/'+state['run_id']).json()
    assert r['kind']=='filters' and len(r['payload']['filters']['variants'])==3


def test_default_filters_leave_existing_signal_execution_unchanged():
    d=demo_candles('bitcoin')
    a=PaperEngine(d,parameters={}).finish();b=PaperEngine(d,parameters={'trend_filter':False,'cooldown_bars':0}).finish()
    assert a==b
    with pytest.raises(ValueError):StrategyConfig(cooldown_bars=-1)
