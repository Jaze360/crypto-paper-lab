"""Fixed daily recency-of-extremes rules, with explicit recent-tie convention."""
import numpy as np
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d)
    day['aroon_up']=day.high.rolling(26,min_periods=26).apply(lambda x:100*(25-int(np.argmax(x[::-1])))/25,raw=True)
    day['aroon_down']=day.low.rolling(26,min_periods=26).apply(lambda x:100*(25-int(np.argmin(x[::-1])))/25,raw=True)
    return attach(d,day)

def long(d,p):
    return d.daily_decision&(d.aroon_up>=70)&(d.aroon_down<=30),d.daily_decision&((d.aroon_up<50)|(d.aroon_down>50))

def short(d,p):
    return d.daily_decision&(d.aroon_down>=70)&(d.aroon_up<=30),d.daily_decision&((d.aroon_down<50)|(d.aroon_up>50))

CARTRIDGE=Cartridge('aroon','Aroon-trend · 25 dagen','Trend op basis van de recentste dagpieken en -bodems; LONG en SHORT.',__name__,(),long,short,
    lambda p:26*24-1,lambda p,side:'Dagelijkse Aroon25-toestand 70/30 in '+side.upper()+'-richting',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
