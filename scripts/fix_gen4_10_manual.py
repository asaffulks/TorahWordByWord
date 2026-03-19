#!/usr/bin/env python3
"""Hand-correct Genesis chapters 4-10. Focus on systematic errors
that repeat across many verses."""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# === GLOBAL fixes across ALL chapters (not just 4-10) ===
# These are systematic errors from wrong Sefaria lexicon entries

GLOBAL_WORD_FIXES = {
    # Names wrongly glossed as common nouns
    'קין': 'Cain',
    'לקין': 'to·Cain',
    'וקין': 'and·Cain',
    'הבל': 'Abel',
    'והבל': 'and·Abel',
    'שת': 'Seth',
    'אנוש': 'Enosh',
    'חנוך': 'Enoch',
    'מתושלח': 'Methuselah',
    'למך': 'Lamech',
    'ולמך': 'and·Lamech',
    'נח': 'Noah',
    'לנח': 'to·Noah',
    'שם': 'Shem',  # context-dependent but mostly Shem in genealogies
    'חם': 'Ham',
    'יפת': 'Japheth',
    'ויפת': 'and·Japheth',
    'נמרד': 'Nimrod',
    'כנען': 'Canaan',
    'וכנען': 'and·Canaan',
    'מצרים': 'Egypt',
    'עדן': 'Eden',
    'בעדן': 'in·Eden',

    # Wrong common word glosses
    'פרת': 'Euphrates',  # NOT "be fruitful"
    'אדמה': 'ground',  # NOT "red"
    'האדמה': 'the·ground',
    'מןהאדמה': 'from·the·ground',
    'עלהאדמה': 'upon·the·ground',
    'גן': 'garden',
    'הגן': 'the·garden',
    'בגן': 'in·the·garden',
    'רעה': 'shepherd',  # context: Abel was a shepherd
    'יצר': 'formed',  # NOT "bind"
    'נהר': 'river',  # NOT "stream"
    'הנהר': 'the·river',
    'שנה': 'year',
    'שנים': 'years',

    # "n m" and "n m/f" junk
    # These need context but let's fix the most common

    # "god" for אל when it means "to"
    # Already mostly fixed but check compounds

    # "prep" prefix
    # Already mostly fixed

    # Wrong verb forms
    'חרה': 'was·angry',  # NOT "be hot"
    'ירד': 'went·down',
    'עלה': 'went·up',
    'נפל': 'fell',
    'שעה': 'regarded',  # NOT "look at"
    'הביא': 'brought',  # NOT "go in"
    'גרש': 'drove·out',
    'הרג': 'killed',
    'קנה': 'acquired',  # NOT "get" or "spear"
    'ידע': 'knew',
    'עשה': 'did',  # past tense
}

# Apply global fixes
fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            e = w['eng']

            if key in GLOBAL_WORD_FIXES:
                correct = GLOBAL_WORD_FIXES[key]
                # Only fix if current gloss is clearly wrong
                if e in ('spear', 'n m', 'n m/f', 'n f', 'bind', 'stream',
                         'red', 'luxury', 'be hot', 'go in', 'look at',
                         'get', 'be·fruitful', 'David'):
                    w['eng'] = correct
                    fixed += 1
                elif e == key:  # Hebrew used as English gloss
                    w['eng'] = correct
                    fixed += 1

# Fix "god" when it should be "to" (אל as preposition, not deity)
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')

            # "god·NOUN" compounds where אל is preposition
            if e.startswith('god\u00B7') and 'אל' in key:
                rest = e[4:]  # after "god·"
                w['eng'] = 'to\u00B7' + rest
                fixed += 1
            elif e == 'god' and len(key) <= 4 and 'אל' in key and 'אלהים' not in key:
                w['eng'] = 'to'
                fixed += 1

# Fix "prep·NOUN" remaining
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            if w['eng'].startswith('prep\u00B7'):
                w['eng'] = 'from\u00B7' + w['eng'][5:]
                fixed += 1
            elif w['eng'] == 'prep':
                w['eng'] = 'from'
                fixed += 1

# Fix "n m", "n m/f", "n f" used as glosses
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')
            if e in ('n m', 'n m/f', 'n f'):
                # Try to use root or a reasonable guess
                if 'גן' in key: w['eng'] = 'garden'
                elif 'נהר' in key: w['eng'] = 'river'
                elif 'עיר' in key: w['eng'] = 'city'
                elif 'שם' in key: w['eng'] = 'name'
                elif 'קדם' in key: w['eng'] = 'east'
                elif w.get('root'):
                    w['eng'] = w['root']
                else:
                    w['eng'] = key
                fixed += 1
            # "n m·SOMETHING" compounds
            elif '\u00B7n m' in e or 'n m\u00B7' in e:
                w['eng'] = e.replace('n m/f', 'garden').replace('n m', 'name')
                fixed += 1

# Fix "interr pron" and "interr·pron"
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            if 'interr' in w['eng']:
                w['eng'] = 'why'
                fixed += 1

# Fix "you" for הוא (should be "he")
# Already done in deep_fix but some compounds remain
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if w['eng'] == 'you' and 'הוא' in key:
                w['eng'] = 'he'
                fixed += 1
            elif w['eng'] == 'also\u00B7you' and 'גם' in key and 'הוא' in key:
                w['eng'] = 'also\u00B7he'
                fixed += 1

# === Specific Gen 4 verse fixes ===
ch4 = d['chapters'][3]
V4 = [
    (1, 0, 'and·the·man'),
    (1, 1, 'knew'),
    (1, 2, 'Eve'),
    (1, 8, 'I·have·acquired'),
    (2, 0, 'and·she·continued'),
    (2, 1, 'to·bear'),
    (2, 2, 'his·brother'),
    (2, 3, 'Abel'),
    (2, 4, 'and·Abel·was'),
    (2, 5, 'a·keeper·of'),
    (2, 7, 'and·Cain'),
    (2, 9, 'a·tiller·of'),
    (2, 10, 'the·ground'),
    (3, 1, 'at·the·end·of'),
    (3, 3, 'and·brought'),
    (3, 5, 'of·the·fruit·of'),
    (3, 7, 'an·offering'),
    (4, 0, 'and·Abel'),
    (4, 1, 'brought'),
    (4, 2, 'also·he'),
    (4, 3, 'of·the·firstborn·of'),
    (4, 5, 'and·of·their·fat'),
    (4, 6, 'and·YHWH·regarded'),
    (4, 8, 'Abel'),
    (4, 9, 'and·his·offering'),
    (5, 0, 'but·to·Cain'),
    (5, 1, 'and·his·offering'),
    (5, 3, 'did·not·regard'),
    (5, 5, 'to·Cain'),
    (5, 7, 'and·fell'),
    (5, 9, 'his·face'),
    (6, 2, 'to·Cain'),
    (6, 4, 'are·you·angry'),
    (6, 6, 'and·why'),
    (6, 7, 'has·fallen'),
    (6, 9, 'your·face'),
    (7, 1, 'if·you·do·well'),
    (7, 2, 'uplift'),
    (7, 5, 'do·well'),
    (7, 6, 'at·the·door'),
    (7, 7, 'sin'),
    (7, 8, 'crouches'),
    (7, 9, 'and·to·you'),
    (7, 10, 'its·desire'),
    (8, 1, 'Cain'),
    (8, 2, 'to·Abel'),
    (8, 5, 'when·they·were'),
    (8, 8, 'Cain'),
    (8, 9, 'against·Abel'),
    (8, 11, 'and·killed·him'),
    (9, 2, 'to·Cain'),
    (9, 3, 'where·is'),
    (9, 4, 'Abel'),
    (9, 9, 'am·I'),
    (9, 10, 'my·brother\'s'),
    (9, 11, 'keeper'),
    (10, 1, 'what'),
    (10, 2, 'have·you·done'),
    (10, 4, 'the·blood·of'),
    (10, 6, 'cries·out'),
    (10, 8, 'from·the·ground'),
    (11, 1, 'cursed'),
    (11, 3, 'from·the·ground'),
    (11, 5, 'opened'),
    (11, 6, 'her·mouth'),
    (11, 7, 'to·receive'),
    (11, 8, 'the·blood·of'),
    (11, 10, 'from·your·hand'),
    (12, 0, 'when'),
    (12, 1, 'you·till'),
    (12, 2, 'the·ground'),
    (12, 3, 'not·again'),
    (12, 4, 'give·its·strength'),
    (12, 6, 'a·wanderer'),
    (12, 7, 'and·fugitive'),
    (12, 8, 'you·shall·be'),
    (13, 1, 'Cain'),
    (13, 3, 'great·is'),
    (13, 4, 'my·punishment'),
    (13, 5, 'to·bear'),
    (14, 0, 'behold'),
    (14, 4, 'from·upon'),
    (14, 5, 'the·face·of'),
    (14, 7, 'and·from·your·face'),
    (14, 8, 'I·shall·hide'),
    (14, 9, 'and·I·shall·be'),
    (14, 14, 'all·who·find·me'),
    (14, 15, 'will·kill·me'),
    (15, 1, 'to·him'),
    (15, 3, 'therefore'),
    (15, 4, 'anyone·who·kills'),
    (15, 5, 'Cain'),
    (15, 10, 'to·Cain'),
    (15, 13, 'striking·him'),
    (15, 14, 'anyone·who·finds·him'),
    (16, 1, 'Cain'),
    (16, 2, 'from·the·presence·of'),
]

for verse_num, word_idx, correct in V4:
    v = ch4['verses'][verse_num - 1]
    if word_idx < len(v['words']):
        v['words'][word_idx]['eng'] = correct

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Verify
print(f"Fixed {fixed} global entries")
print("\nGen 4:1-4 after correction:")
for v in ch4['verses'][:4]:
    print(f'\n{v["ref"]}:')
    for w in v['words']:
        print(f'  {w["heb"]:20s}  {w["eng"]}')
