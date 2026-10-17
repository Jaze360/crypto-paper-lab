"""Breakout cartridge v1: real candle volume required."""
from cartridge_api import Cartridge
def long(d,p):
    return (d.close>d.prior_high20)&(d.volume>p.volume_multiple*d.vol_mean20)&(d.close.shift()<=d.prior_high20.shift()),d.close<d.ema_fast
def short(d,p):
    return (d.close<d.prior_low20)&(d.volume>p.volume_multiple*d.vol_mean20)&(d.close.shift()>=d.prior_low20.shift()),d.close>d.ema_fast
CARTRIDGE=Cartridge("breakout","Breakout + candlevolume","Uitbraak voorbij eerdere highs/lows, bevestigd door echt candlevolume.",__name__,
    ("breakout_period","volume_multiple","ema_fast"),long,short,lambda p:max(22,p.ema_fast,p.breakout_period+1),
    lambda p,side:f"Uitbraak over {p.breakout_period} vorige candles met volumefactor {p.volume_multiple}",requires_volume=True)
