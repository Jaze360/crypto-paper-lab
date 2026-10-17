"""Deterministic, long-only PAPER trading; no broker API or real order path."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import math
import numpy as np
import pandas as pd
from strategies import add_indicators,signal,STRATEGIES

RISK_PER_TRADE = 0.0025  # 0.25%, educational policy hardcap
MAX_EXPOSURE = 0.25     # 25% of current equity
MAX_DAILY_LOSS = 0.01   # block new entries for the day
MAX_DRAWDOWN = 0.10     # permanent block when breached

@dataclass
class Position:
    entry_time: str
    entry: float
    qty: float
    stop: float
    target: float
    fee_paid: float
    signal_index: int

class PaperEngine:
    def __init__(self, candles:pd.DataFrame, strategy:str="ema", capital:float=10000.0, fee:float=0.001, slip:float=0.0005, start:int=0, end:Optional[int]=None):
        if strategy not in STRATEGIES: raise ValueError("Onbekende strategie")
        if strategy=="breakout" and not candles.attrs.get("volume_is_actual",False):
            raise ValueError("Volume-breakout vereist echt candlevolume; CoinGecko OHLC heeft dat niet.")
        if capital<=0 or not(0<=fee<=.01) or not(0<=slip<=.02):raise ValueError("Ongeldige parameters")
        self.d=add_indicators(candles)
        self.strategy=strategy;self.capital=float(capital);self.fee=fee;self.slip=slip
        self.start=int(start);self.end=len(self.d) if end is None else min(int(end),len(self.d))
        self.idx=self.start;self.cash=float(capital);self.position=None
        self.peak=capital;self.locked=False;self.current_day=None;self.start_day_equity=capital
        self.equity_points=[];self.trades=[];self.events=[]
        self.last_price=None;self.max_dd=0

    def equity(self, mark:float)->float:
        return self.cash + (self.position.qty*mark if self.position else 0)

    def _close(self, stamp:str, raw:float, reason:str):
        p=self.position
        if p is None:return
        fill=raw*(1-self.slip)
        fee=fill*p.qty*self.fee
        self.cash+=fill*p.qty-fee
        net=(fill-p.entry)*p.qty-p.fee_paid-fee
        trade={"entry_time":p.entry_time,"exit_time":stamp,"entry":round(p.entry,6),"exit":round(fill,6),
               "qty":round(p.qty,8),"pnl":round(net,4),"pnl_R":round(net / max(1e-9, (p.entry-p.stop)*p.qty+p.fee_paid),3),
               "fees":round(fee+p.fee_paid,4),"reason":reason,"strategy":self.strategy}
        self.trades.append(trade);self.events.append({"type":"SELL (PAPER)","time":stamp,"price":fill,"reason":reason})
        self.position=None

    def _entry(self, i:int, stamp:str, raw_open:float, atr:float):
        if not math.isfinite(atr) or atr<=0:return
        fill=raw_open*(1+self.slip)
        stop=fill-1.5*atr
        if stop<=0:return
        target=fill+3.0*atr
        # Buffer includes both entry and exit fees and slippage at stop, so planned loss <= risk budget.
        worst_exit=stop*(1-self.slip)
        unit_loss=max(1e-9,fill-worst_exit+self.fee*(fill+worst_exit))
        budget=self.equity(raw_open)*RISK_PER_TRADE
        qty=min(budget/unit_loss,self.equity(raw_open)*MAX_EXPOSURE/(fill*(1+self.fee)),self.cash/(fill*(1+self.fee)))
        qty=math.floor(qty * 1e8)/1e8
        if qty*fill<10:return
        fee=qty*fill*self.fee
        self.cash-=qty*fill+fee
        self.position=Position(stamp,fill,qty,stop,target,fee,i-1)
        self.events.append({"type":"BUY (PAPER)","time":stamp,"price":fill,"reason":"Signaal vorige gesloten candle"})

    def step(self, steps:int=1):
        for _ in range(max(0,int(steps))):
            if self.idx>=self.end:break
            i=self.idx; row=self.d.iloc[i]; stamp=row.time.isoformat();day=str(row.time.date())
            # 1. Evaluate existing position using only prior candle signal and current candle open.
            if self.current_day != day:
                self.current_day=day;self.start_day_equity=self.equity(float(row.open))
            _,should_exit=signal(self.d,i-1,self.strategy)
            if self.position and should_exit:
                self._close(stamp,float(row.open),"Strategie exit vorige candle")
            # 2. Process existing stop or target using current candle OHLC; uncertain both => stop-first.
            if self.position:
                p=self.position
                if row.open<=p.stop:self._close(stamp,float(row.open),"Gap onder stop")
                elif row.open>=p.target:self._close(stamp,float(row.open),"Gap boven target")
                elif row.low<=p.stop:self._close(stamp,p.stop,"Stop-loss")
                elif row.high>=p.target:self._close(stamp,p.target,"Take-profit")
            # 3. Update kill switches *before* deciding to open a new position.
            eq=self.equity(float(row.open));self.peak=max(self.peak,eq)
            self.max_dd=max(self.max_dd, (self.peak-eq)/self.peak)
            if self.max_dd>=MAX_DRAWDOWN:self.locked=True
            daily_block=(eq < self.start_day_equity*(1-MAX_DAILY_LOSS))
            should_enter,_=signal(self.d,i-1,self.strategy)
            if not self.position and should_enter and not self.locked and not daily_block:
                prev_atr=float(self.d.iloc[i-1].atr)
                self._entry(i,stamp,float(row.open),prev_atr)
                # Conservative same-bar stop if bar traverses both entry and stop.
                if self.position and row.low<=self.position.stop:
                    self._close(stamp,self.position.stop,"Stop op instapcandle")
                elif self.position and row.high>=self.position.target:
                    self._close(stamp,self.position.target,"Target op instapcandle")
            eq=self.equity(float(row.close));self.peak=max(self.peak,eq)
            self.max_dd=max(self.max_dd,(self.peak-eq)/self.peak)
            if self.max_dd>=MAX_DRAWDOWN:self.locked=True
            self.equity_points.append({"time":stamp,"equity":round(eq,4),"close":float(row.close)})
            self.idx+=1;self.last_price=float(row.close)
        return self.snapshot()

    def finish(self):
        self.step(self.end-self.idx)
        if self.position:
            last=self.d.iloc[self.end-1];self._close(last.time.isoformat(),float(last.close),"Testperiode einde")
            if self.equity_points:self.equity_points[-1]["equity"]=round(self.cash,4)
        return self.snapshot()

    def snapshot(self):
        mark=self.last_price or (float(self.d.iloc[self.idx-1].close) if self.idx>self.start else float(self.d.iloc[self.start].open))
        eq=self.equity(mark);pnl=eq-self.capital
        completed=self.idx>=self.end
        return {"strategy":self.strategy,"completed":completed,"progress":self.idx-self.start,"total":self.end-self.start,
                "initial_capital":self.capital,"equity":round(eq,2),"return_pct":round(pnl/self.capital*100,3),
                "cash":round(self.cash,2),"max_drawdown_pct":round(self.max_dd*100,3),
                "locked":self.locked,"open_position":asdict(self.position) if self.position else None,
                "metrics":metrics(self.trades,self.capital,eq,self.max_dd),
                "equity_curve":self.equity_points,"trades":self.trades,"events":self.events[-15:]}


def metrics(trades,capital,equity,max_dd):
    closed=len(trades)
    profits=[float(x['pnl']) for x in trades]
    wins=[p for p in profits if p>0];losses=[p for p in profits if p<0]
    sum_l=-sum(losses)
    return {"trades":closed,"winrate_pct":round(100*len(wins)/closed,2) if closed else None,
            "avg_net_pnl":round(sum(profits)/closed,2) if closed else None,
            "expectancy_R":round(float(np.mean([t['pnl_R'] for t in trades])),3) if closed else None,
            "profit_factor":round(sum(wins)/sum_l,3) if sum_l else None,
            "net_pnl":round(sum(profits),2),"return_pct":round((equity/capital-1)*100,3),
            "max_drawdown_pct":round(max_dd*100,3)}


def run_backtest(candles, strategy="ema",capital=10000,fee=.001,slip=.0005, split=.70):
    n=len(candles)
    cut=round(n*split)
    if cut<40 or n-cut<20:raise ValueError("Te weinig candles voor een eerlijke train/test-split")
    # Full history used as backward-only indicator warmup, positions and cash reset at test boundary.
    train=PaperEngine(candles,strategy,capital,fee,slip,start=0,end=cut).finish()
    test=PaperEngine(candles,strategy,capital,fee,slip,start=cut,end=n).finish()
    warnings=[]
    for name,result in (("train",train),("out-of-sample",test)):
        if result['metrics']['trades']<30:
            warnings.append(f"{name}: slechts {result['metrics']['trades']} transacties; onvoldoende om betrouwbaarheid vast te stellen")
    warnings.append("Train/test = geen optimalisatie of bewijs van winstgevendheid; historische resultaten zijn indicatief.")
    warnings.append("OHLC-volgorde intrabar is onbekend; bij stop én target wordt conservatief de stop genomen.")
    return {"train":train,"test":test,"split_index":cut,"total_candles":n,"warnings":warnings}
