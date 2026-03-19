#!/usr/bin/env python3
"""
Fix Exodus data to match Genesis v7 gold standard.
====================================================
Fixes:
1. Merge split words (לֵ + וִי = לֵוִי Levi, etc.)
2. Fill missing roots from ETCBC lex data
3. Compute parasha stats and gematria_note
4. Add Hebrew names to parasha data
5. Add missing verse fields (cross_refs, insights if empty)
"""

import json, re, sys
from pathlib import Path
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)


# ═══ Fix 1: Merge split words ═══════════════════════════════════════════

# Known split patterns: consonantal form -> (merged_heb_pattern, correct_eng)
MERGE_RULES = {
    'לוי': ('Levi', 'לוי'),
}

def fix_word_splits(data):
    """Merge incorrectly split words like לֵ + וִי -> לֵוִי."""
    fixed = 0
    for ch in data['chapters']:
        for v in ch['verses']:
            words = v.get('words', [])
            i = 0
            new_words = []
            while i < len(words):
                if i + 1 < len(words):
                    h1 = words[i]['heb']
                    h2 = words[i+1]['heb']
                    c1 = strip_n(h1).replace('\u05BE', '')
                    c2 = strip_n(h2).replace('\u05BE', '')
                    combined = c1 + c2

                    if combined in MERGE_RULES:
                        correct_eng, root = MERGE_RULES[combined]
                        merged = {
                            'heb': h1 + h2,
                            'eng': correct_eng,
                            'root': root,
                            'tr': words[i].get('tr', '') + words[i+1].get('tr', ''),
                            'gem': words[i].get('gem', 0) + words[i+1].get('gem', 0),
                        }
                        if 'meanings' in words[i]:
                            merged['meanings'] = words[i]['meanings']
                        new_words.append(merged)
                        fixed += 1
                        i += 2
                        continue

                new_words.append(words[i])
                i += 1

            v['words'] = new_words

    return fixed


# ═══ Fix 2: Fill missing roots from ETCBC ═══════════════════════════════

def fill_roots(data):
    """Fill missing root fields using ETCBC lex data."""
    etcbc_path = BASE / 'references' / 'etcbc_exodus_by_verse.json'
    with open(etcbc_path, 'r', encoding='utf-8') as f:
        etcbc = json.load(f)

    filled = 0
    for ch in data['chapters']:
        for v in ch['verses']:
            ref = f"{ch['chapter']}:{v['verse']}"
            etcbc_verse = etcbc.get(ref, [])

            for w in v.get('words', []):
                if w.get('root'):
                    continue

                # Try to match by Hebrew consonants
                our_cons = strip_n(w['heb']).replace('\u05BE', '').replace(' ', '')

                # Walk ETCBC morphemes trying to match
                acc = ''
                for em in etcbc_verse:
                    acc_test = acc + em['cons'].replace(' ', '')
                    if acc_test == our_cons:
                        lex = em.get('lex', '')
                        if lex:
                            w['root'] = strip_n(lex)
                            filled += 1
                        break
                    elif our_cons.startswith(acc_test):
                        acc = acc_test
                    else:
                        acc = em['cons'].replace(' ', '')
                        if acc == our_cons:
                            lex = em.get('lex', '')
                            if lex:
                                w['root'] = strip_n(lex)
                                filled += 1
                            break

    return filled


# ═══ Fix 3: Compute parasha stats ═══════════════════════════════════════

GEMATRIA_MAP = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50,
    'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400,
}

def compute_parasha_stats(data, parasha):
    """Compute stats for a parasha from word data."""
    sc, sv = parasha['start_chapter'], parasha['start_verse']
    ec, ev = parasha['end_chapter'], parasha['end_verse']

    verses = 0
    words = 0
    total_gem = 0
    roots = set()

    for ch in data['chapters']:
        cn = ch['chapter']
        for v in ch['verses']:
            vn = v['verse']
            in_range = False
            if cn > sc and cn < ec:
                in_range = True
            elif cn == sc and cn == ec:
                in_range = vn >= sv and vn <= ev
            elif cn == sc:
                in_range = vn >= sv
            elif cn == ec:
                in_range = vn <= ev

            if not in_range:
                continue

            verses += 1
            for w in v.get('words', []):
                words += 1
                gem = w.get('gem', 0)
                if isinstance(gem, int):
                    total_gem += gem
                root = w.get('root', '')
                if root:
                    roots.add(root)

    return {
        'verses': verses,
        'words': words,
        'total_gematria': total_gem,
        'unique_roots': len(roots),
    }


def make_gematria_note(total_gem):
    """Generate a meaningful gematria note (no math noise)."""
    notable = {
        26: "the gematria of God's name (YHWH)",
        7: "the number of completion",
        10: "the number of divine utterances",
        12: "the number of tribes",
        18: "the number of life (chai)",
        40: "the number of trial and transformation",
    }
    for div, meaning in notable.items():
        if total_gem % div == 0 and total_gem > div * 2:
            return f"Total gematria {total_gem:,} is divisible by {div}, {meaning}."
    return f"Total gematria: {total_gem:,}"


# ═══ Fix 4: Add Hebrew names to parasha data ═══════════════════════════

PARASHA_HEBREW = {
    "Shemot": "\u05E9\u05C1\u05B0\u05DE\u05D5\u05B9\u05EA",
    "Va'era": "\u05D5\u05B8\u05D0\u05B5\u05E8\u05B8\u05D0",
    "Bo": "\u05D1\u05B9\u05BC\u05D0",
    "Beshalach": "\u05D1\u05B0\u05BC\u05E9\u05C1\u05B7\u05DC\u05B7\u05BC\u05D7",
    "Yitro": "\u05D9\u05B4\u05EA\u05B0\u05E8\u05D5\u05B9",
    "Mishpatim": "\u05DE\u05B4\u05E9\u05C1\u05B0\u05E4\u05B8\u05BC\u05D8\u05B4\u05D9\u05DD",
    "Terumah": "\u05EA\u05B0\u05BC\u05E8\u05D5\u05BC\u05DE\u05B8\u05D4",
    "Tetzaveh": "\u05EA\u05B0\u05BC\u05E6\u05B7\u05D5\u05B6\u05BC\u05D4",
    "Ki Tisa": "\u05DB\u05B4\u05BC\u05D9 \u05EA\u05B4\u05E9\u05B8\u05BC\u05C2\u05D0",
    "Vayakhel": "\u05D5\u05B7\u05D9\u05B7\u05BC\u05E7\u05B0\u05D4\u05B5\u05DC",
    "Pekudei": "\u05E4\u05B0\u05E7\u05D5\u05BC\u05D3\u05B5\u05D9",
}


# ═══ Fix 5: Ensure all verse fields match Genesis ═══════════════════════

GENESIS_VERSE_FIELDS = ['chizkuni', 'cross_refs', 'gem_note', 'hebrew_full',
                        'ibn_ezra', 'insights', 'kli_yakar', 'onkelos',
                        'or_hachaim', 'rabbeinu_bahya', 'ramban', 'rashi',
                        'ref', 'sforno', 'total_gematria', 'translation',
                        'verse', 'words']

def ensure_verse_fields(data):
    """Make sure every verse has the same fields as Genesis v7."""
    added = 0
    for ch in data['chapters']:
        for v in ch['verses']:
            for field in GENESIS_VERSE_FIELDS:
                if field not in v:
                    if field == 'words':
                        continue  # Don't overwrite
                    v[field] = '' if field != 'total_gematria' else 0
                    added += 1
    return added


# ═══ Main ═══════════════════════════════════════════════════════════════

def main():
    print("Loading Exodus data...")
    with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Fix 1: Merge split words
    print("\nFix 1: Merging split words...")
    merged = fix_word_splits(data)
    print(f"  Merged {merged} split words")

    # Fix 2: Fill missing roots
    print("\nFix 2: Filling missing roots...")
    filled = fill_roots(data)
    print(f"  Filled {filled} roots")

    # Check remaining missing roots
    total_w = 0
    no_root = 0
    for ch in data['chapters']:
        for v in ch['verses']:
            for w in v.get('words', []):
                total_w += 1
                if not w.get('root', ''):
                    no_root += 1
    print(f"  Remaining missing: {no_root}/{total_w} ({100*no_root/total_w:.1f}%)")

    # Fix 5: Ensure verse fields
    print("\nFix 5: Ensuring all verse fields present...")
    added = ensure_verse_fields(data)
    print(f"  Added {added} missing fields")

    # Save
    with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\nSaved exodus_fixed.json")

    # Fix 3+4: Parasha data
    print("\nFix 3+4: Updating parasha data...")
    with open(BASE / 'books' / 'torah' / 'parasha_exodus.json', 'r', encoding='utf-8') as f:
        parashot = json.load(f)

    for p in parashot:
        # Add Hebrew name
        he = PARASHA_HEBREW.get(p['name'], '')
        if he:
            p['he'] = he

        # Compute stats
        stats = compute_parasha_stats(data, p)
        p['stats'] = stats
        p['gematria_note'] = make_gematria_note(stats['total_gematria'])
        print(f"  {p['name']:15s} {stats['verses']:4d}v {stats['words']:5d}w gem={stats['total_gematria']:,}")

    with open(BASE / 'books' / 'torah' / 'parasha_exodus.json', 'w', encoding='utf-8') as f:
        json.dump(parashot, f, ensure_ascii=False, indent=2)
    print("Saved parasha_exodus.json")


if __name__ == '__main__':
    main()
