"""Crypto Paper Lab: 100% simulation. Never sends exchange or broker orders."""
from __future__ import annotations
import csv
import io
import os
from pathlib import Path
from threading import RLock
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from market_data import CoinGeckoProvider, demo_candles, DataError
from engine import PaperEngine, run_backtest
from strategies import STRATEGIES

BASE = Path(__file__).parent
app = FastAPI(title="Crypto Paper Lab — UITSLUITEND SIMULATIE",version="0.1.0")
_sessions = {}
_history = {}
_lock=RLock()

class Params(BaseModel):
    source: Literal["demo","coingecko"] = "demo"
    coin: Literal["bitcoin","ethereum","solana"] = "bitcoin"
    strategy: Literal["ema","rsi","breakout"] = "ema"
    days: Literal[7,14,30] = 30
    capital: float = Field(default=10000,ge=100,le=1e7)
    fee_pct: float = Field(default=0.10,ge=0,le=1)
    slippage_pct: float = Field(default=0.05,ge=0,le=2)

def get_data(p:Params):
    if p.source=="demo":
        return demo_candles(p.coin,360)
    return CoinGeckoProvider().candles(p.coin,p.days)

def summary(df,p):
    return {"source":df.attrs.get("source"),"coin":p.coin,"strategy":p.strategy,
            "volume_is_actual":df.attrs.get("volume_is_actual",False),
            "candle_count":len(df),"from":df.iloc[0].time.isoformat(),"to":df.iloc[-1].time.isoformat(),
            "price_data":[{"time":r.time.isoformat(),"close":round(float(r.close),5)} for r in df.itertuples()]}

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/static/{filename}")
def static(filename:str):
    if filename not in {"app.js","style.css"}:raise HTTPException(404,"Niet gevonden")
    return FileResponse(BASE / "static" / filename)

@app.get("/api/status")
def status():
    return {"app":"Crypto Paper Lab","mode":"PAPER ONLY — nooit live orders", "coingecko_configured":bool(os.getenv("COINGECKO_API_KEY")),
            "strategies":STRATEGIES,"risk_per_trade_pct":0.25,"max_exposure_pct":25,
            "max_daily_loss_pct":1,"max_drawdown_lock_pct":10}

@app.post("/api/backtest")
def backtest(p:Params):
    try:
        df=get_data(p)
        result=run_backtest(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100)
    except (DataError,ValueError) as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc
    with _lock:
        _history["backtest"] = ([dict(trade, segment="ontwikkeling") for trade in result["train"]["trades"]]
                                + [dict(trade, segment="out-of-sample") for trade in result["test"]["trades"]])
    return {"meta":summary(df,p),"backtest":result,
            "disclaimer":"Synthetisch of historisch; nooit een bewezen handelsvoordeel. Geen orders bij een broker."}

@app.post("/api/replay/start")
def replay_start(p:Params):
    try:
        df=get_data(p)
        engine=PaperEngine(df,p.strategy,p.capital,p.fee_pct/100,p.slippage_pct/100)
    except (DataError,ValueError) as exc:raise HTTPException(422,detail=str(exc)) from exc
    with _lock:
        _sessions["local"]=(engine,summary(df,p))
        _history["replay"]=[]
    return {"meta":summary(df,p),"snapshot":engine.snapshot(),
            "mode_note":"HISTORISCHE REPLAY: geen live forward paper trading. Candles worden stap voor stap opnieuw afgespeeld."}

class Step(BaseModel):
    steps: int = Field(default=1,ge=1,le=100)

@app.post("/api/replay/step")
def replay_step(p:Step):
    with _lock:
        if "local" not in _sessions:raise HTTPException(409,"Start eerst een replay")
        eng,meta=_sessions["local"]
        snap=eng.step(p.steps)
        _history["replay"]=snap['trades']
    return {"meta":meta,"snapshot":snap}

@app.get("/api/export/{kind}")
def export(kind:Literal["backtest","replay"]):
    with _lock:
        rows=list(_history.get(kind,[]))
    if not rows:raise HTTPException(404,"Geen transacties om te exporteren")
    fp=io.StringIO();fields=list(rows[0].keys());writer=csv.DictWriter(fp,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
    result=io.BytesIO(fp.getvalue().encode("utf-8-sig"))
    return StreamingResponse(result,media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="paper_{kind}_journal.csv"'})
