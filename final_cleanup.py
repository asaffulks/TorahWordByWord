"""Final cleanup: merge fragments, fix remaining empties, clean HTML remnants."""
import json, re, sys, html as htmlmod

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

from sefaria_pipeline import calc_gematria

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# 1. Clean remaining HTML and dict defs
fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            if '<' in e or 'href' in e:
                e = re.sub(r'<[^>]*>.*$', '', e).strip()
                e = re.sub(r'\(f\.\s*$', '', e).strip()
                if e == 'See' or not e:
                    e = ''
                w['eng'] = e
                fixed += 1
            if '="' in e or '= "' in e:
                m = re.match(r'^([\w\u00B7\[\]\.]+)', e)
                w['eng'] = m.group(1) if m else e.split('=')[0].strip().strip('"')
                fixed += 1
            if '&' in w['eng']:
                w['eng'] = htmlmod.unescape(w['eng'])
            w['eng'] = w['eng'].rstrip('.').strip()

# 2. Merge fragments (1-2 consonant words with empty/generic gloss)
merged = 0
for c in d['chapters']:
    for v in c['verses']:
        words = v['words']
        new_words = []
        i = 0
        while i < len(words):
            w = words[i]
            cons = strip_n(w['heb']).replace('\u05BE', '')
            if (len(cons) <= 2
                and w['eng'] in ('', 'and', 'him', 'he', 'midst', 'day', 'to', 'Lamed', 'end', 'and\u00B7end')
                and i + 1 < len(words)):
                nw = words[i + 1]
                nc = strip_n(nw['heb']).replace('\u05BE', '')
                if len(nc) <= 3 or nw['eng'] in ('', 'and', 'him', 'he', 'midst', 'Lamed', 'refuge'):
                    mh = w['heb'] + nw['heb']
                    new_words.append({
                        'heb': mh,
                        'tr': w['tr'] + nw['tr'],
                        'root': w['root'] or nw['root'],
                        'eng': '',
                        'gem': calc_gematria(mh.replace('\u05BE', '')),
                    })
                    merged += 1
                    i += 2
                    continue
            new_words.append(w)
            i += 1
        if len(new_words) != len(words):
            v['words'] = new_words
            v['total_gematria'] = sum(ww['gem'] for ww in new_words)

# 3. Apply known fixes for remaining empty words
FIXES = {
    '\u05D1\u05E8\u05D0\u05E9\u05D9\u05EA': 'in\u00B7beginning',
    '\u05D1\u05E8\u05D0': 'created',
    '\u05D1\u05E8': 'grain',
    '\u05E8\u05D0\u05E9\u05D9\u05EA': 'beginning',
    '\u05D5\u05E8\u05D0\u05E9\u05D9\u05EA': 'and\u00B7beginning',
    '\u05D5\u05DD': 'day',
    '\u05D5\u05D0': 'he',
    '\u05D4\u05DC': '',
    '\u05D5\u05DC': '',
    '\u05D5\u05DA': 'midst',
    '\u05D2\u05D3': 'Gad',
    '\u05E4\u05D3\u05E0\u05D4': 'to\u00B7Paddan',
    '\u05D0\u05DC\u05D9\u05E4\u05D6': 'Eliphaz',
    '\u05DC\u05D0\u05DC\u05D9\u05E4\u05D6': 'to\u00B7Eliphaz',
    '\u05D5\u05D8\u05DF': 'and\u00B7Lotan',
    '\u05D1\u05D1\u05DC': 'Babel',
    '\u05E6\u05D1\u05D5\u05D9\u05DD': 'Zeboiim',
    '(\u05E6\u05D1\u05D9\u05D9\u05DD)': 'Zeboiim',
    '\u05D0\u05DC\u05D9\u05E9\u05D4': 'Elishah',
    '\u05D1\u05D7\u05E6\u05E6\u05DF': 'in\u00B7Hazazon',
    '\u05D5\u05D9\u05E9\u05EA\u05D7\u05D5\u05D5': 'and\u00B7bowed\u00B7down',
    '\u05D4\u05D0\u05E3': 'indeed?',
    '\u05D1\u05D0\u05E4\u05D9\u05D5': 'in\u00B7his\u00B7anger',
    '\u05D0\u05E4\u05D9\u05DD': 'face',
    '\u05D0\u05E3': 'also',
    '\u05D0\u05E4\u05D9\u05DA': 'your\u00B7anger',
    '\u05D5\u05D9\u05D4\u05DC\u05DC': 'and\u00B7praised',
    '(\u05D9\u05E2\u05D9\u05E9)': 'Iush',
    '(\u05D4\u05D5\u05E6\u05D0)': 'bring\u00B7out',
    '\u05D4\u05D9\u05E6\u05D0': 'will\u00B7go\u00B7out',
    '\u05D5\u05D3\u05D9\u05DD': 'and\u00B7Dodanim',
    '\u05D5\u05D3': 'and\u00B7Ohad',
    '\u05D1\u05D4\u05DE\u05DC': 'when\u00B7circumcised',
    '\u05D4\u05DC\u05D5\u05D0': 'is\u00B7it\u00B7not',
    '\u05D4\u05DC\u05D5\u05DA': 'going',
    '\u05D5\u05DC\u05D5\u05D3': 'and\u00B7Lud',
    '\u05DC\u05D5\u05E9\u05D9': 'knead',
    '\u05DC\u05DC\u05D5\u05DF': 'to\u00B7lodge',
    '\u05D4\u05D5\u05E6\u05D0': 'bring\u00B7out',
    '\u05D5\u05E9\u05D9': 'knead!',
    '(\u05D5\u05D9\u05D9\u05E9\u05DD)': 'and\u00B7was\u00B7set',
    '\u05D5\u05D9\u05D5\u05E9\u05DD': 'and\u00B7was\u00B7set',
    '\u05D5\u05DC\u05D8\u05D5\u05E9\u05DD': 'and\u00B7Letushim',
    '(\u05D2\u05D9\u05D9\u05DD)': 'nations',
    '(\u05E6\u05D9\u05D3\u05D4)': 'game',
    '\u05D5\u05D6': 'and\u00B7Luz',
    '(\u05D1\u05D2\u05D3)': 'fortune!',
    '\u05D5\u05DC\u05D5\u05D6': 'and\u00B7almond',
    '\u05D5\u05D7\u05D4': 'and\u00B7bowed\u00B7down',
    '\u05D5\u05D9\u05EA\u05E0\u05DB\u05DC': 'and\u00B7plotted',
    '\u05D0\u05E4\u05D5': 'his\u00B7anger',
    '(\u05D0\u05E1\u05D5\u05E8\u05D9)': 'prisoners\u00B7of',
    '\u05D1\u05DE\u05DC': 'at\u00B7the\u00B7lodging',
    '\u05D0\u05E4\u05DA': 'your\u00B7anger',
    '\u05D5\u05E4\u05DC': 'and\u00B7Pallu',
    '\u05D5\u05D7\u05E6\u05E8\u05DF': 'and\u00B7Hezron',
    '\u05D5\u05E9\u05DE\u05E8\u05DF': 'and\u00B7Shimron',
    '\u05D5\u05D2\u05D5\u05E0\u05D9': 'and\u00B7Guni',
    '\u05DC\u05D0\u05E4\u05D9\u05D5': 'to\u00B7his\u00B7face',
    '\u05D1\u05D0\u05E4\u05DD': 'in\u00B7their\u00B7anger',
    '\u05D0\u05E4\u05DD': 'their\u00B7anger',
    '\u05D5\u05D9\u05D9\u05E9\u05DD': 'and\u00B7was\u00B7placed',
    '\u05D5\u05D9\u05D9\u05DF': 'and\u00B7wine',
    '\u05D5\u05DE\u05E2\u05DC': 'and\u00B7above',
    '\u05D5\u05DE\u05E9\u05DD': 'and\u00B7from\u00B7there',
    '\u05D9\u05DC\u05D5\u05D4': 'will\u00B7join',
    '\u05D5\u05E9\u05E9\u05D4': 'and\u00B7six',
    '\u05D5\u05D1\u05D4\u05E8': 'and\u00B7in\u00B7the\u00B7mountain',
    '\u05D5\u05D1\u05D9\u05EA': 'and\u00B7house',
    '\u05D5\u05DE\u05D9\u05D3': 'and\u00B7from\u00B7the\u00B7hand',
    '\u05D5\u05DE\u05D4': 'and\u00B7what',
    '\u05D5\u05D1\u05D7\u05DC': 'and\u00B7in\u00B7Hul',
    '\u05D5\u05DC\u05E9\u05DC': 'and\u00B7to\u00B7Shelah',
    '\u05D5\u05D0\u05D5\u05D7\u05E6\u05E8\u05DF': 'and\u00B7Hezron',
    '\u05DE\u05E9\u05DD': 'from\u00B7there',
    '\u05D0\u05D3\u05E0\u05D9\u05D5': 'his\u00B7lord',
}

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if w['eng'] == '' and key in FIXES and FIXES[key]:
                w['eng'] = FIXES[key]
                fixed += 1
            elif w['eng'] == '' and strip_n(w['heb']) == '\u05D5':
                w['eng'] = 'him' if '\u05B9' in w['heb'] else 'and'
                fixed += 1
            # Catch untranslated
            if w['eng'] == 'untranslated':
                w['eng'] = ''

# 4. Gen 1:1 specific fixes
v1 = d['chapters'][0]['verses'][0]
expected = ['in\u00B7beginning', 'created', 'God', '[obj.mark]', 'the\u00B7heavens', 'and\u00B7[obj.mark]', 'the\u00B7earth']
for i, exp in enumerate(expected):
    if i < len(v1['words']):
        v1['words'][i]['eng'] = exp

total = sum(len(v['words']) for c in d['chapters'] for v in c['verses'])
still = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if w['eng'] == '')
html_left = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if '<' in w['eng'])

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Merged {merged}, fixed {fixed}. Empty: {still}, HTML: {html_left}. Total words: {total}')
