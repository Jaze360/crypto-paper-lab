import pytest
from fastapi.testclient import TestClient
import app,storage
from engine import PaperEngine,direction_breakdown
from market_data import demo_candles
from research import research,walk_forward

client=TestClient(app.app)

def trade(side,net,fees,borrow,slip,reason):
    return {"side":side,"pnl":net,"fees":fees,"borrow_cost":borrow,"slippage_cost":slip,
            "gross_pnl":net+fees+borrow,"pnl_R":net/10,"reason":reason}

def test_side_and_exit_sums_reconcile_without_double_counting_slippage():
    trades=[trade("long",90,8,0,2,"Take-profit"),trade("long",-25,4,0,1,"Stop-loss"),
            trade("short",40,5,3,2,"Take-profit"),trade("short",-15,4,1,1,"Strategie exit vorige candle")]
    d=direction_breakdown(trades,10000)
    assert d["sides"]["long"]["net_pnl"]==65
    assert d["sides"]["short"]["net_pnl"]==25
    assert sum(v["contribution_pct"] for v in d["sides"].values())==pytest.approx(.9)
    for side,m in d["sides"].items():
        assert m["gross_before_costs"]-m["slippage_cost"]-m["commissions"]-m["borrow_cost"]==pytest.approx(m["net_pnl"])
        exits=[x for x in d["exits"] if x["side"]==side]
        assert sum(x["trades"] for x in exits)==m["trades"]
        for field in ("net_pnl","commissions","borrow_cost","slippage_cost"):
            assert sum(x[field] for x in exits)==pytest.approx(m[field])
    assert d["sides"]["long"]["winrate_pct"]==50

def test_empty_side_is_explicit_zero_with_no_fake_winrate():
    d=direction_breakdown([trade("short",1,0,0,0,"Testperiode einde")],10000)
    assert d["sides"]["long"]["trades"]==0
    assert d["sides"]["long"]["net_pnl"]==0
    assert d["sides"]["long"]["winrate_pct"] is None
    assert not any(x["side"]=="long" for x in d["exits"])

def test_legacy_slippage_is_unknown_and_original_record_is_unchanged():
    old={"pnl":10,"fees":2,"pnl_R":1,"reason":"Take-profit"}
    original=old.copy();d=direction_breakdown([old],10000)
    assert old==original
    assert d["sides"]["long"]["net_pnl"]==10
    assert d["sides"]["long"]["commissions"]==2
    assert d["sides"]["long"]["slippage_cost"] is None
    assert d["sides"]["long"]["gross_before_costs"] is None
    assert d["sides"]["long"]["gross_after_slippage"]==12

@pytest.mark.parametrize("side",["long","short"])
def test_engine_records_both_execution_costs_and_gross_pnl(side):
    e=PaperEngine(demo_candles(),fee=.001,slip=.002,parameters={"trade_mode":"both"})
    e._entry(100,"open",100,2,side)
    qty=e.position.qty
    e._close("close",110 if side=="long" else 90,"test")
    row=e.trades[0]
    expected=(.2+(110 if side=="long" else 90)*.002)*qty
    assert row["slippage_cost"]==pytest.approx(expected,abs=1e-6)
    assert row["gross_before_slippage"]-row["slippage_cost"]-row["fees"]-row["borrow_cost"]==pytest.approx(row["pnl"],abs=.0002)

def test_research_and_walkforward_keep_breakdown_in_test_and_stress():
    d=demo_candles(count=900)
    r=research(d,10000,.001,.0005,{"trade_mode":"both"})
    assert all("direction_breakdown" in x["test"] and "direction_breakdown" in x["cost_stress"] for x in r["strategies"])
    w=walk_forward(d,"ema",10000,.001,.0005,{"trade_mode":"both"})
    assert "direction_breakdown" in w["holdout"]
    assert "direction_breakdown" in w["holdout_stress"]
    assert all("direction_breakdown" in x["test"] for x in w["folds"])
    for m in (w["holdout"],w["holdout_stress"]):
        assert sum(s["net_pnl"] for s in m["direction_breakdown"]["sides"].values())==pytest.approx(m["net_pnl"],abs=.01)

def test_old_journal_can_be_enriched_on_read_without_database_mutation():
    trades=[{"pnl":10,"fees":2,"pnl_R":1,"reason":"Take-profit"}]
    payload={"backtest":{"test":{"trades":trades,"metrics":{"net_pnl":10}}}}
    rid=storage.save_run("backtest",{"capital":10000},payload)
    r=client.get("/api/runs/"+rid)
    assert r.status_code==200
    m=r.json()["payload"]["backtest"]["test"]["metrics"]
    assert m["direction_breakdown"]["sides"]["long"]["net_pnl"]==10
    assert "direction_breakdown" not in storage.get_run(rid)["payload"]["backtest"]["test"]["metrics"]

def test_open_position_is_not_presented_as_closed_directional_profit():
    e=PaperEngine(demo_candles(),parameters={"trade_mode":"both"})
    e._entry(100,"open",100,2,"short")
    m=e.snapshot()["metrics"]
    assert m["direction_breakdown"]["scope"]=="closed_trades"
    assert sum(v["trades"] for v in m["direction_breakdown"]["sides"].values())==0
