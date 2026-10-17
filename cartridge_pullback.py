"""Frozen trend-pullback v1; available through the fixed protocol only."""
from cartridge_api import Cartridge
def long(d,p):
    return (d.close>d.trend_ema)&(d.ema_slow>d.trend_ema)&(d.trend_slope>0)&(d.close.shift()<=d.ema_fast.shift())&(d.close>d.ema_fast),d.close<d.ema_slow
def short(d,p):
    return (d.close<d.trend_ema)&(d.ema_slow<d.trend_ema)&(d.trend_slope<0)&(d.close.shift()>=d.ema_fast.shift())&(d.close<d.ema_fast),d.close>d.ema_slow
CARTRIDGE=Cartridge("pullback","Trend-pullback v1 (vast)","EMA20-herstel in een EMA50/200-trend. Vooraf vastgelegde test op BTC, ETH en SOL.",__name__,(),long,short,
    lambda p:220,lambda p,side:"Trend-pullback v1: EMA20-herovering in EMA50/200-trend",protocol_only=True,
    fixed=(("ema_fast",20),("ema_slow",50),("trend_filter",True),("cooldown_bars",12),("stop_atr",2.5),("target_atr",5.),("max_holding_bars",30)))
