import io
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
import app
import storage
import updater
import secrets_store
from market_data import demo_candles, pack_candles, unpack_candles, KrakenProvider, import_csv, DataError
from research import research, benchmark

client=TestClient(app.app)

def test_settings_survive_new_connection_without_secrets(monkeypatch):
    saved=[]
    monkeypatch.setattr(app,"save_key",lambda key:saved.append(key))
    r=client.post("/api/settings",json={"params":{"coin":"ethereum","days":180},"api_key":"test-only-key"})
    assert r.status_code==200
    assert saved==["test-only-key"]
    assert storage.settings()["params"]["coin"]=="ethereum"
    assert "test-only-key" not in storage.connect.__module__
    assert "test-only-key" not in client.get("/api/settings").text
    assert "test-only-key" not in (storage.data_dir()/"lab.sqlite3").read_bytes().decode("latin1")

def test_backtest_persists_and_exports_after_memory_clear():
    r=client.post("/api/backtest",json={"strategy":"ema"})
    assert r.status_code==200, r.text
    rid=r.json()["run_id"]
    app._sessions.clear()
    row=client.get("/api/runs/"+rid).json()
    assert row["payload"]["backtest"]==r.json()["backtest"]
    assert client.get("/api/export/backtest?run_id="+rid).status_code==200
    assert client.get("/api/runs").json()[0]["id"]==rid

def test_replay_reconstructs_exact_state_after_restart():
    rid=client.post("/api/replay/start",json={}).json()["run_id"]
    first=client.post("/api/replay/step",json={"steps":100}).json()
    app._sessions.clear()
    resumed=client.post("/api/runs/"+rid+"/resume",json={})
    assert resumed.status_code==200,resumed.text
    assert resumed.json()["snapshot"]==first["snapshot"]
    assert client.post("/api/replay/step",json={"steps":5}).json()["snapshot"]["progress"]==105

def test_remote_site_cannot_update_or_change_settings():
    for path in ("/api/settings","/api/updates/stage"):
        assert client.post(path,json={},headers={"Origin":"https://evil.example"}).status_code==403
    assert client.get("/api/settings",headers={"Host":"evil.example"}).status_code==403
    assert client.post("/api/settings",json={"params":{}},headers={"Sec-Fetch-Site":"cross-site"}).status_code==403

def test_pack_preserves_nan_volume_and_attrs():
    d=demo_candles()
    d["volume"]=np.nan;d.attrs["volume_is_actual"]=False
    out=unpack_candles(json.loads(json.dumps(pack_candles(d),allow_nan=False)))
    assert out.time.equals(d.time)
    assert out.volume.isna().all()
    assert out.attrs==d.attrs

def test_csv_validation_and_persistence():
    d=demo_candles(count=120)
    text=d.to_csv(index=False)
    result=client.post("/api/datasets",json={"coin":"bitcoin","text":text})
    assert result.status_code==200,result.text
    rid=result.json()["dataset_id"]
    r=client.post("/api/backtest",json={"source":"csv","dataset_id":rid})
    assert r.status_code==200,r.text
    assert r.json()["meta"]["candle_count"]==120
    bad=client.post("/api/backtest",json={"source":"csv","coin":"ethereum","dataset_id":rid})
    assert bad.status_code==422
    with pytest.raises(DataError):
        import_csv(d.drop(index=50).to_csv(index=False),"bitcoin")
    d.loc[5,"volume"]=-1
    with pytest.raises(DataError):
        import_csv(d.to_csv(index=False),"bitcoin")

def test_kraken_removes_unfinished_and_caches_across_instances(monkeypatch):
    import market_data
    now=int(pd.Timestamp.now(tz="UTC").floor("1h").timestamp())
    rows=[[now-(100-i)*3600,"100","103","99","101","101","20",5] for i in range(101)]
    calls=[]
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"error":[],"result":{"XXBTZUSD":rows,"last":now}}
    def get(url,**kwargs):
        calls.append(url)
        assert url=="https://api.kraken.com/0/public/OHLC"
        return Response()
    monkeypatch.setattr(market_data.requests,"get",get)
    d=KrakenProvider().candles("bitcoin",30,60)
    assert len(d)==100
    assert d.time.max()<pd.Timestamp(now,unit="s",tz="UTC")
    assert d.attrs["volume_is_actual"]
    assert len(KrakenProvider().candles("bitcoin",30,60))==100
    assert len(calls)==1

def test_unknown_coin_and_demo_extra_coin_rejected():
    for coin in ("evil","ripple"):
        r=client.post("/api/backtest",json={"coin":coin,"source":"demo"})
        assert r.status_code==422,r.text

def test_research_costs_folds_benchmark_and_volume_gate():
    d=demo_candles()
    r=research(d,10000,.001,.0005)
    assert len(r["strategies"])==3
    for row in r["strategies"]:
        folds=row["folds"]
        assert len(folds)==3
        assert all(folds[i]["to"]<folds[i+1]["from"] for i in range(2))
    constant=d.copy()
    constant[["open","high","low","close"]]=100
    base=benchmark(constant,10000,.001,.0005,252,360)
    assert base["return_pct"]<0
    assert base["max_drawdown_pct"]>0
    d.attrs["volume_is_actual"]=False
    assert research(d,10000,.001,.0005)["strategies"][2]["skipped"]
    response=client.post("/api/research",json={})
    assert response.status_code==200,response.text
    assert storage.get_run(response.json()["run_id"])["kind"]=="research"

def archive(extra=None):
    files={"app.py":b"# new", "updater.py":b"# updater", "storage.py":b"# storage",
           "requirements.txt":b"", "START_WINDOWS.bat":b"@echo off",
           "version.json":b'{"version":"0.2.0","paper_only":true}'}
    for name in ("start_lab.py","secrets_store.py","market_data.py","research.py","engine.py","strategies.py","static/index.html","static/app.js","static/style.css"):
        files[name]=b"# test fixture"
    files.update(extra or {})
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        for name,data in files.items():z.writestr("repo-root/"+name,data)
    return buf.getvalue()

@pytest.mark.parametrize("path",["../escape.py",".env","static/../../escape.py","data/results.json","evil.exe","static/key.pem"])
def test_updater_rejects_unsafe_archive(path):
    with pytest.raises(ValueError):updater.archive_files(archive({path:b"bad"}))

def test_update_stage_pin_apply_preserves_data_and_backup(tmp_path,monkeypatch):
    root=tmp_path/"installation";root.mkdir()
    (root/"app.py").write_text("# old")
    (root/".env").write_text("PRIVATE=placeholder")
    monkeypatch.setattr(updater,"ROOT",root)
    raw=archive()
    sha="a"*40
    calls=[]
    def gh(*args,**kwargs):
        calls.append(args)
        if args[-1].endswith("/commits/main"):
            return json.dumps({"sha":sha,"commit":{"message":"test update"}})
        assert args[-1].endswith("/zipball/"+sha)
        return raw
    monkeypatch.setattr(updater,"gh",gh)
    storage.save_settings({"params":{"coin":"ethereum"}})
    assert updater.stage()["staged"]
    updater.apply()
    assert (root/"app.py").read_text()=="# new"
    assert (root/".env").read_text()=="PRIVATE=placeholder"
    assert storage.settings()["params"]["coin"]=="ethereum"
    assert list((storage.data_dir()/"backups").glob("*/app.py"))[0].read_text()=="# old"
    assert not (storage.data_dir()/"pending-update.json").exists()
    assert not updater.check()["available"]

def test_update_tamper_refused(tmp_path,monkeypatch):
    root=tmp_path/"installation";root.mkdir()
    monkeypatch.setattr(updater,"ROOT",root)
    monkeypatch.setattr(updater,"gh",lambda *a,**k:json.dumps({"sha":"a"*40,"commit":{"message":"x"}}) if a[-1].endswith("/commits/main") else archive())
    updater.stage()
    (storage.data_dir()/"update.zip").write_bytes(b"tampered")
    with pytest.raises(ValueError,match="beschadigd"):updater.apply()
    assert not (root/"app.py").exists()

def test_interrupted_update_restores_before_next_apply(tmp_path,monkeypatch):
    root=tmp_path/"installation";root.mkdir()
    (root/"app.py").write_text("half written")
    monkeypatch.setattr(updater,"ROOT",root)
    backup=storage.data_dir()/"backups"/"previous";backup.mkdir(parents=True)
    (backup/"app.py").write_text("original")
    (storage.data_dir()/"update-transaction.json").write_text(json.dumps({"root":str(root),"backup":str(backup),"files":{"app.py":True}}))
    updater.apply()
    assert (root/"app.py").read_text()=="original"

def test_dpapi_roundtrip_no_plaintext_on_disk():
    if __import__("os").name!="nt":pytest.skip("Windows DPAPI")
    secrets_store.save_key("test-only-key-not-a-real-credential")
    assert secrets_store.get_key()=="test-only-key-not-a-real-credential"
    assert b"test-only-key" not in (storage.data_dir()/"coingecko.dpapi").read_bytes()

def test_intrabar_stop_cannot_trigger_retroactive_open_entry(monkeypatch):
    import engine
    from engine import PaperEngine, Position
    d=demo_candles()
    eng=PaperEngine(d,"ema")
    eng.idx=100
    row=eng.d.iloc[100]
    # Existing position stops below the open during this candle.
    eng.position=Position("previous",float(row.open),.01,float(row.open)*.999, float(row.high)*2,0,99)
    eng.cash=9000
    eng.entry_signals[:]=True;eng.exit_signals[:]=False
    eng.rows[100]=eng.rows[100]._replace(low=float(row.open)*.9)
    eng.step(1)
    assert eng.position is None
    assert not any(e["type"]=="BUY LONG (PAPER)" for e in eng.events)

def test_apply_failure_restores_all_original_code(tmp_path,monkeypatch):
    root=tmp_path/"installation";root.mkdir()
    (root/"app.py").write_text("original")
    monkeypatch.setattr(updater,"ROOT",root)
    monkeypatch.setattr(updater,"gh",lambda *a,**k:json.dumps({"sha":"a"*40,"commit":{"message":"x"}}) if a[-1].endswith("/commits/main") else archive())
    updater.stage()
    original_replace=updater.os.replace
    def failed_replace(src,dst):
        if str(dst).endswith("storage.py"):raise OSError("test interrupted")
        return original_replace(src,dst)
    monkeypatch.setattr(updater.os,"replace",failed_replace)
    with pytest.raises(OSError):updater.apply()
    assert (root/"app.py").read_text()=="original"
    assert not (root/"updater.py").exists()
    assert (storage.data_dir()/"pending-update.json").exists()


@pytest.mark.parametrize("strategy",["ema","rsi","breakout"])
def test_all_strategy_signals_are_unchanged_by_future_candles(strategy):
    from strategies import add_indicators,signal
    d=demo_candles()
    original=add_indicators(d)
    changed=d.copy()
    changed.loc[151:,["open","high","low","close"]]*=2
    changed.loc[151:,"volume"]*=10
    altered=add_indicators(changed)
    for i in range(22,151):
        assert signal(original,i,strategy)==signal(altered,i,strategy)

def test_updater_does_not_claim_missing_github_auth_succeeded(monkeypatch):
    monkeypatch.setattr(updater.shutil,"which",lambda name:None)
    def unauthorized(*a,**k):
        raise updater.HTTPError("https://api.github.com",404,"not found",{},None)
    monkeypatch.setattr(updater,"urlopen",unauthorized)
    result=client.get("/api/updates")
    assert result.status_code==503
    assert "GitHub CLI" in result.json()["detail"]

def test_saved_key_takes_precedence_over_process_environment(monkeypatch):
    monkeypatch.setenv("COINGECKO_API_KEY","old-test-value")
    secrets_store.save_key("new-test-value")
    assert secrets_store.get_key()=="new-test-value"




def test_public_updates_do_not_require_github_cli(monkeypatch):
    calls=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):return b'{"sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","commit":{"message":"public update"}}'
    def open_public(request,**kwargs):
        calls.append(request.full_url)
        return Response()
    monkeypatch.setattr(updater,"urlopen",open_public)
    monkeypatch.setattr(updater.shutil,"which",lambda name:None)
    info=updater.check()
    assert info["latest"]=="a"*40
    assert calls==["https://api.github.com/repos/Jaze360/crypto-paper-lab/commits/main"]



