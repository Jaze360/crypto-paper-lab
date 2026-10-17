"""Fixed re-entry into daily Bollinger bands; no fitted thresholds."""
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d);mean=day.close.rolling(20,min_periods=20).mean();std=day.close.rolling(20,min_periods=20).std(ddof=0)
    upper=mean+2*std;lower=mean-2*std
    day['bb_long']=(day.close.shift()<lower.shift())&(day.close>lower)
    day['bb_short']=(day.close.shift()>upper.shift())&(day.close<upper)
    day['bb_exit_long']=day.close>=mean;day['bb_exit_short']=day.close<=mean
    return attach(d,day)

def long(d,p):return d.daily_decision&d.bb_long,d.daily_decision&d.bb_exit_long
def short(d,p):return d.daily_decision&d.bb_short,d.daily_decision&d.bb_exit_short

CARTRIDGE=Cartridge('bollinger','Bollinger-herstel · 20 × 2','Terugkeer binnen dagbanden na een extreme beweging; exit bij het gemiddelde.',__name__,(),long,short,
    lambda p:21*24-1,lambda p,side:'Dag-close keert terug binnen de Bollinger(20,2)-band',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',2.),('target_atr',4.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
