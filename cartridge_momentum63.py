"""Fixed 63-day momentum, weekly LONG/cash decisions, hourly paper execution."""
from cartridge_api import Cartridge
from slow_features import completed_days,attach,none

def prepare(df,p):
    daily=completed_days(df)
    daily['momentum63']=daily.close/daily.close.shift(63)-1
    return attach(df,daily)

def long(df,p):
    return df.weekly_decision&(df.momentum63>0),df.weekly_decision&(df.momentum63<=0)

CARTRIDGE=Cartridge('momentum63','Langzaam momentum · 63 dagen',
    'Wekelijkse keuze tussen LONG en cash, gebaseerd op 63 dagen koersontwikkeling.',__name__,(),long,none,
    lambda p:64*24-1,lambda p,side:'Positief 63-daags momentum op wekelijkse UTC-beslissing',protocol_only=True,
    fixed=(('trade_mode','long'),('trend_filter',False),('cooldown_bars',0),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('long',))
