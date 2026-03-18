"""
Remove ALL Hebrew characters from 'insights' and 'gem_note' fields in genesis_v3.json,
replacing them intelligently with transliterations or English glosses.
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT = 'K:/TorahByWord/genesis_v3.json'

# Hebrew character ranges
HEBREW_RE = re.compile(r'[\u0590-\u05FF]+')
HEBREW_CHAR_RE = re.compile(r'[\u0590-\u05FF]')

# Letter-by-letter transliteration for roots (consonants only)
LETTER_MAP = {
    '\u05D0': 'aleph', '\u05D1': 'bet', '\u05D2': 'gimel', '\u05D3': 'dalet',
    '\u05D4': 'he', '\u05D5': 'vav', '\u05D6': 'zayin', '\u05D7': 'chet',
    '\u05D8': 'tet', '\u05D9': 'yod', '\u05DA': 'kaf', '\u05DB': 'kaf',
    '\u05DC': 'lamed', '\u05DD': 'mem', '\u05DE': 'mem', '\u05DF': 'nun',
    '\u05E0': 'nun', '\u05E1': 'samekh', '\u05E2': 'ayin', '\u05E3': 'pe',
    '\u05E4': 'pe', '\u05E5': 'tsade', '\u05E6': 'tsade', '\u05E7': 'qof',
    '\u05E8': 'resh', '\u05E9': 'shin', '\u05EA': 'tav',
}


def strip_niqqud(text):
    """Strip vowel points / cantillation, keep consonants only."""
    return re.sub(r'[\u0591-\u05C7]', '', text)


def consonants_only(text):
    """Extract only Hebrew consonant letters."""
    return re.sub(r'[^\u05D0-\u05EA]', '', text)


def transliterate_root(heb_text):
    """Transliterate a Hebrew root letter by letter."""
    cons = consonants_only(heb_text)
    parts = []
    for ch in cons:
        parts.append(LETTER_MAP.get(ch, '?'))
    return '-'.join(parts)


def build_word_lookup(data):
    """Build a lookup from Hebrew consonant string -> (transliteration, english)."""
    lookup = {}
    for ch in data['chapters']:
        for v in ch['verses']:
            for w in v.get('words', []):
                heb = w.get('heb', '')
                cons = consonants_only(heb)
                if cons and cons not in lookup:
                    tr = w.get('tr', '')
                    eng = w.get('eng', '')
                    lookup[cons] = (tr, eng)
    return lookup


def build_verse_word_lookup(verse):
    """Build lookup for a specific verse's words."""
    lookup = {}
    for w in verse.get('words', []):
        heb = w.get('heb', '')
        cons = consonants_only(heb)
        if cons:
            tr = w.get('tr', '')
            eng = w.get('eng', '')
            lookup[cons] = (tr, eng)
        # Also store with full text for exact matching
        stripped = strip_niqqud(heb).strip()
        if stripped:
            lookup[stripped] = (tr, eng)
    return lookup


def replace_hebrew_in_text(text, verse_lookup, global_lookup):
    """Replace all Hebrew text in a string with English/transliteration."""
    if not text:
        return text

    def replacer(m):
        heb = m.group(0)
        cons = consonants_only(heb)

        # Try verse-level lookup first (exact match with this form)
        stripped = strip_niqqud(heb).strip()
        if stripped in verse_lookup:
            tr, eng = verse_lookup[stripped]
            if eng and tr:
                return f'{eng} ({tr})'
            elif eng:
                return eng
            elif tr:
                return tr

        # Try consonants-only lookup
        if cons in verse_lookup:
            tr, eng = verse_lookup[cons]
            if eng and tr:
                return f'{eng} ({tr})'
            elif eng:
                return eng
            elif tr:
                return tr

        # Try global lookup
        if cons in global_lookup:
            tr, eng = global_lookup[cons]
            if eng and tr:
                return f'{eng} ({tr})'
            elif eng:
                return eng
            elif tr:
                return tr

        # Fallback: transliterate letter by letter
        if cons:
            return transliterate_root(cons)

        # If only niqqud/cantillation marks with no consonants, just remove
        return ''

    result = HEBREW_RE.sub(replacer, text)

    # Clean up artifacts: double spaces, empty parens, etc.
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r'\s{2,}', ' ', result)
    result = result.strip()

    return result


def clean_gem_note_patterns(text, verse_lookup, global_lookup):
    """Handle specific gem_note patterns before general replacement."""
    if not text:
        return text

    # Pattern: "הַבְּרִית = 86 (Elohim)" -> "Elohim = 86"
    # More general: HEBREW = NUMBER (ENGLISH)
    def gem_with_english(m):
        heb = m.group(1)
        num = m.group(2)
        eng_label = m.group(3)
        return f'{eng_label} = {num}'
    text = re.sub(r'([\u0590-\u05FF]+)\s*=\s*(\d+)\s*\(([^)]+)\)', gem_with_english, text)

    # Pattern: HEBREW = NUMBER (without English label)
    def gem_without_english(m):
        heb = m.group(1)
        num = m.group(2)
        cons = consonants_only(heb)
        # Try lookups
        for lk in [verse_lookup, global_lookup]:
            if cons in lk:
                tr, eng = lk[cons]
                if eng:
                    return f'"{eng}" = {num}'
                elif tr:
                    return f'{tr} = {num}'
        # Fallback
        return f'{transliterate_root(heb)} = {num}'
    text = re.sub(r'([\u0590-\u05FF]+)\s*=\s*(\d+)(?!\s*\()', gem_without_english, text)

    # Now do general replacement for any remaining Hebrew
    text = replace_hebrew_in_text(text, verse_lookup, global_lookup)

    return text


def clean_insights_patterns(text, verse_lookup, global_lookup):
    """Handle specific insights patterns before general replacement."""
    if not text:
        return text

    # Pattern: "word" (HEBREW, N letters) -> "word" (N letters)
    def word_with_heb_letters(m):
        eng = m.group(1)
        num = m.group(2)
        return f'"{eng}" ({num} letters)'
    text = re.sub(r'"([^"]+)"\s*\([\u0590-\u05FF]+,\s*(\d+)\s*letters?\)', word_with_heb_letters, text)

    # Pattern: "word" (HEBREW) -> "word"
    def word_with_heb(m):
        eng = m.group(1)
        return f'"{eng}"'
    text = re.sub(r'"([^"]+)"\s*\([\u0590-\u05FF]+\)', word_with_heb, text)

    # Pattern: (HEBREW, N letters) -> (N letters) -- without preceding English in quotes
    text = re.sub(r'\([\u0590-\u05FF]+,\s*(\d+\s*letters?)\)', r'(\1)', text)

    # Pattern: The root HEBREW appears/is... -> The root TRANSLITERATION appears/is...
    def root_pattern(m):
        prefix = m.group(1)
        heb = m.group(2)
        suffix = m.group(3)
        cons = consonants_only(heb)
        # Try lookups
        for lk in [verse_lookup, global_lookup]:
            if cons in lk:
                tr, eng = lk[cons]
                if tr:
                    return f'{prefix}{tr}{suffix}'
                elif eng:
                    return f'{prefix}"{eng}"{suffix}'
        return f'{prefix}{transliterate_root(heb)}{suffix}'
    text = re.sub(r'((?:root|Root)\s+)([\u0590-\u05FF]+)(\s)', root_pattern, text)

    # Pattern: HEBREW [eng] (num)  in full calculation sections
    def calc_pattern(m):
        eng = m.group(1)
        num = m.group(2)
        return f'{eng} ({num})'
    text = re.sub(r'[\u0590-\u05FF]+\s*\[([^\]]+)\]\s*\((\d+)\)', calc_pattern, text)

    # Pattern: "word" (HEBREW) = NUM, ...
    def notable_word(m):
        eng = m.group(1)
        num = m.group(2)
        rest = m.group(3)
        return f'"{eng}" = {num}{rest}'
    text = re.sub(r'"([^"]+)"\s*\([\u0590-\u05FF]+\)\s*=\s*(\d+)([\s,;.])', notable_word, text)

    # Pattern: (HEBREW) with no preceding quote - just remove
    text = re.sub(r'\([\u0590-\u05FF]+\)', '', text)

    # Now do general replacement for any remaining Hebrew
    text = replace_hebrew_in_text(text, verse_lookup, global_lookup)

    # Final cleanup
    text = re.sub(r'\(\s*,', '(', text)
    text = re.sub(r',\s*\)', ')', text)
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    return text


def main():
    print("Loading genesis_v3.json...")
    with open(INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Building global word lookup...")
    global_lookup = build_word_lookup(data)
    print(f"  {len(global_lookup)} unique Hebrew forms indexed")

    insights_cleaned = 0
    gem_cleaned = 0
    still_has_hebrew_i = 0
    still_has_hebrew_g = 0

    for ch in data['chapters']:
        for verse in ch['verses']:
            verse_lookup = build_verse_word_lookup(verse)

            # Clean insights
            ins = verse.get('insights', '') or ''
            if HEBREW_CHAR_RE.search(ins):
                new_ins = clean_insights_patterns(ins, verse_lookup, global_lookup)
                if HEBREW_CHAR_RE.search(new_ins):
                    # Second pass - aggressive
                    new_ins = replace_hebrew_in_text(new_ins, verse_lookup, global_lookup)
                verse['insights'] = new_ins
                insights_cleaned += 1
                if HEBREW_CHAR_RE.search(new_ins):
                    still_has_hebrew_i += 1
                    print(f"  STILL HAS HEBREW in insights: {verse.get('ref','')}")
                    # Find and show remaining Hebrew
                    for m in HEBREW_CHAR_RE.finditer(new_ins):
                        start = max(0, m.start()-20)
                        end = min(len(new_ins), m.end()+20)
                        print(f"    ...{new_ins[start:end]}...")
                        break

            # Clean gem_note
            gn = verse.get('gem_note', '') or ''
            if HEBREW_CHAR_RE.search(gn):
                new_gn = clean_gem_note_patterns(gn, verse_lookup, global_lookup)
                if HEBREW_CHAR_RE.search(new_gn):
                    new_gn = replace_hebrew_in_text(new_gn, verse_lookup, global_lookup)
                verse['gem_note'] = new_gn
                gem_cleaned += 1
                if HEBREW_CHAR_RE.search(new_gn):
                    still_has_hebrew_g += 1
                    print(f"  STILL HAS HEBREW in gem_note: {verse.get('ref','')}")
                    for m in HEBREW_CHAR_RE.finditer(new_gn):
                        start = max(0, m.start()-20)
                        end = min(len(new_gn), m.end()+20)
                        print(f"    ...{new_gn[start:end]}...")
                        break

    print(f"\nInsights cleaned: {insights_cleaned}")
    print(f"Gem notes cleaned: {gem_cleaned}")
    print(f"Still has Hebrew in insights: {still_has_hebrew_i}")
    print(f"Still has Hebrew in gem_note: {still_has_hebrew_g}")

    # Final verification
    total_hebrew = 0
    for ch in data['chapters']:
        for verse in ch['verses']:
            for field in ['insights', 'gem_note']:
                val = verse.get(field, '') or ''
                count = len(HEBREW_CHAR_RE.findall(val))
                total_hebrew += count

    print(f"\nTotal Hebrew characters remaining in insights+gem_note: {total_hebrew}")

    print("\nSaving genesis_v3.json...")
    with open(INPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Done.")


if __name__ == '__main__':
    main()
