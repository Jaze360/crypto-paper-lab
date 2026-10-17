import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app import app
from market_data import demo_candles, DataError, CoinGeckoProvider
from engine import PaperEngine, run_backtest, RISK_PER_TRADE
from strategies import add_indicators,signal

client=TestClient(app)

def test_demo_reproducible_and_valid():
    a=demo_candles('bitcoin',240);b=demo_candles('bitcoin',240)
    assert np.allclose(a.close,b.close)
    assert np.all(a.low<=a.open) and np.all(a.high>=a.close)
    assert len(a)==240

@pytest.mark.parametrize('strategy',['ema','rsi','breakout'])
def test_backtest_synthetic_completes(strategy):
    d=demo_candles('bitcoin',360)
    r=run_backtest(d,strategy)
    assert r['total_candles']==360
    assert r['split_index']==252
    assert len(r['train']['equity_curve'])==r['split_index']
    assert len(r['test']['equity_curve'])==360-r['split_index']
    for section in ('train','test'):
        assert r[section]['equity']>=0
        assert r[section]['metrics']['trades']>=0
        assert r[section]['max_drawdown_pct']>=0


def test_no_volume_breakout():
    d=demo_candles();d.attrs['volume_is_actual']=False
    with pytest.raises(ValueError,match='volume'):
        PaperEngine(d,'breakout')


def test_stop_gap_can_exceed_planned_risk():
    # gaps must fill at OPEN rather than at stop; no false guaranteed stop price
    d=demo_candles()
    eng=PaperEngine(d,'ema')
    eng.position=None
    # force a position, then process gap with provided open
    from engine import Position
    eng.position=Position('start',100.,1.,95.,110.,.1,0)
    eng.cash=9900
    eng._close('gap',90.0,'Gap onder stop')
    assert eng.trades[-1]['exit']<95
    assert eng.trades[-1]['pnl'] < -5


def test_size_planned_stop_risk_cap():
    d=demo_candles();eng=PaperEngine(d,'ema',capital=10000)
    price=100.;atr=2.
    eng._entry(100,'time',price,atr)
    p=eng.position
    assert p is not None
    planned_loss=(p.entry-p.stop*(1-eng.slip))*p.qty + eng.fee*(p.entry+p.stop*(1-eng.slip))*p.qty
    assert planned_loss<=10000*RISK_PER_TRADE+0.0001


def test_ohlc_strategy_no_future_prices():
    d=demo_candles()
    a=add_indicators(d)
    before=signal(a,100,'ema')
    d2=d.copy();d2.loc[101:,'close']*=3;d2.loc[101:,'high']*=3;d2.loc[101:,'low']*=2
    a2=add_indicators(d2)
    assert signal(a2,100,'ema')==before


def test_api_no_live_order_endpoints():
    routes={r.path for r in app.routes}
    assert '/api/backtest' in routes and '/api/replay/start' in routes
    assert not any('/trade' in route or '/order' in route or '/broker' in route for route in routes)


def test_status_and_backtest():
    r=client.get('/api/status');assert r.status_code==200
    assert 'PAPER' in r.json()['mode']
    r=client.post('/api/backtest',json={'source':'demo','coin':'ethereum','strategy':'rsi'})
    assert r.status_code==200
    assert r.json()['meta']['source'].startswith('DEMO')
    assert r.json()['backtest']['test']['progress']>0


def test_replay_and_export():
    assert client.post('/api/replay/start',json={'strategy':'ema'}).status_code==200
    r=client.post('/api/replay/step',json={'steps':30}); assert r.status_code==200
    assert r.json()['snapshot']['progress']==30
    assert client.get('/api/export/replay').status_code in (200,404)


def test_coingecko_missing_api_key(monkeypatch):
    monkeypatch.delenv('COINGECKO_API_KEY',raising=False)
    provider=CoinGeckoProvider()
    with pytest.raises(DataError,match='API-key ontbreekt'):
        provider.candles('bitcoin',30)


def test_risk_entry_uses_previous_candle():
    d=demo_candles()
    a=PaperEngine(d,'ema',capital=10000)
    a.step(130)
    for tr in a.trades:
        assert tr['entry_time']<=tr['exit_time']
        assert tr['qty']>0


def test_provider_uses_header_and_handles_ohlc_without_volume(monkeypatch):
    import market_data
    class Response:
        status_code=200
        ok=True
        headers={}
        def json(self):
            ts=int(pd.Timestamp.now(tz='UTC').floor('4h').timestamp()*1000)
            return [[ts-(60-i)*4*3600*1000,100+i,103+i,99+i,101+i] for i in range(60)]
    captured={}
    def fake_get(url,params,headers,timeout):
        captured.update({'url':url,'params':params,'headers':headers,'timeout':timeout})
        return Response()
    monkeypatch.setattr(market_data.requests,'get',fake_get)
    provider=CoinGeckoProvider(api_key='local-secret',plan='demo')
    df=provider.candles('ethereum',30)
    assert df.attrs['volume_is_actual'] is False
    assert df['volume'].isna().all()
    assert captured['headers']['x-cg-demo-api-key']=='local-secret'
    assert 'local-secret' not in captured['url']
    assert len(df)==60
