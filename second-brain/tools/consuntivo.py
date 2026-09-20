#!/usr/bin/env python3
"""Consuntivo per commessa × nodo × anno dall'estrazione completa del gestionale.

Produce (o aggiorna in state.json) la chiave `cons`:

  cons = {agg, file, fonte, gen, tipi, note, controlli, cm: {CODICE: {ric: {oc, fat}, nd: {NODO: {ANNO: {fat, con, ddt, ord, int, alt, n}}}}}}

Stadi di costo (Tipo di costo "2 - COSTO"):
  fat   fatture fornitore: Fattura riepilogativa / immediata / accompagnatoria, Nota debito, Nota credito (segno come nel gestionale)
  con   costi contabilizzati sul progetto ("Gestione contabilità progetti", Cliente/fornitore = Fornitore)
  ddt   merce o lavorazioni ricevute e non ancora fatturate: Documento di trasporto, Documenti c/lavoro passivo
  ord   ordini fornitore ancora aperti (F-OA / F-OS / F-OCL)
  int   righe interne ("Gestione contabilità progetti", Cliente/fornitore = Interno): quasi sempre senza costo
  alt   qualunque altro tipo di documento con costo
Regola di Luca Tirotta (15/09/2026): una riga d'ordine sparisce dall'estrazione quando diventa DDT o fattura,
quindi gli stadi non si sovrappongono. I numeri restano quelli del gestionale; lo strumento però segnala in
cons.controlli i casi sospetti, da verificare con Luca: righe DDT identiche a righe di fattura (stesso
progetto, fornitore, articolo, quantità e importo) e ordini aperti con consegne o fatture dello stesso
fornitore e articolo (consegne parziali). Non vengono corretti automaticamente.
Ricavi (Tipo di costo "1 - RICAVO", lato cliente): oc = Ordine cliente (valore a contratto nel gestionale),
  fat = fatture al cliente (note di credito con il loro segno).
Regole sui nodi: "MANCANTE", vuoto o uguale al codice del progetto (il gestionale registra così i costi
  a livello di commessa) diventano "-" = senza nodo.
Righe senza Anno né Data consegna (ordini di servizi senza data): contate nell'anno dell'estrazione (--agg),
  non scartate.
Il codice progetto viene normalizzato con norm_code() (spazi tolti, maiuscolo); la stessa regola la usa
commesse_gestionale.py, così le chiavi di cons.cm coincidono con commesse[].code.

Sorgenti accettate:
  --pkl  file pickle {hdr: [...], rows: [[...]]} (cache di un'estrazione xlsx)
  --xlsx estrazione Excel del gestionale (foglio Foglio1, intestazione in riga 1)
  --csv  CSV aggregato prodotto dallo script Apps Script `preparaConsuntivo()`:
         colonne Progetto;Nodo;Anno;Stadio;Costo;Righe  (Stadio già classificato con le stesse regole)

Esempi:
  consuntivo.py --pkl gestionale_full.pkl --state state.json --agg 2026-09-16 --file "Nuovo Foglio 2.xlsx"
  consuntivo.py --xlsx export.xlsx --out cons.json --all
Senza --all vengono tenute solo le commesse presenti in state.json (campo commesse[].code).
"""
import argparse, csv, datetime as dt, json, pickle, re, sys
from collections import defaultdict

CAMPI = ['Cliente/fornitore', 'Tipo di costo', 'Cod. documento', 'Progetto', 'Data consegna', 'Anno',
         'Ricavo', 'Costo', 'TipoDocumento', 'Nodo']
CAMPI_OPZ = ['Cod. fornitore', 'Codice articolo', 'Descrizione', 'Qt. acquistate', 'N° Doc.']
STADI = ('fat', 'con', 'ddt', 'ord', 'int', 'alt')
LEGENDA = {
    'fat': 'fatture fornitore (note di credito con il loro segno)',
    'con': 'costi contabilizzati sul progetto (contabilità progetti, fornitore)',
    'ddt': 'consegnato non ancora fatturato (DDT, documenti conto lavoro)',
    'ord': 'ordini fornitore aperti',
    'int': 'righe interne di contabilità progetti (di norma senza costo)',
    'alt': 'altri documenti con costo',
}


def norm_code(p):
    """Codice progetto canonico: senza spazi ai bordi, maiuscolo. Vuoto se manca o è "MANCANTE"/"#N/A"."""
    p = str(p or '').strip().upper()
    return '' if p in ('MANCANTE', '#N/A', 'N/A', 'NONE') else p


def num(x):
    if x is None or x == '':
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace('€', '').replace(' ', '')
    if s in ('#N/A', 'N/A', '-', 'None'):
        return 0.0
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def data_di(riga):
    d = riga.get('Data consegna')
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(d or ''))
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def anno_di(riga):
    a = riga.get('Anno')
    try:
        a = int(float(a))
        if 1990 < a < 2100:
            return a
    except (TypeError, ValueError):
        pass
    d = data_di(riga)
    if d:
        return d.year
    m = re.match(r'(\d{4})', str(riga.get('Data consegna') or ''))
    return int(m.group(1)) if m else None


def nodo_di(riga):
    n = str(riga.get('Nodo') or '').strip()
    if not n or n.upper() in ('MANCANTE', '#N/A', 'N/A', 'NONE'):
        return '-'
    if n.upper() == norm_code(riga.get('Progetto')):
        return '-'
    return n


def stadio(riga):
    """Classifica una riga: ritorna (stadio, importo con segno) oppure None se da ignorare."""
    tipo = str(riga.get('Tipo di costo') or '').strip()
    doc = str(riga.get('TipoDocumento') or '').strip()
    chi = str(riga.get('Cliente/fornitore') or '').strip()
    if tipo.startswith('1'):  # ricavo
        r = num(riga.get('Ricavo'))
        if doc == 'Ordine cliente':
            return 'ric_oc', r
        if doc.startswith('Fattura') or doc in ('Nota credito', 'Nota debito'):
            return 'ric_fat', r
        return None
    c = num(riga.get('Costo'))
    if doc == 'Ordine fornitore':
        return 'ord', c
    if doc in ('Documento di trasporto', 'Documenti c/lavoro passivo'):
        return 'ddt', c
    if doc.startswith('Fattura') or doc in ('Nota credito', 'Nota debito'):
        return 'fat', c
    if doc == 'Gestione contabilità progetti':
        return ('int' if chi == 'Interno' else 'con'), c
    if doc == 'Ordine cliente':
        return None
    return 'alt', c


def chiave_articolo(riga):
    """Fornitore + articolo (codice, altrimenti descrizione normalizzata): serve per riconoscere la stessa
    merce tra ordine, DDT e fattura."""
    forn = str(riga.get('Cod. fornitore') or '').strip()
    art = str(riga.get('Codice articolo') or '').strip().upper()
    if not art or art in ('#N/A', 'NONE'):
        art = re.sub(r'\s+', ' ', str(riga.get('Descrizione') or '').strip().upper())[:80]
    if not forn and not art:
        return None   # senza fornitore e articolo il confronto non ha senso: niente controlli su questa riga
    return (forn, art)


def righe_da_pkl(path):
    d = pickle.load(open(path, 'rb'))
    hdr = d['hdr']
    ix = {h: i for i, h in enumerate(hdr)}
    manca = [c for c in CAMPI if c not in ix]
    if manca:
        sys.exit('colonne mancanti nel pickle: %s' % manca)
    campi = CAMPI + [c for c in CAMPI_OPZ if c in ix]
    for r in d['rows']:
        yield {c: (r[ix[c]] if ix[c] < len(r) else None) for c in campi}


def righe_da_xlsx(path, foglio=None):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[foglio] if foglio else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    hdr = [str(h).strip() if h is not None else '' for h in next(it)]
    ix = {h: i for i, h in enumerate(hdr)}
    manca = [c for c in CAMPI if c not in ix]
    if manca:
        sys.exit('colonne mancanti nel foglio: %s' % manca)
    campi = CAMPI + [c for c in CAMPI_OPZ if c in ix]
    for r in it:
        if r is None or all(v is None for v in r):
            continue
        yield {c: (r[ix[c]] if ix[c] < len(r) else None) for c in campi}


def cella_vuota():
    d = {k: 0.0 for k in STADI}
    d['n'] = 0
    return d


def aggrega(righe, anno_agg=None, log=None):
    """cm -> {'ric': {oc, fat}, 'nd': {nodo: {anno: {stadio: importo, 'n': righe}}}}.

    Due passate: la prima raccoglie le righe classificate, la seconda riconosce (per progetto, fornitore e
    articolo) i DDT già fatturati e la parte già consegnata degli ordini aperti."""
    log = log if log is not None else {}
    cm = {}
    righe_costo = []  # (progetto, nodo, anno, stadio, importo, chiave, qta, data)
    senza_anno = 0
    for riga in righe:
        p = norm_code(riga.get('Progetto'))
        if not p:
            continue
        st = stadio(riga)
        if st is None:
            continue
        k, imp = st
        c = cm.setdefault(p, {'ric': {'oc': 0.0, 'fat': 0.0}, 'nd': {}})
        if k.startswith('ric_'):
            c['ric'][k[4:]] += imp
            continue
        a = anno_di(riga)
        if a is None:
            senza_anno += 1
            a = anno_agg or dt.date.today().year
        righe_costo.append([p, nodo_di(riga), a, k, imp, chiave_articolo(riga) if k in ('ddt', 'fat', 'ord', 'con') else None,
                            num(riga.get('Qt. acquistate')), data_di(riga)])
    log['righe_senza_anno'] = senza_anno
    # --- controlli (solo segnalazione, i numeri non cambiano)
    fatture = defaultdict(int)
    for r in righe_costo:
        if r[3] == 'fat' and r[5]:
            fatture[(r[0], r[5], round(r[6], 3), round(r[4], 2))] += 1
    gemelli = {'righe': 0, 'importo': 0.0, 'commesse': defaultdict(float)}
    for r in righe_costo:
        if r[3] == 'ddt' and r[5]:
            key = (r[0], r[5], round(r[6], 3), round(r[4], 2))
            if fatture.get(key):
                fatture[key] -= 1
                gemelli['righe'] += 1
                gemelli['importo'] += r[4]
                gemelli['commesse'][r[0]] += r[4]
    consegne = set()
    for r in righe_costo:
        if r[3] in ('ddt', 'fat') and r[5] and r[4] > 0:
            consegne.add((r[0], r[5]))
    parziali = {'righe': 0, 'importo': 0.0, 'commesse': defaultdict(float)}
    for r in righe_costo:
        if r[3] == 'ord' and r[5] and r[4] > 0 and (r[0], r[5]) in consegne:
            parziali['righe'] += 1
            parziali['importo'] += r[4]
            parziali['commesse'][r[0]] += r[4]
    # costi contabilizzati (FOR-PRO-COS) che hanno una fattura fornitore uguale nello stesso mese: potrebbero
    # essere la stessa spesa registrata due volte
    fat_mese = defaultdict(int)
    for r in righe_costo:
        if r[3] == 'fat' and r[5] and r[7]:
            fat_mese[(r[0], r[5][0], round(r[4], 2), r[7].strftime('%Y-%m'))] += 1
    con_gem = {'righe': 0, 'importo': 0.0, 'commesse': defaultdict(float)}
    for r in righe_costo:
        if r[3] == 'con' and r[5] and r[7] and r[4]:
            key = (r[0], r[5][0], round(r[4], 2), r[7].strftime('%Y-%m'))
            if fat_mese.get(key):
                fat_mese[key] -= 1
                con_gem['righe'] += 1
                con_gem['importo'] += r[4]
                con_gem['commesse'][r[0]] += r[4]
    log['ddt_gemelli'] = gemelli
    log['ordini_con_consegne'] = parziali
    log['contabilizzati_gemelli'] = con_gem
    # --- somma
    for p, nd, a, k, imp, _k, _q, _d in righe_costo:
        c = cm[p]
        cella = c['nd'].setdefault(nd, {}).setdefault(str(a), cella_vuota())
        cella[k] += imp
        cella['n'] += 1
    return finalizza(cm)


def finalizza(cm):
    """Arrotonda, toglie le chiavi a zero e i nodi vuoti: stessa forma per --pkl/--xlsx e per --csv."""
    out = {}
    for p, c in cm.items():
        ric = {k: round(v, 2) for k, v in c['ric'].items() if abs(v) > 0.004}
        nd_out = {}
        for nd, anni in c['nd'].items():
            anni_out = {}
            for a, cella in anni.items():
                cl = {'n': int(cella.get('n', 0))}
                for k in STADI:
                    v = round(cella.get(k, 0.0), 2)
                    if abs(v) >= 0.005:
                        cl[k] = v
                if len(cl) > 1 or cl['n']:
                    anni_out[a] = cl
            if anni_out:
                nd_out[nd] = anni_out
        out[p] = {'ric': ric, 'nd': nd_out}
    return out


def aggrega_csv(path):
    """CSV aggregato (Progetto;Nodo;Anno;Stadio;Costo;Righe) prodotto dall'Apps Script: separatore riconosciuto
    (; o ,), intestazione controllata; si ferma con un messaggio chiaro se il file non è quello atteso."""
    cm = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        prima = f.readline()
        sep = ';' if prima.count(';') >= prima.count(',') else ','
        f.seek(0)
        rd = csv.DictReader(f, delimiter=sep)
        mancano = [c for c in ('Progetto', 'Nodo', 'Anno', 'Stadio', 'Costo') if c not in (rd.fieldnames or [])]
        if mancano:
            sys.exit('il CSV %s non ha le colonne attese (%s): trovate %s' % (path, ', '.join(mancano), rd.fieldnames))
        for r in rd:
            p = norm_code(r.get('Progetto'))
            k = (r.get('Stadio') or '').strip()
            if not p or not k:
                continue
            c = cm.setdefault(p, {'ric': {'oc': 0.0, 'fat': 0.0}, 'nd': {}})
            imp = num(r.get('Costo'))
            if k.startswith('ric_'):
                c['ric'][k[4:]] = c['ric'].get(k[4:], 0.0) + imp
                continue
            if k not in STADI:
                continue
            nd = nodo_di({'Nodo': r.get('Nodo'), 'Progetto': p})
            try:
                a = str(int(float(r.get('Anno') or 0)))
            except ValueError:
                a = ''
            if not a or a == '0':
                continue
            cella = c['nd'].setdefault(nd, {}).setdefault(a, cella_vuota())
            cella[k] += imp
            cella['n'] += int(float(r.get('Righe') or 1))
    return finalizza(cm)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--pkl')
    src.add_argument('--xlsx')
    src.add_argument('--csv', help='CSV aggregato (Progetto;Nodo;Anno;Stadio;Costo;Righe)')
    ap.add_argument('--foglio', default=None)
    ap.add_argument('--state', help='state.json da aggiornare in place (chiave cons)')
    ap.add_argument('--out', help='scrive il solo oggetto cons in questo file')
    ap.add_argument('--agg', required=True, help='data dell\'estrazione AAAA-MM-GG')
    ap.add_argument('--file', default='', help='nome del file di origine, per la nota')
    ap.add_argument('--all', action='store_true', help='tieni tutti i progetti, non solo le commesse dello stato')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    try:
        anno_agg = int(a.agg[:4])
    except ValueError:
        sys.exit('--agg deve essere AAAA-MM-GG')

    log = {}
    if a.pkl:
        cm = aggrega(righe_da_pkl(a.pkl), anno_agg, log)
    elif a.xlsx:
        cm = aggrega(righe_da_xlsx(a.xlsx, a.foglio), anno_agg, log)
    else:
        cm = aggrega_csv(a.csv)

    stato = None
    if a.state:
        stato = json.load(open(a.state, encoding='utf-8'))
        if not a.all:
            codici = {norm_code(c.get('code')) for c in stato.get('commesse', [])}
            cm = {k: v for k, v in cm.items() if k in codici}
    if stato is not None:
        prev_cm = (stato.get('cons') or {}).get('cm') or {}
        if not cm:
            sys.exit('consuntivo vuoto (0 commesse): lo stato NON viene toccato. Controlla separatore e intestazione del file.')
        if prev_cm and len(cm) < 0.5 * len(prev_cm):
            sys.exit('consuntivo troppo piccolo (%d commesse contro %d nello stato): lo stato NON viene toccato.' % (len(cm), len(prev_cm)))
    note = []
    if log.get('righe_senza_anno'):
        note.append('%d righe senza data contate nell\'anno %d' % (log['righe_senza_anno'], anno_agg))
    controlli = {}
    for nome, k in (('ddt_gemelli', 'ddt_gemelli'), ('ordini_con_consegne', 'ordini_con_consegne'), ('contabilizzati_gemelli', 'contabilizzati_gemelli')):
        x = log.get(k)
        if not x or not x['righe']:
            continue
        per = {p: round(v, 2) for p, v in x['commesse'].items() if p in cm}
        controlli[nome] = {'righe': x['righe'], 'importo': round(x['importo'], 2), 'commesse': dict(sorted(per.items(), key=lambda kv: -kv[1])[:40])}
    if controlli.get('ddt_gemelli'):
        note.append('%d righe DDT identiche a righe di fattura (%.0f €): possibili doppioni, da verificare con Luca' % (controlli['ddt_gemelli']['righe'], controlli['ddt_gemelli']['importo']))
    if controlli.get('ordini_con_consegne'):
        note.append('%d righe d\'ordine aperte con consegne o fatture dello stesso articolo (%.0f €): possibili consegne parziali' % (controlli['ordini_con_consegne']['righe'], controlli['ordini_con_consegne']['importo']))
    if controlli.get('contabilizzati_gemelli'):
        note.append('%d costi contabilizzati con una fattura fornitore uguale nello stesso mese (%.0f €): possibili doppioni' % (controlli['contabilizzati_gemelli']['righe'], controlli['contabilizzati_gemelli']['importo']))
    if a.csv and stato is not None and not controlli:
        # dal foglio aggregato i controlli non si possono rifare: si conservano quelli dell'ultima estrazione completa
        prev = stato.get('cons') or {}
        if prev.get('controlli'):
            controlli = prev['controlli']
            note = [x for x in (prev.get('note') or []) if 'senza data' not in x and 'non ricalcolati' not in x] + note
            note.append('controlli non ricalcolati: consuntivo dal foglio aggregato, segnalazioni dell\'estrazione completa del %s' % (prev.get('agg') or '—'))
    cons = {
        'agg': a.agg, 'file': a.file,
        'fonte': 'estrazione completa del gestionale (tutti i tipi di documento), aggregata per commessa, nodo e anno',
        'gen': dt.datetime.now().isoformat(timespec='seconds'),
        'tipi': LEGENDA, 'note': note, 'controlli': controlli,
        'cm': cm,
    }
    if a.out:
        json.dump(cons, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if stato is not None:
        stato['cons'] = cons
        json.dump(stato, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    tot_nodi = sum(len(c['nd']) for c in cm.values())
    print('commesse: %d · nodi: %d · file: %s' % (len(cm), tot_nodi, a.file or '-'))
    for n in note:
        print('  nota: ' + n)
    if a.quiet:
        return
    for p in sorted(cm)[:60]:
        c = cm[p]
        somme = defaultdict(float)
        for anni in c['nd'].values():
            for cella in anni.values():
                for k, v in cella.items():
                    if k != 'n':
                        somme[k] += v
        print('  %-11s nodi %2d · fat %10.0f · con %9.0f · ddt %9.0f · ord %10.0f · OC %10.0f · FAT %10.0f' % (
            p, len(c['nd']), somme['fat'], somme['con'], somme['ddt'], somme['ord'], c['ric'].get('oc', 0), c['ric'].get('fat', 0)))


if __name__ == '__main__':
    main()
