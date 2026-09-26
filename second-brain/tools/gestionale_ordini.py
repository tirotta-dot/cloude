#!/usr/bin/env python3
"""Costruisce il blocco `ordf` del Danilo Second Brain da una o più estrazioni del gestionale.

Uso:
  python3 gestionale_ordini.py --out ordf.json --prev state.json \
      --src S=20260911_Rev00.xlsx:Costi --src C=estrazione_completa.xlsx:Foglio1

Ogni --src è ETICHETTA=file.xlsx[:foglio]. Le righe con TipoDocumento «Ordine fornitore»
sono, per definizione del gestionale, ordini ancora aperti (spiegazione di Luca Tirotta
del 15/09/2026). Le righe uguali in più estrazioni ricevono l'etichetta combinata (es. "SC").
Con --prev vengono conservati i campi già presenti nello stato (solleciti `sl`/`sol`, note).
"""
import argparse
import datetime as dt
import json
import sys

import openpyxl

COLS = {
    'n': 'N° Doc.', 'f': 'Ragione sociale', 'cm': 'Progetto', 'nd': 'Nodo',
    'art': 'Codice articolo', 'd': 'Descrizione', 'q': 'Qt. acquistate', 'imp': 'Costo',
    'dp': 'Data consegna', 'cd': 'Cod. documento',
}


def s(x):
    return '' if x is None else str(x).strip()


def key(v):
    return (s(v.get('n')), s(v.get('f')), s(v.get('art')), s(v.get('d'))[:30])


def leggi(path, foglio=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[foglio] if foglio else wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    hdr = [s(h) for h in next(rows)]
    idx = {h: i for i, h in enumerate(hdr)}
    mancanti = [c for c in COLS.values() if c not in idx and c != 'Cod. documento']
    if 'TipoDocumento' not in idx or mancanti:
        sys.exit(f'{path}: colonne mancanti {mancanti or ["TipoDocumento"]}')
    out = []
    for r in rows:
        if s(r[idx['TipoDocumento']]) != 'Ordine fornitore':
            continue
        v = {}
        for k, col in COLS.items():
            if col not in idx:
                continue
            val = r[idx[col]]
            if k == 'dp':
                v[k] = val.strftime('%Y-%m-%d') if isinstance(val, dt.datetime) else None
            elif k in ('q', 'imp'):
                v[k] = val
            elif k == 'd':
                v[k] = s(val).replace('_x000D_', '').replace('\r', ' ').replace('\n', ' ').strip()
            else:
                v[k] = s(val)
        out.append(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', action='append', required=True, help='ETICHETTA=file.xlsx[:foglio]')
    ap.add_argument('--prev', help='state.json precedente, per conservare sl/sol/note')
    ap.add_argument('--out', required=True)
    ap.add_argument('--agg', default=dt.date.today().isoformat())
    a = ap.parse_args()

    unione = {}
    for spec in a.src:
        et, _, rest = spec.partition('=')
        path, _, foglio = rest.partition(':')
        for v in leggi(path, foglio or None):
            k = key(v)
            if k in unione:
                unione[k]['src'] = ''.join(sorted(set(unione[k]['src'] + et)))
                if v.get('dp'):
                    unione[k]['dp'] = v['dp']
            else:
                v['src'] = et
                unione[k] = v

    if a.prev:
        prev = json.load(open(a.prev, encoding='utf-8'))
        for old in (prev.get('ordf') or {}).get('voci', []):
            k = key(old)
            if k in unione:
                for campo in ('sl', 'sol', 'note', 'nd_note'):
                    if old.get(campo) is not None:
                        unione[k][campo] = old[campo]

    voci = list(unione.values())
    ordf = {
        'agg': a.agg,
        'file': ' + '.join(a.src),
        'fonte': 'righe con TipoDocumento «Ordine fornitore»: restano nell\'estrazione finché '
                 'l\'ordine non diventa DDT o fattura (Luca Tirotta, 15/09/2026)',
        'voci': voci,
    }
    json.dump(ordf, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)
    per_src = {}
    for v in voci:
        per_src[v['src']] = per_src.get(v['src'], 0) + 1
    print(f'{len(voci)} righe → {a.out}  {per_src}')


if __name__ == '__main__':
    main()
