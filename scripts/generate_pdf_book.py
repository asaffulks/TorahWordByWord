#!/usr/bin/env python3
"""
PDF Generator Wrapper — Any Torah Book
========================================
Patches generate_pdf_multi.py to work with any Torah book by
replacing the hardcoded Genesis references.

Usage:
  python generate_pdf_book.py exodus
  python generate_pdf_book.py leviticus
  python generate_pdf_book.py all

Reads: books/torah/{book}_fixed.json + parasha_{book}.json
Output: {book}_pdf_v1.pdf
"""

import json, sys, os, importlib.util
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')
SCRIPTS = BASE / 'scripts'

# Hebrew book names with niqqud
BOOK_CONFIG = {
    'exodus': {
        'english': 'Exodus',
        'hebrew': '\u05E9\u05C1\u05B0\u05DE\u05D5\u05B9\u05EA',  # שְׁמוֹת
        'input': BASE / 'books' / 'torah' / 'exodus_fixed.json',
        'parasha': BASE / 'books' / 'torah' / 'parasha_exodus.json',
        'output': BASE / 'exodus_pdf_v1.pdf',
        'description': 'A complete word-by-word interlinear edition of the Book of Exodus, ',
    },
    'leviticus': {
        'english': 'Leviticus',
        'hebrew': '\u05D5\u05B7\u05D9\u05B4\u05BC\u05E7\u05B0\u05E8\u05B8\u05D0',  # וַיִּקְרָא
        'input': BASE / 'books' / 'torah' / 'leviticus_fixed.json',
        'parasha': BASE / 'books' / 'torah' / 'parasha_leviticus.json',
        'output': BASE / 'leviticus_pdf_v1.pdf',
        'description': 'A complete word-by-word interlinear edition of the Book of Leviticus, ',
    },
    'numbers': {
        'english': 'Numbers',
        'hebrew': '\u05D1\u05B0\u05BC\u05DE\u05B4\u05D3\u05B0\u05D1\u05B7\u05BC\u05E8',  # בְּמִדְבַּר
        'input': BASE / 'books' / 'torah' / 'numbers_fixed.json',
        'parasha': BASE / 'books' / 'torah' / 'parasha_numbers.json',
        'output': BASE / 'numbers_pdf_v1.pdf',
        'description': 'A complete word-by-word interlinear edition of the Book of Numbers, ',
    },
    'deuteronomy': {
        'english': 'Deuteronomy',
        'hebrew': '\u05D3\u05B0\u05BC\u05D1\u05B8\u05E8\u05B4\u05D9\u05DD',  # דְּבָרִים
        'input': BASE / 'books' / 'torah' / 'deuteronomy_fixed.json',
        'parasha': BASE / 'books' / 'torah' / 'parasha_deuteronomy.json',
        'output': BASE / 'deuteronomy_pdf_v1.pdf',
        'description': 'A complete word-by-word interlinear edition of the Book of Deuteronomy, ',
    },
}


def load_parasha_list(parasha_file, book_english):
    """Convert parasha JSON into the format expected by generate_pdf_multi.py."""
    with open(parasha_file, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    # Handle both list and dict-with-parashot-key formats
    if isinstance(raw, dict) and 'parashot' in raw:
        items = raw['parashot']
    elif isinstance(raw, list):
        items = raw
    else:
        items = raw

    parashot = []
    for p in items:
        parashot.append({
            "name": p['name'],
            "he": p.get('he', p['name']),  # Hebrew name if available, else transliteration
            "start": (p['start_chapter'], p['start_verse']),
            "end": (p['end_chapter'], p['end_verse']),
        })

    return parashot


def generate_book_pdf(book_key):
    """Generate PDF for one Torah book."""
    cfg = BOOK_CONFIG[book_key]
    english = cfg['english']
    print(f"\n{'=' * 60}")
    print(f"  Generating PDF: {english}")
    print(f"{'=' * 60}")

    if not cfg['input'].exists():
        print(f"ERROR: {cfg['input']} not found")
        return

    # Load the generator module
    spec = importlib.util.spec_from_file_location("gen_pdf", str(SCRIPTS / 'generate_pdf_multi.py'))
    gen = importlib.util.module_from_spec(spec)

    # Patch sys.argv before loading (to avoid it trying to parse args)
    old_argv = sys.argv
    sys.argv = ['generate_pdf_multi.py', str(cfg['input']), str(cfg['output'])]

    try:
        spec.loader.exec_module(gen)
    except SystemExit:
        pass

    # Patch the module's PARASHOT with book-specific data
    if cfg['parasha'].exists():
        parashot = load_parasha_list(cfg['parasha'], english)
        gen.PARASHOT = parashot
        print(f"  Loaded {len(parashot)} parashiyot from {cfg['parasha'].name}")
    else:
        print(f"  WARNING: No parasha file found at {cfg['parasha']}")

    # Monkey-patch the header text and title
    original_init = gen.PDFBuilder.__init__
    def patched_init(self, output_path):
        original_init(self, output_path)
        self.c.setTitle(f"Torah: Word by Word - {english}")

    original_draw_header = gen.PDFBuilder.draw_header
    def patched_draw_header(self):
        if self.is_title_page:
            return
        y = gen.PAGE_H - 45
        parasha = gen.get_parasha_for_chapter(self.current_chapter)
        self.c.setFillColor(gen.INK_LIGHT)
        self.c.setFont('Serif', 9)
        self.c.drawString(gen.MARGIN_L, y, f"Parashat {parasha['name']} \u00B7 {english} Chapter {self.current_chapter}")
        self.c.setFont('Hebrew', 9)
        he_name = parasha.get('he', parasha['name'])
        self.c.drawRightString(gen.PAGE_W - gen.MARGIN_R, y, gen.heb(he_name))
        self.c.setStrokeColor(gen.DIVIDER)
        self.c.setLineWidth(0.5)
        self.c.line(gen.MARGIN_L, y - 6, gen.PAGE_W - gen.MARGIN_R, y - 6)

    gen.PDFBuilder.__init__ = patched_init
    gen.PDFBuilder.draw_header = patched_draw_header

    # Load data and generate
    with open(cfg['input'], 'r', encoding='utf-8') as f:
        data = json.load(f)

    parasha_data = None
    if cfg['parasha'].exists():
        with open(cfg['parasha'], 'r', encoding='utf-8') as f:
            parasha_data = json.load(f)

    print(f"  {len(data['chapters'])} chapters, {sum(len(ch['verses']) for ch in data['chapters'])} verses")

    gen.register_fonts()

    builder = gen.PDFBuilder(str(cfg['output']))
    builder.build(data, parasha_data)

    print(f"  Output: {cfg['output']}")

    sys.argv = old_argv


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or 'all' in args:
        books = list(BOOK_CONFIG.keys())
    else:
        books = [a for a in args if a in BOOK_CONFIG]

    if not books:
        print("Usage: python generate_pdf_book.py [exodus|leviticus|numbers|deuteronomy|all]")
        sys.exit(1)

    for book_key in books:
        generate_book_pdf(book_key)


if __name__ == '__main__':
    main()
