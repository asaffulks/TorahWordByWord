#!/usr/bin/env python3
"""Fix ALL remaining: to-verb, Hebrew-as-English, [d.o.] compounds, son->sons"""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

TO_PAST = {
    'to bear':'bore','to give':'gave','to take':'took','to say':'said',
    'to return':'returned','to eat':'ate','to die':'died','to know':'knew',
    'to go out':'went out','to speak':'spoke','to bless':'blessed',
    'to dwell':'dwelt','to call':'called','to find':'found',
    'to be good':'was good','to send':'sent','to go up':'went up',
    'to put':'put','to bury':'buried','to go down':'went down',
    'to prevail':'prevailed','to work':'worked','to build':'built',
    'to lift':'lifted','to live':'lived','to be old':'was old',
    'to fall':'fell','to sell':'sold','to weep':'wept',
    'to swear':'swore','to dream':'dreamed','to drink':'drank',
    'to keep':'kept','to stand':'stood','to run':'ran',
    'to kiss':'kissed','to meet':'met','to hate':'hated',
    'to love':'loved','to fear':'feared','to hear':'heard',
    'to write':'wrote','to judge':'judged','to serve':'served',
    'to fill':'filled','to open':'opened','to shut':'shut',
    'to wash':'washed','to bind':'bound','to plant':'planted',
    'to strike':'struck','to steal':'stole','to flee':'fled',
    'to rest':'rested','to turn':'turned','to ask':'asked',
    'to answer':'answered','to count':'counted','to burn':'burned',
    'to cry':'cried','to cut':'cut','to divide':'divided',
    'to dress':'dressed','to drive':'drove','to dry':'dried',
    'to embrace':'embraced','to gather':'gathered',
    'to grow':'grew','to hide':'hid','to hunt':'hunted',
    'to kill':'killed','to laugh':'laughed','to load':'loaded',
    'to mourn':'mourned','to multiply':'multiplied',
    'to pass':'passed','to pour':'poured','to pray':'prayed',
    'to pursue':'pursued','to reign':'reigned','to rule':'ruled',
    'to save':'saved','to scatter':'scattered','to set':'set',
    'to shave':'shaved','to sit':'sat','to sow':'sowed',
    'to teach':'taught','to tear':'tore','to touch':'touched',
    'to wait':'waited','to walk':'walked',
    'to be sorry':'was sorry','to be hot':'was angry',
    'to be heavy':'was heavy','to be able':'was able',
    'to be afraid':'was afraid','to be fruitful':'was fruitful',
    'to be strong':'was strong','to be angry':'was angry',
    'to be unclean':'was unclean','to be waste':'was waste',
    'to be just':'was just','to be slight':'was light',
    'to be bad':'was bad','to be spacious':'was spacious',
    'to conceive':'conceived','to destroy':'destroyed',
    'to interpret':'interpreted','to circumcise':'circumcised',
    'to inherit':'inherited','to slaughter':'slaughtered',
    'to comfort':'comforted','to remember':'remembered',
    'to establish':'established','to command':'commanded',
    'to complete':'completed','to create':'created',
    'to deceive':'deceived','to deliver':'delivered',
    'to expire':'expired','to prosper':'prospered',
    'to refuse':'refused','to separate':'separated',
    'to wrestle':'wrestled','to change':'changed',
    'to bow down':'bowed down','to give birth':'gave birth',
    'to break':'broke','to choose':'chose','to draw':'drew',
    'to dig':'dug','to lodge':'lodged',
}

HEBREW_FIX = {
    '\u05D1\u05EA': 'daughters',
    '\u05D7\u05D9': 'living',
    '\u05E9\u05DE\u05E2': 'heard',
    '\u05D2\u05D3\u05D5\u05DC': 'great',
    '\u05E8\u05E2': 'evil',
    '\u05D2\u05D5\u05D9': 'nation',
    '\u05D4\u05D0\u05E8\u05E5': 'the earth',
    '\u05E9\u05DE\u05D5': 'his name',
    '\u05E8\u05D1': 'many',
    '\u05E7\u05D8\u05DF': 'small',
    '\u05D0\u05DE\u05D4': 'cubit',
    '\u05D1\u05E8\u05D9\u05EA': 'covenant',
    '\u05E2\u05D5\u05DC\u05D4': 'offering',
    '\u05DE\u05D6\u05D1\u05D7': 'altar',
    '\u05E0\u05E4\u05E9': 'soul',
    '\u05E6\u05DC\u05DD': 'image',
    '\u05D3\u05DE\u05D5\u05EA': 'likeness',
    '\u05EA\u05D1\u05D4': 'ark',
    '\u05DE\u05D1\u05D5\u05DC': 'flood',
    '\u05DB\u05DC\u05D9': 'vessel',
    '\u05E6\u05D0\u05DF': 'flock',
    '\u05D1\u05E7\u05E8': 'cattle',
    '\u05E9\u05D5\u05E8': 'ox',
    '\u05DE\u05E9\u05E4\u05D7\u05D4': 'family',
    '\u05D2\u05E4\u05DF': 'vine',
    '\u05DE\u05E9\u05DB\u05DF': 'dwelling',
    '\u05D0\u05D4\u05DC': 'tent',
    '\u05DE\u05E7\u05E0\u05D4': 'livestock',
    '\u05E8\u05DB\u05D5\u05E9': 'possessions',
}

DO_SUFFIX = {
    '[d.o.]\u00B7them': 'them',
    'and\u00B7[d.o.]': 'and',
    '[d.o.]\u00B7me': 'me',
    '[d.o.]\u00B7you': 'you',
    '[d.o.]\u00B7us': 'us',
    '[d.o.]\u00B7him': 'him',
    '[d.o.]\u00B7her': 'her',
    '[d.o.]': '[identifies object]',
}

SKIP = {'to\u00B7me','to\u00B7you','to\u00B7him','to\u00B7her','to\u00B7them',
        'to\u00B7us','to\u00B7Noah','to\u00B7Cain','to\u00B7place','to\u00B7lodge',
        'to\u00B7Abraham','to\u00B7Jacob','to\u00B7Laban','to\u00B7Pharaoh',
        'to\u00B7God','to\u00B7YHWH','to\u00B7Shem','to\u00B7Esau',
        'to\u00B7Joseph','to\u00B7Isaac','to\u00B7the\u00B7man'}

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            key = strip_n(w['heb']).replace('\u05BE', '')

            # to+verb -> past tense
            if e in TO_PAST:
                w['eng'] = TO_PAST[e]
                fixed += 1
                continue

            # Hebrew as English
            if e in HEBREW_FIX:
                w['eng'] = HEBREW_FIX[e]
                fixed += 1
                continue

            # [d.o.] compounds
            if e in DO_SUFFIX:
                w['eng'] = DO_SUFFIX[e]
                fixed += 1
                continue

            # Any remaining to+verb not in dict
            if e.startswith('to ') and len(e) > 5 and '\u00B7' not in e and e not in SKIP:
                w['eng'] = e[3:]  # strip "to "
                fixed += 1
                continue

            # Any remaining Hebrew-as-English
            if e and len(e) > 1 and all(('\u05D0' <= ch <= '\u05EA') or ch in ' \u00B7' for ch in e) and 'identifies' not in e:
                if e in HEBREW_FIX:
                    w['eng'] = HEBREW_FIX[e]
                elif key in HEBREW_FIX:
                    w['eng'] = HEBREW_FIX[key]
                elif w.get('root') and any('a' <= ch <= 'z' for ch in str(w['root'])):
                    w['eng'] = w['root']
                else:
                    w['eng'] = key  # last resort
                fixed += 1
                continue

            # son -> sons for plural forms
            if e == 'son':
                if any(x in key for x in ['בני','בניו','בניך','בנינו','בניהם']):
                    w['eng'] = 'his\u00B7sons' if 'בניו' in key else 'sons'
                    fixed += 1

# Protect Gen 1:1
v1 = d['chapters'][0]['verses'][0]
exp = ['in\u00B7beginning','created','God','[identifies object]','the\u00B7heavens','and\u00B7[object]','the\u00B7earth']
for i, e in enumerate(exp):
    if i < len(v1['words']):
        v1['words'][i]['eng'] = e

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Count remaining
remaining = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            if e.startswith('to ') and len(e) > 5 and '\u00B7' not in e and e not in SKIP:
                remaining += 1
            elif '[d.o.]' in e:
                remaining += 1
            elif e and len(e) > 1 and all(('\u05D0' <= ch <= '\u05EA') or ch in ' \u00B7' for ch in e) and 'identifies' not in e:
                remaining += 1

print(f'Fixed {fixed}. Remaining issues: {remaining}')
