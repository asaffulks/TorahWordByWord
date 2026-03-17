#!/usr/bin/env python3
"""Hand-correct Genesis chapters 1-3 word by word."""
import json, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

ch1 = d['chapters'][0]

# Genesis 1 corrections — (verse, word_index, correct_gloss)
FIXES = [
    # 1:1 — good as-is

    # 1:2
    (2, 0, 'and·the·earth'),
    (2, 2, 'unformed'),
    (2, 3, 'and·void'),
    (2, 4, 'and·darkness'),
    (2, 5, 'upon·the·face·of'),
    (2, 6, 'the·deep'),
    (2, 7, 'and·the·spirit·of'),
    (2, 9, 'hovering'),
    (2, 10, 'upon·the·face·of'),

    # 1:4
    (4, 2, '[object]·the·light'),
    (4, 3, 'that·good'),
    (4, 4, 'and·separated'),

    # 1:5
    (5, 2, 'to·the·light'),
    (5, 4, 'and·to·the·darkness'),
    (5, 5, 'called'),
    (5, 7, 'and·was·evening'),
    (5, 8, 'and·was·morning'),

    # 1:6
    (6, 3, 'expanse'),
    (6, 4, 'in·the·midst·of'),
    (6, 6, 'and·let·it·be'),
    (6, 7, 'separating'),
    (6, 10, 'to·water'),

    # 1:7
    (7, 2, '[object]·the·expanse'),
    (7, 4, 'between'),
    (7, 6, 'that'),
    (7, 7, 'beneath'),
    (7, 8, 'the·expanse'),
    (7, 11, 'that'),
    (7, 13, 'the·expanse'),

    # 1:8
    (8, 2, 'to·the·expanse'),
    (8, 3, 'sky'),
    (8, 7, 'second'),

    # 1:9
    (9, 4, 'beneath'),
    (9, 8, 'and·appear'),

    # 1:10
    (10, 4, 'and·the·gathering·of'),
    (10, 6, 'called'),
    (10, 7, 'seas'),

    # 1:11
    (11, 2, 'let·sprout'),
    (11, 4, 'vegetation'),
    (11, 5, 'plants'),
    (11, 6, 'bearing'),
    (11, 10, 'bearing'),

    # 1:12
    (12, 0, 'and·brought·forth'),
    (12, 2, 'vegetation'),
    (12, 3, 'plants'),
    (12, 4, 'bearing'),
    (12, 8, 'bearing·fruit'),

    # 1:13
    (13, 3, 'third'),

    # 1:14
    (14, 3, 'lights'),
    (14, 4, 'in·the·expanse·of'),
    (14, 6, 'to·separate'),
    (14, 10, 'the·night'),
    (14, 11, 'and·they·shall·be'),
    (14, 12, 'for·signs'),
    (14, 13, 'and·for·seasons'),
    (14, 14, 'and·for·days'),
    (14, 15, 'and·years'),

    # 1:15
    (15, 0, 'and·they·shall·be'),
    (15, 1, 'for·lights'),
    (15, 2, 'in·the·expanse·of'),
    (15, 4, 'to·give·light'),

    # 1:16
    (16, 2, '[object]·two'),
    (16, 3, 'the·lights'),
    (16, 4, 'the·great'),
    (16, 5, '[object]·the·light'),
    (16, 6, 'the·greater'),
    (16, 7, 'for·rule·of'),
]

for verse_num, word_idx, correct in FIXES:
    v = ch1['verses'][verse_num - 1]
    if word_idx < len(v['words']):
        v['words'][word_idx]['eng'] = correct

# Continue with rest of Gen 1
FIXES2 = [
    # 1:16 continued
    (16, 9, 'and·[object]·the·light'),
    (16, 10, 'the·lesser'),
    (16, 11, 'for·rule·of'),
    (16, 12, 'the·night'),
    (16, 13, 'and·[object]·the·stars'),

    # 1:17
    (17, 0, 'and·set'),
    (17, 2, 'in·the·expanse·of'),
    (17, 4, 'to·give·light'),

    # 1:18
    (18, 0, 'and·to·rule'),
    (18, 3, 'and·to·separate'),
    (18, 7, 'and·was·so'),  # if exists

    # 1:20
    (20, 2, 'let·swarm'),
    (20, 4, 'swarming·creatures'),
    (20, 5, 'living'),
    (20, 6, 'soul'),
    (20, 7, 'and·birds'),
    (20, 8, 'let·fly'),
    (20, 9, 'over·the·earth'),
    (20, 10, 'across·the·face·of'),
    (20, 11, 'the·expanse·of'),

    # 1:21
    (21, 2, '[object]·the·great'),
    (21, 3, 'sea·creatures'),
    (21, 5, 'every'),
    (21, 6, 'living'),
    (21, 8, 'the·moving'),

    # 1:22
    (22, 2, 'be·fruitful'),
    (22, 3, 'and·multiply'),
    (22, 4, 'and·fill'),
    (22, 6, 'in·the·seas'),

    # 1:24
    (24, 2, 'let·bring·forth'),
    (24, 4, 'living'),
    (24, 5, 'creature'),
    (24, 6, 'after·its·kind'),
    (24, 7, 'livestock'),
    (24, 8, 'and·creeping·things'),
    (24, 9, 'and·beasts·of'),

    # 1:25
    (25, 2, '[object]·beast·of'),
    (25, 5, '[object]·the·livestock'),
    (25, 8, '[object]·every'),
    (25, 9, 'creeping·thing·of'),

    # 1:26
    (26, 2, 'let·us·make'),
    (26, 3, 'man'),
    (26, 4, 'in·our·image'),
    (26, 5, 'after·our·likeness'),
    (26, 6, 'and·let·them·rule'),
    (26, 7, 'over·the·fish·of'),
    (26, 9, 'and·over·the·birds·of'),
    (26, 11, 'and·over·the·livestock'),
    (26, 12, 'and·over·all'),

    # 1:27
    (27, 0, 'and·created'),
    (27, 2, '[object]·the·man'),
    (27, 3, 'in·his·image'),
    (27, 4, 'in·the·image·of'),
    (27, 6, 'male'),
    (27, 7, 'and·female'),

    # 1:28
    (28, 2, 'be·fruitful'),
    (28, 3, 'and·multiply'),
    (28, 4, 'and·fill'),
    (28, 6, 'and·subdue·it'),
    (28, 7, 'and·rule'),
    (28, 8, 'over·the·fish·of'),
    (28, 10, 'and·over·the·birds·of'),

    # 1:29
    (29, 4, '[object]·every'),
    (29, 5, 'plant'),
    (29, 6, 'bearing'),
    (29, 8, 'upon·the·face·of'),
    (29, 11, 'and·[object]·every'),
    (29, 13, 'in·it'),
    (29, 14, 'fruit·of·tree'),
    (29, 15, 'bearing'),

    # 1:30
    (30, 1, 'every'),
    (30, 2, 'beast·of'),
    (30, 4, 'and·every'),
    (30, 5, 'bird·of'),
    (30, 7, 'and·every'),
    (30, 8, 'that·moves'),
    (30, 10, 'which·in·it'),
    (30, 11, 'living'),
    (30, 12, 'soul'),
    (30, 13, '[object]·every'),
    (30, 14, 'green'),
    (30, 15, 'plant'),
    (30, 16, 'for·food'),

    # 1:31
    (31, 2, '[object]·all'),
    (31, 4, 'and·behold'),
    (31, 5, 'very'),
    (31, 6, 'good'),
]

for verse_num, word_idx, correct in FIXES2:
    v = ch1['verses'][verse_num - 1]
    if word_idx < len(v['words']):
        v['words'][word_idx]['eng'] = correct

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Verify
print("Gen 1:1-5 after manual correction:")
for v in ch1['verses'][:5]:
    print(f'\n{v["ref"]}:  {v["translation"]}')
    for w in v['words']:
        print(f'  {w["heb"]:20s}  {w["eng"]}')
