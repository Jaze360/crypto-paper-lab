"""Long/short PAPER engine with reserved collateral. No broker or live order path."""
from dataclasses import dataclass,asdict
import math
import numpy as np
from strategies import add_indicators,signals,short_signals,config,STRATEGIES

RISK_PER_TRADE=.0025
MAX_EXPOSURE=.25
MAX_DAILY_LOSS=.01
MAX_DRAWDOWN=.10

@dataclass
class Position:
    entry_time:str
    entry:float
    qty:float
    stop:float
    target:float
    fee_paid:float
    signal_index:int
    side:str="long"
    collateral:float=0.
    borrow_paid:float=0.
    planned_risk:float=0.
    held_bars:int=0

class PaperEngine:
    def __init__(self,candles,strategy="ema",capital=10000.,fee=.001,slip=.0005,start=0,end=None,parameters=None):
        if strategy not in STRATEGIES:raise ValueError("Onbekende strategie")
        if strategy=="breakout" and not candles.attrs.get("volume_is_actual",False):
            raise ValueError("Volume-breakout vereist echt candlevolume; CoinGecko OHLC heeft dat niet.")
        if capital<=0 or not(0<=fee<=.01) or not(0<=slip<=.02):raise ValueError("Ongeldige parameters")
        self.parameters=config(parameters)
        self.d=add_indicators(candles,self.parameters)
        self.rows=list(self.d.itertuples(index=False))
        self.entry_signals,self.exit_signals=signals(self.d,strategy)
        self.short_entry_signals,self.short_exit_signals=short_signals(self.d,strategy)
        differences=self.d.time.diff().dropna().dt.total_seconds().to_numpy()
        self.default_seconds=float(np.median(differences)) if len(differences) else 86400.
        self.active_bars=0;self.short_bars=0;self.exposure_sum=0.;self.max_exposure=0.;self.holding_bars=[]
        self.total_borrow=0.;self._record=True
        self.strategy=strategy;self.capital=float(capital);self.fee=fee;self.slip=slip
        self.start=int(start);self.end=len(self.d) if end is None else min(int(end),len(self.d))
        if not 0<=self.start<self.end:raise ValueError("Ongeldige candleperiode.")
        self.idx=self.start;self.cash=float(capital);self.position=None
        self.peak=capital;self.locked=False;self.current_day=None;self.start_day_equity=capital
        self.equity_points=[];self.trades=[];self.events=[]
        self.last_price=None;self.max_dd=0.

    def equity(self,mark):
        p=self.position
        if p is None:return self.cash
        if p.side=="long":return self.cash+p.qty*mark
        return self.cash+p.collateral+(p.entry-mark)*p.qty

    def bar_days(self,index):
        if index+1<len(self.rows):
            return max(0.,(self.rows[index+1].time-self.rows[index].time).total_seconds()/86400.)
        return self.default_seconds/86400.

    def _close(self,stamp,raw,reason):
        p=self.position
        if p is None:return
        sign=1 if p.side=="long" else -1
        fill=raw*(1-self.slip*sign)
        fee=fill*p.qty*self.fee
        gross=(fill-p.entry)*p.qty*sign
        self.cash+=(fill*p.qty if p.side=="long" else p.collateral+gross)-fee
        net=gross-p.fee_paid-fee-p.borrow_paid
        risk=p.planned_risk or (abs(p.entry-p.stop)*p.qty+p.fee_paid)
        trade={"entry_time":p.entry_time,"exit_time":stamp,"side":p.side,
               "entry":round(p.entry,6),"exit":round(fill,6),"qty":round(p.qty,8),
               "pnl":round(net,4),"pnl_R":round(net/max(1e-9,risk),3),
               "fees":round(fee+p.fee_paid,4),"borrow_cost":round(p.borrow_paid,6),
               "holding_bars":p.held_bars,"reason":reason,"strategy":self.strategy}
        self.holding_bars.append(p.held_bars)
        self.trades.append(trade)
        self.events.append({"type":("SELL LONG" if p.side=="long" else "COVER SHORT")+" (PAPER)",
                            "time":stamp,"price":fill,"reason":reason})
        self.position=None

    def _entry(self,i,stamp,raw_open,atr,side="long"):
        if self.position is not None or not math.isfinite(atr) or atr<=0:return
        if side not in ("long","short"):raise ValueError("Ongeldige richting.")
        sign=1 if side=="long" else -1
        fill=raw_open*(1+self.slip*sign)
        stop=fill-sign*self.parameters.stop_atr*atr
        target=fill+sign*self.parameters.target_atr*atr
        if stop<=0 or target<=0:return
        worst_exit=stop*(1-self.slip*sign)
        one_bar_carry=fill*self.parameters.short_borrow_daily_pct/100*self.bar_days(i) if side=="short" else 0.
        unit_loss=abs(fill-worst_exit)+self.fee*(fill+worst_exit)+one_bar_carry
        eq=self.equity(raw_open)
        if eq<=0:return
        qty=min(eq*RISK_PER_TRADE/max(unit_loss,1e-9),eq*MAX_EXPOSURE/(fill*(1+self.fee)),
                self.cash/(fill*(1+self.fee)))
        qty=math.floor(qty*1e8)/1e8
        if qty*fill<10:return
        fee=qty*fill*self.fee
        # Shorts reserve 100% entry notional. Sale proceeds are never spendable cash.
        self.cash-=qty*fill+fee
        self.position=Position(stamp,fill,qty,stop,target,fee,i-1,side,
                               qty*fill if side=="short" else 0.,0.,qty*unit_loss)
        self.events.append({"type":("BUY LONG" if side=="long" else "OPEN SHORT")+" (PAPER)",
                            "time":stamp,"price":fill,"reason":"Signaal vorige gesloten candle"})

    def charge_borrow(self,i):
        p=self.position
        if p is not None and p.side=="short":
            charge=p.entry*p.qty*self.parameters.short_borrow_daily_pct/100*self.bar_days(i)
            self.cash-=charge;p.borrow_paid+=charge;self.total_borrow+=charge

    def update_risk(self,mark):
        eq=self.equity(mark);self.peak=max(self.peak,eq)
        self.max_dd=max(self.max_dd,(self.peak-eq)/self.peak)
        if eq<=0 or self.max_dd>=MAX_DRAWDOWN:self.locked=True
        return eq

    def step(self,steps=1,snapshot=True):
        for _ in range(max(0,int(steps))):
            if self.idx>=self.end:break
            i=self.idx;row=self.rows[i];stamp=row.time.isoformat();day=str(row.time.date())
            if self.current_day!=day:
                self.current_day=day;self.start_day_equity=self.equity(float(row.open))
            # Overnight gaps are handled at actual open, even if a signal also exits.
            if self.position:
                p=self.position
                stop_gap=row.open<=p.stop if p.side=="long" else row.open>=p.stop
                target_gap=row.open>=p.target if p.side=="long" else row.open<=p.target
                if stop_gap:self._close(stamp,float(row.open),"Gap voorbij stop")
                elif target_gap:self._close(stamp,float(row.open),"Gap voorbij target")
            if self.position and i>0:
                leave=self.exit_signals[i-1] if self.position.side=="long" else self.short_exit_signals[i-1]
                if leave:self._close(stamp,float(row.open),"Strategie exit vorige candle")
            eq=self.update_risk(float(row.open))
            daily_block=eq<self.start_day_equity*(1-MAX_DAILY_LOSS)
            long_signal=bool(i>0 and self.entry_signals[i-1] and self.parameters.trade_mode in ("long","both"))
            short_signal=bool(i>0 and self.short_entry_signals[i-1] and self.parameters.trade_mode in ("short","both"))
            if not self.position and not self.locked and not daily_block and long_signal!=short_signal:
                self._entry(i,stamp,float(row.open),float(self.rows[i-1].atr),"long" if long_signal else "short")
            exposure=self.position.qty*float(row.open)/max(self.equity(float(row.open)),1e-9) if self.position else 0.
            if self.position:
                self.active_bars+=1;self.position.held_bars+=1
                if self.position.side=="short":self.short_bars+=1
            self.exposure_sum+=exposure;self.max_exposure=max(self.max_exposure,exposure)
            # Conservative full-candle borrow charge, including an intrabar stop/target.
            self.charge_borrow(i)
            if self.position:
                p=self.position
                stop_hit=row.low<=p.stop if p.side=="long" else row.high>=p.stop
                target_hit=row.high>=p.target if p.side=="long" else row.low<=p.target
                if stop_hit:self._close(stamp,p.stop,"Stop-loss")
                elif target_hit:self._close(stamp,p.target,"Take-profit")
            eq=self.update_risk(float(row.close))
            if self._record:self.equity_points.append({"time":stamp,"equity":round(eq,4),"close":float(row.close)})
            self.idx+=1;self.last_price=float(row.close)
        return self.snapshot() if snapshot else None

    def finish(self,record=True):
        self._record=record
        self.step(self.end-self.idx,snapshot=False)
        if self.position:
            last=self.rows[self.end-1];self._close(last.time.isoformat(),float(last.close),"Testperiode einde")
            self.update_risk(float(last.close))
            if self.equity_points:self.equity_points[-1]["equity"]=round(self.cash,4)
        return self.snapshot()

    def snapshot(self):
        mark=self.last_price or float(self.rows[self.start].open)
        eq=self.equity(mark);stats=metrics(self.trades,self.capital,eq,self.max_dd)
        processed=max(1,self.idx-self.start)
        stats.update(time_in_market_pct=round(100*self.active_bars/processed,3),
                     time_short_pct=round(100*self.short_bars/processed,3),
                     avg_exposure_pct=round(100*self.exposure_sum/processed,3),
                     max_exposure_pct=round(100*self.max_exposure,3),
                     avg_holding_bars=round(float(np.mean(self.holding_bars)),2) if self.holding_bars else None,
                     total_borrow_cost=round(self.total_borrow,6))
        return {"strategy":self.strategy,"completed":self.idx>=self.end,"progress":self.idx-self.start,"total":self.end-self.start,
                "initial_capital":self.capital,"equity":round(eq,2),"return_pct":round((eq/self.capital-1)*100,3),
                "cash":round(self.cash,2),"reserved_collateral":round(self.position.collateral,2) if self.position else 0.,"max_drawdown_pct":round(self.max_dd*100,3),"locked":self.locked,
                "open_position":asdict(self.position) if self.position else None,"parameters":self.parameters.model_dump(),
                "metrics":stats,"equity_curve":self.equity_points,"trades":self.trades,"events":self.events[-15:]}

def metrics(trades,capital,equity,max_dd):
    profits=[float(t["pnl"]) for t in trades];wins=[p for p in profits if p>0];losses=[p for p in profits if p<0]
    n=len(trades);sum_l=-sum(losses)
    return {"trades":n,"long_trades":sum(t.get("side","long")=="long" for t in trades),
            "short_trades":sum(t.get("side")=="short" for t in trades),
            "winrate_pct":round(100*len(wins)/n,2) if n else None,
            "avg_net_pnl":round(sum(profits)/n,2) if n else None,
            "expectancy_R":round(float(np.mean([t["pnl_R"] for t in trades])),3) if n else None,
            "profit_factor":round(sum(wins)/sum_l,3) if sum_l else None,
            "net_pnl":round(sum(profits),2),"return_pct":round((equity/capital-1)*100,3),
            "max_drawdown_pct":round(max_dd*100,3)}

def run_backtest(candles,strategy="ema",capital=10000,fee=.001,slip=.0005,split=.70,parameters=None):
    n=len(candles);cut=round(n*split)
    if cut<40 or n-cut<20:raise ValueError("Te weinig candles voor een eerlijke train/test-split")
    train=PaperEngine(candles,strategy,capital,fee,slip,start=0,end=cut,parameters=parameters).finish()
    test=PaperEngine(candles,strategy,capital,fee,slip,start=cut,end=n,parameters=parameters).finish()
    warnings=[]
    for name,result in (("train",train),("out-of-sample",test)):
        if result["metrics"]["trades"]<30:warnings.append(f"{name}: slechts {result['metrics']['trades']} transacties; onvoldoende bewijs")
    warnings.extend(["Geen bewijs van winstgevendheid; resultaten zijn simulaties.",
                     "Bij stop en target in dezelfde candle: conservatief stop-first.",
                     "Shorts: 100% notional als onderpand, vaste leenkosten, geen echte margin/funding/liquidatie. Gaps en langere looptijd kunnen gepland risico overschrijden."])
    return {"train":train,"test":test,"split_index":cut,"total_candles":n,"warnings":warnings}

