#!/usr/bin/env python3
"""Fix all remaining issues found in deep audit."""
import json, re, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Vav-consecutive: "to X" -> "and·X-ed" when Hebrew starts with וַיּ/וַתּ/וַנּ/וַאּ
VAV_PAST = {
    'to say': 'and·said', 'to speak': 'and·spoke', 'to call': 'and·called',
    'to see': 'and·saw', 'to hear': 'and·heard', 'to know': 'and·knew',
    'to go': 'and·went', 'to come': 'and·came', 'to take': 'and·took',
    'to give': 'and·gave', 'to make': 'and·made', 'to do': 'and·did',
    'to be': 'and·was', 'to go out': 'and·went·out', 'to go up': 'and·went·up',
    'to go down': 'and·went·down', 'to fall': 'and·fell', 'to rise': 'and·arose',
    'to stand': 'and·stood', 'to sit': 'and·sat', 'to lie down': 'and·lay·down',
    'to send': 'and·sent', 'to build': 'and·built', 'to write': 'and·wrote',
    'to eat': 'and·ate', 'to drink': 'and·drank', 'to die': 'and·died',
    'to kill': 'and·killed', 'to bear': 'and·bore', 'to conceive': 'and·conceived',
    'to turn': 'and·turned', 'to return': 'and·returned', 'to flee': 'and·fled',
    'to find': 'and·found', 'to put': 'and·put', 'to set': 'and·set',
    'to burn': 'and·burned', 'to keep': 'and·kept', 'to serve': 'and·served',
    'to pass over': 'and·passed·over', 'to judge': 'and·judged',
    'to command': 'and·commanded', 'to swear': 'and·swore',
    'to bless': 'and·blessed', 'to curse': 'and·cursed',
    'to gather': 'and·gathered', 'to draw near': 'and·drew·near',
    'to stretch out': 'and·stretched·out', 'to strike': 'and·struck',
    'to smite': 'and·smote', 'to reign': 'and·reigned',
    'to count': 'and·counted', 'to cover': 'and·covered',
    'to break': 'and·broke', 'to cut': 'and·cut',
    'to open': 'and·opened', 'to close': 'and·closed',
    'to carry': 'and·carried', 'to bring': 'and·brought',
    'to lead': 'and·led', 'to fight': 'and·fought',
    'to meet': 'and·met', 'to touch': 'and·touched',
    'to fear': 'and·feared', 'to love': 'and·loved', 'to hate': 'and·hated',
    'to cry': 'and·cried', 'to weep': 'and·wept',
    'to hide': 'and·hid', 'to run': 'and·ran',
    'to dwell': 'and·dwelt', 'to camp': 'and·camped',
    'to offer': 'and·offered', 'to sanctify': 'and·sanctified',
    'to sprinkle': 'and·sprinkled', 'to anoint': 'and·anointed',
    'to wash': 'and·washed', 'to pour': 'and·poured',
    'to teem': 'and·teemed', 'to be vast': 'and·grew·mighty',
    'to work': 'and·worked', 'to be good': 'and·was·good',
    'to come near': 'and·drew·near', 'to prevail': 'and·prevailed',
    'to multiply': 'and·multiplied', 'to be pregnant': 'and·conceived',
    'to place': 'and·placed', 'to lift': 'and·lifted',
    'to plant': 'and·planted', 'to be heavy': 'and·was·heavy',
    'to be strong': 'and·was·strong', 'to harden': 'and·hardened',
    'to deliver': 'and·delivered', 'to save': 'and·saved',
    'to destroy': 'and·destroyed', 'to be angry': 'and·was·angry',
    'to be willing': 'and·was·willing', 'to refuse': 'and·refused',
    'to begin': 'and·began', 'to finish': 'and·finished',
    'to complete': 'and·completed', 'to cease': 'and·ceased',
    'to rest': 'and·rested', 'to leave': 'and·left',
    'to remain': 'and·remained', 'to turn aside': 'and·turned·aside',
    'to stretch': 'and·stretched', 'to reach': 'and·reached',
    'to number': 'and·numbered', 'to weigh': 'and·weighed',
    'to bow': 'and·bowed', 'to worship': 'and·worshipped',
    'to slaughter': 'and·slaughtered', 'to sacrifice': 'and·sacrificed',
    'to throw': 'and·threw', 'to cast': 'and·cast',
    'to spread': 'and·spread', 'to swallow': 'and·swallowed',
    'to pursue': 'and·pursued', 'to catch': 'and·caught',
    'to bind': 'and·bound', 'to loose': 'and·loosed',
    'to seize': 'and·seized', 'to hold': 'and·held',
    'to steal': 'and·stole', 'to rob': 'and·robbed',
    'to fill': 'and·filled', 'to empty': 'and·emptied',
    'to change': 'and·changed', 'to exchange': 'and·exchanged',
}

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = {'vav': 0, 'ki': 0, 'obj': 0, 'subst': 0, 'hebrew_in_eng': 0, 'roots': 0}

# Load ETCBC for root filling
with open(BASE / 'references' / 'etcbc_exodus_by_verse.json', 'r', encoding='utf-8') as f:
    etcbc = json.load(f)

for ch in data['chapters']:
    for v in ch['verses']:
        ref = f"{ch['chapter']}:{v['verse']}"
        etcbc_verse = etcbc.get(ref, [])

        for i, w in enumerate(v.get('words', [])):
            e = w.get('eng', '')
            h = strip_n(w['heb']).replace('\u05BE', '')

            # Fix 1: Vav-consecutive verbs
            if h.startswith('וי') or h.startswith('ות') or h.startswith('ונ') or h.startswith('וא'):
                e_lower = e.lower().strip()
                if e_lower in VAV_PAST:
                    w['eng'] = VAV_PAST[e_lower]
                    stats['vav'] += 1

            # Fix 2: "burning" for כי
            e = w['eng']
            if 'burning' in e.lower():
                # Check if this is actually כי (because) not a real burning context
                if h.startswith('כי') or 'כי' in h:
                    new_e = e.lower().replace('burning', 'because')
                    # Clean up common patterns
                    new_e = new_e.replace('because·to ', 'that·')
                    new_e = new_e.replace('because·', 'that·')
                    if new_e.startswith('that·to '):
                        new_e = 'that·' + new_e[8:]
                    w['eng'] = new_e
                    stats['ki'] += 1

            # Fix 3: "sign of the definite direct object"
            e = w['eng']
            if 'sign of the definite' in e:
                w['eng'] = e.replace('sign of the definite direct object', '(object marker)')
                stats['obj'] += 1

            # Fix 4: "subst" for סביב
            if e == 'subst':
                if 'סביב' in h:
                    w['eng'] = 'around'
                    stats['subst'] += 1
                else:
                    w['eng'] = 'upon'
                    stats['subst'] += 1

            # Fix 5: Hebrew chars in English
            e = w['eng']
            if any('\u05D0' <= c <= '\u05EA' for c in e):
                # Strip Hebrew and dict notation
                clean = re.sub(r'[\u05D0-\u05EA\u05B0-\u05C7\u0591-\u05AF]', '', e)
                clean = re.sub(r'c\.\s*st\.\s*of\s*', '', clean)
                clean = re.sub(r'\(dual\s*', '(', clean)
                clean = clean.strip(' ·')
                if clean and len(clean) > 1:
                    w['eng'] = clean
                else:
                    w['eng'] = 'mouth'  # c.st. of פה = mouth
                stats['hebrew_in_eng'] += 1

            # Fix 6: Fill missing roots from ETCBC
            if not w.get('root', ''):
                # Try matching Hebrew to ETCBC morphemes
                our_cons = strip_n(w['heb']).replace('\u05BE', '').replace(' ', '')
                acc = ''
                for em in etcbc_verse:
                    test = acc + em['cons'].replace(' ', '')
                    if test == our_cons:
                        lex = em.get('lex', '')
                        if lex:
                            w['root'] = strip_n(lex)
                            stats['roots'] += 1
                        break
                    elif our_cons.startswith(test):
                        acc = test
                    else:
                        if em['cons'].replace(' ', '') == our_cons:
                            lex = em.get('lex', '')
                            if lex:
                                w['root'] = strip_n(lex)
                                stats['roots'] += 1
                            break
                        acc = em['cons'].replace(' ', '')

        # Ensure insights and cross_refs fields exist
        if 'insights' not in v:
            v['insights'] = ''
        if 'cross_refs' not in v:
            v['cross_refs'] = ''

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixes applied:")
for k, count in stats.items():
    print(f"  {k}: {count}")

# Recount missing roots
no_root = sum(1 for ch in data['chapters'] for v in ch['verses'] for w in v.get('words',[]) if not w.get('root',''))
total_w = sum(1 for ch in data['chapters'] for v in ch['verses'] for w in v.get('words',[]))
print(f"\nRemaining missing roots: {no_root}/{total_w} ({100*no_root/total_w:.1f}%)")
