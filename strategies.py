"""Only lagged price/volume information. Signal computed at candle close."""
from __future__ import annotations
import numpy as np
import pandas as pd

STRATEGIES = {
    "ema":"EMA 8/21 trendvolgend",
    "rsi":"RSI herstel (14)",
    "breakout":"Breakout 20 + echt candlevolume",
}


def add_indicators(candles: pd.DataFrame) -> pd.DataFrame:
    d=candles.copy()
    close=d.close
    d['ema_fast']=close.ewm(span=8,adjust=False,min_periods=8).mean()
    d['ema_slow']=close.ewm(span=21,adjust=False,min_periods=21).mean()
    change=close.diff()
    gain=change.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss=(-change.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs=gain/loss.replace(0,np.nan)
    d['rsi']=100-(100/(1+rs))
    d.loc[(loss==0)&(gain>0), 'rsi']=100.0
    true_range=pd.concat([(d.high-d.low), (d.high-close.shift()).abs(), (d.low-close.shift()).abs()],axis=1).max(axis=1)
    d['atr']=true_range.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    d['prior_high20']=d.high.shift(1).rolling(20,min_periods=20).max()
    d['vol_mean20']=d.volume.shift(1).rolling(20,min_periods=20).mean()
    d.attrs.update(candles.attrs)
    return d


def signal(df:pd.DataFrame, i:int, strategy:str) -> tuple[bool,bool]:
    """Get signal at completed candle i; caller may only act at i+1 open."""
    if i < 22: return False,False
    row = df.iloc[i]
    prev = df.iloc[i-1]
    if strategy=="ema":
        if pd.isna(row.ema_fast) or pd.isna(row.ema_slow): return False,False
        return bool(row.ema_fast > row.ema_slow and prev.ema_fast<=prev.ema_slow), bool(row.ema_fast < row.ema_slow)
    if strategy=="rsi":
        if pd.isna(row.rsi) or pd.isna(prev.rsi): return False,False
        return bool(prev.rsi < 30 and row.rsi >= 30), bool(row.rsi >= 55)
    if strategy=="breakout":
        if pd.isna(row.prior_high20) or pd.isna(row.vol_mean20) or pd.isna(row.volume): return False,False
        return bool(row.close > row.prior_high20 and row.volume > 1.5 * row.vol_mean20 and prev.close <= prev.prior_high20), bool(row.close < row.ema_fast)
    raise ValueError("Onbekende strategie")
