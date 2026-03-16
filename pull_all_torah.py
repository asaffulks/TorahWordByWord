#!/usr/bin/env python3
"""
Pull all 5 books of Torah from Sefaria with all commentaries.
Reuses the sefaria_pipeline infrastructure.
Run: python pull_all_torah.py
"""

import json
import os
import re
import sys
import time
import html as htmlmod
import requests
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import shared functions from the Genesis pipeline
from sefaria_pipeline import (
    cached_get, calc_gematria, strip_nikud, transliterate_hebrew,
    lookup_word, clean_hebrew_text, get_rashi, get_commentary,
    CACHE_DIR, RATE_LIMIT
)

BOOKS = [
    {
        "english": "Exodus",
        "hebrew": "\u05E9\u05B0\u05C1\u05DE\u05D5\u05B9\u05EA",
        "sefaria_name": "Exodus",
        "he_ref": "Shemot",
        "chapters": 40,
        "output": "exodus.json",
    },
    {
        "english": "Leviticus",
        "hebrew": "\u05D5\u05B7\u05D9\u05BC\u05B4\u05E7\u05B0\u05E8\u05B8\u05D0",
        "sefaria_name": "Leviticus",
        "he_ref": "Vayikra",
        "chapters": 27,
        "output": "leviticus.json",
    },
    {
        "english": "Numbers",
        "hebrew": "\u05D1\u05B0\u05BC\u05DE\u05B4\u05D3\u05B0\u05D1\u05B7\u05BC\u05E8",
        "sefaria_name": "Numbers",
        "he_ref": "Bamidbar",
        "chapters": 36,
        "output": "numbers.json",
    },
    {
        "english": "Deuteronomy",
        "hebrew": "\u05D3\u05B0\u05BC\u05D1\u05B8\u05E8\u05B4\u05D9\u05DD",
        "sefaria_name": "Deuteronomy",
        "he_ref": "Devarim",
        "chapters": 34,
        "output": "deuteronomy.json",
    },
]

COMMENTARIES = ["Rashi", "Ramban", "Ibn_Ezra", "Sforno", "Or_HaChaim"]


def get_chapter_text(book_name, chapter):
    return cached_get(
        f"texts/{book_name}.{chapter}?context=0",
        f"text_{book_name.lower()}_{chapter}"
    )


def get_rashi_for_book(book_name, chapter, verse):
    data = cached_get(
        f"texts/Rashi_on_{book_name}.{chapter}.{verse}?lang=en&context=0",
        f"rashi_{book_name.lower()}_{chapter}_{verse}"
    )
    if not data:
        return ""
    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        parts = []
        for t in en:
            clean = re.sub(r'<[^>]+>', '', t).strip()
            clean = htmlmod.unescape(clean)
            if clean:
                parts.append(clean)
        text = ' '.join(parts)
    elif isinstance(en, str):
        text = re.sub(r'<[^>]+>', '', en)
        text = htmlmod.unescape(text)
    else:
        return ""
    text = text.strip()
    if len(text) > 3000:
        text = text[:2997] + "..."
    return text


def get_commentary_for_book(name, book_name, chapter, verse):
    data = cached_get(
        f"texts/{name}_on_{book_name}.{chapter}.{verse}?lang=en&context=0",
        f"{name.lower()}_on_{book_name.lower()}_{chapter}_{verse}"
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
    text = htmlmod.unescape(text).strip()
    if len(text) > 3000:
        text = text[:2997] + "..."
    return text


def process_verse_generic(book_name, he_ref, chapter, verse, he_text, en_text):
    ref = f"{he_ref} {chapter}:{verse}"

    he_clean = clean_hebrew_text(he_text)
    he_words = he_clean.split()

    # Commentaries
    rashi = get_rashi_for_book(book_name, chapter, verse)
    ramban = get_commentary_for_book("Ramban", book_name, chapter, verse)
    ibn_ezra = get_commentary_for_book("Ibn_Ezra", book_name, chapter, verse)
    sforno = get_commentary_for_book("Sforno", book_name, chapter, verse)
    or_hachaim = get_commentary_for_book("Or_HaChaim", book_name, chapter, verse)

    words = []
    for heb_word in he_words:
        gem_word = heb_word.replace('\u05BE', '')
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

    # Clean translation
    en_clean = ""
    if en_text:
        t = str(en_text)
        t = re.sub(r'<sup[^>]*>.*?</sup>', '', t)
        t = re.sub(r'<i class="footnote">.*?</i>', '', t)
        t = re.sub(r'<[^>]+>', '', t)
        en_clean = htmlmod.unescape(t).strip()
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


def pull_book(book_info):
    book_name = book_info["sefaria_name"]
    he_ref = book_info["he_ref"]
    total_chapters = book_info["chapters"]
    output_file = book_info["output"]

    print(f"\n{'='*60}")
    print(f"  Pulling {book_info['english']} ({book_info['hebrew']})")
    print(f"  {total_chapters} chapters")
    print(f"{'='*60}")

    data = {
        "book": book_info["english"],
        "he_name": book_info["hebrew"],
        "chapters": []
    }

    total_verses = 0
    total_words = 0

    for ch in range(1, total_chapters + 1):
        print(f"\n  Chapter {ch}...")
        ch_data = get_chapter_text(book_name, ch)

        if not ch_data:
            print(f"    WARNING: Could not fetch chapter {ch}")
            continue

        he_texts = ch_data.get("he", [])
        en_texts = ch_data.get("text", [])

        if not he_texts:
            print(f"    WARNING: No Hebrew text for chapter {ch}")
            continue

        if not isinstance(en_texts, list):
            en_texts = []
        while len(en_texts) < len(he_texts):
            en_texts.append("")

        chapter_obj = {"chapter": ch, "verses": []}

        for v_idx, he_text in enumerate(he_texts):
            verse_num = v_idx + 1
            if not he_text:
                continue

            verse_data = process_verse_generic(
                book_name, he_ref, ch, verse_num,
                he_text, en_texts[v_idx]
            )
            chapter_obj["verses"].append(verse_data)
            total_verses += 1
            total_words += len(verse_data["words"])

            if verse_num % 10 == 0:
                print(f"    {verse_num} verses processed")

        data["chapters"].append(chapter_obj)
        print(f"    Chapter {ch} complete: {len(chapter_obj['verses'])} verses")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  DONE: {book_info['english']}")
    print(f"  {total_chapters} chapters, {total_verses} verses, {total_words} words")
    print(f"  Output: {output_file}")

    return output_file


def main():
    print("Torah: Word by Word — Full Torah Pipeline")
    print("Pulling Exodus, Leviticus, Numbers, Deuteronomy")
    print("(Genesis already complete)")
    print()

    for book in BOOKS:
        output = book["output"]
        if os.path.exists(output):
            # Check if it looks complete
            with open(output, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if len(existing.get("chapters", [])) == book["chapters"]:
                print(f"  {book['english']} already complete ({output}), skipping")
                continue

        pull_book(book)

    print("\n" + "="*60)
    print("  ALL BOOKS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
