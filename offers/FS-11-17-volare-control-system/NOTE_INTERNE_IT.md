# Note interne – Offerta nuovo control system Flying Swinger "Volaré" (FS-11-17)

**Cliente:** Luna Park Sydney – Milsons Point NSW, Australia
**Giostra:** Flying Swinger 64 posti "Volaré" – commessa FS-11-17 – in servizio dal 2019

Questa nota accompagna la bozza di offerta in inglese (`OFFER_FS-11-17_Control_System_EN.md` /
`.docx`). **Non inviare al cliente** – è solo la checklist interna.

Documentazione analizzata: schema elettrico FS11_17_AUS_V106 (Automazioni 14), distinta +
schema oleodinamico Phs3297 (Power Hydraulik), tabella eccitazione valvole, manuale U&M
FS11-17 UK capitoli 0–10 → vedi `ANALISI_IMPIANTO_ATTUALE_IT.md` e
`PIANO_MANUTENZIONE_FS11-17_IT.md`.

## 1. Dati da inserire prima dell'invio

- [ ] Numero offerta e data
- [ ] Nominativo del referente tecnico/acquisti di Luna Park Sydney
- [ ] **Tutti i prezzi** (posizioni 1–7 + opzioni A–F) – lasciati volutamente in bianco
- [ ] Incoterms (CIP Sydney? DAP Luna Park? EXW?) e modalità di spedizione (mare/aereo)
- [ ] Giorni di trasferta e numero di tecnici per il commissioning (viaggio e alloggio inclusi o esclusi?)
- [ ] Tempi di consegna reali (ipotizzate 16–20 settimane, da verificare con acquisti/produzione)
- [ ] Condizioni di pagamento (ipotizzato 30/60/10 – standard, da confermare)
- [ ] Taglia HMI (ipotizzato 12")
- [ ] Firma: nome e ruolo di chi emette l'offerta

## 2. Scelte tecniche fatte nella bozza (da validare)

- Piattaforma proposta: **Siemens S7-1500F** + drive con STO; nell'offerta è già scritto che a
  richiesta si può quotare l'alternativa "like-for-like" (Pilz PSS + Schneider come l'originale
  Automazioni 14: PSSu multi + 2× ATV930 + HMIGTO3510 + soft starter Emotron TSA).
  **Decidere la linea aziendale prima dell'invio.**
- Taglie azionamenti replicate dall'esistente: 15 kW palo (resistenza ≥5 kW), 30 kW tetto
  (resistenza ≥10 kW), soft starter 37 kW pompa, avviamenti ventilatore 0,5 kW + riscaldatore
  olio 0,6 kW.
- Interfaccia centralina Phs3297: proporzionale ±10 V, 7 EV on/off, 3 pressostati, 2 trasduttori
  4–20 mA, temperatura/livello, sequenza discesa d'emergenza (3 modalità come da manuale §6.14.1.8).
- Riuso di motori, freni, centralina, sensori di campo, cassette e dorsali previa verifica in sito;
  collettore rotante: revisione in **opzione B**.
- HMI: aggiunti promemoria manutenzione a ore/cicli e registro eventi esportabile per il log book
  AS 3533.2 (leva commerciale emersa dal manuale).
- Opzione C anemometro: giustificata dal manuale (limite 15 m/s, oggi valutato con scala Beaufort
  se non c'è strumento). Verificare se a Sydney l'hanno già installato.
- Opzione E: contratto di ispezione annuale/proof test sicurezze a supporto AS 3533.2.

## 3. Punti tecnici ancora da verificare

- [ ] Fogli mancanti dello schema elettrico (abbiamo 18 su 75): I/O completo del PSSu, uscita
      analogica proporzionale, circuiti cancelli (relè amperometrico 150 N), luci di dettaglio
- [ ] Stato reale di: collettore (spazzole a 20 N?), tubi flessibili (prescrizione 6 anni →
      probabilmente scaduta), batterie UPS (sostituzione annuale prescritta), ventole ATV930
- [ ] Il quadro attuale è IP56 1600×2100×600: verificare vincoli di spazio/accesso per il nuovo
- [ ] Tensione motore tetto indicata 3×415 V nel manuale (rete australiana): confermare taratura drive
- [ ] Cancelli motorizzati: inclusi nel perimetro del nuovo control system? (relè amperometrico
      anti-schiacciamento 150 N da replicare)
- [ ] Richieste extra del parco: telemetria, contapersone, integrazione col sistema di parco?

## 4. File nella cartella

| File | Contenuto |
|---|---|
| `OFFER_FS-11-17_Control_System_EN.md` / `.docx` | Offerta per il cliente (EN), prezzi da compilare |
| `ANALISI_IMPIANTO_ATTUALE_IT.md` | Analisi tecnica dell'impianto installato |
| `PIANO_MANUTENZIONE_FS11-17_IT.md` | Manutenzioni prescritte dal manuale + integrazioni |
| `NOTE_INTERNE_IT.md` | Questa checklist |
| `make_docx.py` | Rigenera il .docx dal .md (`python3 make_docx.py`) |
