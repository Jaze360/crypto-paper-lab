import numpy as np,pandas as pd,pytest
from fastapi.testclient import TestClient
from engine import PaperEngine
from cartridges import PRIMARY_IDS,catalog
from slow_features import completed_days
import simple_lab,app

def test_replacements_and_kept_cartridges():
    assert PRIMARY_IDS==('momentum63_both','donchian55_both','supertrend','keltner','aroon','kama')
    items={c['id']:c for c in catalog()}
    assert not items['bollinger']['primary'] and not items['failed_breakout']['primary']
    assert items['supertrend']['version']==items['keltner']['version']=='1.0.0'
    assert items['aroon']['primary'] and items['kama']['primary']
    assert TestClient(app.app).post('/api/lab/start',json={'cartridge':'aroon','risk_per_trade':.01}).status_code==422

def test_aroon_exact_window_and_recent_ties():
    from test_v014 import hours
    d=hours();e=PaperEngine(d,'aroon');at=26*24-1
    assert e.d.aroon_up.iloc[at]==100 and e.d.aroon_down.iloc[at]==0
    assert e.entry_signals[at] and not e.entry_signals[:at].any()
    # Tie at the current day's high must count as zero days ago.
    d.loc[:26*24-1,'high']=200
    q=PaperEngine(d,'aroon');assert q.d.aroon_up.iloc[at]==100
    changed=d.copy();changed.loc[at,'high']=1000
    z=PaperEngine(changed,'aroon')
    assert np.allclose(q.d.aroon_up[:at],z.d.aroon_up[:at],equal_nan=True)

def test_kama_initialization_smoothing_and_flat_series():
    from test_v014 import hours
    d=hours();e=PaperEngine(d,'kama');daily=completed_days(d)
    initial=daily.close.iloc[:10].mean()
    assert e.d.kama.iloc[10*24-1]==pytest.approx(initial)
    assert e.d.kama_er.iloc[11*24-1]==pytest.approx(1)
    assert e.d.kama.iloc[11*24-1]==pytest.approx(initial+(4/9)*(daily.close.iloc[10]-initial))
    flat=d.copy();flat[['open','high','low','close']]=100.
    f=PaperEngine(flat,'kama')
    assert f.d.kama.dropna().eq(100).all() and f.d.kama_er.dropna().eq(0).all()
    assert not f.entry_signals.any() and not f.short_entry_signals.any()

@pytest.mark.parametrize('side',['long','short'])
def test_risk_sizes_real_positions_without_moving_stops_or_caps(side):
    from test_v014 import hours
    positions=[]
    for risk in [.0025,.005,.01]:
        e=PaperEngine(hours(),'supertrend',risk_per_trade=risk)
        e._entry(1000,e.rows[1000].time.isoformat(),100,10,side)
        p=e.position;assert p and p.planned_risk<=10000*risk+1e-6
        assert p.entry*p.qty<=2500 and e.cash>=0
        positions.append(p)
    assert positions[1].qty==pytest.approx(positions[0].qty*2,abs=1e-7)
    assert positions[2].qty==pytest.approx(positions[0].qty*4,abs=1e-7)
    assert len({p.stop for p in positions})==len({p.target for p in positions})==1
    if side=='short':assert positions[2].collateral==pytest.approx(positions[2].entry*positions[2].qty)
    for risk in [.0025,.005,.01]:
        e=PaperEngine(hours(),'supertrend',risk_per_trade=risk)
        e._entry(1000,e.rows[1000].time.isoformat(),100,.1,side)
        assert e.position.entry*e.position.qty*(1+e.fee)<=2500+1e-6

@pytest.mark.parametrize('bad',[True,0,-.1,.02,.001,float('nan'),float('inf'),'0.01'])
def test_risk_scenarios_are_bounded(bad):
    from test_v014 import hours
    with pytest.raises(ValueError,match='risicoscenario'):PaperEngine(hours(),'supertrend',risk_per_trade=bad)

def test_risk_comparison_reuses_base_and_recomputes_full_stress_only(monkeypatch):
    from test_v014 import hours
    calls=[]
    class Engine:
        def __init__(self,df,strategy,capital,fee,slip,start,end,parameters,**kw):
            calls.append((fee,slip,start,end,parameters,kw));self.risk=kw.get('risk_per_trade',.0025)
        def finish(self,record):return {'metrics':{'return_pct':self.risk*100,'trades':40,'loss_analysis':{'first_risk_lock':None}}}
    monkeypatch.setattr(simple_lab,'PaperEngine',Engine)
    r=simple_lab.evaluate(hours(),simple_lab.fixed_plan('aroon','2026-01-01T00:00:00Z'),compare_risk=True)
    assert len(calls)==12 and [s['risk_per_trade_pct'] for s in r['risk_scenarios']]==[.25,.5,1.]
    assert r['risk_scenarios'][0]['metrics'] is r['metrics']
    assert all(c[2:4]==(0,4000) for c in calls[8:])
    assert calls[9][0:2]==(.002,.001) and calls[9][4]['short_borrow_daily_pct']==.04
    assert [c[-1]['risk_per_trade'] for c in calls[8:]]==[.005,.005,.01,.01]
    assert len(r['periods'])==3 and r['consistent']

def test_higher_risk_does_not_disable_permanent_or_daily_blocks():
    from test_v014 import hours
    e=PaperEngine(hours(),'supertrend',risk_per_trade=.01)
    e.cash=8900;e.update_risk(100)
    assert e.locked and e.first_risk_lock['reason']=='10% drawdown bereikt'
    e=PaperEngine(hours(),'supertrend',risk_per_trade=.01);i=1200;e.idx=i
    e.current_day=str(e.rows[i].time.date());e.start_day_equity=10000;e.cash=9899
    e.entry_signals[i-1]=True;e.short_entry_signals[i-1]=False;e.step(1)
    assert e.position is None and e.risk_counts['blocked_daily']==1

def test_updater_requires_both_new_modules():
    import updater
    from test_v02 import archive
    files={'version.json':b'{"version":"0.16.0","paper_only":true}'}
    for name in ['simple_lab.py','protocol.py','universe.py','cartridges.py','cartridge_api.py','cartridge_ema.py','cartridge_rsi.py','cartridge_breakout.py','cartridge_pullback.py','static/lab.html','static/lab.js','static/lab.css','slow_features.py','cartridge_momentum63.py','cartridge_donchian55.py','cartridge_slow_both.py','cartridge_supertrend.py','cartridge_bollinger.py','cartridge_keltner.py','cartridge_failed_breakout.py']:files[name]=b'#fixture'
    with pytest.raises(ValueError,match='Aroon/KAMA'):updater.archive_files(archive(files))
    for name in ['cartridge_aroon.py','cartridge_kama.py']:files[name]=b'#fixture'
    assert 'cartridge_kama.py' in updater.archive_files(archive(files))
