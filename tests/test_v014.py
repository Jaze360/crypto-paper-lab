import numpy as np,pandas as pd,pytest
from engine import PaperEngine
from strategies import add_indicators
from slow_features import completed_days
from cartridges import manifest,get_cartridge

def hours(n=4000,start='2023-01-01T00:00:00Z'):
    x=np.arange(n);c=100+x*.05
    d=pd.DataFrame({'time':pd.date_range(start,periods=n,freq='h'),'open':np.r_[c[0],c[:-1]],'high':c+1,'low':c-1,'close':c,'volume':100.})
    d.attrs.update(volume_is_actual=True,quote='USDT');return d

@pytest.mark.parametrize('strategy',['momentum63','donchian55'])
def test_slow_signals_daily_atr_and_future_mutations_are_causal(strategy):
    d=hours();a=PaperEngine(d,strategy)
    future=d.copy();future.loc[3125:,['open','high','low','close']]*=2
    b=PaperEngine(future,strategy)
    assert np.array_equal(a.entry_signals[:3125],b.entry_signals[:3125])
    assert np.array_equal(a.exit_signals[:3125],b.exit_signals[:3125])
    assert np.allclose(a.d.atr[:3125],b.d.atr[:3125],equal_nan=True)
    assert a.d.atr.iloc[2500]>3 and a.parameters.trade_mode=='long'
    assert not a.short_entry_signals.any()
    assert a.parameters.stop_atr==3 and a.parameters.target_atr==8
    assert 'slow_features.py' in manifest(strategy)['code_sha256']
    assert manifest(strategy)['directions']==['long']
    r=a.finish();assert r['metrics']['short_trades']==0
    assert r['metrics']['long_trades']>0
    for t in r['trades']:
        assert pd.Timestamp(t['entry_time']).hour==0
        if strategy=='momentum63':assert pd.Timestamp(t['entry_time']).dayofweek==0

def test_warmup_has_no_extra_day_and_no_incomplete_day_lookahead():
    d=hours()
    m=PaperEngine(d,'momentum63');b=PaperEngine(d,'donchian55')
    assert m.entry_signals[64*24-1] and not m.entry_signals[:64*24-1].any()
    assert b.entry_signals[56*24-1] and not b.entry_signals[:56*24-1].any()
    assert not b.d.daily_decision.iloc[56*24-2]
    # A day starting at 17:00 in the archive is not a complete UTC day.
    partial=completed_days(hours(start='2023-01-01T17:00:00Z'))
    assert partial.index[0]==pd.Timestamp('2023-01-03T00:00:00Z')
    # The first complete day's high appears at its closing boundary, never earlier.
    first=56*24-1
    changed=d.copy();changed.loc[first,'high']*=10
    q=PaperEngine(changed,'donchian55')
    assert np.allclose(b.d.atr[:first],q.d.atr[:first],equal_nan=True)

def test_channel_excludes_the_decision_day_and_requires_hourly_data():
    d=hours();e=PaperEngine(d,'donchian55')
    at=56*24-1
    # Previous day high is at index 55*24-1; current day's extreme is excluded.
    assert e.d.channel55.iloc[at]==pytest.approx(d.high.iloc[55*24-1])
    assert e.d.channel20.iloc[at]==pytest.approx(d.low.iloc[(55-20)*24])
    with pytest.raises(ValueError,match='1-uurscandles'):PaperEngine(d.iloc[::4].reset_index(drop=True),'momentum63')

def test_daily_atr_keeps_existing_risk_budget_and_caps():
    e=PaperEngine(hours(),'momentum63');e.step(64*24+1)
    assert e.position is not None
    p=e.position;assert p.planned_risk<=10000*.0025+1e-8
    assert p.entry*p.qty<=10000*.25
    assert p.stop==pytest.approx(p.entry-3*e.rows[64*24-1].atr)
def test_updater_requires_slow_modules():
    import updater
    from test_v02 import archive
    version={'version.json':b'{"version":"0.14.0","paper_only":true}'}
    for name in ['simple_lab.py','protocol.py','universe.py','cartridges.py','cartridge_api.py','cartridge_ema.py',
                 'cartridge_rsi.py','cartridge_breakout.py','cartridge_pullback.py','static/lab.html','static/lab.js','static/lab.css']:
        version[name]=b'# test fixture'
    with pytest.raises(ValueError):updater.archive_files(archive(version))
    for name in ['slow_features.py','cartridge_momentum63.py','cartridge_donchian55.py']:version[name]=b'# fixture'
    assert 'slow_features.py' in updater.archive_files(archive(version))

