#!/usr/bin/env python3
"""Aggiunge allo stato, come commesse evase, tutti i progetti del gestionale che non ci sono ancora.

Richiesta di Danilo (18/09/2026): «dopo va fatto per tutte le commesse che trovi nei file del gestionale,
queste commesse vanno aggiunte tutte come commesse evase». Le commesse già presenti nello stato non
vengono toccate (né i campi scritti da Danilo). Ogni commessa aggiunta ha:

  code (normalizzato come in consuntivo.py: senza spazi ai bordi, maiuscolo, così coincide con la chiave
  di cons.cm), cliente (ragione sociale più frequente sulle righe cliente, in forma "Titolo", riallineata
  a un cliente già presente nello stato quando coincide), desc (famiglia prodotto dedotta dal prefisso del
  codice, es. SBC → Splash Battle), ev: true, evd (data dell'ultimo documento, mai oltre oggi),
  gest: {first, last, n, fam, tipo, agg[, attn]}, fonte: 'gestionale', fasi: {}, ref/crit/scad/tg vuoti.
  tipo = 'commessa' per i codici XXX-nn-aa, 'variante' per XXX-nn-R / -RIP / -PORTE / -VE… (riparazioni,
  revisioni, forniture su una commessa), 'fiera' / 'ricambi' / 'altro' per il resto.
  gest.attn = avviso quando la commessa sembra ancora in corso (documenti datati dopo oggi, oppure ordini
  fornitore aperti e documenti recenti): Danilo decide se riaprirla.

Uso:
  commesse_gestionale.py --pkl gestionale_full.pkl --state state.json [--solo-commesse] [--dry]
  commesse_gestionale.py --csv progetti.csv --state state.json     (CSV Progetto;Cliente;Prima;Ultima;Righe dall'Apps Script)
"""
import argparse, csv, datetime as dt, json, os, pickle, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from consuntivo import norm_code
except ImportError:  # copia della regola di consuntivo.py, se lo script gira da solo
    def norm_code(p):
        p = str(p or '').strip().upper()
        return '' if p in ('MANCANTE', '#N/A', 'N/A', 'NONE') else p

FAMIGLIE = {
    'SBC': 'Splash Battle', 'SB': 'Splash Battle (sigla vecchia SB)', 'GB': 'Giostra a cavalli', 'FS': 'Flying Swinger',
    'PS': 'Autoscontro / vetture', 'BBC': 'Vetture a batteria (bumper)', 'MC': 'Mini coaster', 'FC': 'Family Coaster',
    'JC': 'Spinning coaster', 'SKC': 'Coaster monorotaia (SKC)', 'WMR': 'Double dueling coaster (WMR)', 'DR': 'Dark Ride',
    'DT': 'Daytona', 'SM': 'Saltamontes / Kangaroo / Hyper Jump / Yeti', 'ME': 'Music Express', 'CH': 'Chairoplane',
    'WC': 'Water Clash', 'MF': 'Mini Flume', 'CF': 'Compact Flume Ride', 'T': 'Torre / elicotteri', 'WH': 'Ruota panoramica',
    'GT': 'Tazze (tea cup)', 'RT': 'Rotor', 'EK': 'Eureka', 'EKM': 'Monorotaia Eureka', 'MR': 'Monorotaia', 'MA': 'Eureka idro / sottomarino (MA)',
    'AKS': 'Scivolo Harakiri (AKS)', 'A': 'Avio: farfalla / pterodattilo (A)', 'SC': 'Safari car (jeep)', 'BW': 'Bus Wash / Crazy Barn',
    'RR': 'Supporti regolabili (RR)', 'IE': 'Lavorazione (IE)', 'PR': 'Commessa PR', 'FE': 'Commessa FE', 'MVX': 'Commessa MVX',
    'SRC': 'Commessa SRC', 'PARKACQUAT': 'Parco acquatico', 'COM': 'Fornitura commerciale (componenti, piccole attrazioni)',
    'RIC': 'Ricambi', 'RICAMBI': 'Ricambi', 'PSALD': 'Saldatura (PSALD)', 'SP': 'Commessa SP',
}
SUFFISSI = {'R': 'riparazione / revisione', 'RIP': 'riparazione', 'PORTE': 'porte', 'VE': 'fornitura VE', 'SDOG': 'sdoganamento', 'PROG': 'progetto'}
FIERE = re.compile(r'IAAPA|IAPAA|IAAPI|EAS |EAS$|DEAL|RAAPA|ASIAN|EXPO|ATRAX|FIERA|FIHAV|AMTECH|CHINA ATTRACTION|CAE |SAUDI|ESPOSIZIONE', re.I)

# ragioni sociali: sigle societarie in forma "Titolo" (come le scrive Danilo nello stato: Srl, Pty Ltd, Inc),
# alcune con grafia propria; acronimi che restano maiuscoli; parole di legame minuscole.
SIGLE = {'SRL', 'SRLS', 'SPA', 'SAS', 'SASU', 'SNC', 'SARL', 'SPRL', 'EURL', 'LTD', 'LTDA', 'INC', 'CO', 'SAU', 'PVT', 'PTY', 'SHPK',
         'DOO', 'SRO', 'BHD', 'SDN', 'CORP'}                      # in forma Titolo (Srl, Spa, Ltd, Inc…), come le scrive Danilo
SPECIALI = {'GMBH': 'GmbH', 'JSC': 'JSC', 'LLC': 'LLC', 'WLL': 'WLL', 'APS': 'ApS', 'PLC': 'PLC', 'KG': 'KG', 'CV': 'CV', 'OY': 'Oy',
            'SP': 'Sp', 'SA': 'SA', 'SL': 'SL', 'BV': 'BV', 'AB': 'AB', 'AG': 'AG', 'NV': 'NV', 'AS': 'AS'}
ACRONIMI = {'UAB', 'OOO', 'KCA', 'AGC', 'BBI', 'OCT', 'PT', 'LCC', 'LG', 'NW', 'FC', 'GSP', 'MSC', 'DB', 'DG', 'MPS', 'PFV', 'SVK', 'MKC', 'MVA', 'IE', 'DCS', 'CNH', 'LPM', 'BBC'}
MINUSCOLE = {'di', 'da', 'de', 'del', 'della', 'dei', 'degli', 'du', 'des', 'le', 'la', 'les', 'of', 'and', 'for', 'e', 'y', 'the', 'und', 've', 'z', 'a', 'by'}
TOKEN_SPECIALI = {'O.O.': 'o.o.'}                                   # Sp. z o.o.


def titolo(s):
    """Ragione sociale in forma "Titolo": Srl/Spa/Ltd/Inc come le scrive Danilo, GmbH/JSC/LLC/UAB… con la loro grafia,
    "di/de/and/of" minuscoli quando sono parole intere (non in S.P.A.), maiuscola dopo apostrofo e virgolette
    (D'Algerie, "Midika") ma non in Moser's; asterischi iniziali via, spazi doppi e " ," sistemati."""
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    s = re.sub(r'^[\*\s]+', '', s)
    s = re.sub(r'\s*,\s*', ', ', s).strip()
    if not s:
        return ''

    def run(m, prima):
        r = m.group(0)
        u = r.upper()
        pre = m.string[m.start() - 1:m.start()] if m.start() else ''
        post = m.string[m.end():m.end() + 1]
        intera = pre in ('', ' ') and post in ('', ' ', ',')
        if pre in ("'", '’') and len(r) == 1:      # Moser's, Canada's
            return r.lower()
        if u in SPECIALI:
            return SPECIALI[u]
        if u in SIGLE:
            return u.capitalize()
        if u in ACRONIMI or (2 <= len(u) <= 4 and not re.search(r'[AEIOUY]', u)):
            return u
        if not prima and intera and r.lower() in MINUSCOLE:
            return r.lower()
        return r[:1].upper() + r[1:].lower()

    out = []
    for i, w in enumerate(s.split(' ')):
        if w.upper() in TOKEN_SPECIALI:
            out.append(TOKEN_SPECIALI[w.upper()])
            continue
        out.append(re.sub(r'[A-Za-zÀ-ÿ]+', lambda m: run(m, i == 0), w))
    return ' '.join(out)


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s or '').lower()).strip()


def famiglia(code):
    m = re.match(r'^([A-Z]+)-\d+-([A-Z0-9]+)$', code)
    if m:
        return m.group(1), ('commessa' if re.match(r'^\d{2}$', m.group(2)) else 'variante')
    if FIERE.search(code):
        return code.split()[0], 'fiera'
    if code.startswith(('RIC', 'RICAMBI')):
        return 'RICAMBI', 'ricambi'
    return re.split(r'[-\s]', code)[0], 'altro'


def progetti_da_pkl(path):
    d = pickle.load(open(path, 'rb'))
    ix = {h: i for i, h in enumerate(d['hdr'])}
    mancano = [c for c in ('Progetto', 'Cliente/fornitore', 'Ragione sociale', 'Data consegna') if c not in ix]
    if mancano:
        sys.exit('colonne mancanti nell\'estrazione: ' + ', '.join(mancano))
    P = defaultdict(lambda: {'n': 0, 'cli': Counter(), 'first': None, 'last': None, 'grafie': Counter()})
    for r in d['rows']:
        p = norm_code(r[ix['Progetto']])
        if not p:
            continue
        x = P[p]
        x['n'] += 1
        x['grafie'][str(r[ix['Progetto']]).strip()] += 1
        if str(r[ix['Cliente/fornitore']]).strip() == 'Cliente':
            rs = str(r[ix['Ragione sociale']] or '').strip()
            if rs and rs.upper() not in ('#N/A', 'NONE'):
                x['cli'][rs] += 1
        dc = r[ix['Data consegna']]
        if isinstance(dc, (dt.date, dt.datetime)):
            dd = dc.date() if isinstance(dc, dt.datetime) else dc
            x['first'] = dd if x['first'] is None or dd < x['first'] else x['first']
            x['last'] = dd if x['last'] is None or dd > x['last'] else x['last']
    for p, x in P.items():
        if len(x['grafie']) > 1:
            print('unite le grafie %s -> %s' % (sorted(x['grafie']), p), file=sys.stderr)
    return {p: {'n': x['n'], 'cliente': (x['cli'].most_common(1)[0][0] if x['cli'] else ''),
                'first': x['first'].isoformat() if x['first'] else None, 'last': x['last'].isoformat() if x['last'] else None} for p, x in P.items()}


def progetti_da_csv(path):
    out = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f, delimiter=';'):
            p = norm_code(r.get('Progetto'))
            if not p:
                continue
            x = out.setdefault(p, {'n': 0, 'cliente': '', 'first': None, 'last': None})
            x['n'] += int(float(r.get('Righe') or 0))
            x['cliente'] = x['cliente'] or (r.get('Cliente') or '').strip()
            pr, ul = (r.get('Prima') or '')[:10] or None, (r.get('Ultima') or '')[:10] or None
            x['first'] = min(filter(None, [x['first'], pr]), default=None)
            x['last'] = max(filter(None, [x['last'], ul]), default=None)
    return out


def ordini_aperti(cons, code):
    """Somma degli ordini fornitore aperti (stadio ord) nel consuntivo dello stato, se c'è."""
    c = (cons or {}).get('cm', {}).get(code) or {}
    return sum(cella.get('ord', 0) for anni in c.get('nd', {}).values() for cella in anni.values())


def costi_totali(cons, code):
    c = (cons or {}).get('cm', {}).get(code) or {}
    return sum(cella.get(k, 0) for anni in c.get('nd', {}).values() for cella in anni.values() for k in ('fat', 'con', 'ddt', 'ord', 'alt'))


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
    presenti = {norm_code(c.get('code')) for c in cms}
    clienti = {}
    for c in cms:
        if c.get('cliente'):
            clienti.setdefault(norm(c['cliente']), c['cliente'])
    oggi = a.oggi
    recente = (dt.date.fromisoformat(oggi) - dt.timedelta(days=120)).isoformat()
    aggiunte, saltate, avvisi = [], [], []
    for code in sorted(P):
        if code in presenti:
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
        desc = FAMIGLIE.get(fam) or (code if tipo not in ('commessa', 'variante') else 'Commessa ' + fam)
        if tipo == 'variante':
            suf = code.rsplit('-', 1)[-1]
            desc += ' · ' + SUFFISSI.get(suf, suf)
        if tipo == 'fiera':
            desc = 'Fiera: ' + code
        last = x['last']
        attn = None
        if last and last > oggi:
            attn = 'documenti datati dopo oggi (fino al %s): forse ancora in corso' % last
        elif tipo in ('commessa', 'variante') and last and last >= recente:
            # ordini aperti che pesano davvero (almeno il 10 % dei costi e 5.000 €): un residuo piccolo è normale in una commessa chiusa
            oa, ct = ordini_aperti(S.get('cons'), code), costi_totali(S.get('cons'), code)
            if oa >= 5000 and ct > 0 and oa / ct >= 0.10:
                attn = 'ordini fornitore ancora aperti per %.0f € (%.0f%% dei costi) e documenti recenti (%s): forse ancora in corso' % (oa, 100 * oa / ct, last)
        gest = {'first': x['first'], 'last': last, 'n': x['n'], 'fam': fam, 'tipo': tipo, 'agg': oggi}
        if attn:
            gest['attn'] = attn
            avvisi.append((code, attn))
        c = {'code': code, 'cliente': cli, 'desc': desc, 'luogo': None, 'paese': None, 'comm': None, 'capo': None, 'ente': None,
             'dc': None, 'de': None, 'ic': None, 'ie': None, 'mail': 0, 'last': None, 'fasi': {}, 'ref': [], 'eco': None, 'crit': [],
             'scad': [], 'tg': [], 'note': 'Commessa chiusa, presa dall\'estrazione del gestionale (%s righe, documenti dal %s al %s).' % (x['n'], x['first'] or '?', last or '?')
             + (' Attenzione: ' + attn + '.' if attn else ''),
             'ore': None, 'ev': True, 'evd': min(last or oggi, oggi), 'fonte': 'gestionale', 'gest': gest}
        aggiunte.append(c)
        presenti.add(code)
    if a.dry:
        for c in aggiunte:
            print('%-28s %-8s %-40s %s' % (c['code'], c['gest']['tipo'], c['cliente'][:40], c['desc']))
        print('aggiungerei %d commesse (saltate %d); stato ha %d commesse' % (len(aggiunte), len(saltate), len(cms)))
    else:
        cms.extend(aggiunte)
        json.dump(S, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('aggiunte %d commesse evase dal gestionale (saltate %d) · totale %d' % (len(aggiunte), len(saltate), len(cms)))
    if avvisi:
        print('da verificare con Danilo (importate come evase, ma sembrano ancora in corso):')
        for code, attn in avvisi:
            print('  %-26s %s' % (code, attn))


if __name__ == '__main__':
    main()
