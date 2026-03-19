#!/usr/bin/env python3
"""
Fix את compound words — translate the noun after the object marker.
====================================================================
Words like אֶת־אָבִיךָ should show "(object marker)·your·father"
not just "(object marker)".

Uses ETCBC glosses + master dictionary to fill in the noun.
"""
import json, re, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Master noun dictionary: consonantal Hebrew -> English
NOUN_DICT = {
    'אביך': 'your·father', 'אמך': 'your·mother',
    'אביו': 'his·father', 'אמו': 'his·mother',
    'אבתיך': 'your·fathers', 'אבתם': 'their·fathers',
    'אשתו': 'his·wife', 'אשתי': 'my·wife',
    'בניו': 'his·sons', 'בנו': 'his·son', 'בני': 'sons·of',
    'בנתיו': 'his·daughters', 'בנתיך': 'your·daughters',
    'בנים': 'sons', 'בנות': 'daughters',
    'ישראל': 'Israel', 'בניישראל': 'children·of·Israel',
    'מצרים': 'Egypt', 'פרעה': 'Pharaoh',
    'משה': 'Moses', 'אהרן': 'Aaron',
    'יהוה': 'the·LORD',
    'הארץ': 'the·earth', 'ארץ': 'land',
    'השמים': 'the·heavens', 'הים': 'the·sea',
    'המים': 'the·waters', 'הדם': 'the·blood',
    'העם': 'the·people', 'עמי': 'my·people', 'עמו': 'his·people',
    'האיש': 'the·man', 'האשה': 'the·woman',
    'הבית': 'the·house', 'ביתו': 'his·house',
    'ידו': 'his·hand', 'ידיהם': 'their·hands', 'ידיך': 'your·hands',
    'רגליו': 'his·feet', 'רגליהם': 'their·feet',
    'עיניו': 'his·eyes', 'עיניך': 'your·eyes',
    'ראשו': 'his·head', 'ראשם': 'their·heads',
    'לבו': 'his·heart', 'לב': 'heart', 'לבב': 'heart',
    'שמו': 'his·name', 'שמי': 'my·name', 'שמך': 'your·name',
    'דברי': 'words·of', 'הדברים': 'the·words',
    'כלי': 'vessels·of', 'כליו': 'its·vessels', 'כליה': 'her·vessels',
    'עבדיו': 'his·servants', 'עבדך': 'your·servant', 'עבדי': 'my·servant',
    'בגדיו': 'his·garments', 'הבגדים': 'the·garments',
    'הזהב': 'the·gold', 'הכסף': 'the·silver', 'הנחשת': 'the·bronze',
    'השלחן': 'the·table', 'המנרה': 'the·lampstand',
    'המזבח': 'the·altar', 'הארן': 'the·ark', 'הארון': 'the·ark',
    'המשכן': 'the·tabernacle', 'אהל': 'the·tent',
    'הכפרת': 'the·mercy·seat', 'הכיר': 'the·basin', 'הכיור': 'the·basin',
    'העלה': 'the·burnt·offering', 'החטאת': 'the·sin·offering',
    'הפרכת': 'the·veil', 'המסך': 'the·screen',
    'הלחם': 'the·bread', 'השמן': 'the·oil',
    'החשן': 'the·breastpiece', 'האפד': 'the·ephod',
    'התכלת': 'the·blue', 'הארגמן': 'the·purple',
    'תולעת': 'scarlet', 'השש': 'the·fine·linen',
    'הנרת': 'the·lamps', 'נרתיה': 'its·lamps',
    'קרסיו': 'its·clasps', 'קרשיו': 'its·boards',
    'בריחו': 'its·bars', 'עמדיו': 'its·pillars', 'אדניו': 'its·bases',
    'בדיו': 'its·poles', 'כנו': 'its·base',
    'רכבו': 'his·chariot', 'חילו': 'his·army',
    'הרכב': 'the·chariot', 'הפרשים': 'the·horsemen',
    'מקנהו': 'his·livestock', 'מקני': 'my·livestock',
    'צאן': 'flock', 'הצאן': 'the·flock',
    'הבקר': 'the·cattle', 'בהמתך': 'your·animals',
    'לבו': 'his·heart', 'לבי': 'my·heart',
    'גגו': 'its·top', 'קירתיו': 'its·walls',
    'עורו': 'its·hide', 'פרשו': 'its·dung',
    'בשרו': 'its·flesh',
    'החקים': 'the·statutes', 'התורת': 'the·laws',
    'אתתי': 'my·signs', 'מופתי': 'my·wonders',
    'צבאתי': 'my·armies',
    'שבעת': 'seven', 'הימים': 'the·days',
    'השביעי': 'the·seventh', 'השבת': 'the·Sabbath',
    'יום': 'day', 'היום': 'the·day',
    'לחמך': 'your·bread', 'מימיך': 'your·water',
    'כלאשרבם': 'all·that·is·in·them',
    'אדני': 'my·lord', 'אדניו': 'his·master',
}

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load ETCBC for fallback
with open(BASE / 'references' / 'etcbc_exodus_by_verse.json', 'r', encoding='utf-8') as f:
    etcbc = json.load(f)

fixed = 0
unfixed = 0

for ch in data['chapters']:
    for v in ch['verses']:
        ref = f"{ch['chapter']}:{v['verse']}"
        for w in v.get('words', []):
            h = w['heb']
            e = w['eng']

            if e != '(object marker)':
                continue
            if '\u05BE' not in h:
                continue

            # Split on maqaf
            parts = h.split('\u05BE')
            # First part should be את or ואת
            first_cons = strip_n(parts[0])
            if first_cons not in ('את', 'ואת'):
                continue

            # Get the noun part(s)
            noun_parts = parts[1:]
            noun_heb = '\u05BE'.join(noun_parts)
            noun_cons = strip_n(noun_heb).replace('\u05BE', '')

            if not noun_cons:
                continue

            # Try dictionary first
            noun_eng = None
            if noun_cons in NOUN_DICT:
                noun_eng = NOUN_DICT[noun_cons]
            else:
                # Try stripping ה prefix
                if noun_cons.startswith('ה') and noun_cons[1:] in NOUN_DICT:
                    noun_eng = 'the·' + NOUN_DICT[noun_cons[1:]]
                # Try ETCBC
                if not noun_eng:
                    etcbc_verse = etcbc.get(ref, [])
                    for em in etcbc_verse:
                        em_cons = em['cons'].replace(' ', '')
                        if em_cons == noun_cons or noun_cons.endswith(em_cons):
                            g = em.get('gloss', '')
                            if g and g not in ('<object marker>', 'the', 'and'):
                                noun_eng = g
                                break

            if noun_eng:
                prefix = 'and·' if first_cons == 'ואת' else ''
                w['eng'] = f"{prefix}(object marker)·{noun_eng}"
                fixed += 1
            else:
                unfixed += 1

print(f"Fixed: {fixed} compound את words")
print(f"Still unfixed: {unfixed}")

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Saved")
