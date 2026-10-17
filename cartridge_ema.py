"""EMA cartridge v1: unchanged v0.10 entry/exit rules."""
from cartridge_api import Cartridge
def long(d,p):
    return (d.ema_fast>d.ema_slow)&(d.ema_fast.shift()<=d.ema_slow.shift()),d.ema_fast<d.ema_slow
def short(d,p):
    return (d.ema_fast<d.ema_slow)&(d.ema_fast.shift()>=d.ema_slow.shift()),d.ema_fast>d.ema_slow
CARTRIDGE=Cartridge("ema","EMA trendvolgend","Volg een kruising van een snelle en trage EMA.",__name__,
    ("ema_fast","ema_slow"),long,short,lambda p:max(22,p.ema_slow),lambda p,side:f"EMA {p.ema_fast}/{p.ema_slow}-kruising")
