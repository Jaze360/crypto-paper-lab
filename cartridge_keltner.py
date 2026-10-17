"""Fixed daily EMA/ATR channel crossing; prior values are explicit."""
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d);mean=day.close.ewm(span=20,adjust=False,min_periods=20).mean()
    upper=mean+2*day.daily_atr;lower=mean-2*day.daily_atr
    day['kc_long']=(day.close.shift()<=upper.shift())&(day.close>upper)
    day['kc_short']=(day.close.shift()>=lower.shift())&(day.close<lower)
    day['kc_exit_long']=day.close<mean;day['kc_exit_short']=day.close>mean
    return attach(d,day)

def long(d,p):return d.daily_decision&d.kc_long,d.daily_decision&d.kc_exit_long
def short(d,p):return d.daily_decision&d.kc_short,d.daily_decision&d.kc_exit_short

CARTRIDGE=Cartridge('keltner','Keltner-uitbraak · 20 × 2','Dag-close breekt door een kanaal van EMA en volatiliteit; LONG en SHORT.',__name__,(),long,short,
    lambda p:21*24-1,lambda p,side:'Dag-close kruist de Keltner(20,2)-band in '+side.upper()+'-richting',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
