#!/usr/bin/env python3
"""Cross-check our glosses against standard Biblical Hebrew vocabulary."""
import json, re, sys
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Standard Biblical Hebrew vocabulary (Eisenbrauns/BDB consensus)
STANDARD = {
    'אב': 'father', 'אדון': 'lord/master', 'אדם': 'man/human',
    'אדמה': 'ground/soil', 'אהב': 'love', 'אהל': 'tent',
    'אור': 'light', 'אות': 'sign', 'אז': 'then',
    'אזן': 'ear', 'אח': 'brother', 'אחד': 'one',
    'אחר': 'after/other', 'איב': 'enemy', 'אין': 'there is not',
    'איש': 'man', 'אכל': 'eat', 'אל': 'to/toward',
    'אלה': 'these', 'אלהים': 'God', 'אם': 'mother/if',
    'אמר': 'say', 'אני': 'I', 'אנכי': 'I',
    'אסף': 'gather', 'אף': 'also/nose/anger', 'ארון': 'ark',
    'ארץ': 'earth/land', 'אש': 'fire', 'אשה': 'woman/wife',
    'אשר': 'who/which/that', 'את': '[d.o.]', 'אתה': 'you',
    'בגד': 'garment', 'בוא': 'come/enter', 'בין': 'between',
    'בית': 'house', 'בכור': 'firstborn', 'בן': 'son',
    'בנה': 'build', 'בעל': 'lord/husband', 'בקר': 'morning',
    'ברא': 'create', 'ברית': 'covenant', 'ברך': 'bless',
    'בשר': 'flesh', 'בת': 'daughter', 'גדול': 'great',
    'גוי': 'nation', 'גם': 'also', 'דבר': 'word/speak',
    'דור': 'generation', 'דם': 'blood', 'דרך': 'way/road',
    'הוא': 'he', 'היא': 'she', 'היה': 'be/was',
    'הלך': 'go/walk', 'הם': 'they', 'הנה': 'behold',
    'הר': 'mountain', 'זה': 'this', 'זכר': 'remember',
    'זרע': 'seed/offspring', 'חוק': 'statute', 'חזק': 'strong',
    'חטא': 'sin', 'חי': 'living/alive', 'חיה': 'live',
    'חכם': 'wise', 'חמש': 'five', 'חן': 'grace/favor',
    'חסד': 'kindness/loyalty', 'חרב': 'sword',
    'טוב': 'good', 'יד': 'hand', 'ידע': 'know',
    'יהוה': 'YHWH', 'יום': 'day', 'ילד': 'bear/beget',
    'ים': 'sea', 'יסף': 'add', 'יצא': 'go out',
    'ירא': 'fear', 'ירד': 'go down', 'ירש': 'possess/inherit',
    'ישב': 'sit/dwell', 'כבד': 'heavy/honored', 'כבוד': 'glory',
    'כה': 'thus', 'כהן': 'priest', 'כי': 'that/because/when',
    'כל': 'all/every', 'כלה': 'finish', 'כלי': 'vessel',
    'כן': 'so/thus', 'כסף': 'silver/money', 'כרת': 'cut',
    'כתב': 'write', 'לא': 'not', 'לב': 'heart',
    'לחם': 'bread/food', 'לילה': 'night', 'לקח': 'take',
    'מאד': 'very/exceedingly', 'מאה': 'hundred', 'מה': 'what',
    'מות': 'die/death', 'מים': 'water', 'מלא': 'fill/full',
    'מלאך': 'messenger/angel', 'מלך': 'king/reign',
    'מעל': 'above', 'מצא': 'find', 'מקום': 'place',
    'משפחה': 'clan/family', 'משפט': 'justice/judgment',
    'נא': 'please', 'נגד': 'before/opposite', 'נגע': 'touch',
    'נהר': 'river', 'נכה': 'strike', 'נפל': 'fall',
    'נפש': 'soul/life/person', 'נשא': 'lift/carry',
    'נתן': 'give', 'סביב': 'around', 'סור': 'turn aside',
    'עבד': 'serve/servant', 'עבר': 'cross over',
    'עד': 'until/witness', 'עוד': 'still/yet/again',
    'עולם': 'forever/eternity', 'עון': 'iniquity',
    'עין': 'eye/spring', 'עיר': 'city', 'על': 'upon/over',
    'עלה': 'go up', 'עם': 'people/with', 'עמד': 'stand',
    'ענה': 'answer/respond', 'עפר': 'dust',
    'עץ': 'tree/wood', 'ערב': 'evening', 'עשה': 'do/make',
    'עשר': 'ten', 'פה': 'mouth', 'פני': 'face/before',
    'צאן': 'flock', 'צוה': 'command', 'קדש': 'holy',
    'קול': 'voice', 'קום': 'arise/stand', 'קרא': 'call/read',
    'קרב': 'draw near', 'ראה': 'see', 'ראש': 'head/first',
    'רב': 'much/many', 'רגל': 'foot', 'רוח': 'spirit/wind',
    'רע': 'evil/bad', 'שבע': 'seven/swear',
    'שוב': 'return', 'שים': 'put/set', 'שכב': 'lie down',
    'שלום': 'peace', 'שלח': 'send', 'שלש': 'three',
    'שם': 'name/there', 'שמים': 'heavens', 'שמע': 'hear',
    'שמר': 'keep/guard', 'שנה': 'year', 'שני': 'two/second',
    'שער': 'gate', 'שפט': 'judge', 'תוך': 'midst',
}

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Get all word-gloss pairs with frequency
word_glosses = Counter()
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            word_glosses[(key, w['eng'])] += 1

# Cross-check
mismatches = []
for (key, eng), cnt in word_glosses.most_common(800):
    if key in STANDARD:
        std = STANDARD[key]
        eng_lower = eng.lower().replace('\u00B7', ' ').replace('[d.o.]', 'direct object')
        std_options = std.lower().replace('/', ' ').split()
        match = any(opt in eng_lower for opt in std_options)
        if not match and cnt >= 3:
            mismatches.append((cnt, key, eng, std))

mismatches.sort(key=lambda x: -x[0])
print(f'Potential mismatches (freq >= 3):')
for cnt, key, eng, std in mismatches[:40]:
    print(f'  {cnt:4d}x  {key:15s}  ours: "{eng:25s}"  standard: "{std}"')
print(f'\nTotal: {len(mismatches)} potential mismatches')
