#!/usr/bin/env python3
"""Aggiorna alcuni campi di state.json del Danilo Second Brain senza toccare il resto.

Uso:
  python3 aggiorna_state.py --in state.json --out state.nuovo.json \
      [--ordf ordf.json] [--forn-termini termini.json] [--set chiave=file.json ...]

Lo stato è la memoria di lavoro di Danilo (task, note, spunte): questo script sostituisce
solo le chiavi indicate e lascia intatto tutto il resto. Da usare prima di pubblicare
state.json con il tool Artifact (files {"state.json": ...}).
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--ordf', help='JSON prodotto da gestionale_ordini.py')
    ap.add_argument('--forn-termini', help='JSON {fornitore: {testo, tipo, gg, base, rate, fonte, conf}}')
    ap.add_argument('--set', action='append', default=[], help='chiave=file.json')
    a = ap.parse_args()

    S = json.load(open(a.src, encoding='utf-8'))
    if a.ordf:
        S['ordf'] = json.load(open(a.ordf, encoding='utf-8'))
    if a.forn_termini:
        S['fornTermini'] = json.load(open(a.forn_termini, encoding='utf-8'))
    for spec in a.set:
        k, _, f = spec.partition('=')
        S[k] = json.load(open(f, encoding='utf-8'))
    S.setdefault('scadenze', [])
    S.setdefault('fornTermini', {})
    json.dump(S, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'{a.out}: chiavi {sorted(S.keys())}')


if __name__ == '__main__':
    main()
