#!/usr/bin/env python3
"""
Unified Enrichment — Add insights to Torah books
==================================================
Adds to thin verses (< 2000 chars of commentary):
  1. Name etymologies
  2. Cantillation analysis
  3. Letter statistics

Usage:
  python enrich_torah_books.py exodus
  python enrich_torah_books.py all

Input:  books/torah/{book}_fixed.json
Output: modifies in-place (adds 'insights' field)
"""

import json, re, sys, unicodedata, math
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


def strip_niqqud(text):
    return ''.join(ch for ch in text if not (0x0591 <= ord(ch) <= 0x05BD or
            ord(ch) == 0x05BF or 0x05C1 <= ord(ch) <= 0x05C2 or
            0x05C4 <= ord(ch) <= 0x05C5 or ord(ch) == 0x05C7))


# ══════════════════════════════════════════════════════════════════════════
# ETYMOLOGIES — Torah-wide names
# ══════════════════════════════════════════════════════════════════════════

ETYMOLOGIES = {
    # Patriarchs/Matriarchs
    "Abraham": 'The name Abraham/Avraham ("father of multitudes") was expanded from Abram to signify his role as patriarch of many nations.',
    "Sarah": 'The name Sarah ("princess") derives from sar meaning "prince, ruler."',
    "Isaac": 'The name Isaac/Yitzchak ("he will laugh") derives from tzachak meaning "to laugh."',
    "Rebekah": 'The name Rebekah/Rivkah ("to bind, captivating") suggests beauty that ensnares.',
    "Jacob": 'The name Jacob/Yaakov ("heel-grasper, supplanter") derives from akev meaning "heel."',
    "Israel": 'The name Israel/Yisrael ("wrestles with God" or "prince of God") combines sarah ("to strive") with El ("God").',
    "Leah": 'The name Leah ("weary" or "wild cow") may reflect weariness or strength.',
    "Rachel": 'The name Rachel ("ewe, female sheep") evokes pastoral imagery.',
    "Joseph": 'The name Joseph/Yosef ("he will add") derives from yasaf meaning "to add."',

    # Tribes
    "Reuben": 'The name Reuben/Reuven ("see, a son!") combines ra\'ah ("to see") with ben ("son").',
    "Simeon": 'The name Simeon/Shimon ("hearing, he heard") derives from shama meaning "to hear."',
    "Levi": 'The name Levi ("attached, joined") derives from lavah meaning "to join."',
    "Judah": 'The name Judah/Yehudah ("praise") derives from yadah meaning "to praise, to thank."',
    "Dan": 'The name Dan ("judge") derives from din meaning "to judge."',
    "Naphtali": 'The name Naphtali ("my wrestling") derives from pathal meaning "to wrestle."',
    "Gad": 'The name Gad ("fortune, luck") signifies good fortune.',
    "Asher": 'The name Asher ("happy, blessed") derives from osher meaning "happiness."',
    "Issachar": 'The name Issachar/Yissachar ("reward, hired") derives from sachar meaning "wages."',
    "Zebulun": 'The name Zebulun/Zevulun ("dwelling, honor") derives from zaval meaning "to dwell."',
    "Benjamin": 'The name Benjamin/Binyamin ("son of the right hand") combines ben ("son") with yamin ("right hand").',
    "Manasseh": 'The name Manasseh/Menasheh ("causing to forget") derives from nashah meaning "to forget."',
    "Ephraim": 'The name Ephraim ("doubly fruitful") derives from parah meaning "to be fruitful."',

    # Exodus-specific
    "Moses": 'The name Moses/Moshe ("drawn out") derives from mashah meaning "to draw out" — "for I drew him out of the water."',
    "Aaron": 'The name Aaron/Aharon is of uncertain etymology, possibly meaning "mountain of strength" or "exalted."',
    "Miriam": 'The name Miriam may derive from mar meaning "bitter" or from meri meaning "rebellion."',
    "Pharaoh": 'The name Pharaoh is Egyptian, meaning "great house," the title of Egypt\'s ruler.',
    "Jethro": 'The name Jethro/Yitro ("his abundance") derives from yeter meaning "abundance, excellence."',
    "Zipporah": 'The name Zipporah/Tzipporah ("bird") derives from tzippor meaning "bird."',
    "Gershom": 'The name Gershom ("stranger there") reflects Moses\'s words: "I have been a stranger in a foreign land."',
    "Eliezer": 'The name Eliezer ("my God is help") combines El ("God") with ezer ("help").',
    "Bezalel": 'The name Bezalel/Betzalel ("in the shadow of God") combines betzel ("in the shadow") with El ("God").',
    "Oholiab": 'The name Oholiab/Aholiav ("tent of the father") combines ohel ("tent") with av ("father").',
    "Joshua": 'The name Joshua/Yehoshua ("God is salvation") combines the divine name with yasha ("to save").',
    "Caleb": 'The name Caleb/Kalev ("dog" or "whole-hearted") may signify devotion or faithfulness.',
    "Korach": 'The name Korach ("bald" or "ice") derives from kerach meaning "frost, ice."',
    "Balaam": 'The name Balaam/Bilam ("destroyer of the people" or "lord of the people") combines bala ("to swallow") with am ("people").',
    "Balak": 'The name Balak ("devastator") derives from balak meaning "to lay waste."',
    "Pinchas": 'The name Pinchas/Phinehas is possibly Egyptian, meaning "the Nubian" or "dark-skinned."',
    "Zelophehad": 'The name Zelophehad/Tzelafchad is of uncertain meaning, possibly "shadow of fear."',

    # Places
    "Sinai": 'The name Sinai may derive from the word seneh ("bush"), recalling the burning bush.',
    "Horeb": 'The name Horeb/Chorev ("desolation, dryness") describes the arid mountain landscape.',
    "Egypt": 'The name Egypt/Mitzrayim ("narrow places, double straits") may reflect geographical or spiritual constriction.',
    "Canaan": 'The name Canaan/Kenaan ("lowland" or "merchant") designates both the land and its people.',
    "Midian": 'The name Midian ("strife") derives from the root meaning "to contend."',
    "Goshen": 'The name Goshen possibly means "drawing near."',
    "Jordan": 'The name Jordan/Yarden ("descender") derives from yarad meaning "to descend."',
    "Kadesh": 'The name Kadesh ("holy") derives from kadosh meaning "holy, set apart."',
    "Moab": 'The name Moab ("from the father") combines mo ("from") with av ("father").',
    "Edom": 'The name Edom ("red") derives from adom meaning "red," recalling Esau\'s complexion.',
    "Gilgal": 'The name Gilgal ("circle of stones" or "rolling") derives from galal meaning "to roll."',
}

NAME_HEBREW_MAP = {
    "Abraham": ["אברהם"], "Sarah": ["שרה"], "Isaac": ["יצחק"],
    "Rebekah": ["רבקה"], "Jacob": ["יעקב"], "Israel": ["ישראל"],
    "Leah": ["לאה"], "Rachel": ["רחל"], "Joseph": ["יוסף"],
    "Reuben": ["ראובן"], "Simeon": ["שמעון"], "Levi": ["לוי"],
    "Judah": ["יהודה"], "Dan": ["דן"], "Naphtali": ["נפתלי"],
    "Gad": ["גד"], "Asher": ["אשר"], "Issachar": ["יששכר"],
    "Zebulun": ["זבולון", "זבולן"], "Benjamin": ["בנימין", "בנימן"],
    "Manasseh": ["מנשה"], "Ephraim": ["אפרים"],
    "Moses": ["משה"], "Aaron": ["אהרן"], "Miriam": ["מרים"],
    "Pharaoh": ["פרעה"], "Jethro": ["יתרו"], "Zipporah": ["צפרה"],
    "Gershom": ["גרשם", "גרשום"], "Eliezer": ["אליעזר"],
    "Bezalel": ["בצלאל"], "Oholiab": ["אהליאב"],
    "Joshua": ["יהושע"], "Caleb": ["כלב"],
    "Korach": ["קרח"], "Balaam": ["בלעם"], "Balak": ["בלק"],
    "Pinchas": ["פנחס", "פינחס"], "Zelophehad": ["צלפחד"],
    "Sinai": ["סיני"], "Horeb": ["חרב", "חורב"],
    "Egypt": ["מצרים"], "Canaan": ["כנען"], "Midian": ["מדין"],
    "Jordan": ["ירדן"], "Kadesh": ["קדש"], "Moab": ["מואב"],
    "Edom": ["אדום"], "Gilgal": ["גלגל"],
}

AMBIGUOUS_NAMES = {
    "Asher": {"which", "who", "that", "whom", "because", "happy", "as", "in"},
    "Dan": {"judged", "judge", "judges", "judging"},
    "Gad": {"fortune", "troop"},
    "Levi": {"joined", "attached"},
    "Judah": {"praise", "praised", "praising"},
    "Rachel": {"ewe", "sheep"},
    "Caleb": {"dog"},
    "Israel": {"wrestles", "strives"},
    "Egypt": {"narrow"},
}


# ══════════════════════════════════════════════════════════════════════════
# CANTILLATION ANALYSIS
# ══════════════════════════════════════════════════════════════════════════

DISJUNCTIVE = {
    '\u0591': 'Etnachta', '\u0592': 'Segol', '\u0593': 'Shalshelet',
    '\u0594': 'Zaqef Qatan', '\u0595': 'Zaqef Gadol', '\u0596': 'Tipecha',
    '\u0597': 'Revia', '\u0598': 'Zarqa', '\u0599': 'Pashta',
    '\u059A': 'Yetiv', '\u059B': 'Tevir', '\u059C': 'Geresh',
    '\u059D': 'Geresh Muqdam', '\u059E': 'Gershayim', '\u059F': 'Qarney Para',
    '\u05A0': 'Telisha Gedola', '\u05A1': 'Pazer', '\u05AA': 'Yerah Ben Yomo',
}

CONJUNCTIVE = {
    '\u05A3': 'Munach', '\u05A4': 'Mahapakh', '\u05A5': 'Merkha',
    '\u05A6': 'Merkha Kefula', '\u05A7': 'Darga', '\u05A8': 'Qadma',
    '\u05A9': 'Telisha Qetana', '\u05AB': 'Ole',
}

GEMATRIA_MAP = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50,
    'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400,
}


def get_cantillation_marks(heb_word):
    marks = []
    for ch in heb_word:
        cp = ord(ch)
        if 0x0591 <= cp <= 0x05AF or cp == 0x05C3:
            marks.append(ch)
    return marks


def analyze_cantillation(verse):
    """Analyze cantillation patterns in a verse."""
    words = verse.get('words', [])
    if len(words) < 3:
        return ""

    disj_count = 0
    conj_count = 0
    disj_names = Counter()
    notable = []

    for w in words:
        marks = get_cantillation_marks(w.get('heb', ''))
        for m in marks:
            if m in DISJUNCTIVE:
                disj_count += 1
                disj_names[DISJUNCTIVE[m]] += 1
                if m == '\u0593':  # Shalshelet — rare and significant
                    notable.append(f'The rare Shalshelet cantillation appears on "{w["eng"]}", indicating hesitation or dramatic emphasis.')
            elif m in CONJUNCTIVE:
                conj_count += 1

    if disj_count + conj_count < 3:
        return ""

    parts = []
    if notable:
        parts.extend(notable)

    if disj_count > 0:
        top_disj = disj_names.most_common(3)
        disj_desc = ', '.join(f'{name} ({count})' for name, count in top_disj)
        parts.append(f'This verse has {disj_count} disjunctive and {conj_count} conjunctive cantillation marks. Primary pauses: {disj_desc}.')

    return ' '.join(parts)


def analyze_letters(verse):
    """Generate letter statistics for a verse."""
    words = verse.get('words', [])
    all_heb = ''.join(w.get('heb', '') for w in words)
    consonants = strip_niqqud(all_heb).replace('\u05BE', '').replace(' ', '')

    if len(consonants) < 10:
        return ""

    letter_counts = Counter(consonants)
    total = sum(letter_counts.values())
    most_common = letter_counts.most_common(3)

    # Check for interesting patterns
    parts = []
    mc_letter, mc_count = most_common[0]
    pct = 100 * mc_count / total
    if pct > 15:
        gem = GEMATRIA_MAP.get(mc_letter, 0)
        parts.append(f'The letter {mc_letter} (gematria {gem}) appears {mc_count} times ({pct:.0f}% of {total} letters), the most frequent in this verse.')

    # Total gematria
    total_gem = sum(GEMATRIA_MAP.get(c, 0) for c in consonants)
    if total_gem > 0:
        # Check for notable gematria values
        if total_gem % 7 == 0:
            parts.append(f'The verse\'s total gematria is {total_gem}, divisible by 7 (the number of completion).')
        elif total_gem % 26 == 0:
            parts.append(f'The verse\'s total gematria is {total_gem}, divisible by 26 (the gematria of God\'s name).')

    return ' '.join(parts)


# ══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════

COMMENTARY_FIELDS = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
                     'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar']


def get_content_length(verse):
    total = 0
    for fld in COMMENTARY_FIELDS + ['insights', 'gem_note', 'cross_refs']:
        val = verse.get(fld, '')
        if val:
            total += len(str(val))
    return total


def is_name_usage(name, eng):
    if name not in AMBIGUOUS_NAMES:
        return True
    eng_lower = eng.lower().strip()
    for pfx in ["and·", "the·", "of·", "in·", "to·", "from·"]:
        if eng_lower.startswith(pfx):
            eng_lower = eng_lower[len(pfx):]
    if eng_lower in AMBIGUOUS_NAMES[name]:
        return False
    if name.lower() in eng.lower():
        return True
    return True


def find_names_in_verse(verse):
    found = []
    seen = set()
    for w in verse.get('words', []):
        heb = strip_niqqud(w.get('heb', '')).replace('\u05BE', '')
        eng = w.get('eng', '')
        for name, forms in NAME_HEBREW_MAP.items():
            for form in forms:
                if heb == form.replace('\u05BE', '') and is_name_usage(name, eng):
                    etym = ETYMOLOGIES.get(name, '')
                    if etym and etym not in seen:
                        found.append(name)
                        seen.add(etym)
                    break
    return found


def enrich_book(book_key):
    filepath = BOOK_FILES[book_key]
    if not filepath.exists():
        print(f"ERROR: {filepath} not found")
        return

    print(f"\n{'=' * 50}")
    print(f"  Enriching: {book_key.title()}")
    print(f"{'=' * 50}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = 0
    thin = 0
    enriched = 0

    for ch in data['chapters']:
        for v in ch['verses']:
            total += 1
            content_len = get_content_length(v)

            if content_len >= 2000:
                continue
            thin += 1

            insights_parts = []

            # 1. Etymologies
            names = find_names_in_verse(v)
            if names:
                for name in names[:3]:  # Max 3 per verse
                    etym = ETYMOLOGIES.get(name, '')
                    if etym:
                        insights_parts.append(etym)

            # 2. Cantillation analysis
            cant = analyze_cantillation(v)
            if cant:
                insights_parts.append(cant)

            # 3. Letter statistics (only if still thin)
            if content_len + sum(len(p) for p in insights_parts) < 1500:
                letters = analyze_letters(v)
                if letters:
                    insights_parts.append(letters)

            if insights_parts:
                existing = v.get('insights', '') or ''
                new_insights = ' '.join(insights_parts)
                if existing:
                    v['insights'] = existing.rstrip() + ' ' + new_insights
                else:
                    v['insights'] = new_insights
                enriched += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Total verses: {total}")
    print(f"  Thin verses:  {thin}")
    print(f"  Enriched:     {enriched}")


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or 'all' in args:
        books = list(BOOK_FILES.keys())
    else:
        books = [a for a in args if a in BOOK_FILES]

    for book_key in books:
        enrich_book(book_key)


if __name__ == '__main__':
    main()
