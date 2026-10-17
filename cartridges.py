"""Explicit built-in registry. No file scanning, uploaded code, eval or remote imports."""
import hashlib
from pathlib import Path
from functools import lru_cache
from types import MappingProxyType
from cartridge_ema import CARTRIDGE as EMA
from cartridge_rsi import CARTRIDGE as RSI
from cartridge_breakout import CARTRIDGE as BREAKOUT
from cartridge_pullback import CARTRIDGE as PULLBACK

_items=(EMA,RSI,BREAKOUT,PULLBACK)
if len({c.id for c in _items})!=len(_items):raise ValueError("Dubbele cartridge-ID")
REGISTRY=MappingProxyType({c.id:c for c in _items})

def get_cartridge(strategy):
    try:return REGISTRY[strategy]
    except KeyError:raise ValueError("Onbekende strategiecartridge") from None

@lru_cache(maxsize=32)
def _fingerprint(strategy):
    c=get_cartridge(strategy);root=Path(__file__).parent
    files=(c.module+".py","cartridge_api.py","cartridges.py","strategies.py","engine.py")
    return tuple((name,hashlib.sha256((root/name).read_bytes()).hexdigest()) for name in files)

def manifest(strategy):
    c=get_cartridge(strategy)
    return {**c.describe(),"api_version":1,"code_sha256":dict(_fingerprint(strategy))}

def catalog():
    return [manifest(c.id) for c in _items]
