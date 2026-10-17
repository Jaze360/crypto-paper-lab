import json,time
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
import app
from strategies import StrategyConfig,add_indicators,signal
from engine import PaperEngine,RISK_PER_TRADE
from market_data import demo_candles,HistoricalProvider,DataError
from research import walk_forward
import storage

client=TestClient(app.app)

def test_parameter_validation_and_api_reject_invalid():
    for params in ({"ema_fast":50,"ema_slow":20},{"rsi_entry":45,"rsi_exit":40},{"stop_atr":0}):
        with pytest.raises(ValueError):StrategyConfig(**params)
        assert client.post("/api/backtest",json={"parameters":params}).status_code==422

def test_configurable_rules_and_risk_cap():
    d=demo_candles()
    a=add_indicators(d,{"ema_fast":5,"ema_slow":50})
    b=add_indicators(d)
    assert not np.allclose(a.ema_fast.fillna(0),b.ema_fast.fillna(0))
    eng=PaperEngine(d,parameters={"stop_atr":3,"target_atr":6})
    eng._entry(100,"test",100,2)
    p=eng.position
    assert p.stop==pytest.approx(p.entry-6)
    assert p.target==pytest.approx(p.entry+12)
    loss=(p.entry-p.stop*(1-eng.slip))*p.qty+eng.fee*(p.entry+p.stop*(1-eng.slip))*p.qty
    assert loss<=10000*RISK_PER_TRADE+1e-5

def test_exposure_metrics_include_idle_candles():
    d=demo_candles()
    eng=PaperEngine(d,start=100,end=110,fee=0,slip=0)
    eng.entry_signals[:]=False;eng.exit_signals[:]=False
    snap=eng.finish()
    assert snap["metrics"]["time_in_market_pct"]==0
    assert snap["metrics"]["avg_exposure_pct"]==0
    eng=PaperEngine(d,start=100,end=110,fee=0,slip=0)
    eng.entry_signals[:]=False;eng.exit_signals[:]=False
    from engine import Position
    eng.position=Position("test",100,1,1,1e9,0,99);eng.cash=9900
    for i in range(100,110):
        eng.rows[i]=eng.rows[i]._replace(open=100,high=100,low=100,close=100)
    snap=eng.finish()
    assert snap["metrics"]["time_in_market_pct"]==100
    assert snap["metrics"]["avg_exposure_pct"]==1
    assert snap["metrics"]["max_exposure_pct"]==1
    assert snap["metrics"]["avg_holding_bars"] is not None

def test_final_holdout_does_not_influence_selection_or_earlier_folds():
    d=demo_candles(count=900)
    first=walk_forward(d,"ema",10000,.001,.0005)
    changed=d.copy()
    cut=round(len(d)*.8)
    changed.loc[cut:,["open","high","low","close"]]*=3
    second=walk_forward(changed,"ema",10000,.001,.0005)
    assert first["selected"]==second["selected"]
    assert first["selection"]==second["selection"]
    assert first["folds"]==second["folds"]
    assert all(f["train_end"]==f["test_start"] and f["test_end"]<=cut for f in first["folds"])
    assert all(first["folds"][i]["test_end"]==first["folds"][i+1]["test_start"] for i in range(2))
    assert first["holdout_start"]==cut
    assert len(first["selection"])<=4

def test_walkforward_requires_enough_data_and_volume():
    with pytest.raises(ValueError,match="600"):walk_forward(demo_candles(),"ema",10000,.001,.0005)
    d=demo_candles(count=900);d.attrs["volume_is_actual"]=False
    with pytest.raises(ValueError,match="volume"):walk_forward(d,"breakout",10000,.001,.0005)

@pytest.mark.parametrize("strategy",["ema","rsi","breakout"])
def test_custom_parameters_are_causal(strategy):
    params={"ema_fast":5,"ema_slow":50,"rsi_period":21,"breakout_period":40}
    d=demo_candles()
    a=add_indicators(d,params)
    altered=d.copy();altered.loc[151:,["open","high","low","close"]]*=3
    b=add_indicators(altered,params)
    assert [signal(a,i,strategy) for i in range(150)]==[signal(b,i,strategy) for i in range(150)]

def test_history_paginates_uses_data_only_domain_and_caches(monkeypatch):
    import market_data
    calls=[]
    class Response:
        status_code=200
        def __init__(self,params):self.params=params
        def raise_for_status(self):pass
        def json(self):
            number=1000 if len(calls)==1 else 250
            start=self.params["startTime"]
            return [[start+i*3600000,"100","102","99","101","12",start+(i+1)*3600000-1] for i in range(number)]
    class Session:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,url,params,timeout):
            assert url=="https://data-api.binance.vision/api/v3/klines"
            calls.append(params.copy());return Response(params)
    monkeypatch.setattr(market_data.requests,"Session",Session)
    first=HistoricalProvider().candles("bitcoin",1095,60)
    assert len(first)==1250
    assert calls[1]["startTime"]==calls[0]["startTime"]+1000*3600000
    assert first.attrs["quote"]=="USDT" and first.attrs["volume_is_actual"]
    assert len(HistoricalProvider().candles("bitcoin",1095,60))==1250
    assert len(calls)==2

def test_history_does_not_include_unclosed_or_outside_requested_range(monkeypatch):
    import market_data
    now=int(pd.Timestamp.now(tz="UTC").floor("1h").timestamp()*1000)
    class Response:
        status_code=200
        def raise_for_status(self):pass
        def json(self):return [[now-(100-i)*3600000,"100","102","99","101","1",now-(99-i)*3600000-1] for i in range(101)]
    class Session:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def get(self,*a,**k):return Response()
    monkeypatch.setattr(market_data.requests,"Session",Session)
    d=HistoricalProvider().candles("bitcoin",7,60)
    assert len(d)==100
    assert d.time.max()<pd.Timestamp(now,unit="ms",tz="UTC")

def wait_job(job_id):
    for _ in range(1000):
        state=client.get("/api/research/jobs/"+job_id).json()
        if state["status"]!="running":return state
        time.sleep(.01)
    raise AssertionError("Onderzoek bleef lopen")

def test_background_walkforward_persists_results(monkeypatch):
    monkeypatch.setattr(app,"get_data",lambda p,progress=None:demo_candles(p.coin,900))
    r=client.post("/api/research/jobs",json={"params":{},"mode":"walkforward"})
    assert r.status_code==200,r.text
    result=wait_job(r.json()["id"])
    assert result["status"]=="done",result
    stored=storage.get_run(result["run_id"])
    assert stored["kind"]=="walkforward"
    assert stored["payload"]["walkforward"]["holdout_start"]==720

def test_multiple_coins_include_failed_cases(monkeypatch):
    def data(p,progress=None):
        if p.coin=="solana":raise DataError("test market unavailable")
        return demo_candles(p.coin,900)
    monkeypatch.setattr(app,"get_data",data)
    response=client.post("/api/research/jobs",json={"params":{"source":"historical"},"mode":"batch","coins":["bitcoin","ethereum","solana"]})
    state=wait_job(response.json()["id"])
    assert state["status"]=="done",state
    cases=storage.get_run(state["run_id"])["payload"]["batch"]
    assert [r["coin"] for r in cases]==["bitcoin","ethereum","solana"]
    assert "error" in cases[-1]
    assert "walkforward" in cases[0]

def test_old_results_and_settings_remain_readable():
    rid=storage.save_run("backtest",{"coin":"bitcoin"},{"legacy":True})
    assert client.get("/api/runs/"+rid).json()["payload"]["legacy"]
    storage.save_settings({"params":{"source":"kraken","coin":"bitcoin","days":365}})
    assert client.get("/api/settings").status_code==200

def test_asset_responses_disable_stale_browser_cache():
    assert client.get("/").headers["cache-control"]=="no-store"
    assert client.get("/static/app.js").headers["cache-control"]=="no-store"
