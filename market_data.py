"""OHLCV providers. CoinGecko OHLC is NOT OHLCV: volume must not be invented."""
from __future__ import annotations
import os
import time
from datetime import datetime, timezone
from typing import Any
import numpy as np
import pandas as pd
import requests

class DataError(ValueError):
    pass

ALLOWED_COINS = {"bitcoin", "ethereum", "solana"}


def demo_candles(coin: str = "bitcoin", count: int = 360) -> pd.DataFrame:
    if coin not in ALLOWED_COINS:
        raise DataError("Onbekende demo-munt")
    seed = {"bitcoin": 147, "ethereum": 202, "solana": 353}[coin]
    rng = np.random.default_rng(seed)
    count = max(90, min(int(count), 1200))
    # Fixed seed; reproducible demonstratie, geen historische of actuele koersen.
    phases = [0.003, -0.004, 0.0001, 0.002, -0.001]
    open_, high, low, close, volumes = [], [], [], [], []
    previous = {"bitcoin": 55000, "ethereum": 2800, "solana": 130}[coin]
    for i in range(count):
        drift = phases[(i // 70) % len(phases)]
        shock = rng.normal(drift, 0.015)
        o = previous * (1 + rng.normal(0, 0.0012))
        c = max(0.01, o * (1 + shock))
        h = max(o, c) * (1 + abs(rng.normal(0.005, 0.005)))
        l = min(o, c) * (1 - min(abs(rng.normal(0.005, 0.005)), 0.08))
        v = float(max(1, 900 + abs(shock) * 55000 + rng.normal(0, 150)))
        open_.append(o); high.append(h); low.append(l); close.append(c); volumes.append(v)
        previous = c
    last = pd.Timestamp.now(tz="UTC").floor("4h") - pd.Timedelta(hours=4)
    times = pd.date_range(end=last, periods=count, freq="4h")
    df = pd.DataFrame({"time":times,"open":open_,"high":high,"low":low,"close":close,"volume":volumes})
    df.attrs.update(source="DEMO — SYNTHETISCH", volume_is_actual=True, timeframe="4h", coin=coin)
    return validate(df)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) < 5:
        raise DataError("Te weinig candles")
    required = ("time","open","high","low","close")
    if not all(k in df for k in required):
        raise DataError("Candlegegevens missen verplichte velden")
    out = df.sort_values("time").drop_duplicates("time").reset_index(drop=True).copy()
    for c in ("open","high","low","close"):
        out[c] = pd.to_numeric(out[c], errors="raise")
    if (out[list(required[1:])] <= 0).any().any() or not np.isfinite(out[list(required[1:])].to_numpy()).all():
        raise DataError("Ongeldige koerswaarden")
    if ((out.high < out[["open","close"]].max(axis=1)) | (out.low > out[["open","close"]].min(axis=1)) | (out.low > out.high)).any():
        raise DataError("OHLC-integriteit fout")
    out.attrs.update(df.attrs)
    return out


class CoinGeckoProvider:
    """No API key shipped. No coin exchange trading endpoints exist here."""
    _cache: dict[tuple, tuple[float,pd.DataFrame]] = {}
    def __init__(self, api_key: str | None = None, plan: str | None = None):
        self.key = api_key or os.environ.get("COINGECKO_API_KEY", "")
        self.plan = (plan or os.environ.get("COINGECKO_PLAN", "demo")).lower()
        if self.plan not in ("demo", "pro"):
            raise DataError("COINGECKO_PLAN moet demo of pro zijn")
        self.base = "https://pro-api.coingecko.com/api/v3" if self.plan == "pro" else "https://api.coingecko.com/api/v3"

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        headers = {"Accept":"application/json", "User-Agent":"CryptoPaperLab/0.1"}
        if self.key:
            headers["x-cg-pro-api-key" if self.plan == "pro" else "x-cg-demo-api-key"] = self.key
        else:
            raise DataError("CoinGecko API-key ontbreekt. Voeg die eerst lokaal toe.")
        for attempt in range(3):
            try:
                result = requests.get(self.base + path, params=params, headers=headers, timeout=16)
            except requests.RequestException as exc:
                raise DataError("CoinGecko-netwerkfout; controleer internetverbinding") from exc
            if result.status_code == 429 and attempt < 2:
                try: pause = min(max(float(result.headers.get("Retry-After", 2+attempt*2)), 1), 8)
                except ValueError: pause = 2 + attempt*2
                time.sleep(pause)
                continue
            if result.status_code in (401,403):
                raise DataError("CoinGecko toegang geweigerd: controleer API-key en abonnementsrechten")
            if result.status_code == 429:
                raise DataError("CoinGecko rate limit bereikt; probeer later opnieuw")
            if not result.ok:
                raise DataError(f"CoinGecko antwoordt met HTTP {result.status_code}")
            try: return result.json()
            except ValueError as exc: raise DataError("CoinGecko gaf geen geldige JSON terug") from exc
        raise DataError("CoinGecko niet bereikbaar")

    def candles(self, coin: str="bitcoin", days: int=30) -> pd.DataFrame:
        if coin not in ALLOWED_COINS:
            raise DataError("Niet toegestane munt")
        if days not in (7,14,30):
            raise DataError("Kies 7, 14 of 30 dagen; langere periodes vereisen aparte granulariteitscontrole")
        key = (self.plan, coin, days, self.key)
        stored = self._cache.get(key)
        if stored and time.time() - stored[0] < 300:
            return stored[1].copy()
        raw = self._get(f"/coins/{coin}/ohlc", {"vs_currency":"usd", "days":days, "precision":"full"})
        if not isinstance(raw,list) or not raw:
            raise DataError("CoinGecko leverde geen OHLC-data")
        rows = []
        for candle in raw:
            if not isinstance(candle,list) or len(candle) < 5: continue
            rows.append({"time":pd.to_datetime(candle[0], unit="ms", utc=True),
                         "open":float(candle[1]),"high":float(candle[2]),"low":float(candle[3]),"close":float(candle[4]),
                         "volume":float('nan')})
        df = pd.DataFrame(rows)
        if len(df) < 40:
            raise DataError("Te weinig CoinGecko-candles voor deze strategie")
        # CoinGecko timestamp = candle END. Remove a candle if its interval has not ended.
        # Dataset may still include the latest complete candle; no intrabar execution is inferred.
        df = df[df.time <= pd.Timestamp.now(tz="UTC")].copy()
        df.attrs.update(source="CoinGecko OHLC",volume_is_actual=False, time_frame="automatisch (CoinGecko)", coin=coin)
        validated = validate(df)
        self._cache[key] = (time.time(), validated.copy())
        return validated
