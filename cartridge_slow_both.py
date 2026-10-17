"""Explicit mirrored SHORT extensions; v1.0 LONG implementations remain untouched."""
from dataclasses import replace
from cartridge_momentum63 import CARTRIDGE as MOMENTUM
from cartridge_donchian55 import CARTRIDGE as CHANNEL
from slow_features import completed_days,attach

def momentum_short(d,p):
    return d.weekly_decision&(d.momentum63<0),d.weekly_decision&(d.momentum63>=0)

def channel_prepare(d,p):
    daily=completed_days(d)
    daily['channel55']=daily.high.shift().rolling(55,min_periods=55).max()
    daily['channel20']=daily.low.shift().rolling(20,min_periods=20).min()
    daily['short55']=daily.low.shift().rolling(55,min_periods=55).min()
    daily['short20']=daily.high.shift().rolling(20,min_periods=20).max()
    daily['daily_close']=daily.close
    return attach(d,daily)

def channel_short(d,p):
    return d.daily_decision&(d.daily_close<d.short55),d.daily_decision&(d.daily_close>d.short20)

def both(base,**changes):
    return replace(base,module=__name__,version='1.1.0',directions=('both',),
                   fixed=tuple((k,'both' if k=='trade_mode' else v) for k,v in base.fixed),
                   dependencies=(*base.dependencies,base.module+'.py'),long_reference=base.id,**changes)

MOMENTUM_BOTH=both(MOMENTUM,id='momentum63_both',short=momentum_short,
    description='Wekelijks 63-daags momentum, met spiegelbeeldige shorts en een aparte LONG-referentie.',
    reason=lambda p,side:'Positief 63-daags weekmomentum' if side=='long' else 'Negatief 63-daags weekmomentum')
CHANNEL_BOTH=both(CHANNEL,id='donchian55_both',short=channel_short,prepare=channel_prepare,
    description='55-daagse uitbraak omhoog of omlaag; 20-daagse exit. Inclusief aparte LONG-referentie.',
    reason=lambda p,side:'Dag-close boven vorig 55-daags highkanaal' if side=='long' else 'Dag-close onder vorig 55-daags lowkanaal')
