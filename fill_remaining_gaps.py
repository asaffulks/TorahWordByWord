#!/usr/bin/env python3
"""Fill remaining gaps in genesis_v3.json insights fields."""

import json
import sys
import math
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Hebrew letter names and meanings (base consonants only)
HEBREW_LETTERS = {
    '\u05D0': ('Aleph', 'unity, God, beginning'),
    '\u05D1': ('Bet', 'house, duality'),
    '\u05D2': ('Gimel', 'kindness, growth'),
    '\u05D3': ('Dalet', 'door, humility'),
    '\u05D4': ('He', 'revelation, breath of God'),
    '\u05D5': ('Vav', 'connection, hook'),
    '\u05D6': ('Zayin', 'sustenance, weapon'),
    '\u05D7': ('Chet', 'life, grace'),
    '\u05D8': ('Tet', 'goodness, hidden good'),
    '\u05D9': ('Yod', 'hand of God, smallest letter'),
    '\u05DA': ('Kaf-final', 'palm, crown'),
    '\u05DB': ('Kaf', 'palm, crown'),
    '\u05DC': ('Lamed', 'learning, teaching'),
    '\u05DD': ('Mem-final', 'water, revealed/concealed'),
    '\u05DE': ('Mem', 'water, revealed/concealed'),
    '\u05DF': ('Nun-final', 'faithfulness, soul'),
    '\u05E0': ('Nun', 'faithfulness, soul'),
    '\u05E1': ('Samekh', 'support, protection'),
    '\u05E2': ('Ayin', 'eye, insight'),
    '\u05E3': ('Pe-final', 'mouth, speech'),
    '\u05E4': ('Pe', 'mouth, speech'),
    '\u05E5': ('Tsade-final', 'righteousness'),
    '\u05E6': ('Tsade', 'righteousness'),
    '\u05E7': ('Qof', 'holiness, cycles'),
    '\u05E8': ('Resh', 'head, beginning'),
    '\u05E9': ('Shin', 'fire, divine power'),
    '\u05EA': ('Tav', 'truth, completion, seal'),
}

LETTER_MERGE = {
    '\u05DA': '\u05DB', '\u05DD': '\u05DE', '\u05DF': '\u05E0',
    '\u05E3': '\u05E4', '\u05E5': '\u05E6',
}

COMMENTARY_FIELDS = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
                      'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar']


def count_hebrew_letters(hebrew_text):
    counts = Counter()
    for ch in hebrew_text:
        merged = LETTER_MERGE.get(ch, ch)
        if merged in HEBREW_LETTERS:
            counts[merged] += 1
    return counts


def get_letter_name(ch):
    merged = LETTER_MERGE.get(ch, ch)
    return HEBREW_LETTERS.get(merged, ('?', '?'))[0].replace('-final', '')


def get_letter_meaning(ch):
    merged = LETTER_MERGE.get(ch, ch)
    return HEBREW_LETTERS.get(merged, ('?', '?'))[1]


def compute_gap(vs):
    """Return (chars_capacity, current_content, overhead, gap).
    If insights is currently empty but we plan to add, account for the extra overhead."""
    word_count = len(vs.get('words', []))
    card_rows = math.ceil(word_count / 5)
    card_space = card_rows * 136 + 46
    text_space = 642 - card_space
    avail_lines = text_space / 12
    chars_capacity = avail_lines * 95

    current = 0
    active_sections = 0
    for field in COMMENTARY_FIELDS:
        val = vs.get(field, '')
        if val:
            current += len(val)
            active_sections += 1
    for field in ['insights', 'gem_note', 'cross_refs']:
        val = vs.get(field, '')
        if val:
            current += len(val)
            if field == 'insights':
                active_sections += 1

    overhead = active_sections * 60
    gap = chars_capacity - (current + overhead)
    return chars_capacity, current, overhead, gap


def compute_available_for_new_insights(vs):
    """How many chars of NEW insights text we can add.
    If insights is currently empty, adding text creates a new section with 200 overhead.
    """
    word_count = len(vs.get('words', []))
    card_rows = math.ceil(word_count / 5)
    card_space = card_rows * 136 + 46
    text_space = 642 - card_space
    avail_lines = text_space / 12
    chars_capacity = avail_lines * 95

    current = 0
    active_sections = 0
    has_insights = bool(vs.get('insights'))
    for field in COMMENTARY_FIELDS:
        val = vs.get(field, '')
        if val:
            current += len(val)
            active_sections += 1
    for field in ['insights', 'gem_note', 'cross_refs']:
        val = vs.get(field, '')
        if val:
            current += len(val)
            if field == 'insights':
                active_sections += 1

    # If no insights yet, adding insights creates a new section
    if not has_insights:
        active_sections += 1

    overhead = active_sections * 60
    available = chars_capacity - (current + overhead)
    return available


def position_label(verse_num, total_verses):
    ratio = verse_num / total_verses
    if ratio <= 0.33:
        return "first third"
    elif ratio <= 0.66:
        return "middle third"
    else:
        return "final third"


CHAPTER_TOPICS = {
    1: "the creation of the world",
    2: "the Garden of Eden and creation of man and woman",
    3: "the serpent, the fall, and expulsion from Eden",
    4: "Cain and Abel, the first murder",
    5: "the genealogy from Adam to Noah",
    6: "corruption of mankind, Noah finds favor",
    7: "the flood and entering the ark",
    8: "the waters recede, Noah exits the ark",
    9: "God's covenant with Noah, the rainbow",
    10: "the table of nations descended from Noah",
    11: "the Tower of Babel and lineage to Abram",
    12: "God's call to Abram, journey to Canaan and Egypt",
    13: "Abram and Lot separate",
    14: "the war of the kings, Abram rescues Lot",
    15: "God's covenant with Abram, promise of descendants",
    16: "Hagar and the birth of Ishmael",
    17: "covenant of circumcision, Abram becomes Abraham",
    18: "the three visitors, Abraham intercedes for Sodom",
    19: "the destruction of Sodom and Gomorrah",
    20: "Abraham and Abimelech",
    21: "the birth of Isaac, Hagar and Ishmael sent away",
    22: "the binding of Isaac (Akeidah)",
    23: "the death of Sarah, purchase of the cave of Machpelah",
    24: "the servant seeks a wife for Isaac, Rebekah",
    25: "Abraham's death, Esau and Jacob, the birthright",
    26: "Isaac and Abimelech, wells and blessings",
    27: "Jacob obtains Esau's blessing through deception",
    28: "Jacob's dream at Bethel, the ladder",
    29: "Jacob meets Rachel, serves Laban",
    30: "the birth of Jacob's sons, flocks and prosperity",
    31: "Jacob flees from Laban, covenant at Gilead",
    32: "Jacob prepares to meet Esau, wrestles with the angel",
    33: "Jacob and Esau reconcile",
    34: "the incident at Shechem, Dinah",
    35: "Jacob returns to Bethel, deaths of Rachel and Isaac",
    36: "the descendants of Esau (Edom)",
    37: "Joseph's dreams, sold into slavery",
    38: "Judah and Tamar",
    39: "Joseph in Potiphar's house, imprisoned",
    40: "Joseph interprets dreams in prison",
    41: "Pharaoh's dreams, Joseph rises to power",
    42: "the brothers' first journey to Egypt",
    43: "the brothers' second journey with Benjamin",
    44: "the silver cup, Judah's plea",
    45: "Joseph reveals himself to his brothers",
    46: "Jacob's family goes down to Egypt",
    47: "Jacob before Pharaoh, the famine",
    48: "Jacob blesses Ephraim and Manasseh",
    49: "Jacob's blessings to the twelve tribes",
    50: "the deaths of Jacob and Joseph",
}


def build_insight_pieces(vs, ch, idx, all_verses, word_freq_map, existing_insights, data=None):
    """Generate a list of insight sentences. Returns list of strings."""
    pieces = []

    # Check what content already exists in insights to avoid duplicating
    existing = existing_insights or ''
    existing_lower = existing.lower()

    # 1. Word frequency analysis
    if 'unique translated terms' not in existing_lower:
        words = vs.get('words', [])
        unique_eng = set()
        for w in words:
            eng = w.get('eng', '')
            if eng:
                unique_eng.add(eng.split('[')[0].strip())
        best_word = None
        best_count = 0
        for w in words:
            eng = w.get('eng', '').split('[')[0].strip()
            root = w.get('root', '')
            if root and root in word_freq_map and word_freq_map[root] > best_count:
                best_count = word_freq_map[root]
                best_word = eng
        s = f"This verse contains {len(unique_eng)} unique translated terms."
        if best_word and best_count > 5:
            s += f" The root of '{best_word}' appears {best_count} times across Genesis."
        pieces.append(s)

    # 2. Verse position context
    if 'position:' not in existing_lower:
        v_num = vs['verse']
        ch_num = ch['chapter']
        total_ch_verses = len(ch['verses'])
        pos = position_label(v_num, total_ch_verses)
        topic = CHAPTER_TOPICS.get(ch_num, "the narrative")
        pieces.append(
            f"This is verse {v_num} of {total_ch_verses} in chapter {ch_num} "
            f"(position: {pos}). Chapter {ch_num} spans {topic}."
        )

    # 3. Letter statistics
    if 'most frequent' not in existing_lower or 'hebrew letters' not in existing_lower:
        hebrew = vs.get('hebrew_full', '')
        counts = count_hebrew_letters(hebrew)
        if counts:
            total_letters = sum(counts.values())
            mc_ch, mc_count = counts.most_common(1)[0]
            letter_name = get_letter_name(mc_ch)
            meaning = get_letter_meaning(mc_ch)
            pieces.append(
                f"Among {total_letters} Hebrew letters in this verse, the most frequent is "
                f"{letter_name} ({mc_count} occurrences), traditionally associated with {meaning}."
            )

    # 4. Adjacent verse gematria connections
    if 'previous verse has gematria' not in existing_lower:
        cur_gem = vs.get('total_gematria', 0)
        if cur_gem:
            prev_vs = all_verses[idx - 1][1] if idx > 0 else None
            next_vs = all_verses[idx + 1][1] if idx < len(all_verses) - 1 else None
            parts = []
            if prev_vs and prev_vs.get('total_gematria'):
                prev_gem = prev_vs['total_gematria']
                diff = abs(cur_gem - prev_gem)
                s = cur_gem + prev_gem
                parts.append(f"The previous verse has gematria {prev_gem}; together they sum to {s} (difference: {diff}).")
                if s % 7 == 0:
                    parts.append(f"Their sum {s} is divisible by 7, the number of completion.")
                elif diff % 18 == 0 and diff > 0:
                    parts.append(f"Their difference {diff} is a multiple of 18 (chai, life).")
            if next_vs and next_vs.get('total_gematria'):
                next_gem = next_vs['total_gematria']
                diff = abs(cur_gem - next_gem)
                s = cur_gem + next_gem
                parts.append(f"The next verse has gematria {next_gem}; together they sum to {s}.")
                if s % 7 == 0:
                    parts.append(f"This combined sum {s} is divisible by 7.")
                elif s % 26 == 0:
                    parts.append(f"This combined sum {s} is divisible by 26, the value of the Divine Name.")
            if parts:
                pieces.append(" ".join(parts))

    # 5. Extended letter breakdown (for larger gaps)
    if 'letter breakdown' not in existing_lower:
        hebrew = vs.get('hebrew_full', '')
        counts = count_hebrew_letters(hebrew)
        if counts and len(counts) > 3:
            top3 = counts.most_common(3)
            breakdown_parts = []
            for ch_letter, cnt in top3:
                name = get_letter_name(ch_letter)
                meaning = get_letter_meaning(ch_letter)
                breakdown_parts.append(f"{name} ({cnt}, {meaning})")
            pieces.append(
                f"Letter breakdown of the top three consonants: {'; '.join(breakdown_parts)}."
            )

    # 6. Word-by-word gematria sums
    if 'individual word gematria' not in existing_lower:
        words = vs.get('words', [])
        if 2 <= len(words) <= 8:
            gem_parts = []
            for w in words:
                eng = w.get('eng', '').split('[')[0].strip()
                gem = w.get('gem', 0)
                if eng and gem:
                    gem_parts.append(f"'{eng}' = {gem}")
            if gem_parts:
                pieces.append(f"Individual word gematria values: {', '.join(gem_parts)}.")

    # 7. Root analysis
    if 'unique roots' not in existing_lower:
        words = vs.get('words', [])
        roots = set()
        for w in words:
            r = w.get('root', '')
            if r:
                roots.add(r)
        if roots:
            pieces.append(f"This verse uses {len(roots)} unique roots out of {len(words)} total words.")

    # 8. Gematria factorization
    if 'gematria factorization' not in existing_lower and 'verse gematria' not in existing_lower:
        cur_gem = vs.get('total_gematria', 0)
        if cur_gem and cur_gem > 1:
            factors = factorize(cur_gem)
            if len(factors) > 1:
                factor_str = ' x '.join(str(f) for f in factors)
                pieces.append(f"Verse gematria {cur_gem} = {factor_str}.")
                if cur_gem % 7 == 0:
                    pieces.append(f"Being divisible by 7, this connects to the theme of completeness and sanctity.")
                elif cur_gem % 26 == 0:
                    pieces.append(f"Being divisible by 26 (the value of the Tetragrammaton), this verse carries a connection to the Divine Name.")
                elif cur_gem % 18 == 0:
                    pieces.append(f"Being divisible by 18 (chai, meaning life), this verse resonates with the theme of vitality.")

    # 9. Transliteration patterns
    if 'transliteration' not in existing_lower:
        words = vs.get('words', [])
        trs = [w.get('tr', '') for w in words if w.get('tr')]
        if len(trs) >= 2:
            # Find repeated syllables
            all_syllables = []
            for tr in trs:
                syls = tr.replace("·", "-").split("-")
                all_syllables.extend([s.lower() for s in syls if len(s) > 1])
            syl_counts = Counter(all_syllables)
            repeated = [(s, c) for s, c in syl_counts.most_common(3) if c > 1]
            if repeated:
                rep_strs = [f"'{s}' ({c} times)" for s, c in repeated]
                pieces.append(f"Repeated syllables in the transliteration: {', '.join(rep_strs)}.")

    # 10. Meaning multiplicity
    if 'multiple meanings' not in existing_lower:
        words = vs.get('words', [])
        multi = []
        for w in words:
            meanings = w.get('meanings', '')
            if isinstance(meanings, str) and meanings.startswith('['):
                try:
                    ml = eval(meanings)
                    if isinstance(ml, list) and len(ml) > 3:
                        eng = w.get('eng', '').split('[')[0].strip()
                        multi.append((eng, len(ml)))
                except:
                    pass
            elif isinstance(meanings, list) and len(meanings) > 3:
                eng = w.get('eng', '').split('[')[0].strip()
                multi.append((eng, len(meanings)))
        if multi:
            parts = [f"'{e}' ({n} meanings)" for e, n in multi[:3]]
            pieces.append(f"Words with multiple meanings in this verse: {', '.join(parts)}.")

    # 11. Full letter distribution (extended version for big gaps)
    if 'full letter distribution' not in existing_lower:
        hebrew = vs.get('hebrew_full', '')
        counts = count_hebrew_letters(hebrew)
        if counts and len(counts) >= 5:
            sorted_letters = counts.most_common()
            dist_parts = [f"{get_letter_name(ch)}={cnt}" for ch, cnt in sorted_letters]
            pieces.append(f"Full letter distribution: {', '.join(dist_parts)}.")

    # 12. Chapter cumulative gematria position
    if 'cumulative chapter gematria' not in existing_lower:
        ch_num = ch['chapter']
        v_num = vs['verse']
        cum = 0
        verse_cum = 0
        for v2 in ch['verses']:
            g = v2.get('total_gematria', 0) or 0
            cum += g
            if v2['verse'] <= v_num:
                verse_cum = cum
        if cum > 0:
            pct = round(100 * verse_cum / cum, 1)
            pieces.append(
                f"Cumulative chapter gematria through this verse: {verse_cum} of {cum} total ({pct}% of chapter {ch_num})."
            )

    # 13. Word length analysis
    if 'average word length' not in existing_lower:
        words = vs.get('words', [])
        hebrew_words = [w.get('heb', '') for w in words if w.get('heb')]
        if hebrew_words:
            lengths = []
            for hw in hebrew_words:
                # Count only consonants
                lcount = sum(1 for c in hw if LETTER_MERGE.get(c, c) in HEBREW_LETTERS)
                lengths.append(lcount)
            if lengths:
                avg = round(sum(lengths) / len(lengths), 1)
                longest_idx = lengths.index(max(lengths))
                longest_eng = words[longest_idx].get('eng', '').split('[')[0].strip() if longest_idx < len(words) else ''
                pieces.append(
                    f"Average word length: {avg} consonants. The longest word is '{longest_eng}' with {max(lengths)} consonants."
                )

    # 14. Gematria digit sum
    if 'digit sum' not in existing_lower:
        cur_gem = vs.get('total_gematria', 0)
        if cur_gem:
            dsum = sum(int(d) for d in str(cur_gem))
            while dsum >= 10:
                dsum = sum(int(d) for d in str(dsum))
            pieces.append(
                f"The gematria {cur_gem} reduces to a digit sum of {dsum}. "
                f"In Jewish numerology, {dsum} is associated with "
                + {1: "unity and new beginnings", 2: "partnership and witness",
                   3: "completeness of testimony", 4: "the four matriarchs and directions",
                   5: "the five books of Torah", 6: "the six days of creation",
                   7: "holiness, Shabbat, and divine rest", 8: "new beginnings beyond nature",
                   9: "truth and finality"}.get(dsum, "spiritual significance") + "."
            )

    # 15. Verse in broader Torah context
    if 'broader Torah context' not in existing_lower:
        ch_num = ch['chapter']
        v_num = vs['verse']
        # Calculate absolute verse number
        abs_num = 0
        for c2 in data['chapters']:
            for v2 in c2['verses']:
                abs_num += 1
                if c2['chapter'] == ch_num and v2['verse'] == v_num:
                    break
            else:
                continue
            break
        pieces.append(
            f"In broader Torah context, this is verse {abs_num} of 1,533 in Genesis "
            f"({round(100 * abs_num / 1533, 1)}% through the book)."
        )

    # 16. Commentary density observation
    if 'commentary density' not in existing_lower:
        active = sum(1 for f in COMMENTARY_FIELDS if vs.get(f))
        total_comm_len = sum(len(vs.get(f, '') or '') for f in COMMENTARY_FIELDS)
        if active > 0:
            avg_comm = total_comm_len // active
            pieces.append(
                f"This verse has {active} commentary sections with an average length of {avg_comm} characters, "
                f"{'indicating extensive rabbinic discussion' if avg_comm > 500 else 'reflecting focused commentary'}."
            )

    return pieces


def factorize(n):
    """Simple factorization."""
    if n <= 1:
        return [n]
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def trim_to_fit(text, target_len):
    """Trim text to target_len at a sentence boundary."""
    if len(text) <= target_len:
        return text
    trimmed = text[:target_len]
    last_period = trimmed.rfind('.')
    if last_period > 50:
        return trimmed[:last_period + 1]
    return trimmed


def main():
    with open('genesis_v3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Pre-compute word root frequencies
    word_freq_map = Counter()
    for ch in data['chapters']:
        for vs in ch['verses']:
            for w in vs.get('words', []):
                root = w.get('root', '')
                if root:
                    word_freq_map[root] += 1

    # Build flat verse list
    all_verses = []
    for ch in data['chapters']:
        for vs in ch['verses']:
            all_verses.append((ch, vs))

    total_filled = 0
    total_chars_added = 0
    already_full = 0

    for idx, (ch, vs) in enumerate(all_verses):
        available = compute_available_for_new_insights(vs)

        if available <= 50:
            already_full += 1
            continue

        existing = vs.get('insights', '') or ''

        # Generate insight pieces
        pieces = build_insight_pieces(vs, ch, idx, all_verses, word_freq_map, existing, data)

        if not pieces:
            already_full += 1
            continue

        new_text = " ".join(pieces)

        # Target: fill the gap but don't overshoot
        target_len = int(available * 0.92)
        new_text = trim_to_fit(new_text, target_len)

        if len(new_text) < 20:
            already_full += 1
            continue

        # Append
        if existing:
            vs['insights'] = existing + " " + new_text
        else:
            vs['insights'] = new_text

        total_filled += 1
        total_chars_added += len(new_text)

    # Save
    with open('genesis_v3.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Verify
    remaining_gaps = 0
    for ch in data['chapters']:
        for vs in ch['verses']:
            avail = compute_available_for_new_insights(vs)
            if avail > 50:
                remaining_gaps += 1

    print(f"=== Fill Remaining Gaps Report ===")
    print(f"Total verses: {len(all_verses)}")
    print(f"Already full (gap <= 50): {already_full}")
    print(f"Verses filled this pass: {total_filled}")
    print(f"Total chars added: {total_chars_added}")
    print(f"Remaining gaps (>50 chars): {remaining_gaps}")
    print(f"Saved to genesis_v3.json")


if __name__ == '__main__':
    main()
