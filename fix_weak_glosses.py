#!/usr/bin/env python3
"""
Fix 284 weak word-level glosses in genesis_v3.json.

Targets words where eng is just "to", "and", "see", or "be" —
these lost their contextual meaning and need reconstruction from
Hebrew morphology and ETCBC cross-reference data.
"""

import json
import sys
import os
import unicodedata
import shutil

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GENESIS_FILE = os.path.join(os.path.dirname(__file__), 'genesis_v3.json')
BACKUP_FILE = os.path.join(os.path.dirname(__file__), 'genesis_v3_backup.json')
ETCBC_FILE = os.path.join(os.path.dirname(__file__), 'references', 'etcbc_genesis_by_verse.json')


def strip_niqqud(s):
    """Remove all Hebrew vowel points (niqqud), cantillation marks, and combining marks."""
    # Remove maqaf (Hebrew hyphen) too so compound words merge
    s = s.replace('\u05BE', '')  # maqaf ־
    return ''.join(
        c for c in s
        if unicodedata.category(c) not in ('Mn', 'Cf')
        and c not in (
            '\u05B0', '\u05B1', '\u05B2', '\u05B3', '\u05B4', '\u05B5',
            '\u05B6', '\u05B7', '\u05B8', '\u05B9', '\u05BA', '\u05BB',
            '\u05BC', '\u05BD', '\u05BF', '\u05C0', '\u05C1', '\u05C2',
            '\u05C3', '\u05C4', '\u05C5', '\u05C7',
        )
    )


# ─────────────────────────────────────────────
#  1. "to" — prepositions with pronominal suffixes
# ─────────────────────────────────────────────
# Keyed by consonantal form (niqqud stripped, maqaf removed)
TO_LOOKUP = {
    # ל + suffix
    'לו':   'to·him',
    'לה':   'to·her',
    'לך':   'to·you',      # masc default; context rarely female in Genesis
    'לי':   'to·me',
    'להם':  'to·them',
    'להן':  'to·them(f)',
    'לנו':  'to·us',
    'למו':  'to·them',     # archaic/poetic form

    # אל + suffix  (el = "to/toward")
    'אלי':  'to·me',
    'אליו': 'to·him',
    'אליה': 'to·her',
    'אליהם':'to·them',
    'אלהם': 'to·them',
    'אליך': 'to·you',
    'אלינו':'to·us',

    # על + suffix  (al = "upon/on")
    'עליו': 'upon·him',
    'עליה': 'upon·her',
    'עליהם':'upon·them',
    'עלי':  'upon·me',
    'עליך': 'upon·you',
    'עלינו':'upon·us',

    # bare prepositions (no suffix) — these are legitimately just "to"
    'אל':   'to',          # will try ETCBC fallback
    'ל':    'to',
}

# Special overrides by chapter:verse for tricky cases
TO_OVERRIDES = {
    # 14:22 אֵל = "God" (El), not "to"
    ('14:22', 'אל'): 'God',
    # 20:13 אֶל = plain "to" — but it's a standalone preposition, leave it
}


# ─────────────────────────────────────────────
#  2. "see" — forms of ראה
# ─────────────────────────────────────────────
SEE_LOOKUP = {
    # Perfect (past)
    'ראה':    'saw',            # 3ms — context may need "he·saw"
    'ראתה':   'she·saw',
    'ראית':   'you·saw',
    'ראיתי':  'I·saw',
    'ראינו':  'we·saw',
    'ראו':    'they·saw',
    'ראם':    'he·saw·them',
    'ראיתם':  'you(pl)·saw',
    'ראיתיו': 'I·saw·him',

    # Imperfect
    'ירא':    'let·(him)·see',  # jussive
    'יראה':   'will·see',       # also "the LORD will see/provide"
    'תרא':    'she·was·seen',
    'תתראו':  'look·at·one·another',
    'אראה':   'I·will·see',

    # Imperative
    'ראה':    'saw',            # (also imperative "see!" — but 3ms past more common in Genesis)

    # Infinitive
    'לראות':  'to·see',
    'לראת':   'to·see',
    'ראות':   'seeing',
    'ראותי':  'my·seeing',
    'מראת':   'from·seeing',

    # Niphal (passive)
    'נראו':   'were·seen',
    'הנראה':  'the·one·appearing',

    # Hiphil (causative)
    'הראה':   'showed',
    'אראך':   'I·will·show·you',
    'אראנו':  'I·will·see·him',  # or "let me see him"

    # With prefixes
    'וראה':   'and·saw',
    'וארא':   'and·I·saw',
    'ואראה':  'and·I·will·see',
    'ואראנו': 'and·I·will·see·him',
    'וראיתיה':'and·I·will·see·it',
    'כראת':   'when·seeing',
    'כראותה': 'when·she·saw',
    'כראותו': 'when·he·saw',
}

# Overrides for specific verse references where context matters
SEE_OVERRIDES = {
    # 22:14 יראה = "will provide" (Moriah theophany)
    ('22:14', 'יראה', 0): 'will·provide',
    ('22:14', 'יראה', 1): 'will·be·seen',
    # 24:62 ראי = Beer Lahai Roi (place name)
    # Actually this one has eng="and" not "see" — handled in AND section
    # 41:33 ירא = "let·see" (jussive — let Pharaoh see/find)
    ('41:33', 'ירא'): 'let·(him)·see',
}


# ─────────────────────────────────────────────
#  3. "be" — wrong glosses, need ETCBC cross-ref
# ─────────────────────────────────────────────
# These are compound words that got collapsed to "be" by mistake.
# We map by consonantal form to the correct gloss.
BE_LOOKUP = {
    'ויקדש':     'and·he·sanctified',
    'ורבובה':    'and·multiply·in·it',
    'יפתמראה':   'beautiful·of·appearance',
    'משלש':      'three-year-old',
    'היפלא':     'is·(anything)·too·wondrous',
    'הרחק':      'at·a·distance',
    'אשכל':      'I·will·be·bereaved',
    'יפתתאר':    'beautiful·of·form',
    'ותקנא':     'and·she·was·jealous',
    'עדיגדל':    'until·he·grows·up',
    'קצף':       'was·angry',
    'אגדל':      'I·will·be·greater',
    'שלמתם':     'you(pl)·repaid',
    'כיטוב':     'for·the·best',
    'כיגדל':     'for·he·grew',    # 26:13 and 38:14
    'יגדל':      'he·will·be·great',  # 48:19 (x2)
}


# ─────────────────────────────────────────────
#  4. "and" — lost compound glosses
# ─────────────────────────────────────────────
AND_LOOKUP = {
    'ואד':  'and·mist',
    'ראי':  'Roi',          # Beer Lahai Roi — place name element
}


def load_etcbc():
    """Load ETCBC morpheme data."""
    with open(ETCBC_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def etcbc_reconstruct(verse_morphemes, target_cons):
    """
    Try to reconstruct a gloss from ETCBC morphemes that together
    spell out the target consonantal text.
    """
    if not verse_morphemes:
        return None

    # Try to find a sequence of morphemes whose consonants concatenate
    # to match the target
    for i in range(len(verse_morphemes)):
        built = ''
        parts = []
        for j in range(i, len(verse_morphemes)):
            m = verse_morphemes[j]
            mc = strip_niqqud(m.get('heb', ''))
            # Also try the 'cons' field (which may use shin dots differently)
            mc2 = m.get('cons', '').replace('\u05E9\u05C1', 'שׁ').replace('\u05E9\u05C2', 'שׂ')
            mc2_stripped = strip_niqqud(mc2)

            # Use whichever matches better
            built_with_mc = built + mc
            built_with_mc2 = built + mc2_stripped

            gloss = m.get('gloss', '')
            if gloss in ('<interrogative>',):
                gloss = '?'
            elif gloss in ('<uncertain>',):
                gloss = '(?)'

            if built_with_mc == target_cons or built_with_mc2 == target_cons:
                parts.append(gloss)
                if len(parts) == 1:
                    return parts[0]
                # Filter out empty/article glosses for cleaner output
                meaningful = [p for p in parts if p and p not in ('the',)]
                return '·'.join(meaningful) if meaningful else '·'.join(parts)

            # Check if we're still on track
            if target_cons.startswith(built_with_mc) or target_cons.startswith(built_with_mc2):
                built = built_with_mc if target_cons.startswith(built_with_mc) else built_with_mc2
                if gloss:
                    parts.append(gloss)
            else:
                break

    return None


def fix_to(word, ref, etcbc_data, occurrence_index):
    """Fix a word with eng='to'."""
    cons = strip_niqqud(word['heb'])

    # Check overrides first
    key = (ref, cons)
    if key in TO_OVERRIDES:
        return TO_OVERRIDES[key]

    # Direct lookup
    if cons in TO_LOOKUP:
        result = TO_LOOKUP[cons]
        if result != 'to':  # Only return if we actually improved it
            return result

    # For bare 'אל' or 'ל', try ETCBC reconstruction
    morphemes = etcbc_data.get(ref, [])
    reconstructed = etcbc_reconstruct(morphemes, cons)
    if reconstructed and reconstructed != 'to':
        return reconstructed

    return None  # Couldn't fix


def fix_see(word, ref, etcbc_data, occurrence_index):
    """Fix a word with eng='see'."""
    cons = strip_niqqud(word['heb'])

    # Check verse-specific overrides (with occurrence tracking for 22:14)
    key3 = (ref, cons, occurrence_index)
    if key3 in SEE_OVERRIDES:
        return SEE_OVERRIDES[key3]
    key2 = (ref, cons)
    if key2 in SEE_OVERRIDES:
        return SEE_OVERRIDES[key2]

    # Direct lookup
    if cons in SEE_LOOKUP:
        return SEE_LOOKUP[cons]

    # ETCBC fallback
    morphemes = etcbc_data.get(ref, [])
    reconstructed = etcbc_reconstruct(morphemes, cons)
    if reconstructed and reconstructed != 'see':
        return reconstructed

    return None


def fix_be(word, ref, etcbc_data, occurrence_index):
    """Fix a word with eng='be'."""
    cons = strip_niqqud(word['heb'])

    # Direct lookup
    if cons in BE_LOOKUP:
        return BE_LOOKUP[cons]

    # ETCBC fallback — reconstruct from morphemes
    morphemes = etcbc_data.get(ref, [])
    reconstructed = etcbc_reconstruct(morphemes, cons)
    if reconstructed and reconstructed != 'be':
        return reconstructed

    return None


def fix_and(word, ref, etcbc_data, occurrence_index):
    """Fix a word with eng='and'."""
    cons = strip_niqqud(word['heb'])

    # Direct lookup
    if cons in AND_LOOKUP:
        return AND_LOOKUP[cons]

    # ETCBC fallback
    morphemes = etcbc_data.get(ref, [])
    reconstructed = etcbc_reconstruct(morphemes, cons)
    if reconstructed and reconstructed != 'and':
        return reconstructed

    return None


FIXERS = {
    'to':  fix_to,
    'see': fix_see,
    'be':  fix_be,
    'and': fix_and,
}


def main():
    # Load data
    print("Loading genesis_v3.json...")
    with open(GENESIS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Loading ETCBC data...")
    etcbc_data = load_etcbc()

    # Backup
    print(f"Backing up to {BACKUP_FILE}...")
    shutil.copy2(GENESIS_FILE, BACKUP_FILE)

    # Track fixes
    fixes = {'to': 0, 'see': 0, 'be': 0, 'and': 0}
    unfixed = {'to': [], 'see': [], 'be': [], 'and': []}
    total_weak = 0

    # Process
    for ch in data['chapters']:
        for v in ch['verses']:
            ref = f"{ch['chapter']}:{v['verse']}"

            # Track occurrence index per (eng, cons) within a verse
            # for handling duplicates like 22:14 which has two יראה
            occurrence_counts = {}

            for w in v['words']:
                eng = w['eng']
                if eng not in FIXERS:
                    continue

                total_weak += 1
                cons = strip_niqqud(w['heb'])

                # Track occurrence
                occ_key = (eng, cons)
                idx = occurrence_counts.get(occ_key, 0)
                occurrence_counts[occ_key] = idx + 1

                fixer = FIXERS[eng]
                new_gloss = fixer(w, ref, etcbc_data, idx)

                if new_gloss and new_gloss != eng:
                    print(f"  {ref:>8s}  {w['heb']:>20s}  {eng:>5s} -> {new_gloss}")
                    w['eng'] = new_gloss
                    fixes[eng] += 1
                else:
                    unfixed[eng].append((ref, w['heb'], cons))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_fixed = sum(fixes.values())
    print(f"Total weak glosses found: {total_weak}")
    print(f"Total fixed:              {total_fixed}")
    for cat in ('to', 'see', 'be', 'and'):
        print(f"  {cat:>5s}: {fixes[cat]} fixed")
        if unfixed[cat]:
            print(f"         {len(unfixed[cat])} UNFIXED:")
            for ref, heb, cons in unfixed[cat]:
                print(f"           {ref}: {heb} ({cons})")

    # Save
    print(f"\nSaving to {GENESIS_FILE}...")
    with open(GENESIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Done!")


if __name__ == '__main__':
    main()
