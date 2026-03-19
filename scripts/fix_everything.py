#!/usr/bin/env python3
"""
THE FINAL FIX. Goes through every single word in Genesis.
1. Fills ALL missing roots from Sefaria word lookup cache
2. Fixes wrong roots (like איל for אל)
3. Fixes translations that don't match the verse translation
"""
import json, re, sys, os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

CACHE_DIR = Path("sefaria_cache")

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# === STEP 1: Build root dictionary from Sefaria cache ===
# The cache has word lookups with headwords (roots)
root_dict = {}
for cache_file in CACHE_DIR.glob("word_*.json"):
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            entry = data[0]
            if isinstance(entry, dict):
                headword = entry.get('headword', '')
                if headword:
                    root = strip_n(headword)
                    root = ''.join(c for c in root if '\u05D0' <= c <= '\u05EA')
                    if 2 <= len(root) <= 4:
                        # Get the lookup word from filename
                        fname = cache_file.stem  # word_XXXXX
                        key = fname.replace('word_', '')
                        root_dict[key] = root
    except:
        pass

print(f"Loaded {len(root_dict)} roots from cache")

# === STEP 2: Known correct roots for common words ===
KNOWN_ROOTS = {
    'בראשית': '\u05E8\u05D0\u05E9',  # ראש
    'ברא': '\u05D1\u05E8\u05D0',     # ברא
    'אלהים': '\u05D0\u05DC\u05D4',   # אלה
    'את': '\u05D0\u05EA',             # את
    'השמים': '\u05E9\u05DE\u05DD',    # שמם
    'הארץ': '\u05D0\u05E8\u05E5',     # ארץ
    'ארץ': '\u05D0\u05E8\u05E5',
    'היה': '\u05D4\u05D9\u05D4',
    'אמר': '\u05D0\u05DE\u05E8',
    'ראה': '\u05E8\u05D0\u05D4',
    'עשה': '\u05E2\u05E9\u05D4',
    'נתן': '\u05E0\u05EA\u05DF',
    'לקח': '\u05DC\u05E7\u05D7',
    'הלך': '\u05D4\u05DC\u05DA',
    'בוא': '\u05D1\u05D5\u05D0',
    'ישב': '\u05D9\u05E9\u05D1',
    'שמע': '\u05E9\u05DE\u05E2',
    'ידע': '\u05D9\u05D3\u05E2',
    'דבר': '\u05D3\u05D1\u05E8',
    'קרא': '\u05E7\u05E8\u05D0',
    'שלח': '\u05E9\u05DC\u05D7',
    'מות': '\u05DE\u05D5\u05EA',
    'חיה': '\u05D7\u05D9\u05D4',
    'ילד': '\u05D9\u05DC\u05D3',
    'שוב': '\u05E9\u05D5\u05D1',
    'עלה': '\u05E2\u05DC\u05D4',
    'ירד': '\u05D9\u05E8\u05D3',
    'יצא': '\u05D9\u05E6\u05D0',
    'בנה': '\u05D1\u05E0\u05D4',
    'ברך': '\u05D1\u05E8\u05DA',
    'קום': '\u05E7\u05D5\u05DD',
    'שים': '\u05E9\u05D9\u05DD',
    'אכל': '\u05D0\u05DB\u05DC',
    'מצא': '\u05DE\u05E6\u05D0',
    'שבע': '\u05E9\u05D1\u05E2',
    'מלך': '\u05DE\u05DC\u05DA',
    'עבד': '\u05E2\u05D1\u05D3',
    'עבר': '\u05E2\u05D1\u05E8',
    'נשא': '\u05E0\u05E9\u05D0',
    'פקד': '\u05E4\u05E7\u05D3',
    'צוה': '\u05E6\u05D5\u05D4',
    'כרת': '\u05DB\u05E8\u05EA',
    'שפט': '\u05E9\u05E4\u05D8',
    'אהב': '\u05D0\u05D4\u05D1',
    'ירא': '\u05D9\u05E8\u05D0',
    'שכב': '\u05E9\u05DB\u05D1',
    'גדל': '\u05D2\u05D3\u05DC',
    'מלא': '\u05DE\u05DC\u05D0',
    'קבר': '\u05E7\u05D1\u05E8',
    'זכר': '\u05D6\u05DB\u05E8',
    'חטא': '\u05D7\u05D8\u05D0',
    'נגד': '\u05E0\u05D2\u05D3',
    'נפל': '\u05E0\u05E4\u05DC',
    'בכה': '\u05D1\u05DB\u05D4',
    'רוח': '\u05E8\u05D5\u05D7',
    'נפש': '\u05E0\u05E4\u05E9',
    'דם': '\u05D3\u05DD',
    'אב': '\u05D0\u05D1',
    'אם': '\u05D0\u05DD',
    'בן': '\u05D1\u05DF',
    'בת': '\u05D1\u05EA',
    'אח': '\u05D0\u05D7',
    'איש': '\u05D0\u05D9\u05E9',
    'אשה': '\u05D0\u05E9\u05D4',
    'שם': '\u05E9\u05DD',
    'יד': '\u05D9\u05D3',
    'עין': '\u05E2\u05D9\u05DF',
    'לב': '\u05DC\u05D1',
    'פנה': '\u05E4\u05E0\u05D4',
    'כל': '\u05DB\u05DC',
    'על': '\u05E2\u05DC',
    'אל': '\u05D0\u05DC',
    'מים': '\u05DE\u05D9\u05DD',
    'יום': '\u05D9\u05D5\u05DD',
    'שנה': '\u05E9\u05E0\u05D4',
    'בית': '\u05D1\u05D9\u05EA',
    'עיר': '\u05E2\u05D9\u05E8',
    'דרך': '\u05D3\u05E8\u05DA',
    'טוב': '\u05D8\u05D5\u05D1',
    'רע': '\u05E8\u05E2',
    'גדול': '\u05D2\u05D3\u05DC',
    'חסד': '\u05D7\u05E1\u05D3',
    'משפט': '\u05E9\u05E4\u05D8',
    'כהן': '\u05DB\u05D4\u05DF',
}

# === STEP 3: Fix wrong root 'איל' (ram) for 'אל' (to) ===
WRONG_ROOTS = {
    '\u05D0\u05D9\u05DC': {  # איל (ram) — often wrong for אל
        'to': '\u05D0\u05DC',
        'to·him': '\u05D0\u05DC',
        'to·her': '\u05D0\u05DC',
        'to·them': '\u05D0\u05DC',
        'to·me': '\u05D0\u05DC',
        'to·you': '\u05D0\u05DC',
        'to·us': '\u05D0\u05DC',
        'to·Abram': '\u05D0\u05DC',
        'to·Abraham': '\u05D0\u05DC',
        'to·Jacob': '\u05D0\u05DC',
        'to·Laban': '\u05D0\u05DC',
        'to·Noah': '\u05D0\u05DC',
        'to·Pharaoh': '\u05D0\u05DC',
        'to·Joseph': '\u05D0\u05DC',
        'to·Isaac': '\u05D0\u05DC',
        'to·Esau': '\u05D0\u05DC',
        'to·Cain': '\u05D0\u05DC',
        'to·brother': '\u05D0\u05D7',
        'to·earth': '\u05D0\u05E8\u05E5',
        'to·man': '\u05D0\u05D3\u05DD',
    },
}

# === STEP 4: Apply fixes ===
roots_fixed = 0
roots_wrong_fixed = 0

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')

            # Fix missing roots
            if not w['root']:
                # Try known roots
                if key in KNOWN_ROOTS:
                    w['root'] = KNOWN_ROOTS[key]
                    roots_fixed += 1
                # Try cache lookup (strip prefixes)
                else:
                    for pfx_len in range(0, min(4, len(key))):
                        subkey = key[pfx_len:]
                        if subkey in KNOWN_ROOTS:
                            w['root'] = KNOWN_ROOTS[subkey]
                            roots_fixed += 1
                            break
                        if subkey in root_dict:
                            w['root'] = root_dict[subkey]
                            roots_fixed += 1
                            break

            # Fix wrong roots
            if w['root'] in WRONG_ROOTS:
                eng = w['eng']
                corrections = WRONG_ROOTS[w['root']]
                for eng_pattern, correct_root in corrections.items():
                    if eng == eng_pattern or eng.startswith(eng_pattern.split('\u00B7')[0]):
                        w['root'] = correct_root
                        roots_wrong_fixed += 1
                        break

# === STEP 5: Fix remaining wrong translations using verse context ===
# These are specific known-wrong patterns
trans_fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        trans = v.get('translation', '').lower()
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')

            # "to verb" remaining
            if e.startswith('to ') and len(e) > 5 and '\u00B7' not in e:
                if e in ('to him','to her','to them','to us','to you','to me',
                         'to Noah','to Abraham','to Jacob','to Laban','to Pharaoh',
                         'to Joseph','to Isaac','to Esau','to Cain','to make',
                         'to place','to lodge','to Paddan','to Egypt','to Abram',
                         'to God','to YHWH','to Shem','to Sarah','to Lot'):
                    continue
                # Convert to past tense
                verb = e[3:]
                w['eng'] = verb
                trans_fixed += 1

            # Specific wrong words
            if e == 'unto·thee·unto' and 'לךלך' in key:
                w['eng'] = 'go·for·yourself'; trans_fixed += 1
            elif e == 'land' and 'מארצך' in key:
                w['eng'] = 'from·your·land'; trans_fixed += 1
            elif e == 'kindred' and 'ממולדתך' in key:
                w['eng'] = 'from·your·kindred'; trans_fixed += 1
            elif e == 'name' and 'מבית' in key:
                w['eng'] = 'from·the·house·of'; trans_fixed += 1
            elif e == 'another' and key == 'אחר' and 'after' in trans:
                w['eng'] = 'after'; trans_fixed += 1
            elif e == 'the under part' and 'תחת' in key:
                w['eng'] = 'beneath'; trans_fixed += 1
            elif e == 'abundance' and ('להם' in key or 'מהם' in key):
                if 'to·them' not in e:
                    w['eng'] = 'from·them' if 'מהם' in key else 'to·them'
                    trans_fixed += 1
            elif e == 'above' and 'מעל' in key and 'from' in trans:
                w['eng'] = 'from·upon'; trans_fixed += 1
            elif e == 'above·face' and 'עלפני' in key:
                w['eng'] = 'upon·the·face·of'; trans_fixed += 1
            elif e == 'weapon' and 'שלח' in key:
                w['eng'] = 'and·sent'; trans_fixed += 1
            elif e == 'built' and 'מבנות' in key:
                w['eng'] = 'from·the·daughters·of'; trans_fixed += 1
            elif e == 'profane' and 'החל' in key:
                w['eng'] = 'began'; trans_fixed += 1
            elif e == 'nation' and key == 'עם' and 'people' in trans:
                w['eng'] = 'people'; trans_fixed += 1
            elif e == 'lip' and 'שפה' in key and 'language' in trans:
                w['eng'] = 'language'; trans_fixed += 1
            elif e == 'standing place' and 'מקום' in key:
                w['eng'] = 'place'; trans_fixed += 1
            elif e == 'standing' and 'מקום' in key:
                w['eng'] = 'place'; trans_fixed += 1

# Protect Gen 1:1
v1 = d['chapters'][0]['verses'][0]
v1['words'][0]['root'] = '\u05E8\u05D0\u05E9'  # ראש

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

total = sum(len(v['words']) for c in d['chapters'] for v in c['verses'])
still_missing = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if not w['root'])

print(f"Roots fixed: {roots_fixed}")
print(f"Wrong roots fixed: {roots_wrong_fixed}")
print(f"Translations fixed: {trans_fixed}")
print(f"Still missing roots: {still_missing} ({still_missing*100//total}%)")
