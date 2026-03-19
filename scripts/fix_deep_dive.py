#!/usr/bin/env python3
"""Fix all 133 issues from deep dive audit."""
import json, re, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(BASE / 'references' / 'etcbc_exodus_by_verse.json', 'r', encoding='utf-8') as f:
    etcbc = json.load(f)

fixed = 0

# Direct replacements
DIRECT = {
    'I (first pers. sing. -usually used for emphasis)': 'I',
    'to divide by six; to multiply by six': 'six',
    "Ma\u02BF\u0103lath M\u2019ra. Targ. Y. I Num. XXXII": 'steps',
    'woe': 'and',
}

# Compound POS fixes
COMPOUND = {
    'if\u00B7n f': 'if\u00B7daughter',
    'all\u00B7n f': 'all\u00B7the\u00B7daughters',
    'n f\u00B7Pharaoh': 'daughter\u00B7of\u00B7Pharaoh',
    'or\u00B7n f': 'or\u00B7daughter',
    'if\u00B7n m': 'if\u00B7remains',
    'all\u00B7n m': 'all\u00B7the\u00B7nations',
    'n m\u00B7fire': 'roasted\u00B7by\u00B7fire',
    'mother\u00B7n m\u00B7fire': 'but\u00B7roasted\u00B7by\u00B7fire',
    'to\u00B7n m': 'do\u00B7not\u00B7leave\u00B7over',
    '(relative part.)\u00B7Egypt': 'which\u00B7in\u00B7Egypt',
    '(object marker)\u00B7all\u00B7(relative part': '(object marker)\u00B7all\u00B7that\u00B7in\u00B7it',
    'and\u00B7(object marker)\u00B7<those unable to march>': 'and\u00B7(object marker)\u00B7your\u00B7little\u00B7ones',
    'and\u00B7(object marker)\u00B7smoke of sacrifice': 'and\u00B7(object marker)\u00B7incense',
}

# Truncated word fixes by consonantal form
TRUNC = {
    'בחמר': 'with\u00B7bitumen',
    'לנחש': 'into\u00B7a\u00B7serpent',
    'במכסת': 'according\u00B7to',
    'מיום': 'from\u00B7the\u00B7day',
    'מגדל': 'Migdol',
    'כיאני': 'for\u00B7I',
    'בקצהו': 'at\u00B7its\u00B7edge',
    'בקול': 'with\u00B7a\u00B7voice',
    'ראיתם': 'you\u00B7have\u00B7seen',
    'ערותך': 'your\u00B7nakedness',
    'לאדניה': 'to\u00B7her\u00B7master',
    'יעדה': 'designated\u00B7her',
    'סביב': 'around',
    'נחשת': 'bronze',
    'מצות': 'unleavened\u00B7bread',
    'מבקש': 'seeking',
    'פעמתיו': 'its\u00B7feet',
    'הכפרת': 'the\u00B7mercy\u00B7seat',
    'תשביתו': 'you\u00B7shall\u00B7remove',
    'לגלגלת': 'per\u00B7head',
    'וילדיה': 'and\u00B7her\u00B7children',
    'העמודים': 'the\u00B7pillars',
    'תעשהלי': 'you\u00B7shall\u00B7make\u00B7for\u00B7me',
    'יהיהעוד': 'shall\u00B7be\u00B7again',
    'אלתאכל': 'do\u00B7not\u00B7eat',
    'אתארצך': '(object marker)\u00B7your\u00B7land',
    'לאתבנה': 'you\u00B7shall\u00B7not\u00B7build',
    'מןהמחנה': 'from\u00B7the\u00B7camp',
    'בכלהמקום': 'in\u00B7every\u00B7place',
    'לפיאכלו': 'according\u00B7to\u00B7his\u00B7eating',
    'נעליכם': 'your\u00B7sandals',
    'אדירים': 'mighty\u00B7waters',
    'אלהאלהים': 'to\u00B7God',
    'אלהאלהם': 'to\u00B7God',
    'תשברעולחם': 'you\u00B7shall\u00B7be\u00B7satisfied\u00B7with\u00B7bread',
    'ואתבדיו': 'and\u00B7(object marker)\u00B7its\u00B7poles',
    'עלארון': 'upon\u00B7the\u00B7ark',
}

for ch in data['chapters']:
    for v in ch['verses']:
        ref = f"{ch['chapter']}:{v['verse']}"
        for w in v.get('words', []):
            e = w['eng']
            h_cons = strip_n(w['heb']).replace('\u05BE', '')

            # Direct replacements
            if e in DIRECT:
                w['eng'] = DIRECT[e]
                fixed += 1
                continue

            # Compound POS
            if e in COMPOUND:
                w['eng'] = COMPOUND[e]
                fixed += 1
                continue

            # prep dot X -> from dot X
            if e.startswith('prep\u00B7'):
                w['eng'] = 'from\u00B7' + e[5:]
                fixed += 1
                continue

            # perpetuity dot X -> until dot X
            if e.startswith('perpetuity\u00B7'):
                w['eng'] = 'until\u00B7' + e[11:]
                fixed += 1
                continue

            # Truncated by consonantal form
            if h_cons in TRUNC and e in ('and', 'to', 'in', 'from', 'the', 'not', 'upon'):
                w['eng'] = TRUNC[h_cons]
                fixed += 1
                continue

            # Marginal reading
            if w['heb'] == '(\u05D5\u05D9\u05DC\u05D9\u05E0\u05D5)' and e == 'and':
                w['eng'] = 'and\u00B7complained'
                fixed += 1
                continue

            # face dot turban -> face of turban (pnei compound)
            if 'face\u00B7turban' in e:
                w['eng'] = e.replace('face\u00B7turban', 'front\u00B7of\u00B7the\u00B7turban')
                fixed += 1
                continue

print(f"Fixed: {fixed}")

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Saved")
