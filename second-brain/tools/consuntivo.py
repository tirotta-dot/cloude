#!/usr/bin/env python3
"""Consuntivo per commessa × nodo × anno dall'estrazione completa del gestionale.

Produce (o aggiorna in state.json) la chiave `cons`:

  cons = {agg, file, fonte, gen, tipi, cm: {CODICE: {ric: {oc, fat}, nd: {NODO: {ANNO: {fat, con, ddt, ord, int, alt, n}}}}}}

Stadi di costo (Tipo di costo "2 - COSTO"):
  fat  fatture fornitore: Fattura riepilogativa / immediata / accompagnatoria, Nota debito (+), Nota credito (−)
  con  costi contabilizzati sul progetto ("Gestione contabilità progetti", Cliente/fornitore = Fornitore)
  ddt  merce o lavorazioni ricevute e non ancora fatturate: Documento di trasporto, Documenti c/lavoro passivo
  ord  ordini fornitore ancora aperti (F-OA / F-OS / F-OCL)
  int  righe interne ("Gestione contabilità progetti", Cliente/fornitore = Interno): quasi sempre senza costo
  alt  qualunque altro tipo di documento con costo
Ricavi (Tipo di costo "1 - RICAVO", lato cliente): oc = Ordine cliente (valore a contratto nel gestionale),
  fat = fatture al cliente (Nota credito sottratta).
Il nodo "MANCANTE" (o vuoto) diventa "-" = senza nodo.

Sorgenti accettate:
  --pkl  file pickle {hdr: [...], rows: [[...]]} (cache di un'estrazione xlsx)
  --xlsx estrazione Excel del gestionale (foglio Foglio1, intestazione in riga 1)
  --csv  CSV aggregato prodotto dallo script Apps Script `preparaConsuntivo()`:
         colonne Progetto;Nodo;Anno;Stadio;Costo;Righe  (Stadio già classificato: fat/con/ddt/ord/int/alt/ric_oc/ric_fat)

Esempi:
  consuntivo.py --pkl gestionale_full.pkl --state state.json --agg 2026-09-16 --file "Nuovo Foglio 2.xlsx"
  consuntivo.py --xlsx export.xlsx --out cons.json --all
Senza --all vengono tenute solo le commesse presenti in state.json (campo commesse[].code).
"""
import argparse, csv, datetime as dt, json, pickle, re, sys
from collections import defaultdict

CAMPI = ['Cliente/fornitore', 'Tipo di costo', 'Cod. documento', 'Progetto', 'Data consegna', 'Anno',
         'Ricavo', 'Costo', 'TipoDocumento', 'Nodo']
LEGENDA = {
    'fat': 'fatture fornitore (note credito sottratte)',
    'con': 'costi contabilizzati sul progetto (contabilità progetti, fornitore)',
    'ddt': 'consegnato non ancora fatturato (DDT, documenti conto lavoro)',
    'ord': 'ordini fornitore aperti',
    'int': 'righe interne di contabilità progetti (di norma senza costo)',
    'alt': 'altri documenti con costo',
}


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


def anno_di(riga):
    a = riga.get('Anno')
    try:
        a = int(float(a))
        if 1990 < a < 2100:
            return a
    except (TypeError, ValueError):
        pass
    d = riga.get('Data consegna')
    if isinstance(d, (dt.date, dt.datetime)):
        return d.year
    m = re.match(r'(\d{4})', str(d or ''))
    return int(m.group(1)) if m else None


def nodo_di(riga):
    n = str(riga.get('Nodo') or '').strip()
    if not n or n.upper() in ('MANCANTE', '#N/A', 'N/A', 'NONE'):
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
        if doc.startswith('Fattura'):
            return 'ric_fat', r
        if doc == 'Nota credito':
            return 'ric_fat', -abs(r)
        if doc == 'Nota debito':
            return 'ric_fat', abs(r)
        return None
    c = num(riga.get('Costo'))
    if doc == 'Ordine fornitore':
        return 'ord', c
    if doc in ('Documento di trasporto', 'Documenti c/lavoro passivo'):
        return 'ddt', c
    if doc.startswith('Fattura'):
        return 'fat', c
    if doc == 'Nota credito':
        return 'fat', -abs(c)
    if doc == 'Nota debito':
        return 'fat', abs(c)
    if doc == 'Gestione contabilità progetti':
        return ('int' if chi == 'Interno' else 'con'), c
    if doc == 'Ordine cliente':
        return None
    return 'alt', c


def righe_da_pkl(path):
    d = pickle.load(open(path, 'rb'))
    hdr = d['hdr']
    ix = {h: i for i, h in enumerate(hdr)}
    manca = [c for c in CAMPI if c not in ix]
    if manca:
        sys.exit('colonne mancanti nel pickle: %s' % manca)
    for r in d['rows']:
        yield {c: (r[ix[c]] if ix[c] < len(r) else None) for c in CAMPI}


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
    for r in it:
        if r is None or all(v is None for v in r):
            continue
        yield {c: (r[ix[c]] if ix[c] < len(r) else None) for c in CAMPI}


def aggrega(righe):
    """cm -> {'ric': {oc, fat}, 'nd': {nodo: {anno: {stadio: importo, 'n': righe}}}}"""
    cm = {}
    for riga in righe:
        p = str(riga.get('Progetto') or '').strip()
        if not p or p.upper() in ('MANCANTE', '#N/A'):
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
            continue
        nd = c['nd'].setdefault(nodo_di(riga), {})
        cella = nd.setdefault(str(a), {'fat': 0.0, 'con': 0.0, 'ddt': 0.0, 'ord': 0.0, 'int': 0.0, 'alt': 0.0, 'n': 0})
        cella[k] += imp
        cella['n'] += 1
    # arrotonda e togli gli zeri
    for p, c in cm.items():
        c['ric'] = {k: round(v, 2) for k, v in c['ric'].items() if abs(v) > 0.004}
        for nd, anni in c['nd'].items():
            for a, cella in anni.items():
                for k in list(cella.keys()):
                    if k == 'n':
                        continue
                    cella[k] = round(cella[k], 2)
                    if abs(cella[k]) < 0.005:
                        del cella[k]
    return cm


def aggrega_csv(path):
    cm = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f, delimiter=';')
        for r in rd:
            p = (r.get('Progetto') or '').strip()
            k = (r.get('Stadio') or '').strip()
            if not p or not k:
                continue
            c = cm.setdefault(p, {'ric': {'oc': 0.0, 'fat': 0.0}, 'nd': {}})
            imp = num(r.get('Costo'))
            if k.startswith('ric_'):
                c['ric'][k[4:]] = round(c['ric'].get(k[4:], 0.0) + imp, 2)
                continue
            nd = (r.get('Nodo') or '-').strip() or '-'
            if nd.upper() == 'MANCANTE':
                nd = '-'
            a = str(int(float(r.get('Anno') or 0)) or '')
            if not a:
                continue
            cella = c['nd'].setdefault(nd, {}).setdefault(a, {'n': 0})
            cella[k] = round(cella.get(k, 0.0) + imp, 2)
            cella['n'] += int(float(r.get('Righe') or 1))
    return cm


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
    a = ap.parse_args()

    if a.pkl:
        cm = aggrega(righe_da_pkl(a.pkl))
    elif a.xlsx:
        cm = aggrega(righe_da_xlsx(a.xlsx, a.foglio))
    else:
        cm = aggrega_csv(a.csv)

    stato = None
    if a.state:
        stato = json.load(open(a.state, encoding='utf-8'))
        if not a.all:
            codici = {c.get('code') for c in stato.get('commesse', [])}
            cm = {k: v for k, v in cm.items() if k in codici}
    cons = {
        'agg': a.agg, 'file': a.file,
        'fonte': 'estrazione completa del gestionale (tutti i tipi di documento), aggregata per commessa, nodo e anno',
        'gen': dt.datetime.now().isoformat(timespec='seconds'),
        'tipi': LEGENDA,
        'cm': cm,
    }
    if a.out:
        json.dump(cons, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if stato is not None:
        stato['cons'] = cons
        json.dump(stato, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    tot_nodi = sum(len(c['nd']) for c in cm.values())
    print('commesse: %d · nodi: %d · file: %s' % (len(cm), tot_nodi, a.file or '-'))
    for p in sorted(cm)[:60]:
        c = cm[p]
        somme = defaultdict(float)
        for anni in c['nd'].values():
            for cella in anni.values():
                for k, v in cella.items():
                    if k != 'n':
                        somme[k] += v
        print('  %-11s nodi %2d · fat %10.0f · con %9.0f · ddt %9.0f · ord %10.0f · OC %10.0f' % (
            p, len(c['nd']), somme['fat'], somme['con'], somme['ddt'], somme['ord'], c['ric'].get('oc', 0)))


if __name__ == '__main__':
    main()
