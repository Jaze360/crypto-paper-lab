"""Fixed-rule comparisons and chronological parameter selection, with final holdout."""
import numpy as np
from engine import PaperEngine, run_backtest
from strategies import STRATEGIES,config

def benchmark(df,capital,fee,slip,start,end,exposure=1.):
    part=df.iloc[start:end]
    entry=float(part.iloc[0].open)*(1+slip)
    qty=capital*exposure/(entry*(1+fee));cash=capital-qty*entry*(1+fee)
    curve=cash+qty*part.close.to_numpy(dtype=float)
    curve[-1]=cash+qty*float(part.iloc[-1].close)*(1-slip)*(1-fee)
    peak=np.maximum.accumulate(np.r_[capital,curve])[1:]
    return {"return_pct":round((float(curve[-1])/capital-1)*100,3),
            "max_drawdown_pct":round(float(np.max((peak-curve)/peak))*100,3),"exposure_pct":exposure*100}

def run(df,strategy,capital,fee,slip,left,right,parameters):
    return PaperEngine(df,strategy,capital,fee,slip,start=left,end=right,parameters=parameters).finish(record=False)

def stress_parameters(parameters):
    p=config(parameters).model_dump()
    p["short_borrow_daily_pct"]=min(1.,p["short_borrow_daily_pct"]*2)
    return p

def research(df,capital,fee,slip,parameters=None):
    n=len(df)
    if n<120:raise ValueError("Vergelijking vereist minimaal 120 gesloten candles.")
    p=config(parameters).model_dump();cut=round(n*.7);rows=[]
    for strategy,label in STRATEGIES.items():
        if strategy=="breakout" and not df.attrs.get("volume_is_actual"):
            rows.append({"strategy":strategy,"label":label,"skipped":"Geen echt candlevolume."});continue
        train=run(df,strategy,capital,fee,slip,0,cut,p)
        test=run(df,strategy,capital,fee,slip,cut,n,p)
        edges=[round(n*x) for x in (.4,.6,.8,1)]
        folds=[]
        for left,right in zip(edges,edges[1:]):
            result=run(df,strategy,capital,fee,slip,left,right,p)
            folds.append({"from":df.iloc[left].time.isoformat(),"to":df.iloc[right-1].time.isoformat(),
                          **result["metrics"]})
        stress=run(df,strategy,capital,min(fee*2,.01),min(slip*2,.02),cut,n,stress_parameters(p))
        rows.append({"strategy":strategy,"label":label,"parameters":p,"train":train["metrics"],
                     "test":test["metrics"],"folds":folds,"cost_stress_return_pct":stress["return_pct"],
                     "warnings":[f"{name}: slechts {r['metrics']['trades']} transacties; onvoldoende bewijs."
                                 for name,r in (("train",train),("test",test)) if r["metrics"]["trades"]<30]})
    return {"strategies":rows,"benchmark":benchmark(df,capital,fee,slip,cut,n),
            "benchmark_25pct":benchmark(df,capital,fee,slip,cut,n,.25),
            "notes":["Ingestelde parameters, zonder selectie op de laatste testperiode.",
                     "Drie tijdvensters overlappen niet met elkaar, maar wel met de 70/30-test.",
                     "Elke periode start met leeg fictief account; alleen eerdere candles warmen indicatoren op.",
                     "Tijd in markt is het aandeel candles met een positie na de beslissingen op candle-open; geen exacte intrabar tijd.",
                     "Gemiddelde blootstelling is de gemiddelde positie/vermogen-verhouding op candle-open, inclusief lege candles.",
                     "Benchmarks zijn kopen-en-vasthouden LONG, ook bij shortonderzoek; risicoprofielen verschillen.",
                     "Shorts gebruiken 100% onderpand en vaste leenkosten; geen echte financiering, liquidatie of levergarantie.",
                     "Kostenstress verdubbelt ook shortleenkosten, tot de ingestelde modelgrens.",
                     "Meerdere tests en weinig trades beperken conclusies."]}

def candidates(strategy,parameters):
    base=config(parameters).model_dump();result=[base]
    changes={"ema":[{"ema_fast":5,"ema_slow":20},{"ema_fast":12,"ema_slow":50},{"ema_fast":20,"ema_slow":100}],
             "rsi":[{"rsi_entry":25,"rsi_exit":55},{"rsi_entry":35,"rsi_exit":60},{"rsi_period":21,"rsi_entry":30,"rsi_exit":55}],
             "breakout":[{"breakout_period":10,"volume_multiple":1.2},{"breakout_period":40,"volume_multiple":1.5},{"breakout_period":60,"volume_multiple":2.}]}[strategy]
    for change in changes:
        p=config(dict(base,**change)).model_dump()
        if p not in result:result.append(p)
    return result

def choose(df,strategy,capital,fee,slip,left,right,options):
    # Deterministic scoring and minimum count are fixed before any test window is read.
    results=[]
    for p in options:
        snap=run(df,strategy,capital,fee,slip,left,right,p)
        m=snap["metrics"]
        score=m["return_pct"]-m["max_drawdown_pct"] if m["trades"]>=5 else None
        results.append({"parameters":p,"metrics":m,"score":score})
    eligible=[x for x in results if x["score"] is not None]
    chosen=max(eligible,key=lambda x:x["score"]) if eligible else results[0]
    return chosen,results,bool(eligible)

def walk_forward(df,strategy,capital,fee,slip,parameters=None,progress=None):
    n=len(df);hold=round(n*.8)
    if n<600:raise ValueError("Walk-forward vereist minimaal 600 gesloten candles; kies langere historie.")
    if strategy=="breakout" and not df.attrs.get("volume_is_actual"):raise ValueError("Walk-forward breakout vereist candlevolume.")
    options=candidates(strategy,parameters)
    bounds=[round(n*x) for x in (.4,.533333333,.666666667,.8)]
    folds=[]
    for index,(left,right) in enumerate(zip(bounds,bounds[1:])):
        if progress:progress(f"Walk-forward venster {index+1}/3: parameters kiezen op eerdere data.")
        chosen,scored,eligible=choose(df,strategy,capital,fee,slip,0,left,options)
        result=run(df,strategy,capital,fee,slip,left,right,chosen["parameters"])
        base=benchmark(df,capital,fee,slip,left,right,.25)
        direction=(float(df.iloc[right-1].close)/float(df.iloc[left].open)-1)*100
        folds.append({"train_start":0,"train_end":left,"test_start":left,"test_end":right,
                      "from":df.iloc[left].time.isoformat(),"to":df.iloc[right-1].time.isoformat(),
                      "selected":chosen["parameters"],"selection_valid":eligible,"candidates":scored,
                      "test":result["metrics"],"benchmark_25pct":base,
                      "market_return_pct":round(direction,3),
                      "market_period":"stijgend" if direction>5 else "dalend" if direction< -5 else "zijwaarts"})
    if progress:progress("Parameters vastzetten op eerste 80%; daarna pas de laatste 20% testen.")
    # Selection sees only [0,hold), never the final holdout prices.
    chosen,scored,eligible=choose(df,strategy,capital,fee,slip,0,hold,options)
    final=run(df,strategy,capital,fee,slip,hold,n,chosen["parameters"])
    stress=run(df,strategy,capital,min(fee*2,.01),min(slip*2,.02),hold,n,stress_parameters(chosen["parameters"]))
    return {"strategy":strategy,"folds":folds,"holdout_start":hold,"holdout_end":n,
            "holdout_from":df.iloc[hold].time.isoformat(),"holdout_to":df.iloc[-1].time.isoformat(),
            "selected":chosen["parameters"],"selection_valid":eligible,"selection":scored,
            "holdout":final["metrics"],"holdout_stress":stress["metrics"],
            "benchmark":benchmark(df,capital,fee,slip,hold,n),
            "benchmark_25pct":benchmark(df,capital,fee,slip,hold,n,.25),
            "notes":["Selectieregel vooraf vast: netto rendement minus max drawdown; minimaal 5 trainingstrades, anders basisparameters.",
                     "Drie uitbreidende ontwikkelperioden en daaropvolgende gescheiden testvensters; laatste 20% buiten alle parameterkeuzes.",
                     "Laatste test wordt pas na selectie uitgevoerd. Herhaald onderzoeken van dezelfde dataset maakt die periode voor jou niet meer ongezien.",
                     "Selectie blijft beperkt tot maximaal vier vooraf vastgelegde kandidaten; geen winstgarantie.",
                     "Elke periode herstart fictief kapitaal en posities; rendementen zijn geen samengestelde live rekening.",
                     "Marktperiode is achteraf ingedeeld op prijsverandering (>5% stijgend, <-5% dalend); geen voorspellend signaal.",
                     "Minder dan 30 testtrades blijft onvoldoende bewijs, ook na parameterselectie.",
                     "Handelsrichting blijft vast tijdens parameterkeuze. Shortleenkosten worden meegenomen; stress verdubbelt ze.",
                     "Benchmarks zijn long kopen-en-vasthouden; shorts zijn een vereenvoudigd onderpandmodel zonder echte margin-liquidatie."]}

