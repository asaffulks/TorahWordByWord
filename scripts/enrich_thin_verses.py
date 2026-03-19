#!/usr/bin/env python3
"""
Enrich thin commentary verses in genesis_v3.json with richer gematria
and Kabbalistic insights. Targets verses with < 500 chars total commentary.
"""

import json
import sys
import math

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- Significant numbers and their meanings ---
SIGNIFICANT_NUMBERS = {
    1: "absolute unity (Echad)",
    3: "the Patriarchs (Avot)",
    4: "the Matriarchs / four worlds",
    7: "completion and holiness (Shabbat)",
    8: "beyond nature (brit milah on 8th day)",
    10: "divine order (Ten Commandments, Ten Sefirot)",
    12: "the twelve tribes of Israel",
    13: "unity/love (gematria of Echad/Ahavah)",
    18: "chai (life)",
    22: "letters of the Hebrew alphabet / paths on the Tree of Life",
    26: "the Tetragrammaton (YHWH)",
    32: "paths of wisdom (Lev, heart)",
    36: "double-chai / the 36 hidden righteous (Lamed-Vav Tzaddikim)",
    40: "trial, testing, and transformation",
    42: "the 42-letter Name of God",
    50: "Jubilee / the 50th Gate of Understanding (Binah)",
    70: "the seventy nations / seventy elders",
    72: "the 72 Names of God",
    86: "Elohim (divine judgment)",
    100: "fullness and completeness (Me'ah)",
    248: "positive mitzvot / limbs of the body",
    314: "Shaddai (Almighty)",
    358: "Mashiach (Messiah)",
    365: "negative mitzvot / days of the solar year",
    541: "Yisrael (Israel)",
    613: "total mitzvot",
}

# Word-level significant gematria values
WORD_GEMATRIA = {
    1: "Alef, unity",
    5: "Heh, divine breath",
    8: "Chet, life-force",
    13: "Echad (one) / Ahavah (love)",
    17: "Tov (good)",
    18: "Chai (life)",
    21: "Ehyeh (I Am)",
    26: "YHWH",
    30: "Lamed, learning",
    36: "Leah / double-chai",
    40: "Mem, waters of Torah",
    42: "the 42-letter Name",
    44: "Dam (blood, life-force)",
    45: "Adam (man) / Mah (What)",
    50: "Nun, Jubilee",
    52: "Ben (son)",
    58: "Chen (grace)",
    68: "Chaim (life, plural)",
    72: "Chesed (lovingkindness)",
    78: "Lechem (bread) / Mazal",
    86: "Elohim (God as Judge)",
    91: "Amen / union of YHWH and Adonai",
    100: "Kuf, holiness",
    110: "Nes (miracle)",
    137: "Kabbalah (receiving)",
    200: "Resh, head/beginning",
    248: "Avraham / Rechem (womb)",
    300: "Ruach Elohim (Spirit of God: Shin)",
    314: "Shaddai (Almighty)",
    340: "Shem (name)",
    345: "Moshe (Moses) / HaShem",
    358: "Mashiach / Nachash (serpent)",
    400: "Tav, completion/truth",
    410: "Shema / Kadosh (holy)",
    430: "Nefesh (soul)",
    441: "Emet (truth)",
    480: "Talmud",
    541: "Yisrael (Israel)",
    611: "Torah",
    613: "Moshe Rabbeinu",
}

# Sefirot
SEFIROT = [
    "Keter (Crown)", "Chokhmah (Wisdom)", "Binah (Understanding)",
    "Chesed (Lovingkindness)", "Gevurah (Strength)", "Tiferet (Beauty)",
    "Netzach (Victory)", "Hod (Splendor)", "Yesod (Foundation)",
    "Malkhut (Sovereignty)"
]

FOUR_WORLDS = ["Atzilut (Emanation)", "Beriah (Creation)", "Yetzirah (Formation)", "Assiah (Action)"]


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def is_triangular(n):
    """Check if n is a triangular number (1, 3, 6, 10, 15, 21, 28, ...)"""
    if n <= 0:
        return False, 0
    # n = k*(k+1)/2 => k^2 + k - 2n = 0 => k = (-1 + sqrt(1+8n))/2
    discriminant = 1 + 8 * n
    sqrt_d = int(math.isqrt(discriminant))
    if sqrt_d * sqrt_d == discriminant and (sqrt_d - 1) % 2 == 0:
        k = (sqrt_d - 1) // 2
        return True, k
    return False, 0


def meaningful_factors(n):
    """Find meaningful factor pairs."""
    results = []
    for sig_num, meaning in SIGNIFICANT_NUMBERS.items():
        if sig_num > 1 and n % sig_num == 0 and n // sig_num > 1:
            quotient = n // sig_num
            if quotient in SIGNIFICANT_NUMBERS:
                results.append(f"{sig_num} x {quotient} ({meaning} x {SIGNIFICANT_NUMBERS[quotient]})")
            elif quotient <= 100:
                results.append(f"{sig_num} x {quotient} ({meaning})")
    return results


def count_hebrew_letters(word):
    """Count actual Hebrew letters in a word (skip nikkud/cantillation)."""
    count = 0
    for ch in word:
        cp = ord(ch)
        if 0x05D0 <= cp <= 0x05EA:  # Alef through Tav
            count += 1
    return count


def build_insights(verse, chapter_num, verse_num, chapter_totals):
    """Build rich insight text for a verse."""
    parts = []
    words = verse.get('words', [])
    total_gem = verse.get('total_gematria', 0)
    word_count = len(words)

    # Count total letters
    total_letters = sum(count_hebrew_letters(w['heb']) for w in words)

    # --- 1. Structural observations ---
    struct_parts = []
    word_note = ""
    if word_count == 10:
        word_note = ", mirroring the Ten Sefirot"
    elif word_count == 7:
        word_note = ", reflecting the seven days of creation and divine completion"
    elif word_count == 3:
        word_note = ", echoing the three Patriarchs and the tripartite structure of creation"
    elif word_count == 4:
        word_note = ", corresponding to the four worlds of Kabbalistic cosmology and the four letters of the Divine Name"
    elif word_count == 5:
        word_note = ", corresponding to the five books of Torah and the five levels of the soul"
    elif word_count == 6:
        word_note = ", corresponding to the six days of creation and the six spatial directions"
    elif word_count == 12:
        word_note = ", paralleling the twelve tribes of Israel"
    elif word_count == 22:
        word_note = ", matching the twenty-two letters of the Hebrew alphabet"

    struct_parts.append(f"This verse contains {word_count} words and {total_letters} Hebrew letters{word_note}")

    if total_letters == 22:
        struct_parts.append("The 22 letters mirror the 22 paths on the Kabbalistic Tree of Life")
    elif total_letters == 32:
        struct_parts.append("The 32 letters correspond to the 32 Paths of Wisdom described in Sefer Yetzirah")
    elif total_letters == 10:
        struct_parts.append("The 10 letters correspond to the Ten Sefirot")
    elif total_letters in SIGNIFICANT_NUMBERS:
        struct_parts.append(f"The letter count ({total_letters}) connects to {SIGNIFICANT_NUMBERS[total_letters]}")

    parts.append(". ".join(struct_parts) + ".")

    # Central word
    if word_count >= 3:
        mid_idx = word_count // 2
        mid_word = words[mid_idx]
        parts.append(f"The central word is \"{mid_word['eng']}\" ({mid_word['heb']}), with gematria {mid_word['gem']}.")

    # First and last word connection
    if word_count >= 2:
        first_w = words[0]
        last_w = words[-1]
        fl_sum = first_w['gem'] + last_w['gem']
        note = f"First word \"{first_w['eng']}\" ({first_w['gem']}) and last word \"{last_w['eng']}\" ({last_w['gem']}) together equal {fl_sum}"
        if fl_sum in WORD_GEMATRIA:
            note += f", the value of {WORD_GEMATRIA[fl_sum]}"
        elif fl_sum in SIGNIFICANT_NUMBERS:
            note += f", connected to {SIGNIFICANT_NUMBERS[fl_sum]}"
        parts.append(note + ".")

    # --- 2. Verse total gematria connections ---
    gem_parts = []
    gem_parts.append(f"Total gematria: {total_gem}")

    # Direct match
    if total_gem in SIGNIFICANT_NUMBERS:
        gem_parts.append(f"a number signifying {SIGNIFICANT_NUMBERS[total_gem]}")

    # Multiples of significant numbers
    mult_notes = []
    for sig in [7, 10, 13, 18, 26, 36, 42, 50, 72, 86]:
        if total_gem % sig == 0 and total_gem != sig:
            quotient = total_gem // sig
            meaning = SIGNIFICANT_NUMBERS[sig]
            if quotient in SIGNIFICANT_NUMBERS:
                mult_notes.append(f"{sig} x {quotient} ({meaning} x {SIGNIFICANT_NUMBERS[quotient]})")
            else:
                mult_notes.append(f"{sig} x {quotient} ({meaning})")
    if mult_notes:
        gem_parts.append("divisible as " + mult_notes[0])
        if len(mult_notes) > 1:
            gem_parts.append("also " + mult_notes[1])

    # Triangular number
    tri, tri_k = is_triangular(total_gem)
    if tri:
        gem_parts.append(f"a triangular number (T{tri_k}), representing cumulative wholeness")

    # Prime
    if is_prime(total_gem):
        gem_parts.append("a prime number, signifying indivisible unity")

    # Parallel with other verses in same chapter
    parallels = []
    for other_vnum, other_total in chapter_totals.items():
        if other_vnum != verse_num and other_total == total_gem:
            parallels.append(str(other_vnum))
    if parallels:
        gem_parts.append(f"shares its gematria with verse(s) {', '.join(parallels)} in this chapter, suggesting a hidden thematic link")

    parts.append(". ".join(gem_parts) + ".")

    # --- 3. Word-level gematria ---
    word_gems = [(w['eng'], w['heb'], w['gem']) for w in words if w['gem'] > 0]
    if word_gems:
        # Find words matching known values
        matches = []
        for eng, heb, gem in word_gems:
            if gem in WORD_GEMATRIA:
                matches.append(f"\"{eng}\" ({heb}, {gem}) equals {WORD_GEMATRIA[gem]}")
        if matches:
            parts.append("Word-level connections: " + "; ".join(matches[:3]) + ".")

        # Words with same gematria
        gem_groups = {}
        for eng, heb, gem in word_gems:
            gem_groups.setdefault(gem, []).append(f"\"{eng}\"")
        shared = {g: ws for g, ws in gem_groups.items() if len(ws) > 1}
        if shared:
            for g, ws in list(shared.items())[:1]:
                parts.append(f"The words {' and '.join(ws)} share gematria {g}, revealing a hidden bond between these concepts.")

        # Highest and lowest
        if len(word_gems) >= 3:
            sorted_gems = sorted(word_gems, key=lambda x: x[2])
            low = sorted_gems[0]
            high = sorted_gems[-1]
            if low[2] != high[2]:
                parts.append(f"The highest-value word is \"{high[0]}\" ({high[2]}) and the lowest is \"{low[0]}\" ({low[2]}), spanning a range of {high[2] - low[2]}.")

    # --- 4. Kabbalistic/Sefirotic connections ---
    kab_parts = []

    # Verse number connection
    if verse_num <= 10:
        sefirah = SEFIROT[verse_num - 1]
        kab_parts.append(f"As verse {verse_num}, this corresponds to the sefirah of {sefirah}")
    elif verse_num == 22:
        kab_parts.append("Verse 22 corresponds to the 22 letters of creation")
    elif verse_num == 32:
        kab_parts.append("Verse 32 aligns with the 32 Paths of Wisdom")

    # Chapter connection to four worlds
    if chapter_num <= 4:
        world = FOUR_WORLDS[chapter_num - 1]
        kab_parts.append(f"Chapter {chapter_num} resonates with the world of {world}")
    elif chapter_num <= 10:
        kab_parts.append(f"Chapter {chapter_num} resonates with the sefirah of {SEFIROT[chapter_num - 1]}")

    # Digital root (mystical reduction)
    if total_gem > 9:
        dr = total_gem
        while dr > 9:
            dr = sum(int(d) for d in str(dr))
        if dr in SIGNIFICANT_NUMBERS:
            kab_parts.append(f"Its digital root is {dr}, associated with {SIGNIFICANT_NUMBERS[dr]}")
        elif dr <= 10:
            kab_parts.append(f"Its kabbalistic reduction yields {dr}, linking to {SEFIROT[dr - 1]}")

    if kab_parts:
        parts.append(". ".join(kab_parts) + ".")

    # --- 5. Repeated roots ---
    roots = [w.get('root', '') for w in words if w.get('root', '')]
    root_counts = {}
    for r in roots:
        root_counts[r] = root_counts.get(r, 0) + 1
    repeated = {r: c for r, c in root_counts.items() if c > 1}
    if repeated:
        for r, c in repeated.items():
            parts.append(f"The root {r} appears {c} times, emphasizing its thematic centrality through repetition.")

    # Combine and trim to target range (400-800 chars)
    result = " ".join(parts)

    # Trim if too long
    while len(result) > 800 and len(parts) > 3:
        parts.pop()
        result = " ".join(parts)

    # Pad if too short - add extra observations
    if len(result) < 400 and total_gem > 0:
        # Add digit sum observation
        digit_sum = sum(int(d) for d in str(total_gem))
        if digit_sum in SIGNIFICANT_NUMBERS:
            parts.append(f"The digit sum of the total gematria ({digit_sum}) connects to {SIGNIFICANT_NUMBERS[digit_sum]}.")
        # Add ratio of highest word to total
        if word_gems:
            sorted_gems = sorted(word_gems, key=lambda x: x[2], reverse=True)
            top = sorted_gems[0]
            pct = round(top[2] / total_gem * 100)
            parts.append(f"The word \"{top[0]}\" carries {pct}% of the verse's total gematric weight, marking it as the energetic focus of the verse.")
        # Mention unique roots
        unique_roots = set(w.get('root', '') for w in words if w.get('root', ''))
        if unique_roots:
            parts.append(f"The verse draws from {len(unique_roots)} distinct roots, each contributing a unique semantic thread to its meaning.")
        result = " ".join(parts)

    return result


def main():
    input_file = "genesis_v3.json"
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    commentary_fields = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim', 'kli_yakar',
                         'chizkuni', 'rabbeinu_bahya', 'onkelos']

    # Pre-compute chapter totals for cross-referencing
    all_chapter_totals = {}
    for ch in data['chapters']:
        ch_num = ch['chapter']
        totals = {}
        for v in ch['verses']:
            totals[v['verse']] = v.get('total_gematria', 0)
        all_chapter_totals[ch_num] = totals

    enriched_count = 0
    total_thin = 0

    for ch in data['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            total_commentary = sum(len(v.get(f, '') or '') for f in commentary_fields)

            if total_commentary < 500:
                total_thin += 1
                chapter_totals = all_chapter_totals[ch_num]

                new_insights = build_insights(v, ch_num, v_num, chapter_totals)

                v['insights'] = new_insights
                enriched_count += 1

    print(f"Found {total_thin} thin verses (< 500 chars commentary)")
    print(f"Enriched {enriched_count} verses with richer insights")

    # Show a sample
    for ch in data['chapters']:
        for v in ch['verses']:
            commentary_total = sum(len(v.get(f, '') or '') for f in commentary_fields)
            if commentary_total < 500 and len(v.get('insights', '')) > 300:
                print(f"\nSample enriched verse - {v['ref']}:")
                print(f"  Insight length: {len(v['insights'])} chars")
                print(f"  Text: {v['insights'][:500]}...")
                break
        else:
            continue
        break

    # Save
    print(f"\nSaving to {input_file}...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Done!")


if __name__ == '__main__':
    main()
