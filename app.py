"""Local paper research API. No broker authentication or order execution."""
import csv
import io
import json
import os
from pathlib import Path
from threading import RLock
from typing import Literal
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from market_data import (CoinGeckoProvider, KrakenProvider, demo_candles, DataError,
                         COINS, pack_candles, unpack_candles, import_csv)
from engine import PaperEngine, run_backtest
from strategies import STRATEGIES
import storage
from secrets_store import get_key, save_key
import updater
from research import research

BASE = Path(__file__).parent
VERSION = json.loads((BASE/"version.json").read_text(encoding="utf-8-sig"))["version"]
app = FastAPI(title="Crypto Paper Lab — UITSLUITEND SIMULATIE", version=VERSION)
_sessions = {}
_lock = RLock()

@app.middleware("http")
async def local_only(request: Request, call_next):
    # Host validation + origin validation protect settings/update endpoints from remote sites.
    host = request.headers.get("host","").split(":")[0]
    if host not in {"127.0.0.1","localhost","testserver"}:
        return JSONResponse({"detail":"Alleen lokaal bereikbaar."},status_code=403)
    if request.method not in {"GET","HEAD","OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin != "http://" + request.headers.get("host", "") :
            return JSONResponse({"detail":"Aanvraag van een andere website geweigerd."},status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail":"Cross-site aanvraag geweigerd."},status_code=403)
        if request.headers.get("content-length") and int(request.headers["content-length"])>9_000_000:
            return JSONResponse({"detail":"Aanvraag te groot."},status_code=413)
    return await call_next(request)

class Params(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["demo","coingecko","kraken","csv"] = "demo"
    coin: str = Field(default="bitcoin", pattern="^[a-z0-9-]{1,60}$")
    strategy: Literal["ema","rsi","breakout"] = "ema"
    days: Literal[7,14,30,90,180,365] = 30
    interval: Literal[60,240,1440] = 1440
    dataset_id: str | None = Field(default=None, pattern="^[a-f0-9]{32}$")
    capital: float = Field(default=10000,ge=100,le=1e7,allow_inf_nan=False)
    fee_pct: float = Field(default=.10,ge=0,le=1,allow_inf_nan=False)
    slippage_pct: float = Field(default=.05,ge=0,le=2,allow_inf_nan=False)

def get_data(p):
    if p.coin not in COINS:
        raise DataError("Niet toegestane munt.")
    if p.source=="demo":
        return demo_candles(p.coin,360)
    if p.source=="coingecko":
        return CoinGeckoProvider().candles(p.coin,p.days)
    if p.source=="kraken":
        return KrakenProvider().candles(p.coin,p.days,p.interval)
    if not p.dataset_id:
        raise DataError("Importeer eerst een CSV-bestand.")
    try:
        stored=storage.get_run(p.dataset_id)
    except KeyError:
        raise DataError("CSV-dataset niet gevonden.")
    if stored["kind"]!="dataset" or stored["params"]["coin"]!=p.coin:
        raise DataError("CSV-dataset hoort bij een andere coin.")
    return unpack_candles(stored["payload"])

def summary(df,p):
    gaps = df.time.diff().dropna()
    return {"source":df.attrs.get("source"),"coin":p.coin,"strategy":p.strategy,
            "volume_is_actual":df.attrs.get("volume_is_actual",False),
            "synthetic":p.source=="demo", "timeframe":df.attrs.get("timeframe",df.attrs.get("time_frame","onbekend")),
            "note":df.attrs.get("note", "Synthetische demonstratiedata; geen echte historische koersen." if p.source=="demo" else "CoinGecko bepaalt candle-intervallen automatisch; langere periode betekent niet noodzakelijk meer candles."),
            "gaps_detected": bool(len(gaps) and (gaps > gaps.median()*1.5).any()),
            "candle_count":len(df),"from":df.iloc[0].time.isoformat(),"to":df.iloc[-1].time.isoformat(),
            "price_data":[{"time":r.time.isoformat(),"close":round(float(r.close),5)} for r in df.itertuples()]}

@app.get("/")
def index():
    return FileResponse(BASE/"static/index.html")

@app.get("/static/{filename}")
def static(filename:str):
    if filename not in {"app.js","style.css"}: raise HTTPException(404)
    return FileResponse(BASE/"static"/filename)

@app.get("/api/status")
def status():
    try:
        configured=bool(get_key())
    except ValueError:
        configured=False
    return {"app":"Crypto Paper Lab","version":VERSION,"mode":"PAPER ONLY — nooit live orders",
            "coingecko_configured":configured,"strategies":STRATEGIES,
            "coins":{k:v[0] for k,v in COINS.items()},"storage":str(storage.data_dir()),
            "risk_per_trade_pct":.25,"max_exposure_pct":25,"max_daily_loss_pct":1,"max_drawdown_lock_pct":10}

class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    params: Params = Field(default_factory=Params)
    coingecko_plan: Literal["demo","pro"] = "demo"
    api_key: str | None = Field(default=None,max_length=512)
    remember_environment_key: bool = False

@app.get("/api/settings")
def settings():
    return storage.settings()

@app.post("/api/settings")
def set_settings(value:Settings):
    try:
        if value.api_key:
            save_key(value.api_key)
        elif value.remember_environment_key:
            key=get_key()
            if not key: raise ValueError("Er is geen API-sleutel ingesteld.")
            save_key(key)
        data=value.model_dump(exclude={"api_key","remember_environment_key"})
        storage.save_settings(data)
        return {"saved":True,"settings":data}
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc

@app.post("/api/backtest")
def backtest(p:Params):
    try:
        df=get_data(p)
        result=run_backtest(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100)
        payload={"meta":summary(df,p),"backtest":result,
                 "disclaimer":"Uitsluitend historische of synthetische simulatie; geen handelsorders."}
        run_id=storage.save_run("backtest",p.model_dump(),payload)
        return dict(payload,run_id=run_id)
    except (DataError,ValueError) as exc: raise HTTPException(422,str(exc)) from exc

@app.post("/api/research")
def compare(p:Params):
    try:
        df=get_data(p)
        payload={"meta":summary(df,p),"research":research(df,p.capital,p.fee_pct/100,p.slippage_pct/100)}
        return dict(payload,run_id=storage.save_run("research",p.model_dump(),payload))
    except (DataError,ValueError) as exc: raise HTTPException(422,str(exc)) from exc

class CSVImport(BaseModel):
    coin:str=Field(pattern="^[a-z0-9-]{1,60}$")
    text:str=Field(max_length=8_000_000)

@app.post("/api/datasets")
def dataset(value:CSVImport):
    try:
        if value.coin not in COINS: raise DataError("Niet toegestane munt.")
        df=import_csv(value.text,value.coin)
        dataset_id=storage.save_run("dataset",{"coin":value.coin},pack_candles(df))
        return {"dataset_id":dataset_id,"candles":len(df)}
    except (ValueError,DataError) as exc: raise HTTPException(422,str(exc)) from exc

def replay_payload(eng,meta,candles):
    return {"meta":meta,"snapshot":eng.snapshot(),"candles":candles}

@app.post("/api/replay/start")
def replay_start(p:Params):
    try:
        df=get_data(p)
        eng=PaperEngine(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100)
        meta=summary(df,p); candles=pack_candles(df)
        run_id=storage.save_run("replay",p.model_dump(),replay_payload(eng,meta,candles))
        with _lock:
            _sessions["local"]=(eng,meta,candles,run_id,p.model_dump())
        return {"meta":meta,"snapshot":eng.snapshot(),"run_id":run_id,"mode_note":"Historische replay, automatisch opgeslagen; geen live forward trading."}
    except (DataError,ValueError) as exc: raise HTTPException(422,str(exc)) from exc

class Step(BaseModel):
    steps:int=Field(default=1,ge=1,le=100)

@app.post("/api/replay/step")
def replay_step(p:Step):
    with _lock:
        if "local" not in _sessions: raise HTTPException(409,"Start of hervat eerst een replay.")
        eng,meta,candles,run_id,params=_sessions["local"]
        eng.step(p.steps)
        payload=replay_payload(eng,meta,candles)
        storage.save_run("replay",params,payload,run_id)
    return {"meta":meta,"snapshot":payload["snapshot"],"run_id":run_id}

@app.get("/api/runs")
def runs():
    return storage.list_runs()

def find_run(run_id):
    try: return storage.get_run(run_id)
    except KeyError: raise HTTPException(404,"Resultaat niet gevonden.")

@app.get("/api/runs/{run_id}")
def run_detail(run_id:str):
    row=find_run(run_id)
    # Candle archive needed for replay internally, not for displaying old results.
    row["payload"].pop("candles",None)
    return row

@app.post("/api/runs/{run_id}/resume")
def resume(run_id:str):
    row=find_run(run_id)
    if row["kind"]!="replay": raise HTTPException(422,"Dit is geen replay.")
    p=Params(**row["params"]); payload=row["payload"]
    df=unpack_candles(payload["candles"])
    eng=PaperEngine(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100)
    eng.step(payload["snapshot"]["progress"])
    with _lock:
        _sessions["local"]=(eng,payload["meta"],payload["candles"],run_id,p.model_dump())
    return {"meta":payload["meta"],"snapshot":eng.snapshot(),"run_id":run_id}

@app.get("/api/export/{kind}")
def export(kind:Literal["backtest","replay"], run_id:str|None=None):
    if run_id:
        row=find_run(run_id)
    else:
        row=next((find_run(x["id"]) for x in storage.list_runs(1000) if x["kind"]==kind),None)
    if not row or row["kind"]!=kind: raise HTTPException(404,"Geen resultaat.")
    payload=row["payload"]
    rows=payload["snapshot"]["trades"] if kind=="replay" else [
        dict(t,segment=label) for label in ("train","test") for t in payload["backtest"][label]["trades"]]
    if not rows: raise HTTPException(404,"Geen transacties om te exporteren.")
    fp=io.StringIO()
    writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    return StreamingResponse(io.BytesIO(fp.getvalue().encode("utf-8-sig")),media_type="text/csv",
        headers={"Content-Disposition":f'attachment; filename="paper_{kind}_journal.csv"'})

@app.get("/api/updates")
def updates():
    try: return updater.check()
    except (ValueError, OSError, __import__("subprocess").TimeoutExpired) as exc:
        raise HTTPException(503,str(exc) if isinstance(exc,ValueError) else "Updatecontrole mislukt; controleer GitHub CLI.") from exc

@app.post("/api/updates/stage")
def stage_update():
    try: return updater.stage()
    except (ValueError, OSError, __import__("subprocess").TimeoutExpired) as exc:
        raise HTTPException(503,str(exc) if isinstance(exc,ValueError) else "Update downloaden mislukt.") from exc

