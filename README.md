# Analisi bot Coinrule + Strategia APEX Trend per TradingView

Analisi dei bot del report settimanale Coinrule ("Top Strategies Weekly"),
replica in Pine Script v5, backtest indipendente su 5 cripto e costruzione
di una strategia ottimizzata (APEX Trend) con buon rendimento e basso drawdown.

## ⚠️ Prima di tutto: come leggere i numeri di Coinrule

I numeri dell'email (es. "BB+RSI Short +15.53% in 30 giorni") **non sono una
prova di profittabilità**, per tre motivi:

1. **Finestra cortissima**: 7/30 giorni dicono quasi nulla. Qualunque strategia
   ha mesi buoni; conta il comportamento su anni e su regimi diversi (bull,
   bear, laterale).
2. **Selection bias**: Coinrule pubblica ogni settimana le *migliori* strategie
   di quella settimana. Le peggiori non le vedi. È come giudicare un casinò
   intervistando solo i vincitori.
3. **Niente drawdown**: mostrano il profitto realizzato, mai il rischio corso
   per ottenerlo.

### Verdetto sul backtest indipendente (2021 → giu 2026, daily, BTC/ETH/SOL/BNB/XRP)

| Bot Coinrule | CAGR medio | MaxDD medio | Verdetto |
|---|---|---|---|
| BB + RSI Short Selling | **-22.9%** | -75% | ❌ Il peggiore: shortare gli eccessi rialzisti in un asset che fa +10x è suicida. Il +15% del report è una settimana fortunata. |
| Range Trading (Solana) | -6.2% | -59% | ❌ Funziona solo nei laterali; nei trend forti compra i crolli senza protezione sufficiente. |
| Flash Crash | -3.4% | -46% | ❌ Idea sensata ma TP/SL fissi la rovinano: vince spesso ma perde di più quando il "crash" continua. |
| Buy + SL/TP | -2.2% | -50% | ❌ Troppo semplice: l'esito dipende solo dal rapporto TP/SL, le commissioni erodono tutto. |
| Scalping On Trend | -0.5% | -13% | ⚠️ Quasi pari: TP 2% / SL 1.5% sul daily genera tante operazioni mangiate dalle commissioni (su timeframe brevi può andare meglio). |
| Rebalance Trend Following | +9.7% | -58% | ⚠️ Profittevole ma DD inaccettabile: entra/esce troppo tardi. |
| MA Crossing (9/21) | +19.6% | -55% | ⚠️ L'unico concetto che regge: il trend following paga sulle cripto. Ma il DD resta enorme. |

**Conclusione**: dei 7 bot, solo quelli *trend following* hanno un edge reale
sulle cripto. Quelli *mean reversion* (BB short, range trading) perdono nel
lungo periodo. Da qui nasce APEX.

## 🏆 APEX Trend Strategy (la strategia costruita)

File: [`pinescript/apex_trend_strategy.pine`](pinescript/apex_trend_strategy.pine) — copia/incolla nel Pine Editor di TradingView, timeframe **1D**.

Regole:
- **Regime**: si opera solo se `close > EMA200` (mai contro il trend strutturale)
- **Entrata**: chiusura sopra il massimo di chiusura degli ultimi 30 giorni (breakout Donchian)
- **Uscite**: chiusura sotto EMA20 • trailing stop 4×ATR(14) • stop di emergenza -12%
- **Money management** (la vera differenza): si investe solo la frazione di
  capitale per cui il trailing stop costa ~10% dell'equity. Con volatilità alta
  si compra poco, con volatilità bassa di più. È questo che taglia il drawdown.

### Risultati backtest (2021 → giu 2026, commissioni 0.10% + slippage 0.05% per lato)

| Cripto | Rendimento tot. | CAGR | MaxDD | Sharpe | Trade | Win rate | Profit factor |
|---|---|---|---|---|---|---|---|
| BTC | +60.6% | 9.1% | -24.0% | 0.56 | 28 | 50.0% | 1.91 |
| ETH | +40.3% | 6.4% | -20.0% | 0.43 | 25 | 44.0% | 1.94 |
| SOL | +852.3% | 51.4% | -24.6% | 1.52 | 22 | 72.7% | 11.77 |
| BNB | +237.1% | 25.1% | -44.5% | 0.78 | 31 | 35.5% | 5.51 |
| XRP | +193.6% | 21.9% | -41.8% | 0.81 | 28 | 32.1% | 2.85 |

**Portafoglio (capitale diviso sulle 5 cripto): +276.8% totale, CAGR 27.7%,
MaxDD -17.0%, Sharpe 1.31.** Nel bear market 2022 (quando BTC faceva -65% e
SOL -94%) il portafoglio ha perso solo il 4.5%.

Il profit factor è positivo su **tutte e 5** le cripto e i parametri sono su un
plateau robusto (le combinazioni vicine danno risultati simili, vedi
`backtest/sweep_results.csv`): non è un risultato cucito sui dati.

## Struttura del repo

```
pinescript/
  apex_trend_strategy.pine      ← la strategia principale (TradingView, 1D)
  coinrule_replicas/            ← le 7 repliche dei bot Coinrule in Pine v5
backtest/
  engine.py                     ← motore event-driven (no lookahead, costi inclusi)
  strategies.py                 ← logica identica ai .pine
  tune.py                       ← sweep parametri
  run.py                        ← esegue tutto e genera results.md
  results.md                    ← report completo
data/                           ← OHLCV giornalieri 2021→2026 (fonte FMP)
```

Per riprodurre: `pip install pandas numpy && python3 backtest/run.py`

## Limiti e avvertenze

- Backtest ≠ futuro: 5.5 anni includono bull 2021, bear 2022, ripresa 23-25,
  ma il mercato può cambiare regime.
- Su TradingView i risultati possono differire leggermente (dati exchange
  diversi, esecuzione ordini di Pine).
- La strategia è **long-only spot**, pensata per essere eseguibile anche su
  Coinrule/exchange senza leva. Niente leva: il sizing a rischio fa già il lavoro.
- Non è consulenza finanziaria: testala in paper trading prima di metterci capitale.
