#!/usr/bin/env python3
"""
Universal Gloss Fixer — Works on any Torah book
=================================================
Applies master corrections dictionary, strips HTML, fixes dictionary defs,
cleans jargon, fixes vav-consecutive verbs, merges fragments, and
shortens long glosses.

Combines: deep_fix_glosses + fix_jargon + fix_vav_verbs + fix_fragments +
          fix_reader_friendly + fix_long_glosses

Usage:
  python fix_book_glosses.py exodus
  python fix_book_glosses.py leviticus numbers deuteronomy
  python fix_book_glosses.py all

Input:  books/torah/{book}_fixed.json (from rebuild_book.py)
Output: books/torah/{book}_fixed.json (in-place)
"""

import json, re, sys, html as htmlmod
from pathlib import Path
from collections import Counter

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

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)


# ══════════════════════════════════════════════════════════════════════════
# MASTER GLOSS DICTIONARY — Universal Biblical Hebrew
# ══════════════════════════════════════════════════════════════════════════

GLOSS_FIXES = {
    # ─── WRONG TRANSLATIONS (highest priority) ───
    'כי': 'because',  'וכי': 'and·because',
    'הוא': 'he', 'והוא': 'and·he', 'ההוא': 'that', 'ההיא': 'that',
    'היא': 'she', 'והיא': 'and·she',
    'בן': 'son', 'בנו': 'his·son', 'בני': 'sons·of', 'בנים': 'sons',
    'ובני': 'and·sons·of', 'ובנו': 'and·his·son',
    'בנות': 'daughters', 'בנותי': 'my·daughters', 'בנותיך': 'your·daughters',
    'בת': 'daughter', 'בתו': 'his·daughter',
    'אל': 'to', 'ואל': 'and·to',
    'אליו': 'to·him', 'אליה': 'to·her', 'אליהם': 'to·them',
    'אלי': 'to·me', 'אליך': 'to·you', 'אלינו': 'to·us',
    'שנה': 'year', 'שנים': 'years', 'שני': 'two',
    'שנת': 'year·of', 'שנותיו': 'years·of',
    'עד': 'until', 'ועד': 'and·until',
    'ימים': 'days', 'הימים': 'the·days', 'ימי': 'days·of',
    'שם': 'there', 'שמו': 'his·name', 'שמה': 'her·name',
    'שמם': 'their·name', 'בשם': 'in·the·name·of',
    'עוד': 'yet', 'ועוד': 'and·still',

    # ─── OBJECT MARKERS ───
    'את': '(object marker)', 'ואת': 'and·(object marker)',
    'אתו': '(object marker)·him', 'אתם': '(object marker)·them',
    'אתי': '(object marker)·me', 'אתך': '(object marker)·you',
    'אתכם': '(object marker)·you(pl)', 'אתנו': '(object marker)·us',
    'אותו': '(object marker)·him', 'אותם': '(object marker)·them',
    'אותי': '(object marker)·me', 'אותך': '(object marker)·you',
    'אותנו': '(object marker)·us',

    # ─── PRONOUNS & PREPOSITIONS ───
    'לי': 'to·me', 'לו': 'to·him', 'לה': 'to·her',
    'להם': 'to·them', 'לנו': 'to·us', 'לך': 'to·you', 'לכם': 'to·you(pl)',
    'בו': 'in·him', 'בה': 'in·her', 'בם': 'in·them', 'בי': 'in·me',
    'לפני': 'before', 'לפניו': 'before·him',
    'לפניך': 'before·you', 'לפניהם': 'before·them',
    'אנכי': 'I', 'אני': 'I', 'אתה': 'you', 'אנחנו': 'we',
    'הם': 'they', 'הן': 'they(f)',
    'זה': 'this', 'הזה': 'this', 'הזאת': 'this', 'זאת': 'this',
    'אלה': 'these', 'ואלה': 'and·these',
    'ועתה': 'and·now', 'עתה': 'now',
    'מה': 'what', 'למה': 'why',
    'הנה': 'behold', 'והנה': 'and·behold',
    'על': 'upon', 'עליו': 'upon·him', 'עלי': 'upon·me',
    'עליהם': 'upon·them', 'עליך': 'upon·you',
    'עליה': 'upon·her', 'עלינו': 'upon·us',
    'כן': 'so', 'גם': 'also',
    'לא': 'not', 'ולא': 'and·not',
    'אם': 'if', 'ואם': 'and·if',
    'בין': 'between', 'ובין': 'and·between',
    'מעל': 'above', 'מתחת': 'from·beneath',
    'עם': 'with', 'עמו': 'with·him', 'עמי': 'with·me', 'עמך': 'with·you',
    'ממנו': 'from·him', 'ממנה': 'from·her', 'מהם': 'from·them',
    'ממני': 'from·me', 'ממך': 'from·you',
    'בתוך': 'in·the·midst·of', 'מתוך': 'from·the·midst·of',
    'אחרי': 'after', 'אחריו': 'after·him',
    'תחת': 'under', 'תחתיו': 'under·him',

    # ─── COMMON VERBS (past tense for interlinear) ───
    'ויאמר': 'and·said', 'ויאמרו': 'and·they·said',
    'ותאמר': 'and·she·said', 'אמר': 'said', 'לאמר': 'saying',
    'ויהי': 'and·it·was', 'והיה': 'and·it·shall·be',
    'היה': 'was', 'היתה': 'was', 'יהי': 'let·there·be',
    'ויעש': 'and·made', 'עשה': 'made',
    'ויקרא': 'and·called', 'וירא': 'and·saw',
    'ויבא': 'and·came', 'ויבאו': 'and·they·came',
    'ויקח': 'and·took', 'ויתן': 'and·gave',
    'ותלד': 'and·she·bore', 'ויולד': 'and·begot', 'וילד': 'and·begot',
    'ויחי': 'and·lived', 'וימת': 'and·died',
    'וישב': 'and·dwelt', 'וישלח': 'and·sent',
    'ויצא': 'and·went·out', 'וילך': 'and·went', 'וילכו': 'and·they·went',
    'ויקם': 'and·arose', 'וישם': 'and·placed',
    'וידבר': 'and·spoke', 'ויברך': 'and·blessed',
    'וישמע': 'and·heard', 'ויקרב': 'and·drew·near',
    'ויען': 'and·answered', 'ויעל': 'and·went·up',
    'וירד': 'and·went·down', 'ויסע': 'and·journeyed',
    'ויבן': 'and·built', 'וישתחו': 'and·bowed·down',
    'ויפל': 'and·fell', 'ויבך': 'and·wept',
    'ויעבר': 'and·passed·over', 'ויחל': 'and·began',
    'וידע': 'and·knew', 'ויברח': 'and·fled',
    'ויכתב': 'and·wrote', 'וישפט': 'and·judged',
    'וימלך': 'and·reigned', 'ויצו': 'and·commanded',

    # ─── NOUNS ───
    'ארץ': 'land', 'הארץ': 'the·earth', 'בארץ': 'in·the·land',
    'מארץ': 'from·the·land', 'ארצה': 'to·the·land',
    'שמים': 'heavens', 'השמים': 'the·heavens',
    'מים': 'water', 'המים': 'the·waters',
    'יום': 'day', 'היום': 'the·day', 'ביום': 'on·the·day',
    'בקר': 'morning', 'ערב': 'evening',
    'אור': 'light', 'האור': 'the·light', 'חשך': 'darkness',
    'איש': 'man', 'האיש': 'the·man',
    'אשה': 'woman', 'האשה': 'the·woman', 'אשתו': 'his·wife',
    'האדם': 'the·man', 'אדם': 'man',
    'אב': 'father', 'אביו': 'his·father', 'אבי': 'father·of',
    'אביך': 'your·father', 'אביכם': 'your·father',
    'אם': 'mother', 'אמו': 'his·mother',
    'אח': 'brother', 'אחיו': 'his·brother', 'אחי': 'brother·of', 'אחיך': 'your·brother',
    'עבד': 'servant', 'עבדיו': 'his·servants', 'עבדך': 'your·servant', 'עבדי': 'my·servant',
    'עיר': 'city', 'בית': 'house', 'הבית': 'the·house', 'ביתו': 'his·house',
    'דבר': 'word', 'הדברים': 'the·words', 'דברי': 'words·of',
    'עין': 'eye', 'עיני': 'eyes·of',
    'בעיני': 'in·the·eyes·of', 'בעיניו': 'in·his·eyes', 'בעיניך': 'in·your·eyes',
    'יד': 'hand', 'ידו': 'his·hand', 'ידי': 'hands·of',
    'בידו': 'in·his·hand', 'ביד': 'in·the·hand·of',
    'לב': 'heart', 'לבו': 'his·heart', 'לבב': 'heart',
    'נפש': 'soul', 'כל': 'all', 'וכל': 'and·all',
    'לכל': 'to·all', 'מכל': 'from·all', 'בכל': 'in·all',
    'מאד': 'very', 'אשר': 'which', 'כאשר': 'as', 'באשר': 'in·which',
    'ראש': 'head', 'רגל': 'foot', 'פה': 'mouth',
    'מאה': 'hundred', 'מאות': 'hundreds',
    'אלף': 'thousand', 'אלפים': 'thousands',
    'רעה': 'evil', 'ברית': 'covenant', 'בריתי': 'my·covenant',
    'חטאת': 'sin', 'עון': 'iniquity',
    'משפט': 'judgment', 'חק': 'statute', 'חקה': 'statute',
    'מצוה': 'commandment', 'תורה': 'Torah',
    'כהן': 'priest', 'הכהן': 'the·priest', 'כהנים': 'priests',
    'עלה': 'burnt·offering', 'מנחה': 'grain·offering',
    'שלמים': 'peace·offering', 'חטאת': 'sin·offering',
    'משכן': 'tabernacle', 'אהל': 'tent', 'מועד': 'meeting',
    'ארון': 'ark', 'הארן': 'the·ark',
    'מזבח': 'altar', 'המזבח': 'the·altar',
    'דם': 'blood', 'הדם': 'the·blood',
    'חרב': 'sword', 'מטה': 'staff',

    # ─── GOD'S NAME ───
    'יהוה': 'LORD',
    'אלהים': 'God', 'האלהים': 'God',
    'אלהי': 'God·of', 'אלהיך': 'your·God',
    'אלהיו': 'his·God', 'אלהיהם': 'their·God',
    'אלהינו': 'our·God', 'אדני': 'my·Lord',

    # ─── NAMES (shared across Torah) ───
    'אברהם': 'Abraham', 'ואברהם': 'and·Abraham',
    'לאברהם': 'to·Abraham', 'אלאברהם': 'to·Abraham',
    'יצחק': 'Isaac', 'ליצחק': 'to·Isaac',
    'יעקב': 'Jacob', 'ויעקב': 'and·Jacob',
    'ליעקב': 'to·Jacob', 'אליעקב': 'to·Jacob',
    'יוסף': 'Joseph', 'ליוסף': 'to·Joseph',
    'ישראל': 'Israel', 'לישראל': 'to·Israel', 'בישראל': 'in·Israel',
    'בניישראל': 'children·of·Israel',
    'פרעה': 'Pharaoh', 'לפרעה': 'to·Pharaoh', 'אלפרעה': 'to·Pharaoh',
    'מצרים': 'Egypt', 'מצרימה': 'to·Egypt',
    'ממצרים': 'from·Egypt', 'במצרים': 'in·Egypt',
    'כנען': 'Canaan', 'בכנען': 'in·Canaan',
    'משה': 'Moses', 'למשה': 'to·Moses', 'אלמשה': 'to·Moses',
    'אהרן': 'Aaron', 'לאהרן': 'to·Aaron', 'אלאהרן': 'to·Aaron',
    'ראובן': 'Reuben', 'שמעון': 'Simeon', 'לוי': 'Levi',
    'יהודה': 'Judah', 'דן': 'Dan', 'נפתלי': 'Naphtali',
    'גד': 'Gad', 'זבולן': 'Zebulun', 'בנימין': 'Benjamin',
    'יששכר': 'Issachar', 'מנשה': 'Manasseh', 'אפרים': 'Ephraim',
    'סיני': 'Sinai', 'חרב': 'Horeb',
    'מדין': 'Midian', 'במדבר': 'in·the·wilderness',
    'ירדן': 'Jordan', 'הירדן': 'the·Jordan',
}


# ══════════════════════════════════════════════════════════════════════════
# VAV-CONSECUTIVE VERB FIXES
# ══════════════════════════════════════════════════════════════════════════

VAV_PAST = {
    'to say': 'said', 'to speak': 'spoke', 'to call': 'called',
    'to see': 'saw', 'to hear': 'heard', 'to know': 'knew',
    'to go': 'went', 'to come': 'came', 'to take': 'took',
    'to give': 'gave', 'to make': 'made', 'to do': 'did',
    'to be': 'was', 'to go out': 'went·out', 'to go up': 'went·up',
    'to go down': 'went·down', 'to fall': 'fell', 'to rise': 'arose',
    'to stand': 'stood', 'to sit': 'sat', 'to lie down': 'lay·down',
    'to send': 'sent', 'to build': 'built', 'to write': 'wrote',
    'to eat': 'ate', 'to drink': 'drank', 'to die': 'died',
    'to kill': 'killed', 'to bear': 'bore', 'to conceive': 'conceived',
    'to turn': 'turned', 'to return': 'returned', 'to flee': 'fled',
    'to find': 'found', 'to put': 'put', 'to set': 'set',
    'to burn': 'burned', 'to keep': 'kept', 'to serve': 'served',
    'to pass over': 'passed·over', 'to judge': 'judged',
    'to command': 'commanded', 'to swear': 'swore',
    'to bless': 'blessed', 'to curse': 'cursed',
    'to gather': 'gathered', 'to draw near': 'drew·near',
    'to stretch out': 'stretched·out', 'to strike': 'struck',
    'to smite': 'smote', 'to reign': 'reigned',
    'to count': 'counted', 'to cover': 'covered',
    'to break': 'broke', 'to cut': 'cut',
    'to plant': 'planted', 'to open': 'opened', 'to close': 'closed',
    'to carry': 'carried', 'to bring': 'brought',
    'to lead': 'led', 'to fight': 'fought',
    'to meet': 'met', 'to touch': 'touched',
    'to prevail': 'prevailed', 'to multiply': 'multiplied',
    'to fear': 'feared', 'to love': 'loved', 'to hate': 'hated',
    'to cry': 'cried', 'to weep': 'wept',
    'to hide': 'hid', 'to run': 'ran',
    'to dwell': 'dwelt', 'to camp': 'camped',
    'to number': 'numbered', 'to offer': 'offered',
    'to sanctify': 'sanctified', 'to sprinkle': 'sprinkled',
    'to anoint': 'anointed', 'to slaughter': 'slaughtered',
    'to wash': 'washed', 'to pour': 'poured',
}


# ══════════════════════════════════════════════════════════════════════════
# FIX PIPELINE
# ══════════════════════════════════════════════════════════════════════════

def fix_book(book_key):
    filepath = BOOK_FILES[book_key]
    if not filepath.exists():
        print(f"ERROR: {filepath} not found. Run rebuild_book.py first.")
        return

    print(f"\n{'=' * 60}")
    print(f"  Fixing glosses: {book_key.title()}")
    print(f"{'=' * 60}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = Counter()

    for ch in data['chapters']:
        for v in ch['verses']:
            for w in v.get('words', []):
                key = strip_n(w['heb']).replace('\u05BE', '')
                eng = w['eng']
                original = eng

                # ── Pass 1: Master dictionary ──
                if key in GLOSS_FIXES:
                    correct = GLOSS_FIXES[key]
                    if eng != correct:
                        w['eng'] = correct
                        stats['master_dict'] += 1
                        continue

                # ── Pass 2: HTML cleanup ──
                if '<a ' in eng or 'href' in eng or 'class=' in eng or '</' in eng or '<i>' in eng:
                    clean = re.sub(r'<[^>]*>.*', '', eng).strip()
                    clean = re.sub(r'\(f\.\s*$', '', clean).strip()
                    w['eng'] = clean if clean and len(clean) > 1 else eng.split('<')[0].strip()
                    if '&' in w['eng']:
                        w['eng'] = htmlmod.unescape(w['eng'])
                    stats['html'] += 1
                    continue

                # ── Pass 3: Dictionary etymology cleanup ──
                # "Name = "meaning"" → "Name"
                m = re.match(r'^([A-Z][a-z]+(?:\s*or\s*[A-Z][a-z]+)?)\s*=\s*"', eng)
                if m:
                    w['eng'] = m.group(1).split(' or ')[0].strip()
                    stats['dict_etym'] += 1
                    continue

                # Compound: "word·Name = "meaning""
                if '=' in eng and '"' in eng:
                    parts = eng.split('\u00B7')
                    cleaned = []
                    for p in parts:
                        m2 = re.match(r'^([A-Z][a-z]+)\s*=\s*"', p)
                        if m2:
                            cleaned.append(m2.group(1))
                        elif '=' not in p:
                            cleaned.append(p)
                        else:
                            cleaned.append(p.split('=')[0].strip().strip('"'))
                    w['eng'] = '\u00B7'.join(cleaned)
                    stats['dict_etym'] += 1
                    continue

                # ── Pass 4: "Commonly transcribed YHWH" ──
                if 'Commonly transcribed' in eng or eng == 'Commonly transcribed YHWH':
                    w['eng'] = 'LORD'
                    stats['yhwh'] += 1
                    continue

                # ── Pass 5: Trailing periods ──
                if eng.endswith('.') and not eng.endswith('...'):
                    w['eng'] = eng.rstrip('.')
                    stats['period'] += 1

                # ── Pass 6: Academic jargon ──
                if eng in ('adj', 'adv', 'subst', 'n m', 'n f', 'n m/f', 'vb', 'v',
                           'prep', 'conj', 'pron', 'interj', 'n pr m', 'n pr', 'n pr f',
                           'n pr loc', 'pron 3p s'):
                    # Try to resolve from ETCBC or leave for manual fix
                    if eng == 'pron 3p s':
                        w['eng'] = 'he'
                    elif eng in ('adj', 'adv', 'subst', 'n m', 'n f', 'vb', 'v', 'prep', 'conj', 'pron'):
                        # Leave as-is — rebuild_book should have caught these
                        pass
                    stats['jargon'] += 1
                    continue

                if 'inflected' in eng:
                    for pronoun in ['to me', 'to you', 'to us', 'to him', 'to her', 'to them']:
                        if pronoun in eng:
                            w['eng'] = pronoun.replace(' ', '\u00B7')
                            break
                    else:
                        w['eng'] = eng.split('.')[0].strip()
                    stats['jargon'] += 1
                    continue

                # ── Pass 7: "sign of the definite direct object" ──
                if eng.startswith('sign of the definite'):
                    w['eng'] = '(object marker)'
                    stats['obj_mark'] += 1
                    continue

                # ── Pass 8: Vav-consecutive verbs ──
                heb_cons = key
                if heb_cons and (heb_cons.startswith('וי') or heb_cons.startswith('ות')
                                 or heb_cons.startswith('ונ') or heb_cons.startswith('וא')):
                    eng_lower = eng.lower().strip()
                    if eng_lower in VAV_PAST:
                        w['eng'] = 'and·' + VAV_PAST[eng_lower]
                        stats['vav_verb'] += 1
                        continue
                    elif eng_lower.startswith('to ') and eng_lower in VAV_PAST:
                        w['eng'] = 'and·' + VAV_PAST[eng_lower]
                        stats['vav_verb'] += 1
                        continue

                # ── Pass 9: Parenthetical cleanup ──
                if '(' in eng and ')' in eng:
                    stripped = re.sub(r'\s*\([^)]*\)\s*', ' ', eng).strip()
                    if stripped and len(stripped) >= 2:
                        w['eng'] = stripped
                        stats['parens'] += 1

                # ── Pass 10: Long gloss shortening ──
                if len(w['eng']) > 25:
                    e = w['eng']
                    # "X or Y" → "X"
                    if ' or ' in e:
                        e = e.split(' or ')[0].strip()
                    # "to be or become X" → "be·X"
                    e = re.sub(r'^to be or become\s+', 'be·', e)
                    e = re.sub(r'^to cause to\s+', '', e)
                    if len(e) < len(w['eng']):
                        w['eng'] = e
                        stats['shorten'] += 1

    # ── Second pass: remaining HTML ──
    for ch in data['chapters']:
        for v in ch['verses']:
            for w in v.get('words', []):
                if '<' in w['eng']:
                    w['eng'] = re.sub(r'<[^>]*>', '', w['eng']).strip()
                    if '&' in w['eng']:
                        w['eng'] = htmlmod.unescape(w['eng'])
                    stats['html_pass2'] += 1

    # ── Save ──
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_words = sum(len(v.get('words', [])) for ch in data['chapters'] for v in ch['verses'])
    total_fixes = sum(stats.values())
    still_empty = sum(1 for ch in data['chapters'] for v in ch['verses']
                      for w in v.get('words', []) if not w['eng'])
    still_jargon = sum(1 for ch in data['chapters'] for v in ch['verses']
                       for w in v.get('words', [])
                       if w['eng'] in ('adj', 'adv', 'subst', 'n m', 'n f', 'vb', 'v', 'prep', 'nm'))
    still_html = sum(1 for ch in data['chapters'] for v in ch['verses']
                     for w in v.get('words', []) if '<' in w['eng'])

    print(f"\n  Results for {book_key.title()}:")
    print(f"  Total words:    {total_words}")
    print(f"  Total fixes:    {total_fixes}")
    for k, v in stats.most_common():
        print(f"    {k:15s}: {v}")
    print(f"  Still empty:    {still_empty}")
    print(f"  Still jargon:   {still_jargon}")
    print(f"  Still HTML:     {still_html}")

    return stats


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or 'all' in args:
        books = ['exodus', 'leviticus', 'numbers', 'deuteronomy']
    else:
        books = [a for a in args if a in BOOK_FILES]

    for book_key in books:
        fix_book(book_key)


if __name__ == '__main__':
    main()
