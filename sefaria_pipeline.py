#!/usr/bin/env python3
"""
Sefaria Data Pipeline — Tanach: Word by Word
=============================================
Pulls all of Genesis (50 chapters, 1,533 verses) from the Sefaria API
and outputs a clean genesis.json with word-level interlinear data.

Run:      python sefaria_pipeline.py
Output:   genesis.json + sefaria_cache/ directory

Requires: pip install requests
"""

import html
import json
import os
import re
import sys
import time
import unicodedata
import requests
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── Configuration ──────────────────────────────────────────────────────────

BOOK = "Genesis"
HE_BOOK = "\u05D1\u05B0\u05BC\u05E8\u05B5\u05D0\u05E9\u05C1\u05B4\u05D9\u05EA"  # בְּרֵאשִׁית
TOTAL_CHAPTERS = 50
CACHE_DIR = Path("sefaria_cache")
OUTPUT_FILE = "genesis.json"
API_BASE = "https://www.sefaria.org/api"
RATE_LIMIT = 0.5  # seconds between API calls

# ─── Gematria ───────────────────────────────────────────────────────────────

GEMATRIA_MAP = {
    '\u05D0': 1, '\u05D1': 2, '\u05D2': 3, '\u05D3': 4, '\u05D4': 5,
    '\u05D5': 6, '\u05D6': 7, '\u05D7': 8, '\u05D8': 9,
    '\u05D9': 10, '\u05DB': 20, '\u05DA': 20, '\u05DC': 30,
    '\u05DE': 40, '\u05DD': 40, '\u05E0': 50, '\u05DF': 50,
    '\u05E1': 60, '\u05E2': 70, '\u05E4': 80, '\u05E3': 80,
    '\u05E6': 90, '\u05E5': 90, '\u05E7': 100, '\u05E8': 200,
    '\u05E9': 300, '\u05EA': 400,
}

def strip_nikud(text):
    """Remove vowel marks U+05B0-U+05C7 and cantillation U+0591-U+05AF."""
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', text)

def calc_gematria(word):
    """Calculate standard Mispar Hechrachi gematria (consonants only)."""
    clean = strip_nikud(word)
    return sum(GEMATRIA_MAP.get(c, 0) for c in clean)

# ─── Transliteration ───────────────────────────────────────────────────────

CONSONANT_MAP = {
    '\u05D0': "'", '\u05D1': 'v', '\u05D2': 'g', '\u05D3': 'd',
    '\u05D4': 'h', '\u05D5': 'v', '\u05D6': 'z', '\u05D7': 'ch',
    '\u05D8': 't', '\u05D9': 'y', '\u05DB': 'ch', '\u05DA': 'ch',
    '\u05DC': 'l', '\u05DE': 'm', '\u05DD': 'm', '\u05E0': 'n',
    '\u05DF': 'n', '\u05E1': 's', '\u05E2': "'", '\u05E4': 'f',
    '\u05E3': 'f', '\u05E6': 'ts', '\u05E5': 'ts', '\u05E7': 'k',
    '\u05E8': 'r', '\u05E9': 'sh', '\u05EA': 't',
}

VOWEL_MAP = {
    '\u05B0': 'e',   # shva (often silent, simplified)
    '\u05B1': 'e',   # hataf segol
    '\u05B2': 'a',   # hataf patach
    '\u05B3': 'o',   # hataf qamats
    '\u05B4': 'i',   # hiriq
    '\u05B5': 'e',   # tsere
    '\u05B6': 'e',   # segol
    '\u05B7': 'a',   # patach
    '\u05B8': 'a',   # qamats
    '\u05B9': 'o',   # holam
    '\u05BA': 'o',   # holam haser
    '\u05BB': 'u',   # qubuts
}

def transliterate_hebrew(word):
    """Basic Hebrew-to-Latin transliteration with syllable dots and stress."""
    result = []
    chars = list(word)
    i = 0
    has_dagesh = set()

    # Pre-scan for dagesh positions
    for j, c in enumerate(chars):
        if c == '\u05BC':  # dagesh
            # Find preceding consonant
            for k in range(j - 1, -1, -1):
                if '\u05D0' <= chars[k] <= '\u05EA':
                    has_dagesh.add(k)
                    break

    i = 0
    while i < len(chars):
        c = chars[i]

        # Hebrew consonant
        if '\u05D0' <= c <= '\u05EA':
            # Shin vs Sin
            if c == '\u05E9':
                if i + 1 < len(chars) and chars[i + 1] == '\u05C2':
                    result.append('s')
                else:
                    result.append('sh')
            # Bet: dagesh = b, without = v
            elif c == '\u05D1':
                result.append('b' if i in has_dagesh else 'v')
            # Peh: dagesh = p, without = f
            elif c == '\u05E4':
                result.append('p' if i in has_dagesh else 'f')
            elif c == '\u05E3':  # final peh
                result.append('f')
            # Kaf: dagesh = k, without = ch
            elif c == '\u05DB':
                result.append('k' if i in has_dagesh else 'ch')
            elif c == '\u05DA':  # final kaf
                result.append('ch')
            else:
                result.append(CONSONANT_MAP.get(c, ''))
        # Vowel
        elif c in VOWEL_MAP:
            result.append(VOWEL_MAP[c])
        # Maqaf
        elif c == '\u05BE':
            result.append('-')
        # Skip dagesh, shin/sin dots, cantillation
        i += 1

    raw = ''.join(result)
    # Clean up
    raw = re.sub(r"'+", "'", raw)
    raw = raw.strip("'")
    raw = re.sub(r'(.)\1{2,}', r'\1\1', raw)

    # Simple syllable splitting: insert dots between CV groups
    # Heuristic: after vowel, before next consonant
    syllabified = []
    vowels = set('aeiou')
    prev_was_vowel = False
    for j, ch in enumerate(raw):
        if ch in vowels:
            prev_was_vowel = True
            syllabified.append(ch)
        elif ch == '-':
            syllabified.append('-')
            prev_was_vowel = False
        else:
            if prev_was_vowel and j > 0 and syllabified:
                syllabified.append('\u00B7')  # middle dot
            syllabified.append(ch)
            prev_was_vowel = False

    text = ''.join(syllabified)

    # Capitalize last syllable (Hebrew stress is usually on last syllable - milra)
    parts = text.split('\u00B7')
    if len(parts) > 1:
        parts[-1] = parts[-1].upper()
        text = '\u00B7'.join(parts)
    elif text:
        text = text.upper()

    return text if text else word


# ─── API Helpers ────────────────────────────────────────────────────────────

CACHE_DIR.mkdir(exist_ok=True)

def cached_get(endpoint, cache_key):
    """GET from Sefaria API with filesystem cache and rate limiting."""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, ValueError):
            # Corrupt cache file — delete and re-fetch
            cache_file.unlink()
            pass

    url = f"{API_BASE}/{endpoint}"
    time.sleep(RATE_LIMIT)

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            # Cache empty result for 404s to avoid re-fetching
            data = {}
        else:
            resp.raise_for_status()
            data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: API error for {endpoint}: {e}")
        return {}
    except json.JSONDecodeError:
        print(f"  WARNING: Invalid JSON from {endpoint}")
        return {}

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def get_chapter_text(chapter):
    """Get Hebrew + English text for an entire chapter."""
    return cached_get(
        f"texts/Genesis.{chapter}?context=0",
        f"text_genesis_{chapter}"
    )


def get_word_lookup(hebrew_word):
    """Look up a Hebrew word in Sefaria's lexicon."""
    # Use the word itself as cache key (filesystem-safe version)
    safe_key = strip_nikud(hebrew_word).replace('\u05BE', '_')
    # Remove any chars that are invalid in filenames
    safe_key = re.sub(r'[<>:"/\\|?*()[\]{}]', '', safe_key)
    if not safe_key:
        safe_key = 'empty'
    return cached_get(
        f"words/{requests.utils.quote(hebrew_word)}",
        f"word_{safe_key}"
    )


def get_rashi(chapter, verse):
    """Get ALL Rashi commentary for a verse (English, all comments joined)."""
    data = cached_get(
        f"texts/Rashi_on_Genesis.{chapter}.{verse}?lang=en&context=0",
        f"rashi_genesis_{chapter}_{verse}"
    )
    if not data:
        return ""

    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        # Join ALL comments, strip HTML from each
        parts = []
        for t in en:
            clean = re.sub(r'<[^>]+>', '', t).strip()
            clean = html.unescape(clean)
            if clean:
                parts.append(clean)
        text = ' '.join(parts)
    elif isinstance(en, str):
        text = re.sub(r'<[^>]+>', '', en)
        text = html.unescape(text)
    else:
        return ""

    text = text.strip()
    # No character cap — let the full commentary through
    return text


def get_ramban(chapter, verse):
    """Get Ramban (Nachmanides) commentary for a verse (English)."""
    data = cached_get(
        f"texts/Ramban_on_Genesis.{chapter}.{verse}?lang=en&context=0",
        f"ramban_genesis_{chapter}_{verse}"
    )
    if not data:
        return ""

    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        text = re.sub(r'<[^>]+>', '', ' '.join(en))
    elif isinstance(en, str):
        text = re.sub(r'<[^>]+>', '', en)
    else:
        return ""

    text = html.unescape(text).strip()
    # No character cap — let the full commentary through
    return text


def get_commentary(name, chapter, verse):
    """Get any named commentary from Sefaria. Returns empty string if unavailable."""
    data = cached_get(
        f"texts/{name}_on_Genesis.{chapter}.{verse}?lang=en&context=0",
        f"{name.lower()}_genesis_{chapter}_{verse}"
    )
    if not data:
        return ""

    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        text = re.sub(r'<[^>]+>', '', ' '.join(en))
    elif isinstance(en, str):
        text = re.sub(r'<[^>]+>', '', en)
    else:
        return ""

    text = html.unescape(text).strip()
    # No character cap — let the full commentary through
    return text


# ─── Word Processing ───────────────────────────────────────────────────────

# Cache for word lookups (in-memory, keyed by Hebrew word form)
word_lookup_cache = {}

def _lookup_single(word):
    """Look up a single Hebrew word (no maqaf) in Sefaria lexicon.
    Returns (root, english_gloss)."""
    data = get_word_lookup(word)

    if not isinstance(data, list) or len(data) == 0:
        return ("", "")

    entry = data[0]
    if not isinstance(entry, dict):
        return ("", "")

    # Extract root from headword
    root = ""
    headword = entry.get('headword', '')
    if headword:
        root_clean = strip_nikud(headword)
        root_clean = ''.join(c for c in root_clean if '\u05D0' <= c <= '\u05EA')
        if 2 <= len(root_clean) <= 4:
            root = root_clean

    # Extract English gloss from content.senses
    eng = ""
    content = entry.get('content', {})
    if isinstance(content, dict):
        senses = content.get('senses', [])
        if senses and isinstance(senses, list):
            first_sense = senses[0]
            if isinstance(first_sense, dict):
                eng = first_sense.get('definition', '')
                if isinstance(eng, str):
                    eng = eng.split(',')[0].strip()
                    eng = re.sub(r'<[^>]+>', '', eng).strip()
                    eng = html.unescape(eng)

    return (root, eng)


def lookup_word(hebrew_word):
    """Look up a Hebrew word and return (root, english_gloss).
    For maqaf-joined words, tries the whole compound first,
    then falls back to looking up individual parts."""
    if hebrew_word in word_lookup_cache:
        return word_lookup_cache[hebrew_word]

    result = ("", "")

    # First try the whole word (with maqaf stripped)
    lookup = hebrew_word.replace('\u05BE', '')
    if not lookup:
        word_lookup_cache[hebrew_word] = result
        return result

    result = _lookup_single(lookup)

    # If that failed and word has maqaf, try individual parts
    if (result[0] == "" or result[1] == "") and '\u05BE' in hebrew_word:
        parts = hebrew_word.split('\u05BE')
        roots = []
        glosses = []
        for part in parts:
            if not part:
                continue
            r, e = _lookup_single(part)
            if r:
                roots.append(r)
            if e:
                glosses.append(e)

        # Use the most meaningful root (usually the main verb/noun, not a prefix)
        if not result[0] and roots:
            # Prefer longer roots (skip common prefixes like את, ו)
            roots.sort(key=len, reverse=True)
            result = (roots[0], result[1])
        if not result[1] and glosses:
            # Join glosses with dot notation per the brief
            result = (result[0], '\u00B7'.join(glosses))

    word_lookup_cache[hebrew_word] = result
    return result


def clean_hebrew_text(text):
    """Thoroughly clean Hebrew text from Sefaria API."""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities (&thinsp; &nbsp; etc.)
    text = html.unescape(text)
    # Remove paseq mark (׀) and surrounding thin/non-breaking spaces
    text = re.sub(r'\s*\u05C0\s*', ' ', text)
    # Remove paragraph markers {פ} {ס} and surrounding spaces
    text = re.sub(r'\s*\{[פס]\}\s*', '', text)
    # Remove sof pasuq (׃) — the colon-like verse-end mark
    text = text.replace('\u05C3', '')
    # Remove Sefaria footnote markers like *(בספרי or *(כתיב
    text = re.sub(r'\*\([^)]*\)', '', text)
    text = re.sub(r'\*\([^)]*$', '', text)  # unclosed parens at end
    # Remove square brackets (ketiv/qere notation) but keep contents
    text = text.replace('[', '').replace(']', '')
    # Remove zero-width / invisible Unicode characters that merge words
    text = re.sub(r'[\u200B-\u200F\uFEFF\u034F]', '', text)
    # Fix specific case: consecutive Hebrew words merged (consonant + vowels + consonant
    # without space). Insert space before vav-conjunctive prefix after a word-final letter.
    # Pattern: letter + nikud/cantillation + letter that starts a new word (vav prefix)
    # This catches cases like יִשְׂרָאֵלוַיִּהְיוּ -> יִשְׂרָאֵל וַיִּהְיוּ
    text = re.sub(r'(\u05DC)([\u0591-\u05AF\u05B0-\u05C7]*)(\u05D5[\u05B7\u05B0-\u05C7])', r'\1\2 \3', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def process_verse(chapter, verse, he_text, en_text):
    """Process a single verse into full interlinear data."""
    ref = f"Bereshit {chapter}:{verse}"

    # Clean Hebrew text thoroughly
    he_clean = clean_hebrew_text(he_text)
    he_words = he_clean.split()

    # Get all commentaries
    rashi = get_rashi(chapter, verse)
    ramban = get_ramban(chapter, verse)
    ibn_ezra = get_commentary("Ibn_Ezra", chapter, verse)
    sforno = get_commentary("Sforno", chapter, verse)
    or_hachaim = get_commentary("Or_HaChaim", chapter, verse)

    # Build word list
    words = []
    for heb_word in he_words:
        gem_word = heb_word.replace('\u05BE', '')  # remove maqaf for gematria
        gem = calc_gematria(gem_word)
        tr = transliterate_hebrew(heb_word)
        root, eng = lookup_word(heb_word)

        words.append({
            "heb": heb_word,
            "tr": tr,
            "root": root,
            "eng": eng,
            "gem": gem,
        })

    # Clean English translation — remove footnotes before stripping HTML
    en_clean = ""
    if en_text:
        t = str(en_text)
        # Remove footnote markers and footnote content entirely
        t = re.sub(r'<sup[^>]*>.*?</sup>', '', t)
        t = re.sub(r'<i class="footnote">.*?</i>', '', t)
        # Strip remaining HTML
        t = re.sub(r'<[^>]+>', '', t)
        en_clean = html.unescape(t).strip()
        # Collapse multiple spaces
        en_clean = re.sub(r'\s+', ' ', en_clean)

    total_gem = sum(w["gem"] for w in words)

    return {
        "verse": verse,
        "ref": ref,
        "hebrew_full": he_clean,
        "translation": en_clean,
        "rashi": rashi,
        "ramban": ramban,
        "ibn_ezra": ibn_ezra,
        "sforno": sforno,
        "or_hachaim": or_hachaim,
        "total_gematria": total_gem,
        "gem_note": "",
        "words": words,
    }


# ─── Main Pipeline ─────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Tanach: Word by Word -- Sefaria Data Pipeline")
    print("  Pulling Genesis (50 chapters)")
    print("=" * 60)

    genesis = {
        "book": BOOK,
        "he_name": HE_BOOK,
        "chapters": []
    }

    total_verses = 0
    total_words = 0
    missing_roots = 0
    missing_glosses = 0
    missing_rashi = 0
    missing_ramban = 0

    for ch in range(1, TOTAL_CHAPTERS + 1):
        print(f"\nChapter {ch}...")
        ch_data = get_chapter_text(ch)

        if not ch_data:
            print(f"  WARNING: Could not fetch chapter {ch}, skipping")
            continue

        he_texts = ch_data.get("he", [])
        en_texts = ch_data.get("text", [])

        if not he_texts:
            print(f"  WARNING: No Hebrew text for chapter {ch}")
            continue

        if not isinstance(en_texts, list):
            en_texts = []
        while len(en_texts) < len(he_texts):
            en_texts.append("")

        chapter_obj = {
            "chapter": ch,
            "verses": []
        }

        for v_idx, he_text in enumerate(he_texts):
            verse_num = v_idx + 1

            if not he_text:
                continue

            verse_data = process_verse(ch, verse_num, he_text, en_texts[v_idx])
            chapter_obj["verses"].append(verse_data)

            total_verses += 1
            total_words += len(verse_data["words"])
            missing_roots += sum(1 for w in verse_data["words"] if w["root"] == "")
            missing_glosses += sum(1 for w in verse_data["words"] if w["eng"] == "")
            if verse_data["rashi"] == "":
                missing_rashi += 1
            if verse_data["ramban"] == "":
                missing_ramban += 1

            if verse_num % 10 == 0:
                print(f"  {verse_num} verses processed")

        genesis["chapters"].append(chapter_obj)
        print(f"  Chapter {ch} complete: {len(chapter_obj['verses'])} verses")

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(genesis, f, ensure_ascii=False, indent=2)

    # Validation summary
    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Chapters:       {len(genesis['chapters'])}")
    print(f"  Total verses:   {total_verses}")
    print(f"  Total words:    {total_words}")
    print(f"  Missing roots:  {missing_roots} ({100*missing_roots/max(total_words,1):.1f}%)")
    print(f"  Missing glosses:{missing_glosses} ({100*missing_glosses/max(total_words,1):.1f}%)")
    print(f"  Missing Rashi:  {missing_rashi} ({100*missing_rashi/max(total_verses,1):.1f}%)")
    print(f"  Missing Ramban: {missing_ramban} ({100*missing_ramban/max(total_verses,1):.1f}%)")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"  Cache:  {CACHE_DIR}/")
    print(f"{'=' * 60}")

    # Quick validation check
    if genesis['chapters']:
        ch1 = genesis['chapters'][0]
        if ch1['verses']:
            v1 = ch1['verses'][0]
            if v1['words']:
                w1 = v1['words'][0]
                print(f"\n  Validation - Genesis 1:1 word 1:")
                print(f"    heb: {w1['heb']}")
                print(f"    gem: {w1['gem']} (expected: 913)")
                print(f"    verse total: {v1['total_gematria']} (expected: 2701)")

    # Check for empty verses
    empty_verses = sum(
        1 for ch in genesis['chapters']
        for v in ch['verses']
        if len(v['words']) == 0
    )
    if empty_verses:
        print(f"\n  WARNING: {empty_verses} verses with 0 words!")


if __name__ == "__main__":
    main()
