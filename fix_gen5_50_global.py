#!/usr/bin/env python3
"""
Global systematic fixes for Genesis 5-50.
Instead of verse-by-verse, fix patterns that repeat hundreds of times.
"""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fixed = 0

# === Pass 1: Fix Hebrew text used as English glosses ===
HEBREW_TO_ENGLISH = {
    '\u05E1\u05E4\u05E8': 'book',          # ספר
    '\u05D3\u05DE\u05D5\u05EA': 'likeness', # דמות
    '\u05D1\u05EA': 'daughters',            # בת
    '\u05D5\u05D1\u05EA': 'and·daughters',  # ובת
    '\u05E6\u05DC\u05DD': 'image',          # צלם
    '\u05E0\u05E4\u05E9': 'soul',           # נפש
    '\u05DE\u05D1\u05D5\u05DC': 'flood',    # מבול
    '\u05EA\u05D1\u05D4': 'ark',            # תבה
    '\u05D0\u05DE\u05D4': 'cubit',          # אמה
    '\u05D2\u05E4\u05E8': 'gopher',         # גפר
    '\u05DB\u05E4\u05E8': 'pitch',          # כפר
    '\u05E7\u05E9\u05EA': 'bow',            # קשת
    '\u05D1\u05E8\u05D9\u05EA': 'covenant', # ברית
    '\u05DE\u05D6\u05D1\u05D7': 'altar',    # מזבח
    '\u05E2\u05D5\u05DC\u05D4': 'offering', # עולה
    '\u05E0\u05D9\u05D7\u05D7': 'pleasing', # ניחח
    '\u05E8\u05D9\u05D7': 'scent',          # ריח
}

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            if w['eng'] in HEBREW_TO_ENGLISH:
                w['eng'] = HEBREW_TO_ENGLISH[w['eng']]
                fixed += 1
            # Also check if eng is pure Hebrew characters
            if w['eng'] and all(('\u05D0' <= ch <= '\u05EA') or ch in ' \u00B7' for ch in w['eng']):
                key = w['eng'].replace('\u00B7', '')
                if key in HEBREW_TO_ENGLISH:
                    w['eng'] = HEBREW_TO_ENGLISH[key]
                    fixed += 1

# === Pass 2: Fix names in genealogy context ===
# When a name appears as first/second word in a genealogy verse, it's a name not a noun
NAME_FIXES = {
    'שת': 'Seth',
    'אנוש': 'Enosh',
    'קינן': 'Kenan',
    'מהללאל': 'Mahalalel',
    'ירד': 'Jared',
    'חנוך': 'Enoch',
    'מתושלח': 'Methuselah',
    'למך': 'Lamech',
    'נח': 'Noah',
    'שם': 'Shem',
    'חם': 'Ham',
    'יפת': 'Japheth',
    'תרח': 'Terah',
    'אברם': 'Abram',
    'נחור': 'Nahor',
    'הרן': 'Haran',
    'שרי': 'Sarai',
    'לוט': 'Lot',
}

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if key in NAME_FIXES:
                current = w['eng']
                correct = NAME_FIXES[key]
                # Only fix if current gloss is wrong (not already the name)
                if current != correct and current in (
                    'seat of body', 'seat', 'man', 'go down', 'rest',
                    'dedicated', 'complete', 'there', 'hot', 'Shem',
                    'leave', 'spear', 'princess', 'wrap up', 'delay',
                    key,  # Hebrew used as gloss
                ):
                    w['eng'] = correct
                    fixed += 1

# === Pass 3: Fix maqaf compounds with names ===
# "and·live·seat" -> "and·Seth·lived" etc.
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            # "and·live·seat" or "and·lived·seat" patterns
            if 'seat' in e and ('live' in e or 'lived' in e):
                w['eng'] = e.replace('seat of body', 'Seth').replace('seat', 'Seth')
                fixed += 1
            # "all·day·seat" -> "all·the·days·of·Seth"
            if 'day\u00B7seat' in e:
                w['eng'] = e.replace('day\u00B7seat', 'days·of·Seth')
                fixed += 1
            # "day·man" in genealogy context -> "the·days·of·Adam"
            if e == 'day\u00B7man' or e == 'day\u00B7Adam':
                w['eng'] = 'the·days·of·Adam'
                fixed += 1

# === Pass 4: Fix common wrong glosses ===
WRONG_GLOSSES = {
    'seat of body': 'Seth',
    'seat': 'Seth',
    'n m': None,       # needs context
    'n m/f': None,     # needs context
    'n f': None,       # needs context
    'son': None,       # check if it's ברא=created
    'remember': None,  # check if it's זכר=male
    'adj': None,       # already mostly fixed but check
    'go in': 'brought',
    'interr pron': 'why',
    'interrog adv': 'why',
}

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')

            # ברא = "created" not "son"
            if e == 'son' and 'ברא' in key and 'בן' not in key:
                w['eng'] = 'created'
                fixed += 1

            # זכר = "male" in creation context, "remember" elsewhere
            if e == 'remember' and key == 'זכר':
                trans = v.get('translation', '').lower()
                if 'male' in trans:
                    w['eng'] = 'male'
                    fixed += 1

            # which·adj -> which·lived
            if e == 'which\u00B7adj' or e == 'which\u00B7living':
                w['eng'] = 'which·he·lived'
                fixed += 1

            # "and·was" for ויהיו -> "and·were" (plural)
            if e == 'and·was' and 'ויהיו' in key:
                w['eng'] = 'and·were'
                fixed += 1

# === Pass 5: Fix remaining "n m/f" and "n m" with context ===
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')
            if e in ('n m', 'n m/f', 'n f'):
                if 'גן' in key: w['eng'] = 'garden'
                elif 'נהר' in key: w['eng'] = 'river'
                elif 'עיר' in key: w['eng'] = 'city'
                elif 'שם' in key: w['eng'] = 'name'
                elif 'קדם' in key: w['eng'] = 'east'
                elif 'מבול' in key: w['eng'] = 'flood'
                elif 'תבה' in key: w['eng'] = 'ark'
                elif 'מגדל' in key: w['eng'] = 'tower'
                elif 'לבנה' in key: w['eng'] = 'brick'
                elif 'חמר' in key: w['eng'] = 'tar'
                elif w.get('root'): w['eng'] = w['root']
                else: w['eng'] = key
                fixed += 1

# === Pass 6: Fix "bore" that should be "begot" for fathers ===
# In genealogies, הוליד = "begot" (caused to be born), not "bore"
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if w['eng'] == 'bore' and 'הוליד' in key:
                w['eng'] = 'begot'
                fixed += 1

# === Pass 7: Fix [identifies object] for maqaf compounds ===
# Already done globally but check remaining
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            # Standalone [identifies object] for את + name compound
            if e == '[identifies object]' and '\u05BE' in w['heb']:
                parts = w['heb'].split('\u05BE')
                if len(parts) >= 2:
                    second = strip_n(parts[-1])
                    if second in NAME_FIXES:
                        w['eng'] = NAME_FIXES[second]
                        fixed += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Count remaining issues
remaining_hebrew = 0
remaining_nm = 0
remaining_wrong = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            if e and all(('\u05D0' <= ch <= '\u05EA') for ch in e.replace('\u00B7', '').replace(' ', '')):
                remaining_hebrew += 1
            if e in ('n m', 'n m/f', 'n f'):
                remaining_nm += 1
            if e in ('adj', 'seat', 'seat of body', 'spear', 'bind'):
                remaining_wrong += 1

print(f"Fixed {fixed} entries globally")
print(f"Remaining: Hebrew-as-English={remaining_hebrew}, n_m/f={remaining_nm}, known_wrong={remaining_wrong}")

# Show Gen 5:1-8 as sample
print("\nGen 5:1-8:")
for v in d['chapters'][4]['verses'][:8]:
    print(f'\n{v["ref"]}:')
    for w in v['words']:
        print(f'  {w["heb"]:20s}  {w["eng"]}')
