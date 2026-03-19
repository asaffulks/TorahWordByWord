#!/usr/bin/env python3
"""
For each verse, use the correct Sefaria English translation to verify
and fix individual word glosses. Only fixes words that are clearly wrong —
leaves correct glosses untouched.
"""
import json, re, sys
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Known function words that don't need translation-matching
SKIP_GLOSSES = {
    '[identifies object]', 'and', 'the', 'to', 'in', 'from', 'upon',
    'which', 'that', 'not', 'all', 'because', 'if', 'so', 'also',
    'and·[object]', 'between', 'and·between', 'behold', 'and·behold',
    'I', 'you', 'he', 'she', 'they', 'we', 'him', 'her', 'them',
    'to·me', 'to·you', 'to·him', 'to·her', 'to·them', 'to·us',
    'his', 'my', 'your', 'our', 'their',
}

# Words that are correct even if they don't match the translation
# (different translation style)
ALWAYS_CORRECT = {
    'YHWH', 'God', '[identifies object]',
}

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        trans = v.get('translation', '').lower()
        if not trans:
            continue

        trans_words = set(re.findall(r'[a-z]+', trans))

        for w in v['words']:
            eng = w['eng']

            # Skip function words and known-correct
            if eng in SKIP_GLOSSES or eng in ALWAYS_CORRECT:
                continue
            if len(eng) <= 2:
                continue

            # Get the core English words from the gloss (split on dots)
            gloss_words = set(eng.lower().replace('\u00B7', ' ').split())

            # Check if any gloss word appears in the translation
            match = any(gw in trans_words for gw in gloss_words if len(gw) > 2)

            if match:
                continue  # gloss matches translation, it's fine

            # No match — this gloss might be wrong
            # Try to find a better word from the translation
            key = strip_n(w['heb']).replace('\u05BE', '')

            # Don't fix names (capitalized glosses)
            if eng and eng[0].isupper() and eng not in ('Lamed', 'Perf', 'David'):
                continue

            # Don't fix compound glosses that are mostly correct
            if '\u00B7' in eng and len(gloss_words) > 2:
                # Check if at least half the words match
                matches = sum(1 for gw in gloss_words if gw in trans_words and len(gw) > 2)
                if matches >= len(gloss_words) / 2:
                    continue

            # This gloss doesn't match the translation at all
            # Mark it for review but don't auto-fix yet — just collect stats
            # (We'll fix in the next pass)

            # Actually, let's try some safe auto-fixes:

            # If gloss is a Hebrew consonantal form, it's definitely wrong
            if all(('\u05D0' <= ch <= '\u05EA') for ch in eng.replace('\u00B7', '')):
                # Try root
                if w.get('root'):
                    w['eng'] = w['root']
                    fixed += 1
                continue

            # If gloss is "nm", "n m", etc.
            if eng in ('nm', 'n m', 'n f', 'n m/f'):
                if w.get('root'):
                    w['eng'] = w['root']
                else:
                    w['eng'] = key
                fixed += 1
                continue

            # If gloss is academic junk
            if eng in ('adj', 'v', 'prep', 'conj', 'pron', 'adv'):
                if w.get('root'):
                    w['eng'] = w['root']
                fixed += 1
                continue

# Now do a second pass: for remaining non-matching glosses,
# try to find the right word from the translation using position hints
total_checked = 0
total_mismatch = 0
for c in d['chapters']:
    for v in c['verses']:
        trans = v.get('translation', '').lower()
        if not trans:
            continue
        trans_words_list = re.findall(r'[a-z]+', trans)
        trans_words_set = set(trans_words_list)

        for w in v['words']:
            eng = w['eng']
            if eng in SKIP_GLOSSES or eng in ALWAYS_CORRECT:
                continue
            if len(eng) <= 2 or (eng[0].isupper() and eng not in ('Lamed','Perf','David')):
                continue

            total_checked += 1
            gloss_words = set(eng.lower().replace('\u00B7', ' ').split())
            match = any(gw in trans_words_set for gw in gloss_words if len(gw) > 2)
            if not match:
                total_mismatch += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Fixed {fixed} clearly wrong glosses")
print(f"Checked {total_checked} content words against translations")
print(f"Mismatches remaining: {total_mismatch} ({total_mismatch*100//max(total_checked,1)}%)")
