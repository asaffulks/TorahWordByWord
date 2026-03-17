#!/usr/bin/env python3
"""
Build multi-meaning word data for Genesis.
For each word, extract ALL meanings from Sefaria lexicon.
Adds 'meanings' field to each word: list of alternative meanings.
The 'eng' field stays as the primary/contextual meaning.
"""
import json, re, sys, os, html as htmlmod
from pathlib import Path
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

CACHE_DIR = Path("sefaria_cache")

def get_all_meanings(hebrew_word):
    """Get ALL meanings for a Hebrew word from Sefaria cache."""
    clean = strip_n(hebrew_word).replace('\u05BE', '')
    if not clean:
        return []

    # Try the word itself, then stripped versions
    candidates = [clean]
    # Strip common prefixes: ו, ה, ב, ל, מ, כ, ש
    for pfx in ['ו', 'ה', 'ב', 'ל', 'מ', 'כ', 'ש', 'וה', 'וב', 'ול', 'ומ']:
        if clean.startswith(pfx) and len(clean) > len(pfx) + 1:
            candidates.append(clean[len(pfx):])

    all_meanings = []
    seen = set()

    for word in candidates:
        # Find cache file
        safe_key = re.sub(r'[<>:"/\\|?*()[\]{}]', '', word)
        cache_file = CACHE_DIR / f"word_{safe_key}.json"
        if not cache_file.exists():
            continue

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue

        if not isinstance(data, list):
            continue

        for entry in data:
            if not isinstance(entry, dict):
                continue
            content = entry.get('content', {})
            if not isinstance(content, dict):
                continue

            senses = content.get('senses', [])
            for sense in senses:
                if not isinstance(sense, dict):
                    continue

                # Top-level definition
                defn = sense.get('definition', '')
                if isinstance(defn, str) and defn:
                    clean_def = re.sub(r'<[^>]+>', '', defn)
                    clean_def = htmlmod.unescape(clean_def).strip()
                    # Take first meaning before comma, clean up
                    parts = clean_def.split(',')
                    for part in parts[:3]:
                        part = part.strip().strip('.')
                        if part and len(part) > 1 and len(part) < 40 and part.lower() not in seen:
                            if not any(c in part for c in '<>&{}[]'):
                                all_meanings.append(part)
                                seen.add(part.lower())

                # Sub-senses
                for sub in sense.get('senses', [])[:5]:
                    if isinstance(sub, dict):
                        sub_def = sub.get('definition', '')
                        if isinstance(sub_def, str) and sub_def:
                            clean_sub = re.sub(r'<[^>]+>', '', sub_def)
                            clean_sub = htmlmod.unescape(clean_sub).strip()
                            parts = clean_sub.split(',')
                            for part in parts[:2]:
                                part = part.strip().strip('.')
                                if part and len(part) > 1 and len(part) < 40 and part.lower() not in seen:
                                    if not any(c in part for c in '<>&{}[]'):
                                        all_meanings.append(part)
                                        seen.add(part.lower())

    # Remove the primary meaning (already in 'eng' field) and junk
    JUNK = {'adj', 'n m', 'n f', 'nm', 'nf', 'v', 'vb', 'prep', 'conj', 'pron',
            'adv', 'subst', 'interj', 'sign of the definite direct object',
            '(relative part.)', 'not translated in English'}
    filtered = [m for m in all_meanings if m.lower() not in JUNK and len(m) > 1]

    return filtered[:6]  # max 6 alternative meanings


# Load genesis.json
with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Process every word
total_words = 0
words_with_meanings = 0
meaning_cache = {}  # consonantal form -> meanings list

for c in d['chapters']:
    ch_num = c['chapter']
    if ch_num % 10 == 0:
        print(f"  Chapter {ch_num}...")
    for v in c['verses']:
        for w in v['words']:
            total_words += 1
            key = strip_n(w['heb']).replace('\u05BE', '')

            if key in meaning_cache:
                meanings = meaning_cache[key]
            else:
                meanings = get_all_meanings(w['heb'])
                meaning_cache[key] = meanings

            # Filter out the primary meaning from alternatives
            primary = w['eng'].lower().replace('\u00B7', ' ')
            alt_meanings = [m for m in meanings
                          if m.lower() != primary
                          and m.lower() not in primary
                          and primary not in m.lower()]

            w['meanings'] = alt_meanings[:5]  # max 5 alternatives
            if alt_meanings:
                words_with_meanings += 1

# Save
with open('K:/TorahByWord/genesis_multi.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"\nDone: {total_words} words, {words_with_meanings} with alternative meanings")
print(f"Saved to genesis_multi.json")

# Show samples
print("\nSamples:")
for v in d['chapters'][0]['verses'][:3]:
    print(f"\n{v['ref']}:")
    for w in v['words']:
        alt = w.get('meanings', [])
        alt_str = f"  [{', '.join(alt[:3])}]" if alt else ""
        print(f"  {w['heb']:18s}  {w['eng']:20s}{alt_str}")
