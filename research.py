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
                     "test":test["metrics"],"folds":folds,"cost_stress_return_pct":stress["return_pct"],"cost_stress":stress["metrics"],
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




def bot_arena(df,capital,fee,slip,parameters=None,progress=None):
    """Nine fixed contestants; same candles/capital/costs, no winner selection."""
    base=config(parameters).model_dump();bots=[];common=None
    rules={"ema":"Kruising snelle/trage EMA; uitstap bij tegengestelde trend.",
           "rsi":"LONG: RSI herstelt over instapdrempel; SHORT: neerwaartse kruising van gespiegelde drempel.",
           "breakout":"Uitbraak voorbij vorige highs/lows met echt candlevolume; uitstap op EMA."}
    for direction in ("long","short","both"):
        if progress:progress("Botarena: "+direction.upper()+" testen op dezelfde candles.")
        report=research(df,capital,fee,slip,dict(base,trade_mode=direction));common=report
        for row in report["strategies"]:
            row=dict(row,id=row["strategy"]+"-"+direction,direction=direction,
                     rule=rules[row["strategy"]],label=row["label"]+" · "+direction.upper())
            if not row.get("skipped"):
                sides=row["test"]["direction_breakdown"]["sides"].values()
                net=sum(x["net_pnl"] for x in sides);cost=sum(x["total_costs"] for x in sides)
                row["closed_net_pnl"]=round(net,6);row["closed_costs"]=round(cost,6)
                row["net_per_trade"]=round(net/row["test"]["trades"],6) if row["test"]["trades"] else None
                row["assessment"]=("Te weinig trades" if row["test"]["trades"]<30 else
                                   "Negatief na kosten" if row["test"]["return_pct"]<=0 else
                                   "Kwetsbaar voor kosten" if row["cost_stress_return_pct"]<=0 else "Verder onderzoeken")
            bots.append(row)
    cut=round(len(df)*.7)
    return {"bots":bots,"base_parameters":base,"test_from":df.iloc[cut].time.isoformat(),
            "test_to":df.iloc[-1].time.isoformat(),"benchmark":common["benchmark"],
            "benchmark_25pct":common["benchmark_25pct"],"notes":[
            "Negen vaste profielen: EMA, RSI en breakout × LONG, SHORT en BOTH. Geen LLM-agenten; uitvoering volgt vaste regels.",
            "Identieke candles, kapitaal, kosten en 70/30-grens. Alleen strategie en handelsrichting verschillen; overige instellingen blijven gelijk.",
            "Geen rangschikking, automatische winnaarselectie, optimalisatie of uitschakeling van verliezers. Alle profielen blijven zichtbaar.",
            "Drie tijdvensters overlappen niet met elkaar, maar deels met de 30%-test. Herhaald bekijken maakt testdata niet meer ongezien.",
            "Profielen hebben verschillende blootstelling; dit is geen portefeuille of vergelijking bij gelijk risico.",
            "Netto/trade en totale kosten betreffen gesloten trades. Slippage is al in fills verwerkt; niet opnieuw aftrekken.",
            "Minder dan 30 trades is onvoldoende bewijs; een positieve uitkomst of kostenstress bewijst geen toekomstige winst.",
            "Een profiel gebruiken laadt de vastgelegde strategie en richting in het formulier. Er start geen handel of nieuwe test.",
            "Simulatie zonder hefboom. Shorts gebruiken het bestaande vereenvoudigde onderpand- en leenkostenmodel."]}


def filter_experiment(df,strategy,capital,fee,slip,parameters=None,progress=None):
    """Predefined ablation. No candidate scoring or selection on any test window."""
    n=len(df)
    if n<600:raise ValueError("Filteronderzoek vereist minimaal 600 gesloten candles; kies langere historie.")
    base=config(parameters).model_dump()
    base.update(trend_filter=False,cooldown_bars=0)
    specs=[("basis","Huidige regels",dict(base)),
           ("rust","12 candles wachten",dict(base,cooldown_bars=12)),
           ("trend","Wachttijd + trendfilter",dict(base,cooldown_bars=12,trend_filter=True))]
    bounds=[round(n*x) for x in (.4,.533333333,.666666667,.8,1)]
    periods=[("ontwikkeling","Ontwikkeling · eerste 40%",0,bounds[0])]+[
        ("venster"+str(i+1),"Testvenster "+str(i+1),l,r) for i,(l,r) in enumerate(zip(bounds[:3],bounds[1:4]))]+[
        ("laatste","Laatste 20%",bounds[3],bounds[4])]
    variants=[]
    for key,label,p in specs:
        results=[]
        for period,name,left,right in periods:
            if progress:progress(label+": "+name)
            normal=run(df,strategy,capital,fee,slip,left,right,p)
            stress=run(df,strategy,capital,min(fee*2,.01),min(slip*2,.02),left,right,stress_parameters(p))
            results.append({"id":period,"label":name,"start":left,"end":right,
                            "from":df.iloc[left].time.isoformat(),"to":df.iloc[right-1].time.isoformat(),
                            "metrics":normal["metrics"],"stress":stress["metrics"]})
        variants.append({"id":key,"label":label,"parameters":p,"periods":results})
    return {"strategy":strategy,"variants":variants,"notes":[
        "Vooraf vaste hypothesen: basis; 12 candles wachten na iedere exit; dezelfde wachttijd plus EMA200-trendfilter. Geen optimalisatie of winnaarselectie.",
        "LONG alleen als de vorige gesloten candle boven EMA200 sluit én EMA200 hoger is dan 20 candles eerder. SHORT precies omgekeerd. Ontbrekende warm-up blokkeert instap.",
        "De 12 candles direct na een exit worden overgeslagen; de eerstvolgende instap mag op candle 13. Dit verlaagt niet noodzakelijk het totale aantal trades door veranderde posities en risicostops.",
        "Alleen entries worden gefilterd. Stops, targets, signal exits en harde risicolimieten veranderen niet. Iedere variant en periode start met nieuw kapitaal en zonder positie.",
        "Eerste 40% is ontwikkelcontext, daarna drie gescheiden testvensters tot 80% en laatste 20%. Parameters worden nergens gekozen op resultaten.",
        "Dezelfde data zijn al bekeken: de laatste 20% is geen nieuw ongezien bewijs. Variantscores vormen geen samengestelde rekening en verschillen in blootstelling.",
        "Dubbele kosten kunnen eerder een risicostop activeren; vergelijk ook blokkades en tradeaantallen, niet alleen eindrendement.",
        "EMA200 en de wachttijd zijn in candles, niet in vaste uren. Alle indicatorbeslissingen gebruiken uitsluitend eerdere gesloten candles."]}
