"""Fixed daily 55/20 channel decisions on completed days, hourly execution."""
from cartridge_api import Cartridge
from slow_features import completed_days,attach,none

def prepare(df,p):
    daily=completed_days(df)
    daily['channel55']=daily.high.shift().rolling(55,min_periods=55).max()
    daily['channel20']=daily.low.shift().rolling(20,min_periods=20).min()
    daily['daily_close']=daily.close
    return attach(df,daily)

def long(df,p):
    return df.daily_decision&(df.daily_close>df.channel55),df.daily_decision&(df.daily_close<df.channel20)

CARTRIDGE=Cartridge('donchian55','Kanaaluitbraak · 55/20 dagen',
    'LONG bij een langzame uitbraak; cash na een neerwaartse kanaalbreuk.',__name__,(),long,none,
    lambda p:56*24-1,lambda p,side:'Gesloten UTC-dag boven het voorafgaande 55-daagse highkanaal',protocol_only=True,
    fixed=(('trade_mode','long'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',3.),('target_atr',8.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('long',))
