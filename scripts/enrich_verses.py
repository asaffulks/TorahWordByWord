#!/usr/bin/env python3
"""
Enrich genesis.json with computed insights that fill empty space.
All content is derived from the text itself — nothing made up.

Adds 'insights' field with:
- Word-by-word gematria breakdown for notable words
- Root frequency analysis ("This root appears X times in Genesis")
- First/last occurrence notes
- Verse structure notes (word count, letter count, symmetry)
- Parallel verse references within Genesis
"""
import json, re, sys, math
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

def count_letters(heb):
    return sum(1 for ch in strip_n(heb) if '\u05D0' <= ch <= '\u05EA')

# Notable gematria values
NOTABLE_VALUES = {
    18: 'chai (life)', 26: 'YHWH', 36: 'double-chai',
    72: 'chesed (kindness)', 86: 'Elohim', 137: 'Kabbalah',
    248: 'positive mitzvot', 314: 'Shaddai', 345: 'Moshe',
    358: 'Mashiach', 365: 'negative mitzvot', 400: 'tav (completion)',
    541: 'Yisrael', 613: 'total mitzvot',
}

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Pre-compute: root frequency across all of Genesis
root_freq = Counter()
root_first = {}  # root -> first verse ref
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            r = w.get('root', '')
            if r:
                root_freq[r] += 1
                if r not in root_first:
                    root_first[r] = v['ref']

# Pre-compute: word gematria frequency
gem_freq = Counter()
gem_words = {}  # gematria value -> list of (word, ref)
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            g = w.get('gem', 0)
            if g > 10:
                gem_freq[g] += 1
                key = strip_n(w['heb']).replace('\u05BE', '')
                if g not in gem_words:
                    gem_words[g] = set()
                gem_words[g].add(key)

enriched = 0
for c in d['chapters']:
    for v in c['verses']:
        # Check how much content this verse already has
        existing = sum(len(v.get(k, '')) for k in ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim', 'gem_note', 'cross_refs'])

        # Only enrich verses that need it (thin content)
        if existing > 800:
            v['insights'] = ''
            continue

        insights = []

        # 1. Word and letter count
        num_words = len(v['words'])
        num_letters = sum(count_letters(w['heb']) for w in v['words'])
        if num_words == 7 or num_letters == 28 or num_letters % 7 == 0:
            insights.append(f"This verse contains {num_words} words and {num_letters} letters.")
        elif num_words > 0:
            insights.append(f"Verse structure: {num_words} words, {num_letters} letters.")

        # 2. Notable individual word gematria values
        for w in v['words']:
            g = w.get('gem', 0)
            if g in NOTABLE_VALUES:
                eng = w.get('eng', '')
                nota = NOTABLE_VALUES[g]
                # Don't note if it's the obvious word (Elohim = 86)
                if nota.split('(')[0].strip().lower() not in eng.lower():
                    insights.append(f"The word \"{eng}\" ({w['heb']}) has gematria {g}, equal to {nota}.")
                    break

        # 3. Root frequency insights
        roots_in_verse = set()
        for w in v['words']:
            r = w.get('root', '')
            if r and r not in roots_in_verse:
                roots_in_verse.add(r)
                freq = root_freq.get(r, 0)
                if freq == 1:
                    insights.append(f"The root {r} appears only once in all of Genesis (hapax legomenon).")
                elif freq <= 3:
                    insights.append(f"The root {r} is rare in Genesis, appearing only {freq} times.")
                elif freq >= 100:
                    insights.append(f"The root {r} is one of the most common in Genesis ({freq} occurrences).")
                if len(insights) >= 4:
                    break

        # 4. First occurrence notes
        for w in v['words']:
            r = w.get('root', '')
            if r and root_first.get(r) == v['ref']:
                eng = w.get('eng', r)
                insights.append(f"First appearance of the root {r} (\"{eng}\") in the Torah.")
                break

        # 5. Gematria connections between words in this verse
        verse_gems = {}
        for w in v['words']:
            g = w.get('gem', 0)
            if g > 10:
                if g not in verse_gems:
                    verse_gems[g] = []
                verse_gems[g].append(w)
        for g, words_with_g in verse_gems.items():
            if len(words_with_g) >= 2:
                # Different words with same gematria
                unique_cons = set(strip_n(w['heb']).replace('\u05BE', '') for w in words_with_g)
                if len(unique_cons) >= 2:
                    w1 = words_with_g[0]
                    w2 = words_with_g[1]
                    insights.append(f"\"{w1['eng']}\" and \"{w2['eng']}\" share the same gematria value of {g}.")
                    break

        # 6. Verse total properties
        total = v.get('total_gematria', 0)
        if total > 0:
            # Check if divisible by notable numbers
            if total % 26 == 0:
                insights.append(f"The verse total ({total}) is divisible by 26 (YHWH).")
            elif total % 18 == 0:
                insights.append(f"The verse total ({total}) is divisible by 18 (chai/life).")

        # Combine insights
        combined = ' '.join(insights)
        if len(combined) > 1500:
            combined = combined[:1497] + '...'
        v['insights'] = combined
        if combined:
            enriched += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Enriched {enriched} verses with computed insights")

# Recheck content gaps
thin = 0
for c in d['chapters']:
    for v in c['verses']:
        total = sum(len(v.get(k, '')) for k in ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim', 'gem_note', 'cross_refs', 'insights'])
        if total < 300:
            thin += 1
print(f"Verses still thin after enrichment: {thin}")
