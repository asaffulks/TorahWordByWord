#!/usr/bin/env python3
"""
Fix word splits — merge incorrectly fragmented Hebrew words.
==============================================================
The Sefaria data sometimes splits words at arbitrary points,
creating 1-consonant fragments. This script merges them back.

Works on any book. Run BEFORE PDF generation.

Usage:
  python fix_word_splits.py books/torah/exodus_fixed.json
"""

import json, re, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Known standalone 1-consonant words that should NOT be merged
LEGIT_SINGLE = set()  # None in Biblical Hebrew are truly 1-consonant standalone

# Known 2-consonant standalone words
LEGIT_TWO = {
    'לא', 'כי', 'אם', 'אל', 'על', 'עד', 'גם', 'כל', 'מה', 'אך', 'אף',
    'גד', 'דן', 'אב', 'אח', 'יד', 'פה', 'דם', 'חי', 'רע', 'שם', 'כה',
    'מי', 'בו', 'בה', 'בי', 'לו', 'לי', 'לה', 'בן', 'בת', 'את', 'מן',
    'עם', 'כן', 'אז', 'לך', 'שב', 'קם', 'בא', 'רב', 'זה', 'זר', 'או',
    'גר', 'שר', 'דר', 'סר', 'חם', 'נא', 'עז', 'אש', 'חק', 'הם', 'הן',
}

# Known correct merges: consonantal_combined -> english_gloss
# Only used for specific known-bad patterns
KNOWN_MERGES = {
    'לוי': 'Levi',
    'הלוי': 'the·Levite',
}

GEMATRIA_MAP = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50,
    'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400,
}

# Prefix glosses: what the single-letter prefix means
PREFIX_GLOSSES = {
    'ל': 'to',
    'ב': 'in',
    'כ': 'like',
    'מ': 'from',
    'ה': 'the',
    'ו': 'and',
}


def calc_gem(heb):
    return sum(GEMATRIA_MAP.get(c, 0) for c in strip_n(heb))


def merge_words(w1, w2, override_eng=None):
    """Merge two word objects into one."""
    merged_heb = w1['heb'] + w2['heb']

    if override_eng:
        merged_eng = override_eng
    else:
        # Combine English: prefix·rest
        e1 = w1.get('eng', '').strip()
        e2 = w2.get('eng', '').strip()
        if e1 and e2:
            merged_eng = f"{e1}·{e2}"
        elif e2:
            merged_eng = e2
        else:
            merged_eng = e1

    merged = {
        'heb': merged_heb,
        'eng': merged_eng,
        'root': w2.get('root', '') or w1.get('root', ''),
        'tr': (w1.get('tr', '') + w2.get('tr', '')).strip(),
        'gem': (w1.get('gem', 0) or 0) + (w2.get('gem', 0) or 0),
    }
    if 'meanings' in w2:
        merged['meanings'] = w2['meanings']
    elif 'meanings' in w1:
        merged['meanings'] = w1['meanings']
    return merged


def fix_splits(data):
    """Merge single-consonant fragments with their next word."""
    total_merged = 0

    for ch in data['chapters']:
        for v in ch['verses']:
            words = v.get('words', [])
            new_words = []
            i = 0

            while i < len(words):
                w = words[i]
                cons = strip_n(w['heb']).replace('\u05BE', '').replace(' ', '')

                # Check if this is a single-consonant fragment
                if len(cons) == 1 and i + 1 < len(words):
                    next_w = words[i + 1]
                    combined_cons = cons + strip_n(next_w['heb']).replace('\u05BE', '').replace(' ', '')

                    # Check for known merges
                    override = KNOWN_MERGES.get(combined_cons)

                    # Merge: single prefix letter + next word
                    merged = merge_words(w, next_w, override)
                    new_words.append(merged)
                    total_merged += 1
                    i += 2
                    continue

                # Check if this is an orphaned 2-consonant fragment that's not legit
                # (e.g., 'וי' from a Levi split where first part was already consumed)
                if len(cons) == 2 and cons not in LEGIT_TWO:
                    # Check if it looks like a suffix fragment (ו + something)
                    if cons.startswith('ו') and i + 1 < len(words):
                        # Could be an orphaned vav + next letter — check if merging makes sense
                        next_w = words[i + 1]
                        next_cons = strip_n(next_w['heb']).replace('\u05BE', '').replace(' ', '')
                        combined_cons = cons + next_cons
                        override = KNOWN_MERGES.get(combined_cons)
                        if override:
                            merged = merge_words(w, next_w, override)
                            new_words.append(merged)
                            total_merged += 1
                            i += 2
                            continue

                new_words.append(w)
                i += 1

            v['words'] = new_words

    return total_merged


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_word_splits.py <input.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"ERROR: {filepath} not found")
        sys.exit(1)

    print(f"Loading {filepath.name}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Count before
    total_before = sum(len(v.get('words', [])) for ch in data['chapters'] for v in ch['verses'])

    merged = fix_splits(data)

    total_after = sum(len(v.get('words', [])) for ch in data['chapters'] for v in ch['verses'])

    print(f"Merged {merged} fragments")
    print(f"Words: {total_before} -> {total_after}")

    # Verify: check for remaining 1-consonant words
    remaining = []
    for ch in data['chapters']:
        for v in ch['verses']:
            for i, w in enumerate(v.get('words', [])):
                cons = strip_n(w['heb']).replace('\u05BE', '').replace(' ', '')
                if len(cons) == 1:
                    remaining.append(f"  {ch['chapter']}:{v['verse']}[{i}] '{w['heb']}' -> '{w['eng']}'")

    if remaining:
        print(f"\nWARNING: {len(remaining)} single-consonant words still remain:")
        for r in remaining[:10]:
            print(r)
    else:
        print("\nNo single-consonant fragments remain.")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {filepath.name}")


if __name__ == '__main__':
    main()
