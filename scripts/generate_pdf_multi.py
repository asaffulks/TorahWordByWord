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

# Card dimensions — MULTI-MEANING VERSION (taller cards)
CARD_W = 90
CARD_H = 130
CARD_PAD = 6
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

def heb_mixed(text):
    """Handle mixed Hebrew/English text: reverse only Hebrew segments in place.
    This keeps numbers and English in LTR while Hebrew reads RTL."""
    import re
    def reverse_heb(m):
        return get_display(m.group(0))
    return re.sub(r'[\u05B0-\u05EA\u05BE]+', reverse_heb, text)

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
                "English gloss, and gematria value. Commentary by Rashi, Ramban, Ibn Ezra, "
                "Sforno, Or HaChaim, Chizkuni, Rabbeinu Bahya, Onkelos, and Kli Yakar. "
                "Gematria values follow the standard Mispar Hechrachi system.")
        for line in self._wrap_text(desc, 'Serif', 9, 360):
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= 14

        y -= 20
        self._draw_gematria_chart(y)

        # --- Bottom section ---
        # Forum Press logo (PNG with transparency — includes "THE FORUM PRESS" text)
        logo_path = FONT_DIR / "fp_logo.png"
        if not logo_path.exists():
            logo_path = FONT_DIR / "fp_logo.jpg"
        if logo_path.exists():
            logo_w = 80
            logo_h = 80
            c.drawImage(str(logo_path), PAGE_W / 2 - logo_w / 2, MARGIN_B + 48,
                        width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

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

    def draw_parasha_title(self, parasha, data=None, parasha_info=None):
        """Draw a rich parasha title page with insights and content."""
        self.draw_footer()
        self.new_page()
        self.is_title_page = True
        c = self.c
        left = MARGIN_L + 20
        right = PAGE_W - MARGIN_R - 20
        text_w = right - left
        y = PAGE_H - 120

        # "Parashat" label
        c.setFont('SerifItalic', 13)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, y, "Parashat")
        y -= 40

        # Hebrew parasha name (large)
        c.setFont('HebrewBold', 44)
        c.setFillColor(INK)
        c.drawCentredString(PAGE_W / 2, y, heb(parasha['he']))
        y -= 45

        # English parasha name
        c.setFont('SerifBold', 24)
        c.setFillColor(INK_LIGHT)
        c.drawCentredString(PAGE_W / 2, y, parasha['name'])
        y -= 28

        # Decorative line
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(1.5)
        c.line(PAGE_W/2 - 100, y, PAGE_W/2 + 100, y)
        y -= 22

        # Chapter/verse range
        s_ch, s_v = parasha['start']
        e_ch, e_v = parasha['end']
        c.setFont('Serif', 11)
        c.setFillColor(INK_FAINT)
        c.drawCentredString(PAGE_W / 2, y, f"Genesis {s_ch}:{s_v} \u2013 {e_ch}:{e_v}")
        y -= 22

        if not parasha_info:
            self.is_title_page = False
            return

        # ── Thematic Summary ──
        summary = parasha_info.get('thematic_summary', '')
        if summary:
            c.setFont('SerifItalic', 9.5)
            c.setFillColor(INK)
            for line in self._wrap_text(summary, 'SerifItalic', 9.5, text_w):
                c.drawString(left, y, line)
                y -= 13
            y -= 8

        # ── Stats box ──
        stats = parasha_info.get('stats', {})
        if stats:
            box_w = CONTENT_W - 40
            box_h = 36
            box_x = MARGIN_L + 20
            draw_rounded_rect(c, box_x, y - box_h, box_w, box_h, 4, fill=AMBER_BG, stroke=AMBER_BORDER)
            c.setFont('Serif', 8.5)
            c.setFillColor(AMBER_TEXT)
            col_w = box_w / 4
            c.drawCentredString(box_x + col_w * 0.5, y - 14, f"Verses: {stats.get('verses', 0)}")
            c.drawCentredString(box_x + col_w * 1.5, y - 14, f"Words: {stats.get('words', 0)}")
            c.drawCentredString(box_x + col_w * 2.5, y - 14, f"Gematria: {stats.get('total_gematria', 0):,}")
            c.drawCentredString(box_x + col_w * 3.5, y - 14, f"Roots: {stats.get('unique_roots', 0)}")
            gem_note = parasha_info.get('gematria_note', '')
            if gem_note:
                c.setFont('SerifItalic', 7.5)
                c.setFillColor(INK_FAINT)
                c.drawCentredString(box_x + box_w / 2, y - 30, gem_note[:120])
            y -= box_h + 12

        # ── Key Figures ──
        figures = parasha_info.get('key_figures', [])
        if figures:
            c.setFont('SerifBold', 9)
            c.setFillColor(ACCENT_GOLD)
            c.drawString(left, y, "Key Figures")
            y -= 14
            c.setFont('Serif', 8.5)
            c.setFillColor(INK_LIGHT)
            for fig in figures[:5]:
                line = f"\u2022 {fig['name']} \u2014 {fig['role']}"
                for wl in self._wrap_text(line, 'Serif', 8.5, text_w - 10)[:2]:
                    c.drawString(left + 5, y, wl)
                    y -= 11
            y -= 6

        # ── Notable Firsts ──
        firsts = parasha_info.get('notable_firsts', [])
        if firsts:
            c.setFont('SerifBold', 9)
            c.setFillColor(ACCENT_GOLD)
            c.drawString(left, y, "Notable Firsts")
            y -= 14
            c.setFont('Serif', 8.5)
            c.setFillColor(INK_LIGHT)
            for first in firsts[:5]:
                line = f"\u2022 {first}"
                c.drawString(left + 5, y, truncate(line, 'Serif', 8.5, text_w - 10, c))
                y -= 11
            y -= 6

        # ── Famous Verses ──
        famous = parasha_info.get('famous_verses', [])
        if famous and y > MARGIN_B + 100:
            c.setFont('SerifBold', 9)
            c.setFillColor(ACCENT_GOLD)
            c.drawString(left, y, "Famous Verses")
            y -= 14
            for fv in famous[:3]:
                c.setFont('SerifBold', 8.5)
                c.setFillColor(INK)
                c.drawString(left + 5, y, f"{fv['ref']}:")
                y -= 12
                c.setFont('SerifItalic', 8.5)
                c.setFillColor(INK_LIGHT)
                for wl in self._wrap_text(f"\u201C{fv['text']}\u201D", 'SerifItalic', 8.5, text_w - 15)[:3]:
                    c.drawString(left + 10, y, wl)
                    y -= 11
                y -= 4

        # ── Haftarah ──
        haftarah = parasha_info.get('haftarah', {})
        if haftarah and y > MARGIN_B + 50:
            y -= 4
            c.setStrokeColor(DIVIDER)
            c.setLineWidth(0.5)
            c.line(left, y + 6, right, y + 6)
            c.setFont('SerifBold', 9)
            c.setFillColor(ACCENT_GOLD)
            c.drawString(left, y - 6, f"Haftarah: ")
            label_end = left + c.stringWidth("Haftarah: ", 'SerifBold', 9)
            c.setFont('Serif', 8.5)
            c.setFillColor(INK)
            c.drawString(label_end, y - 6, haftarah.get('ref', ''))
            y -= 18
            conn = haftarah.get('connection', '')
            if conn:
                c.setFont('SerifItalic', 8.5)
                c.setFillColor(INK_LIGHT)
                for wl in self._wrap_text(conn, 'SerifItalic', 8.5, text_w)[:2]:
                    c.drawString(left, y, wl)
                    y -= 11

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
        has_commentary = any(verse.get(k) for k in ['rashi','ramban','ibn_ezra','sforno','or_hachaim','chizkuni','rabbeinu_bahya','onkelos','kli_yakar'])
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
            c.drawString(left, cur_y, heb_mixed(truncate(gem_note, 'SerifItalic', 8, text_w, c)))

        # -- Commentary sections --
        commentary_list = [
            ("Rashi", verse.get('rashi', '')),
            ("Ramban", verse.get('ramban', '')),
            ("Ibn Ezra", verse.get('ibn_ezra', '')),
            ("Sforno", verse.get('sforno', '')),
            ("Or HaChaim", verse.get('or_hachaim', '')),
            ("Chizkuni", verse.get('chizkuni', '')),
            ("Rabbeinu Bahya", verse.get('rabbeinu_bahya', '')),
            ("Onkelos", verse.get('onkelos', '')),
            ("Kli Yakar", verse.get('kli_yakar', '')),
        ]
        active = [(lbl, txt) for lbl, txt in commentary_list if txt]
        num_active = len(active)
        cross_refs = verse.get('cross_refs', '')

        insights = verse.get('insights', '')

        for label, text in active:
            if cur_y - 28 < stop_y:
                break

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

            # Draw text — full text, but end at last complete sentence that fits
            c.setFont('SerifItalic', 8.5)
            c.setFillColor(INK_LIGHT)

            # Calculate how many lines fit
            lines_available = max(1, int((cur_y - stop_y) / 13))

            # Wrap full text
            first_line_w = right - label_end
            first_lines = self._wrap_text(text, 'SerifItalic', 8.5, first_line_w)
            rest_text = text[len(first_lines[0]):].strip() if first_lines else text
            cont_lines = self._wrap_text(rest_text, 'SerifItalic', 8.5, text_w)
            all_display = ([first_lines[0]] if first_lines else []) + cont_lines

            # If text doesn't fit, find last natural break point
            if len(all_display) > lines_available:
                fit_lines = all_display[:lines_available]
                joined = ' '.join(fit_lines)
                # Find last natural break: sentence end, semicolon, closing bracket/quote, or comma
                best_break = -1
                for i, ch in enumerate(joined):
                    if i < 20:
                        continue
                    if ch in '.!?':
                        best_break = i
                    elif ch in ';' and i > 40:
                        best_break = i
                    elif ch in ']\u201D\u2019)\u0027' and i > 30:  # ] " ' )
                        best_break = i
                    elif ch == ',' and i > 60 and best_break < i - 80:
                        # Use comma only if no better break found recently
                        best_break = i
                if best_break > 0:
                    trimmed = joined[:best_break + 1]
                else:
                    # No punctuation break — back up to last complete word
                    last_space = joined.rfind(' ', 20, len(joined) - 1)
                    if last_space > 0:
                        trimmed = joined[:last_space].rstrip()
                    else:
                        trimmed = joined
                # Ensure we don't end mid-word — strip trailing partial words
                while trimmed and not trimmed[-1].isspace() and trimmed[-1] not in '.!?;,)]\u201D\u2019\u0027: ' and len(trimmed) > 50:
                    last_sp = trimmed.rfind(' ')
                    if last_sp > 20:
                        trimmed = trimmed[:last_sp].rstrip()
                    else:
                        break
                # Re-wrap the trimmed text
                first_lines = self._wrap_text(trimmed, 'SerifItalic', 8.5, first_line_w)
                rest_text = trimmed[len(first_lines[0]):].strip() if first_lines else trimmed
                cont_lines = self._wrap_text(rest_text, 'SerifItalic', 8.5, text_w)

            # Draw
            if first_lines:
                c.drawString(label_end, cur_y, first_lines[0])
                for line in cont_lines:
                    if cur_y - 13 < stop_y:
                        break
                    cur_y -= 13
                    c.drawString(left, cur_y, line)

        # -- Cross-references (fill remaining space) --
        if cross_refs and cur_y - 28 > stop_y:
            cur_y -= 14
            c.setStrokeColor(DIVIDER)
            c.setLineWidth(0.5)
            c.setDash(3, 3)
            c.line(left, cur_y + 10, right, cur_y + 10)
            c.setDash()

            c.setFont('SerifBold', 8)
            c.setFillColor(INK_FAINT)
            c.drawString(left, cur_y, "See also:")
            label_end = left + c.stringWidth("See also: ", 'SerifBold', 8) + 2

            c.setFont('Serif', 8)
            c.setFillColor(INK_FAINT)
            first_w = right - label_end
            first_lines = self._wrap_text(cross_refs, 'Serif', 8, first_w)
            if first_lines:
                c.drawString(label_end, cur_y, first_lines[0])
                rest = cross_refs[len(first_lines[0]):].strip()
                cont_lines = self._wrap_text(rest, 'Serif', 8, text_w)
                for line in cont_lines:
                    if cur_y - 12 < stop_y:
                        break
                    cur_y -= 12
                    c.drawString(left, cur_y, line)

        # -- Insights (computed analysis, fills more space) --
        insights = verse.get('insights', '')
        if insights and cur_y - 28 > stop_y:
            cur_y -= 14
            c.setStrokeColor(DIVIDER)
            c.setLineWidth(0.5)
            c.setDash(3, 3)
            c.line(left, cur_y + 10, right, cur_y + 10)
            c.setDash()

            c.setFont('SerifBold', 8)
            c.setFillColor(INK_FAINT)
            c.drawString(left, cur_y, "Gematria Reflections:")
            label_end_ins = left + c.stringWidth("Gematria Reflections: ", 'SerifBold', 8) + 2

            c.setFont('Serif', 8)
            c.setFillColor(INK_FAINT)
            first_w = right - label_end_ins
            first_lines = self._wrap_text(insights, 'Serif', 8, first_w)
            if first_lines:
                c.drawString(label_end_ins, cur_y, heb_mixed(first_lines[0]))
                rest = insights[len(first_lines[0]):].strip()
                cont_lines = self._wrap_text(rest, 'Serif', 8, text_w)
                for line in cont_lines:
                    if cur_y - 12 < stop_y:
                        break
                    cur_y -= 12
                    c.drawString(left, cur_y, heb_mixed(line))

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

        # Primary English gloss (bold) — wrap to 2 lines if needed
        c.setFillColor(INK)
        eng_text = word.get('eng', '')
        eng_w = c.stringWidth(eng_text, 'SerifBold', 9)
        max_eng_w = w - 2*p

        if eng_w <= max_eng_w:
            # Fits on one line
            c.setFont('SerifBold', 9)
            c.drawCentredString(x + w/2, inner_y - 9, eng_text)
            inner_y -= 13
        else:
            # Try smaller font first
            eng_w_sm = c.stringWidth(eng_text, 'SerifBold', 7.5)
            if eng_w_sm <= max_eng_w:
                c.setFont('SerifBold', 7.5)
                c.drawCentredString(x + w/2, inner_y - 9, eng_text)
                inner_y -= 13
            else:
                # Wrap to two lines — split on middle dot or space
                parts = eng_text.replace('\u00b7', ' \u00b7 ').split()
                mid = len(parts) // 2
                line1 = ' '.join(parts[:mid]).replace(' \u00b7 ', '\u00b7')
                line2 = ' '.join(parts[mid:]).replace(' \u00b7 ', '\u00b7')
                c.setFont('SerifBold', 7.5)
                c.drawCentredString(x + w/2, inner_y - 8, truncate(line1, 'SerifBold', 7.5, max_eng_w, c))
                c.drawCentredString(x + w/2, inner_y - 17, truncate(line2, 'SerifBold', 7.5, max_eng_w, c))
                inner_y -= 21

        # Thin divider (always drawn — uniform across all cards)
        c.setStrokeColor(DIVIDER)
        c.setLineWidth(0.3)
        c.line(x + p + 5, inner_y, x + w - p - 5, inner_y)
        inner_y -= 2

        # Alternative meanings (smaller, lighter)
        meanings = word.get('meanings', [])
        if meanings:
            c.setFont('SerifItalic', 6.5)
            c.setFillColor(INK_FAINT)
            # Show up to 3 alternative meanings
            for i, meaning in enumerate(meanings[:3]):
                m_text = truncate(meaning, 'SerifItalic', 6.5, w - 2*p, c)
                c.drawCentredString(x + w/2, inner_y - 7, m_text)
                inner_y -= 9
        # Gematria badge — always anchored to bottom of card
        gem_y = y + p + 2  # fixed position near bottom
        gem_text = str(word.get('gem', 0))
        gem_w = max(c.stringWidth(gem_text, 'Serif', 7) + 10, 22)
        gem_x = x + (w - gem_w) / 2
        draw_rounded_rect(c, gem_x, gem_y, gem_w, 11, 5, fill=BLUE_BG, stroke=BLUE_BORDER)
        c.setFont('Serif', 7)
        c.setFillColor(BLUE_TEXT)
        c.drawCentredString(x + w/2, gem_y + 2, gem_text)

    # ─── Build ───────────────────────────────────────────────────────────

    def build(self, data, parasha_data=None):
        print(f"Building PDF: {len(data['chapters'])} chapters, {len(PARASHOT)} parashot...")

        # Index parasha data by name
        p_info = {}
        if parasha_data:
            for pi in parasha_data:
                p_info[pi['name']] = pi

        self.draw_title_page()

        drawn_parashot = set()
        for ch_data in data['chapters']:
            ch_num = ch_data['chapter']

            # Check if this chapter starts a new parasha — full title page
            for p in PARASHOT:
                if p['start'][0] == ch_num and p['name'] not in drawn_parashot:
                    self.draw_parasha_title(p, data, p_info.get(p['name']))
                    drawn_parashot.add(p['name'])
                    # Start fresh content page after parasha title
                    self.draw_footer()
                    self.new_page()
                    self.draw_header()
                    self.y = PAGE_H - MARGIN_T - 20
                    break

            print(f"  Chapter {ch_num}: {len(ch_data['verses'])} verses")

            # Inline chapter header (no full page)
            self.current_chapter = ch_num
            self.draw_chapter_title(ch_num)

            for verse in ch_data['verses']:
                self.draw_verse(verse)

        self.draw_footer()
        self.c.save()
        print(f"Done! {self.page_num} pages generated.")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "genesis_v3.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "genesis_pdf_v4.pdf"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load parasha data if available
    parasha_data = None
    parasha_file = Path(input_file).parent / 'parasha_data.json'
    if parasha_file.exists():
        with open(parasha_file, 'r', encoding='utf-8') as f:
            parasha_data = json.load(f)
        print(f"Loaded parasha data: {len(parasha_data)} parashot")

    print(f"Loaded {input_file}: {len(data['chapters'])} chapters")

    register_fonts()

    builder = PDFBuilder(output_file)
    builder.build(data, parasha_data)
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
