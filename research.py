"""Research comparisons with fixed rules; no parameter search or profit claims."""
import numpy as np
from engine import PaperEngine, run_backtest
from strategies import STRATEGIES

def benchmark(df, capital, fee, slip, start, end, exposure=1.0):
    part = df.iloc[start:end]
    entry = float(part.iloc[0].open) * (1+slip)
    qty = capital * exposure / (entry*(1+fee))
    cash = capital - qty*entry*(1+fee)
    curve = cash + qty*part.close.to_numpy(dtype=float)
    curve[-1] = cash + qty*float(part.iloc[-1].close)*(1-slip)*(1-fee)
    peak = np.maximum.accumulate(np.r_[capital, curve])[1:]
    return {"return_pct": round((float(curve[-1])/capital-1)*100,3),
            "max_drawdown_pct": round(float(np.max((peak-curve)/peak))*100,3),
            "exposure_pct": exposure*100}

def research(df, capital, fee, slip):
    n = len(df)
    if n < 120:
        raise ValueError("Vergelijking vereist minimaal 120 gesloten candles.")
    cut = round(n*.7)
    rows = []
    for strategy, label in STRATEGIES.items():
        if strategy == "breakout" and not df.attrs.get("volume_is_actual"):
            rows.append({"strategy": strategy, "label": label, "skipped": "Geen echt candlevolume."})
            continue
        result = run_backtest(df, strategy, capital, fee, slip)
        # Three chronological, disjoint test windows. Prior history only warms indicators.
        folds = []
        edges = [round(n*x) for x in (.4,.6,.8,1)]
        for left,right in zip(edges,edges[1:]):
            snap = PaperEngine(df,strategy,capital,fee,slip,start=left,end=right).finish()
            folds.append({"from":df.iloc[left].time.isoformat(), "to":df.iloc[right-1].time.isoformat(),
                          "return_pct":snap["return_pct"], "trades":snap["metrics"]["trades"],
                          "max_drawdown_pct":snap["max_drawdown_pct"]})
        stressed = PaperEngine(df,strategy,capital,min(fee*2,.01),min(slip*2,.02),start=cut,end=n).finish()
        rows.append({"strategy":strategy, "label":label, "train":result["train"]["metrics"],
                     "test":result["test"]["metrics"], "folds":folds,
                     "cost_stress_return_pct":stressed["return_pct"],
                     "warnings":result["warnings"]})
    return {"strategies": rows, "benchmark": benchmark(df,capital,fee,slip,cut,n),
            "benchmark_25pct": benchmark(df,capital,fee,slip,cut,n,.25),
            "notes":["Vaste regels; geen automatische optimalisatie of selectie van een winnaar.",
                     "De drie tijdvensters overlappen niet met elkaar, maar wel deels met de 70/30-test. Dit zijn geen onafhankelijke bevestigingen.",
                     "Elke test start opnieuw met fictief kapitaal en een lege positie; indicatoren gebruiken alleen eerdere candles.",
                     "Buy-and-hold met 100% en 25% blootstelling is geen gelijk risicoprofiel; kosten gelden aan beide zijden.",
                     "Weinig trades, synthetische data en meerdere vergelijkingen beperken conclusies. Geen winstgarantie."]}
