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

COINS = {
    "bitcoin": ("Bitcoin (BTC)", "XBTUSD"), "ethereum": ("Ethereum (ETH)", "ETHUSD"),
    "solana": ("Solana (SOL)", "SOLUSD"), "ripple": ("XRP", "XRPUSD"),
    "cardano": ("Cardano (ADA)", "ADAUSD"), "dogecoin": ("Dogecoin (DOGE)", "DOGEUSD"),
    "avalanche-2": ("Avalanche (AVAX)", "AVAXUSD"), "chainlink": ("Chainlink (LINK)", "LINKUSD"),
    "polkadot": ("Polkadot (DOT)", "DOTUSD"), "litecoin": ("Litecoin (LTC)", "LTCUSD"),
    "bitcoin-cash": ("Bitcoin Cash (BCH)", "BCHUSD"), "uniswap": ("Uniswap (UNI)", "UNIUSD")}
ALLOWED_COINS = set(COINS)
DEMO_COINS = {"bitcoin", "ethereum", "solana"}


def demo_candles(coin: str = "bitcoin", count: int = 360) -> pd.DataFrame:
    if coin not in DEMO_COINS:
        raise DataError("De demo ondersteunt alleen Bitcoin, Ethereum en Solana.")
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
        from secrets_store import get_key
        from storage import settings
        self.key = api_key if api_key is not None else get_key()
        self.plan = (plan or os.environ.get("COINGECKO_PLAN") or settings().get("coingecko_plan", "demo")).lower()
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
        if days not in (7,14,30,90,180,365):
            raise DataError("Kies 7, 14, 30, 90, 180 of 365 dagen; beschikbaarheid hangt af van je abonnement")
        if not self.key:
            raise DataError("CoinGecko API-key ontbreekt. Voeg die eerst lokaal toe.")
        key = (self.plan, coin, days, self.key)
        from storage import cache_get, cache_put
        import hashlib
        disk_key = "coingecko:" + hashlib.sha256(repr(key).encode()).hexdigest()
        cached = cache_get(disk_key)
        if cached:
            return unpack_candles(cached)
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
        cache_put(disk_key, pack_candles(validated))
        return validated

def pack_candles(df):
    frame = df.astype(object).where(pd.notna(df), None)
    frame["time"] = df.time.map(lambda t: t.isoformat())
    return {"rows": frame.to_dict(orient="records"), "attrs": df.attrs}

def unpack_candles(value):
    from io import StringIO
    df = pd.DataFrame(value["rows"])
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df.attrs.update(value["attrs"])
    return validate(df)

class KrakenProvider:
    """Public market data only. No authentication, accounts, or order endpoints."""
    def candles(self, coin="bitcoin", days=365, interval=1440):
        from storage import cache_get, cache_put
        if coin not in COINS or interval not in (60, 240, 1440):
            raise DataError("Niet toegestane munt of interval.")
        key = f"kraken:{coin}:{days}:{interval}"
        cached = cache_get(key)
        if cached:
            return unpack_candles(cached)
        try:
            response = requests.get("https://api.kraken.com/0/public/OHLC",
                                    params={"pair": COINS[coin][1], "interval": interval}, timeout=20)
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise DataError("Kraken-marktdata niet beschikbaar. Probeer later opnieuw.") from exc
        if body.get("error"):
            raise DataError("Kraken weigert deze markt of aanvraag: " + ", ".join(body["error"]))
        series = [v for k,v in body.get("result", {}).items() if k != "last"]
        if len(series) != 1:
            raise DataError("Onverwacht Kraken-antwoord.")
        rows = series[0][:-1]  # Kraken's last candle is always unfinished.
        df = pd.DataFrame(rows, columns=["time","open","high","low","close","vwap","volume","count"])
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        now = pd.Timestamp.now(tz="UTC")
        df = df[(df.time + pd.Timedelta(minutes=interval) <= now) & (df.time >= now-pd.Timedelta(days=days))].copy()
        df["volume"] = pd.to_numeric(df["volume"], errors="raise")
        if (df.volume < 0).any() or not np.isfinite(df.volume).all():
            raise DataError("Ongeldig candlevolume.")
        df.attrs.update(source="Kraken OHLCV (publiek)", volume_is_actual=True,
                        timeframe=f"{interval} min", coin=coin, quote="USD",
                        note="Maximaal 719 gesloten candles per aanvraag; de feitelijke periode staat bij de grafiek.")
        out = validate(df)
        cache_put(key, pack_candles(out))
        return out

def import_csv(text, coin):
    """CSV time = UTC candle start; explicit OHLCV only, no fabricated candle volume."""
    from io import StringIO
    try:
        df = pd.read_csv(StringIO(text))
        required = {"time", "open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns) or not 60 <= len(df) <= 50000:
            raise DataError("CSV vereist 60–50.000 rijen met time,open,high,low,close,volume.")
        df = df[list(("time","open","high","low","close","volume"))].copy()
        df["time"] = pd.to_datetime(df["time"], utc=True, errors="raise")
        if df.time.isna().any() or df.time.duplicated().any():
            raise DataError("Dubbele of ontbrekende tijdstippen.")
        df = df.sort_values("time").reset_index(drop=True)
        deltas = df.time.diff().dropna()
        if (deltas <= pd.Timedelta(0)).any() or deltas.nunique() != 1:
            raise DataError("CSV moet vaste candle-intervallen hebben, zonder gaten.")
        interval = deltas.iloc[0]
        if interval < pd.Timedelta(minutes=1):
            raise DataError("Gebruik candles van minimaal 1 minuut.")
        df["volume"] = pd.to_numeric(df.volume, errors="raise")
        if not np.isfinite(df.volume).all() or (df.volume < 0).any():
            raise DataError("Ongeldig volume.")
        df = df[df.time + interval <= pd.Timestamp.now(tz="UTC")].copy()
        df.attrs.update(source="CSV OHLCV (door gebruiker aangeleverd)", coin=coin,
                        volume_is_actual=True, timeframe=str(interval), quote="USD",
                        note="CSV-prijzen moeten in USD staan; bron en correctheid zijn niet onafhankelijk geverifieerd.")
        return validate(df)
    except DataError:
        raise
    except (ValueError, TypeError, KeyError) as exc:
        raise DataError("CSV kon niet worden gelezen; gebruik ISO-8601 UTC-tijden en numerieke OHLCV-kolommen.") from exc




BINANCE_SYMBOLS=dict(zip(COINS,["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","DOTUSDT","LTCUSDT","BCHUSDT","UNIUSDT"]))

# Explicit CoinGecko IDs; do not infer exchange identities from ambiguous ticker symbols.
BINANCE_SYMBOLS.update({"binancecoin":"BNBUSDT","tron":"TRXUSDT","zcash":"ZECUSDT","hyperliquid":"HYPEUSDT","stellar":"XLMUSDT","sui":"SUIUSDT",
    "the-open-network":"TONUSDT","hedera-hashgraph":"HBARUSDT","shiba-inu":"SHIBUSDT","aptos":"APTUSDT",
    "near":"NEARUSDT","internet-computer":"ICPUSDT","ethereum-classic":"ETCUSDT","aave":"AAVEUSDT",
    "filecoin":"FILUSDT","cosmos":"ATOMUSDT","arbitrum":"ARBUSDT","optimism":"OPUSDT",
    "pepe":"PEPEUSDT","ondo-finance":"ONDOUSDT","render-token":"RENDERUSDT"})

class HistoricalProvider:
    """Paginated public OHLCV. Dedicated data-only domain; no credentials or trading routes."""
    def candles(self,coin="bitcoin",days=1095,interval=240,progress=None):
        from storage import cache_get,cache_put
        if coin not in BINANCE_SYMBOLS or interval not in (60,240,1440) or not 7<=days<=1825:
            raise DataError("Historie vereist een bekende coin, 1u/4u/1d en maximaal vijf jaar.")
        end=int(pd.Timestamp.now(tz="UTC").floor(f"{interval}min").timestamp()*1000)-1
        step=interval*60_000
        start=end+1-days*86_400_000
        key=f"historical-v1:{coin}:{days}:{interval}:{end//3_600_000}"
        stored=cache_get(key,ttl=3600)
        if stored:
            if progress:progress("Historische data uit lokale cache geladen.")
            return unpack_candles(stored)
        cursor=start;rows=[]
        with requests.Session() as session:
            for page in range(50):
                if progress:progress(f"Historie laden: {len(rows):,} candles; pagina {page+1}.")
                try:
                    response=session.get("https://data-api.binance.vision/api/v3/klines",
                        params={"symbol":BINANCE_SYMBOLS[coin],"interval":{60:"1h",240:"4h",1440:"1d"}[interval],
                                "startTime":cursor,"endTime":end,"limit":1000},timeout=25)
                    if response.status_code in (418,429):
                        raise DataError("Historische databron begrenst aanvragen; probeer later opnieuw.")
                    if response.status_code in (403,451):
                        raise DataError("Historische databron is niet toegankelijk in deze regio. Gebruik een OHLCV-CSV.")
                    response.raise_for_status();batch=response.json()
                except (requests.RequestException,ValueError) as exc:
                    if isinstance(exc,DataError):raise
                    raise DataError("Historische data niet bereikbaar; geen vervanging door demodata.") from exc
                if not isinstance(batch,list):raise DataError("Ongeldig antwoord van historische databron.")
                if not batch:break
                if any(not isinstance(x,list) or len(x)<7 for x in batch):
                    raise DataError("Historische candle mist verplichte velden.")
                last=int(batch[-1][0])
                if last<cursor:raise DataError("Historische paginering maakte geen voortgang.")
                for row in batch:
                    opened=int(row[0]);closed=int(row[6])
                    if cursor<=opened<=end and closed<=end:
                        rows.append({"time":pd.to_datetime(opened,unit="ms",utc=True),
                                     "open":float(row[1]),"high":float(row[2]),"low":float(row[3]),
                                     "close":float(row[4]),"volume":float(row[5])})
                cursor=last+step
                if cursor>end or len(batch)<1000:break
            else:raise DataError("Historie overschrijdt de limiet van 50 pagina's.")
        if len(rows)<60:raise DataError("Te weinig historische candles beschikbaar voor deze markt.")
        df=pd.DataFrame(rows)
        if not np.isfinite(df.volume).all() or (df.volume<0).any():raise DataError("Ongeldig candlevolume.")
        df.attrs.update(source="Historische OHLCV (Binance publiek)",coin=coin,quote="USDT",volume_is_actual=True,
                        timeframe=f"{interval} min",requested_days=days,
                        note="Prijzen in USDT, niet USD. Publieke data zonder account; beschikbaarheid hangt af van noteringsdatum en regio.")
        result=validate(df);cache_put(key,pack_candles(result))
        return result

