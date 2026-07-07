# Analisi impianto attuale – Flying Swinger "Volaré" FS-11-17 (Luna Park Sydney)

Fonti: schema elettrico **FS11_17_AUS_V106** (Automazioni 14 srl, progetto 2018_03_AU09,
nascita 22/06/2018, ultimo rilascio 14/10/2019, quadro 1191EE/FS11 – estratto 18 fogli su 75),
distinta base e schema oleodinamico **Phs3297** (Power Hydraulik srl, 2018), tabella
eccitazione valvole Phs 3251-3259-3297, **manuale d'uso e manutenzione FS11-17 UK**
(capitoli 0–10, ed. 2018/2020).

## 0. Dati giostra (dal manuale, cap. 2)

| Parametro | Valore |
|---|---|
| Posti passeggeri | 64 (2+1 per braccio, 16 bracci) |
| Rotazione tetto (antioraria, rispetto colonna) | 17 RPM |
| Rotazione colonna (oraria) | 6 RPM |
| Rotazione massima ammessa (risultante) | 11 RPM antioraria |
| Velocità di sollevamento | 0,170 m/s |
| Potenza totale azionamenti / nominale (senza luci) / luci | 90 kW / 82 kW / 8 kW |
| Riduttori rotazione colonna e tetto | Bonfiglioli 307 R3 HZ (olio Shell Omala S4 WE320, 4 l) |
| Ralla | Rothe Erde (ingrassaggio piste ogni 100 h) |
| Vento max in esercizio | **15 m/s (54 km/h)** – fuori servizio secondo AS 1170.2-2011 |
| Ore di esercizio considerate dal manuale | 1750 h/anno (stagione 7-8 mesi), 10 h/giorno |

## 1. Dati di targa elettrici

| Parametro | Valore |
|---|---|
| Alimentazione | 400V+N ±7%, 50 Hz, sistema TNS |
| Potenza richiesta / assorbita | 90 kW / 88 kW – 156 A |
| Interruttore generale | 4 poli, 160 A, curva C, Icc 25 kA, con bobina di sgancio |
| Differenziale generale | Toroide D105 (max 600 A) + relè RF001 0,3 A <40 ms |
| Tensione di comando | 24 V dc (alim. Omron S8VKC24024) |
| Sezione minima linea | 70 mm² |
| Norma di riferimento quadro | EN 60204-1, CE |

## 2. Architettura di controllo attuale

| Funzione | Componente installato | Note |
|---|---|---|
| PLC di sicurezza | **Pilz PSSuniversal multi** (A101, rack 1-2, slot 00–14, SafetyNET) | Piattaforma 2018 |
| HMI operatore | **Schneider Magelis HMIGTO3510** touch (A302) | Serie GTO in via di obsolescenza |
| Inverter rotazione palo | **Schneider ATV930D15N4** – 15 kW/27 A (UD111) + resistenza frenatura 5 kW 28 Ω (R111) | STO cablato, relè progr. R1/R2/R3 (Inverter OK, Max speed OK, Speed<20Hz) |
| Inverter rotazione tetto | **Schneider ATV930D30N4** – 30 kW/54 A (UD121) + resistenza frenatura 10 kW 16 Ω (R121) | Motore M121 30 kW alimentato via collettore rotante |
| Avviatore pompa idraulica | **Soft starter Emotron TSA** 37 kW/70 A (UD101) | Motore pompa M101 37 kW (WEG IE3) |
| Ausiliari centralina | Ventilatore scambiatore M102 0,5 kW; riscaldatore olio R103 0,6 kW | KM102/KM103 |
| Freni motore | KM131 (freno base), KM132 (freno tetto + cinture), KM133/KM134 4 kW 24 V dc (freno palo / apertura cinture) | Motori autofrenanti M111/M121 |
| Collettore rotante | UR200 (ST17 AE910620) + UR201 (blocco apertura cinture tetto) | Potenza 30 kW, luci, comandi cinture |
| Rete | Switch Ethernet IES-150B 5 porte + **Tosibox Lock 100** (teleassistenza Wi-Fi/LAN cliente) | ETH01–06 |
| UPS | Whad 1000 – 1 kW 230 V ac | Circuiti privilegiati/frenatura |
| Consolle operatore (UB110, 600×1100×400) | E-stop (PB102), start bicanale CH01/CH02 (PB103/104), chiave reset emergenza (KB105), chiave discesa emergenza (KB106), apertura cinture (PB107), stop ciclo (PB108), clacson (PB109), lampada lap-bars (LBS) | Comando remoto via cavo WC132 |
| Luci | Distribuzione FQ150 40A 4p diff. 0,3 A; linee tetto/palo/pozzo fisso (KL151/152), lap-bars FQ153, trasformatori luci tetto (UB301a) | |

### Quadri installati (6)

| Sigla | Descrizione | Dimensioni | IP |
|---|---|---|---|
| QG | Quadro generale | 1600×2100×600 | IP56 outdoor |
| UB110/UN110 | Consolle operatore | 600×1100×400 (targa: 400×500×200) | IP66 outdoor |
| UB101 | Distribuzione centralina idraulica | 370×470×180 | – |
| UB120 | Cassetta derivazione base | 550×750×220 | – |
| UB201 | Cassetta derivazione colonna | 550×750×220 | – |
| UB301 (+UB301a) | Quadro distribuzione tetto + trasformatori luci | – | – |

Servizi di quadro: 3 resistenze anticondensa 45 W con termostati +5/+35 °C,
condizionatore 600 W, luce interna LED.

## 3. Impianto oleodinamico (sollevamento/inclinazione)

Centralina Power Hydraulik **Phs3297** "Fly Swinger 64 posti CS5M", esecuzione **INOX**
(rif. Australia), senza resistenza:

- Motore pompa 37 kW WEG + pompa a palette Vickers 45V42 (196 l/min, 115 bar taratura)
- Valvola proporzionale **Hydac P4WEHRE E16** (alim. 24 V, segnale ±10 V) per rampe salita/discesa
- 7 elettrovalvole on/off 24 V dc: Y01 abilitazione salita, Y02 abilitazione discesa, Y03 discesa,
  Y04 rallentamento salita/discesa, Y05 discesa manuale d'emergenza, Y06/Y07 discesa cilindro DX/SX
- 3 pressostati IPN-160/E (PR1–PR3, 105 bar), 2 trasduttori di pressione 0–400 bar 4–20 mA (TP1/TP2),
  1 trasduttore di temperatura IFM TT3250/TR2439, livello elettrico + visivo, termostato 0–90 °C
- Filtro in pressione Hydac DF ON 500 e filtro di ritorno RFM 500 con indicatori di intasamento,
  filtro aria BDE1000, scambiatore di calore Emmegi con ventilatore
- 2 cilindri di sollevamento (Phc2226) con valvole di blocco d'emergenza HAWE LB4-C-63 e
  scarico manuale per discesa d'emergenza; alimentazione tramite collettore rotante

La logica di eccitazione (tabella Power Hydraulik) è: pressurizzazione → salita con rampa
proporzionale → rallentamento → discesa (Y02+Y03+Y04+Y06+Y07) → discesa d'emergenza (Y05, motore
fermo, per gravità).

## 4. Considerazioni per l'offerta del nuovo control system

1. **Età impianto**: progetto 2018, in servizio dal 2019 → ~7-8 stagioni in ambiente marino
   (porto di Sydney). Ventole e condensatori inverter, batterie UPS, spazzole/anelli del
   collettore e guarnizioni cassette sono a metà/fine vita utile.
2. **Obsolescenza**: HMI Magelis GTO in phase-out Schneider; Tosibox Lock 100 superato dalle
   generazioni successive; PSSu multi piattaforma matura (ricambi da verificare). Argomento
   commerciale forte per il rinnovo.
3. **Scopo tecnico del nuovo sistema** (da rispecchiare in offerta):
   - 2 inverter (15 kW palo + 30 kW tetto) con resistenze di frenatura e STO
   - soft starter 37 kW pompa + ausiliari centralina (ventilatore, riscaldatore olio)
   - PLC di sicurezza con: E-stop, start bicanale, monitoraggio velocità (soglie "max speed"
     e "<20 Hz"), gestione freni, cinture/lap-bars con blocco apertura, discesa d'emergenza
   - uscita analogica ±10 V per la proporzionale + 7 uscite valvole, ingressi 3 pressostati,
     2 trasduttori 4–20 mA, temperatura e livello olio
   - distribuzione luci con differenziali dedicati, UPS, alimentatore 24 V dc, router VPN
   - consolle operatore con le stesse funzioni della attuale (abitudine operatori = meno training)
4. **Riusabile** (previa verifica in sito): motori, freni, centralina idraulica e sensoristica di
   campo, collettore rotante (con revisione), cassette di derivazione e cablaggi dorsali.
   Da sostituire: QG, consolle, quadro centralina, PLC, HMI, drive, soft starter, UPS,
   alimentatori, router, protezioni.
5. **Punti aperti**: revisione/ricambio collettore ST17 (offrirla come opzione), taglia reale
   condizionatore quadro, stato cavi al collettore, eventuale richiesta del parco di nuove
   funzioni (telemetria, contatori cicli, registrazione eventi per SafeWork NSW).
