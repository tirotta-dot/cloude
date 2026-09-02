# Analisi bot Coinrule + Strategia APEX Trend per TradingView

Analisi dei bot del report settimanale Coinrule ("Top Strategies Weekly"),
replica in Pine Script v5, backtest indipendente e costruzione di una famiglia
di strategie trend-following (APEX) con validazione walk-forward, Monte Carlo
e — da settembre 2026 — un **audit indipendente del motore** che ha corretto
diversi bug e ricalcolato tutti i numeri al ribasso, onestamente.

## 🔎 Audit del motore (set 2026): leggere prima di tutto

Un audit multi-agente con verifica avversariale (3 "refuter" indipendenti per
ogni bug) ha confermato **30 finding** e i fix sono tutti applicati. I più
pesanti:

- **Lookahead nel ranking momentum** (critico): la rotazione top-N usava il
  close di *oggi* per decidere ingressi eseguiti all'open di *oggi*. Era il
  turbo irrealistico di X/X2/V/V2.
- **Segnali pendenti mai ripuliti**: ingressi eseguiti su segnali vecchi anche
  di settimane, con filtri non più validi.
- **Take profit mai valutato sulla barra di ingresso** (toccava le repliche
  Coinrule con TP).
- **Profit factor calcolato sui rendimenti % non pesati per la size**: con il
  sizing a rischio i PF pubblicati erano gonfiati (es. SOL 16.9 → 9.7).
- **Funding della leva sottostimato** (~1/4 del reale): ora addebitato
  sull'intero notional, come su un conto futures.
- **EMA200 di regime valida troppo presto** per coin con storico corto (DOT).
- **Pine**: la leva moltiplicava la size (esposizione doppia vs backtest),
  slippage ~0 invece di 0.05%, e la variante MTF ripaintava (request.security
  senza offset). Tutti corretti; preset rigenerati.

Il motore è ora coperto da 9 test automatici (anti-lookahead inclusi, validati
contro motori "mutanti"). **Prima → dopo** (full 2021→ago 2026):

| | APEX base | APEX-X | APEX-X2 | APEX-V | APEX-V2 |
|---|---|---|---|---|---|
| CAGR dichiarato prima | 85% | 116% | 165% | 112% | 128% |
| **CAGR reale (motore corretto)** | **31.4%** | **50.3%** | **53.1%** | **37.8%** | **46.7%** |
| MaxDD reale | -27.3% | -40.9% | -47.0% | -39.8% | -38.3% |

La morale non cambia (il trend following sulle cripto paga, i filtri di regime
proteggono nei bear), ma le grandezze sì. Nessun backtest è una promessa; uno
col lookahead è una bugia.

## ⚠️ Come leggere i numeri di Coinrule

I numeri dell'email (es. "BB+RSI Short +15.53% in 30 giorni") **non sono una
prova di profittabilità**:

1. **Finestra cortissima**: 7/30 giorni non dicono nulla; contano anni e
   regimi diversi (bull, bear, laterale).
2. **Selection bias**: Coinrule pubblica ogni settimana le *migliori* della
   settimana. Le peggiori non le vedi.
3. **Niente drawdown**: mostrano il profitto, mai il rischio corso.

### Verdetto sul backtest indipendente (2021 → ago 2026, daily, BTC/ETH/SOL/BNB/XRP)

| Bot Coinrule | CAGR medio | MaxDD medio | Verdetto |
|---|---|---|---|
| BB + RSI Short Selling | **-18.3%** | -69.7% | ❌ Il peggiore: shortare gli eccessi rialzisti in asset che fanno multipli è suicida. |
| Flash Crash | -11.9% | -57.6% | ❌ Idea sensata, TP/SL fissi la rovinano. |
| Range Trading (Solana) | -6.3% | -64.5% | ❌ Funziona solo nei laterali, compra i crolli nei trend. |
| Buy + SL/TP | -3.6% | -45.3% | ❌ Troppo semplice, le commissioni erodono tutto. |
| Scalping On Trend | -1.6% | -9.6% | ⚠️ Quasi pari: TP 2%/SL 1.5% sul daily genera trade mangiati dai costi. |
| Rebalance Trend Following | +9.3% | -58.3% | ⚠️ Profittevole ma DD inaccettabile. |
| MA Crossing (9/21) | **+24.3%** | -50.6% | ⚠️ L'unico concetto che regge: il trend following paga. Ma il DD resta enorme. |

**Conclusione**: solo i bot *trend following* hanno un edge reale; i *mean
reversion* perdono nel lungo periodo. Da qui nasce APEX.

## 🏆 APEX Trend Strategy v2 (la strategia costruita)

File: [`pinescript/apex_trend_strategy.pine`](pinescript/apex_trend_strategy.pine) — copia/incolla nel Pine Editor di TradingView, timeframe **1D**. Alert JSON per webhook, tabella statistiche, parametri configurabili. Costi allineati al backtest (0.15%/lato).

Regole:
- **Regime locale**: `close > EMA200` **e** `EMA50 > EMA200`
- **Regime di mercato**: le altcoin entrano solo se **anche BTC** è sopra la
  sua EMA200
- **Entrata**: chiusura sopra il massimo di chiusura degli ultimi 30 giorni
- **Uscite**: chiusura sotto EMA20 • trailing 4×ATR(14) • stop di emergenza -12%
- **Money management**: posizione dimensionata perché lo stop costi ~10%
  dell'equity, con cap del 30% per coin
- **v2**: profit-lock (oltre +50% il trailing si stringe a 3×ATR) e cooldown
  15 giorni dopo un'uscita in perdita

### Risultati per singola cripto (2021 → ago 2026, costi 0.15%/lato)

Config "APEX base" single-coin: solo regime EMA200 + canale 30 + uscite +
sizing a rischio (il filtro BTC e l'allineamento EMA50/200 sono meccaniche di
portafoglio, vedi sotto).

| Cripto | Rendimento tot. | CAGR | MaxDD | Sharpe | Trade | Win rate | Profit factor |
|---|---|---|---|---|---|---|---|
| BTC | +72.9% | 10.2% | -24.1% | 0.61 | 29 | 51.7% | 2.03 |
| ETH | +50.8% | 7.5% | -19.9% | 0.48 | 26 | 46.2% | 1.72 |
| SOL | +1021.3% | 53.3% | -24.5% | 1.56 | 23 | 73.9% | 9.72 |
| BNB | +256.3% | 25.2% | -44.4% | 0.79 | 32 | 37.5% | 1.91 |
| XRP | +162.4% | 18.6% | -46.8% | 0.72 | 30 | 30.0% | 2.38 |

### Portafoglio reale a capitale condiviso (config FINALE: filtro BTC + allineamento + cap 30%)

Simulato in [`backtest/portfolio.py`](backtest/portfolio.py), validazione in
[`backtest/validate.py`](backtest/validate.py):

| Periodo | CAGR | MaxDD | Sharpe | Sortino | Calmar | Profit factor |
|---|---|---|---|---|---|---|
| **Full 2021→ago 2026** | **31.4%** | **-27.3%** | 1.15 | 1.82 | 1.15 | 2.88 |
| **Out-of-sample 2024→2026** (parametri congelati) | **13.9%** | **-23.8%** | 0.64 | 0.91 | 0.58 | 2.34 |

Rendimenti per anno: 2021 **+94.6%** · 2022 **0%** (bear: fuori dal mercato) ·
2023 **+62.0%** · 2024 **+39.7%** · 2025 **+6.6%** · 2026 YTD ~0%.

### Validazione (la parte che i report di marketing non mostrano)

- **Walk-forward**: parametri core ottimizzati su 2021-23 → su 2024-26 la
  selezione ancorata pulita rende il **10.9%/anno (PF 2.03)**. Il 13.9% sopra
  è la config deployata, i cui parametri furono scelti (anche) guardando
  l'intero periodo: differenza dichiarata, non nascosta (lo sweep di
  `tune.py` è in-sample e ora lo dice esplicitamente).
- **Monte Carlo** (2000 block-bootstrap): DD mediano -32%, 95° percentile
  -51%. Pianifica come se un -40/50% potesse accadere.
- **Stress costi doppi** (0.30%/lato): CAGR 31.4% → 29.6%. Robusta.
- **Senza i 5 trade migliori** (ora contati in denaro, non in %): profit
  factor 1.39 → l'edge si assottiglia ma resta positivo; la dipendenza dai
  colpi grossi è più alta di quanto il vecchio calcolo facesse credere.
- Report: [`backtest/validation_report.txt`](backtest/validation_report.txt),
  trade: [`backtest/trades_final.csv`](backtest/trades_final.csv), grafici in
  `backtest/charts/`.

**Aspettativa realistica**: **~10-15% annuo con DD ~-25%** in condizioni
normali, upside forte nei bull veri (2021: +95%), capitale protetto nei bear
(2022: 0% contro -65% di BTC). Per lo spot senza pensieri è questa la config.

## 🚀 Le varianti aggressive: X, X2, V, V2 (futures/margin)

> Dopo l'audit i "100% annui" non esistono più nemmeno nei backtest. Le
> varianti restano interessanti, ma il quadro onesto è questo (full
> 2021→ago 2026 e walk-forward ancorato, motore corretto):

| | base | X (top-3, leva 2×) | X2 (10 coin, top-5) | V (vol-target) | **V2 (consigliata futures)** |
|---|---|---|---|---|---|
| CAGR full | 31.4% | 50.3% | 53.1% | 37.8% | **46.7%** |
| MaxDD full | -27.3% | -40.9% | -47.0% | -39.8% | **-38.3%** |
| Profit factor | 2.88 | 2.47 | 1.87 | 2.01 | **2.29** |
| WF 2023 | — | — | +123% | +100% | **+192%** |
| WF 2024 | — | — | +211% | +61% | +47% |
| WF 2025-26 | — | — | **-17.3%** | -9.7% | **-5.2%** |
| Monte Carlo DD p95 | -51% | — | **-73%** | — | — |

- **APEX-X** (5 coin, rotazione top-3 momentum, leva 2×, trailing 5×ATR):
  full 50.3%, OOS 2024-26 **39.8%** — la variante aggressiva più pulita.
  Dettagli in [`backtest/aggressive.py`](backtest/aggressive.py).
- **APEX-X2** (universo 10 coin, top-5, canale 20, vol-cap 85°, chandelier,
  protezione equity-curve): più trade e più CAGR full, ma **perde nel regime
  2025-26** (-17.3%) e il Monte Carlo dice DD mediano -51%, p95 -73%:
  macchina da bull market, non da compounding tranquillo.
- **APEX-V** (X2 + vol-targeting 60% sulla leva): dopo i fix **non è più vero
  che nessuna finestra walk-forward è negativa** (2025-26: -9.7%); resta vero
  che riduce il danno nei regimi deboli rispetto a X2.
- **APEX-V2** (V + cooldown 15g + profit-lock): ancora la variante col
  miglior equilibrio — più CAGR di V, meno DD di X2, la finestra 2025-26
  quasi in pari (-5.2%) e il miglior worst-case walk-forward (DD -32.0%).

### Le due prove regine (rifatte col motore corretto)

1. **Test freddo cross-sezionale**: V2 congelata sulle 5 coin MAI usate per
   il tuning (ADA, DOGE, LINK, AVAX, DOT; BTC solo come filtro di regime):
   **CAGR 18.9%, PF 2.33; OOS 2024-26 +20.3%/anno (PF 2.35)**. L'edge si
   trasferisce a coin mai viste: è un fenomeno di mercato, non curve-fitting.
2. **Checkpoint out-of-sample "vero"** (`backtest/checkpoint_oos.py`): il
   sistema congelato al 9 giu 2026 misurato sui dati arrivati DOPO ogni
   scelta di design (10 giu → 31 ago 2026): **0.0%** — zero trade, mentre BTC
   rimbalzava +27.8%. Non è un errore: BTC è rimasto sotto la sua EMA200 per
   tutta la finestra (bear iniziato nel 2025) e ha chiuso sopra solo il 31/8,
   con allineamento ancora negativo. Il filtro ha fatto il suo lavoro: niente
   rimbalzi da bear, si entra a regime confermato. È il costo noto del trend
   following — e il checkpoint è ripetibile a ogni aggiornamento dati.

## ⚡ Preset pronti e varianti intraday

- [`pinescript/ready/`](pinescript/ready) — APEX-V2 single-coin 1D per la
  top-5 del ranking corretto: **SOL, DOGE, ADA, XRP, LINK** (BNB è uscito:
  col motore corretto il suo CAGR crolla al 2.7%). Header con i numeri veri
  della logica che il Pine implementa davvero (senza equity-curve filter).
- [`pinescript/ready_4h/`](pinescript/ready_4h) — stessi preset adattati al
  4H (APEX-F, canale/uscite più veloci). **Nota onesta**: le coin vengono dal
  ranking daily V2; non esiste un backtest intraday in questo repo (i dati
  sono daily), quindi i numeri citati sono daily.
- [`pinescript/apex_mtf_30m_1h.pine`](pinescript/apex_mtf_30m_1h.pine) e
  [`pinescript/ready_30m/`](pinescript/ready_30m) — variante multi-timeframe
  (ingressi 30m con conferma di regime 1h), ora **davvero anti-repaint**
  (request.security con offset [1]). Stessa nota: nessun backtest intraday,
  provala in paper trading.

## Struttura del repo

```
pinescript/
  apex_trend_strategy.pine      ← la strategia principale (TradingView, 1D)
  apex_momentum_screener.pine   ← screener momentum per la rotazione
  apex_mtf_30m_1h.pine          ← variante multi-timeframe 30m/1h
  ready/ ready_4h/ ready_30m/   ← preset per coin (generati dagli script)
  coinrule_replicas/            ← le 7 repliche dei bot Coinrule
backtest/
  engine.py                     ← motore event-driven (audit set 2026, 9 test)
  strategies.py                 ← logica delle strategie single-coin
  portfolio.py                  ← portafoglio a capitale condiviso
  aggressive.py                 ← varianti X (rotazione momentum, leva)
  report.py                     ← APEX-X2/V/V2 + report completo
  improvements.py               ← banco di prova feature
  validate.py                   ← walk-forward, Monte Carlo, stress test
  checkpoint_oos.py             ← checkpoint out-of-sample ripetibile
  single_coin.py / fast.py      ← ranking single-coin e preset 4H
  tune.py                       ← sweep parametri (IN-SAMPLE, dichiarato)
  run.py                        ← backtest per-cripto, genera results.md
  test_engine.py                ← 9 test automatici (anti-lookahead inclusi)
data/                           ← OHLCV giornalieri 2021 → 31 ago 2026 (FMP)
```

Per riprodurre: `pip install pandas numpy matplotlib`, poi
`python3 backtest/test_engine.py`, `python3 backtest/run.py`,
`python3 backtest/validate.py`, `python3 backtest/report.py`,
`python3 backtest/checkpoint_oos.py`.

### Nota metodologica (trasparenza)

- I parametri core (canale 30, trailing 4×ATR, EMA20) vengono dallo sweep di
  `tune.py`, che è **in-sample sull'intero periodo**: l'unica validazione
  fuori campione è il walk-forward ancorato di `validate.py` (10.9%/anno) e
  il checkpoint OOS. Le scelte strutturali (filtro BTC, cap 30%, rischio 10%)
  sono state selezionate guardando l'intero periodo: bias di selezione
  leggero, dichiarato.
- Il vol-targeting di V e le cure di V2 furono scelti osservando (anche) la
  debolezza 2025-26: il loro out-of-sample vero è iniziato il 10 giu 2026 ed
  è misurato dal checkpoint a ogni aggiornamento dati.
- La derivazione storica di X2 in `improvements.py` testa le feature
  singolarmente (il vol-cap al 90° vs l'85° adottato): la combinazione finale
  non è riproducibile da quel file — verità storica, lasciata agli atti.

## Limiti e avvertenze

- Backtest ≠ futuro: 5.7 anni includono bull 2021, bear 2022, ripresa 23-24,
  bear 2025-26, ma il mercato può cambiare regime.
- Su TradingView i risultati possono differire (dati exchange diversi,
  broker emulator di Pine).
- **APEX base è long-only spot senza leva** (il sizing a rischio fa il
  lavoro); X/X2/V/V2 richiedono futures/margin con leva ≤2× e funding reale.
- I numeri fanno metà della fatica: la strategia migliore resta quella che
  riesci a seguire nei momenti peggiori. Testa in paper trading prima di
  metterci capitale. Non è consulenza finanziaria.
