#!/usr/bin/env python3
"""Budget e consuntivo per nodo → cartella Excel (.xlsx) per la scheda Commesse → Budget.

Specchio in Python del modello della pagina (funzione bdgModello del blocco R24/R25 in app.js): stessa
aritmetica, così il file Excel e la scheda mostrano gli stessi numeri. Le colonne derivate
(budget ore, budget totale, impegnato, scostamento, utile, prezzo di vendita) sono formule
Excel che leggono il foglio Parametri: Danilo può ritoccare budget, tariffe, margine e indici nel
file e vedere il ricalcolo.

R25 (18/09/2026, sera): per una commessa in corso senza budget salvato, nodi e importi vengono proposti
dalle commesse chiuse della stessa famiglia (prefisso del codice: SBC, GB, FS…) come media dei costi
consuntivi per nodo indicizzati all'anno corrente e arrotondati a 100 € (al massimo 3 commesse, le più
recenti). L'utile è «a budget» (prezzo − budget) per le commesse in corso e «consuntivo» (prezzo − costi
consuntivi: impegnato + ore) per le evase. Le ore a budget possono essere anche per l'intera commessa
(c.bdg.hu / c.bdg.ho) e si sommano a quelle per nodo.

  budget_xlsx.py --state state.json --cm SBC-15-26 --out export/          → export/budget-SBC-15-26.xlsx
  budget_xlsx.py --state state.json --all --out export/                   → export/budget-tutte.xlsx (Riepilogo + un foglio per commessa in corso)
  budget_xlsx.py --state state.json --cm A --cm B --out file.xlsx
  budget_xlsx.py --state state.json --cm SBC-15-26 --json                 → modello in JSON (per i controlli incrociati con la pagina)
  budget_xlsx.py --state state.json --cm SBC-15-26 --rif SBC-14-24 …      → proposta da una sola commessa di riferimento (come il selettore in pagina)

Fogli: Riepilogo (se più commesse), un foglio per commessa (nodi, ore interne, utile), Parametri.
"""
import argparse, datetime as dt, json, math, os, re, sys

IDX_DEFAULT = {"2013": 1.2, "2014": 0.2, "2015": 0.1, "2016": -0.1, "2017": 1.2, "2018": 1.2, "2019": 0.6,
               "2020": -0.2, "2021": 1.9, "2022": 8.1, "2023": 5.7, "2024": 1.0, "2025": 1.7, "2026": 1.8, "2027": 1.9}
STADI = ('fat', 'con', 'ddt', 'ord', 'alt')


def num(x, d=0.0):
    try:
        v = float(x)
        return d if v != v else v
    except (TypeError, ValueError):
        return d


def jsround(x):
    """Math.round di JavaScript (metà verso +∞), non l'arrotondamento bancario di Python."""
    return int(math.floor(x + 0.5))


def js_keys(d):
    """Object.keys: le chiavi 'intere' prima, in ordine numerico, poi le altre in ordine di inserimento."""
    ks = list((d or {}).keys())
    ints = [k for k in ks if re.fullmatch(r'0|[1-9]\d*', str(k))]
    return sorted(ints, key=int) + [k for k in ks if k not in ints]


def bcfg(S):
    c = dict(S.get('cfg') or {})
    idx = c.get('idx') if isinstance(c.get('idx'), dict) else IDX_DEFAULT
    c['idx'] = {str(k): num(v) for k, v in idx.items()}
    c['marg'] = 30.0 if c.get('marg') is None or num(c.get('marg'), None) is None else num(c['marg'])
    c['margTipo'] = 'ricarico' if c.get('margTipo') == 'ricarico' else 'prezzo'
    c['tUff'] = num(c.get('tUff'))
    c['tOff'] = num(c.get('tOff'))
    return c


def fattore_idx(cf, da, a):
    f = 1.0
    for y in range(int(da) + 1, int(a) + 1):
        f *= 1 + cf['idx'].get(str(y), 0.0) / 100
    return f


def fattore_prezzo(cf):
    m = cf['marg'] / 100
    if cf['margTipo'] == 'ricarico':
        return 1 + m
    return 1.0 if m >= 1 else 1 / (1 - m)


def norm_nodo(s):
    s = str(s or '').upper()
    for acc, rep in (('ÀÁÂÃÄ', 'A'), ('ÈÉÊË', 'E'), ('ÌÍÎÏ', 'I'), ('ÒÓÔÕÖ', 'O'), ('ÙÚÛÜ', 'U')):
        for ch in acc:
            s = s.replace(ch, rep)
    return re.sub(r'[^A-Z0-9]+', ' ', s).strip()


def titolo(s):
    return re.sub(r'(^|[\s(/-])([a-zà-ù])', lambda m: m.group(1) + m.group(2).upper(), str(s or '').lower())


def nodo_label(nd):
    return 'Senza nodo' if nd == '-' else titolo(nd)


def cons_cm(S, code):
    return ((S.get('cons') or {}).get('cm') or {}).get(code)


def cons_nodi(S, code):
    c = cons_cm(S, code)
    return js_keys((c or {}).get('nd'))


def fam_cm(code):
    m = re.match(r'^([A-Za-z]+)-', str(code or ''))
    return m.group(1).upper() if m else None


def anno_cm(S, c):
    m = re.match(r'^[A-Za-z]+-\d+-(\d{2})$', str(c.get('code') or ''))
    if m:
        return 2000 + int(m.group(1))
    cc, y = cons_cm(S, c.get('code')), 0
    for nd, anni in ((cc or {}).get('nd') or {}).items():
        for a in (anni or {}):
            if num(a) > y:
                y = int(num(a))
    return y or None


def costi_idx_nodi(S, cf, code, Y):
    """Costi consuntivi di una commessa per nodo (nome del gestionale), indicizzati all'anno Y."""
    cc, out, tot = cons_cm(S, code), {}, 0.0
    if not cc:
        return {'nodi': out, 'tot': 0.0}
    nd_all = cc.get('nd') or {}
    for nd in js_keys(nd_all):
        s = 0.0
        for y in js_keys(nd_all[nd]):
            a = nd_all[nd][y] or {}
            v = sum(num(a.get(k)) for k in STADI)
            s += v * fattore_idx(cf, int(num(y)), Y)
        if s:
            out[nd] = s
            tot += s
    return {'nodi': out, 'tot': tot}


def bdg_simili(S, cf, c, Y):
    """Commesse chiuse della stessa famiglia con costi nel gestionale, le più recenti prima (max 3)."""
    fam = fam_cm(c.get('code'))
    if not fam:
        return []
    out = []
    for x in S.get('commesse') or []:
        if x.get('code') == c.get('code') or not x.get('ev') or fam_cm(x.get('code')) != fam:
            continue
        k = costi_idx_nodi(S, cf, x.get('code'), Y)
        if k['tot'] > 0:
            out.append({'c': x, 'code': x.get('code'), 'tot': k['tot'], 'nodi': k['nodi'], 'anno': anno_cm(S, x)})
    out.sort(key=lambda s: (-(s['anno'] or 0), -s['tot']))
    return out[:3]


def proposta(S, cf, c, Y, rif_mode=None):
    """Nodi e budget proposti: nodi dal contratto (c.nodi), dal gestionale della commessa e dalle commesse
    simili chiuse; importi = media dei costi consuntivi per nodo delle simili, indicizzati all'anno corrente
    (oppure una sola commessa di riferimento: rif_mode = codice). Per una commessa evasa non si propone
    nessun budget: contano i costi consuntivi."""
    out, seen = [], set()
    simili = [] if c.get('ev') else bdg_simili(S, cf, c, Y)
    mode = rif_mode or 'media'
    rif = simili if mode == 'media' else [s for s in simili if s['code'] == mode]
    if not rif:
        rif, mode = simili, 'media'

    def trova(nome):
        k = norm_nodo(nome)
        if not k:
            return None
        for o in out:
            if norm_nodo(o['n']) == k or k in [norm_nodo(a) for a in o['al']]:
                return o
        for o in out:
            ko = norm_nodo(o['n'])
            if len(ko) >= 4 and len(k) >= 4 and (ko.startswith(k) or k.startswith(ko)):
                return o
        return None

    def agg(nome, d='', al=None):
        k = norm_nodo(nome)
        if not k or k in seen:
            return None
        seen.add(k)
        o = {'id': 'b%d' % (len(out) + 1), 'n': nome, 'd': d or '', 'al': list(al or []), 'ext': None, 'hu': None, 'ho': None, 'note': '', 'prop': []}
        out.append(o)
        return o

    def agg_gest(nd, val):
        if nd == '-':
            if not (val is not None and val > 0):
                return
            v = trova('Varie')
            if not v:
                v = agg('Varie', 'costi registrati nel gestionale senza nodo', ['-'])
            if '-' not in v['al']:
                v['al'].append('-')
            v['prop'].append(val)
            return
        hit = trova(nd)
        if hit:
            if norm_nodo(hit['n']) != norm_nodo(nd) and nd not in hit['al']:
                hit['al'].append(nd)
        else:
            hit = agg(titolo(nd), '', [])
        if hit is not None and val is not None:
            hit['prop'].append(val)

    for n in (c.get('nodi') or []):
        agg(n.get('n'), n.get('d'))
    for nd in cons_nodi(S, c.get('code')):
        if nd != '-':
            agg_gest(nd, None)
    for s in rif:
        for nd in js_keys(s['nodi']):
            agg_gest(nd, s['nodi'][nd])
    tot = 0
    for o in out:
        if o['prop']:
            o['ext'] = jsround(sum(o['prop']) / len(o['prop']) / 100) * 100
            tot += o['ext']
        del o['prop']
    # ore: media delle ore consuntive delle commesse di riferimento (se il file ore le ha)
    hu = ho = None
    nO, sU, sO = 0, 0.0, 0.0
    for s in rif:
        o = s['c'].get('ore') or {}
        if o.get('uff') is not None or o.get('off') is not None:
            nO += 1
            sU += num(o.get('uff'))
            sO += num(o.get('off'))
    if nO:
        hu, ho = jsround(sU / nO), jsround(sO / nO)
    return {'nodi': out, 'rif': rif, 'simili': simili, 'mode': mode, 'tot': tot, 'hu': hu, 'ho': ho}


def mappa(S, c, nodi):
    m = {}
    for nd in cons_nodi(S, c['code']):
        k = norm_nodo(nd)
        for b in nodi:
            if nd in m:
                break
            if norm_nodo(b.get('n')) == k or k in [norm_nodo(a) for a in (b.get('al') or [])]:
                m[nd] = b['id']
    return m


def vuota(id_, n):
    r = {'id': id_, 'n': n, 'd': '', 'al': [], 'gest': [], 'ext': 0.0, 'hu': 0.0, 'ho': 0.0, 'note': '', 'anni': {}, 'extra': False, 'bOre': 0.0, 'bTot': 0.0}
    for k in STADI:
        r[k] = 0.0
    return r


def modello(S, c, Y, rif_mode=None):
    cf = bcfg(S)
    tU, tO = cf['tUff'], cf['tOff']
    bdg = c.get('bdg') or {}
    nodi = bdg.get('nodi') if bdg.get('nodi') else None
    prop, P = nodi is None, None
    if prop:
        P = proposta(S, cf, c, Y, rif_mode)
        nodi = P['nodi']
    h_cm = {'u': (P['hu'] or 0) if P else num(bdg.get('hu')), 'o': (P['ho'] or 0) if P else num(bdg.get('ho'))}
    cc = cons_cm(S, c['code']) or {'nd': {}, 'ric': {}}
    mp = mappa(S, c, nodi)
    righe = []
    for b in nodi:
        r = vuota(b['id'], b.get('n') or '')
        r['d'], r['al'], r['note'] = b.get('d') or '', list(b.get('al') or []), b.get('note') or ''
        r['ext'], r['hu'], r['ho'] = num(b.get('ext')), num(b.get('hu')), num(b.get('ho'))
        righe.append(r)
    by_id = {r['id']: r for r in righe}
    extra = []
    nd_all = cc.get('nd') or {}
    for nd in js_keys(nd_all):
        anni = nd_all[nd]
        r = by_id.get(mp.get(nd))
        if r is None:
            r = vuota('g:' + nd, nodo_label(nd))
            r['extra'] = True
            extra.append(r)
            by_id[r['id']] = r
        r['gest'].append(nd)
        for y in js_keys(anni):
            a, imp = anni[y] or {}, 0.0
            for k in STADI:
                v = num(a.get(k))
                r[k] += v
                imp += v
            r['anni'][y] = r['anni'].get(y, 0.0) + imp
    extra.sort(key=lambda r: (r['id'] == 'g:-', -(r['fat'] + r['con'] + r['ddt'] + r['ord'] + r['alt'])))
    tutte = righe + extra
    tot = vuota('tot', 'Totale')
    for k in ('sost', 'imp', 'idxY', 'idxY1', 'przY', 'przY1'):
        tot[k] = 0.0
    fp = fattore_prezzo(cf)
    for r in tutte:
        r['sost'] = r['fat'] + r['con'] + r['ddt'] + r['alt']
        r['imp'] = r['sost'] + r['ord']
        r['bOre'] = r['hu'] * tU + r['ho'] * tO
        r['bTot'] = r['ext'] + r['bOre']
        r['sc'] = r['imp'] - r['ext']
        r['pct'] = r['imp'] / r['ext'] if r['ext'] > 0 else None
        iy = 0.0
        for y in js_keys(r['anni']):
            iy += r['anni'][y] * fattore_idx(cf, int(num(y)), Y)
        r['idxY'], r['idxY1'] = iy, iy * fattore_idx(cf, Y, Y + 1)
        r['przY'], r['przY1'] = r['idxY'] * fp, r['idxY1'] * fp
        if r['ext'] > 0:
            r['stato'] = 'bad' if r['pct'] > 1 else 'warn' if r['pct'] > 0.9 else 'ok'
        else:
            r['stato'] = ('extra' if r['extra'] else 'nob') if r['imp'] else 'vuoto'
        for k in ('ext', 'hu', 'ho', 'fat', 'con', 'ddt', 'ord', 'alt', 'sost', 'imp', 'bOre', 'bTot', 'idxY', 'idxY1', 'przY', 'przY1'):
            tot[k] += r[k]
    tot['sc'] = tot['imp'] - tot['ext']
    tot['pct'] = tot['imp'] / tot['ext'] if tot['ext'] > 0 else None
    tot['stato'] = ('bad' if tot['pct'] > 1 else 'warn' if tot['pct'] > 0.9 else 'ok') if tot['ext'] > 0 else 'nob'
    ore = c.get('ore') or {}
    cU, cO = num(ore.get('uff')), num(ore.get('off'))
    ore_cons = cU * tU + cO * tO
    bU, bO = tot['hu'] + h_cm['u'], tot['ho'] + h_cm['o']
    ore_bdg = bU * tU + bO * tO
    eco = c.get('eco') or {}
    valore = num(eco.get('valore')) if eco.get('valore') else None
    oc = num((cc.get('ric') or {}).get('oc')) if (cc.get('ric') or {}).get('oc') else None
    prezzo = valore if valore is not None else oc
    fonte = 'contratto' if valore is not None else ('ordine cliente nel gestionale' if oc is not None else None)
    ha_budget = tot['ext'] > 0 or bU > 0 or bO > 0
    M = {'c': c, 'nodi': nodi, 'proposta': prop, 'conf': bool(bdg.get('conf')), 'righe': tutte, 'tot': tot, 'Y': Y, 'tU': tU, 'tO': tO,
         'rif': P['rif'] if P else [], 'simili': P['simili'] if P else [], 'rifMode': P['mode'] if P else None, 'propTot': P['tot'] if P else 0,
         'ore': {'bU': bU, 'bO': bO, 'cU': cU, 'cO': cO, 'bEur': ore_bdg, 'cEur': ore_cons, 'hCm': h_cm},
         'prezzo': prezzo, 'prezzoFonte': fonte, 'oc': oc, 'valore': valore, 'haBudget': ha_budget, 'chiusa': bool(c.get('ev')),
         'budgetTot': tot['ext'] + ore_bdg, 'costoOggi': tot['imp'] + ore_cons}
    # utile: a budget per le commesse in corso, consuntivo per le evase (R25)
    M['utileB'] = prezzo - M['budgetTot'] if prezzo is not None and ha_budget else None
    M['utileO'] = prezzo - M['costoOggi'] if prezzo is not None else None
    if c.get('ev'):
        M['utile'] = M['utileO']
        M['utileTipo'] = 'consuntivo' if M['utile'] is not None else None
    else:
        M['utile'] = M['utileB']
        M['utileTipo'] = ('budget proposto' if prop else 'budget') if M['utile'] is not None else None
    M['marg'] = M['utile'] / prezzo if M['utile'] is not None and prezzo else None
    M['margB'] = M['utileB'] / prezzo if M['utileB'] is not None and prezzo else None
    M['margO'] = M['utileO'] / prezzo if M['utileO'] is not None and prezzo else None
    return M


def stato_nodi(M):
    return 'evasa' if M['chiusa'] else 'proposti' if M['proposta'] else 'confermati' if M['conf'] else 'da confermare'


def rif_txt(M):
    """Descrizione della proposta: da quali commesse e come."""
    if not (M['proposta'] and M['rif']):
        return ''
    return ('media dei costi consuntivi per nodo di ' if len(M['rif']) > 1 else 'costi consuntivi per nodo di ') \
        + ', '.join(s['code'] + (' (%d)' % s['anno'] if s['anno'] else '') for s in M['rif']) + ', indicizzati al %d' % M['Y']


# ---------------------------------------------------------------- Excel
def _stili():
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    thin = Side(style='thin', color='D0D5DD')
    return {
        'h1': Font(name='Calibri', size=14, bold=True), 'h2': Font(name='Calibri', size=10, color='667085'),
        'th': Font(name='Calibri', size=10, bold=True, color='FFFFFF'), 'thfill': PatternFill('solid', fgColor='1F2A44'),
        'tot': Font(name='Calibri', size=10, bold=True), 'totfill': PatternFill('solid', fgColor='EEF2F7'),
        'extra': Font(name='Calibri', size=10, italic=True, color='7A4B00'), 'bold': Font(name='Calibri', size=10, bold=True),
        'prop': Font(name='Calibri', size=10, italic=True, color='1F4E9C'),
        'norm': Font(name='Calibri', size=10), 'sub': Font(name='Calibri', size=9, color='667085'),
        'in': PatternFill('solid', fgColor='FFF8E1'), 'border': Border(top=thin, bottom=thin, left=thin, right=thin),
        'right': Alignment(horizontal='right'), 'center': Alignment(horizontal='center'), 'wrap': Alignment(wrap_text=True, vertical='top'),
        'bad': PatternFill('solid', fgColor='FDE2E1'), 'warn': PatternFill('solid', fgColor='FFF1D6'), 'ok': PatternFill('solid', fgColor='E3F5E9'),
    }


EUR = '#,##0 "€";[Red]-#,##0 "€";"–"'
ORE = '#,##0.0 "h";-#,##0.0 "h";"–"'
PCT = '+0%;-0%;0%'
PCT0 = '0%'


def nome_foglio(code, usati):
    base = re.sub(r'[\[\]\*\?/\\:]', '_', str(code))[:28] or 'commessa'
    n, i = base, 2
    while n in usati:
        n = '%s (%d)' % (base[:25], i)
        i += 1
    usati.add(n)
    return n


def scrivi_parametri(wb, cf, Y, S):
    st = _stili()
    ws = wb.create_sheet('Parametri')
    ws['A1'], ws['A1'].font = 'Parametri del calcolo', st['h1']
    ws['A2'], ws['A2'].font = 'Tariffe, margine e indici come nella pagina (Denaro → Tariffe, Commesse → Budget). Le celle gialle si possono cambiare: i fogli ricalcolano.', st['h2']
    righe = [('Tariffa ufficio €/h', cf['tUff'], '#,##0.00 "€"'), ('Tariffa produzione €/h', cf['tOff'], '#,##0.00 "€"'),
             ('Margine %', cf['marg'], '0.0'), ('Tipo margine (prezzo / ricarico)', cf['margTipo'], '@'), ('Anno corrente', Y, '0')]
    for i, (k, v, f) in enumerate(righe, start=4):
        ws.cell(i, 1, k).font = st['norm']
        c = ws.cell(i, 2, v)
        c.number_format, c.fill, c.border, c.font = f, st['in'], st['border'], st['norm']
    ws.cell(9, 1, 'Fattore prezzo (costo → prezzo di vendita)').font = st['norm']
    c = ws.cell(9, 2, '=IF(B7="ricarico",1+B6/100,IF(B6>=100,1,1/(1-B6/100)))')
    c.number_format, c.font = '0.0000', st['bold']
    ws.cell(10, 1, 'margine sul prezzo: prezzo = costo ÷ (1 − margine); ricarico: prezzo = costo × (1 + margine)').font = st['sub']
    ws.cell(12, 1, 'Anno').font = st['th']; ws.cell(12, 1).fill = st['thfill']
    ws.cell(12, 2, 'Indice %').font = st['th']; ws.cell(12, 2).fill = st['thfill']
    ws.cell(12, 3, 'Fattore fino all\'anno corrente').font = st['th']; ws.cell(12, 3).fill = st['thfill']
    anni = sorted(set(list(cf['idx'].keys()) + [str(Y), str(Y + 1)]), key=int)
    r0 = 13
    for i, y in enumerate(anni):
        r = r0 + i
        ws.cell(r, 1, int(y)).number_format = '0'
        c = ws.cell(r, 2, cf['idx'].get(y, 0.0))
        c.number_format, c.fill, c.border = '0.0', st['in'], st['border']
        # fattore da questo anno all'anno corrente: prodotto (1+idx) per gli anni successivi fino a Y
        ws.cell(r, 3, '=IF(A%d>=$B$8,1,PRODUCT(1+IF((A$%d:A$%d>A%d)*(A$%d:A$%d<=$B$8),B$%d:B$%d,0)/100))' % (r, r0, r0 + len(anni) - 1, r, r0, r0 + len(anni) - 1, r0, r0 + len(anni) - 1)).number_format = '0.0000'
    ws.cell(r0 + len(anni) + 1, 1, 'Fonte indici: ISTAT NIC medie annue 2013-2024; 2025-2027 stime, modificabili.').font = st['sub']
    ws.column_dimensions['A'].width = 44; ws.column_dimensions['B'].width = 14; ws.column_dimensions['C'].width = 26
    cons = S.get('cons') or {}
    ws.cell(r0 + len(anni) + 3, 1, 'Consuntivo: %s%s' % (cons.get('agg') or 'non caricato', (' · ' + cons['file']) if cons.get('file') else '')).font = st['sub']
    return {'tUff': "Parametri!$B$4", 'tOff': "Parametri!$B$5", 'fp': "Parametri!$B$9", 'anni': (r0, r0 + len(anni) - 1)}


def scrivi_commessa(wb, S, M, P, usati):
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.utils import get_column_letter as L
    st = _stili()
    c, Y = M['c'], M['Y']
    ws = wb.create_sheet(nome_foglio(c['code'], usati))
    ws['A1'] = '%s · %s%s%s' % (c['code'], c.get('cliente') or '', (' · ' + c['desc']) if c.get('desc') else '', ' · commessa evasa' if M['chiusa'] else '')
    ws['A1'].font = st['h1']
    bdg = c.get('bdg') or {}
    cons = S.get('cons') or {}
    prop_rif = M['proposta'] and bool(M['rif'])
    if M['chiusa']:
        testa = 'Commessa evasa: contano i costi consuntivi (utile consuntivo = prezzo − impegnato − ore)' \
            + (' · budget salvato il %s, resta solo come memoria' % bdg['agg'] if bdg.get('agg') else ' · nessun budget salvato')
    elif prop_rif:
        testa = 'BUDGET PROPOSTO, DA CONFERMARE: %s' % rif_txt(M) \
            + ((' · ore proposte %s h ufficio, %s h produzione (media delle stesse commesse)' % (M['ore']['hCm']['u'], M['ore']['hCm']['o'])) if M['ore']['hCm']['u'] or M['ore']['hCm']['o'] else '')
    elif M['proposta']:
        testa = 'Nodi proposti (non ancora confermati) · nessuna commessa simile chiusa con costi nel gestionale%s: il budget per nodo va inserito' % ((' (famiglia %s)' % fam_cm(c['code'])) if fam_cm(c['code']) else '')
    else:
        testa = 'Budget: %s%s%s' % ('nodi confermati' if M['conf'] else 'nodi da confermare', (' · salvato il ' + bdg['agg']) if bdg.get('agg') else '', (' · ' + bdg['fonte']) if bdg.get('fonte') else '')
    ws['A2'] = '%s · consuntivo dall\'estrazione del %s · generato il %s' % (testa, cons.get('agg') or '—', dt.date.today().isoformat())
    ws['A2'].font = st['h2']

    # ---- tabella nodi
    H = ['Nodo', 'Nel gestionale', 'Budget proposto' if prop_rif else 'Budget esterno', 'Ore ufficio', 'Ore produzione', 'Budget ore €', 'Budget totale', 'Fatturato', 'Consegnato', 'Ordinato',
         'Impegnato', 'Scost. €', 'Scost. %', 'Indicizzato %d' % Y, 'Prezzo %d' % Y, 'Indicizzato %d' % (Y + 1), 'Prezzo %d' % (Y + 1), 'Note']
    r_h = 11
    for j, h in enumerate(H, start=1):
        cell = ws.cell(r_h, j, h)
        cell.font, cell.fill, cell.alignment, cell.border = st['th'], st['thfill'], st['wrap'], st['border']
    ws.row_dimensions[r_h].height = 30
    r1 = r_h + 1
    for i, r in enumerate(M['righe']):
        row = r1 + i
        vals = [r['n'], ', '.join(r['gest']), r['ext'], r['hu'], r['ho'],
                '=D{0}*{1}+E{0}*{2}'.format(row, P['tUff'], P['tOff']), '=C{0}+F{0}'.format(row),
                r['fat'] + r['con'] + r['alt'], r['ddt'], r['ord'], '=H{0}+I{0}+J{0}'.format(row),
                '=IF(C{0}>0,K{0}-C{0},"")'.format(row), '=IF(C{0}>0,K{0}/C{0}-1,"")'.format(row),
                r['idxY'], '=N{0}*{1}'.format(row, P['fp']), r['idxY1'], '=P{0}*{1}'.format(row, P['fp']),
                r['note'] or ('non a budget' if r['extra'] else '') or (('proposto: ' + rif_txt(M)) if prop_rif and r['ext'] and not r['d'] else '') or r['d']]
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row, j, v)
            cell.border = st['border']
            cell.font = st['extra'] if r['extra'] else st['norm']
            if j in (3, 4, 5, 18):
                cell.fill = st['in']
        for j in (3, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17):
            ws.cell(row, j).number_format = EUR
        ws.cell(row, 4).number_format = ORE; ws.cell(row, 5).number_format = ORE; ws.cell(row, 13).number_format = PCT
        ws.cell(row, 11).font = st['bold']; ws.cell(row, 15).font = st['bold']; ws.cell(row, 17).font = st['bold']
        if prop_rif and r['ext']:
            ws.cell(row, 3).font = st['prop']
    rn = r1 + len(M['righe']) - 1 if M['righe'] else r1 - 1
    rt = rn + 1
    ws.cell(rt, 1, 'Totale')
    if M['righe']:
        for j in (3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17):
            ws.cell(rt, j, '=SUM({0}{1}:{0}{2})'.format(L(j), r1, rn))
        ws.cell(rt, 12, '=IF(C{0}>0,K{0}-C{0},"")'.format(rt)); ws.cell(rt, 13, '=IF(C{0}>0,K{0}/C{0}-1,"")'.format(rt))
    else:
        for j in (3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17):
            ws.cell(rt, j, 0)
    for j in range(1, len(H) + 1):
        cell = ws.cell(rt, j)
        cell.font, cell.fill, cell.border = st['tot'], st['totfill'], st['border']
        cell.number_format = ORE if j in (4, 5) else PCT if j == 13 else EUR if j >= 3 else '@'
    if M['righe']:
        ws.conditional_formatting.add('M%d:M%d' % (r1, rt), CellIsRule(operator='greaterThan', formula=['0'], fill=st['bad']))
        ws.conditional_formatting.add('M%d:M%d' % (r1, rt), CellIsRule(operator='between', formula=['-0.1', '0'], fill=st['warn']))
        ws.conditional_formatting.add('M%d:M%d' % (r1, rt), CellIsRule(operator='lessThan', formula=['-0.1'], fill=st['ok']))
        ws.conditional_formatting.add('L%d:L%d' % (r1, rt), CellIsRule(operator='greaterThan', formula=['0'], fill=st['bad']))

    # ---- ore interne: budget = ore per nodo (somma della tabella) + ore per l'intera commessa (cella gialla)
    ro = rt + 2
    o = M['ore']
    ws.cell(ro, 1, 'Ore interne').font = st['bold']
    ws.cell(ro, 2, 'budget = ore per nodo (somma) + ore per l\'intera commessa (celle gialle J)%s · consuntivo del gestionale per commessa%s' % (
        (' · proposte: media delle commesse di riferimento' if prop_rif and (o['hCm']['u'] or o['hCm']['o']) else ''),
        (' · ore aggiornate a ' + c['ore']['last']) if (c.get('ore') or {}).get('last') else '')).font = st['sub']
    HO = ['', 'Tariffa €/h', 'Budget h', 'Budget €', 'Consuntivo h', 'Consuntivo €', 'Scost. €', 'Scost. %', 'Ore per nodo (somma)', 'Ore intera commessa']
    for j, h in enumerate(HO, start=1):
        cell = ws.cell(ro + 1, j, h)
        cell.font, cell.fill, cell.border, cell.alignment = st['th'], st['thfill'], st['border'], st['wrap']
    ws.row_dimensions[ro + 1].height = 30
    ru, rp, rs = ro + 2, ro + 3, ro + 4
    for row, nome, tar, col, ch, hcm in ((ru, 'Ufficio', P['tUff'], 'D', o['cU'], o['hCm']['u']), (rp, 'Produzione', P['tOff'], 'E', o['cO'], o['hCm']['o'])):
        vals = [nome, '=' + tar, '=I{0}+J{0}'.format(row), '=C{0}*B{0}'.format(row), ch, '=E{0}*B{0}'.format(row),
                '=IF(D{0}>0,F{0}-D{0},"")'.format(row), '=IF(D{0}>0,F{0}/D{0}-1,"")'.format(row), '={0}{1}'.format(col, rt), hcm or 0]
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row, j, v)
            cell.border, cell.font = st['border'], st['norm']
        ws.cell(row, 2).number_format = '#,##0.00 "€"'
        for j in (3, 5, 9, 10):
            ws.cell(row, j).number_format = ORE
        for j in (4, 6, 7):
            ws.cell(row, j).number_format = EUR
        ws.cell(row, 8).number_format = PCT
        ws.cell(row, 10).fill = st['in']
        if prop_rif and hcm:
            ws.cell(row, 10).font = st['prop']
    ws.cell(rs, 1, 'Totale ore')
    for j in (3, 4, 5, 6, 9, 10):
        ws.cell(rs, j, '={0}{1}+{0}{2}'.format(L(j), ru, rp))
    ws.cell(rs, 7, '=IF(D{0}>0,F{0}-D{0},"")'.format(rs)); ws.cell(rs, 8, '=IF(D{0}>0,F{0}/D{0}-1,"")'.format(rs))
    for j in range(1, len(HO) + 1):
        cell = ws.cell(rs, j)
        cell.font, cell.fill, cell.border = st['tot'], st['totfill'], st['border']
        cell.number_format = ORE if j in (3, 5, 9, 10) else PCT if j == 8 else EUR if j >= 4 else '@'
    ws.conditional_formatting.add('H%d:H%d' % (ru, rs), CellIsRule(operator='greaterThan', formula=['0'], fill=st['bad']))

    # ---- riquadro riepilogo (righe 4-9), con formule sulla tabella e sul blocco ore
    ws['A4'], ws['B4'] = 'Prezzo di vendita', M['prezzo'] if M['prezzo'] is not None else ''
    ws['C4'] = ('da ' + M['prezzoFonte']) if M['prezzoFonte'] else 'non trovato: né contratto né ordine cliente'
    if M['valore'] is not None and M['oc'] is not None and abs(M['valore'] - M['oc']) > 1:
        ws['C4'] = ws['C4'].value + ' · ordine cliente nel gestionale %s €' % format(round(M['oc']), ',').replace(',', '.')
    ws['A5'] = 'Budget proposto (esterni + ore) · da confermare' if prop_rif else 'Budget totale (esterni + ore)'
    ws['B5'] = '=C{0}+D{1}'.format(rt, rs)
    ws['C5'] = '=IF(OR(B5>0,C{1}>0),"esterni "&TEXT(C{0},"#.##0")&" € + ore "&TEXT(D{1},"#.##0")&" €"{2},"{3}")'.format(
        rt, rs, '&" · da confermare"' if prop_rif else '', 'commessa evasa: contano i costi consuntivi' if M['chiusa'] else 'nessun budget inserito')
    ws['A6'], ws['B6'] = 'Costi a oggi (impegnato + ore)', '=K{0}+F{1}'.format(rt, rs)
    ws['C6'] = '="impegnato "&TEXT(K{0},"#.##0")&" € + ore "&TEXT(F{1},"#.##0")&" €"'.format(rt, rs)
    ws['A7'], ws['B7'] = 'Scostamento esterni', '=IF(C{0}>0,K{0}-C{0},"")'.format(rt)
    ws['C7'] = '=IF(C{0}>0,TEXT(K{0}/C{0}-1,"+0%;-0%")&" sul budget esterno","serve il budget per nodo")'.format(rt)
    utile_b = '=IF(OR(B4="",AND(B5<=0,C{0}<=0)),"",B4-B5)'.format(rs)   # utile a budget: solo con prezzo e budget (esterni o ore)
    utile_o = '=IF(B4="","",B4-B6)'                                      # utile con i costi a oggi
    if M['chiusa']:
        ws['A8'], ws['B8'] = 'Utile consuntivo', utile_o
        ws['C8'] = '=IF(B4="","manca il prezzo di vendita","margine "&TEXT(B8/B4,"0%")&" sul prezzo · prezzo − costi consuntivi (impegnato + ore)")'
        ws['A9'], ws['B9'] = 'Utile a budget (memoria)', utile_b
        ws['C9'] = '=IF(B9="","nessun budget","margine "&TEXT(B9/B4,"0%")&" · prezzo − budget totale")'
    else:
        ws['A8'], ws['B8'] = 'Utile a budget', utile_b
        ws['C8'] = '=IF(B4="","manca il prezzo di vendita",IF(B8="","serve il budget: inseriscilo o conferma quello proposto","margine "&TEXT(B8/B4,"0%")&" sul prezzo{0} · con i soli costi a oggi "&TEXT(B4-B6,"#.##0")&" € ("&TEXT((B4-B6)/B4,"0%")&")"))'.format(
            ' · sul budget proposto, da confermare' if prop_rif else '')
        ws['A9'], ws['B9'] = 'Utile con i costi a oggi', utile_o
        ws['C9'] = '=IF(B9="","manca il prezzo di vendita","margine "&TEXT(B9/B4,"0%")&" · prezzo − costi a oggi (impegnato + ore)")'
    for r in range(4, 10):
        ws.cell(r, 1).font = st['norm']; ws.cell(r, 2).font = st['bold']; ws.cell(r, 2).number_format = EUR; ws.cell(r, 3).font = st['sub']
    ws['B4'].fill = st['in']
    ws.conditional_formatting.add('B8', CellIsRule(operator='lessThan', formula=['0'], fill=st['bad']))
    ws.conditional_formatting.add('B9', CellIsRule(operator='lessThan', formula=['0'], fill=st['bad']))
    ws.conditional_formatting.add('B7', CellIsRule(operator='greaterThan', formula=['0'], fill=st['bad']))

    # ---- larghezze, blocco, stampa
    widths = [30, 26, 14, 11, 12, 13, 14, 13, 13, 13, 14, 13, 9, 14, 14, 14, 14, 28]
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[L(j)].width = w
    ws.freeze_panes = 'B%d' % r1
    ws.sheet_view.zoomScale = 90
    ws.print_options.horizontalCentered = True
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.cell(rs + 2, 1, 'Celle gialle = budget da compilare (per nodo; ore anche per l\'intera commessa). Fatturato = fatture fornitore + costi contabilizzati; Consegnato = DDT e conto lavoro non ancora fatturati; Ordinato = ordini fornitore aperti; Impegnato = la somma. '
            'Utile a budget = prezzo − budget totale (commesse in corso); utile consuntivo = prezzo − costi (commesse evase). Indicizzato e Prezzo usano il foglio Parametri.').font = st['sub']
    return ws.title


def scrivi_riepilogo(wb, S, MM):
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.utils import get_column_letter as L
    st = _stili()
    ws = wb.create_sheet('Riepilogo', 0)
    cons = S.get('cons') or {}
    n_ch = sum(1 for M in MM if M['chiusa'])
    ws['A1'], ws['A1'].font = 'Budget e consuntivo · ' + ('commesse in corso' if not n_ch else 'commesse evase' if n_ch == len(MM) else 'commesse'), st['h1']
    ws['A2'] = '%d commesse%s · consuntivo dall\'estrazione del %s · generato il %s · valori calcolati (i fogli per commessa hanno le formule) · utile: a budget per le commesse in corso, consuntivo per le evase' % (
        len(MM), (' (%d evase)' % n_ch) if n_ch and n_ch != len(MM) else '', cons.get('agg') or '—', dt.date.today().isoformat())
    ws['A2'].font = st['h2']
    H = ['Commessa', 'Cliente', 'Descrizione', 'Nodi', 'Stato nodi', 'Prezzo di vendita', 'Fonte prezzo', 'Budget esterno', 'Budget ore €', 'Budget totale', 'Fatturato', 'Consegnato', 'Ordinato', 'Impegnato',
         'Ore consuntivo €', 'Costi a oggi', 'Scost. esterni €', 'Scost. %', 'Utile', 'Tipo utile', 'Margine %', 'Utile a budget', 'Utile con i costi a oggi']
    rh = 4
    for j, h in enumerate(H, start=1):
        cell = ws.cell(rh, j, h)
        cell.font, cell.fill, cell.alignment, cell.border = st['th'], st['thfill'], st['wrap'], st['border']
    ws.row_dimensions[rh].height = 30
    for i, M in enumerate(MM):
        row, t, c = rh + 1 + i, M['tot'], M['c']
        vals = [c['code'], c.get('cliente') or '', c.get('desc') or '', len(M['nodi']), stato_nodi(M) + ((' da %d simil%s' % (len(M['rif']), 'i' if len(M['rif']) > 1 else 'e')) if M['proposta'] and M['rif'] and not M['chiusa'] else ''),
                M['prezzo'] if M['prezzo'] is not None else '', M['prezzoFonte'] or '', t['ext'], M['ore']['bEur'], M['budgetTot'], t['fat'] + t['con'] + t['alt'], t['ddt'], t['ord'], t['imp'],
                M['ore']['cEur'], M['costoOggi'], t['sc'] if t['ext'] > 0 else '', (t['pct'] - 1) if t['pct'] is not None else '',
                M['utile'] if M['utile'] is not None else '', M['utileTipo'] or '', M['marg'] if M['marg'] is not None else '',
                M['utileB'] if M['utileB'] is not None else '', M['utileO'] if M['utileO'] is not None else '']
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row, j, v)
            cell.border, cell.font = st['border'], st['norm']
            cell.number_format = PCT if j == 18 else PCT0 if j == 21 else '@' if j in (7, 20) else EUR if j >= 6 else '@' if j != 4 else '0'
        ws.cell(row, 1).font = st['bold']; ws.cell(row, 19).font = st['bold']
        if not M['chiusa'] and (M['proposta'] or not M['conf']):
            ws.cell(row, 5).fill = st['warn']
    rn = rh + len(MM)
    rt = rn + 1
    ws.cell(rt, 1, 'Totale')
    for j in (6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 22, 23):
        ws.cell(rt, j, '=SUM({0}{1}:{0}{2})'.format(L(j), rh + 1, rn)).number_format = EUR
    ws.cell(rt, 17, '=IF(H{0}>0,N{0}-H{0},"")'.format(rt)).number_format = EUR
    ws.cell(rt, 18, '=IF(H{0}>0,N{0}/H{0}-1,"")'.format(rt)).number_format = PCT
    ws.cell(rt, 20, 'consuntivo' if n_ch == len(MM) and MM else 'a budget / consuntivo' if n_ch else 'a budget')
    ws.cell(rt, 21, '=IF(F{0}>0,S{0}/F{0},"")'.format(rt)).number_format = PCT0
    for j in range(1, len(H) + 1):
        cell = ws.cell(rt, j)
        cell.font, cell.fill, cell.border = st['tot'], st['totfill'], st['border']
    if MM:
        ws.conditional_formatting.add('R%d:R%d' % (rh + 1, rt), CellIsRule(operator='greaterThan', formula=['0'], fill=st['bad']))
        ws.conditional_formatting.add('S%d:S%d' % (rh + 1, rt), CellIsRule(operator='lessThan', formula=['0'], fill=st['bad']))
    widths = [12, 26, 24, 6, 18, 15, 22, 14, 13, 14, 13, 13, 13, 14, 14, 14, 15, 9, 14, 15, 10, 14, 16]
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[L(j)].width = w
    ws.freeze_panes = 'B%d' % (rh + 1)
    ws.auto_filter.ref = 'A%d:%s%d' % (rh, L(len(H)), rn)
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def lista_commesse(S, codici):
    by = {c.get('code'): c for c in S.get('commesse', [])}
    if codici is None:
        return [c for c in S.get('commesse', []) if not c.get('ev') and not c.get('sp')]
    mancanti = [k for k in codici if k not in by]
    if mancanti:
        sys.exit('commesse non trovate nello stato: %s' % ', '.join(mancanti))
    return [by[k] for k in codici]


def costruisci(S, codici, Y=None, riepilogo=None, rif_mode=None):
    import openpyxl
    Y = Y or dt.date.today().year
    cf = bcfg(S)
    lista = lista_commesse(S, codici)
    MM = [modello(S, c, Y, rif_mode) for c in lista]
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    P = scrivi_parametri(wb, cf, Y, S)
    usati = {'Parametri', 'Riepilogo'}
    for M in MM:
        scrivi_commessa(wb, S, M, P, usati)
    if riepilogo or (riepilogo is None and len(MM) != 1):
        scrivi_riepilogo(wb, S, MM)
    wb.move_sheet('Parametri', offset=len(wb.sheetnames))
    wb.active = 0
    return wb, MM


def json_modello(MM):
    def sim(s):
        return {'code': s['code'], 'anno': s['anno'], 'tot': s['tot'], 'nodi': s['nodi']}

    def pulisci(M):
        d = {k: v for k, v in M.items() if k not in ('c', 'righe', 'tot', 'nodi', 'rif', 'simili')}
        d['code'] = M['c']['code']
        d['nodi'] = [{k: v for k, v in n.items()} for n in M['nodi']]
        d['rif'] = [sim(s) for s in M['rif']]
        d['simili'] = [sim(s) for s in M['simili']]
        d['righe'] = [{k: v for k, v in r.items() if k != 'anni'} | {'anni': r['anni']} for r in M['righe']]
        d['tot'] = M['tot']
        return d
    return [pulisci(M) for M in MM]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--state', required=True)
    ap.add_argument('--cm', action='append', help='codice commessa (ripetibile)')
    ap.add_argument('--all', action='store_true', help='tutte le commesse in corso (non evase, non sospese)')
    ap.add_argument('--out', help='file .xlsx o cartella di destinazione')
    ap.add_argument('--anno', type=int, help='anno corrente (default: oggi)')
    ap.add_argument('--rif', help='commessa chiusa di riferimento per la proposta (default: media delle simili)')
    ap.add_argument('--json', action='store_true', help='stampa il modello calcolato in JSON invece di scrivere il file')
    a = ap.parse_args()
    if not a.all and not a.cm:
        ap.error('indica --cm CODICE (anche più volte) oppure --all')
    S = json.load(open(a.state, encoding='utf-8'))
    codici = None if a.all else a.cm
    if a.json:
        Y = a.anno or dt.date.today().year
        print(json.dumps(json_modello([modello(S, c, Y, a.rif) for c in lista_commesse(S, codici)]), ensure_ascii=False, indent=1))
        return
    if not a.out:
        ap.error('--out è obbligatorio senza --json')
    wb, MM = costruisci(S, codici, a.anno, rif_mode=a.rif)
    out = a.out
    if os.path.isdir(out) or out.endswith('/') or not out.lower().endswith('.xlsx'):
        os.makedirs(out, exist_ok=True)
        nome = 'budget-tutte.xlsx' if codici is None else 'budget-%s.xlsx' % re.sub(r'[^A-Za-z0-9_-]+', '_', '-'.join(codici))[:60]
        out = os.path.join(out, nome)
    wb.save(out)
    print('%s · %d commesse · fogli: %s' % (out, len(MM), ', '.join(wb.sheetnames[:6]) + (' …' if len(wb.sheetnames) > 6 else '')))


if __name__ == '__main__':
    main()
