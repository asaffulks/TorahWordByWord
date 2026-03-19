#!/usr/bin/env python3
"""Pull cross-references for Genesis verses from Sefaria links API."""
import json, os, re, sys, time, requests, html as htmlmod
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CACHE_DIR = Path("sefaria_cache")
CACHE_DIR.mkdir(exist_ok=True)

def cached_get_links(ref, cache_key):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            cache_file.unlink()

    url = f"https://www.sefaria.org/api/links/{ref}?with_text=0"
    time.sleep(0.3)
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            data = []
        else:
            resp.raise_for_status()
            data = resp.json()
    except:
        return []

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def get_cross_refs(book_sefaria, chapter, verse):
    """Get cross-references for a verse, return formatted string."""
    ref = f"{book_sefaria}.{chapter}.{verse}"
    links = cached_get_links(ref, f"links_{book_sefaria.lower()}_{chapter}_{verse}")

    if not isinstance(links, list):
        return ""

    # Filter for Tanach cross-references only (not Talmud, Midrash, etc.)
    tanach_cats = {'Torah', 'Prophets', 'Writings', 'Tanakh'}
    refs = []
    seen = set()
    for link in links:
        if not isinstance(link, dict):
            continue
        cat = link.get('category', '')
        ref_text = link.get('ref', '')
        # Only include Tanach references
        if cat in tanach_cats or link.get('collectiveTitle', {}).get('en', '') in tanach_cats:
            if ref_text and ref_text not in seen:
                refs.append(ref_text)
                seen.add(ref_text)
        # Also include if it's a Torah/Nevi'im/Ketuvim reference by checking the ref format
        elif ref_text and any(ref_text.startswith(b) for b in [
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
            'Joshua', 'Judges', 'I Samuel', 'II Samuel', 'I Kings', 'II Kings',
            'Isaiah', 'Jeremiah', 'Ezekiel', 'Hosea', 'Joel', 'Amos',
            'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
            'Haggai', 'Zechariah', 'Malachi', 'Psalms', 'Proverbs', 'Job',
            'Song of Songs', 'Ruth', 'Lamentations', 'Ecclesiastes', 'Esther',
            'Daniel', 'Ezra', 'Nehemiah', 'I Chronicles', 'II Chronicles',
        ]):
            if ref_text not in seen:
                refs.append(ref_text)
                seen.add(ref_text)

    if not refs:
        return ""

    # Limit to 8 most relevant
    return "; ".join(refs[:8])


def main():
    with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
        d = json.load(f)

    added = 0
    total = 0
    for c in d['chapters']:
        ch = c['chapter']
        print(f"  Chapter {ch}...")
        for v in c['verses']:
            total += 1
            refs = get_cross_refs("Genesis", ch, v['verse'])
            v['cross_refs'] = refs
            if refs:
                added += 1

    with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {added}/{total} verses have cross-references")


if __name__ == "__main__":
    main()
