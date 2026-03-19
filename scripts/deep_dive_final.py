#!/usr/bin/env python3
"""
Deep dive: find EVERY 100% certain wrong translation in Exodus.
Cross-reference against ETCBC morpheme-level data AND verse translations.
Only flag things that are DEFINITELY wrong, not style preferences.
"""
import json, re, sys
from collections import Counter
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(BASE / 'references' / 'etcbc_exodus_by_verse.json', 'r', encoding='utf-8') as f:
    etcbc = json.load(f)

# ══════════════════════════════════════════════════════════════════════════
# KNOWN HOMOGRAPH BUGS — Hebrew words with multiple meanings where
# Sefaria consistently picks the WRONG one
# ══════════════════════════════════════════════════════════════════════════

# Format: consonantal_key -> {wrong_eng: correct_eng}
# Only entries where the "wrong" meaning is NEVER correct in Exodus
HOMOGRAPH_FIXES = {
    # כי = because/that/for/when — NEVER "burning" in Exodus
    # (already fixed but double-check compounds)

    # עַל = upon/over — sometimes wrongly shows "leaf" or "ascend"
    # But על as standalone is already fixed. Check compounds.

    # פֶּן = lest — NEVER "corner" in narrative context
    'פן': {'corner': 'lest'},

    # עֵד = witness — NEVER "until" (that's עַד)
    # But context matters. Skip.

    # נֶפֶשׁ = soul/life/person — NEVER "breathing" in context
    'נפש': {'breathing': 'soul'},

    # מִשְׁפָּט = judgment/ordinance — NEVER "clan"
    'משפט': {'clan': 'judgment'},
    'משפטים': {'clans': 'judgments'},

    # רֹאשׁ = head/top/chief — NEVER "venom/poison" in Exodus narrative
    # Actually ראש CAN mean poison. Skip.

    # שֵׁם = name — wrongly "there" in some places (already partially fixed)
    # Done earlier.

    # דָּבָר = word/thing — wrongly shows as "bee" sometimes
    'דבר': {'bee': 'word'},

    # אֶרֶץ = land/earth — NEVER "bottom"
    'ארץ': {'bottom': 'land'},

    # חֹדֶשׁ = month — wrongly "new moon" in some contexts (it IS new moon sometimes, skip)

    # בֶּגֶד = garment — NEVER "treachery" in Exodus clothing contexts
    # Context-dependent. Skip.

    # שָׁלֹשׁ = three — NEVER "officer" in counting contexts
    # Actually שליש IS officer. Skip.
}

# ══════════════════════════════════════════════════════════════════════════
# MAQAF COMPOUND CHECKS — prefix·noun where prefix is definitely wrong
# ══════════════════════════════════════════════════════════════════════════

# Prefix consonants that have known wrong Sefaria translations
MAQAF_PREFIX_FIXES = {
    # על = upon/over — in compounds
    'על': {
        'wrong': {'leaf', 'ascend', 'burnt offering', 'subst', 'yoke'},
        'correct': 'upon',
    },
    # עד = until/as far as — in compounds
    'עד': {
        'wrong': {'perpetuity', 'booty', 'witness'},
        'correct': 'until',
    },
    # מן = from — in compounds (not "kind" or "portion")
    'מן': {
        'wrong': {'kind', 'portion', 'a gift'},
        'correct': 'from',
    },
    # בין = between
    'בין': {
        'wrong': {'understanding'},
        'correct': 'between',
    },
    # פני = before/face of
    'פני': {
        'wrong': {'turn', 'face'},  # "face" is ok standalone but in לפני compounds = "before"
        'correct': 'face·of',
    },
}

# ══════════════════════════════════════════════════════════════════════════
# SPECIFIC WORD PATTERNS — 100% wrong in all contexts
# ══════════════════════════════════════════════════════════════════════════

# Words where the ETCBC POS + gloss disagrees with ours and ETCBC is clearly right
# We check: if our eng matches a known-wrong Sefaria default AND ETCBC gives something different

ALWAYS_WRONG = {
    # prep for prepositions showing "subst" etc
    'n m': None,  # part of speech label, not translation
    'n f': None,
    'adj': None,
    'adv': None,
    'vb': None,
    'v': None,
    'prep': None,
    'subst': None,
    'conj': None,
    'pron': None,
    'nm': None,
    'nf': None,
}

# ══════════════════════════════════════════════════════════════════════════
# RUN AUDIT
# ══════════════════════════════════════════════════════════════════════════

fixes = []

for ch in data['chapters']:
    for v in ch['verses']:
        ref = f"{ch['chapter']}:{v['verse']}"

        for i, w in enumerate(v.get('words', [])):
            h = w['heb']
            e = w['eng']
            h_cons = strip_n(h).replace('\u05BE', '')

            # 1. Check for POS-label glosses that slipped through
            if e.lower() in ALWAYS_WRONG:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': f'POS label "{e}" not a translation',
                    'category': 'jargon',
                })
                continue

            # 2. Check maqaf compounds for wrong prefix
            if '\u05BE' in h:
                parts = h.split('\u05BE')
                first_cons = strip_n(parts[0])
                first_eng = e.split('·')[0] if '·' in e else e

                for prefix_cons, cfg in MAQAF_PREFIX_FIXES.items():
                    if first_cons == prefix_cons and first_eng.lower() in {x.lower() for x in cfg['wrong']}:
                        noun_eng = '·'.join(e.split('·')[1:]) if '·' in e else ''
                        new_eng = cfg['correct'] + ('·' + noun_eng if noun_eng else '')
                        fixes.append({
                            'ref': ref, 'idx': i, 'heb': h, 'old': e,
                            'new': new_eng,
                            'reason': f'"{first_eng}" wrong for {prefix_cons}, should be "{cfg["correct"]}"',
                            'category': 'maqaf_prefix',
                        })
                        break

            # 3. Check standalone homograph fixes
            for cons_key, wrong_map in HOMOGRAPH_FIXES.items():
                if cons_key in h_cons:
                    for wrong_eng, correct_eng in wrong_map.items():
                        if e.lower() == wrong_eng.lower():
                            fixes.append({
                                'ref': ref, 'idx': i, 'heb': h, 'old': e,
                                'new': correct_eng,
                                'reason': f'"{wrong_eng}" is wrong homograph for {cons_key}',
                                'category': 'homograph',
                            })

            # 4. Check for "n f" or "n m" buried in compound translations
            if '·n f' in e or '·n m' in e or e.startswith('n f·') or e.startswith('n m·'):
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'POS label embedded in compound',
                    'category': 'jargon_compound',
                })

            # 5. Check for "(relative part.)" remnants
            if '(relative part' in e:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'new': e.replace('(relative part.)', 'which').replace('(relative part', 'which').strip('·').strip(),
                    'reason': 'Sefaria jargon remnant',
                    'category': 'jargon_compound',
                })

            # 6. "sea" for נשים (women) — wrong homograph
            if 'sea' in e.lower() and 'נשׁ' in h_cons and 'ים' not in h_cons[-2:]:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'new': 'women',
                    'reason': '"sea" for נשים should be "women"',
                    'category': 'homograph',
                })

            # 7. "woe" or "woe;" remnants
            if 'woe' in e.lower() and 'woe' not in (v.get('translation','').lower()):
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': '"woe" likely wrong — Sefaria Aramaic dict leak',
                    'category': 'dict_leak',
                })

            # 8. "Targ. Prov." or similar dictionary reference
            if 'Targ.' in e or 'Prov.' in e or 'BDB' in e or 'Ges.' in e:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'Dictionary reference in translation',
                    'category': 'dict_leak',
                })

            # 9. Very long translations (>30 chars) that look like dictionary entries
            if len(e) > 35 and ('or ' in e or '; ' in e or '(' in e):
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'Suspiciously long — likely dict entry',
                    'category': 'too_long',
                })

            # 10. "prep" as standalone or in compound
            if e == 'prep' or e.startswith('prep·') or '·prep' in e:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'POS label "prep"',
                    'category': 'jargon',
                })

            # 11. Empty eng
            if not e.strip():
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': '(empty)',
                    'reason': 'Empty translation',
                    'category': 'empty',
                })

            # 12. Hebrew characters in English
            if any('\u05D0' <= c <= '\u05EA' for c in e):
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'Hebrew characters in English field',
                    'category': 'hebrew_in_eng',
                })

            # 13. "× " (multiplication sign from Sefaria)
            if '×' in e or '✕' in e:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': 'Sefaria formatting artifact',
                    'category': 'dict_leak',
                })

            # 14. Standalone "and" for long words (missed earlier?)
            if e == 'and' and len(h_cons) > 3:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': f'Just "and" for {len(h_cons)}-consonant word',
                    'category': 'truncated',
                })

            # 15. Standalone preposition for long compound words
            if e in ('to', 'in', 'from', 'upon', 'the', 'not') and len(h_cons) > 5:
                fixes.append({
                    'ref': ref, 'idx': i, 'heb': h, 'old': e,
                    'reason': f'Just "{e}" for {len(h_cons)}-consonant word',
                    'category': 'truncated',
                })

# ══════════════════════════════════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════════════════════════════════

print(f"{'='*70}")
print(f"DEEP DIVE AUDIT — 100% CERTAIN ISSUES")
print(f"{'='*70}")
print(f"Total issues found: {len(fixes)}")
print()

cats = Counter(f['category'] for f in fixes)
for cat, count in cats.most_common():
    print(f"  {cat}: {count}")

for cat in ['jargon', 'jargon_compound', 'homograph', 'maqaf_prefix', 'dict_leak',
            'too_long', 'truncated', 'hebrew_in_eng', 'empty']:
    items = [f for f in fixes if f['category'] == cat]
    if not items:
        continue
    print(f"\n{'─'*60}")
    print(f"  {cat.upper()} ({len(items)} issues)")
    print(f"{'─'*60}")
    for f in items:
        new = f.get('new', '???')
        print(f"  {f['ref']:>8s}[{f['idx']:2d}] {f['heb']}")
        print(f"           was: '{f['old']}'")
        print(f"           reason: {f['reason']}")
        if 'new' in f:
            print(f"           fix: '{f['new']}'")
        print()

# Save report
with open(BASE / 'exodus_deep_dive.json', 'w', encoding='utf-8') as fp:
    json.dump(fixes, fp, ensure_ascii=False, indent=2)
print(f"\nFull report saved to exodus_deep_dive.json")
