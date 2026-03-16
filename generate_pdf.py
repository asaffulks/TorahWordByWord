#!/usr/bin/env python3
"""
PDF Generator — Tanach: Word by Word
=====================================
Reads genesis.json and produces a print-ready interlinear PDF.

Run:      python generate_pdf.py genesis.json tanach_genesis.pdf
Requires: pip install reportlab python-bidi
"""

import json
import os
import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── Font Setup ──────────────────────────────────────────────────────────────

FONT_DIR = Path(__file__).parent / "fonts"

def register_fonts():
    """Register fonts for PDF rendering."""
    free_serif = FONT_DIR / "FreeSerif.ttf"
    free_serif_bold = FONT_DIR / "FreeSerifBold.ttf"
    free_serif_italic = FONT_DIR / "FreeSerifItalic.ttf"

    if free_serif.exists():
        pdfmetrics.registerFont(TTFont('Hebrew', str(free_serif)))
        pdfmetrics.registerFont(TTFont('HebrewBold', str(free_serif_bold) if free_serif_bold.exists() else str(free_serif)))
        pdfmetrics.registerFont(TTFont('HebrewItalic', str(free_serif_italic) if free_serif_italic.exists() else str(free_serif)))
        pdfmetrics.registerFont(TTFont('Serif', str(free_serif)))
        pdfmetrics.registerFont(TTFont('SerifBold', str(free_serif_bold) if free_serif_bold.exists() else str(free_serif)))
        pdfmetrics.registerFont(TTFont('SerifItalic', str(free_serif_italic) if free_serif_italic.exists() else str(free_serif)))
    else:
        print("WARNING: FreeSerif not found in fonts/, falling back to Times New Roman")
        pdfmetrics.registerFont(TTFont('Hebrew', 'C:/Windows/Fonts/times.ttf'))
        pdfmetrics.registerFont(TTFont('HebrewBold', 'C:/Windows/Fonts/timesbd.ttf'))
        pdfmetrics.registerFont(TTFont('HebrewItalic', 'C:/Windows/Fonts/timesi.ttf'))
        pdfmetrics.registerFont(TTFont('Serif', 'C:/Windows/Fonts/times.ttf'))
        pdfmetrics.registerFont(TTFont('SerifBold', 'C:/Windows/Fonts/timesbd.ttf'))
        pdfmetrics.registerFont(TTFont('SerifItalic', 'C:/Windows/Fonts/timesi.ttf'))

# ─── Page Constants ──────────────────────────────────────────────────────────

PAGE_W, PAGE_H = letter  # 612 x 792
MARGIN_L = 36
MARGIN_R = 36
MARGIN_T = 66
MARGIN_B = 54
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R  # ~540

# Colors
INK = HexColor('#2C1810')
INK_LIGHT = HexColor('#5C4A3A')
INK_FAINT = HexColor('#8A7A6A')
AMBER_BG = HexColor('#FAEEDA')
AMBER_TEXT = HexColor('#633806')
AMBER_BORDER = HexColor('#E8D5B0')
BLUE_BG = HexColor('#E6F1FB')
BLUE_TEXT = HexColor('#0C447C')
BLUE_BORDER = HexColor('#B8D4F0')
SECTION_BG = HexColor('#F5F0E8')
PARCHMENT_DEEP = HexColor('#F0E8DA')
CARD_BG = HexColor('#FEFDFB')
CARD_BORDER = HexColor('#E0D8CC')
DIVIDER = HexColor('#D8CFBF')
ACCENT_GOLD = HexColor('#B8860B')
PARCHMENT = HexColor('#FAF6F0')

# Card dimensions
CARD_W = 84
CARD_H = 94
CARD_PAD = 7
CARD_GAP = 4
ROW_GAP = 6

# ─── Parasha Data ───────────────────────────────────────────────────────────

PARASHOT = [
    {"name": "Bereshit",      "he": "\u05D1\u05B0\u05BC\u05E8\u05B5\u05D0\u05E9\u05C1\u05B4\u05D9\u05EA", "start": (1,1),  "end": (6,8)},
    {"name": "Noach",         "he": "\u05E0\u05B9\u05D7\u05B7",             "start": (6,9),  "end": (11,32)},
    {"name": "Lech Lecha",    "he": "\u05DC\u05B6\u05DA\u05BE\u05DC\u05B0\u05DA\u05B8", "start": (12,1), "end": (17,27)},
    {"name": "Vayera",        "he": "\u05D5\u05B7\u05D9\u05B5\u05BC\u05E8\u05B8\u05D0",   "start": (18,1), "end": (22,24)},
    {"name": "Chayei Sarah",  "he": "\u05D7\u05B7\u05D9\u05B5\u05BC\u05D9 \u05E9\u05B8\u05C2\u05E8\u05B8\u05D4", "start": (23,1), "end": (25,18)},
    {"name": "Toldot",        "he": "\u05EA\u05BC\u05D5\u05B9\u05DC\u05B0\u05D3\u05B9\u05EA",   "start": (25,19), "end": (28,9)},
    {"name": "Vayetze",       "he": "\u05D5\u05B7\u05D9\u05B5\u05BC\u05E6\u05B5\u05D0",   "start": (28,10), "end": (32,3)},
    {"name": "Vayishlach",    "he": "\u05D5\u05B7\u05D9\u05B4\u05E9\u05C1\u05B0\u05DC\u05B7\u05D7", "start": (32,4), "end": (36,43)},
    {"name": "Vayeshev",      "he": "\u05D5\u05B7\u05D9\u05B5\u05BC\u05E9\u05C1\u05B6\u05D1",   "start": (37,1), "end": (40,23)},
    {"name": "Miketz",        "he": "\u05DE\u05B4\u05E7\u05B5\u05BC\u05E5",         "start": (41,1), "end": (44,17)},
    {"name": "Vayigash",      "he": "\u05D5\u05B7\u05D9\u05B4\u05BC\u05D2\u05B7\u05BC\u05E9\u05C1", "start": (44,18), "end": (47,27)},
    {"name": "Vayechi",       "he": "\u05D5\u05B7\u05D9\u05B0\u05D7\u05B4\u05D9",     "start": (47,28), "end": (50,26)},
]

def get_parasha_for_chapter(chapter):
    """Return the parasha that contains this chapter."""
    for p in PARASHOT:
        if p["start"][0] <= chapter <= p["end"][0]:
            return p
    return PARASHOT[0]

def get_parasha_for_verse(chapter, verse):
    """Return the parasha that contains this specific verse."""
    for p in PARASHOT:
        s_ch, s_v = p["start"]
        e_ch, e_v = p["end"]
        if (chapter > s_ch or (chapter == s_ch and verse >= s_v)) and \
           (chapter < e_ch or (chapter == e_ch and verse <= e_v)):
            return p
    return PARASHOT[0]

def is_parasha_start(chapter, verse):
    """Check if this verse is the start of a new parasha."""
    for p in PARASHOT:
        if p["start"] == (chapter, verse):
            return p
    return None

# ─── Helper Functions ────────────────────────────────────────────────────────

def heb(text):
    """Wrap Hebrew text with bidi for correct RTL rendering."""
    return get_display(text)

def truncate(text, font, size, max_w, c):
    """Truncate text with ellipsis to fit max_w."""
    if not text:
        return ""
    w = c.stringWidth(text, font, size)
    if w <= max_w:
        return text
    while len(text) > 1 and c.stringWidth(text + '...', font, size) > max_w:
        text = text[:-1]
    return text.rstrip() + '...'

def draw_rounded_rect(c, x, y, w, h, r, fill=None, stroke=None):
    """Draw a rounded rectangle."""
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    p.close()
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(0.5)
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)

def draw_pill(c, x, y, text, font, size, bg, fg, border, min_w=30):
    """Draw a pill badge with centered text. Returns pill width."""
    c.setFont(font, size)
    tw = c.stringWidth(text, font, size)
    pw = max(tw + 10, min_w)
    ph = size + 4
    draw_rounded_rect(c, x, y, pw, ph, ph/2, fill=bg, stroke=border)
    c.setFillColor(fg)
    c.drawCentredString(x + pw/2, y + 2.5, text)
    return pw


# ─── PDF Builder ─────────────────────────────────────────────────────────────

class PDFBuilder:
    def __init__(self, output_path):
        self.c = canvas.Canvas(output_path, pagesize=letter)
        self.c.setTitle("Torah: Word by Word - Genesis")
        self.c.setAuthor("The Forum Press")
        self.page_num = 0
        self.current_chapter = 0
        self.y = PAGE_H - MARGIN_T
        self.is_title_page = False

    def new_page(self):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self.y = PAGE_H - MARGIN_T
        # Page background
        self.c.setFillColor(PARCHMENT)
        self.c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def draw_header(self):
        if self.is_title_page:
            return
        y = PAGE_H - 45
        parasha = get_parasha_for_chapter(self.current_chapter)
        self.c.setFillColor(INK_LIGHT)
        self.c.setFont('Serif', 9)
        self.c.drawString(MARGIN_L, y, f"Parashat {parasha['name']} \u00B7 Genesis Chapter {self.current_chapter}")
        self.c.setFont('Hebrew', 9)
        self.c.drawRightString(PAGE_W - MARGIN_R, y, heb(parasha['he']))
        self.c.setStrokeColor(DIVIDER)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN_L, y - 6, PAGE_W - MARGIN_R, y - 6)

    def draw_footer(self):
        if self.is_title_page:
            return
        self.c.setFillColor(INK_FAINT)
        self.c.setFont('Serif', 9)
        self.c.drawCentredString(PAGE_W / 2, MARGIN_B - 20, str(self.page_num))

    def ensure_space(self, needed):
        """Start a new page if not enough space. Returns True if page changed."""
        if self.y - needed < MARGIN_B:
            self.draw_footer()
            self.new_page()
            self.draw_header()
            self.y = PAGE_H - MARGIN_T - 20
            return True
        return False

    # ─── Title Page ──────────────────────────────────────────────────────

    def draw_title_page(self):
        self.new_page()
        self.is_title_page = True
        c = self.c
        y = PAGE_H - 160

        # Hebrew title
        c.setFont('HebrewBold', 52)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, y, heb('\u05EA\u05BC\u05D5\u05B9\u05E8\u05B8\u05D4'))
        y -= 55

        # English title: Torah
        c.setFont('SerifBold', 28)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, y, "Torah")
        y -= 35

        # Subtitle: Word by Word
        c.setFont('SerifBold', 16)
        c.setFillColor(ACCENT_GOLD)
        c.drawCentredString(PAGE_W / 2, y, "Word by Word")
        y -= 28

        # Sub-subtitle: An Interlinear Edition
        c.setFont('SerifItalic', 13)
        c.setFillColor(INK_LIGHT)
        c.drawCentredString(PAGE_W / 2, y, "An Interlinear Edition")
        y -= 35

        # Decorative line
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(1)
        c.line(PAGE_W/2 - 80, y, PAGE_W/2 + 80, y)
        y -= 25

        # Compiled by
        c.setFont('Serif', 11)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, y, "Compiled by Asaf Fulks")
        y -= 30

        # Description
        c.setFont('Serif', 9)
        c.setFillColor(INK_LIGHT)
        desc = ("A complete word-by-word interlinear edition of the Book of Genesis, "
                "presenting each Hebrew word with its transliteration, three-letter root, "
                "English gloss, and gematria value. Commentary by Rashi and Ramban. "
                "Gematria values follow the standard Mispar Hechrachi system.")
        for line in self._wrap_text(desc, 'Serif', 9, 360):
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= 14

        y -= 20
        self._draw_gematria_chart(y)

        # --- Bottom section ---
        # Forum Press logo
        logo_path = FONT_DIR / "fp_logo.jpg"
        if logo_path.exists():
            logo_w = 60
            logo_h = 60
            c.drawImage(str(logo_path), PAGE_W / 2 - logo_w / 2, MARGIN_B + 72,
                        width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

        # Publisher
        c.setFont('SerifBold', 10)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, MARGIN_B + 56, "The Forum Press")

        # Book design credit
        c.setFont('SerifItalic', 8.5)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, MARGIN_B + 42, "Book design and layout by Yakira Shimoni Fulks")

        # Copyright
        c.setFont('Serif', 8)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, MARGIN_B + 26, "\u00A9 2026 The Forum Press. All rights reserved.")

        # Tagline
        c.setFont('SerifItalic', 8)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, MARGIN_B + 12, "The Hebrew Bible, one word at a time")

        self.is_title_page = False

    def _draw_gematria_chart(self, start_y):
        c = self.c
        letters = [
            ('\u05D0', 1), ('\u05D1', 2), ('\u05D2', 3), ('\u05D3', 4), ('\u05D4', 5),
            ('\u05D5', 6), ('\u05D6', 7), ('\u05D7', 8), ('\u05D8', 9), ('\u05D9', 10), ('\u05DB', 20),
            ('\u05DC', 30), ('\u05DE', 40), ('\u05E0', 50), ('\u05E1', 60), ('\u05E2', 70),
            ('\u05E4', 80), ('\u05E6', 90), ('\u05E7', 100), ('\u05E8', 200), ('\u05E9', 300), ('\u05EA', 400),
        ]
        chart_w = 400
        cell_w = chart_w / 11
        cell_h = 40
        x_start = (PAGE_W - chart_w) / 2
        y = start_y

        draw_rounded_rect(c, x_start - 10, y - cell_h * 2 - 20, chart_w + 20, cell_h * 2 + 30, 6,
                          fill=AMBER_BG, stroke=AMBER_BORDER)

        c.setFont('SerifBold', 10)
        c.setFillColor(AMBER_TEXT)
        c.drawCentredString(PAGE_W / 2, y + 2, "Gematria Reference - Mispar Hechrachi")
        y -= 8

        for row_idx in range(2):
            row = letters[row_idx * 11:(row_idx + 1) * 11]
            for col, (letter_char, val) in enumerate(row):
                cx = x_start + col * cell_w + cell_w / 2
                c.setFont('Hebrew', 16)
                c.setFillColor(INK)
                c.drawCentredString(cx, y - 16, heb(letter_char))
                c.setFont('Serif', 8)
                c.setFillColor(BLUE_TEXT)
                c.drawCentredString(cx, y - 30, str(val))
            y -= cell_h

    # ─── Chapter Title Page ──────────────────────────────────────────────

    def _get_parasha_stats(self, parasha, data):
        """Compute statistics for a parasha from the data."""
        s_ch, s_v = parasha['start']
        e_ch, e_v = parasha['end']
        verses = []
        for ch in data['chapters']:
            for v in ch['verses']:
                ch_num = ch['chapter']
                v_num = v['verse']
                if (ch_num > s_ch or (ch_num == s_ch and v_num >= s_v)) and \
                   (ch_num < e_ch or (ch_num == e_ch and v_num <= e_v)):
                    verses.append(v)
        total_words = sum(len(v['words']) for v in verses)
        total_gem = sum(v.get('total_gematria', 0) for v in verses)
        has_rashi = sum(1 for v in verses if v.get('rashi'))
        return {
            'verses': len(verses),
            'words': total_words,
            'total_gem': total_gem,
            'has_rashi': has_rashi,
        }

    def draw_parasha_title(self, parasha, data=None):
        """Draw a parasha title page with stats and content."""
        self.draw_footer()
        self.new_page()
        self.is_title_page = True
        c = self.c
        y = PAGE_H - 140

        # "Parashat" label
        c.setFont('SerifItalic', 14)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, y, "Parashat")
        y -= 45

        # Hebrew parasha name (large)
        c.setFont('HebrewBold', 48)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, y, heb(parasha['he']))
        y -= 50

        # English parasha name
        c.setFont('SerifBold', 26)
        c.setFillColor(INK_LIGHT)
        c.drawCentredString(PAGE_W / 2, y, parasha['name'])
        y -= 35

        # Decorative line
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(1.5)
        c.line(PAGE_W/2 - 100, y, PAGE_W/2 + 100, y)
        y -= 30

        # Chapter/verse range
        s_ch, s_v = parasha['start']
        e_ch, e_v = parasha['end']
        c.setFont('Serif', 12)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, y, f"Genesis {s_ch}:{s_v} \u2013 {e_ch}:{e_v}")
        y -= 35

        # Statistics box
        if data:
            stats = self._get_parasha_stats(parasha, data)

            # Stats in amber box
            box_w = 320
            box_h = 70
            box_x = (PAGE_W - box_w) / 2
            draw_rounded_rect(c, box_x, y - box_h, box_w, box_h, 6, fill=AMBER_BG, stroke=AMBER_BORDER)

            c.setFont('SerifBold', 10)
            c.setFillColor(AMBER_TEXT)
            c.drawCentredString(PAGE_W / 2, y - 16, "Parasha Overview")

            c.setFont('Serif', 9)
            c.setFillColor(INK_LIGHT)
            col1_x = box_x + 30
            col2_x = box_x + box_w / 2 + 20
            c.drawString(col1_x, y - 34, f"Verses: {stats['verses']}")
            c.drawString(col2_x, y - 34, f"Words: {stats['words']}")
            c.drawString(col1_x, y - 50, f"Total Gematria: {stats['total_gem']:,}")
            c.drawString(col2_x, y - 50, f"Rashi Comments: {stats['has_rashi']}")

            # Gematria factorization of total
            from collections import Counter
            factors = []
            n = stats['total_gem']
            d_val = 2
            while d_val * d_val <= n:
                while n % d_val == 0:
                    factors.append(d_val)
                    n //= d_val
                d_val += 1
            if n > 1:
                factors.append(n)
            if len(factors) > 1:
                counts = Counter(factors)
                parts = []
                for p in sorted(counts.keys()):
                    if counts[p] == 1:
                        parts.append(str(p))
                    else:
                        parts.append(f"{p}^{counts[p]}")
                c.setFont('SerifItalic', 8)
                c.setFillColor(INK_FAINT)
                c.drawCentredString(PAGE_W / 2, y - 64, f"Parasha gematria: {stats['total_gem']:,} = {' x '.join(parts)}")

            y -= box_h + 25

        # Decorative line
        c.setStrokeColor(DIVIDER)
        c.setLineWidth(0.5)
        c.line(PAGE_W/2 - 60, y, PAGE_W/2 + 60, y)
        y -= 25

        # Opening verse preview (first verse of parasha)
        if data:
            # Find the first verse
            for ch in data['chapters']:
                for v in ch['verses']:
                    if ch['chapter'] == s_ch and v['verse'] == s_v:
                        # Hebrew text of opening verse
                        c.setFont('SerifItalic', 10)
                        c.setFillColor(INK_FAINT)
                        c.drawCentredString(PAGE_W / 2, y, "Opening verse:")
                        y -= 20

                        c.setFont('Hebrew', 14)
                        c.setFillColor(INK)
                        heb_full = v.get('hebrew_full', '')
                        # Wrap if long
                        heb_lines = self._wrap_text(heb_full, 'Hebrew', 14, CONTENT_W - 80)
                        for line in heb_lines[:2]:
                            c.drawCentredString(PAGE_W / 2, y, heb(line))
                            y -= 20
                        y -= 8

                        # Translation
                        c.setFont('SerifItalic', 10)
                        c.setFillColor(INK_LIGHT)
                        trans = v.get('translation', '')
                        trans_lines = self._wrap_text(trans, 'SerifItalic', 10, CONTENT_W - 80)
                        for line in trans_lines[:3]:
                            c.drawCentredString(PAGE_W / 2, y, line)
                            y -= 15
                        y -= 15

                        # Rashi on opening verse
                        rashi = v.get('rashi', '')
                        if rashi:
                            c.setStrokeColor(DIVIDER)
                            c.setLineWidth(0.5)
                            c.setDash(3, 3)
                            c.line(PAGE_W/2 - 80, y + 8, PAGE_W/2 + 80, y + 8)
                            c.setDash()

                            c.setFont('SerifBold', 9)
                            c.setFillColor(INK)
                            c.drawString(MARGIN_L + 20, y, "Rashi on opening verse:")
                            y -= 14

                            c.setFont('SerifItalic', 8.5)
                            c.setFillColor(INK_LIGHT)
                            rashi_lines = self._wrap_text(rashi, 'SerifItalic', 8.5, CONTENT_W - 40)
                            for line in rashi_lines:
                                if y < MARGIN_B + 40:
                                    break
                                c.drawString(MARGIN_L + 20, y, line)
                                y -= 13
                        break
                else:
                    continue
                break

        self.is_title_page = False

    def draw_chapter_title(self, chapter_num):
        """Draw an inline chapter divider (not a full page)."""
        self.current_chapter = chapter_num
        c = self.c

        parasha = get_parasha_for_chapter(chapter_num)

        # Need ~95pt for the inline chapter header with parasha
        self.ensure_space(100)

        x_mid = MARGIN_L + CONTENT_W / 2
        y = self.y

        # Gold line above
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(1)
        c.line(x_mid - 120, y, x_mid + 120, y)
        y -= 18

        # Parasha name (Hebrew + English)
        c.setFont('SerifItalic', 11)
        c.setFillColor(ACCENT_GOLD)
        c.drawCentredString(x_mid, y, f"Parashat {parasha['name']}")
        y -= 16

        c.setFont('Hebrew', 12)
        c.setFillColor(ACCENT_GOLD)
        c.drawCentredString(x_mid, y, heb(parasha['he']))
        y -= 20

        # Chapter label
        c.setFont('SerifBold', 14)
        c.setFillColor(INK)
        c.drawCentredString(x_mid, y, f"Chapter {chapter_num}")
        y -= 18

        # Gold line below
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(0.5)
        c.line(x_mid - 80, y, x_mid + 80, y)
        y -= 12

        self.y = y

    # ─── Verse Block ─────────────────────────────────────────────────────

    def calc_verse_height(self, verse):
        """Minimum height needed for verse — compact estimate for page-break decisions.
        Commentary will expand dynamically to fill remaining space at render time."""
        words = verse['words']
        cards_per_row = max(1, int((CONTENT_W + CARD_GAP) / (CARD_W + CARD_GAP)))
        num_rows = (len(words) + cards_per_row - 1) // cards_per_row

        header_h = 28
        cards_h = num_rows * CARD_H + max(0, num_rows - 1) * ROW_GAP + 12
        # Compact footer: just gematria + minimal Rashi
        # Ramban is NOT counted — it only fills leftover space
        footer_h = 32
        if verse.get('gem_note'):
            footer_h += 16
        if verse.get('rashi'):
            footer_h += 44

        return header_h + cards_h + footer_h + 12

    def _available(self):
        """Available vertical space on current page."""
        return self.y - MARGIN_B

    def _next_page(self):
        """Start a new content page."""
        self.draw_footer()
        self.new_page()
        self.draw_header()
        self.y = PAGE_H - MARGIN_T - 20

    def _calc_footer_h(self, verse, available_space=None):
        """Calculate footer height based on actual content that will be rendered.
        If available_space given, allow more lines up to that limit."""
        footer_h = 32
        if verse.get('gem_note'):
            footer_h += 16

        rashi = verse.get('rashi', '')
        ramban = verse.get('ramban', '')

        # How many lines can we show?
        if available_space and available_space > 120:
            max_rashi_lines = min(15, max(3, len(rashi) // 70 + 1))
            max_ramban_lines = min(10, max(2, len(ramban) // 70 + 1))
        else:
            max_rashi_lines = min(6, max(2, len(rashi) // 70 + 1))
            max_ramban_lines = min(4, max(2, len(ramban) // 70 + 1))

        if rashi:
            rashi_lines = min(max_rashi_lines, len(rashi) // 70 + 1)
            footer_h += 18 + rashi_lines * 13
        if ramban:
            ramban_lines = min(max_ramban_lines, len(ramban) // 70 + 1)
            footer_h += 18 + ramban_lines * 13

        # Cap to available space if given
        if available_space:
            footer_h = min(footer_h, int(available_space))

        return footer_h

    def draw_verse(self, verse):
        c = self.c
        x_base = MARGIN_L
        words = verse['words']
        cards_per_row = max(1, int((CONTENT_W + CARD_GAP) / (CARD_W + CARD_GAP)))
        num_rows = (len(words) + cards_per_row - 1) // cards_per_row

        header_h = 28
        footer_h = self._calc_footer_h(verse)
        verse_h = self.calc_verse_height(verse)

        # Never split a verse across pages — if it doesn't fit, push to next page
        if verse_h > self._available():
            self._next_page()

        y = self.y

        # ── Header bar — wraps translation to 2 lines if needed ──
        trans = verse.get('translation', '')
        ref_text = verse['ref'].upper()
        ref_w = c.stringWidth(ref_text, 'SerifBold', 10) + 20
        trans_w = CONTENT_W - ref_w - 16
        trans_lines = self._wrap_text(trans, 'SerifItalic', 9, trans_w) if trans else []
        header_h = 28 if len(trans_lines) <= 1 else 40

        draw_rounded_rect(c, x_base, y - header_h, CONTENT_W, header_h, 4, fill=AMBER_BG, stroke=AMBER_BORDER)
        c.setFont('SerifBold', 10)
        c.setFillColor(AMBER_TEXT)
        c.drawString(x_base + 8, y - 19, ref_text)
        c.setFont('SerifItalic', 9)
        c.setFillColor(INK_LIGHT)
        if trans_lines:
            c.drawRightString(x_base + CONTENT_W - 8, y - 19, trans_lines[0])
        if len(trans_lines) > 1:
            c.drawRightString(x_base + CONTENT_W - 8, y - 33, trans_lines[1])
        y -= header_h + 6

        # ── Word cards (RTL) — entire verse on one page ──
        for row_start in range(0, len(words), cards_per_row):
            row_words = words[row_start:row_start + cards_per_row]

            # Draw cards from right edge, moving left
            card_x = x_base + CONTENT_W
            for word in row_words:
                card_x -= CARD_W
                self._draw_word_card(card_x, y - CARD_H, word)
                card_x -= CARD_GAP

            y -= CARD_H + ROW_GAP

        y -= 2

        # ── Footer bar ──
        # Has commentary? Fill to bottom. No commentary? Compact footer, share page.
        has_commentary = any(verse.get(k) for k in ['rashi','ramban','ibn_ezra','sforno','or_hachaim'])
        if has_commentary:
            footer_h = max(32, y - MARGIN_B)
        else:
            footer_h = 32
            if verse.get('gem_note'):
                footer_h += 16
        box_top = y
        box_bottom = y - footer_h
        left = x_base + 10          # text left margin inside box
        right = x_base + CONTENT_W - 10  # text right margin inside box
        text_w = right - left        # actual drawable text width

        draw_rounded_rect(c, x_base, box_bottom, CONTENT_W, footer_h, 4,
                          fill=PARCHMENT_DEEP, stroke=CARD_BORDER)

        cur_y = box_top - 16  # start drawing from top of box
        stop_y = box_bottom + 10  # stop drawing near bottom of box

        # -- Gematria total --
        c.setFont('Serif', 9)
        c.setFillColor(INK_FAINT)
        c.drawString(left, cur_y, "Verse total:")
        tw = c.stringWidth("Verse total: ", 'Serif', 9)
        draw_pill(c, left + tw + 4, cur_y - 2, str(verse.get('total_gematria', 0)),
                  'Serif', 9, BLUE_BG, BLUE_TEXT, BLUE_BORDER)

        # -- Gematria note --
        gem_note = verse.get('gem_note', '')
        if gem_note and cur_y - 16 > stop_y:
            cur_y -= 16
            c.setFont('SerifItalic', 8)
            c.setFillColor(INK_FAINT)
            c.drawString(left, cur_y, truncate(gem_note, 'SerifItalic', 8, text_w, c))

        # -- Commentary sections --
        commentary_list = [
            ("Rashi", verse.get('rashi', '')),
            ("Ramban", verse.get('ramban', '')),
            ("Ibn Ezra", verse.get('ibn_ezra', '')),
            ("Sforno", verse.get('sforno', '')),
            ("Or HaChaim", verse.get('or_hachaim', '')),
        ]
        active = [(lbl, txt) for lbl, txt in commentary_list if txt]
        num_active = len(active)

        # Calculate fair line budget per commentator
        total_lines = max(1, int((cur_y - stop_y) / 13))
        if num_active > 0:
            lines_each = max(3, total_lines // num_active)
        else:
            lines_each = total_lines

        for label, text in active:
            if cur_y - 28 < stop_y:
                break  # no room for another section

            cur_y -= 14
            # Dashed divider
            c.setStrokeColor(DIVIDER)
            c.setLineWidth(0.5)
            c.setDash(3, 3)
            c.line(left, cur_y + 10, right, cur_y + 10)
            c.setDash()

            # Label
            c.setFont('SerifBold', 9)
            c.setFillColor(INK)
            c.drawString(left, cur_y, f"{label}:")
            label_end = left + c.stringWidth(f"{label}: ", 'SerifBold', 9) + 2

            # First line — narrower (after label)
            c.setFont('SerifItalic', 8.5)
            c.setFillColor(INK_LIGHT)
            first_w = right - label_end
            first_lines = self._wrap_text(text, 'SerifItalic', 8.5, first_w)
            if first_lines:
                c.drawString(label_end, cur_y, first_lines[0])

            # Continuation lines — full width, capped at lines_each
            rest = text[len(first_lines[0]):].strip() if first_lines else text
            cont_lines = self._wrap_text(rest, 'SerifItalic', 8.5, text_w)
            drawn = 1
            for line in cont_lines:
                if drawn >= lines_each:
                    break
                if cur_y - 13 < stop_y:
                    break
                cur_y -= 13
                c.drawString(left, cur_y, line)
                drawn += 1

        if has_commentary:
            self.y = MARGIN_B - 1  # next verse on new page
        else:
            self.y = y - footer_h - 6  # room for next verse on this page

    def _wrap_text(self, text, font, size, max_w):
        words = text.split()
        lines = []
        current = []
        for w in words:
            test = ' '.join(current + [w])
            if self.c.stringWidth(test, font, size) > max_w:
                if current:
                    lines.append(' '.join(current))
                current = [w]
            else:
                current.append(w)
        if current:
            lines.append(' '.join(current))
        return lines

    def _draw_word_card(self, x, y, word):
        c = self.c
        w = CARD_W
        h = CARD_H
        p = CARD_PAD

        draw_rounded_rect(c, x, y, w, h, 4, fill=CARD_BG, stroke=CARD_BORDER)

        inner_y = y + h - p

        # Hebrew text (16pt — the star of the show)
        c.setFont('Hebrew', 16)
        c.setFillColor(INK)
        heb_text = heb(word['heb'])
        if c.stringWidth(heb_text, 'Hebrew', 16) > w - 2*p:
            c.setFont('Hebrew', 13)
        c.drawCentredString(x + w/2, inner_y - 16, heb_text)
        inner_y -= 21

        # Transliteration
        c.setFont('SerifItalic', 8)
        c.setFillColor(INK_FAINT)
        tr = truncate(word.get('tr', ''), 'SerifItalic', 8, w - 2*p, c)
        c.drawCentredString(x + w/2, inner_y - 8, tr)
        inner_y -= 13

        # Root badge
        root = word.get('root', '')
        if root:
            root_text = heb(root)
            pill_w = max(c.stringWidth(root_text, 'Hebrew', 8) + 10, 26)
            pill_x = x + (w - pill_w) / 2
            draw_rounded_rect(c, pill_x, inner_y - 12, pill_w, 13, 6, fill=AMBER_BG, stroke=AMBER_BORDER)
            c.setFont('Hebrew', 8)
            c.setFillColor(AMBER_TEXT)
            c.drawCentredString(x + w/2, inner_y - 10, root_text)
        inner_y -= 15

        # Divider
        c.setStrokeColor(DIVIDER)
        c.setLineWidth(0.5)
        c.line(x + p, inner_y, x + w - p, inner_y)
        inner_y -= 3

        # English gloss
        c.setFont('Serif', 9)
        c.setFillColor(INK)
        eng = truncate(word.get('eng', ''), 'Serif', 9, w - 2*p, c)
        c.drawCentredString(x + w/2, inner_y - 9, eng)
        inner_y -= 14

        # Gematria badge
        gem_text = str(word.get('gem', 0))
        gem_w = max(c.stringWidth(gem_text, 'Serif', 8) + 10, 24)
        gem_x = x + (w - gem_w) / 2
        draw_rounded_rect(c, gem_x, inner_y - 12, gem_w, 13, 6, fill=BLUE_BG, stroke=BLUE_BORDER)
        c.setFont('Serif', 8)
        c.setFillColor(BLUE_TEXT)
        c.drawCentredString(x + w/2, inner_y - 9, gem_text)

    # ─── Build ───────────────────────────────────────────────────────────

    def build(self, data):
        print(f"Building PDF: {len(data['chapters'])} chapters, {len(PARASHOT)} parashot...")

        self.draw_title_page()

        drawn_parashot = set()
        for ch_data in data['chapters']:
            ch_num = ch_data['chapter']

            # Check if this chapter starts a new parasha — full title page
            for p in PARASHOT:
                if p['start'][0] == ch_num and p['name'] not in drawn_parashot:
                    self.draw_parasha_title(p, data)
                    drawn_parashot.add(p['name'])
                    # Start fresh content page after parasha title
                    self.draw_footer()
                    self.new_page()
                    self.draw_header()
                    self.y = PAGE_H - MARGIN_T - 20
                    break

            print(f"  Chapter {ch_num}: {len(ch_data['verses'])} verses")
            self.draw_chapter_title(ch_num)

            for verse in ch_data['verses']:
                self.draw_verse(verse)

        self.draw_footer()
        self.c.save()
        print(f"Done! {self.page_num} pages generated.")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "genesis.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "Torah Word by Word - Genesis.pdf"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {input_file}: {len(data['chapters'])} chapters")

    register_fonts()

    builder = PDFBuilder(output_file)
    builder.build(data)
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
