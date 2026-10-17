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
from market_data import (CoinGeckoProvider, KrakenProvider, HistoricalProvider, demo_candles, DataError,
                         COINS, pack_candles, unpack_candles, import_csv)
from engine import PaperEngine, run_backtest, direction_breakdown
from strategies import STRATEGIES, StrategyConfig
import storage
from secrets_store import get_key, save_key
import updater
from protocol import protocol_coin,COHORT,reference_params
from research import auto_tune,filter_experiment,bot_arena,research, walk_forward

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
    source: Literal["demo","coingecko","kraken","historical","csv"] = "demo"
    coin: str = Field(default="bitcoin", pattern="^[a-z0-9-]{1,60}$")
    strategy: Literal["ema","rsi","breakout"] = "ema"
    days: Literal[7,14,30,90,180,365,730,1095,1825] = 30
    interval: Literal[60,240,1440] = 1440
    parameters: StrategyConfig = Field(default_factory=StrategyConfig)
    dataset_id: str | None = Field(default=None, pattern="^[a-f0-9]{32}$")
    capital: float = Field(default=10000,ge=100,le=1e7,allow_inf_nan=False)
    fee_pct: float = Field(default=.10,ge=0,le=1,allow_inf_nan=False)
    slippage_pct: float = Field(default=.05,ge=0,le=2,allow_inf_nan=False)

def get_data(p,progress=None):
    if p.coin not in COINS:
        raise DataError("Niet toegestane munt.")
    if p.source=="demo":
        return demo_candles(p.coin,360)
    if p.source=="historical":
        return HistoricalProvider().candles(p.coin,p.days,p.interval,progress)
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
    return {"source":df.attrs.get("source"),"coin":p.coin,"strategy":p.strategy,"trade_mode":p.parameters.trade_mode,
            "volume_is_actual":df.attrs.get("volume_is_actual",False),
            "quote":df.attrs.get("quote","USD"),"requested_days":p.days,"synthetic":p.source=="demo", "timeframe":df.attrs.get("timeframe",df.attrs.get("time_frame","onbekend")),
            "note":df.attrs.get("note", "Synthetische demonstratiedata; geen echte historische koersen." if p.source=="demo" else "CoinGecko bepaalt candle-intervallen automatisch; langere periode betekent niet noodzakelijk meer candles."),
            "gaps_detected": bool(len(gaps) and (gaps > gaps.median()*1.5).any()),
            "candle_count":len(df),"from":df.iloc[0].time.isoformat(),"to":df.iloc[-1].time.isoformat(),
            "chart_sampled":len(df)>1500,"price_data":[{"time":r.time.isoformat(),"close":round(float(r.close),5)} for r in df.iloc[sorted(set(range(0,len(df),max(1,len(df)//1499)))|{len(df)-1})].itertuples()]}

@app.get("/")
def index():
    return FileResponse(BASE/"static/index.html",headers={"Cache-Control":"no-store"})

@app.get("/static/{filename}")
def static(filename:str):
    if filename not in {"app.js","style.css"}: raise HTTPException(404)
    return FileResponse(BASE/"static"/filename,headers={"Cache-Control":"no-store"})

@app.get("/api/status")
def status():
    try:
        configured=bool(get_key())
    except ValueError:
        configured=False
    return {"app":"Crypto Paper Lab","version":VERSION,"mode":"PAPER ONLY — nooit live orders",
            "coingecko_configured":configured,"strategies":STRATEGIES,
            "coins":{k:v[0] for k,v in COINS.items()},"storage":str(storage.data_dir()),
            "supported_directions":["long","short","both"],"risk_per_trade_pct":.25,"max_exposure_pct":25,"max_daily_loss_pct":1,"max_drawdown_lock_pct":10}

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
        result=run_backtest(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,parameters=p.parameters)
        payload={"meta":summary(df,p),"backtest":result,
                 "disclaimer":"Uitsluitend historische of synthetische simulatie; geen handelsorders."}
        run_id=storage.save_run("backtest",p.model_dump(),payload)
        return dict(payload,run_id=run_id)
    except (DataError,ValueError) as exc: raise HTTPException(422,str(exc)) from exc

@app.post("/api/research")
def compare(p:Params):
    try:
        df=get_data(p)
        payload={"meta":summary(df,p),"research":research(df,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters)}
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
    return {"meta":meta,"snapshot":eng.snapshot(),"candles":candles,"engine_format":"long-short-v1"}

@app.post("/api/replay/start")
def replay_start(p:Params):
    try:
        df=get_data(p)
        eng=PaperEngine(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,parameters=p.parameters)
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
    # Enrich legacy runs only when their actual trade journals were retained.
    payload=row["payload"]
    capital=float(row["params"].get("capital",10000))
    snapshots=list(payload.get("backtest",{}).values()) if row["kind"]=="backtest" else [payload.get("snapshot",{})] if row["kind"]=="replay" else []
    for snap in snapshots:
        if isinstance(snap,dict) and "trades" in snap and "metrics" in snap:
            snap["metrics"].setdefault("direction_breakdown",direction_breakdown(snap["trades"],capital))
    # Candle archive needed for replay internally, not for displaying old results.
    row["payload"].pop("candles",None)
    return row

@app.post("/api/runs/{run_id}/resume")
def resume(run_id:str):
    row=find_run(run_id)
    if row["kind"]!="replay": raise HTTPException(422,"Dit is geen replay.")
    p=Params(**row["params"]); payload=row["payload"]
    if payload.get("engine_format")!="long-short-v1":raise HTTPException(409,"Oud replaymodel: het opgeslagen resultaat blijft beschikbaar. Start een nieuwe replay voor de huidige engine.")
    df=unpack_candles(payload["candles"])
    eng=PaperEngine(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,parameters=p.parameters)
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



# Long history and repeated strategy tests run in one background worker.
# Existing results persist; unfinished jobs stop when the server stops.
from concurrent.futures import ThreadPoolExecutor
import uuid
_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix="paper-research")
_jobs={}
_jobs_lock=RLock()

class ResearchJob(BaseModel):
    model_config=ConfigDict(extra="forbid")
    params:Params=Field(default_factory=Params)
    mode:Literal["compare","walkforward","batch","arena","filters","tune","protocol"]="walkforward"
    coins:list[str]=Field(default_factory=list,max_length=4)

def execute_job(job_id,request):
    def progress(message):
        with _jobs_lock:_jobs[job_id]["message"]=message
    try:
        p=request.params
        if request.mode=="compare":
            df=get_data(p,progress)
            progress("Strategieën vergelijken.")
            payload={"meta":summary(df,p),"research":research(df,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters)}
            kind="research"
        elif request.mode=="protocol":
            p=p.model_copy(update={"source":"historical","days":1095,"interval":240,"strategy":"ema",
                                   "parameters":StrategyConfig(**reference_params(p.parameters.short_borrow_daily_pct)),"dataset_id":None})
            request.params=p
            datasets={};errors={};results=[]
            for coin in COHORT:
                item=p.model_copy(update={"coin":coin})
                try:datasets[coin]=get_data(item,lambda m:progress(coin+": "+m))
                except (ValueError,DataError) as exc:errors[coin]=str(exc)
            common_left=max((d.time.min() for d in datasets.values()),default=None)
            common_right=min((d.time.max() for d in datasets.values()),default=None)
            for coin in COHORT:
                if coin in errors:
                    results.append({"coin":coin,"error":errors[coin]});continue
                item=p.model_copy(update={"coin":coin});df=datasets[coin]
                df=df[(df.time>=common_left)&(df.time<=common_right)].reset_index(drop=True)
                try:
                    result=protocol_coin(df,item.capital,item.fee_pct,item.slippage_pct,item.parameters.short_borrow_daily_pct,lambda m:progress(coin+": "+m))
                    result["notes"].append("Beschikbare coins zijn begrensd tot dezelfde begin- en eindtijd. Gaten kunnen aantallen en exacte splits nog laten verschillen.")
                    results.append({"coin":coin,"meta":summary(df,item),"protocol":result})
                except (ValueError,DataError) as exc:results.append({"coin":coin,"error":str(exc)})
            if not any("protocol" in x for x in results):raise ValueError("Geen coin kon worden getest: "+"; ".join(x["coin"]+": "+x["error"] for x in results))
            payload={"protocol_batch":results,"params":p.model_dump()}
            kind="protocol"
        elif request.mode=="tune":
            df=get_data(p,progress)
            payload={"meta":summary(df,p),"tuning":auto_tune(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters,progress),"params":p.model_dump()}
            kind="tune"
        elif request.mode=="filters":
            df=get_data(p,progress)
            payload={"meta":summary(df,p),"filters":filter_experiment(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters,progress),"params":p.model_dump()}
            kind="filters"
        elif request.mode=="arena":
            df=get_data(p,progress)
            payload={"meta":summary(df,p),"arena":bot_arena(df,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters,progress),"params":p.model_dump()}
            kind="arena"
        elif request.mode=="walkforward":
            df=get_data(p,progress)
            payload={"meta":summary(df,p),"walkforward":walk_forward(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100,p.parameters,progress)}
            kind="walkforward"
        else:
            if p.source not in {"historical","kraken","coingecko"}:
                raise ValueError("Vergelijk meerdere coins met een echte API-databron.")
            coins=list(dict.fromkeys(request.coins or [p.coin]))
            results=[]
            for i,coin in enumerate(coins):
                progress(f"Coin {i+1}/{len(coins)}: {coin}")
                item=p.model_copy(update={"coin":coin})
                try:
                    df=get_data(item,lambda m:progress(coin+": "+m))
                    result=walk_forward(df,item.strategy,item.capital,item.fee_pct/100,item.slippage_pct/100,item.parameters)
                    results.append({"coin":coin,"meta":summary(df,item),"walkforward":result})
                except (ValueError,DataError) as exc:
                    results.append({"coin":coin,"error":str(exc)})
            if not any("walkforward" in x for x in results):
                raise ValueError("Geen coin kon worden getest: "+"; ".join(x["coin"]+": "+x["error"] for x in results))
            payload={"batch":results,"notes":["Iedere coin heeft een eigen chronologische test. Dit is geen gecombineerd portfolio.",
                                             "Ook mislukte coins blijven zichtbaar; er is geen selectie van alleen succesvolle tests."]}
            kind="batch"
        record=storage.save_run(kind,request.params.model_dump(),payload)
        with _jobs_lock:_jobs[job_id].update(status="done",message="Onderzoek bewaard.",run_id=record)
    except Exception as exc:
        with _jobs_lock:_jobs[job_id].update(status="failed",message=str(exc) if isinstance(exc,(ValueError,DataError)) else "Onderzoek mislukt. Controleer de servermelding en databron.")

@app.post("/api/research/jobs")
def start_job(request:ResearchJob):
    if any(coin not in COINS for coin in request.coins):raise HTTPException(422,"Onbekende coin.")
    with _jobs_lock:
        if any(x["status"]=="running" for x in _jobs.values()):raise HTTPException(409,"Er loopt al een onderzoek. Wacht tot het klaar is.")
        if len(_jobs)>=20:_jobs.pop(next(iter(_jobs)))
        job_id=uuid.uuid4().hex
        _jobs[job_id]={"id":job_id,"status":"running","message":"Onderzoek gestart."}
    _pool.submit(execute_job,job_id,request)
    return {"id":job_id}

@app.get("/api/research/jobs/{job_id}")
def job_status(job_id:str):
    with _jobs_lock:
        if job_id not in _jobs:raise HTTPException(404,"Taak niet gevonden; mogelijk is de server herstart. Eerdere resultaten staan bij Opgeslagen onderzoeken.")
        return dict(_jobs[job_id])




