#!/usr/bin/env python3
"""Trasforma il risultato della ricerca in Gmail sui termini di pagamento in `fornTermini`.

Uso:
  python3 termini_fornitori.py --in risultato_workflow.json --out fornTermini.json [--min media]

Input: {"fornitori": [{fornitore, trovato, termini: [{testo, tipo, giorni, base, rate, direzione,
threadId, data, mittente, oggetto, citazione, verifica: {confermato, motivo, correzione}}],
sintesi, confidenza, note}]}.

Regola "mai indovinare": entra in fornTermini solo un termine la cui citazione è stata
CONFERMATA da un secondo agente che ha riaperto la mail. Fra più termini confermati vince il
più recente. I fornitori senza termini confermati non compaiono: la pagina li mostra come
"termini da confermare" e mette il pagamento alla data di consegna, in una riga separata.
"""
import argparse
import json
import re

ORD = {'alta': 3, 'media': 2, 'bassa': 1, 'nessuna': 0}


def normalizza(t):
    """Ricava gg/base dal testo quando l'agente non li ha compilati bene."""
    gg = t.get('giorni')
    base = (t.get('base') or 'non specificato').lower()
    testo = (t.get('testo') or '').lower()
    if gg is None or gg < 0:
        m = re.search(r'(\d{2,3})\s*(gg|giorni|g\.|days?)', testo)
        gg = int(m.group(1)) if m else None
    if base == 'non specificato':
        if re.search(r'f\.?\s*m\.?|fine mese|dffm|d\.f\.f\.m', testo):
            base = 'dffm'
        elif re.search(r'd\.?f\.?|data fattura|dalla fattura|invoice date', testo):
            base = 'df'
        elif re.search(r'consegna|delivery', testo):
            base = 'consegna'
        elif re.search(r'anticip|all\'ordine|ordine|advance|down ?payment', testo):
            base = 'ordine'
    if gg is None and re.search(r'anticip|vista fattura|contanti|rimessa diretta|alla consegna', testo):
        gg = 0
    return gg, base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--min', default='bassa', choices=['alta', 'media', 'bassa'],
                    help='confidenza minima del fornitore per usare i termini nel cash flow')
    a = ap.parse_args()

    R = json.load(open(a.src, encoding='utf-8'))
    out, scartati = {}, []
    for f in R.get('fornitori', []):
        if not f.get('trovato'):
            continue
        conf = (f.get('confidenza') or 'nessuna').lower()
        buoni = [t for t in f.get('termini', []) if (t.get('verifica') or {}).get('confermato')]
        if not buoni or ORD.get(conf, 0) < ORD[a.min]:
            scartati.append((f.get('fornitore'), conf, len(f.get('termini', [])), len(buoni)))
            continue
        # preferisce il termine USABILE (giorni e base noti) piu' recente; a parita', il piu' recente
        def punteggio(t):
            gg, base = normalizza(t)
            usabile = gg is not None and base in ('df', 'dffm', 'consegna')
            parziale = gg is not None or base not in ('non specificato', 'altro')
            return (2 if usabile else 1 if parziale else 0, t.get('data') or '')
        buoni.sort(key=punteggio, reverse=True)
        t = buoni[0]
        gg, base = normalizza(t)
        corr = ((t.get('verifica') or {}).get('correzione') or '').strip()
        fonte = f"{t.get('mittente', '')} · {t.get('data', '')} · {t.get('oggetto', '')} · thread {t.get('threadId', '')}"
        if corr:
            fonte += ' · nota verifica: ' + (corr[:220] + '…' if len(corr) > 220 else corr)
        out[f['fornitore']] = {
            'testo': t.get('testo', ''),
            'tipo': t.get('tipo', ''),
            'gg': gg,
            'base': base,
            'rate': t.get('rate', ''),
            'direzione': t.get('direzione', ''),
            'fonte': fonte,
            'citazione': t.get('citazione', ''),
            'conf': conf,
            'correzione': corr,
            'altri': len(buoni) - 1,
        }
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(out)} fornitori con termini confermati → {a.out}')
    for s in scartati:
        print('  scartato:', s)


if __name__ == '__main__':
    main()
