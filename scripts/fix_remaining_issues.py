#!/usr/bin/env python3
"""Fix remaining gloss issues across 4 Torah books:
1. Empty glosses (~252) - translate using ETCBC + manual dictionary
2. Jargon glosses (~25) - replace POS labels with actual translations via ETCBC
3. HTML junk (~4) - strip HTML tags
"""

import json
import re
import sys
import os

# Strip nikud (vowels U+05B0-U+05C7) and cantillation (U+0591-U+05AF) from Hebrew
def strip_nikud(s):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7\u05F3\u05F4]', '', s).replace('\u05BE', '-').strip()

def strip_nikud_bare(s):
    """Strip nikud and also maqaf, for consonant matching."""
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7\u05F3\u05F4\u05BE\u200D\uFB20-\uFB4F]', '', s).replace('-', '').strip()


# Known manual translations for common empty-gloss patterns
MANUAL_DICT = {
    # Suffix fragments
    'ו': 'him',       # 3ms suffix (also "and" as prefix, context dependent)
    'וּ': 'him',
    'וֹ': 'him',
    'ום': 'peace',    # shalom fragment (של + ום)
    'וה': 'woe',      # interjection
    'לאתעל': 'you·shall·not·offer·up',  # Exodus 30:9 (combined word)

    # אין forms
    'אין': 'there·is·not',
    'איננו': 'he·is·not',
    'איננה': 'it·is·not',
    'אינני': 'I·am·not',
    'אינכם': 'you·are·not',

    # אשר combinations
    'אשרל': 'which·(belongs)·to',
    'אשריאכל': 'which·they·shall·eat',
    'אשרתבשל': 'which·you·shall·cook',
    'אשרעל': 'who·went·up·with',
    'אשרראינו': 'which·we·saw',
    'אשרנכל': 'which·they·beguiled',
    'אשרנשבעתי': 'which·I·swore',
    'אשרינחל': 'who·shall·divide',
    'אשרעשה': 'which·did',

    # Proper nouns
    'בלעם': 'Balaam',
    'נבו': 'Nebo',
    'נמרה': 'Nimrah',
    'שופן': 'Shophan',
    'בשמת': 'by·names',

    # Common words
    'הל': 'is·it·not',  # interrogative
    'ה': 'the',         # article
    'מנחת': 'offering·of',
    'חלב': 'milk',
    'מוקדה': 'burning',
    'תפיני': 'baked·pieces',
    'צוה': 'commanded',
    'צויתי': 'I·commanded',
    'אצוה': 'I·shall·command',
    'שארה': 'her·flesh',
    'דמיה': 'her·blood',
    'השנים': 'the·years',
    'הערכך': 'your·valuation',
    'מאדם': 'from·man',
    'ישרתהו': 'shall·minister·to·it',
    'אתמשה': 'Moses',
    'בהמתם': 'their·livestock',
    'ליהוה': 'to·YHWH',
    'כןעשו': 'so·they·did',
    'חיה': 'beast',
    'גבלת': 'twisted',
    'שבו': 'agate',
    'ייסך': 'shall·be·poured',
    'ואיבתי': 'and·I·will·be·hostile·to',
    'אלבני': 'to·the·sons·of',
    'אלהערפל': 'to·the·thick·darkness',
    'אתשמי': 'My·name',
    'אתפני': 'the·face·of',
    'אםאין': 'if·not',
    'איןל': 'there·is·not·to',
    'והרמתם': 'and·you·shall·set·apart',
    'עלהנהר': 'on·the·river',
    'היכל': 'am·I·able',
    'שתם': 'open',
    'קנא': 'was·zealous',
    'תניאון': 'you·would·discourage',
    'טפנו': 'our·little·ones',
    'ערי': 'cities·of',
    'ששערי': 'six·cities·of',
    'אשרינחל': 'who·shall·divide',
    'יען': 'because',
    'בקרבכם': 'in·your·midst',
    'ירשה': 'possession',
    'השמידו': 'He·destroyed·him',
    'אתגדל': 'the·greatness·of',
    'בשעריכם': 'in·your·gates',
    'בשעריך': 'in·your·gates',
    'ואמרת': 'and·you·say',
    'ובו': 'and·to·Him',
    'חלק': 'portion',
    'השבעות': 'the·Weeks',
    'הרבות': 'to·multiply',
    'שפכו': 'shed',
    'לקחתי': 'I·took',
    'לאיוכל': 'he·cannot',
    'בהן': 'in·them',
    'כלאשר': 'all·that',
    'טפכם': 'your·little·ones',
    'תשי': 'you·forgot',
    'תכו': 'they·were·set',
    'חסידך': 'Your·faithful·one',
    'תריבהו': 'You·tested·him',
    'למינהו': 'according·to·its·kind',
    'תתנו': 'you·give',
    'יצא': 'go·out',
    'קמצו': 'his·handful',
    'שמע': 'heard',
    'היטיבו': 'they·have·done·well',
    'עמדי': 'with·Me',
    'ימין': 'right',
    'אתקל': 'the·voice·of',
    'שפכו': 'shed',

    # Combined/merged words from Deut
    'תנאףלא': 'you·shall·not·commit·adultery;·you·shall·not',
    'תנאףולא': 'you·shall·not·commit·adultery;·and·you·shall·not',
    'רעךולא': 'your·neighbor;·and·you·shall·not',
}

# Jargon POS labels to detect
JARGON_SET = {'n m', 'n f', 'adj', 'adv', 'n pr', 'n loc', 'prep', 'conj', 'pron', 'interj', 'v'}


def load_etcbc(book_name):
    """Load ETCBC by-verse reference data."""
    path = f'K:/TorahByWord/references/etcbc_{book_name}_by_verse.json'
    if not os.path.exists(path):
        print(f"  WARNING: ETCBC file not found: {path}")
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def find_etcbc_gloss(etcbc_verse, heb_word):
    """Try to find a gloss for heb_word in the ETCBC verse data."""
    if not etcbc_verse:
        return None

    cons_target = strip_nikud_bare(heb_word)
    if not cons_target:
        return None

    # Try exact consonant match first
    for entry in etcbc_verse:
        entry_cons = entry.get('cons', '')
        if not entry_cons:
            entry_cons = strip_nikud_bare(entry.get('heb', ''))
        else:
            entry_cons = entry_cons.replace('\u05C2', '').replace('\u05C1', '')  # strip shin/sin dots

        if entry_cons == cons_target:
            gloss = entry.get('gloss', '')
            if gloss and gloss.strip():
                return gloss

    # Try substring match (our word may be a combined form)
    # Build concatenated consonant string and find where our target fits
    combined = ''
    glosses = []
    for entry in etcbc_verse:
        entry_cons = entry.get('cons', '')
        if not entry_cons:
            entry_cons = strip_nikud_bare(entry.get('heb', ''))
        else:
            entry_cons = entry_cons.replace('\u05C2', '').replace('\u05C1', '')
        combined += entry_cons
        glosses.append((entry_cons, entry.get('gloss', '')))

    # Check if target appears as concatenation of consecutive ETCBC words
    running = ''
    start_idx = None
    matched_glosses = []
    for i, (ec, eg) in enumerate(glosses):
        if start_idx is None:
            if cons_target.startswith(ec):
                running = ec
                start_idx = i
                matched_glosses = [eg]
                if running == cons_target:
                    return '·'.join(g for g in matched_glosses if g)
        else:
            running += ec
            matched_glosses.append(eg)
            if running == cons_target:
                return '·'.join(g for g in matched_glosses if g)
            if not cons_target.startswith(running):
                # Reset
                start_idx = None
                running = ''
                matched_glosses = []
                # Re-check current
                if cons_target.startswith(ec):
                    running = ec
                    start_idx = i
                    matched_glosses = [eg]

    return None


def strip_html(eng):
    """Strip HTML tags and everything after them."""
    cleaned = re.sub(r'<[^>]*>.*', '', eng, flags=re.DOTALL).strip()
    # Also strip dictionary-style junk: "(interj.; cmp. b. h. " etc
    cleaned = re.sub(r'\(interj\..*', '', cleaned).strip()
    cleaned = re.sub(r'\(cmp\..*', '', cleaned).strip()
    # Also remove trailing punctuation artifacts
    cleaned = cleaned.rstrip('= .;')
    # If what remains is just "not" or short junk from a dictionary entry, discard
    if cleaned in ('not', 'h', 'not·= h', 'not·=', ''):
        return ''
    return cleaned


def fix_book(book_name, filepath):
    """Fix all issues in one book. Returns counts."""
    print(f"\n{'='*60}")
    print(f"Processing: {book_name} ({filepath})")
    print(f"{'='*60}")

    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    etcbc = load_etcbc(book_name)

    fixed_empty = 0
    fixed_jargon = 0
    fixed_html = 0
    still_empty = 0
    changes = []

    for ch in data['chapters']:
        for vs in ch['verses']:
            ref = f"{ch['chapter']}:{vs['verse']}"
            etcbc_verse = etcbc.get(ref, [])

            for w in vs['words']:
                eng = w.get('eng', '')
                heb = w['heb']
                cons = strip_nikud_bare(heb)

                # Issue 1: Empty glosses
                if not eng or not eng.strip():
                    new_gloss = None

                    # Check manual dictionary first
                    if cons in MANUAL_DICT:
                        new_gloss = MANUAL_DICT[cons]

                    # Special handling for וֹ / וּ suffix fragments after ל (to·him)
                    if new_gloss is None and cons == 'ו':
                        new_gloss = 'him'

                    # Try ETCBC lookup
                    if new_gloss is None:
                        etcbc_gloss = find_etcbc_gloss(etcbc_verse, heb)
                        if etcbc_gloss:
                            new_gloss = etcbc_gloss

                    # Special: empty heb (like the nun hafukha in Numbers 10:36)
                    if not cons or cons == '׆':
                        new_gloss = ''  # truly orphaned

                    if new_gloss is not None and new_gloss != eng:
                        old = repr(eng)
                        w['eng'] = new_gloss
                        if new_gloss:
                            fixed_empty += 1
                            changes.append(f"  EMPTY {ref} [{heb}] {old} -> \"{new_gloss}\"")
                        else:
                            still_empty += 1
                    else:
                        still_empty += 1
                        changes.append(f"  UNFIXED {ref} [{heb}] cons={cons}")

                # Issue 2: Jargon glosses (POS labels)
                elif eng.strip() in JARGON_SET:
                    new_gloss = None
                    etcbc_gloss = find_etcbc_gloss(etcbc_verse, heb)
                    if etcbc_gloss:
                        new_gloss = etcbc_gloss

                    # Fallback manual overrides for known jargon cases
                    if new_gloss is None:
                        jargon_fallback = {
                            'מת': 'dead',
                            'הזכרים': 'the·males',
                            'הזכר': 'the·male',
                            'מזכר': 'from·male',
                            'גדול': 'great',
                            'מורה': 'teacher',
                            'ואמתו': 'and·his·maidservant',
                            'תשמעו': 'you·shall·listen',
                            'ספר': 'recount',
                            'חלף': 'in·exchange·for',
                            'לאמת': 'not·dead',
                            'רעךלאתחמד': 'your·neighbor;·you·shall·not·covet',
                            'בספר': 'in·the·book',
                        }
                        if cons in jargon_fallback:
                            new_gloss = jargon_fallback[cons]

                    if new_gloss and new_gloss != eng:
                        old = eng
                        w['eng'] = new_gloss
                        fixed_jargon += 1
                        changes.append(f"  JARGON {ref} [{heb}] \"{old}\" -> \"{new_gloss}\"")
                    else:
                        changes.append(f"  JARGON-UNFIXED {ref} [{heb}] \"{eng}\" cons={cons}")

                # Issue 3: HTML junk
                elif '<' in eng:
                    cleaned = strip_html(eng)
                    if cleaned and cleaned != eng:
                        old = eng[:60]
                        w['eng'] = cleaned
                        fixed_html += 1
                        changes.append(f"  HTML {ref} [{heb}] \"{old}...\" -> \"{cleaned}\"")
                    else:
                        # Try ETCBC
                        etcbc_gloss = find_etcbc_gloss(etcbc_verse, heb)
                        if etcbc_gloss:
                            w['eng'] = etcbc_gloss
                            fixed_html += 1
                            changes.append(f"  HTML->ETCBC {ref} [{heb}] -> \"{etcbc_gloss}\"")
                        elif cons in MANUAL_DICT:
                            w['eng'] = MANUAL_DICT[cons]
                            fixed_html += 1
                            changes.append(f"  HTML->MANUAL {ref} [{heb}] -> \"{MANUAL_DICT[cons]}\"")
                        else:
                            changes.append(f"  HTML-UNFIXED {ref} [{heb}] \"{eng[:60]}\"")

    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Report
    for c in changes:
        print(c)

    print(f"\n  Fixed: {fixed_empty} empty, {fixed_jargon} jargon, {fixed_html} HTML")
    if still_empty:
        print(f"  Still empty: {still_empty} (orphaned fragments set to empty string)")

    return fixed_empty, fixed_jargon, fixed_html, still_empty


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    books = [
        ('exodus', 'K:/TorahByWord/books/torah/exodus_fixed.json'),
        ('leviticus', 'K:/TorahByWord/books/torah/leviticus_fixed.json'),
        ('numbers', 'K:/TorahByWord/books/torah/numbers_fixed.json'),
        ('deuteronomy', 'K:/TorahByWord/books/torah/deuteronomy_fixed.json'),
    ]

    total_empty = 0
    total_jargon = 0
    total_html = 0
    total_still = 0

    for book_name, filepath in books:
        fe, fj, fh, se = fix_book(book_name, filepath)
        total_empty += fe
        total_jargon += fj
        total_html += fh
        total_still += se

    print(f"\n{'='*60}")
    print(f"TOTAL FIXED: {total_empty} empty, {total_jargon} jargon, {total_html} HTML")
    print(f"TOTAL STILL EMPTY: {total_still}")
    print(f"GRAND TOTAL CHANGES: {total_empty + total_jargon + total_html}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
