# APEX-X2 - report finale

Universo: BTCUSD, ETHUSD, SOLUSD, BNBUSD, XRPUSD, ADAUSD, DOGEUSD, LINKUSD, AVAXUSD, DOTUSD | rotazione top-5 momentum, max 6 posizioni, canale 20gg, leva 2.0x

## Metriche full period (2021 → giu 2026)

 total_return_pct  cagr_pct  max_drawdown_pct  sharpe  sortino  calmar  n_trades  win_rate_pct  profit_factor  avg_trade_usd  max_consec_losses  avg_exposure_pct
          1014.41     53.08            -47.04    1.14     1.81    1.13       118          41.5           1.87         983.71                  6              30.7

## Rendimenti per anno

 anno  rendimento%
 2021        126.7
 2022         -1.7
 2023        109.1
 2024        228.1
 2025        -27.1
 2026          0.0

## Walk-forward ancorato (parametri congelati)

finestra OOS  CAGR%  MaxDD%   PF  trades  win%
        2023 123.29  -17.61 4.63      23  43.5
        2024 210.53  -37.50 5.57      37  56.8
     2025-26 -17.33  -31.62 0.60      33  27.3

## Monte Carlo (2000 block-bootstrap)

 dd_mediano  dd_p95  dd_p99  cagr_mediano  prob_periodo_negativo_pct
      -50.6   -72.7   -81.1          50.5                        3.6

## Tabella mensile (%)

       Gen   Feb   Mar  Apr  Mag  Giu   Lug    Ago   Set   Ott    Nov   Dic
anno                                                                       
2021   0.0   0.0   0.0  0.0  0.0  0.0   5.6  143.1 -18.8  -2.9   21.1  -7.6
2022   0.0   0.0   1.6 -3.3  0.0  0.0   0.0    0.0   0.0   0.0    0.0   0.0
2023   0.0  -4.6   3.9  1.5  2.3 -4.0  -6.2    0.0  -1.0  18.3    7.3  79.6
2024  -5.8  29.4  22.2 -0.9 -1.1 -1.2  -2.0   -5.7   3.2  -7.9  174.3  -5.5
2025 -17.2  -5.0  -5.7  1.4 -0.8  0.0  18.4   -8.5  -6.8  -3.4    0.0   0.0
2026   0.0   0.0   0.0  0.0  0.0  0.0   0.0    0.0   NaN   NaN    NaN   NaN

Trade totali: 118 (~22/anno) | lista completa in trades_x2.csv
