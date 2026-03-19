#!/usr/bin/env python3
"""
Pull missing commentaries from Sefaria API for Torah books.
=============================================================
Pulls Chizkuni, Rabbeinu Bahya, Onkelos, Kli Yakar for
Exodus, Leviticus, Numbers, Deuteronomy.

Usage:
  python pull_commentary_torah.py              # all missing
  python pull_commentary_torah.py exodus       # one book
  python pull_commentary_torah.py exodus chizkuni  # one book, one commentary

Caches to sefaria_cache/ and adds to {book}_fixed.json.
"""

import json, os, re, sys, time, html as htmlmod
import urllib.request
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

CACHE = Path('K:/TorahByWord/sefaria_cache')
BOOKS_DIR = Path('K:/TorahByWord/books/torah')

# Sefaria API paths for each commentary × book
# Format: (cache_prefix, api_path_template, display_name)
# api_path_template uses {book} placeholder
COMMENTARIES = {
    'chizkuni': {
        'display': 'Chizkuni',
        'api_paths': {
            'exodus': 'Chizkuni,_Exodus',
            'leviticus': 'Chizkuni,_Leviticus',
            'numbers': 'Chizkuni,_Numbers',
            'deuteronomy': 'Chizkuni,_Deuteronomy',
        },
    },
    'rabbeinu_bahya': {
        'display': 'Rabbeinu Bahya',
        'api_paths': {
            'exodus': 'Rabbeinu_Bahya,_Shemot',
            'leviticus': 'Rabbeinu_Bahya,_Vayikra',
            'numbers': 'Rabbeinu_Bahya,_Bamidbar',
            'deuteronomy': 'Rabbeinu_Bahya,_Devarim',
        },
    },
    'onkelos': {
        'display': 'Onkelos',
        'api_paths': {
            'exodus': 'Onkelos_Exodus',
            'leviticus': 'Onkelos_Leviticus',
            'numbers': 'Onkelos_Numbers',
            'deuteronomy': 'Onkelos_Deuteronomy',
        },
    },
    'kli_yakar': {
        'display': 'Kli Yakar',
        'api_paths': {
            'exodus': 'Kli_Yakar_on_Exodus',
            'leviticus': 'Kli_Yakar_on_Leviticus',
            'numbers': 'Kli_Yakar_on_Numbers',
            'deuteronomy': 'Kli_Yakar_on_Deuteronomy',
        },
    },
}

BOOK_FILES = {
    'exodus': BOOKS_DIR / 'exodus_fixed.json',
    'leviticus': BOOKS_DIR / 'leviticus_fixed.json',
    'numbers': BOOKS_DIR / 'numbers_fixed.json',
    'deuteronomy': BOOKS_DIR / 'deuteronomy_fixed.json',
}


def cached_get(url, cache_key):
    cache_file = CACHE / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f), False
        except:
            pass

    time.sleep(0.4)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        data = {}

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data, True


def extract_text(data):
    en = data.get('text', [])
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
        return ' '.join(parts)
    elif isinstance(en, str):
        return htmlmod.unescape(re.sub(r'<[^>]+>', '', en)).strip()
    return ""


def pull_commentary(book_key, commentary_key):
    """Pull one commentary for one book."""
    cfg = COMMENTARIES[commentary_key]
    api_path = cfg['api_paths'].get(book_key)
    if not api_path:
        print(f"  No API path for {commentary_key} on {book_key}")
        return 0

    book_file = BOOK_FILES[book_key]
    with open(book_file, 'r', encoding='utf-8') as f:
        book_data = json.load(f)

    display = cfg['display']
    pulled = 0
    cached = 0
    has_content = 0

    for ch in book_data['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            cache_key = f"{commentary_key}_{book_key}_{ch_num}_{v_num}"

            url = f"https://www.sefaria.org/api/texts/{api_path}.{ch_num}.{v_num}?lang=en&context=0"
            data, was_pulled = cached_get(url, cache_key)

            text = extract_text(data)
            if was_pulled:
                pulled += 1
            else:
                cached += 1

            if text:
                has_content += 1

            # Add to verse data
            v[commentary_key] = text

            if pulled > 0 and pulled % 100 == 0:
                print(f"    {display} {book_key}: ch {ch_num}:{v_num} — {pulled} pulled, {has_content} with content")

    # Save updated book data
    with open(book_file, 'w', encoding='utf-8') as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)

    print(f"    {display} on {book_key.title()}: {pulled} new + {cached} cached, {has_content} with content")
    return has_content


def main():
    args = [a.lower() for a in sys.argv[1:]]

    # Determine which books and commentaries to pull
    books_to_pull = []
    commentaries_to_pull = []

    for a in args:
        if a in BOOK_FILES:
            books_to_pull.append(a)
        elif a in COMMENTARIES:
            commentaries_to_pull.append(a)

    if not books_to_pull:
        books_to_pull = list(BOOK_FILES.keys())
    if not commentaries_to_pull:
        commentaries_to_pull = list(COMMENTARIES.keys())

    total_content = 0
    print(f"Pulling {len(commentaries_to_pull)} commentaries for {len(books_to_pull)} books...")
    print(f"  Books: {', '.join(b.title() for b in books_to_pull)}")
    print(f"  Commentaries: {', '.join(COMMENTARIES[c]['display'] for c in commentaries_to_pull)}")
    print()

    for book_key in books_to_pull:
        print(f"\n{'=' * 50}")
        print(f"  {book_key.title()}")
        print(f"{'=' * 50}")
        for commentary_key in commentaries_to_pull:
            content_count = pull_commentary(book_key, commentary_key)
            total_content += content_count

    print(f"\n{'=' * 50}")
    print(f"  DONE — {total_content} total commentary entries with content")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    main()
