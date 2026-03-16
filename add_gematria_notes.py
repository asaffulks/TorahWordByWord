"""
Add computed gematria notes to each verse's gem_note field in genesis.json.
Only notes genuinely interesting mathematical properties.
"""

import json
import math
import re
from collections import Counter


def prime_factors(n):
    """Return list of prime factors with multiplicity."""
    if n < 2:
        return []
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


def strip_niqqud(s):
    """Strip cantillation marks and vowel points, leaving only consonants."""
    # Hebrew consonants are U+05D0-U+05EA, maqaf U+05BE
    return re.sub(r'[\u0591-\u05BD\u05BF-\u05C7]', '', s)


def format_factorization(n):
    """Format prime factorization, return string or None if not interesting."""
    factors = prime_factors(n)
    if not factors:
        return None
    counts = Counter(factors)
    unique = sorted(counts.keys())

    # Not interesting: prime itself
    if len(factors) == 1:
        return None

    # Not interesting: 2 x prime, 3 x prime (too simple)
    if len(factors) == 2 and len(unique) == 2:
        if min(unique) <= 3 and max(unique) > 50:
            return None

    # Not interesting: only 2 factors total and no structure
    if len(factors) == 2 and len(unique) == 2 and all(c == 1 for c in counts.values()):
        # Two distinct primes multiplied — only interesting if palindromic or notable
        a, b = unique
        if str(a) != str(b)[::-1]:
            return None

    # Build the string
    parts = []
    for p in sorted(counts.keys()):
        if counts[p] == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{counts[p]}")
    factorization_str = " x ".join(parts)

    # Check if genuinely interesting:
    interesting = False

    # Palindromic factor pair (37 x 73)
    for f in unique:
        rev_s = str(f)[::-1]
        if len(str(f)) >= 2 and rev_s != str(f):
            rev = int(rev_s)
            if rev in counts:
                interesting = True

    # Power of a single prime (e.g., 2^10, 3^5)
    if len(unique) == 1 and counts[unique[0]] >= 3:
        interesting = True

    # Perfect power: n^k where k >= 2 and n is composite
    if len(unique) >= 2 and all(c >= 2 for c in counts.values()):
        interesting = True

    # Many distinct factors (5+) — highly composite
    if len(unique) >= 5:
        interesting = True

    # 4 distinct factors, ALL small (<= 20)
    if len(unique) == 4 and all(p <= 20 for p in unique):
        interesting = True

    # High total factor count (>= 6 prime factors with multiplicity)
    if len(factors) >= 6 and len(unique) >= 3:
        interesting = True

    # All factors are small and beautiful (all <= 13 with total >= 4)
    if all(p <= 13 for p in unique) and len(factors) >= 4:
        interesting = True

    # Repunit-related or round numbers
    if n % 100 == 0 or n % 1000 == 0:
        interesting = True

    if not interesting:
        return None

    return f"{n} = {factorization_str}"


def is_triangular(n):
    """Check if n is a triangular number T_k = k*(k+1)/2. Return k or None."""
    if n < 1:
        return None
    discriminant = 1 + 8 * n
    sqrt_d = int(math.isqrt(discriminant))
    if sqrt_d * sqrt_d == discriminant and (sqrt_d - 1) % 2 == 0:
        k = (sqrt_d - 1) // 2
        if k * (k + 1) // 2 == n:
            return k
    return None


def is_perfect_square(n):
    """Check if n is a perfect square. Return sqrt or None."""
    if n < 4:
        return None
    s = int(math.isqrt(n))
    if s * s == n:
        return s
    return None


def find_shared_gematria(words):
    """Find words with shared gematria, excluding trivially identical words."""
    gem_groups = {}
    for w in words:
        g = w["gem"]
        if g <= 0:
            continue
        consonants = strip_niqqud(w["heb"])
        if g not in gem_groups:
            gem_groups[g] = []
        gem_groups[g].append((w["heb"], consonants))

    results = []
    for g, entries in gem_groups.items():
        if len(entries) < 2:
            continue
        # Check if at least two entries have DIFFERENT consonants
        consonant_set = set(c for _, c in entries)
        if len(consonant_set) < 2:
            continue  # Same word repeated, skip
        # Pick two with different consonants
        seen = {}
        pair = []
        for heb, cons in entries:
            if cons not in seen:
                seen[cons] = heb
                pair.append(heb)
                if len(pair) == 2:
                    break
        if len(pair) == 2:
            results.append((g, pair[0], pair[1]))

    return results


def find_interesting_properties(total, words):
    """Build a concise note about interesting gematria properties of the verse."""
    parts = []

    # Prime factorization
    fact = format_factorization(total)

    # Triangular number
    tri = is_triangular(total)

    # Perfect square
    sq = is_perfect_square(total)

    # Build the main number note
    if fact and tri:
        parts.append(f"{fact} (triangular T{tri})")
    elif fact and sq:
        parts.append(f"{fact} (perfect square, {sq}^2)")
    elif tri:
        parts.append(f"{total} = triangular T{tri}")
    elif sq:
        factors = prime_factors(total)
        counts = Counter(factors)
        fp = []
        for p in sorted(counts.keys()):
            if counts[p] == 1:
                fp.append(str(p))
            else:
                fp.append(f"{p}^{counts[p]}")
        parts.append(f"{total} = {' x '.join(fp)} ({sq}^2, perfect square)")
    elif fact:
        parts.append(fact)

    # Shared gematria between different words
    shared = find_shared_gematria(words)
    if shared:
        shared.sort(key=lambda x: x[0], reverse=True)
        g, w1, w2 = shared[0]
        parts.append(f"{w1} and {w2} both = {g}")

    # Word and letter count
    num_words = len(words)
    num_letters = sum(1 for w in words for ch in strip_niqqud(w['heb']) if '\u05D0' <= ch <= '\u05EA')
    if num_words > 0 and num_letters > 0:
        # Only note if counts are interesting (multiples of 7, perfect numbers, etc.)
        if num_words == 7 or num_letters == 28 or num_letters % 7 == 0:
            parts.append(f"{num_words} words, {num_letters} letters")

    # Notable individual word values
    NOTABLE = {26: 'YHWH', 86: 'Elohim', 345: 'Moshe', 314: 'Shaddai',
               72: 'Chesed', 17: 'Tov', 18: 'Chai', 36: 'double-Chai',
               613: 'mitzvot', 248: 'limbs', 365: 'sinews'}
    for w in words:
        g = w.get('gem', 0)
        if g in NOTABLE:
            cons = strip_niqqud(w['heb'])
            # Don't note if the word IS the thing (e.g. אלהים = 86 = Elohim is obvious)
            if NOTABLE[g].lower() not in w.get('eng', '').lower():
                parts.append(f"{w['heb']} = {g} ({NOTABLE[g]})")
                break  # only one notable per verse

    if not parts:
        return ""

    note = ". ".join(parts)
    if len(note) > 200:
        note = note[:197] + "..."
    return note


def main():
    input_path = "K:/TorahByWord/genesis.json"

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    notes_added = 0
    total_verses = 0

    for chapter in data["chapters"]:
        for verse in chapter["verses"]:
            total_verses += 1
            total_gem = verse.get("total_gematria", 0)
            words = verse.get("words", [])
            if total_gem and words:
                note = find_interesting_properties(total_gem, words)
                verse["gem_note"] = note
                if note:
                    notes_added += 1
            else:
                verse["gem_note"] = ""

    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Processed {total_verses} verses, added notes to {notes_added}.")
    # Show examples
    count = 0
    for ch in data["chapters"]:
        for v in ch["verses"]:
            n = v.get("gem_note", "")
            if n:
                count += 1
                if count <= 15:
                    print(f"  {v['ref']}: {ascii(n)}")


if __name__ == "__main__":
    main()
