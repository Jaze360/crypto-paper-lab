"""Lagged indicators and bounded, explicit strategy parameters."""
import numpy as np
import pandas as pd
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

STRATEGIES={"ema":"EMA trendvolgend","rsi":"RSI herstel","breakout":"Breakout + candlevolume"}
class StrategyConfig(BaseModel):
    model_config=ConfigDict(extra="forbid")
    trend_filter:bool=False
    cooldown_bars:int=Field(default=0,ge=0,le=100)
    trade_mode:Literal["long","short","both"]="long"
    short_borrow_daily_pct:float=Field(default=.02,ge=0,le=1,allow_inf_nan=False)
    ema_fast:int=Field(default=8,ge=3,le=100)
    ema_slow:int=Field(default=21,ge=5,le=250)
    rsi_period:int=Field(default=14,ge=5,le=50)
    rsi_entry:float=Field(default=30,ge=10,le=50,allow_inf_nan=False)
    rsi_exit:float=Field(default=55,ge=40,le=90,allow_inf_nan=False)
    breakout_period:int=Field(default=20,ge=5,le=100)
    volume_multiple:float=Field(default=1.5,ge=1,le=3,allow_inf_nan=False)
    stop_atr:float=Field(default=1.5,ge=.5,le=4,allow_inf_nan=False)
    target_atr:float=Field(default=3,ge=1,le=8,allow_inf_nan=False)
    @model_validator(mode="after")
    def valid_order(self):
        if self.ema_fast>=self.ema_slow:raise ValueError("Snelle EMA moet korter zijn dan trage EMA.")
        if self.rsi_entry>=self.rsi_exit:raise ValueError("RSI-instap moet lager zijn dan RSI-uitstap.")
        return self
def config(value=None):
    return value if isinstance(value,StrategyConfig) else StrategyConfig(**(value or {}))
def add_indicators(candles, parameters=None):
    p=config(parameters);d=candles.copy();close=d.close
    d["ema_fast"]=close.ewm(span=p.ema_fast,adjust=False,min_periods=p.ema_fast).mean()
    d["ema_slow"]=close.ewm(span=p.ema_slow,adjust=False,min_periods=p.ema_slow).mean()
    change=close.diff()
    gain=change.clip(lower=0).ewm(alpha=1/p.rsi_period,adjust=False,min_periods=p.rsi_period).mean()
    loss=(-change.clip(upper=0)).ewm(alpha=1/p.rsi_period,adjust=False,min_periods=p.rsi_period).mean()
    d["rsi"]=100-100/(1+gain/loss.replace(0,np.nan))
    d.loc[(loss==0)&(gain>0),"rsi"]=100.
    d.loc[(loss==0)&(gain==0),"rsi"]=50.
    tr=pd.concat([d.high-d.low,(d.high-close.shift()).abs(),(d.low-close.shift()).abs()],axis=1).max(axis=1)
    d["trend_ema"]=close.ewm(span=200,adjust=False,min_periods=200).mean()
    d["trend_slope"]=d["trend_ema"]-d["trend_ema"].shift(20)
    d["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    d["prior_high20"]=d.high.shift().rolling(p.breakout_period,min_periods=p.breakout_period).max()
    d["prior_low20"]=d.low.shift().rolling(p.breakout_period,min_periods=p.breakout_period).min()
    d["vol_mean20"]=d.volume.shift().rolling(p.breakout_period,min_periods=p.breakout_period).mean()
    d.attrs.update(candles.attrs);d.attrs["strategy_config"]=p.model_dump()
    return d
def signals(df,strategy):
    p=config(df.attrs.get("strategy_config"))
    if strategy=="ema":
        enter=(df.ema_fast>df.ema_slow)&(df.ema_fast.shift()<=df.ema_slow.shift())
        leave=df.ema_fast<df.ema_slow
    elif strategy=="rsi":
        enter=(df.rsi.shift()<p.rsi_entry)&(df.rsi>=p.rsi_entry)
        leave=df.rsi>=p.rsi_exit
    elif strategy=="breakout":
        enter=(df.close>df.prior_high20)&(df.volume>p.volume_multiple*df.vol_mean20)&(df.close.shift()<=df.prior_high20.shift())
        leave=df.close<df.ema_fast
    else:raise ValueError("Onbekende strategie")
    warmup=max(22,p.ema_slow if strategy=="ema" else p.rsi_period+1 if strategy=="rsi" else max(p.ema_fast,p.breakout_period+1))
    enter=enter.fillna(False).to_numpy(dtype=bool);leave=leave.fillna(False).to_numpy(dtype=bool)
    enter[:warmup]=False;leave[:warmup]=False
    return enter,leave
def signal(df,i,strategy):
    if i<0 or i>=len(df):return False,False
    enter,leave=signals(df,strategy)
    return bool(enter[i]),bool(leave[i])


def short_signals(df,strategy):
    p=config(df.attrs.get("strategy_config"))
    if strategy=="ema":
        enter=(df.ema_fast<df.ema_slow)&(df.ema_fast.shift()>=df.ema_slow.shift())
        leave=df.ema_fast>df.ema_slow
    elif strategy=="rsi":
        enter=(df.rsi.shift()>100-p.rsi_entry)&(df.rsi<=100-p.rsi_entry)
        leave=df.rsi<=100-p.rsi_exit
    elif strategy=="breakout":
        enter=(df.close<df.prior_low20)&(df.volume>p.volume_multiple*df.vol_mean20)&(df.close.shift()>=df.prior_low20.shift())
        leave=df.close>df.ema_fast
    else:raise ValueError("Onbekende strategie")
    warmup=max(22,p.ema_slow if strategy=="ema" else p.rsi_period+1 if strategy=="rsi" else max(p.ema_fast,p.breakout_period+1))
    enter=enter.fillna(False).to_numpy(dtype=bool);leave=leave.fillna(False).to_numpy(dtype=bool)
    enter[:warmup]=False;leave[:warmup]=False
    return enter,leave
