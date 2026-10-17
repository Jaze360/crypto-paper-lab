"""Completed UTC days derived causally from hourly candles. No daily execution fills."""
import pandas as pd

def completed_days(df):
    if len(df)>1 and not df.time.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError('Deze cartridge vereist aaneengesloten 1-uurscandles.')
    indexed=df.set_index('time')
    groups=indexed.resample('D',label='right',closed='left')
    daily=groups.agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
    daily=daily[groups.close.count()==24].copy()
    tr=pd.concat([daily.high-daily.low,(daily.high-daily.close.shift()).abs(),(daily.low-daily.close.shift()).abs()],axis=1).max(axis=1)
    daily['daily_atr']=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    return daily

def attach(df,daily):
    """At hour t, only days complete at t+1h may inform next-open decisions."""
    clock=pd.DatetimeIndex(df.time+pd.Timedelta(hours=1))
    values=daily.reindex(clock,method='ffill')
    d=df.copy()
    for name in daily.columns:
        if name not in ('open','high','low','close','volume'):d[name]=values[name].to_numpy()
    d['atr']=d['daily_atr']
    d['daily_decision']=(clock.hour==0)
    d['weekly_decision']=(clock.hour==0)&(clock.dayofweek==0)
    d.attrs.update(df.attrs)
    return d

def none(df,p):
    return pd.Series(False,index=df.index),pd.Series(False,index=df.index)
