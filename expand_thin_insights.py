"""
Expand the 'insights' field for verses in genesis_v3.json that have
too much empty page space, using only verifiable mathematical,
structural, and cross-reference facts.
"""

import json
import sys
import re
import math
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT = 'K:/TorahByWord/genesis_v3.json'
TARGET_CHARS = 2000

# Well-known gematria values
NOTABLE_VALUES = {
    13: "echad (one) / ahavah (love)",
    18: "chai (life)",
    26: "YHWH",
    36: "double-chai",
    45: "Adam",
    50: "nun / jubilee",
    72: "chesed (kindness)",
    86: "Elohim",
    91: "amen",
    100: "kuf",
    314: "Shaddai",
    345: "Moshe (Moses)",
    358: "Mashiach (Messiah)",
    400: "tav",
}

HEBREW_LETTER_RE = re.compile(r'[\u05D0-\u05EA]')


def count_hebrew_letters(text):
    """Count only Hebrew consonants (aleph through tav)."""
    return len(HEBREW_LETTER_RE.findall(text))


def prime_factors(n):
    """Return prime factorization as list of (prime, exponent) tuples."""
    if n < 2:
        return []
    factors = []
    d = 2
    while d * d <= n:
        exp = 0
        while n % d == 0:
            exp += 1
            n //= d
        if exp:
            factors.append((d, exp))
        d += 1
    if n > 1:
        factors.append((n, 1))
    return factors


def format_factors(n):
    """Format prime factorization as string."""
    factors = prime_factors(n)
    if not factors:
        return str(n)
    parts = []
    for p, e in factors:
        if e == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{e}")
    result = " x ".join(parts)
    product = 1
    for p, e in factors:
        product *= p ** e
    if len(factors) == 1 and factors[0][1] == 1:
        return f"{n} is prime"
    return f"{n} = {result}"


def renderable_length(verse):
    """Estimate total renderable text length for a verse."""
    total = 0
    # Commentary fields
    for key in ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
                'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar']:
        total += len(verse.get(key, '') or '')
    # Other rendered fields
    for key in ['gem_note', 'cross_refs', 'insights']:
        total += len(verse.get(key, '') or '')
    return total


def build_indexes(data):
    """Build cross-reference indexes from all verses."""
    # gematria total -> list of refs
    gematria_index = defaultdict(list)
    # root -> count of occurrences
    root_count = defaultdict(int)
    # root -> list of refs where it appears
    root_refs = defaultdict(set)
    # word heb (stripped) -> count
    word_freq = defaultdict(int)
    # word heb (stripped) -> list of refs
    word_refs = defaultdict(list)

    for ch in data['chapters']:
        for v in ch['verses']:
            ref = v.get('ref', '')
            tg = v.get('total_gematria', 0)
            if tg:
                gematria_index[tg].append(ref)
            for w in v.get('words', []):
                root = w.get('root', '')
                if root:
                    root_count[root] += 1
                    root_refs[root].add(ref)
                heb = w.get('heb', '')
                stripped = ''.join(HEBREW_LETTER_RE.findall(heb))
                if stripped:
                    word_freq[stripped] += 1
                    word_refs[stripped].append(ref)

    return gematria_index, root_count, root_refs, word_freq, word_refs


def get_chapter_verse_positions(data):
    """Map each ref to its position info within the chapter."""
    positions = {}
    for ch in data['chapters']:
        verses = ch['verses']
        n = len(verses)
        for i, v in enumerate(verses):
            ref = v.get('ref', '')
            positions[ref] = {
                'index': i,
                'total': n,
                'is_first': i == 0,
                'is_last': i == n - 1,
                'is_middle': i == n // 2 and n > 2,
            }
    return positions


def generate_insights(verse, gematria_index, root_count, root_refs,
                      word_freq, word_refs, positions, chars_needed):
    """Generate verifiable insight text for a verse."""
    ref = verse.get('ref', '')
    words = verse.get('words', [])
    tg = verse.get('total_gematria', 0)
    insights_parts = []

    # 1. Structural facts
    word_count = len(words)
    total_letters = 0
    for w in words:
        total_letters += count_hebrew_letters(w.get('heb', ''))

    structural = f"This verse has {word_count} words and {total_letters} Hebrew letters."

    # Position info
    pos = positions.get(ref, {})
    if pos.get('is_first'):
        structural += f" It is the first verse of its chapter ({pos['total']} verses total)."
    elif pos.get('is_last'):
        structural += f" It is the last verse of its chapter ({pos['total']} verses total)."
    elif pos.get('is_middle'):
        structural += f" It is the middle verse of its chapter (verse {pos['index']+1} of {pos['total']})."

    # Shortest and longest words by letter count
    if word_count >= 3:
        word_letter_counts = []
        for w in words:
            heb = w.get('heb', '')
            lc = count_hebrew_letters(heb)
            eng = w.get('eng', '')
            word_letter_counts.append((lc, heb, eng))
        word_letter_counts.sort()
        shortest = word_letter_counts[0]
        longest = word_letter_counts[-1]
        if shortest[0] != longest[0]:
            structural += (f" The shortest word is \"{shortest[2]}\" "
                          f"({shortest[1]}, {shortest[0]} letters) and the "
                          f"longest is \"{longest[2]}\" "
                          f"({longest[1]}, {longest[0]} letters).")

    # Repeated roots in this verse
    verse_roots = defaultdict(int)
    for w in words:
        r = w.get('root', '')
        if r:
            verse_roots[r] += 1
    repeated = [(r, c) for r, c in verse_roots.items() if c > 1]
    if repeated:
        for r, c in repeated:
            structural += f" The root {r} appears {c} times in this verse."

    # Unique roots count
    unique_roots = len([r for r in verse_roots if r])
    if unique_roots > 0:
        structural += f" {unique_roots} unique roots are used."

    insights_parts.append(structural)

    if len(' '.join(insights_parts)) >= chars_needed:
        return ' '.join(insights_parts)[:chars_needed + 200]

    # 2. Gematria facts
    gematria_text = ""
    if tg:
        gematria_text = f"Verse gematria: {format_factors(tg)}."

        # Words matching notable values
        notable_matches = []
        for w in words:
            gem = w.get('gem', 0)
            if gem in NOTABLE_VALUES:
                eng = w.get('eng', '')
                heb = w.get('heb', '')
                notable_matches.append(
                    f"\"{eng}\" ({heb}) = {gem}, the value of {NOTABLE_VALUES[gem]}")
        if notable_matches:
            gematria_text += " Notable word values: " + "; ".join(notable_matches) + "."

        # Words sharing the same gematria
        gem_groups = defaultdict(list)
        for w in words:
            gem = w.get('gem', 0)
            if gem:
                gem_groups[gem].append(w.get('eng', '?'))
        shared = [(g, ws) for g, ws in gem_groups.items() if len(ws) > 1]
        if shared:
            for g, ws in shared:
                gematria_text += (f" Words sharing gematria {g}: "
                                 f"{', '.join(ws)}.")

        # Pairs summing to notable values (only if we need more chars)
        if len(' '.join(insights_parts)) + len(gematria_text) < chars_needed:
            pair_notes = []
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    s = (words[i].get('gem', 0) or 0) + (words[j].get('gem', 0) or 0)
                    if s in NOTABLE_VALUES:
                        pair_notes.append(
                            f"\"{words[i].get('eng', '')}\" + "
                            f"\"{words[j].get('eng', '')}\" = "
                            f"{s} ({NOTABLE_VALUES[s]})")
                if len(pair_notes) >= 3:
                    break
            if pair_notes:
                gematria_text += " Notable pairs: " + "; ".join(pair_notes) + "."

    if gematria_text:
        insights_parts.append(gematria_text)

    if len(' '.join(insights_parts)) >= chars_needed:
        return ' '.join(insights_parts)[:chars_needed + 200]

    # 3. Full gematria calculation for short verses (<=8 words)
    if word_count <= 8 and tg:
        calc_parts = []
        for w in words:
            heb = w.get('heb', '')
            gem = w.get('gem', 0)
            eng = w.get('eng', '')
            calc_parts.append(f"{heb} [{eng}] ({gem})")
        calc = " + ".join(calc_parts) + f" = {tg}"
        insights_parts.append(f"Full calculation: {calc}.")

    if len(' '.join(insights_parts)) >= chars_needed:
        return ' '.join(insights_parts)[:chars_needed + 200]

    # 4. Cross-references within Genesis
    xref_text = ""
    if tg:
        same_gem = [r for r in gematria_index.get(tg, []) if r != ref]
        if same_gem:
            shown = same_gem[:5]
            xref_text += (f"Other Genesis verses with gematria {tg}: "
                         f"{', '.join(shown)}"
                         f"{f' (and {len(same_gem)-5} more)' if len(same_gem) > 5 else ''}. ")

    # Hapax legomena (words appearing only once in Genesis)
    hapax = []
    for w in words:
        heb = w.get('heb', '')
        stripped = ''.join(HEBREW_LETTER_RE.findall(heb))
        if stripped and word_freq.get(stripped, 0) == 1:
            eng = w.get('eng', '')
            hapax.append(f"\"{eng}\" ({heb})")
    if hapax and len(hapax) <= 4:
        xref_text += (f"Unique to this verse in Genesis (hapax): "
                     f"{', '.join(hapax)}. ")
    elif hapax:
        xref_text += (f"{len(hapax)} words in this verse appear nowhere else "
                     f"in Genesis. ")

    # Roots with very few occurrences (rare roots)
    if len(' '.join(insights_parts)) + len(xref_text) < chars_needed:
        rare_roots = []
        for w in words:
            r = w.get('root', '')
            if r and root_count.get(r, 0) <= 3:
                eng = w.get('eng', '')
                cnt = root_count[r]
                if cnt == 1:
                    rare_roots.append(f"\"{eng}\" (root {r}, only here in Genesis)")
                else:
                    rare_roots.append(f"\"{eng}\" (root {r}, {cnt}x in Genesis)")
        if rare_roots:
            xref_text += "Rare roots: " + "; ".join(rare_roots[:4]) + ". "

    if xref_text:
        insights_parts.append(xref_text)

    if len(' '.join(insights_parts)) >= chars_needed:
        return ' '.join(insights_parts)[:chars_needed + 200]

    # 5. Additional filler: common roots in this verse with their Genesis frequency
    if len(' '.join(insights_parts)) < chars_needed:
        freq_notes = []
        for w in words:
            r = w.get('root', '')
            if r and root_count.get(r, 0) > 10:
                eng = w.get('eng', '')
                freq_notes.append(f"\"{eng}\" (root {r}, {root_count[r]}x in Genesis)")
        if freq_notes:
            insights_parts.append("Frequent roots: " + "; ".join(freq_notes[:5]) + ".")

    return ' '.join(insights_parts)


def main():
    print("Loading genesis_v3.json...")
    with open(INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Building indexes...")
    gematria_index, root_count, root_refs, word_freq, word_refs = build_indexes(data)
    positions = get_chapter_verse_positions(data)

    expanded_count = 0
    skipped_already_full = 0

    for ch in data['chapters']:
        for verse in ch['verses']:
            current_len = renderable_length(verse)
            if current_len >= TARGET_CHARS:
                skipped_already_full += 1
                continue

            chars_needed = TARGET_CHARS - current_len
            if chars_needed < 50:
                skipped_already_full += 1
                continue

            new_insight = generate_insights(
                verse, gematria_index, root_count, root_refs,
                word_freq, word_refs, positions, chars_needed
            )

            if not new_insight:
                continue

            # Append to existing insights
            existing = verse.get('insights', '') or ''
            if existing:
                verse['insights'] = existing.rstrip() + " " + new_insight
            else:
                verse['insights'] = new_insight

            expanded_count += 1

    print(f"Verses expanded: {expanded_count}")
    print(f"Verses already full (skipped): {skipped_already_full}")

    print("Saving genesis_v3.json...")
    with open(INPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Done.")


if __name__ == '__main__':
    main()
