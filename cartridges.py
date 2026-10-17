"""Explicit built-in registry. No file scanning, uploaded code, eval or remote imports."""
import hashlib
from pathlib import Path
from functools import lru_cache
from types import MappingProxyType
from cartridge_ema import CARTRIDGE as EMA
from cartridge_rsi import CARTRIDGE as RSI
from cartridge_breakout import CARTRIDGE as BREAKOUT
from cartridge_pullback import CARTRIDGE as PULLBACK
from cartridge_momentum63 import CARTRIDGE as MOMENTUM63
from cartridge_donchian55 import CARTRIDGE as DONCHIAN55
from cartridge_slow_both import MOMENTUM_BOTH,CHANNEL_BOTH
from cartridge_supertrend import CARTRIDGE as SUPERTREND
from cartridge_bollinger import CARTRIDGE as BOLLINGER
from cartridge_keltner import CARTRIDGE as KELTNER
from cartridge_failed_breakout import CARTRIDGE as FAILED_BREAKOUT
from cartridge_aroon import CARTRIDGE as AROON
from cartridge_kama import CARTRIDGE as KAMA

PRIMARY_IDS=('momentum63_both','donchian55_both','supertrend','keltner','aroon','kama')
_items=(EMA,RSI,BREAKOUT,PULLBACK,MOMENTUM63,DONCHIAN55,MOMENTUM_BOTH,CHANNEL_BOTH,SUPERTREND,BOLLINGER,KELTNER,FAILED_BREAKOUT,AROON,KAMA)
if len({c.id for c in _items})!=len(_items):raise ValueError("Dubbele cartridge-ID")
REGISTRY=MappingProxyType({c.id:c for c in _items})

def get_cartridge(strategy):
    try:return REGISTRY[strategy]
    except KeyError:raise ValueError("Onbekende strategiecartridge") from None

@lru_cache(maxsize=32)
def _fingerprint(strategy):
    c=get_cartridge(strategy);root=Path(__file__).parent
    files=(c.module+".py","cartridge_api.py","cartridges.py","strategies.py","engine.py",*c.dependencies)
    return tuple((name,hashlib.sha256((root/name).read_bytes()).hexdigest()) for name in files)

def manifest(strategy):
    c=get_cartridge(strategy)
    return {**c.describe(),"api_version":1,"code_sha256":dict(_fingerprint(strategy))}

def catalog():
    return [{**manifest(c.id),'primary':c.id in PRIMARY_IDS} for c in sorted(_items,key=lambda c:PRIMARY_IDS.index(c.id) if c.id in PRIMARY_IDS else len(PRIMARY_IDS))]
