# APEX-X2 - report finale

Universo: BTCUSD, ETHUSD, SOLUSD, BNBUSD, XRPUSD, ADAUSD, DOGEUSD, LINKUSD, AVAXUSD, DOTUSD | rotazione top-5 momentum, max 6 posizioni, canale 20gg, leva 2.0x

## Metriche full period (2021 → giu 2026)

 total_return_pct  cagr_pct  max_drawdown_pct  sharpe  sortino  calmar  n_trades  win_rate_pct  profit_factor  avg_trade_pct  max_consec_losses  avg_exposure_pct
         19756.12    164.74            -42.35    1.81     1.76    3.89       157          45.2           5.32           16.2                  8              39.1

## Rendimenti per anno

 anno  rendimento%
 2021       1420.3
 2022         -4.9
 2023        230.5
 2024        346.7
 2025        -11.9
 2026          0.0

## Walk-forward ancorato (parametri congelati)

finestra OOS  CAGR%  MaxDD%   PF  trades  win%
        2023 260.17  -18.99 8.58      24  54.2
        2024 350.07  -33.28 8.23      42  54.8
     2025-26  -8.43  -27.73 0.92      37  32.4

## Monte Carlo (2000 block-bootstrap)

 dd_mediano  dd_p95  dd_p99  cagr_mediano  prob_anno_negativo_pct
      -51.7   -71.6   -81.0         160.8                     0.3

## Tabella mensile (%)

       Gen    Feb   Mar    Apr   Mag  Giu   Lug    Ago   Set   Ott    Nov    Dic
anno                                                                            
2021  -2.9  102.1   2.6  219.3 -18.5  0.0   9.4  155.1 -25.3   8.1   11.4   -7.5
2022  -3.0   -0.3   1.6   -3.1   0.0  0.0   0.0    0.0   0.0   0.0    0.0    0.0
2023   0.0   -5.9   4.3    2.3   2.4 -2.1  -5.9    0.0  -1.0  33.2   25.2  101.0
2024 -13.8   50.4  16.8   -2.0  -0.5 -3.7   0.1   -4.8   9.2  -4.5  224.3  -14.3
2025 -11.1   -0.4  -5.6    1.2  -1.6  0.0  25.5    0.3  -4.8  -3.9   -1.2    0.0
2026   0.0    0.0   0.0    0.0   0.0  0.0   NaN    NaN   NaN   NaN    NaN    NaN

Trade totali: 157 (~29/anno) | lista completa in trades_x2.csv
