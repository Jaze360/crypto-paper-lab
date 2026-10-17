"""Fixed false-breakout rejection in the direction of the daily EMA100."""
from cartridge_api import Cartridge
from slow_features import completed_days,attach

def prepare(d,p):
    day=completed_days(d);low=day.low.shift().rolling(20,min_periods=20).min();high=day.high.shift().rolling(20,min_periods=20).max()
    mean=day.close.ewm(span=100,adjust=False,min_periods=100).mean();mid=(high+low)/2
    exit_long=(day.close>=mid)|(day.close<mean);exit_short=(day.close<=mid)|(day.close>mean)
    day['fb_long']=(day.low<low)&(day.close>low)&(day.close>mean)&~exit_long
    day['fb_short']=(day.high>high)&(day.close<high)&(day.close<mean)&~exit_short
    day['fb_exit_long']=exit_long;day['fb_exit_short']=exit_short
    return attach(d,day)

def long(d,p):return d.daily_decision&d.fb_long,d.daily_decision&d.fb_exit_long
def short(d,p):return d.daily_decision&d.fb_short,d.daily_decision&d.fb_exit_short

CARTRIDGE=Cartridge('failed_breakout','Mislukte uitbraak · 20/100','Afgewezen daguitbraak met EMA100-trendfilter; LONG en SHORT.',__name__,(),long,short,
    lambda p:100*24-1,lambda p,side:'Mislukte 20-daagse uitbraak, herstelde close en EMA100-trendfilter',protocol_only=True,
    fixed=(('trade_mode','both'),('trend_filter',False),('cooldown_bars',24),('max_holding_bars',0),('stop_atr',2.),('target_atr',4.)),
    prepare=prepare,dependencies=('slow_features.py',),directions=('both',))
