#!/usr/bin/env python3
"""Fix glosses and roots in genesis.json using a corrections dictionary."""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_nikud(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Corrections: consonantal form -> (root, english)
# None means "keep existing value"
CORRECTIONS = {
    # God
    '\u05D0\u05DC\u05D4\u05D9\u05DD': ('\u05D0\u05DC\u05D4', 'God'),
    '\u05D4\u05D0\u05DC\u05D4\u05D9\u05DD': ('\u05D0\u05DC\u05D4', 'the\u00B7God'),
    '\u05D0\u05DC\u05D4\u05D9': ('\u05D0\u05DC\u05D4', 'God\u00B7of'),
    '\u05D5\u05D0\u05DC\u05D4\u05D9': ('\u05D0\u05DC\u05D4', 'and\u00B7God\u00B7of'),
    '\u05DC\u05D0\u05DC\u05D4\u05D9\u05DD': ('\u05D0\u05DC\u05D4', 'to\u00B7God'),
    '\u05D0\u05EA\u05D4\u05D0\u05DC\u05D4\u05D9\u05DD': ('\u05D0\u05DC\u05D4', '[obj.mark]\u00B7the\u00B7God'),
    # Object marker
    '\u05D0\u05EA': (None, '[obj.mark]'),
    '\u05D5\u05D0\u05EA': (None, 'and\u00B7[obj.mark]'),
    # Bad glosses
    '\u05DE\u05D0\u05D3': ('\u05DE\u05D0\u05D3', 'very'),
    '\u05D1\u05DE\u05D0\u05D3': ('\u05DE\u05D0\u05D3', 'very\u00B7much'),
    '\u05DE\u05E2\u05DC': ('\u05E2\u05DC', 'above'),
    '\u05E2\u05DC': ('\u05E2\u05DC', 'upon'),
    '\u05E2\u05DC\u05D9\u05D5': ('\u05E2\u05DC', 'upon\u00B7him'),
    '\u05E2\u05DC\u05D9': ('\u05E2\u05DC', 'upon\u00B7me'),
    '\u05E2\u05DC\u05D9\u05E0\u05D5': ('\u05E2\u05DC', 'upon\u00B7us'),
    '\u05E2\u05DC\u05D9\u05D4\u05DD': ('\u05E2\u05DC', 'upon\u00B7them'),
    '\u05E2\u05DC\u05D9\u05DA': ('\u05E2\u05DC', 'upon\u00B7you'),
    '\u05E2\u05DC\u05D9\u05D4': ('\u05E2\u05DC', 'upon\u00B7her'),
    '\u05DB\u05DF': ('\u05DB\u05D5\u05DF', 'so'),
    '\u05DC\u05D1\u05DC\u05EA\u05D9': ('\u05D1\u05DC\u05D4', 'so\u00B7as\u00B7not\u00B7to'),
    '\u05E2\u05D5\u05D3\u05E0\u05D5': ('\u05E2\u05D5\u05D3', 'still'),
    '\u05D4\u05E2\u05D5\u05D3': ('\u05E2\u05D5\u05D3', 'is\u00B7there\u00B7still'),
    '\u05DB\u05E0\u05D9\u05DD': ('\u05DB\u05D5\u05DF', 'honest'),
    # Common verbs
    '\u05D5\u05D9\u05D0\u05DE\u05E8': ('\u05D0\u05DE\u05E8', 'and\u00B7said'),
    '\u05D0\u05DE\u05E8': ('\u05D0\u05DE\u05E8', 'said'),
    '\u05D5\u05EA\u05D0\u05DE\u05E8': ('\u05D0\u05DE\u05E8', 'and\u00B7she\u00B7said'),
    '\u05DC\u05D0\u05DE\u05E8': ('\u05D0\u05DE\u05E8', 'saying'),
    '\u05D5\u05D9\u05D4\u05D9': ('\u05D4\u05D9\u05D4', 'and\u00B7it\u00B7was'),
    '\u05D4\u05D9\u05D4': ('\u05D4\u05D9\u05D4', 'was'),
    '\u05D4\u05D9\u05EA\u05D4': ('\u05D4\u05D9\u05D4', 'was'),
    '\u05D9\u05D4\u05D9': ('\u05D4\u05D9\u05D4', 'let\u00B7there\u00B7be'),
    '\u05D5\u05D4\u05D9\u05D4': ('\u05D4\u05D9\u05D4', 'and\u00B7it\u00B7shall\u00B7be'),
    '\u05D5\u05D9\u05E2\u05E9': ('\u05E2\u05E9\u05D4', 'and\u00B7made'),
    '\u05E2\u05E9\u05D4': ('\u05E2\u05E9\u05D4', 'made'),
    '\u05D5\u05D9\u05E7\u05E8\u05D0': ('\u05E7\u05E8\u05D0', 'and\u00B7called'),
    '\u05E7\u05E8\u05D0': ('\u05E7\u05E8\u05D0', 'called'),
    '\u05D5\u05D9\u05E8\u05D0': ('\u05E8\u05D0\u05D4', 'and\u00B7saw'),
    '\u05D5\u05D9\u05D1\u05D3\u05DC': ('\u05D1\u05D3\u05DC', 'and\u00B7separated'),
    '\u05D5\u05D9\u05D1\u05E8\u05D0': ('\u05D1\u05E8\u05D0', 'and\u00B7created'),
    '\u05D1\u05E8\u05D0': ('\u05D1\u05E8\u05D0', 'created'),
    '\u05D5\u05D9\u05DC\u05DA': ('\u05D4\u05DC\u05DA', 'and\u00B7went'),
    '\u05D5\u05D9\u05DC\u05DB\u05D5': ('\u05D4\u05DC\u05DA', 'and\u00B7they\u00B7went'),
    '\u05D5\u05D9\u05D1\u05D0': ('\u05D1\u05D5\u05D0', 'and\u00B7came'),
    '\u05D5\u05D9\u05D1\u05D0\u05D5': ('\u05D1\u05D5\u05D0', 'and\u00B7they\u00B7came'),
    '\u05D5\u05D9\u05E7\u05D7': ('\u05DC\u05E7\u05D7', 'and\u00B7took'),
    '\u05D5\u05EA\u05E7\u05D7': ('\u05DC\u05E7\u05D7', 'and\u00B7she\u00B7took'),
    '\u05D5\u05D9\u05EA\u05DF': ('\u05E0\u05EA\u05DF', 'and\u00B7gave'),
    '\u05D5\u05EA\u05DC\u05D3': ('\u05D9\u05DC\u05D3', 'and\u00B7she\u00B7bore'),
    '\u05D5\u05D9\u05D5\u05DC\u05D3': ('\u05D9\u05DC\u05D3', 'and\u00B7begot'),
    '\u05D5\u05D9\u05DC\u05D3': ('\u05D9\u05DC\u05D3', 'and\u00B7begot'),
    '\u05D5\u05D9\u05D7\u05D9': ('\u05D7\u05D9\u05D4', 'and\u00B7lived'),
    '\u05D5\u05D9\u05DE\u05EA': ('\u05DE\u05D5\u05EA', 'and\u00B7died'),
    '\u05D5\u05D9\u05E9\u05D1': ('\u05D9\u05E9\u05D1', 'and\u00B7dwelt'),
    '\u05D5\u05D9\u05E9\u05DC\u05D7': ('\u05E9\u05DC\u05D7', 'and\u00B7sent'),
    '\u05D5\u05D9\u05E6\u05D0': ('\u05D9\u05E6\u05D0', 'and\u00B7went\u00B7out'),
    '\u05D5\u05D9\u05E9\u05DD': ('\u05E9\u05D9\u05DD', 'and\u00B7placed'),
    '\u05D5\u05D9\u05D3\u05D1\u05E8': ('\u05D3\u05D1\u05E8', 'and\u00B7spoke'),
    # Common nouns
    '\u05D0\u05E8\u05E5': ('\u05D0\u05E8\u05E5', 'earth'),
    '\u05D4\u05D0\u05E8\u05E5': ('\u05D0\u05E8\u05E5', 'the\u00B7earth'),
    '\u05D1\u05D0\u05E8\u05E5': ('\u05D0\u05E8\u05E5', 'in\u00B7the\u00B7land'),
    '\u05DE\u05D0\u05E8\u05E5': ('\u05D0\u05E8\u05E5', 'from\u00B7the\u00B7land'),
    '\u05E9\u05DE\u05D9\u05DD': ('\u05E9\u05DE\u05DD', 'heavens'),
    '\u05D4\u05E9\u05DE\u05D9\u05DD': ('\u05E9\u05DE\u05DD', 'the\u00B7heavens'),
    '\u05DE\u05D9\u05DD': ('\u05DE\u05D9\u05DD', 'water'),
    '\u05D4\u05DE\u05D9\u05DD': ('\u05DE\u05D9\u05DD', 'the\u00B7waters'),
    '\u05D9\u05D5\u05DD': ('\u05D9\u05D5\u05DD', 'day'),
    '\u05D1\u05D9\u05D5\u05DD': ('\u05D9\u05D5\u05DD', 'on\u00B7the\u00B7day'),
    '\u05DC\u05D9\u05DC\u05D4': ('\u05DC\u05D9\u05DC', 'night'),
    '\u05D1\u05E7\u05E8': ('\u05D1\u05E7\u05E8', 'morning'),
    '\u05E2\u05E8\u05D1': ('\u05E2\u05E8\u05D1', 'evening'),
    '\u05D0\u05D5\u05E8': ('\u05D0\u05D5\u05E8', 'light'),
    '\u05D4\u05D0\u05D5\u05E8': ('\u05D0\u05D5\u05E8', 'the\u00B7light'),
    '\u05DC\u05D0\u05D5\u05E8': ('\u05D0\u05D5\u05E8', 'to\u00B7the\u00B7light'),
    '\u05D7\u05E9\u05DA': ('\u05D7\u05E9\u05DA', 'darkness'),
    '\u05D4\u05D7\u05E9\u05DA': ('\u05D7\u05E9\u05DA', 'the\u00B7darkness'),
    '\u05D0\u05D9\u05E9': ('\u05D0\u05D9\u05E9', 'man'),
    '\u05D4\u05D0\u05D9\u05E9': ('\u05D0\u05D9\u05E9', 'the\u00B7man'),
    '\u05D0\u05E9\u05D4': ('\u05D0\u05E9\u05D4', 'woman'),
    '\u05D4\u05D0\u05E9\u05D4': ('\u05D0\u05E9\u05D4', 'the\u00B7woman'),
    '\u05D0\u05E9\u05EA\u05D5': ('\u05D0\u05E9\u05D4', 'his\u00B7wife'),
    '\u05D1\u05DF': ('\u05D1\u05DF', 'son'),
    '\u05D1\u05E0\u05D5': ('\u05D1\u05DF', 'his\u00B7son'),
    '\u05D1\u05E0\u05D9': ('\u05D1\u05DF', 'sons\u00B7of'),
    '\u05D1\u05E0\u05EA': ('\u05D1\u05EA', 'daughter'),
    '\u05D1\u05E0\u05D5\u05EA': ('\u05D1\u05EA', 'daughters'),
    '\u05D0\u05D1': ('\u05D0\u05D1', 'father'),
    '\u05D0\u05D1\u05D9\u05D5': ('\u05D0\u05D1', 'his\u00B7father'),
    '\u05D0\u05D1\u05D9\u05DA': ('\u05D0\u05D1', 'your\u00B7father'),
    '\u05D0\u05DD': ('\u05D0\u05DD', 'mother'),
    '\u05D0\u05DE\u05D5': ('\u05D0\u05DD', 'his\u00B7mother'),
    '\u05D0\u05D7': ('\u05D0\u05D7', 'brother'),
    '\u05D0\u05D7\u05D9\u05D5': ('\u05D0\u05D7', 'his\u00B7brother'),
    '\u05E2\u05D1\u05D3': ('\u05E2\u05D1\u05D3', 'servant'),
    '\u05E2\u05D1\u05D3\u05D9\u05D5': ('\u05E2\u05D1\u05D3', 'his\u00B7servants'),
    '\u05E2\u05D1\u05D3\u05DA': ('\u05E2\u05D1\u05D3', 'your\u00B7servant'),
    '\u05E2\u05D9\u05E8': ('\u05E2\u05D9\u05E8', 'city'),
    '\u05D4\u05E2\u05D9\u05E8': ('\u05E2\u05D9\u05E8', 'the\u00B7city'),
    '\u05D1\u05D9\u05EA': ('\u05D1\u05D9\u05EA', 'house'),
    '\u05D4\u05D1\u05D9\u05EA': ('\u05D1\u05D9\u05EA', 'the\u00B7house'),
    '\u05E2\u05D9\u05DF': ('\u05E2\u05D9\u05DF', 'eye'),
    '\u05E2\u05D9\u05E0\u05D9': ('\u05E2\u05D9\u05DF', 'eyes\u00B7of'),
    '\u05D1\u05E2\u05D9\u05E0\u05D9': ('\u05E2\u05D9\u05DF', 'in\u00B7the\u00B7eyes\u00B7of'),
    '\u05D9\u05D3': ('\u05D9\u05D3', 'hand'),
    '\u05D9\u05D3\u05D5': ('\u05D9\u05D3', 'his\u00B7hand'),
    '\u05D1\u05D9\u05D3\u05D5': ('\u05D9\u05D3', 'in\u00B7his\u00B7hand'),
    '\u05DC\u05D1': ('\u05DC\u05D1', 'heart'),
    '\u05DC\u05D1\u05D5': ('\u05DC\u05D1', 'his\u00B7heart'),
    '\u05E0\u05E4\u05E9': ('\u05E0\u05E4\u05E9', 'soul'),
    '\u05DB\u05DC': ('\u05DB\u05DC', 'all'),
    '\u05D5\u05DB\u05DC': ('\u05DB\u05DC', 'and\u00B7all'),
    '\u05DC\u05DB\u05DC': ('\u05DB\u05DC', 'to\u00B7all'),
    '\u05DE\u05DB\u05DC': ('\u05DB\u05DC', 'from\u00B7all'),
    '\u05D1\u05DB\u05DC': ('\u05DB\u05DC', 'in\u00B7all'),
    # Particles
    '\u05DB\u05D9': ('\u05DB\u05D9', 'because'),
    '\u05D0\u05E9\u05E8': ('\u05D0\u05E9\u05E8', 'which'),
    '\u05D0\u05DC': ('\u05D0\u05DC', 'to'),
    '\u05DC\u05D0': ('\u05DC\u05D0', 'not'),
    '\u05D5\u05DC\u05D0': ('\u05DC\u05D0', 'and\u00B7not'),
    '\u05D2\u05DD': ('\u05D2\u05DD', 'also'),
    '\u05E2\u05D3': ('\u05E2\u05D3', 'until'),
    '\u05D1\u05D9\u05DF': ('\u05D1\u05D9\u05DF', 'between'),
    '\u05D5\u05D1\u05D9\u05DF': ('\u05D1\u05D9\u05DF', 'and\u00B7between'),
    '\u05D4\u05E0\u05D4': ('\u05D4\u05E0\u05D4', 'behold'),
    '\u05D5\u05D4\u05E0\u05D4': ('\u05D4\u05E0\u05D4', 'and\u00B7behold'),
    '\u05E2\u05D5\u05D3': ('\u05E2\u05D5\u05D3', 'still'),
    '\u05DC\u05DE\u05D4': ('\u05DE\u05D4', 'why'),
    '\u05DE\u05D4': ('\u05DE\u05D4', 'what'),
    # Pronouns
    '\u05D4\u05D5\u05D0': ('\u05D4\u05D5\u05D0', 'he'),
    '\u05D4\u05D9\u05D0': ('\u05D4\u05D9\u05D0', 'she'),
    '\u05D4\u05DD': ('\u05D4\u05DD', 'they'),
    '\u05D0\u05E0\u05D9': ('\u05D0\u05E0\u05D9', 'I'),
    '\u05D0\u05E0\u05DB\u05D9': ('\u05D0\u05E0\u05DB\u05D9', 'I'),
    '\u05D0\u05EA\u05D4': ('\u05D0\u05EA\u05D4', 'you'),
    '\u05D6\u05D4': ('\u05D6\u05D4', 'this'),
    '\u05D6\u05D0\u05EA': ('\u05D6\u05D0\u05EA', 'this'),
    # Numbers
    '\u05E9\u05E0\u05D4': ('\u05E9\u05E0\u05D4', 'year'),
    '\u05E9\u05E0\u05D9\u05DD': ('\u05E9\u05E0\u05D4', 'years'),
    '\u05E9\u05E0\u05EA': ('\u05E9\u05E0\u05D4', 'year\u00B7of'),
    '\u05DE\u05D0\u05EA': ('\u05DE\u05D0\u05D4', 'hundred'),
    '\u05DE\u05D0\u05D5\u05EA': ('\u05DE\u05D0\u05D4', 'hundreds'),
    '\u05E9\u05DC\u05E9': ('\u05E9\u05DC\u05E9', 'three'),
    '\u05D0\u05E8\u05D1\u05E2': ('\u05D0\u05E8\u05D1\u05E2', 'four'),
    '\u05D7\u05DE\u05E9': ('\u05D7\u05DE\u05E9', 'five'),
    '\u05E9\u05E9': ('\u05E9\u05E9', 'six'),
    '\u05E9\u05D1\u05E2': ('\u05E9\u05D1\u05E2', 'seven'),
    '\u05E9\u05DE\u05E0\u05D4': ('\u05E9\u05DE\u05E0\u05D4', 'eight'),
    '\u05EA\u05E9\u05E2': ('\u05EA\u05E9\u05E2', 'nine'),
    '\u05E2\u05E9\u05E8': ('\u05E2\u05E9\u05E8', 'ten'),
    '\u05E2\u05E9\u05E8\u05D4': ('\u05E2\u05E9\u05E8', 'ten'),
    '\u05E2\u05E9\u05E8\u05D9\u05DD': ('\u05E2\u05E9\u05E8', 'twenty'),
    '\u05E9\u05DC\u05E9\u05D9\u05DD': ('\u05E9\u05DC\u05E9', 'thirty'),
    '\u05D0\u05E8\u05D1\u05E2\u05D9\u05DD': ('\u05D0\u05E8\u05D1\u05E2', 'forty'),
    '\u05D7\u05DE\u05E9\u05D9\u05DD': ('\u05D7\u05DE\u05E9', 'fifty'),
    '\u05E9\u05E9\u05D9\u05DD': ('\u05E9\u05E9', 'sixty'),
    '\u05E9\u05D1\u05E2\u05D9\u05DD': ('\u05E9\u05D1\u05E2', 'seventy'),
    '\u05E9\u05DE\u05E0\u05D9\u05DD': ('\u05E9\u05DE\u05E0\u05D4', 'eighty'),
    '\u05EA\u05E9\u05E2\u05D9\u05DD': ('\u05EA\u05E9\u05E2', 'ninety'),
}

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fixed_eng = 0
fixed_root = 0

BAD_GLOSSES = {
    '(plural intensive-singular meaning)',
    'subst', 'adv', '(relative part.)',
    'sign of the definite direct object',
    'sign of the definite direct object not translated in English',
}

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_nikud(w['heb']).replace('\u05BE', '')

            if key in CORRECTIONS:
                new_root, new_eng = CORRECTIONS[key]
                if new_eng and (w['eng'] == '' or w['eng'] in BAD_GLOSSES):
                    w['eng'] = new_eng
                    fixed_eng += 1
                if new_root is not None and w['root'] == '':
                    w['root'] = new_root
                    fixed_root += 1

            # Catch remaining bad glosses globally
            if w['eng'] in BAD_GLOSSES or '(plural intensive' in w['eng']:
                if key in CORRECTIONS and CORRECTIONS[key][1]:
                    w['eng'] = CORRECTIONS[key][1]
                elif '(plural intensive' in w['eng']:
                    w['eng'] = 'God'
                    fixed_eng += 1

total_words = sum(len(v['words']) for c in d['chapters'] for v in c['verses'])
still_eng = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if w['eng'] == '')
still_root = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if w['root'] == '')

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed_eng} English glosses, {fixed_root} roots')
print(f'Still missing: {still_eng} eng ({still_eng/total_words*100:.1f}%), {still_root} roots ({still_root/total_words*100:.1f}%)')
print(f'Total words: {total_words}')
