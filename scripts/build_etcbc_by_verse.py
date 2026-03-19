#!/usr/bin/env python3
"""
Build ETCBC by-verse JSON for any book.
========================================
Parses Text-Fabric .tf files to map word slots to verses,
then groups per_book morpheme data by chapter:verse.

Usage:
  python build_etcbc_by_verse.py Exodus
  python build_etcbc_by_verse.py Leviticus
  python build_etcbc_by_verse.py          # all Torah books

Output: references/etcbc_{book}_by_verse.json
"""

import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')
REF = BASE / 'references'

BOOK_NAMES = [
    'Genesis', 'Exodus', 'Leviticus', 'Numeri', 'Deuteronomium',
    'Josua', 'Judices', 'Samuel_I', 'Samuel_II', 'Reges_I', 'Reges_II',
    'Jesaia', 'Jeremia', 'Ezechiel',
    'Hosea', 'Joel', 'Amos', 'Obadia', 'Jona', 'Micha',
    'Nahum', 'Habakuk', 'Zephania', 'Haggai', 'Sacharia', 'Maleachi',
    'Psalmi', 'Iob', 'Proverbia', 'Ruth', 'Canticum', 'Ecclesiastes',
    'Threni', 'Esther', 'Daniel', 'Esra', 'Nehemia',
    'Chronica_I', 'Chronica_II',
]

# Node ranges from otype.tf
BOOK_NODES = (426591, 426629)
CHAPTER_NODES = (426630, 427558)
VERSE_NODES = (1414389, 1437601)


def parse_tf_header(lines):
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('@'):
            return i
    return len(lines)


def parse_range(range_str):
    """Parse '1-28764' or '1,3,5-10' into sorted list of ints."""
    slots = []
    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-', 1)
            slots.extend(range(int(a), int(b) + 1))
        else:
            slots.append(int(part))
    return slots


def load_oslots_for_ranges(ranges_needed):
    """Read oslots.tf once, extract nodes for multiple (min, max) ranges.
    ranges_needed: dict of label -> (node_min, node_max)
    Returns: dict of label -> {node_id: [slots]}
    """
    lines = (REF / 'etcbc_oslots.tf').read_text(encoding='utf-8').splitlines()
    data_start = parse_tf_header(lines)

    # Find the global min/max we care about
    all_mins = [r[0] for r in ranges_needed.values()]
    all_maxs = [r[1] for r in ranges_needed.values()]
    global_max = max(all_maxs)

    results = {label: {} for label in ranges_needed}
    current_node = None

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        if '\t' in line:
            p = line.split('\t', 1)
            current_node = int(p[0])
            range_str = p[1]
        else:
            if current_node is not None:
                current_node += 1
            range_str = line

        if current_node is None:
            continue
        if current_node > global_max:
            break

        for label, (nmin, nmax) in ranges_needed.items():
            if nmin <= current_node <= nmax:
                results[label][current_node] = parse_range(range_str)

    return results


def load_tf_int(filepath):
    """Load a TF file with integer values. Returns dict node_id -> value."""
    lines = filepath.read_text(encoding='utf-8').splitlines()
    data_start = parse_tf_header(lines)
    result = {}
    current_node = None

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        if '\t' in line:
            parts = line.split('\t', 1)
            current_node = int(parts[0])
            result[current_node] = int(parts[1])
        else:
            if current_node is not None:
                current_node += 1
                result[current_node] = int(line)

    return result


def build_by_verse(book_name, oslots_data, chapter_nums, verse_nums):
    """Build by-verse dict for a given book."""
    if book_name not in BOOK_NAMES:
        print(f"ERROR: Unknown book '{book_name}'. Known: {BOOK_NAMES}")
        return None

    book_idx = BOOK_NAMES.index(book_name)
    book_node = 426591 + book_idx

    print(f"\nBuilding by-verse data for {book_name}...")

    # Load per-book morpheme data
    per_book_path = REF / 'per_book' / f'{book_name}.json'
    if not per_book_path.exists():
        print(f"  ERROR: {per_book_path} not found")
        return None

    with open(per_book_path, 'r', encoding='utf-8') as f:
        morphemes = json.load(f)
    print(f"  {len(morphemes)} morphemes from {per_book_path.name}")

    # Book slot range
    book_slots = oslots_data['books'].get(book_node)
    if not book_slots:
        print(f"  ERROR: Book node {book_node} not in oslots")
        return None

    slot_min, slot_max = min(book_slots), max(book_slots)
    expected = slot_max - slot_min + 1
    print(f"  Slots: {slot_min}-{slot_max} ({expected})")
    if expected != len(morphemes):
        print(f"  WARNING: slot count {expected} != morpheme count {len(morphemes)}")

    # Chapters for this book
    chapter_ranges = []
    for node in sorted(oslots_data['chapters']):
        slots = oslots_data['chapters'][node]
        if slots and slots[0] >= slot_min and slots[-1] <= slot_max:
            ch_num = chapter_nums.get(node, 0)
            chapter_ranges.append((ch_num, min(slots), max(slots)))

    print(f"  {len(chapter_ranges)} chapters")

    def find_chapter(first_slot):
        for ch_num, ch_start, ch_end in chapter_ranges:
            if ch_start <= first_slot <= ch_end:
                return ch_num
        return 0

    # Verses for this book
    result = {}
    for node in sorted(oslots_data['verses']):
        slots = oslots_data['verses'][node]
        if not slots or slots[0] < slot_min or slots[-1] > slot_max:
            continue

        v_num = verse_nums.get(node, 0)
        ch_num = find_chapter(slots[0])

        if ch_num == 0 or v_num == 0:
            continue

        ref = f"{ch_num}:{v_num}"
        verse_morphemes = []
        for s in slots:
            idx = s - slot_min
            if 0 <= idx < len(morphemes):
                verse_morphemes.append(morphemes[idx])

        result[ref] = verse_morphemes

    return result


def main():
    args = sys.argv[1:]

    if not args:
        books = ['Exodus', 'Leviticus', 'Numeri', 'Deuteronomium']
    else:
        books = args

    # Load all TF data once
    print("Loading oslots.tf (one pass for all ranges)...")
    oslots_data = load_oslots_for_ranges({
        'books': BOOK_NODES,
        'chapters': CHAPTER_NODES,
        'verses': VERSE_NODES,
    })
    print(f"  Books: {len(oslots_data['books'])}, Chapters: {len(oslots_data['chapters'])}, Verses: {len(oslots_data['verses'])}")

    print("Loading chapter/verse numbers...")
    chapter_nums = load_tf_int(REF / 'etcbc_chapter.tf')
    verse_nums = load_tf_int(REF / 'etcbc_verse.tf')

    name_map = {
        'Numeri': 'numbers',
        'Deuteronomium': 'deuteronomy',
    }

    for book_name in books:
        result = build_by_verse(book_name, oslots_data, chapter_nums, verse_nums)
        if result is None:
            continue

        out_name = name_map.get(book_name, book_name.lower())
        out_path = REF / f'etcbc_{out_name}_by_verse.json'

        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        total_morphemes = sum(len(v) for v in result.values())
        print(f"  Output: {out_path.name}")
        print(f"  {len(result)} verses, {total_morphemes} morphemes")

        # Spot check
        first_key = list(result.keys())[0]
        print(f"  Spot check {first_key}: {[w['gloss'] for w in result[first_key][:4]]}")


if __name__ == '__main__':
    main()
