import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
import app
from engine import PaperEngine,Position,RISK_PER_TRADE
from market_data import demo_candles
from strategies import add_indicators,short_signals
from research import walk_forward,research,stress_parameters

client=TestClient(app.app)

def engine(rate=0,mode="short",fee=0,slip=0):
    return PaperEngine(demo_candles(),parameters={"trade_mode":mode,"short_borrow_daily_pct":rate},fee=fee,slip=slip)

def test_short_reserves_cash_and_releases_collateral_with_profit():
    e=engine();e._entry(100,"entry",100,2,"short");p=e.position
    assert p.side=="short"
    assert e.cash==pytest.approx(10000-p.entry*p.qty)
    assert e.equity(100)==pytest.approx(10000)
    assert e.equity(90)==pytest.approx(10000+10*p.qty)
    q=p.qty;e._close("exit",90,"test")
    assert e.cash==pytest.approx(10000+10*q)
    assert e.trades[-1]["pnl"]==pytest.approx(round(10*q,4))
    assert e.trades[-1]["side"]=="short"

def test_rising_price_loses_money_on_short():
    e=engine();e._entry(100,"entry",100,2,"short");q=e.position.qty
    assert e.equity(110)<10000
    e._close("exit",110,"test")
    assert e.cash==pytest.approx(10000-10*q)
    assert e.trades[-1]["pnl"]<0

def test_short_slippage_commission_and_risk_budget():
    e=engine(rate=.1,fee=.001,slip=.002)
    e._entry(100,"entry",100,2,"short");p=e.position
    assert p.entry==pytest.approx(99.8)
    assert p.stop>p.entry and 0<p.target<p.entry
    assert p.planned_risk<=10000*RISK_PER_TRADE+1e-8
    worst=p.stop*(1+e.slip)
    loss=(worst-p.entry)*p.qty+e.fee*(p.entry+worst)*p.qty
    assert loss<=10000*RISK_PER_TRADE
    e._close("exit",90,"test")
    assert e.trades[-1]["exit"]==pytest.approx(90.18)
    assert e.cash-10000==pytest.approx(e.trades[-1]["pnl"],abs=.0001)

def force_short(e,index=100):
    e.idx=index;e.start=index;e.end=index+1
    e.entry_signals[:]=False;e.exit_signals[:]=False
    e.short_entry_signals[:]=False;e.short_exit_signals[:]=False
    e._entry(index,e.rows[index].time.isoformat(),100,2,"short")
    return e.position

def test_short_intrabar_stop_first_when_both_levels_hit():
    e=engine();p=force_short(e)
    e.rows[100]=e.rows[100]._replace(open=100,high=110,low=90,close=100)
    e.step(1)
    assert e.position is None
    assert e.trades[-1]["reason"]=="Stop-loss"
    assert e.trades[-1]["exit"]==p.stop

def test_short_gap_does_not_fill_at_stop_and_can_create_debt():
    e=engine();p=force_short(e)
    e.rows[100]=e.rows[100]._replace(open=10000,high=10000,low=10000,close=10000)
    e.step(1)
    assert e.trades[-1]["exit"]==10000
    assert e.trades[-1]["exit"]>p.stop
    assert e.cash<0 and e.locked

def test_short_target_above_zero_required():
    e=engine();e._entry(100,"entry",1,10,"short")
    assert e.position is None

def test_borrow_is_deducted_once_per_bar_and_in_trade_pnl():
    e=engine(rate=.2);p=force_short(e)
    e.rows[100]=e.rows[100]._replace(open=100,high=100,low=100,close=100)
    expected=p.entry*p.qty*.002*e.bar_days(100)
    e.step(1)
    assert e.position.borrow_paid==pytest.approx(expected)
    assert e.equity(100)==pytest.approx(10000-expected)
    e._close("exit",100,"test")
    assert e.cash==pytest.approx(10000-expected)
    assert e.trades[-1]["borrow_cost"]==pytest.approx(round(expected,6))
    assert e.trades[-1]["pnl"]==pytest.approx(round(-expected,4))

def test_direction_modes_only_generate_allowed_sides():
    d=demo_candles(count=900)
    for mode,allowed in (("long",{"long"}),("short",{"short"}),("both",{"long","short"})):
        result=PaperEngine(d,parameters={"trade_mode":mode}).finish()
        sides={x["side"] for x in result["trades"]}
        assert sides and sides<=allowed
        if mode=="both":assert sides==allowed
        assert result["metrics"]["long_trades"]+result["metrics"]["short_trades"]==len(result["trades"])

@pytest.mark.parametrize("strategy",["ema","rsi","breakout"])
def test_short_signals_never_depend_on_future_candles(strategy):
    d=demo_candles()
    a=short_signals(add_indicators(d),strategy)
    changed=d.copy();changed.loc[151:,["open","high","low","close"]]*=3
    b=short_signals(add_indicators(changed),strategy)
    assert np.array_equal(a[0][:151],b[0][:151])
    assert np.array_equal(a[1][:151],b[1][:151])

def test_breakdown_signals_use_prior_lows_and_real_volume():
    d=demo_candles()
    eng=PaperEngine(d,"breakout",parameters={"trade_mode":"short","volume_multiple":1})
    # Force one completed candle below all previous lows with enough volume.
    i=100;d.loc[i,"close"]=d.loc[:i-1,"low"].min()*.5
    d.loc[i,"low"]=d.loc[i,"close"]*.99;d.loc[i,"volume"]=1e9
    enters,_=short_signals(add_indicators(d,{"volume_multiple":1}),"breakout")
    assert enters[i]

def test_short_replay_exactly_resumes_and_exports_direction_and_cost():
    params={"parameters":{"trade_mode":"short","short_borrow_daily_pct":.2}}
    r=client.post("/api/replay/start",json=params);assert r.status_code==200,r.text
    rid=r.json()["run_id"]
    first=client.post("/api/replay/step",json={"steps":100}).json()
    app._sessions.clear()
    resumed=client.post("/api/runs/"+rid+"/resume",json={})
    assert resumed.status_code==200,resumed.text
    assert resumed.json()["snapshot"]==first["snapshot"]
    test=client.post("/api/backtest",json=params)
    assert test.status_code==200,test.text
    exported=client.get("/api/export/backtest?run_id="+test.json()["run_id"])
    assert exported.status_code==200
    assert "side" in exported.text and "borrow_cost" in exported.text and "short" in exported.text

def test_walkforward_does_not_optimize_or_change_direction():
    result=walk_forward(demo_candles(count=900),"ema",10000,.001,.0005,{"trade_mode":"short"})
    assert result["selected"]["trade_mode"]=="short"
    assert all(f["selected"]["trade_mode"]=="short" for f in result["folds"])
    assert result["holdout"]["long_trades"]==0
    assert stress_parameters({"trade_mode":"short","short_borrow_daily_pct":.2})["short_borrow_daily_pct"]==.4

def test_invalid_direction_or_negative_borrow_rejected():
    for p in ({"trade_mode":"live"},{"short_borrow_daily_pct":-1},{"short_borrow_daily_pct":float("inf")}):
        if p.get("short_borrow_daily_pct")==float("inf"):continue
        assert client.post("/api/backtest",json={"parameters":p}).status_code==422

def test_older_replay_is_preserved_instead_of_silently_recomputed():
    import storage
    rid=storage.save_run("replay",{"coin":"bitcoin"},{"snapshot":{"progress":10},"meta":{"coin":"bitcoin"},"candles":{}})
    response=client.post("/api/runs/"+rid+"/resume",json={})
    assert response.status_code==409
    stored=client.get("/api/runs/"+rid)
    assert stored.status_code==200
    assert stored.json()["payload"]["snapshot"]["progress"]==10

def test_both_direction_replay_holds_only_one_position_and_pnl_matches_cash():
    e=PaperEngine(demo_candles(count=900),parameters={"trade_mode":"both","short_borrow_daily_pct":.05})
    for _ in range(9):
        e.step(100)
        if e.position:assert e.position.side in ("long","short")
    result=e.finish()
    assert e.position is None
    assert result["equity"]==pytest.approx(10000+sum(t["pnl"] for t in e.trades),abs=.02)


def test_short_holding_duration_counts_final_candle_once():
    e=engine();p=force_short(e)
    e.end=105
    for i in range(100,105):
        e.rows[i]=e.rows[i]._replace(open=100,high=100,low=100,close=100)
    result=e.finish()
    assert result["metrics"]["avg_holding_bars"]==5
    assert e.trades[-1]["holding_bars"]==5

def test_both_mode_can_flip_only_at_the_open():
    e=engine(mode="both");e.idx=100;e.start=100;e.end=101
    e._entry(100,"previous",100,2,"long")
    e.entry_signals[:]=False;e.exit_signals[:]=False;e.short_entry_signals[:]=False
    e.short_exit_signals[:]=False
    e.exit_signals[99]=True;e.short_entry_signals[99]=True
    e.rows[99]=e.rows[99]._replace(atr=2)
    e.rows[100]=e.rows[100]._replace(open=100,high=100,low=100,close=100)
    e.step(1)
    assert e.position.side=="short"
    assert len(e.trades)==1 and e.trades[0]["side"]=="long"

def test_intrabar_short_stop_cannot_reenter_retroactively():
    e=engine();force_short(e)
    e.short_entry_signals[:]=True
    e.rows[100]=e.rows[100]._replace(open=100,high=110,low=99,close=100)
    e.step(1)
    assert e.position is None
    assert len([x for x in e.events if x["type"]=="OPEN SHORT (PAPER)"])==1

