"""Frozen paper protocol; fee sensitivity is not a venue-specific derivatives backtest."""
import hashlib
import json
from pathlib import Path
from research import run,stress_parameters,benchmark
from strategies import REFERENCE_STRATEGIES

PROTOCOL_ID="trend-pullback-v1-2026-10-17"
COHORT=("bitcoin","ethereum","solana")
COST_SOURCES=[
 {"venue":"Binance USDⓈ-M","taker_pct":.05,"status":"Rekenvoorbeeld uit officiële uitleg; actueel accounttarief niet vastgesteld","url":"https://www.binance.com/en/support/faq/detail/360033544231","schedule":"https://www.binance.com/en/fee/futureFee"},
 {"venue":"Kraken Futures tier 1","taker_pct":.05,"status":"Publiek instaptarief; accountvolume en product controleren","url":"https://www.kraken.com/features/fee-schedule"},
 {"venue":"Coinbase International perps public tier 10","taker_pct":.04,"status":"International Exchange, geen Coinbase Advanced-spot of US-futures","url":"https://help.coinbase.com/en/international-exchange/trading-deposits-withdrawals/international-exchange-fees"}]

def reference_params(borrow=.02):
    return {"trade_mode":"both","trend_filter":False,"cooldown_bars":0,"max_holding_bars":0,
            "short_borrow_daily_pct":borrow,"ema_fast":8,"ema_slow":21,"rsi_period":14,
            "rsi_entry":30.,"rsi_exit":55.,"breakout_period":20,"volume_multiple":1.5,"stop_atr":1.5,"target_atr":3.}

def hypothesis_params(borrow=.02):
    return dict(reference_params(borrow),ema_fast=20,ema_slow=50,trend_filter=True,cooldown_bars=12,
                stop_atr=2.5,target_atr=5.,max_holding_bars=30)

def cost_review(fee_pct,slippage_pct,borrow_pct):
    return {"checked":"2026-10-17","current":{"fee_pct":fee_pct,"slippage_pct":slippage_pct,"short_borrow_daily_pct":borrow_pct},
            "sources":COST_SOURCES,"verdict":"Accountkosten niet volledig gevalideerd: scenarioanalyse",
            "limits":["Alle fills worden als taker gemodelleerd; fee aan beide zijden. Slippage  is een aanname, geen gemeten orderboekuitvoering.",
                      "De historische candles zijn Binance SPOT in USDT. Kraken- en Coinbase-fees veranderen alleen een rekenscenario, niet de koersbron of quotevaluta.",
                      "Perpetual funding, margin-openingskosten, rollover, liquidaties, spreads per beurs en regio-/accounttoegang worden niet gereconstrueerd.",
                      "Het vaste shortleentarief is een simulatieproxy, geen historische funding of gevalideerde marginrente. Ook longs kunnen bij perpetuals funding betalen.",
                      "Lage fee-resultaten zijn dus geen bevestigde beursrendementen. Spot-margin en perpetuals hebben verschillende kostenmodellen."]}

def protocol_coin(df,capital,fee_pct,slippage_pct,borrow_pct=.02,progress=None):
    if len(df)<1200:raise ValueError("Protocol vereist minstens 1.200 gesloten candles.")
    if not df.attrs.get("volume_is_actual"):raise ValueError("Protocol vereist echt candlevolume voor de breakoutreferentie.")
    durations=df.time.diff().dropna().dt.total_seconds()
    if len(durations) and float(durations.median())!=14400:raise ValueError("Het vaste protocol gebruikt uitsluitend 4-uurscandles.")
    n=len(df);bounds=[0,round(n*.6),round(n*.7),round(n*.8),n]
    names=("Ontwikkeling 60%","Testvenster 1 · 10%","Testvenster 2 · 10%","Laatste 20%")
    base=reference_params(borrow_pct);new=hypothesis_params(borrow_pct)
    scenarios=[{"id":"huidig","label":"Huidig kostenmodel","fee_pct":fee_pct,"slippage_pct":slippage_pct}]
    # Same execution model and carry in every scenario, only fee sensitivity changes.
    for fee in (.05,.04):scenarios.append({"id":"fee"+str(fee),"label":f"Alleen feegevoeligheid {fee:.2f}% per zijde","fee_pct":fee,"slippage_pct":slippage_pct})
    rows=[]
    for strategy,label in [*REFERENCE_STRATEGIES.items(),("pullback","Trend-pullback v1")]:
        p=new if strategy=="pullback" else base
        for scenario in scenarios:
            fee=scenario["fee_pct"]/100;slip=scenario["slippage_pct"]/100
            for k,(left,right) in enumerate(zip(bounds,bounds[1:])):
                if progress:progress(label+": "+names[k]+" · "+scenario["label"])
                m=run(df,strategy,capital,fee,slip,left,right,p)["metrics"]
                stress=run(df,strategy,capital,min(fee*2,.01),min(slip*2,.02),left,right,stress_parameters(p))["metrics"]
                rows.append({"strategy":strategy,"label":label,"scenario":scenario["id"],"scenario_label":scenario["label"],
                             "period":k,"period_label":names[k],"from":df.iloc[left].time.isoformat(),"to":df.iloc[right-1].time.isoformat(),
                             "parameters":dict(p),"metrics":m,"stress":stress,
                             "benchmark_25pct":benchmark(df,capital,fee,slip,left,right,.25)})
    code={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ("engine.py","strategies.py","protocol.py")}
    data_hash=hashlib.sha256(df[["time","open","high","low","close","volume"]].to_json(orient="records",date_format="iso",date_unit="ms").encode()).hexdigest()
    return {"protocol":PROTOCOL_ID,"candles":n,"bounds":bounds,"references":dict(REFERENCE_STRATEGIES),
            "reference_parameters":base,"hypothesis_parameters":new,"data_sha256":data_hash,"code_sha256":code,
            "costs":cost_review(fee_pct,slippage_pct,borrow_pct),"scenarios":scenarios,"rows":rows,
            "notes":["Vaste hypothese: herstel over EMA20 binnen een EMA50/200-trend. LONG bij close boven EMA200, EMA50 boven EMA200 en stijgende EMA200 over 20 candles; SHORT gespiegeld.",
                     "Instap uitsluitend na kruising van close over EMA20; uitvoering op de volgende candle-open. Exit bij close voorbij EMA50 in tegengestelde richting, op de volgende open.",
                     "ATR14 stop 2,5× en target 5× bij instap; maximaal 30 actieve candles, twaalf volledige candles wachttijd na een exit. Risico 0,25%, instapblootstelling maximaal 25%; geen hefboom.",
                     "Alle referenties staan vast op v0.9-basisregels in BOTH. Geen optimalisatie of selectie op ontwikkeling, testvensters, coins of kostenscenario's. Alle uitkomsten blijven zichtbaar.",
                     "Ontwikkeling 60%, daarna twee afzonderlijke 10%-vensters en laatste 20%. Iedere combinatie start met nieuw fictief kapitaal en lege positie; geen samengestelde portefeuille.",
                     "Bitcoin en Solana zijn eerder onderzocht; historische resultaten zijn niet nieuw ongezien bewijs. Ook deze vaste nieuwe hypothese kan verlieslatend zijn.",
                     "Vooraf vastgelegde coins BTC, ETH, SOL op 4u en drie jaar historie. Dit is geen willekeurige marktsteekproef. Historische beschikbaarheid en datagaten blijven zichtbaar.",
                     "Minder dan 30 trades per testvenster is onvoldoende bewijs; ook boven die grens bestaat geen winstgarantie. Geen automatische activering van een winnaar.",
                     "De referentieparameters, protocolversie, codehashes en candlehash worden bij het resultaat opgeslagen. Latere programmaversies mogen oude rapporten niet stilzwijgend overschrijven."]}
