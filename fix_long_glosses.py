#!/usr/bin/env python3
"""Shorten all glosses that are too long for word cards (max ~15 chars).
Keep [identifies object] as-is. Keep dot convention. Fix dictionary-style glosses."""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Specific replacements for known long/wrong glosses
REPLACEMENTS = {
    # Dictionary "or" definitions
    'to be or become light': 'give·light',
    'be or become light': 'give·light',
    'to be or become great': 'be·great',
    'be or become great': 'be·great',
    'to be or become many': 'be·many',
    'be or become many': 'be·many',
    'to be or become high': 'be·high',
    'to be or become long': 'be·long',
    'to be or become old': 'be·old',
    'to be or become unclean': 'be·unclean',
    'to be or become strong': 'be·strong',
    'to be or become small': 'be·small',
    'to pass over or by or through': 'pass·over',
    'teeming or swarming things': 'swarming·things',
    'a precious stone or gem': 'precious·stone',
    'Asshur or Assyria': 'Assyria',
    'Padan or Padan-aram': 'Paddan-Aram',
    'Sidon or Zidon': 'Sidon',

    # Verbose phrases
    'father of an individual': 'father',
    'after the following part': 'after',
    'Commonly transcribed YHWH': 'YHWH',
    'flying creatures': 'birds',
    'to give to drink': 'water',
    'sojourning place': 'dwelling',
    'to rouse oneself': 'rise·up',
    'to be conspicuous': 'tell',
    'standing place': 'place',
    'to put to shame': 'be·ashamed',
    'to bear fruit': 'be·fruitful',
    'to be prudent': 'be·wise',
    'burnt-offering': 'offering',
    'to·burnt-offering': 'to·offering',
    'all·flying creatures': 'all·birds',
    'to·standing place': 'to·place',
    'and·stretched·out': 'and·stretched',

    # "burning" = כי was already fixed to "because" but compounds remain
    'burning·to be good': 'because·good',
    'burning·to go in': 'because·came',
    'burning·to say': 'because·said',
    'burning·to eat': 'because·ate',
    'burning·to call': 'because·called',
    'burning·to give': 'because·gave',
    'burning·to be': 'because·was',
    'burning·to take': 'because·took',
    'burning·to see': 'because·saw',
    'burning·to know': 'because·knew',
    'burning·to hear': 'because·heard',
    'burning·to find': 'because·found',

    # Long name compounds
    '[identifies object]·Joseph': '[object]·Joseph',
    '[identifies object]·Jacob': '[object]·Jacob',
    '[identifies object]·Isaac': '[object]·Isaac',
    '[identifies object]·Pharaoh': '[object]·Pharaoh',
    '[identifies object]·Abraham': '[object]·Abraham',
    '[identifies object]·him': '[object]·him',
    '[identifies object]·them': '[object]·them',
    '[identifies object]·me': '[object]·me',
    '[identifies object]·you': '[object]·you',
    '[identifies object]·us': '[object]·us',
    '[identifies object]·you·all': '[object]·you·all',
    'and·[identifies object]': 'and·[object]',
    'to·father of an individual': 'to·father',
    '[identifies object]·the·God': '[object]·God',
}

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            orig = e

            # Direct replacements
            if e in REPLACEMENTS:
                w['eng'] = REPLACEMENTS[e]
                fixed += 1
                continue

            # Pattern: "burning·ANYTHING" where burning = כי
            if e.startswith('burning\u00B7'):
                rest = e[8:]  # after "burning·"
                # Strip "to " from verbs
                if rest.startswith('to '):
                    rest = rest[3:]
                w['eng'] = 'because\u00B7' + rest
                fixed += 1
                continue

            # Pattern: any "X or Y" longer than 15 chars — keep first option
            if ' or ' in e and len(e) > 15:
                parts = e.split(' or ')
                w['eng'] = parts[0].strip()
                fixed += 1
                continue

            # Pattern: "to verb phrase" longer than 15 — shorten
            if e.startswith('to ') and len(e) > 15:
                # Strip "to " and simplify
                verb = e[3:]
                # Common simplifications
                verb = verb.replace('oneself', '').replace('himself', '').strip()
                if len(verb) > 12:
                    # Take first word only
                    verb = verb.split()[0] if verb.split() else verb
                w['eng'] = verb
                fixed += 1
                continue

            # Any remaining gloss > 18 chars (except [identifies object] alone)
            if len(e) > 18 and e != '[identifies object]':
                # Try to shorten by removing common padding
                shortened = e
                shortened = shortened.replace('of an individual', '')
                shortened = shortened.replace('the following part', '')
                shortened = shortened.replace('Commonly transcribed ', '')
                shortened = shortened.strip()
                if len(shortened) > 18:
                    # Take essential words only
                    words = shortened.replace('\u00B7', ' ').split()
                    if len(words) > 3:
                        shortened = '\u00B7'.join(words[:3])
                    elif len(words) > 2:
                        shortened = '\u00B7'.join(words[:2])
                w['eng'] = shortened.strip()
                fixed += 1

# Protect Gen 1:1
v1 = d['chapters'][0]['verses'][0]
expected = ['in\u00B7beginning', 'created', 'God', '[identifies object]',
            'the\u00B7heavens', 'and\u00B7[identifies object]', 'the\u00B7earth']
for i, exp in enumerate(expected):
    if i < len(v1['words']):
        v1['words'][i]['eng'] = exp

# Count remaining long glosses
still_long = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            if len(w['eng']) > 18 and w['eng'] != '[identifies object]':
                still_long += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed} glosses. Still > 18 chars: {still_long}')
