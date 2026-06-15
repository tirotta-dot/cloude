# Stato dell'arte: Intelligenza Artificiale nelle giostre / attrazioni e nei photo system di parco
### Ricerca di prior art per deposito brevettuale — panorama completo (landscape commerciale + documenti brevettuali)
*Data: 15 giugno 2026 — Metodologia: deep research multi-fonte, 5 angoli di indagine in parallelo + verifica mirata su Google Patents/USPTO. I numeri, i richiedenti e le date dei brevetti sono stati confrontati con le pagine reali; i campi non confermabili sono marcati **[DA VERIFICARE]**.*

---

## 0. Sintesi esecutiva (per l'avvocato)

**Dove c'è AI "vera" e dispiegata.** L'AI genuina (machine learning / computer vision / reinforcement learning) nel settore si concentra in **quattro cluster**, non nel controllo della giostra:

1. **Photo system con riconoscimento facciale** — il cluster più maturo e rilevante per un brevetto sul tema "foto". **Pomvom/Picsolve** è il caso commerciale di riferimento (selfie → template facciale numerico monodirezionale → matching automatico dell'ospite su camere di giostra, fotografi mobili, green-screen e video wall), realizzato su **AWS Rekognition** e dispiegato nei parchi **Merlin** (Alton Towers, Madame Tussauds, London Eye, Legoland), **San Diego Zoo/Safari**, **Dubai Parks**.
2. **Manutenzione predittiva / anomaly detection** — **DMT RideGuard** (TÜV NORD): ML su dati di vibrazione/shock con sensor fusion, dispiegato 2023-2026 (Movie Park Germany, Karls); **OneWatt EARS** (acustico, pilota Efteling 2018).
3. **Personaggi robotici e trasformazione dell'ospite** — **Disney BDX/Olaf** (reinforcement learning per la locomozione bipede + sim-to-real, NVIDIA Newton/Isaac + DeepMind; Olaf con layer conversazionale moderato) e **Holovis HoloTrac/"Deep Smarts"** (CV deep-learning che trasforma l'ospite in Minifigure a LEGOLAND New York).
4. **Operazioni di parco** — crowd analytics in computer vision (**Safari AI**, **V-Count**), previsione code e dynamic pricing ML (**accesso**, **Connect&GO/Moov AI**), assistenti generativi (**Six Flags + Google Vertex AI**), itinerari (**Disney Genie+**).

**Dove l'"AI" è marketing.** Il **controllo in tempo reale** delle giostre (coaster) è **mecca­tronica deterministica / PLC di sicurezza**, NON machine learning, anche quando etichettato "smart/intelligent": Maurer "SmartCoaster", Intamin (blocking dinamico), KUKA/Robocoaster, Gerstlauer, S&S, Premier. Anche i sistemi "interattivi" di puntamento (Triotech *Maestro*, Alterface) sono **tracking sensoriale (Leap Motion/IR), non ML**. Vanno scartati come "AI prior art" pur essendo automazione sofisticata.

**Risposta diretta alla domanda sui photo system.** **Sì, esistono e sono commercialmente dispiegati** sistemi fotografici che usano l'AI: (a) **riconoscimento facciale** per abbinare l'ospite alle proprie foto/video (Pomvom/Picsolve, Semnox, integrazione Captomatic); (b) **selezione "best-frame" via ML** (consolidata nella prior art di imaging generale — Microsoft US 9,807,301 — e nei brevetti di smile/eyes-open detection); (c) compositing/effetti. **Correzione importante:** il **Disney PhotoPass** per le foto on-ride si basa su **RFID (MagicBand), non su riconoscimento facciale** (il face-rec Disney è usato sulle navi da crociera e in test d'ingresso); **Universal "Photo Validation"** è **controllo d'accesso**, non foto-souvenir.

**Densità di prior art (allarme per la brevettabilità).** Il matching foto-ospite per volto è anticipato fino al **brevetto fondazionale CenterFrame/Goldberg US 6,526,158 (priorità 1996)**. Un OEM di giostre — **Maurer** — ha già brevettato il **riconoscimento dell'espressione facciale a bordo (US 9,038,543, 2015)**. **Disney** ha un portafoglio fitto su controllo adattivo della giostra in base allo stato del passeggero (US 9,610,510 / US 9,943,769), verifica ML dei restraint (US 2026/0109316), virtual queue e biometria. Questi sono i principali **riferimenti potenzialmente bloccanti** a seconda dell'oggetto della tua rivendicazione (vedi §5 FTO e white space).

---

## 1. Metodologia e attendibilità

- **Fonti commerciali:** siti dei costruttori, stampa di settore (Blooloop, InPark Magazine, Amusement Today, Park World, IAAPA), comunicati, paper accademici (arXiv, ACM/SIGGRAPH).
- **Brevetti:** ricerche domain-scoped su `patents.google.com` + endpoint PDF USPTO `image-ppubs.uspto.gov`, con cross-check su notizie. **Caveat tecnico:** nell'ambiente di ricerca il fetch diretto delle pagine brevettuali era bloccato (HTTP 403); i dati provengono da estrazioni di ricerca verificate e incrociate. **Prima di un uso ufficiale come prior art, ogni numero/richiedente/data va riconfermato su Espacenet/USPTO/DEPATISnet.**
- **Filtro scettico:** ogni voce è classificata **AI reale vs marketing** e per **maturità** (concetto / prototipo-ricerca / solo brevetto / prodotto dispiegato).

---

## 2. PARTE A — Landscape commerciale (azienda → prodotto → tipo di AI → descrizione → maturità → fonte/anno)

### A1 — Controllo giostra, sicurezza, manutenzione predittiva

| Azienda | Prodotto / giostra | Tipo di AI | Come è usata | Maturità | Reale/Marketing | Fonte (anno) |
|---|---|---|---|---|---|---|
| **DMT GmbH (TÜV NORD)** | **DMT RideGuard** (+ cloud SAFEGUARD) | ML anomaly detection + sensor fusion | Sensore MEMS triassiale "VIB3D" invia vibrazione/shock al cloud; algoritmi ML apprendono i pattern di guasto e il tempo medio tra fermi, generano alert predittivi; integra il CMMS Mobaro | **Dispiegato** (Movie Park Germany 2023→2024; Karls). German Excellence Award 2026 "Digital Solutions & AI" | **Reale (alta)** | dmt-group.com/rideguard.html; iot-now.com (2024); amusementtoday.com (2026) |
| **OneWatt** | **EARS** (Embedded Acoustic Recognition Sensor) | ML acustico (edge) | Sensori "ascoltano" i motori; modelli ML predicono guasti a cuscinetti/motore prima del fermo. Obiettivo Efteling: uptime 95-100% | **Pilota giostre** (Efteling 2018); prodotto commerciale in eolico/industriale | **Reale (alta) / deployment giostre incerto** | thenextweb.com (2018) |
| **Noiseless Acoustics** | NL Camera/Sense | Imaging acustico + analytics | Localizzazione sorgenti di rumore/guasto a Efteling con OneWatt | Pilota | Reale parziale (signal processing) | thenextweb.com (2018) |
| **Maurer SE** | **"SmartCoaster" / Spike** | *Nessuna AI* | "Smart" = safety-PLC decentralizzato per veicolo, regolazione posizione/velocità centimetrica. È controllo deterministico ridondante | Dispiegato | **Marketing ("smart")** | maurer-rides.de/smartcoaster |
| **Intamin** | Blocking dinamico (brevetti) | *Nessuna AI* | Zone di blocco per veicolo dimensionate in tempo reale su velocità/carico (distanza di arresto calcolata) | Dispiegato/brevetto | **Algoritmico, non ML** | US 10,514,933; US 9,908,056 |
| **KUKA** | **Robocoaster / KUKA Coaster** | *Nessuna AI nel prodotto* | Controllo robotico real-time PC-based con monitoraggio accelerazioni/coppia, profili di moto memorizzati (livelli 1-5); VxWorks | Dispiegato (Harry Potter Forbidden Journey, 2010) | **Robotica deterministica** (ML solo in ricerca KUKA) | kuka.com; windriver.com |
| **Gerstlauer** | Infinity Coaster control | *Nessuna AI* | Antirollback magnetico, lanci LSM, sicurezza ridondante | Dispiegato | Ingegneria convenzionale | gerstlauer-rides.de |
| **Premier Rides / S&S–Sansei** | Lanci LIM/LSM, sistemi ad aria | *Nessuna AI* | Propulsione e controllo magnetico/pneumatico | Dispiegato | Nessun ML | wikipedia S&S |
| **Bolliger & Mabillard** | — | — | Nessuna offerta AI/condition-monitoring pubblica | — | Assenza di evidenza | wikipedia B&M |
| **Vekoma** | "New ride control systems"; treni Karls 2026 con sensori | *Nessuna AI confermata* | Upgrade di controllo e "sensori di nuova generazione" sui treni; la dicitura "predittivo" viene da terzi, non da Vekoma | Sensori plausibili 2026 | **Non confermato ML** | vekoma.com; blooloop.com |
| **Amusement Technical** | **RideMinder** (IIoT) | *Nessuna AI* | Sensori retrofit con alert **a soglia/regole** (non modelli addestrati) | Dispiegato | **IoT a regole, non ML** | amusementtechnical.com |
| **Zamperla** | "smart technology" (Windstarz + Rockwell) | *Dubbio* | Monitoraggio remoto della giostra; claim "AI e robotica nei processi" vago e non documentato | Dispiegato (monitoraggio) | **Marketing** | coaster101.com (2018) |
| **D-Tex Visual** | **Bolt-iT** (edge-AI) | CV edge | Sensori edge-AI con algoritmi personalizzabili per monitoraggio sicurezza/manutenzione di infrastruttura attrazioni | Annunciato/early (IAAPA 2025) | Reale (media-alta) | blooloop.com (2025) |
| *(ricerca/accademico)* | Robot arrampicatore ispezione binari (Cina) | CV + NDT (EMAT, eddy-current) | Robot con camera + sonde per cricche/corrosione su binari verticali; deep-learning per i difetti | **Prototipo lab** (2023) | Reale (hardware); ML difetti da confermare | PMC10611218 (MDPI) |
| *(design-side)* | **CoasterAI** (indipendente) | NN + algoritmo genetico + motore fisico | Genera spline di tracciato, simula, valuta g-force/velocità ed evolve i layout | Concept hobbistico | Reale ML, non prodotto OEM | toolify.ai; sentisight.ai |

> **Punto chiave per il prior art:** nel **controllo real-time** dei coaster non c'è ML; il ML reale è in **manutenzione predittiva** (DMT, OneWatt) e nei **brevetti Disney di sicurezza** (CV bus-bar; verifica restraint — §4).

### A2 — Animatronics, robot, personaggi (AI reale: RL + CV)

| Azienda | Prodotto | Tipo di AI | Come è usata | Maturità | Fonte |
|---|---|---|---|---|---|
| **Disney (WDI + Disney Research Zurich)** | **Droidi BDX** (Star Wars) | **Deep RL** locomotion + sim-to-real | Policy RL addestrata in simulazione (NVIDIA Isaac Lab + MuJoCo) per eseguire animazioni d'artista mantenendo equilibrio; domain randomization per il sim-to-real; HW con 2 NVIDIA Jetson | **Dispiegato** (Galaxy's Edge dal 2023; poi FL, Paris, Tokyo, navi) | thewaltdisneycompany.com; arXiv 2501.05204 (2025) |
| **Disney + NVIDIA + Google DeepMind** | **Olaf** robotico (World of Frozen) | **Deep RL** + stack conversazionale moderato | RL nel simulatore "Kamino" (su NVIDIA **Newton**) per camminare su una barca in movimento; conversazione = speech recognition + intent detection su **albero di risposte curato/moderato** (non LLM libero) | **Dispiegato** (Disneyland Paris, 29/03/2026; GTC 2026) | thewaltdisneycompany.com; wdwnt.com (2026) |
| **NVIDIA/Disney/DeepMind** | **Newton** (physics engine) | Infrastruttura RL differenziabile | Simulazione contact-rich per addestrare policy di personaggi robotici prima dell'hardware | Annunciato GTC 2025; usato per Olaf | variety.com (2025) |
| **Disney Research** | AMOR, ReActor, RobotKeyframing | RL multi-obiettivo / retargeting | Policy RL condizionata su pesi di reward (frontiera di Pareto) per regolare a runtime il comportamento del personaggio | Ricerca (peer-review), upstream dei robot | la.disneyresearch.com; arXiv 2407.11562 |
| **Disney** | **Project Kiwi** (Baby Groot) | Robot bipede free-roaming | Piattaforma per piccoli personaggi che camminano; **RL non confermato** per l'unità 2021 (probabile gait ingegnerizzato + puppeteering) | Prototipo | techcrunch.com (2021) |
| **Holovis + ETF** | **HoloTrac / "Deep Smarts"** — *LEGO Factory Adventure* (LEGOLAND New York) | **Deep-learning CV** (face/attribute, body/hand tracking) | Camere a bordo rilevano l'ospite; reti deep "trasformano" il volto in una Minifigure che ne specchia aspetto ed espressione/movimenti in <0,5 s, su veicolo trackless ETF | **Dispiegato** | holovis.com/projects/lego-factory; legoland.com |
| *(ricerca)* | Piattaforma "Interactive AI Character Experiences" | **Generative AI**: LLM + memoria + sintesi multimodale | Input vocale/video → LLM (memoria, personalità regolabile) → voce/volto/corpo + image generation; 5 slider di personalità | Prototipo (SIGGRAPH 2025) | dl.acm.org/10.1145/3721238.3730762 |
| **Oceaneering** | REVOLUTION Tru-Trackless ("self-driving") | Navigazione autonoma (AGV) | Veicoli free-ranging con navigazione inerziale, laser scanner, encoder, magneti/RFID | Dispiegato | inparkmagazine.com |
| **Triotech** | XD Dark Ride / **Maestro** | *Nessun ML* | Puntamento "device-free" via **Ultraleap Leap Motion** (tracking IR della mano), non CV/ML | Dispiegato | trio-tech.com/maestro |
| **Alterface** | Interactive dark rides (partner Sally) | *Nessun ML* | Tracking di puntamento ad alta precisione (~30 ms) + show control | Dispiegato | alterface.com |
| **Sally Dark Rides / Dynamic Attractions / ETF / Simworx** | Dark ride / trackless / dueling | *Nessun ML* | Animatronics tradizionali, navigazione e game-logic; interattività via Alterface | Dispiegato | siti rispettivi |
| **Brogent** | Flying theatres | AI **solo in produzione contenuti** | Unreal/AIGC per creare i film; non AI adattiva in tempo reale | Theatre dispiegati; AI roadmap | brogent.com |
| **Mack Rides / MackNeXT** | Eatrenalin ("AI guide") | *Marketing* | "Guida AI" = narrazione/branding, nessun ML documentato | Dispiegato | wikipedia Eatrenalin |

### A3 — Photo system con AI (sezione centrale — dettaglio in §3)

| Vendor / parco | Sistema | Tipo di AI | Come è usata | Maturità | Reale/Marketing |
|---|---|---|---|---|---|
| **Pomvom (+ Picsolve, fusi 2025)** | "Picture/Video of Me"; piattaforma Picsolve | **Riconoscimento facciale** (AWS Rekognition) | Selfie dell'ospite → template facciale numerico monodirezionale → matching su camere giostra, fotografi, green-screen, video wall; "il tuo volto è il tuo account"; age-check minori | **Dispiegato** (Merlin: Alton Towers 2023; San Diego Zoo 2023; Dubai Parks) | **Reale (alta)** |
| **Picsolve** | "Association technology" + ride capture multi-frame | Face-rec + selezione frame | Camere shutterless 4-30 fps, 16MP; profilazione demografica via AWS per targeting prodotti | Dispiegato (350+ installazioni) | Reale (alta) |
| **Semnox** | Parafait "spot photo systems" | **Riconoscimento facciale** | Registrazione volto pre-ingresso; camere confermano l'ospite in ogni sedile e abbinano la foto | Piattaforma diffusa; modulo face-rec da quantificare | Reale (media) |
| **Captomatic** | On-ride camera system | Automazione + integrazione face-rec | Trigger/ripresa/editing/consegna automatici per fila/vettura specifica; API per look immagine; "integra sistemi di riconoscimento facciale" | Dispiegato | Reale automazione; AI per integrazione |
| **Magic Memories** | Ride photo multi-angolo; booth | Convenzionale + "AI avatars" (marketing) | Camere multi-angolo per scegliere il frame e ritagliare estranei; booth con "AI avatars / curated content" | Ride photo diffuso; AI elementi early/marketing | Reale capture; **AI debole** |
| **PictureWorks / PictureAir** | Soluzione coaster automatizzata | Trigger sensoriale | Fino a 6 camere attivate da sensori | Dispiegato | Automazione; AI non confermata |
| **ImageInsight / System Insight / NXT Capture / Kodak Moments** | Suite foto di parco | Capture+matching standard | Coaster/water/dark ride, roving, green-screen | Dispiegato | Nessun AME sostanziale |
| **Flowstate / KoolReplay** | Video/clip auto (surf park / parchi) | Claim AI tracking/highlight | Auto-clip rider; meccanismo non verificato | Marketing/lead | Da verificare |
| **Disney PhotoPass / Memory Maker** | Abbinamento foto on-ride | **RFID (MagicBand), NON face-rec** | Le foto on-ride si associano via RFID; il face-rec è usato **sulle navi** per ordinare le foto; AR "PhotoPass Lenses" = effetti | Dispiegato | **Correzione: ride photo = RFID** |
| **Universal "Photo Validation"** | Turnstile 3D template | Validazione biometrica d'**ingresso** | Camera 3D + IR creano "Photo Template" (dati, non foto) per anti-frode Express Pass | Dispiegato | **Controllo accesso, non foto-souvenir** |

### A4 — Code, crowd analytics, personalizzazione, pricing (AI reale, lato operazioni)

| Azienda | Prodotto | Tipo di AI | Come è usata | Maturità | Fonte |
|---|---|---|---|---|---|
| **Connect&GO + Moov AI** | **Konnect AttendX** (Predictor + Smart Pricing) | **ML forecasting + dynamic pricing** | Modello per-parco su 2 anni di affluenza/vendite + meteo/calendari scolastici; pricing con analisi di sensibilità prezzo/domanda (elasticità), override operatore | **Dispiegato (GA ~2024)** | connectngo.com; moov.ai; blooloop.com |
| **Safari AI** | Dispatch optimization / wait times | **Computer vision** | Le telecamere IP esistenti misurano conteggi, throughput, dwell, lunghezza code, se i veicoli partono pieni (dispatch) | Dispiegato | getsafari.ai |
| **V-Count** | Nano/Ultima AI + BoostBI | **CV people counting** | Sensori stereo 3D con AI contano i visitatori, occupancy, flussi, alert sovraffollamento (fino al 99%) | Dispiegato | v-count.com |
| **Six Flags + Google Cloud** | Assistente virtuale (Vertex AI) | **LLM generativo** | Raccomandazioni personalizzate, ordini, parcheggio nell'app | Annunciato 2023, stato live incerto | prnewswire.com (2023) |
| **Attractions.io** | Conversational AI Assistant; **GX Pulse** | NLP/ML + sentiment | Assistente in-app NL con raccomandazioni; GX Pulse = sentiment NLP su recensioni per fase del viaggio | Dispiegato (clienti: Chester Zoo, KSC, Alton Towers) | attractions.io |
| **Convious** | Convious AI | LLM/chatbot commerce | Acquisto/modifica biglietti via WhatsApp/web in conversazione | Lanciato IAAPA 2024 | blooloop.com |
| **Embed (Sacoa)** | Embed AI / Sidequest AI | ML analytics + reco | Previsione ricavi, staffing, pricing agile; raccomandazione giochi (FEC) | IAAPA 2025 (Brass Ring) | embedcard.com |
| **accesso** | LoQueue / Qsmart / Prism; (+ Dexibit 2026) | Virtual queue adattivo; analytics | Ricalcolo dinamico tempi d'attesa; ML rivendicato nei brevetti (§4.5); Dexibit = forecasting cross-platform | Dispiegato | accesso.com; blooloop.com |
| **Disney** | **Genie / Genie+** | Reco engine + analytics predittive | Itinerari ottimizzati su attese/spettacoli/ristori + dati storici di affluenza (anche crowd-balancing) | Dispiegato (2021→) | hftp.org; digitaldefynd.com |
| *(terzi)* | TouringPlans, modelli accademici | ML supervisionato (Random Forest, NN) | Previsione tempi d'attesa Disney su ~190 feature (meteo, parate, scuole, stagione) | Dispiegato in tool consumer | touringplans.com |
| **Legoland / ROLLER** | Surge pricing / dynamic pricing | Pricing a regole/domanda | Legoland: prezzo legato a giornate di sole (per lo più regole) | Dispiegato | aol.com; roller.software |

**Timeline IAAPA Expo:** 2024 (Orlando) — AI tema centrale: sessione "Using AI to Your Advantage" (Connect&GO), DOF Robotics (AI+robotica), Convious AI, Oscar Sort. 2025 — Attractions.io GX Pulse, D-Tex Bolt-iT (edge-AI safety), accesso "AI-powered commerce"/Dexibit, Embed AI.

---

## 3. PARTE B — Photo system con AI: approfondimento

**Conferma:** i photo system con AI **esistono e sono dispiegati**. Tre meccanismi distinti, tutti rilevanti come prior art:

1. **Matching ospite↔contenuti tramite riconoscimento facciale** (il più diffuso e maturo).
   - **Pomvom/Picsolve**: pipeline selfie → template facciale numerico monodirezionale → match su tutte le sorgenti di cattura. Backend **AWS Rekognition**. Dispiegato in scala (Merlin, San Diego Zoo, Dubai Parks). Picsolve dichiara anche **profilazione demografica** (fascia d'età) per il targeting commerciale on-site.
   - **Semnox Parafait**: registrazione facciale pre-ingresso e conferma dell'ospite **per singolo sedile**.
   - **Captomatic**: automazione di cattura con **integrazione** di sistemi di riconoscimento facciale di terzi.
2. **Selezione automatica del "best-frame" / scatto al momento ottimale** (ML di imaging, non specifico-parco ma direttamente applicabile).
   - **Microsoft US 9,807,301 B1**: buffering continuo di N frame pre/post-scatto; **modello predittivo** che classifica i frame dal migliore al peggiore su feature alte (qualità, nitidezza) e basse (**occhi aperti/chiusi**), con auto-regolazione di esposizione/ISO/WB e auto-enhancement.
   - **Smile detection → auto-scatto**: US 8,983,202 B2 / WO 2012/036669 A1; US 9,268,995 B2.
   - **Eyes-open detection**: US 8,761,516.
3. **Compositing / effetti / generazione**: green-screen, rimozione sfondo, "AI avatars" (Magic Memories), AR overlay (Disney PhotoPass Lenses). Qui l'"AI" è spesso più marketing che metodologia documentata.

**Tre confusioni di categoria da evitare nel prior art** (rilevate e separate):
- **Disney ride photo = RFID (MagicBand), non riconoscimento facciale.** Il face-rec Disney è usato per **ordinare le foto sulle navi** e in **test d'ingresso** (Magic Kingdom 2021; gate 2026), non per le foto on-ride dei parchi.
- **Universal "Photo Validation" = controllo d'accesso/Express Pass** (template 3D, non fotografia souvenir).
- **"Generative AI + theme park"** in molte notizie = strumenti di **design** della giostra o generatori d'immagini consumer, non photo system on-ride.

**Contenzioso privacy biometrica (contesto, da tenere presente per il valore/uso commerciale del brevetto):**
- **Six Flags** — *Rosenbach v. Six Flags*: storica sentenza Illinois (2019, **BIPA**) sulle impronte ai cancelli; **settlement $36M**.
- **Disney** — class action BIPA proposta 2025 (face scanning, MagicBand/PhotoPass, profili cross-business); reportistica di un separato settlement $10M.
- Implicazione progettuale: una soluzione di **matching face-template "privacy-by-design"** (template monodirezionale, niente storage di identificatori biometrici, cancellazione all'uscita) ha sia rilevanza tecnica sia valore commerciale. *(Nota: Universal US 11,321,554 — §4.2 — rivendica proprio la cancellazione del dato facciale all'uscita.)*

---

## 4. PARTE C — Documenti brevettuali (prior art)

> Legenda affidabilità: **[V]** numero/titolo/richiedente confermati su pagina brevetto; **[V-news]** confermato da fonti multiple + PDF USPTO ma non da testo pagina; **[DA VERIFICARE]** campo non confermato. *Le date di concessione "giorno esatto" vanno comunque riconfermate.*

### Tabella riepilogativa

| # | Numero | Titolo (sintesi) | Richiedente | Date chiave | Tema | Aff. |
|---|---|---|---|---|---|---|
| 1 | **US 6,526,158 B1** | Person-specific images in a public venue (face recognition) | CenterFrame / D. Goldberg | priorità **1996-09-04**; conc. 2003 | Foto/Face | **[V]** |
| 2 | US 6,819,783 B2 | Obtaining person-specific images (face) | famiglia Goldberg/Photonmotion | dep. 2003-11-14; conc. 2004 | Foto/Face | [V-news] |
| 3 | US 7,561,723 B2 | (continuazione famiglia Goldberg) | Goldberg | — | Foto/Face | [V] |
| 4 | **US 9,143,744 B2** | Park guest-activated image capture | Colorvision Int'l | dep. 2013-05-06; pri. 2012-05-04; conc. 2015-09-22 | Foto | **[V]** |
| 5 | US 9,332,138 B2 | Guest-activated image capture (venues) | Colorvision Int'l | conc. ~2016 | Foto | [DA VERIFICARE] |
| 6 | US 6,608,563 B2 | Automated photo capture/retrieval (RFID) | Lochtefeld/Weston | pri. 2000-01-26; conc. 2003 | Foto/RFID | [DA VERIFICARE] |
| 7 | US 2004/0201738 A1 | Auto access to venue images (trigger a sensore) | [DA VERIFICARE] | application | Foto | [DA VERIFICARE] |
| 8 | **US 9,807,301 B1** | Best-frame: buffering N frame + selezione/enhancement ML | **Microsoft Technology Licensing** | conc. 2017 | Imaging/best-frame | **[V]** |
| 9 | US 8,983,202 B2 / WO2012/036669 | Smile detection (auto-scatto) | [DA VERIFICARE] | — | Imaging | [V-news] |
| 10 | US 8,761,516 | Eyes open/closed detection | [DA VERIFICARE] | — | Imaging | [V-news] |
| 11 | **US 11,321,554 B2** | Gestione efficiente del face-rec in più aree (cancella all'uscita) | **Universal City Studios** | conc. ~2022-05 | Face/Ingresso | [V-news] |
| 12 | **US 9,393,697 B1** | Foot recognition per esperienza personalizzata | **Walt Disney (Switzerland)** | conc. 2016-07 | Biometria ID | **[V]** |
| 13 | US 10,861,267 B2 | Gamification/tracking ospite e **sedile** (RFID+pressione+camera) | **James A. Aman (indip.)** | pri. 2017-08-04; conc. 2020 | Tracking | **[V]** |
| 14 | US 11,443,575 B2 | (divisionale di #13) | James A. Aman (indip.) | dep. 2018-08-04; conc. 2022 | Tracking | [V-news] |
| 15 | **US 9,610,510 B2** | Controllo veicolo in base alla **consapevolezza/stato** dell'occupante | **Disney Enterprises** | dep. 2015-07-21; conc. 2017 | Ride control | **[V]** |
| 16 | US 9,943,769 B2 | Veicoli trackless controllati su **stato occupante** (divisionale) | Disney Enterprises | conc. 2018 | Ride control | [V] |
| 17 | **US 9,038,543 B2** | **Giostra con sistema di riconoscimento dell'espressione facciale** | **Maurer Söhne** | conc. 2015-05-26 | Ride control/CV | **[V]** |
| 18 | US 11,899,442 B2 | Structural health monitoring via IoT + ML (generico) | [DA VERIFICARE] | conc. | Manut. predittiva | [DA VERIFICARE] |
| 19 | **US 2026/0109316 A1** | **Verifica corretto uso dei restraint (ML + CV)** | **Disney Enterprises** | pubbl. **2026-04-23** | ML/CV sicurezza | **[V-news]** |
| 20 | **US 10,152,840 B2** | Virtual queue system | accesso / Lo-Q | dep. 2017-03-15; conc. 2018-12-11 | Code | [V] |
| 21 | **US 10,943,188 B2** | Virtual queuing (calcolo tempo d'attesa) | **Universal City Studios** (Schwartz, Geraghty) | dep. 2017-11-08; conc. 2021 | Code | **[V]** |
| 22 | US 11,775,883 B2 | Virtual queuing (dispatch comune) | Universal City Studios | conc. 2023-10-03 | Code | [V] |
| 23 | US 10,922,933 B2 | Posti a sedere efficienti (metrica posti vuoti) | Universal City Studios | pri. 2019-05-09; conc. 2021 | Code/Seating | [V] |
| 24 | US 11,936,815 B2 | Enhanced virtual queuing (ML **generico**) | accesso | conc. 2024 | Code/ML | [V-news] |
| 25 | US 11,968,328 B2 | Enhanced virtual queuing + access control | accesso | conc. 2024 | Code/ML | [V-news] |
| 26 | US 11,522,998 B2 | Enhanced virtual queuing (simulazione) | accesso | conc. 2022 | Code/ML | [V-news] |
| 27 | **US 11,526,916 B2** / WO2016176506A1 | **"Intelligent prediction of queue wait times"** — ML specifico (Bayes/NN/ALS, GPS, beacon, meteo, face-rec) | accesso | — | Code/ML | [V-news] |
| 28 | US 11,893,516 | Wait Time Recommender (per lo più a regole) | Disney | conc. 2024 | Code | [V-news] |
| 29 | US 7,955,168 B2 | Amusement ride and video game (interattivo) | **Disney Enterprises** (Mendelsohn) | dep. 2005-10-03; conc. 2011 | Interattivo | [V] |
| 30 | US 6,796,908 B2 | Interactive dark ride | Creative Kingdoms→MQ Gaming | conc. 2004 | Interattivo | [V] |
| 31 | (Disney "memories") | Generative AI da memorie dell'utente → personaggio AI | Disney | dep. ~2024 | Gen-AI | [DA VERIFICARE numero] |

### 4.1 Foto on-ride e matching foto-ospite (tema centrale)
- **US 6,526,158 B1 — CenterFrame / David A. Goldberg** *(priorità 1996-09-04, conc. 2003)*. **Riferimento fondazionale**: raccogliere immagini di un avventore in un venue di intrattenimento e recuperare quelle specifiche **tramite riconoscimento facciale**, con biometria "soft" (abbigliamento, altezza, accompagnatori, occhiali, barba) per migliorare il match. Famiglia: US 6,819,783; US 7,561,723. → *È l'anticipazione più pericolosa per qualunque claim di "abbinamento foto-ospite per volto".*
- **US 9,143,744 B2 — Colorvision** *(pri. 2012, conc. 2015)*: aree tematiche con camera + chiosco con lettore ID; l'ospite presenta un ID che **fa scattare la camera automaticamente** e collega le foto al suo album; dipendenti rivendicano l'inserimento dell'ospite in una scena panoramica. Famiglia: US 9,332,138; US 9,214,032; US 10,257,442; US 10,834,335 (video wall/floor/ceiling, "souvenir portfolios").
- **US 6,608,563 B2 — (Weston/Creative Kingdoms lineage)**: **tag RFID con ID univoco** per cattura/indicizzazione automatica di foto/video e recupero successivo (antenato concettuale del PhotoPass/MagicBand).
- **US 2004/0201738 A1**: sensori piezo/strain rilevano il carico della giostra → break di un fascio IR/laser → scatto automatico on-ride.
- **Best-frame/qualità (imaging generale, applicabile):** **US 9,807,301 (Microsoft)** selezione ML del frame migliore; smile detection (US 8,983,202; WO2012/036669; US 9,268,995); eyes-open (US 8,761,516).
- **Picsolve/Pomvom:** nessun brevetto proprietario di face-rec confermato per numero; Picsolve detiene IP sull'**"Experience Wall"** video; la piattaforma face-rec poggia su **AWS Rekognition** (tecnologia di terzi). *Spazio: il "come" dell'integrazione on-ride privacy-preserving resta poco coperto da loro brevetti.*

### 4.2 Riconoscimento facciale / biometria dell'ospite
- **US 11,321,554 B2 — Universal City Studios** *(~2022)*: all'ingresso il volto è legato a biglietto/credenziali; **il dato facciale è cancellato dal DB attivo all'uscita** (match solo con gli ospiti dentro al parco). Sottende il face-rec d'ingresso di Universal Orlando/Epic Universe.
- **US 9,393,697 B1 — Walt Disney (Switzerland)** *(2016)*: **riconoscimento del piede/scarpa** (forma 3D + aspetto) come ID biometrico non facciale per personalizzare l'esperienza.
- **US 10,861,267 B2 / US 11,443,575 B2 — James A. Aman (inventore indipendente, NON Universal/Disney)**: RFID esteso + **lettori RFID + sensori di pressione + camere** per tracciare l'ospite **fino al singolo sedile** su veicoli guidati/free-ranging; i dati alimentano un sistema di gioco che personalizza gli effetti. *(Correzione rispetto all'assunzione iniziale: titolarità di un indipendente.)*

### 4.3 Controllo della giostra basato su sensori/ML
- **US 9,610,510 B2 / US 9,943,769 B2 — Disney Enterprises** *(dep. 2015, conc. 2017/2018)*: un sensore sul **veicolo trackless** rileva dati del passeggero → si determina lo **stato del passeggero** (camere, sensori biometrici, RFID, software di "emotion/attention determination") → in base a stato + posizione si seleziona un **percorso alternativo** per modificare lo stato (regolare velocità/scenografia, mitigare il mal di moto, adattare il contenuto). → *Riferimento potenzialmente bloccante per "ride adattiva in base a emozione/stato del rider".*
- **US 9,038,543 B2 — Maurer Söhne** *(2015)*: **giostra con sistema di riconoscimento dell'espressione facciale** — una o più videocamere nel veicolo registrano il volto del passeggero **durante** la corsa; un sistema di riconoscimento analizza l'espressione e la **classifica per posizione lungo il tracciato**. → *Un OEM di giostre detiene già CV emozionale in-ride: prior art forte e potenzialmente bloccante.*

### 4.4 Manutenzione predittiva / sicurezza (ML/CV)
- **Nessun brevetto concesso** trovato che rivendichi specificamente la manutenzione predittiva ML/CV **di giostre**. Il più vicino è **US 11,899,442 B2** (Structural Health Monitoring IoT+ML, **generico**, non ride-specific).
- **US 2026/0109316 A1 — Disney Enterprises** *(pubbl. 2026-04-23)*: piattaforma di **verifica restraint** con più **modelli ML** (rilevano corpo/posizione/taglia, tipo di restraint, lunghezza visibile della cintura, posizione), fusi con sensori (seduta/clasp/prossimità, encoder, microfoni, RFID, LIDAR) per confermare la chiusura e velocizzare il carico. → *AI in funzione safety-critical: rilevante sia come prior art sia come benchmark di novità.*
- *(Contesto)* Brevetti Disney 2026 su **CV per ispezione bus-bar/conductor-rail** (camere sul veicolo + ML per corrosione/usura), riportati dalla stampa di settore.

### 4.5 Code / crowd / posti (ML "vero" vs generico)
- **US 10,152,840 B2 — accesso/Lo-Q**: virtual queue con wearable/chioschi.
- **US 10,943,188 B2 / US 11,775,883 B2 — Universal**: calcolo del tempo d'attesa da numero/dimensione gruppi e capacità; gestione con dispatch comune. **US 10,922,933 B2 — Universal**: ottimizzazione posti con **metrica dei posti vuoti**.
- **accesso "enhanced virtual queuing" (US 11,936,815 / 11,968,328 / 11,522,998)**: il ML è descritto in modo **generico** ("a machine learning algorithm"); la novità è l'architettura (prediction module + queue manager + load balancer; simulazione di combinazioni di coda; chiave d'accesso a sensori).
- **US 11,526,916 B2 / WO2016176506A1 — accesso "Intelligent prediction of queue wait times"**: **qui** la metodologia ML è specifica — **algoritmo Bayesiano / nearest-neighbor / ALS / reti neurali**, auto-addestrante, alimentato da misura diretta del tempo d'attesa (**camere con riconoscimento facciale** o beacon che tracciano i dispositivi mobili), **GPS**, calendari eventi, **meteo**, metadati (ora, giorno, stagione) e tempo di percorrenza dell'ospite. → *Da aggiungere allo scope se il brevetto tocca la previsione code con ML.*
- **US 11,893,516 — Disney** ("Wait Time Recommender", per lo più a regole).

### 4.6 Interattive / scoring
- **US 7,955,168 B2 — Disney (Mendelsohn)**: collega una giostra interattiva in-park a un **videogioco remoto/casalingo** sincronizzato (scoring target/laser).
- **US 6,796,908 B2 — Creative Kingdoms→MQ Gaming**: classe fondazionale di **dark ride interattive** con effetti che rispondono alle azioni del rider. *(On-theme anche US 5,382,026; US 9,463,379.)*

### 4.7 Generative AI / personaggi
- **Disney — domanda "generative AI da memorie"** *(dep. ~2024, numero [DA VERIFICARE])*: traduce le memorie/emozioni dell'utente in un **"personaggio AI interattivo"** che genera contenuto personalizzato (es. un personaggio che crea una canzone sui ricordi del parco), implementabile in oggetti fisici/animatronics o digitali (app/AR/VR).
- *(Contesto)* Il lavoro Disney Research su locomozione RL (BDX/Olaf, AMOR, ReActor) risulta **pubblicato come paper accademici, non come brevetti**: rilevante come stato dell'arte tecnico, non come prior art brevettuale.

---

## 5. PARTE D — "AI vera" vs marketing (verdetto rapido)

**AI/ML genuino e dispiegato:** Pomvom/Picsolve (face-rec foto); DMT RideGuard, OneWatt (manut. predittiva); Disney BDX/Olaf (RL), Holovis HoloTrac (CV); Safari AI, V-Count (CV crowd); Connect&GO/Moov AI (forecasting+pricing); Attractions.io GX Pulse (NLP); Six Flags Vertex AI (LLM, stato live incerto); modelli ML di previsione attese (terzi).

**Reale ma "sfumato"/parziale:** Disney Genie+ (personalizzazione reale ma anche crowd-balancing); Disney "real-time AI pricing" (grado di ML non confermato); accesso LoQueue in produzione (regole adattive vs modello addestrato); Embed AI (direzione reale, dettagli scarsi); Legoland surge pricing (a regole sul meteo).

**"AI" che è in realtà automazione/tracking/PLC (NON ML):** Maurer SmartCoaster, Intamin blocking, KUKA/Robocoaster, Gerstlauer, S&S, Premier (controllo deterministico); Triotech Maestro (Leap Motion), Alterface, Sally, Dynamic Attractions, ETF, Simworx (tracking + show control); Amusement Technical RideMinder (IoT a soglie); Zamperla "smart" (monitoraggio remoto); Brogent/Mack "AI" (produzione contenuti/branding).

**Da NON sovra-attribuire:** Universal Virtual Line e app Six Flags/Cedar Fair (virtual queue / display, non previsione ML); Disney PhotoPass on-ride (RFID, non face-rec).

---

## 6. PARTE E — Gap e osservazioni di brevettabilità / FTO

*(Osservazioni di landscape, non parere legale definitivo. Poiché hai scelto un "panorama completo", indico sia i riferimenti potenzialmente bloccanti sia gli spazi bianchi più promettenti; andranno calibrati sull'oggetto effettivo della rivendicazione.)*

**Principali riferimenti potenzialmente bloccanti (FTO) per tema:**
- *Foto-ospite per volto:* **US 6,526,158 (CenterFrame/Goldberg, pri. 1996)** + famiglia; integrazione Pomvom/Picsolve dispiegata.
- *Scatto/selezione automatica del frame:* **US 9,807,301 (Microsoft)** + smile/eyes-open detection.
- *Cattura on-ride attivata automaticamente:* **US 9,143,744 (Colorvision)**, US 2004/0201738 (trigger a sensore), US 6,608,563 (RFID).
- *Giostra adattiva su emozione/stato del rider:* **US 9,610,510 / US 9,943,769 (Disney)** e **US 9,038,543 (Maurer, espressione facciale in-ride)**.
- *Previsione code con ML:* **US 11,526,916 (accesso)**; Universal US 10,943,188 / US 11,775,883.
- *Biometria d'ingresso con cancellazione all'uscita:* **US 11,321,554 (Universal)**.

**Possibili spazi bianchi / dove orientare i claim (da validare con ricerca di novità mirata):**
1. **Photo system "privacy-by-design" integrato on-ride:** pipeline end-to-end con **matching su template monodirezionale on-device** (niente storage di identificatori biometrici, cancellazione all'uscita) **combinata** con selezione best-frame ML e sincronizzazione al passaggio del veicolo. I singoli mattoni sono noti; una **specifica integrazione tecnica con effetto tecnico verificabile** (latenza, niente DB biometrico persistente, conformità BIPA/GDPR) può essere difendibile — e ha forte valore commerciale dato il contenzioso biometrico.
2. **Cattura innescata da emozione/espressione in tempo reale** che seleziona il frame in funzione di un picco emotivo rilevato a bordo — attenzione però a **Maurer US 9,038,543** (espressione in-ride) e **Microsoft US 9,807,301** (selezione frame): la novità andrà nel *come si combinano* (es. trigger emozione → finestra di buffering → best-frame → match volto), non nei singoli passi.
3. **Manutenzione predittiva ride-specific:** i brevetti SHM sono **generici**; modelli addestrati su **modi di guasto propri della giostra** (LSM/LIM, ruote, restraint, dinamica del treno) con effetto tecnico misurabile sono un'area meno presidiata da brevetti (DMT/OneWatt hanno prodotti, ma la copertura brevettuale ride-specific risulta sottile).
4. **Generative AI "safety-bounded" in contesto fisico di giostra:** personaggi conversazionali con **garanzie di moderazione/sicurezza** e integrazione show-control (l'Olaf dispiegato usa un albero curato; il landscape brevettuale è ancora rado al di fuori della domanda Disney "memories").
5. **Verifica restraint/condizione del passeggero con CV:** **Disney US 2026/0109316** ha appena occupato l'area safety-critical; eventuali claim qui vanno costruiti con attenzione alla distanza da quella domanda.

---

## 7. Fonti principali (selezione, per categoria)

**Photo system / face-rec:** pomvom.com/faq; inparkmagazine.com/picsolve-biometric; parkworld-online.com (Picsolve face-rec); blooloop.com (Picsolve/Pomvom merger); thedeadpixelssociety.com (accordo Merlin); semnox.com; captomatic.com; disneyworld.disney.go.com (PhotoPass); attractionsmagazine.com (Universal Photo Validation).

**Controllo/manutenzione:** dmt-group.com/rideguard.html; iot-now.com (2024, Movie Park); amusementtoday.com (2026, German Excellence Award); thenextweb.com (2018, OneWatt/Efteling); maurer-rides.de/smartcoaster; kuka.com (KUKA Coaster); amusementtechnical.com (RideMinder).

**Robot/animatronics/CV:** thewaltdisneycompany.com (BDX, Olaf); arXiv 2501.05204; variety.com (NVIDIA Newton); holovis.com/projects/lego-factory; legoland.com (LEGO Factory Adventure).

**Operazioni/code/pricing:** connectngo.com + moov.ai (Konnect AttendX); getsafari.ai; v-count.com; prnewswire.com (Six Flags/Google 2023); attractions.io (GX Pulse); blooloop.com (recensioni IAAPA 2024/2025).

**Brevetti (Google Patents / USPTO):** US6526158, US9143744, US9807301, US9038543, US9610510, US9943769, US11321554, US9393697, US10861267, US11443575, US10152840, US10943188, US11775883, US10922933, US11526916/WO2016176506A1, US7955168, US6796908; domanda Disney restraint US 2026/0109316 A1.

---

*Nota finale: i numeri brevettuali e le date qui riportati provengono da ricerche verificate ma con fetch diretto delle pagine bloccato nell'ambiente; per il fascicolo di deposito riconfermare ogni riferimento su Espacenet/USPTO Patent Public Search/DEPATISnet ed eseguire una ricerca di novità mirata sull'oggetto specifico della rivendicazione (incluse classi CPC come A63G "carousels, swings, rides"; G06V "image/video recognition"; G07C "time/attendance, queue").*
