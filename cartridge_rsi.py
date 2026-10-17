"""RSI cartridge v1: unchanged mirrored recovery rules."""
from cartridge_api import Cartridge
def long(d,p):
    return (d.rsi.shift()<p.rsi_entry)&(d.rsi>=p.rsi_entry),d.rsi>=p.rsi_exit
def short(d,p):
    return (d.rsi.shift()>100-p.rsi_entry)&(d.rsi<=100-p.rsi_entry),d.rsi<=100-p.rsi_exit
CARTRIDGE=Cartridge("rsi","RSI herstel","Onderzoek herstel na een sterke koersbeweging; SHORT gebruikt gespiegelde drempels.",__name__,
    ("rsi_period","rsi_entry","rsi_exit"),long,short,lambda p:max(22,p.rsi_period+1),
    lambda p,side:f"RSI {p.rsi_period} kruist {p.rsi_entry if side=='long' else 100-p.rsi_entry}")
