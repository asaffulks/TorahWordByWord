#!/usr/bin/env python3
"""
Pull the FULL Tanach from Sefaria — Torah, Nevi'im, Ketuvim.
Runs after pull_all_torah.py completes.
Skips any book that already has a complete JSON file.

Run: python pull_full_tanach.py
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

from sefaria_pipeline import (
    cached_get, calc_gematria, strip_nikud, transliterate_hebrew,
    lookup_word, clean_hebrew_text, CACHE_DIR
)

# ─── All books of the Tanach ────────────────────────────────────────────────

TANACH = {
    "Torah": [
        # Already done
        {"english": "Genesis", "hebrew": "\u05D1\u05B0\u05BC\u05E8\u05B5\u05D0\u05E9\u05C1\u05B4\u05D9\u05EA", "sefaria": "Genesis", "he_ref": "Bereshit", "chapters": 50, "output": "genesis.json"},
        {"english": "Exodus", "hebrew": "\u05E9\u05B0\u05C1\u05DE\u05D5\u05B9\u05EA", "sefaria": "Exodus", "he_ref": "Shemot", "chapters": 40, "output": "exodus.json"},
        {"english": "Leviticus", "hebrew": "\u05D5\u05B7\u05D9\u05BC\u05B4\u05E7\u05B0\u05E8\u05B8\u05D0", "sefaria": "Leviticus", "he_ref": "Vayikra", "chapters": 27, "output": "leviticus.json"},
        {"english": "Numbers", "hebrew": "\u05D1\u05B0\u05BC\u05DE\u05B4\u05D3\u05B0\u05D1\u05B7\u05BC\u05E8", "sefaria": "Numbers", "he_ref": "Bamidbar", "chapters": 36, "output": "numbers.json"},
        {"english": "Deuteronomy", "hebrew": "\u05D3\u05B0\u05BC\u05D1\u05B8\u05E8\u05B4\u05D9\u05DD", "sefaria": "Deuteronomy", "he_ref": "Devarim", "chapters": 34, "output": "deuteronomy.json"},
    ],
    "Neviim": [
        {"english": "Joshua", "hebrew": "\u05D9\u05B0\u05D4\u05D5\u05B9\u05E9\u05C1\u05BB\u05E2\u05B7", "sefaria": "Joshua", "he_ref": "Yehoshua", "chapters": 24, "output": "joshua.json"},
        {"english": "Judges", "hebrew": "\u05E9\u05C1\u05D5\u05B9\u05E4\u05B0\u05D8\u05B4\u05D9\u05DD", "sefaria": "Judges", "he_ref": "Shoftim", "chapters": 21, "output": "judges.json"},
        {"english": "I Samuel", "hebrew": "\u05E9\u05C1\u05B0\u05DE\u05D5\u05BC\u05D0\u05B5\u05DC \u05D0", "sefaria": "I_Samuel", "he_ref": "Shmuel Aleph", "chapters": 31, "output": "i_samuel.json"},
        {"english": "II Samuel", "hebrew": "\u05E9\u05C1\u05B0\u05DE\u05D5\u05BC\u05D0\u05B5\u05DC \u05D1", "sefaria": "II_Samuel", "he_ref": "Shmuel Bet", "chapters": 24, "output": "ii_samuel.json"},
        {"english": "I Kings", "hebrew": "\u05DE\u05B0\u05DC\u05B8\u05DB\u05B4\u05D9\u05DD \u05D0", "sefaria": "I_Kings", "he_ref": "Melakhim Aleph", "chapters": 22, "output": "i_kings.json"},
        {"english": "II Kings", "hebrew": "\u05DE\u05B0\u05DC\u05B8\u05DB\u05B4\u05D9\u05DD \u05D1", "sefaria": "II_Kings", "he_ref": "Melakhim Bet", "chapters": 25, "output": "ii_kings.json"},
        {"english": "Isaiah", "hebrew": "\u05D9\u05B0\u05E9\u05C1\u05B7\u05E2\u05B0\u05D9\u05B8\u05D4\u05D5\u05BC", "sefaria": "Isaiah", "he_ref": "Yeshayahu", "chapters": 66, "output": "isaiah.json"},
        {"english": "Jeremiah", "hebrew": "\u05D9\u05B4\u05E8\u05B0\u05DE\u05B0\u05D9\u05B8\u05D4\u05D5\u05BC", "sefaria": "Jeremiah", "he_ref": "Yirmiyahu", "chapters": 52, "output": "jeremiah.json"},
        {"english": "Ezekiel", "hebrew": "\u05D9\u05B0\u05D7\u05B6\u05D6\u05B0\u05E7\u05B5\u05D0\u05DC", "sefaria": "Ezekiel", "he_ref": "Yechezkel", "chapters": 48, "output": "ezekiel.json"},
        {"english": "Hosea", "hebrew": "\u05D4\u05D5\u05B9\u05E9\u05C1\u05B5\u05E2\u05B7", "sefaria": "Hosea", "he_ref": "Hoshea", "chapters": 14, "output": "hosea.json"},
        {"english": "Joel", "hebrew": "\u05D9\u05D5\u05B9\u05D0\u05B5\u05DC", "sefaria": "Joel", "he_ref": "Yoel", "chapters": 4, "output": "joel.json"},
        {"english": "Amos", "hebrew": "\u05E2\u05B8\u05DE\u05D5\u05B9\u05E1", "sefaria": "Amos", "he_ref": "Amos", "chapters": 9, "output": "amos.json"},
        {"english": "Obadiah", "hebrew": "\u05E2\u05D5\u05B9\u05D1\u05B7\u05D3\u05B0\u05D9\u05B8\u05D4", "sefaria": "Obadiah", "he_ref": "Ovadyah", "chapters": 1, "output": "obadiah.json"},
        {"english": "Jonah", "hebrew": "\u05D9\u05D5\u05B9\u05E0\u05B8\u05D4", "sefaria": "Jonah", "he_ref": "Yonah", "chapters": 4, "output": "jonah.json"},
        {"english": "Micah", "hebrew": "\u05DE\u05B4\u05D9\u05DB\u05B8\u05D4", "sefaria": "Micah", "he_ref": "Mikhah", "chapters": 7, "output": "micah.json"},
        {"english": "Nahum", "hebrew": "\u05E0\u05B7\u05D7\u05D5\u05BC\u05DD", "sefaria": "Nahum", "he_ref": "Nachum", "chapters": 3, "output": "nahum.json"},
        {"english": "Habakkuk", "hebrew": "\u05D7\u05B2\u05D1\u05B7\u05E7\u05BC\u05D5\u05BC\u05E7", "sefaria": "Habakkuk", "he_ref": "Chavakuk", "chapters": 3, "output": "habakkuk.json"},
        {"english": "Zephaniah", "hebrew": "\u05E6\u05B0\u05E4\u05B7\u05E0\u05B0\u05D9\u05B8\u05D4", "sefaria": "Zephaniah", "he_ref": "Tzefanyah", "chapters": 3, "output": "zephaniah.json"},
        {"english": "Haggai", "hebrew": "\u05D7\u05B7\u05D2\u05B7\u05BC\u05D9", "sefaria": "Haggai", "he_ref": "Chaggai", "chapters": 2, "output": "haggai.json"},
        {"english": "Zechariah", "hebrew": "\u05D6\u05B0\u05DB\u05B7\u05E8\u05B0\u05D9\u05B8\u05D4", "sefaria": "Zechariah", "he_ref": "Zekharyah", "chapters": 14, "output": "zechariah.json"},
        {"english": "Malachi", "hebrew": "\u05DE\u05B7\u05DC\u05B0\u05D0\u05B8\u05DB\u05B4\u05D9", "sefaria": "Malachi", "he_ref": "Malakhi", "chapters": 3, "output": "malachi.json"},
    ],
    "Ketuvim": [
        {"english": "Psalms", "hebrew": "\u05EA\u05B0\u05BC\u05D4\u05B4\u05DC\u05B4\u05BC\u05D9\u05DD", "sefaria": "Psalms", "he_ref": "Tehillim", "chapters": 150, "output": "psalms.json"},
        {"english": "Proverbs", "hebrew": "\u05DE\u05B4\u05E9\u05C1\u05B0\u05DC\u05B5\u05D9", "sefaria": "Proverbs", "he_ref": "Mishlei", "chapters": 31, "output": "proverbs.json"},
        {"english": "Job", "hebrew": "\u05D0\u05B4\u05D9\u05BC\u05D5\u05B9\u05D1", "sefaria": "Job", "he_ref": "Iyov", "chapters": 42, "output": "job.json"},
        {"english": "Song of Songs", "hebrew": "\u05E9\u05C1\u05B4\u05D9\u05E8 \u05D4\u05B7\u05E9\u05C1\u05B4\u05BC\u05D9\u05E8\u05B4\u05D9\u05DD", "sefaria": "Song_of_Songs", "he_ref": "Shir HaShirim", "chapters": 8, "output": "song_of_songs.json"},
        {"english": "Ruth", "hebrew": "\u05E8\u05D5\u05BC\u05EA", "sefaria": "Ruth", "he_ref": "Rut", "chapters": 4, "output": "ruth.json"},
        {"english": "Lamentations", "hebrew": "\u05D0\u05B5\u05D9\u05DB\u05B8\u05D4", "sefaria": "Lamentations", "he_ref": "Eikhah", "chapters": 5, "output": "lamentations.json"},
        {"english": "Ecclesiastes", "hebrew": "\u05E7\u05B9\u05D4\u05B6\u05DC\u05B6\u05EA", "sefaria": "Ecclesiastes", "he_ref": "Kohelet", "chapters": 12, "output": "ecclesiastes.json"},
        {"english": "Esther", "hebrew": "\u05D0\u05B6\u05E1\u05B0\u05EA\u05B5\u05BC\u05E8", "sefaria": "Esther", "he_ref": "Ester", "chapters": 10, "output": "esther.json"},
        {"english": "Daniel", "hebrew": "\u05D3\u05B8\u05BC\u05E0\u05B4\u05D9\u05BC\u05B5\u05D0\u05DC", "sefaria": "Daniel", "he_ref": "Daniel", "chapters": 12, "output": "daniel.json"},
        {"english": "Ezra", "hebrew": "\u05E2\u05B6\u05D6\u05B0\u05E8\u05B8\u05D0", "sefaria": "Ezra", "he_ref": "Ezra", "chapters": 10, "output": "ezra.json"},
        {"english": "Nehemiah", "hebrew": "\u05E0\u05B0\u05D7\u05B6\u05DE\u05B0\u05D9\u05B8\u05D4", "sefaria": "Nehemiah", "he_ref": "Nechemyah", "chapters": 13, "output": "nehemiah.json"},
        {"english": "I Chronicles", "hebrew": "\u05D3\u05B4\u05BC\u05D1\u05B0\u05E8\u05B5\u05D9 \u05D4\u05B7\u05D9\u05BC\u05B8\u05DE\u05B4\u05D9\u05DD \u05D0", "sefaria": "I_Chronicles", "he_ref": "Divrei HaYamim Aleph", "chapters": 29, "output": "i_chronicles.json"},
        {"english": "II Chronicles", "hebrew": "\u05D3\u05B4\u05BC\u05D1\u05B0\u05E8\u05B5\u05D9 \u05D4\u05B7\u05D9\u05BC\u05B8\u05DE\u05B4\u05D9\u05DD \u05D1", "sefaria": "II_Chronicles", "he_ref": "Divrei HaYamim Bet", "chapters": 36, "output": "ii_chronicles.json"},
    ],
}


def get_chapter_text(book_sefaria, chapter):
    return cached_get(
        f"texts/{book_sefaria}.{chapter}?context=0",
        f"text_{book_sefaria.lower()}_{chapter}"
    )


def get_rashi_generic(book_sefaria, chapter, verse):
    data = cached_get(
        f"texts/Rashi_on_{book_sefaria}.{chapter}.{verse}?lang=en&context=0",
        f"rashi_{book_sefaria.lower()}_{chapter}_{verse}"
    )
    if not data:
        return ""
    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        parts = [htmlmod.unescape(re.sub(r'<[^>]+>', '', t)).strip() for t in en]
        text = ' '.join(p for p in parts if p)
    elif isinstance(en, str):
        text = htmlmod.unescape(re.sub(r'<[^>]+>', '', en))
    else:
        return ""
    text = text.strip()
    return text[:2997] + "..." if len(text) > 3000 else text


def get_commentary_generic(name, book_sefaria, chapter, verse):
    data = cached_get(
        f"texts/{name}_on_{book_sefaria}.{chapter}.{verse}?lang=en&context=0",
        f"{name.lower()}_on_{book_sefaria.lower()}_{chapter}_{verse}"
    )
    if not data:
        return ""
    en = data.get("text", [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        text = htmlmod.unescape(re.sub(r'<[^>]+>', '', ' '.join(en)))
    elif isinstance(en, str):
        text = htmlmod.unescape(re.sub(r'<[^>]+>', '', en))
    else:
        return ""
    text = text.strip()
    return text[:2997] + "..." if len(text) > 3000 else text


def pull_book(book_info):
    book_sefaria = book_info["sefaria"]
    he_ref = book_info["he_ref"]
    total_chapters = book_info["chapters"]
    output_file = book_info["output"]

    # Skip if already complete
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if len(existing.get("chapters", [])) == total_chapters:
                print(f"  {book_info['english']} already complete, skipping")
                return
        except:
            pass

    print(f"\n{'='*60}")
    print(f"  {book_info['english']} ({book_info['hebrew']})")
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
        print(f"  Chapter {ch}...")
        ch_data = get_chapter_text(book_sefaria, ch)

        if not ch_data:
            print(f"    WARNING: Could not fetch chapter {ch}")
            continue

        he_texts = ch_data.get("he", [])
        en_texts = ch_data.get("text", [])

        if not he_texts:
            print(f"    WARNING: No Hebrew text")
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

            ref = f"{he_ref} {ch}:{verse_num}"
            he_clean = clean_hebrew_text(he_text)
            he_words = he_clean.split()

            # Commentaries
            rashi = get_rashi_generic(book_sefaria, ch, verse_num)
            ramban = get_commentary_generic("Ramban", book_sefaria, ch, verse_num)
            ibn_ezra = get_commentary_generic("Ibn_Ezra", book_sefaria, ch, verse_num)
            sforno = get_commentary_generic("Sforno", book_sefaria, ch, verse_num)
            or_hachaim = get_commentary_generic("Or_HaChaim", book_sefaria, ch, verse_num)

            # Words
            words = []
            for heb_word in he_words:
                gem_word = heb_word.replace('\u05BE', '')
                gem = calc_gematria(gem_word)
                tr = transliterate_hebrew(heb_word)
                root, eng = lookup_word(heb_word)
                words.append({"heb": heb_word, "tr": tr, "root": root, "eng": eng, "gem": gem})

            # Translation
            en_clean = ""
            if en_texts[v_idx]:
                t = str(en_texts[v_idx])
                t = re.sub(r'<sup[^>]*>.*?</sup>', '', t)
                t = re.sub(r'<i class="footnote">.*?</i>', '', t)
                t = re.sub(r'<[^>]+>', '', t)
                en_clean = htmlmod.unescape(t).strip()
                en_clean = re.sub(r'\s+', ' ', en_clean)

            total_gem = sum(w["gem"] for w in words)

            chapter_obj["verses"].append({
                "verse": verse_num,
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
            })
            total_verses += 1
            total_words += len(words)

            if verse_num % 10 == 0:
                print(f"    {verse_num} verses")

        data["chapters"].append(chapter_obj)
        print(f"    Chapter {ch}: {len(chapter_obj['verses'])} verses")

        # Save after each chapter (resume-safe)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  DONE: {book_info['english']} — {total_verses} verses, {total_words} words")


def main():
    print("="*60)
    print("  Tanach: Word by Word — Full Tanach Pipeline")
    print("="*60)

    for section_name, books in TANACH.items():
        print(f"\n--- {section_name} ---")
        for book in books:
            pull_book(book)

    print("\n" + "="*60)
    print("  FULL TANACH COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
