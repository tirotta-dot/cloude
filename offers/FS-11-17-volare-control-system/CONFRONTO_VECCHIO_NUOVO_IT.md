# Confronto impianto attuale ↔ nuovo control system – FS-11-17 "Volaré"

**Stato**: baseline dell'impianto attuale completa (colonna "Attuale (2018)").
Le colonne "Nuovo" e "Migliorie" verranno compilate all'arrivo della documentazione del
nuovo control system. Questo documento diventerà l'allegato tecnico-commerciale dell'offerta
che evidenzia il valore del retrofit.

## 1. Centrale idraulica (sollevamento/inclinazione tetto)

| Aspetto | Attuale (2018) | Nuovo | Migliorie / benefici |
|---|---|---|---|
| Motore pompa | Asincrono WEG 37 kW 4 poli IE3, avviato da soft starter Emotron TSA, **in rotazione continua** anche nelle pause (ricircolo per filtrazione/raffreddamento, §6.14.1.9 manuale) | *(es. motore brushless / servopompa – da doc.)* | *(es. consumo ridotto: potenza erogata solo quando serve; niente surriscaldamento olio; minor rumore; avvio/arresto illimitati)* |
| Pompa | A palette Vickers 45V42, 196 l/min, taratura 115 bar | | |
| Controllo movimento | Valvola proporzionale Hydac P4WEHRE ±10 V + 7 EV on/off, rampe gestite dal PLC | | |
| Raffreddamento olio | Scambiatore Emmegi con ventilatore 0,5 kW + ricircolo continuo | | *(se il motore gira solo a richiesta: olio più freddo → vita olio/guarnizioni più lunga, possibile eliminazione/riduzione scambiatore)* |
| Riscaldatore olio | 0,6 kW comandato da termostato | | |
| Monitoraggio | 3 pressostati 105 bar, 2 trasduttori 0–400 bar 4–20 mA, sonda temperatura IFM, livello elettrico+visivo, indicatori intasamento filtri | | |
| Manutenzione associata | Filtri ogni 3 mesi/500 h; olio ogni anno; test valvole di blocco mensile; flessibili ogni 6 anni | | *(quantificare riduzioni: meno ore motore = meno stress olio/filtri?)* |

## 2. Azionamenti rotazione

| Aspetto | Attuale (2018) | Nuovo | Migliorie / benefici |
|---|---|---|---|
| Rotazione palo/colonna | ATV930D15N4 15 kW + resistenza frenatura 5 kW 28 Ω, motore autofrenante, riduttore Bonfiglioli 307 R3 HZ, 6 RPM | | *(es. recupero energia in rete anziché dissipazione su resistenza?)* |
| Rotazione tetto | ATV930D30N4 30 kW + resistenza 10 kW 16 Ω, alimentazione via collettore rotante, 17 RPM | | |
| Sicurezza drive | STO cablato bicanale, relè soglie velocità (max speed, <20 Hz) | | |

## 3. Sistema di controllo e sicurezza

| Aspetto | Attuale (2018) | Nuovo | Migliorie / benefici |
|---|---|---|---|
| PLC di sicurezza | Pilz PSSuniversal multi (SafetyNET), PL d Cat. 3 | | |
| HMI | Schneider Magelis HMIGTO3510 (serie in phase-out) | | *(ricambi garantiti, diagnostica migliore, contatori manutenzione)* |
| Consolle | E-stop, start bicanale, chiavi reset/discesa emergenza, apertura cinture, stop ciclo, clacson | | |
| Ritenute | Monitoraggio cinture/lap-bars con blocco apertura via collettore (UR201) | | |
| Discesa d'emergenza | 3 modalità (Y05 elettrica, rubinetto manuale, procedura totale assenza energia) | | |
| Monitoraggio vento | **Assente** (manuale: scala Beaufort; limite esercizio 15 m/s) | | *(anemometro con soglie automatiche)* |

## 4. Distribuzione, ausiliari e servizi

| Aspetto | Attuale (2018) | Nuovo | Migliorie / benefici |
|---|---|---|---|
| Quadro generale | QG 1600×2100×600 IP56 outdoor, condizionatore 600 W, anticondensa 3×45 W | | |
| Protezioni | Generale 160 A + toroide 300 mA <40 ms; RCD dedicati luci (300 mA) e servizi (30 mA) | | |
| UPS / 24 V | Whad 1000 1 kW (batteria da sostituire ogni anno da manuale) + Omron S8VK 24 V dc | | |
| Teleassistenza | Tosibox Lock 100 + switch 5 porte | | *(VPN aggiornata, diagnostica remota P&B)* |
| Luci | Distribuzione 40 A con differenziale, trasformatori tetto, linea lap-bars | | |
| Collettore rotante | ST17 AE910620 (potenza tetto, luci, comandi cinture) – spazzole: 20 N, sostituzione a 2 mm | | |

## 5. Sintesi migliorie (da compilare a fine confronto)

1. *(efficienza energetica: kWh/ciclo stimati prima/dopo)*
2. *(riduzione manutenzione: interventi/anno eliminati o diradati)*
3. *(sicurezza: nuove funzioni o PL superiori)*
4. *(disponibilità ricambi / fine obsolescenza)*
5. *(diagnostica, teleassistenza, supporto log book AS 3533.2)*
