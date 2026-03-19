#!/usr/bin/env python3
"""
Pre-Print Audit — Torah Books
===============================
Checks all word-level data for quality issues before PDF generation.

Usage:
  python audit_torah_books.py exodus
  python audit_torah_books.py all
"""

import json, re, sys
from collections import Counter
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

BOOK_FILES = {
    'exodus': BASE / 'books' / 'torah' / 'exodus_fixed.json',
    'leviticus': BASE / 'books' / 'torah' / 'leviticus_fixed.json',
    'numbers': BASE / 'books' / 'torah' / 'numbers_fixed.json',
    'deuteronomy': BASE / 'books' / 'torah' / 'deuteronomy_fixed.json',
}

JARGON = {'adj', 'adv', 'subst', 'n m', 'n f', 'n m/f', 'vb', 'v',
          'prep', 'conj', 'pron', 'interj', 'n pr m', 'n pr', 'n pr f',
          'n pr loc', 'pron 3p s', 'nm', 'nf'}


def audit_book(book_key):
    filepath = BOOK_FILES[book_key]
    if not filepath.exists():
        print(f"ERROR: {filepath} not found")
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    issues = {
        'empty_eng': [],
        'jargon': [],
        'html': [],
        'dict_def': [],
        'too_long': [],
        'missing_heb': [],
        'no_commentary': [],
    }

    total_words = 0
    total_verses = 0
    total_with_commentary = 0
    word_lengths = []

    commentary_fields = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
                         'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar']

    for ch in data['chapters']:
        for v in ch['verses']:
            total_verses += 1
            ref = f"{ch['chapter']}:{v['verse']}"

            has_commentary = any(v.get(f, '').strip() for f in commentary_fields)
            if has_commentary:
                total_with_commentary += 1
            else:
                issues['no_commentary'].append(ref)

            for i, w in enumerate(v.get('words', [])):
                total_words += 1
                eng = w.get('eng', '')
                heb = w.get('heb', '')

                if not eng or not eng.strip():
                    issues['empty_eng'].append(f"{ref}[{i}] {heb}")
                elif eng.lower() in JARGON:
                    issues['jargon'].append(f"{ref}[{i}] {heb} -> '{eng}'")
                elif '<' in eng or 'href' in eng:
                    issues['html'].append(f"{ref}[{i}] {heb} -> '{eng[:60]}'")
                elif '="' in eng and 'meaning' not in eng:
                    issues['dict_def'].append(f"{ref}[{i}] {heb} -> '{eng[:60]}'")
                elif len(eng) > 40:
                    issues['too_long'].append(f"{ref}[{i}] {heb} -> '{eng[:60]}'")

                if not heb:
                    issues['missing_heb'].append(f"{ref}[{i}]")

                word_lengths.append(len(eng))

    return {
        'book': book_key.title(),
        'total_words': total_words,
        'total_verses': total_verses,
        'with_commentary': total_with_commentary,
        'issues': issues,
        'avg_eng_len': sum(word_lengths) / len(word_lengths) if word_lengths else 0,
    }


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or 'all' in args:
        books = list(BOOK_FILES.keys())
    else:
        books = [a for a in args if a in BOOK_FILES]

    all_results = []
    for book_key in books:
        result = audit_book(book_key)
        if not result:
            continue
        all_results.append(result)

        print(f"\n{'=' * 60}")
        print(f"  AUDIT: {result['book']}")
        print(f"{'=' * 60}")
        print(f"  Words: {result['total_words']}")
        print(f"  Verses: {result['total_verses']}")
        print(f"  With commentary: {result['with_commentary']}/{result['total_verses']} "
              f"({100*result['with_commentary']/result['total_verses']:.0f}%)")
        print(f"  Avg eng length: {result['avg_eng_len']:.1f} chars")

        total_issues = sum(len(v) for v in result['issues'].values())
        print(f"\n  Issues: {total_issues}")
        for issue_type, items in result['issues'].items():
            if items:
                label = issue_type.replace('_', ' ')
                print(f"    {label}: {len(items)}")
                for item in items[:5]:
                    print(f"      {item}")
                if len(items) > 5:
                    print(f"      ... and {len(items) - 5} more")

    if len(all_results) > 1:
        print(f"\n{'=' * 60}")
        print(f"  SUMMARY")
        print(f"{'=' * 60}")
        for r in all_results:
            total_issues = sum(len(v) for k, v in r['issues'].items() if k != 'no_commentary')
            print(f"  {r['book']:15s}  {r['total_words']:6d} words  "
                  f"{total_issues:3d} data issues  "
                  f"{r['with_commentary']}/{r['total_verses']} with commentary")


if __name__ == '__main__':
    main()
