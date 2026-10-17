"""Fixed daily Supertrend state; price fills stay hourly."""
import numpy as np,pandas as pd
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d);previous=day.close.shift()
    tr=pd.concat([day.high-day.low,(day.high-previous).abs(),(day.low-previous).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/10,adjust=False,min_periods=10).mean()
    upper=((day.high+day.low)/2+3*atr).to_numpy(copy=True)
    lower=((day.high+day.low)/2-3*atr).to_numpy(copy=True)
    close=day.close.to_numpy();direction=np.zeros(len(day),dtype=int)
    for i in range(len(day)):
        if not np.isfinite(upper[i]):continue
        if i==0 or not np.isfinite(upper[i-1]):direction[i]=1;continue
        if not(upper[i]<upper[i-1] or close[i-1]>upper[i-1]):upper[i]=upper[i-1]
        if not(lower[i]>lower[i-1] or close[i-1]<lower[i-1]):lower[i]=lower[i-1]
        direction[i]=(-1 if close[i]<lower[i] else 1) if direction[i-1]>0 else (1 if close[i]>upper[i] else -1)
    day['supertrend_direction']=direction
    return attach(d,day)

def long(d,p):return d.daily_decision&(d.supertrend_direction>0),d.daily_decision&(d.supertrend_direction<0)
def short(d,p):return d.daily_decision&(d.supertrend_direction<0),d.daily_decision&(d.supertrend_direction>0)

CARTRIDGE=Cartridge('supertrend','Supertrend · 10 × 3','Dagelijkse trendrichting met een ATR-band; LONG en SHORT.',__name__,(),long,short,
    lambda p:30*24-1,lambda p,side:'Dagelijkse Supertrend(10,3) in '+side.upper()+'-richting',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
