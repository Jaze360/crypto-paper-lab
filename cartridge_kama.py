"""Fixed adaptive daily average crossing and efficiency filter; hourly fills."""
import numpy as np,pandas as pd
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d);change=day.close.diff(10).abs();noise=day.close.diff().abs().rolling(10,min_periods=10).sum()
    er=(change/noise.replace(0,np.nan)).where(noise!=0,0.)
    smoothing=(er*(2/3-2/31)+2/31)**2
    close=day.close.to_numpy();kama=np.full(len(day),np.nan)
    if len(day)>=10:kama[9]=float(np.mean(close[:10]))
    for i in range(10,len(day)):kama[i]=kama[i-1]+float(smoothing.iloc[i])*(close[i]-kama[i-1])
    value=pd.Series(kama,index=day.index);previous=value.shift()
    day['kama']=value;day['kama_er']=er
    day['kama_long']=(day.close.shift()<=previous)&(day.close>value)&(value>previous)&(er>=.30)
    day['kama_short']=(day.close.shift()>=previous)&(day.close<value)&(value<previous)&(er>=.30)
    day['kama_exit_long']=day.close<value;day['kama_exit_short']=day.close>value
    return attach(d,day)

def long(d,p):return d.daily_decision&d.kama_long,d.daily_decision&d.kama_exit_long
def short(d,p):return d.daily_decision&d.kama_short,d.daily_decision&d.kama_exit_short

CARTRIDGE=Cartridge('kama','KAMA adaptieve trend · 10/2/30','Kruising van een adaptief daggemiddelde, met filter voor koersruis.',__name__,(),long,short,
    lambda p:31*24-1,lambda p,side:'Dagelijkse KAMA-kruising, juiste helling en ER >= 0,30',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
