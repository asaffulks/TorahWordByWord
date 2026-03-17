#!/usr/bin/env python3
"""Make ALL glosses reader-friendly. No jargon, no Hebrew in English field,
no academic abbreviations, no confusing parentheticals."""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Hebrew-to-English for roots appearing as glosses
HEBREW_GLOSSES = {
    '\u05D1\u05D9\u05EA': 'house',
    '\u05D0\u05D9\u05DC': 'ram',
    '\u05E1\u05E4\u05E8': 'count',
    '\u05E4\u05E7\u05D3': 'appoint',
    '\u05E2\u05D9\u05E8\u05DD': 'Iram',
    '\u05E2\u05DC\u05D9\u05D5\u05DF': 'Most High',
    '\u05D7\u05E0\u05D8': 'embalm',
    '\u05D1\u05DA': 'in·you',
    '\u05D4\u05E8\u05D0\u05E9\u05D5\u05DF': 'the·first',
    '\u05DC\u05D5\u05D8\u05DF': 'Lotan',
    '\u05D4\u05E8\u05E7\u05D5\u05EA': 'the·temples',
}

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            orig = e

            # 1. Strip parenthetical clarifications — keep just the main word
            # "seven (cardinal number)" -> "seven"
            # "you (second pers. sing. masc.)" -> "you"
            # "I (first pers. sing.)" -> "I"
            # "stone (large or small)" -> "stone"
            if '(' in e and ')' in e:
                clean = re.sub(r'\s*\([^)]*\)', '', e).strip()
                if clean and len(clean) >= 1:
                    e = clean

            # "I (we) pray" -> "please" (this is נא)
            if 'I (we) pray' in e:
                e = e.replace('I (we) pray', 'please')

            # 2. Hebrew text in English gloss -> translate
            has_hebrew = any('\u05D0' <= ch <= '\u05EA' for ch in e)
            if has_hebrew:
                # Check if it's a known Hebrew word
                heb_only = ''.join(ch for ch in e if '\u05D0' <= ch <= '\u05EA')
                if heb_only in HEBREW_GLOSSES:
                    e = HEBREW_GLOSSES[heb_only]
                elif w.get('root') and w['root'] != e:
                    # Has a root, use that concept
                    e = w['root']
                else:
                    # Strip Hebrew chars, keep English
                    e_stripped = re.sub(r'[\u05D0-\u05EA\u05B0-\u05C7\u0591-\u05AF]+', '', e).strip()
                    if e_stripped and len(e_stripped) > 1:
                        e = e_stripped
                    else:
                        key = strip_n(w['heb']).replace('\u05BE', '')
                        e = key  # consonantal form as last resort

            # 3. Academic abbreviations
            if e == 'prep':
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'אל' in key: e = 'to'
                elif 'על' in key: e = 'upon'
                elif 'מן' in key or key.startswith('מ'): e = 'from'
                elif 'עד' in key: e = 'until'
                elif 'בין' in key: e = 'between'
                elif 'אחר' in key: e = 'after'
                elif 'תחת' in key: e = 'under'
                elif 'לפני' in key: e = 'before'
                else: e = 'to'
            elif e == 'nm': e = 'name'
            elif e == 'nf': e = 'female'
            elif e == 'vb': e = w.get('root', 'do')
            elif e == 'conj': e = 'and'
            elif e == 'adv': e = 'thus'

            # 4. Specific cleanup
            # "extended surface (solid)" -> "firmament"
            e = e.replace('extended surface', 'firmament')
            # "you(pl)" -> "you all"
            e = e.replace('you(pl)', 'you·all')
            e = e.replace('they(f)', 'they')
            # "cubit-a measure of distance (the forearm)" -> "cubit"
            if 'cubit' in e and 'measure' in e:
                e = 'cubit'
            # "flat (of the hand or foot)" -> "palm"
            if 'flat' in e and 'hand' in e:
                e = 'palm'
            # "sheaf (as something bound)" -> "sheaf"
            if 'sheaf' in e and 'bound' in e:
                e = 'sheaf'
            # "far be it (from me)" -> "far be it"
            if 'far be it' in e:
                e = 'far·be·it'
            # "that which is (or belongs) to" -> "that·which·belongs·to"
            if 'that which is' in e:
                e = 'belonging·to'
            # "to draw (water)" -> "to·draw·water"
            if e == 'to draw':
                e = 'draw·water'
            # "to interpret (dreams)" -> "interpret"
            if 'to interpret' in e:
                e = 'interpret'
            # "open (the eyes)" -> "open"
            if 'open' in e and 'eyes' in e:
                e = 'open'
            # "ram·please" from "ram·I (we) pray" - ram here is אל misglossed
            if e == 'ram\u00B7please':
                e = 'to\u00B7please'
            if e.startswith('ram\u00B7'):
                e = e.replace('ram\u00B7', 'to\u00B7')
            # "mother·please" -> "please"
            if 'mother\u00B7please' in e:
                e = 'please'

            # 5. Clean up
            e = e.strip()
            e = re.sub(r'\s+', ' ', e)
            e = e.replace(' \u00B7', '\u00B7').replace('\u00B7 ', '\u00B7')

            if e != orig:
                w['eng'] = e
                fixed += 1

# Protect Gen 1:1
v1 = d['chapters'][0]['verses'][0]
expected = ['in\u00B7beginning', 'created', 'God', '[identifies object]', 'the\u00B7heavens', 'and\u00B7[identifies object]', 'the\u00B7earth']
for i, exp in enumerate(expected):
    if i < len(v1['words']):
        v1['words'][i]['eng'] = exp

# Final check
remaining = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            if e in ('nm', 'nf', 'vb', 'adj', 'adv', 'v', 'n', 'conj', 'prep', 'pron'):
                remaining += 1
            elif any('\u05D0' <= ch <= '\u05EA' for ch in e) and 'identifies' not in e:
                remaining += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed} entries. Remaining issues: {remaining}')
