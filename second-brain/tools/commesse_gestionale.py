#!/usr/bin/env python3
"""Aggiunge allo stato, come commesse evase, tutti i progetti del gestionale che non ci sono ancora.

Richiesta di Danilo (18/09/2026): «dopo va fatto per tutte le commesse che trovi nei file del gestionale,
queste commesse vanno aggiunte tutte come commesse evase». Le commesse già presenti nello stato non
vengono toccate (né i campi scritti da Danilo). Ogni commessa aggiunta ha:

  code, cliente (ragione sociale più frequente sulle righe cliente, in forma "Titolo", riallineata a un
  cliente già presente nello stato quando coincide), desc (famiglia prodotto dedotta dal prefisso del
  codice, es. SBC → Splash Battle), ev: true, evd (data dell'ultimo documento), gest: {first, last, n,
  fam, tipo}, fonte: 'gestionale', fasi: {}, ref/crit/scad/tg vuoti.
  tipo = 'commessa' per i codici XXX-nn-aa, 'fiera' / 'ricambi' / 'altro' per il resto.

Uso:
  commesse_gestionale.py --pkl gestionale_full.pkl --state state.json [--solo-commesse] [--dry]
  commesse_gestionale.py --csv progetti.csv --state state.json     (CSV Progetto;Cliente;Prima;Ultima;Righe dall'Apps Script)
"""
import argparse, csv, datetime as dt, json, pickle, re, sys
from collections import Counter, defaultdict

FAMIGLIE = {
    'SBC': 'Splash Battle', 'GB': 'Giostra a cavalli', 'FS': 'Flying Swinger', 'PS': 'Autoscontro / vetture',
    'MC': 'Mini coaster', 'FC': 'Family Coaster', 'DR': 'Dark Ride', 'DT': 'Daytona', 'JC': 'Spinning coaster',
    'SM': 'Saltamontes / Kangaroo / Hyper Jump', 'ME': 'Music Express', 'CH': 'Chairoplane', 'BBC': 'Vetture a batteria (bumper)',
    'WC': 'Water Clash', 'WMR': 'Coaster (WMR)', 'T': 'Torre / elicotteri', 'MF': 'Mini Flume', 'SKC': 'Coaster (SKC)',
    'AKS': 'Attrazione AKS', 'A': 'Attrazione (A)', 'CF': 'Attrazione (CF)', 'EK': 'Attrazione (EK)', 'EKM': 'Attrazione (EKM)',
    'GT': 'Attrazione (GT)', 'MA': 'Attrazione (MA)', 'MR': 'Attrazione (MR)', 'RT': 'Attrazione (RT)', 'SC': 'Attrazione (SC)',
    'SB': 'Splash Battle (SB)', 'WH': 'Attrazione (WH)', 'BW': 'Attrazione (BW)', 'IE': 'Attrazione (IE)', 'PR': 'Attrazione (PR)',
    'FE': 'Attrazione (FE)', 'MVX': 'Attrazione (MVX)', 'SRC': 'Attrazione (SRC)', 'PARKACQUAT': 'Parco acquatico',
    'COM': 'Commessa commerciale / componenti', 'RIC': 'Ricambi', 'RICAMBI': 'Ricambi', 'PSALD': 'Saldatura (PSALD)',
}
FIERE = re.compile(r'IAAPA|IAPAA|IAAPI|EAS |EAS$|DEAL|RAAPA|ASIAN|EXPO|ATRAX|FIERA|FIHAV|AMTECH|CHINA ATTRACTION|CAE |SAUDI', re.I)


def titolo(s):
    s = str(s or '').strip()
    if not s:
        return ''
    out = s.lower()
    out = re.sub(r'(^|[\s(/\-.&])([a-zà-ù])', lambda m: m.group(1) + m.group(2).upper(), out)
    for sig in ('Srl', 'Spa', 'Sas', 'Snc', 'Llc', 'Ltd', 'Gmbh', 'Sa', 'Sl', 'Bv', 'B.v.', 'Pvt', 'Inc', 'Co.', 'Jsc', 'Wll', 'Ag', 'Oy', 'Aps', 'Ab', 'Sarl', 'Sasu', 'Pty'):
        out = re.sub(r'\b%s\b' % re.escape(sig), sig.upper(), out)
    return out


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s or '').lower()).strip()


def famiglia(code):
    m = re.match(r'^([A-Z]+)-\d+-[A-Za-z0-9]+$', code)
    if m:
        return m.group(1), 'commessa'
    if FIERE.search(code):
        return code.split()[0], 'fiera'
    if code.upper().startswith(('RIC', 'RICAMBI')):
        return 'RICAMBI', 'ricambi'
    return re.split(r'[-\s]', code)[0], 'altro'


def progetti_da_pkl(path):
    d = pickle.load(open(path, 'rb'))
    ix = {h: i for i, h in enumerate(d['hdr'])}
    P = defaultdict(lambda: {'n': 0, 'cli': Counter(), 'first': None, 'last': None})
    for r in d['rows']:
        p = str(r[ix['Progetto']] or '').strip()
        if not p or p.upper() in ('MANCANTE', '#N/A'):
            continue
        x = P[p]
        x['n'] += 1
        if str(r[ix['Cliente/fornitore']]).strip() == 'Cliente':
            rs = str(r[ix['Ragione sociale']] or '').strip()
            if rs and rs.upper() not in ('#N/A', 'NONE'):
                x['cli'][rs] += 1
        dc = r[ix['Data consegna']]
        if isinstance(dc, (dt.date, dt.datetime)):
            dd = dc.date() if isinstance(dc, dt.datetime) else dc
            x['first'] = dd if x['first'] is None or dd < x['first'] else x['first']
            x['last'] = dd if x['last'] is None or dd > x['last'] else x['last']
    return {p: {'n': x['n'], 'cliente': (x['cli'].most_common(1)[0][0] if x['cli'] else ''),
                'first': x['first'].isoformat() if x['first'] else None, 'last': x['last'].isoformat() if x['last'] else None} for p, x in P.items()}


def progetti_da_csv(path):
    out = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            p = (r.get('Progetto') or '').strip()
            if not p:
                continue
            out[p] = {'n': int(float(r.get('Righe') or 0)), 'cliente': (r.get('Cliente') or '').strip(),
                      'first': (r.get('Prima') or '')[:10] or None, 'last': (r.get('Ultima') or '')[:10] or None}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--pkl')
    src.add_argument('--csv')
    ap.add_argument('--state', required=True)
    ap.add_argument('--solo-commesse', action='store_true', help='aggiungi solo i codici XXX-nn-aa (niente fiere, ricambi, varie)')
    ap.add_argument('--dry', action='store_true', help='non scrivere, stampa solo cosa farebbe')
    ap.add_argument('--oggi', default=dt.date.today().isoformat())
    a = ap.parse_args()
    P = progetti_da_pkl(a.pkl) if a.pkl else progetti_da_csv(a.csv)
    S = json.load(open(a.state, encoding='utf-8'))
    cms = S.setdefault('commesse', [])
    presenti = {str(c.get('code') or '').strip().upper() for c in cms}
    clienti = {}
    for c in cms:
        if c.get('cliente'):
            clienti.setdefault(norm(c['cliente']), c['cliente'])
    oggi = a.oggi
    aggiunte, saltate = [], []
    for code in sorted(P):
        if code.strip().upper() in presenti:
            continue
        fam, tipo = famiglia(code)
        if a.solo_commesse and tipo != 'commessa':
            saltate.append(code)
            continue
        x = P[code]
        cli_raw = x['cliente']
        cli = clienti.get(norm(cli_raw)) or titolo(cli_raw)
        if not cli:
            cli = 'Fiera / evento' if tipo == 'fiera' else 'Interno' if tipo in ('ricambi', 'altro') else ''
        desc = FAMIGLIE.get(fam) or (code if tipo != 'commessa' else 'Commessa ' + fam)
        if tipo == 'fiera':
            desc = 'Fiera: ' + code
        c = {'code': code, 'cliente': cli, 'desc': desc, 'luogo': None, 'paese': None, 'comm': None, 'capo': None, 'ente': None,
             'dc': None, 'de': None, 'ic': None, 'ie': None, 'mail': 0, 'last': None, 'fasi': {}, 'ref': [], 'eco': None, 'crit': [],
             'scad': [], 'tg': [], 'note': 'Commessa chiusa, presa dall\'estrazione del gestionale (%s righe, documenti dal %s al %s).' % (x['n'], x['first'] or '?', x['last'] or '?'),
             'ore': None, 'ev': True, 'evd': x['last'] or oggi, 'fonte': 'gestionale', 'gest': {'first': x['first'], 'last': x['last'], 'n': x['n'], 'fam': fam, 'tipo': tipo, 'agg': oggi}}
        aggiunte.append(c)
        presenti.add(code.upper())
    if a.dry:
        for c in aggiunte:
            print('%-28s %-8s %-40s %s' % (c['code'], c['gest']['tipo'], c['cliente'][:40], c['desc']))
        print('aggiungerei %d commesse (saltate %d); stato ha %d commesse' % (len(aggiunte), len(saltate), len(cms)))
        return
    cms.extend(aggiunte)
    json.dump(S, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('aggiunte %d commesse evase dal gestionale (saltate %d) · totale %d' % (len(aggiunte), len(saltate), len(cms)))


if __name__ == '__main__':
    main()
