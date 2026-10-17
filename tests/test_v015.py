import numpy as np,pandas as pd,pytest
from fastapi.testclient import TestClient
from engine import PaperEngine
from cartridges import PRIMARY_IDS,catalog,get_cartridge
import simple_lab,app

def hourly(n=8200):
    x=np.arange(n);c=200*np.exp(.00001*x+.25*np.sin(x/300))
    d=pd.DataFrame({'time':pd.date_range('2023-01-01',periods=n,freq='h',tz='UTC'),'open':np.r_[c[0],c[:-1]],'close':c,'high':c*1.004,'low':c*.996,'volume':100.})
    d['high']=d[['high','open']].max(axis=1);d['low']=d[['low','open']].min(axis=1)
    d.attrs.update(volume_is_actual=True,quote='USDT');return d

def test_exactly_six_primary_with_preserved_old_modules():
    assert {c['id'] for c in catalog() if c['primary']}==set(PRIMARY_IDS)
    assert len(PRIMARY_IDS)==6
    for strategy in ['momentum63','donchian55']:
        c=get_cartridge(strategy);assert c.version=='1.0.0' and dict(c.fixed)['trade_mode']=='long'
        extended=get_cartridge(strategy+'_both');assert extended.long_reference==strategy and extended.version=='1.1.0'
    client=TestClient(app.app)
    assert sum(c['primary'] for c in client.get('/api/cartridges').json()['cartridges'])==6
    for strategy in PRIMARY_IDS:assert client.post('/api/backtest',json={'strategy':strategy}).status_code==422

@pytest.mark.parametrize('strategy',PRIMARY_IDS)
def test_every_primary_is_causal_hourly_and_both_sides(strategy):
    d=hourly();a=PaperEngine(d,strategy);changed=d.copy();changed.loc[6003:,['open','high','low','close']]*=1.7
    b=PaperEngine(changed,strategy)
    for attribute in ['entry_signals','exit_signals','short_entry_signals','short_exit_signals']:
        assert np.array_equal(getattr(a,attribute)[:6003],getattr(b,attribute)[:6003])
    assert np.allclose(a.d.atr[:6003],b.d.atr[:6003],equal_nan=True)
    for signals in [a.entry_signals,a.short_entry_signals]:assert not (signals&~a.d.daily_decision.to_numpy()).any()
    assert a.parameters.trade_mode=='both'
    result=a.finish()
    for trade in result['trades']:assert pd.Timestamp(trade['entry_time']).hour==0
    breakdown=result['metrics']['direction_breakdown']['sides']
    assert sum(s['trades'] for s in breakdown.values())==result['metrics']['trades']
    assert sum(s['contribution_pct'] for s in breakdown.values())==pytest.approx(result['metrics']['return_pct'],abs=.001)
    if strategy!='failed_breakout':assert result['metrics']['short_trades']>0 and result['metrics']['long_trades']>0
    with pytest.raises(ValueError,match='1-uurscandles'):PaperEngine(d.iloc[::4].reset_index(drop=True),strategy)

@pytest.mark.parametrize('strategy',['momentum63','donchian55'])
def test_mirrored_shorts_keep_original_long_signals_and_reference(strategy):
    d=hourly(4000);old=PaperEngine(d,strategy);extended=PaperEngine(d,strategy+'_both')
    assert np.array_equal(old.entry_signals,extended.entry_signals)
    assert np.array_equal(old.exit_signals,extended.exit_signals)
    assert np.allclose(old.d.atr,extended.d.atr,equal_nan=True)
    plan=simple_lab.fixed_plan(strategy+'_both','2026-01-01T00:00:00Z')
    result=simple_lab.evaluate(d,plan)
    reference=simple_lab.evaluate(d,simple_lab.fixed_plan(strategy,'2026-01-01T00:00:00Z'))
    assert result['long_reference']==reference
    assert 'long_reference' not in reference
    assert plan['long_reference']['id']==strategy

@pytest.mark.parametrize('side',['long','short'])
def test_failed_breakout_has_prior_day_bounds_and_directional_filter(side):
    from test_v014 import hours
    d=hours();day=150
    if side=='short':
        for col in ['open','close','high','low']:d[col]=600-d[col]
        d[['high','low']]=d[['low','high']].to_numpy()
    before=d.iloc[(day-20)*24:day*24];low=before.low.min();high=before.high.max()
    candidate=d.copy()
    if side=='long':
        candidate.loc[day*24:(day+1)*24-1,'low']=low*.95
        candidate.loc[(day+1)*24-1,'close']=low+(high-low)*.2
    else:
        candidate.loc[day*24:(day+1)*24-1,'high']=high*1.05
        candidate.loc[(day+1)*24-1,'close']=high-(high-low)*.2
    e=PaperEngine(candidate,'failed_breakout')
    i=(day+1)*24-1
    enter=e.entry_signals if side=='long' else e.short_entry_signals
    leave=e.exit_signals if side=='long' else e.short_exit_signals
    assert enter[i] and not leave[i]
    assert not e.entry_signals[i-1] and not e.short_entry_signals[i-1]

def test_updater_requires_every_new_module():
    import updater
    from test_v02 import archive
    files={'version.json':b'{"version":"0.15.0","paper_only":true}'}
    names=['simple_lab.py','protocol.py','universe.py','cartridges.py','cartridge_api.py','cartridge_ema.py','cartridge_rsi.py','cartridge_breakout.py','cartridge_pullback.py','static/lab.html','static/lab.js','static/lab.css','slow_features.py','cartridge_momentum63.py','cartridge_donchian55.py']
    files.update({name:b'# fixture' for name in names})
    with pytest.raises(ValueError,match='LONG/SHORT'):updater.archive_files(archive(files))
    for name in ['cartridge_slow_both.py','cartridge_supertrend.py','cartridge_bollinger.py','cartridge_keltner.py','cartridge_failed_breakout.py']:files[name]=b'# fixture'
    assert 'cartridge_supertrend.py' in updater.archive_files(archive(files))
