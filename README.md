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
| BB + RSI Short Selling | **-17.6%** | -68% | ❌ Il peggiore: shortare gli eccessi rialzisti in un asset che fa +10x è suicida. Il +15% del report è una settimana fortunata. |
| Flash Crash | -10.7% | -54% | ❌ Idea sensata ma TP/SL fissi la rovinano: vince spesso ma perde di più quando il "crash" continua. |
| Range Trading (Solana) | -7.7% | -64% | ❌ Funziona solo nei laterali; nei trend forti compra i crolli senza protezione sufficiente. |
| Buy + SL/TP | -1.5% | -46% | ❌ Troppo semplice: l'esito dipende solo dal rapporto TP/SL, le commissioni erodono tutto. |
| Scalping On Trend | +0.9% | -10% | ⚠️ Quasi pari: TP 2% / SL 1.5% sul daily genera tante operazioni mangiate dalle commissioni (su timeframe brevi può andare meglio). |
| Rebalance Trend Following | +9.7% | -58% | ⚠️ Profittevole ma DD inaccettabile: entra/esce troppo tardi. |
| MA Crossing (9/21) | +21.4% | -51% | ⚠️ L'unico concetto che regge: il trend following paga sulle cripto. Ma il DD resta enorme. |

**Conclusione**: dei 7 bot, solo quelli *trend following* hanno un edge reale
sulle cripto. Quelli *mean reversion* (BB short, range trading) perdono nel
lungo periodo. Da qui nasce APEX.

## 🏆 APEX Trend Strategy v2 (la strategia costruita)

File: [`pinescript/apex_trend_strategy.pine`](pinescript/apex_trend_strategy.pine) — copia/incolla nel Pine Editor di TradingView, timeframe **1D**. Include alert JSON pronti per webhook (Coinrule/3Commas), tabella statistiche sul grafico e tutti i parametri configurabili.

Regole:
- **Regime locale**: `close > EMA200` **e** `EMA50 > EMA200` (mai contro il trend)
- **Regime di mercato**: le altcoin entrano solo se **anche BTC** è sopra la sua
  EMA200 — quando BTC è in bear, le alt sanguinano: questo filtro da solo
  migliora CAGR *e* drawdown (vedi `backtest/experiments.csv`)
- **Entrata**: chiusura sopra il massimo di chiusura degli ultimi 30 giorni (breakout Donchian)
- **Uscite**: chiusura sotto EMA20 • trailing stop 4×ATR(14) • stop di emergenza -12%
- **Money management** (dove si vince davvero): posizione dimensionata perché lo
  stop costi ~10% dell'equity, **con cap del 30% di capitale per coin**. Il cap
  forza la diversificazione: nel test taglia il DD di 10 punti *e aumenta* il CAGR.

### Risultati per singola cripto (2021 → giu 2026, costi 0.15%/lato)

| Cripto | Rendimento tot. | CAGR | MaxDD | Sharpe | Trade | Win rate | Profit factor |
|---|---|---|---|---|---|---|---|
| BTC | +61.1% | 9.2% | -24.1% | 0.56 | 28 | 50.0% | 1.91 |
| ETH | +40.9% | 6.5% | -19.9% | 0.43 | 25 | 44.0% | 1.94 |
| SOL | +945.9% | 54.0% | -24.5% | 1.56 | 22 | 72.7% | 16.89 |
| BNB | +238.4% | 25.2% | -44.4% | 0.78 | 31 | 35.5% | 5.51 |
| XRP | +171.0% | 20.1% | -46.8% | 0.75 | 29 | 31.0% | 2.85 |

### Portafoglio reale a capitale condiviso (un conto, 5 cripto insieme)

Simulato in [`backtest/portfolio.py`](backtest/portfolio.py): un solo conto,
sizing a rischio sull'equity corrente, cap 30%/posizione, priorità ai segnali
con momentum più forte. Profit factor positivo su tutte e 5 le coin.

| Periodo | CAGR | MaxDD | Sharpe | Sortino | Calmar | Profit factor |
|---|---|---|---|---|---|---|
| **Full 2021→2026** | **84.7%** | **-24.9%** | 1.71 | 1.71 | 3.41 | 6.92 |
| **Out-of-sample 2024→2026** (parametri congelati) | **19.1%** | **-22.2%** | 0.79 | 0.64 | 0.86 | 3.61 |

Rendimenti per anno: 2021 **+938%** · 2022 **0%** (bear: la strategia resta
fuori) · 2023 **+67%** · 2024 **+40%** · 2025 **+10%** · 2026 YTD ~0%.

### Validazione (la parte che i report di marketing non mostrano)

- **Walk-forward**: parametri ottimizzati SOLO su 2021-23 e congelati →
  su 2024-26 la strategia resta profittevole (PF 3.6). La config migliore
  in-sample (30/3.0/20) e quella finale (30/4.0/20) sono adiacenti sul plateau:
  niente overfitting da picco isolato.
- **Monte Carlo** (2000 block-bootstrap): DD mediano -32%, 95° percentile
  -48%. Tradotto: il -24.9% realizzato è nella parte fortunata della
  distribuzione, **pianifica come se un -40/50% potesse accadere**.
- **Stress test costi doppi** (0.30%/lato): CAGR 84.7% → 81.8%. Robusta.
- **Senza i 5 trade migliori**: profit factor ancora 2.8 → l'edge non dipende
  da pochi colpi fortunati.
- Report completo: [`backtest/validation_report.txt`](backtest/validation_report.txt),
  lista trade: [`backtest/trades_final.csv`](backtest/trades_final.csv),
  grafici: `backtest/charts/`.

**Aspettativa realistica**: il CAGR full-period (85%) è gonfiato dal bull 2021.
Il numero su cui ragionare è l'out-of-sample: **~15-20% annuo con DD ~-20/25%**
in condizioni normali, con upside enorme quando arriva un bull market vero —
e soprattutto capitale protetto nei bear (2022: 0% contro -65% di BTC).

## 🚀 APEX-X: la versione aggressiva (target 100% annuo)

> Prima la verità: **un "100% annuo garantito" non esiste**. APEX-X è quanto di
> più vicino si possa costruire onestamente, e si paga in rischio. Tutto in
> [`backtest/aggressive.py`](backtest/aggressive.py) e `aggressive_results.csv`.

Differenze rispetto ad APEX base:
- **Rotazione momentum**: opera solo le **top-3 coin per momentum 90 giorni**
  (lo screener [`apex_momentum_screener.pine`](pinescript/apex_momentum_screener.pine)
  replica la classifica su TradingView)
- **Rischio 15% / cap 50%** per posizione (vs 10%/30%)
- **Leva 2×** (futures/margin; funding simulato al 12%/anno, stress fino al 50%)
- **Trailing più largo 5×ATR** (lascia correre i trend con la leva)

| | full 2021→26 | OOS 2024→26 | Monte Carlo |
|---|---|---|---|
| **APEX base** | CAGR 85% · DD -25% | CAGR 19% · DD -22% | DD p95 **-48%** |
| **APEX-X** | **CAGR 116%** · DD -37% | **CAGR 75%** · DD -31% | DD p95 **-60%**, p99 -69% |

Per anno (APEX-X): 2021 **+597%** · 2022 **0%** · 2023 **+127%** · 2024 **+238%** · 2025 +17%.

Robustezza: i parametri vicini (rischio 12-18, cap 40-50, leva 1.75-2, trailing
4.5-5.5) danno tutti full ~93-126% e OOS ~57-76% → plateau, non overfitting.
Stress: con funding al 50%/anno o costi doppi resta sopra il 110% full / 69% OOS.
Il motore è coperto da test automatici anti-lookahead (`backtest/test_engine.py`)
e i dati FMP sono stati verificati contro Crypto.com Exchange (scarti ≤0.2%).
Senza leva il motore di rotazione si spegne (OOS 14%): la leva qui non è un
vezzo, è strutturale — e infatti il conto va gestito su futures.

**Il prezzo del biglietto**: la media storica supera il 100%, ma NON ogni anno
(2022: 0%, 2025: +17%) e il Monte Carlo dice di **pianificare un drawdown del
-40/-60%**. Se un -50% ti farebbe staccare la spina, usa APEX base: la
strategia migliore è quella che riesci a seguire nei momenti peggiori.

Su TradingView: stessa strategia `apex_trend_strategy.pine` con preset
APEX-X (rischio 15, cap 50, leva 2, trailing 5) sulle coin indicate dallo
screener. Il funding dei perpetual non è simulato da TradingView: i numeri
reali saranno leggermente più bassi.

## ⚡ APEX-X2: piu' trade, universo a 10 coin (l'evoluzione iperattiva)

Richiesta: piu' operazioni. Risposta misurata (`backtest/report.py`,
`APEX_X2_report.md`): universo raddoppiato a **10 coin** (+ADA, DOGE, LINK,
AVAX, DOT), rotazione **top-5**, max **6 posizioni**, canale piu' veloce
(**20gg**), piu' i 3 miglioramenti promossi dal banco di prova
(`improvements.py`): **filtro volatilita' 85° pctile** (blocca i breakout in
blow-off), **trailing chandelier**, **protezione equity-curve** (rischio
dimezzato quando il sistema stesso e' in drawdown). Bocciati dopo test:
smart-exit, piramidazione, breadth-scaling, momentum-required (degradavano
l'out-of-sample).

| | APEX-X (5 coin) | **APEX-X2 (10 coin)** |
|---|---|---|
| Trade totali (5.5 anni) | 93 (~17/anno) | **157 (~29/anno)** |
| CAGR full | 116% | **165%** |
| MaxDD full | -37% | -42% |
| Calmar | 3.16 | **3.89** |
| Monte Carlo DD p95 | -60% | **-72%** |

Per anno (X2): 2021 **+1420%** · 2022 -5% · 2023 **+230%** · 2024 **+347%** ·
**2025 -12%** · 2026 ~0%.

**Walk-forward ancorato** (parametri mai ri-ottimizzati sui dati che li
giudicano): 2023 **+260%** (PF 8.6) · 2024 **+350%** (PF 8.2) ·
**2025-26 -8.4% (PF 0.92)** ← *il sistema sta perdendo nel regime attuale*.

### Lettura da professionista
X2 e' una **macchina da bull market**: piu' coin + canale veloce + leva =
esplosivo quando il mercato corre (2021/23/24), ma **negativo nei regimi
deboli** (2025-26) dove X base restava a +17%/-0%. Piu' trade ≠ piu' soldi
sempre: paghi l'attivita' extra nei mercati laterali. Il Monte Carlo (DD
mediano -52%, p95 -72%) dice che vanno previsti dimezzamenti del conto.
Scegli in base al regime e alla tua tolleranza: X2 per esposizione massima
al prossimo bull, X per compounding piu' regolare, APEX base spot per dormire.

## Struttura del repo

```
pinescript/
  apex_trend_strategy.pine      ← la strategia principale (TradingView, 1D)
  coinrule_replicas/            ← le 7 repliche dei bot Coinrule in Pine v5
backtest/
  engine.py                     ← motore event-driven (no lookahead, costi inclusi)
  strategies.py                 ← logica identica ai .pine
  portfolio.py                  ← simulatore portafoglio a capitale condiviso
  validate.py                   ← walk-forward, Monte Carlo, stress test, grafici
  tune.py                       ← sweep parametri single-symbol
  run.py                        ← backtest per-cripto, genera results.md
  results.md / validation_report.txt / trades_final.csv / charts/
data/                           ← OHLCV giornalieri 2021→2026 (fonte FMP)
```

Per riprodurre: `pip install pandas numpy matplotlib`, poi
`python3 backtest/run.py` (per-cripto) e `python3 backtest/validate.py`
(portafoglio + validazione completa).

### Nota metodologica (trasparenza)

I parametri core (canale 30, trailing 4×ATR, EMA20 di uscita) sono validati
walk-forward. Le scelte *strutturali* (filtro BTC, cap 30%, rischio 10%) sono
state selezionate guardando l'intero periodo: è una forma leggera di bias di
selezione, mitigata dal fatto che ogni variante vicina resta ampiamente
profittevole (vedi `backtest/experiments.csv`). Nessun backtest è una promessa.

## Limiti e avvertenze

- Backtest ≠ futuro: 5.5 anni includono bull 2021, bear 2022, ripresa 23-25,
  ma il mercato può cambiare regime.
- Su TradingView i risultati possono differire leggermente (dati exchange
  diversi, esecuzione ordini di Pine).
- La strategia è **long-only spot**, pensata per essere eseguibile anche su
  Coinrule/exchange senza leva. Niente leva: il sizing a rischio fa già il lavoro.
- Non è consulenza finanziaria: testala in paper trading prima di metterci capitale.
