#!/usr/bin/env python3
"""Deep fix of all glosses in genesis.json — corrects wrong translations,
cleans HTML leaks, fixes dictionary definitions, and normalizes format."""
import json, re, sys, html as htmlmod
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# ─── Master corrections dictionary ─────────────────────────────────────
# Format: consonantal_key -> correct_gloss
# These override whatever Sefaria gave us

GLOSS_FIXES = {
    # === WRONG TRANSLATIONS (highest priority) ===
    # כי = "because/that/for" NOT "burning"
    'כי': 'because',
    'וכי': 'and·because',
    # הוא = "he" NOT "you"
    'הוא': 'he',
    'והוא': 'and·he',
    'ההוא': 'that',
    'ההיא': 'that',
    # היא = "she"
    'היא': 'she',
    'והיא': 'and·she',
    # בן = "son" NOT "between"
    'בן': 'son',
    'בנו': 'his·son',
    'בני': 'sons·of',
    'בנים': 'sons',
    'ובני': 'and·sons·of',
    'ובנו': 'and·his·son',
    'בנות': 'daughters',
    'בנותי': 'my·daughters',
    'בנותיך': 'your·daughters',
    # אל = "to/unto" NOT "ram"
    'אל': 'to',
    'ואל': 'and·to',
    'אליו': 'to·him',
    'אליה': 'to·her',
    'אליהם': 'to·them',
    'אלי': 'to·me',
    'אליך': 'to·you',
    'אלינו': 'to·us',
    # שנה/שנים = "year/years" NOT "to repeat"
    'שנה': 'year',
    'שנים': 'years',
    'שני': 'two',
    'שנת': 'year·of',
    'שנותיו': 'years·of',
    # עד = "until/as far as" NOT "perpetuity"
    'עד': 'until',
    'ועד': 'and·until',
    # ימים = "days" NOT "sea"
    'ימים': 'days',
    'הימים': 'the·days',
    'ימי': 'days·of',
    # שם = context-dependent but mostly "name" or "there"
    'שם': 'there',
    'שמו': 'his·name',
    'שמה': 'her·name',
    'שמם': 'their·name',
    'בשם': 'in·the·name·of',
    'לשם': 'to·Shem',
    # לבן = "Laban" in Genesis context NOT "white"
    'לבן': 'Laban',
    'ללבן': 'to·Laban',
    # עוד = "still/yet/again" NOT "to be"
    'עוד': 'yet',
    'ועוד': 'and·still',
    # ויצא = "and went out" NOT "David"
    'ויצא': 'and·went·out',

    # === OBJECT MARKERS ===
    'את': '[obj.mark]',
    'ואת': 'and·[obj.mark]',
    'אתו': '[obj.mark]·him',
    'אתם': '[obj.mark]·them',
    'אתי': '[obj.mark]·me',
    'אתך': '[obj.mark]·you',
    'אתכם': '[obj.mark]·you(pl)',
    'אתנו': '[obj.mark]·us',
    'אותו': '[obj.mark]·him',
    'אותם': '[obj.mark]·them',
    'אותי': '[obj.mark]·me',
    'אותך': '[obj.mark]·you',
    'אותנו': '[obj.mark]·us',

    # === PRONOUNS & PREPOSITIONS ===
    'לי': 'to·me',
    'לו': 'to·him',
    'לה': 'to·her',
    'להם': 'to·them',
    'לנו': 'to·us',
    'לך': 'to·you',
    'לכם': 'to·you(pl)',
    'בו': 'in·him',
    'בה': 'in·her',
    'בם': 'in·them',
    'בי': 'in·me',
    'לפני': 'before',
    'לפניו': 'before·him',
    'לפניך': 'before·you',
    'לפניהם': 'before·them',
    'אנכי': 'I',
    'אני': 'I',
    'אתה': 'you',
    'אנחנו': 'we',
    'הם': 'they',
    'הן': 'they(f)',
    'זה': 'this',
    'הזה': 'this',
    'הזאת': 'this',
    'זאת': 'this',
    'אלה': 'these',
    'ואלה': 'and·these',
    'ועתה': 'and·now',
    'עתה': 'now',
    'מה': 'what',
    'למה': 'why',
    'הנה': 'behold',
    'והנה': 'and·behold',

    # === COMMON VERBS (past tense for interlinear) ===
    'ויאמר': 'and·said',
    'ויאמרו': 'and·they·said',
    'ותאמר': 'and·she·said',
    'אמר': 'said',
    'לאמר': 'saying',
    'ויהי': 'and·it·was',
    'והיה': 'and·it·shall·be',
    'היה': 'was',
    'היתה': 'was',
    'יהי': 'let·there·be',
    'ויעש': 'and·made',
    'עשה': 'made',
    'ויקרא': 'and·called',
    'וירא': 'and·saw',
    'ויבא': 'and·came',
    'ויבאו': 'and·they·came',
    'ויקח': 'and·took',
    'ויתן': 'and·gave',
    'ותלד': 'and·she·bore',
    'ויולד': 'and·begot',
    'וילד': 'and·begot',
    'ויחי': 'and·lived',
    'וימת': 'and·died',
    'וישב': 'and·dwelt',
    'וישלח': 'and·sent',
    'ויצא': 'and·went·out',
    'וילך': 'and·went',
    'וילכו': 'and·they·went',
    'ויקם': 'and·arose',
    'וישם': 'and·placed',
    'וידבר': 'and·spoke',
    'ויברך': 'and·blessed',
    'וישמע': 'and·heard',
    'ויקרב': 'and·drew·near',
    'ויען': 'and·answered',
    'ויעל': 'and·went·up',
    'וירד': 'and·went·down',
    'ויסע': 'and·journeyed',
    'ויבן': 'and·built',
    'וישתחו': 'and·bowed·down',
    'ויפל': 'and·fell',
    'ויבך': 'and·wept',
    'ויעבר': 'and·passed·over',
    'ויחל': 'and·began',
    'וישלחהו': 'and·sent·him',
    'ויקם': 'and·arose',

    # === NOUNS ===
    'ארץ': 'land',
    'הארץ': 'the·earth',
    'בארץ': 'in·the·land',
    'מארץ': 'from·the·land',
    'ארצה': 'to·the·land',
    'שמים': 'heavens',
    'השמים': 'the·heavens',
    'מים': 'water',
    'המים': 'the·waters',
    'יום': 'day',
    'היום': 'the·day',
    'ביום': 'on·the·day',
    'בקר': 'morning',
    'ערב': 'evening',
    'אור': 'light',
    'האור': 'the·light',
    'חשך': 'darkness',
    'איש': 'man',
    'האיש': 'the·man',
    'אשה': 'woman',
    'האשה': 'the·woman',
    'אשתו': 'his·wife',
    'האדם': 'the·man',
    'אדם': 'man',
    'אב': 'father',
    'אביו': 'his·father',
    'אבי': 'father·of',
    'אביך': 'your·father',
    'אביכם': 'your·father',
    'אם': 'mother',
    'אמו': 'his·mother',
    'אח': 'brother',
    'אחיו': 'his·brother',
    'אחי': 'brother·of',
    'אחיך': 'your·brother',
    'עבד': 'servant',
    'עבדיו': 'his·servants',
    'עבדך': 'your·servant',
    'עבדי': 'my·servant',
    'עיר': 'city',
    'בית': 'house',
    'הבית': 'the·house',
    'ביתו': 'his·house',
    'דבר': 'word',
    'הדברים': 'the·words',
    'דברי': 'words·of',
    'עין': 'eye',
    'עיני': 'eyes·of',
    'בעיני': 'in·the·eyes·of',
    'בעיניו': 'in·his·eyes',
    'בעיניך': 'in·your·eyes',
    'יד': 'hand',
    'ידו': 'his·hand',
    'ידי': 'hands·of',
    'בידו': 'in·his·hand',
    'ביד': 'in·the·hand·of',
    'לב': 'heart',
    'לבו': 'his·heart',
    'נפש': 'soul',
    'כל': 'all',
    'וכל': 'and·all',
    'לכל': 'to·all',
    'מכל': 'from·all',
    'בכל': 'in·all',
    'כלהארץ': 'all·the·earth',
    'עלהארץ': 'upon·the·earth',
    'מאת': 'hundred',
    'מאות': 'hundreds',
    'רעה': 'evil',
    'ברית': 'covenant',
    'בריתי': 'my·covenant',

    # === NAMES (clean — just the name, no etymology) ===
    'אברהם': 'Abraham',
    'ואברהם': 'and·Abraham',
    'לאברהם': 'to·Abraham',
    'אלאברהם': 'to·Abraham',
    'אברם': 'Abram',
    'אלאברם': 'to·Abram',
    'לאברם': 'to·Abram',
    'יצחק': 'Isaac',
    'אתיצחק': '[obj.mark]·Isaac',
    'ליצחק': 'to·Isaac',
    'יעקב': 'Jacob',
    'ויעקב': 'and·Jacob',
    'ליעקב': 'to·Jacob',
    'אליעקב': 'to·Jacob',
    'אתיעקב': '[obj.mark]·Jacob',
    'עשו': 'Esau',
    'לעשו': 'to·Esau',
    'יוסף': 'Joseph',
    'ליוסף': 'to·Joseph',
    'אליוסף': 'to·Joseph',
    'אתיוסף': '[obj.mark]·Joseph',
    'ישראל': 'Israel',
    'לישראל': 'to·Israel',
    'פרעה': 'Pharaoh',
    'לפרעה': 'to·Pharaoh',
    'אלפרעה': 'to·Pharaoh',
    'אתפרעה': '[obj.mark]·Pharaoh',
    'מצרים': 'Egypt',
    'מצרימה': 'to·Egypt',
    'ממצרים': 'from·Egypt',
    'במצרים': 'in·Egypt',
    'כנען': 'Canaan',
    'בכנען': 'in·Canaan',
    'נח': 'Noah',
    'לנח': 'to·Noah',
    'שרי': 'Sarai',
    'שרה': 'Sarah',
    'ושרה': 'and·Sarah',
    'לשרה': 'to·Sarah',
    'רחל': 'Rachel',
    'לאה': 'Leah',
    'דינה': 'Dinah',
    'בלהה': 'Bilhah',
    'זלפה': 'Zilpah',
    'יהודה': 'Judah',
    'ראובן': 'Reuben',
    'שמעון': 'Simeon',
    'לוי': 'Levi',
    'דן': 'Dan',
    'נפתלי': 'Naphtali',
    'גד': 'Gad',
    'אשר': 'Asher',  # Note: also means "which" — handled by context below
    'יששכר': 'Issachar',
    'זבולן': 'Zebulun',
    'בנימין': 'Benjamin',
    'אדום': 'Edom',
    'ארם': 'Aram',
    'סדם': 'Sodom',
    'עמרה': 'Gomorrah',
    'ממרא': 'Mamre',
    'חרן': 'Haran',
    'חברון': 'Hebron',
    'רבקה': 'Rebekah',
    'ישמעאל': 'Ishmael',
    'לוט': 'Lot',
    'ולוט': 'and·Lot',
    'אבימלך': 'Abimelech',
    'פלשתים': 'Philistines',
    'החתי': 'the·Hittite',
    'בניחת': 'sons·of·Heth',
    'יהוה': 'YHWH',

    # === MISC FIXES ===
    'מאד': 'very',
    'במאד': 'very·much',
    'אשר': 'which',
    'כאשר': 'as',
    'באשר': 'in·which',
    'מעל': 'above',
    'על': 'upon',
    'עליו': 'upon·him',
    'עלי': 'upon·me',
    'עליהם': 'upon·them',
    'עליך': 'upon·you',
    'עליה': 'upon·her',
    'עלינו': 'upon·us',
    'כן': 'so',
    'גם': 'also',
    'לא': 'not',
    'ולא': 'and·not',
    'אם': 'if',
    'ואם': 'and·if',
    'בין': 'between',
    'ובין': 'and·between',
    'כלאשרלו': 'all·that·to·him',
}

# ─── Apply fixes ─────────────────────────────────────────────────────────

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fixed_gloss = 0
fixed_html = 0
fixed_dict = 0
fixed_period = 0

for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            eng = w['eng']

            # 1. Direct corrections from master dictionary
            if key in GLOSS_FIXES:
                correct = GLOSS_FIXES[key]
                if eng != correct:
                    w['eng'] = correct
                    fixed_gloss += 1
                    continue

            # 2. Strip HTML leaks
            if '<a ' in eng or 'href' in eng or 'class=' in eng or '</' in eng:
                # Try to extract useful text before HTML
                clean = re.sub(r'<[^>]*>.*', '', eng).strip()
                clean = re.sub(r'\(f\.\s*$', '', clean).strip()
                if clean and len(clean) > 1:
                    w['eng'] = clean
                else:
                    w['eng'] = ''  # will need manual fix but better than HTML
                fixed_html += 1
                continue

            # 3. Strip dictionary etymologies from names
            # Pattern: "Name = "meaning""
            m = re.match(r'^([A-Z][a-z]+)\s*=\s*"', eng)
            if m:
                w['eng'] = m.group(1)
                fixed_dict += 1
                continue

            # 4. Compound glosses with dictionary defs
            # Pattern: "word·Name = "meaning""
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
                fixed_dict += 1
                continue

            # 5. Fix trailing periods
            if eng.endswith('.') and not eng.endswith('...'):
                w['eng'] = eng.rstrip('.')
                fixed_period += 1
                continue

            # 6. Fix academic jargon
            if 'inflected' in eng:
                if 'to me' in eng: w['eng'] = 'to·me'
                elif 'to you' in eng: w['eng'] = 'to·you'
                elif 'to us' in eng: w['eng'] = 'to·us'
                elif 'to him' in eng: w['eng'] = 'to·him'
                elif 'to her' in eng: w['eng'] = 'to·her'
                elif 'to them' in eng: w['eng'] = 'to·them'
                else: w['eng'] = eng.split('.')[0].strip()
                fixed_gloss += 1
                continue

            if eng == 'pron 3p s':
                w['eng'] = 'he'
                fixed_gloss += 1
                continue

            # 7. Fix "sign of the definite direct object" variants
            if eng.startswith('sign of the definite'):
                w['eng'] = '[obj.mark]'
                fixed_gloss += 1
                continue

            # 8. Verbose compound obj markers
            if eng.startswith('[obj.mark]\u00B7sign of'):
                parts = eng.split('\u00B7')
                cleaned = [p if 'sign of' not in p else '[obj.mark]' for p in parts]
                w['eng'] = '\u00B7'.join(dict.fromkeys(cleaned))
                fixed_gloss += 1

# ─── Second pass: fix compound keys ─────────────────────────────────────
# For maqaf-joined words, check if the compound key matches
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            eng = w['eng']
            # Fix any remaining HTML
            if '<' in eng:
                w['eng'] = re.sub(r'<[^>]*>', '', eng).strip()
                if '&' in w['eng']:
                    w['eng'] = htmlmod.unescape(w['eng'])
                fixed_html += 1
            # Fix &amp; etc
            if '&' in w['eng']:
                w['eng'] = htmlmod.unescape(w['eng'])

# ─── Stats ───────────────────────────────────────────────────────────────

total_w = sum(len(v['words']) for c in d['chapters'] for v in c['verses'])
still_empty = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if w['eng'] == '')

# Check for remaining problems
remaining_html = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if '<' in w['eng'] or 'href' in w['eng'])
remaining_dict = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words'] if '="' in w['eng'])

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Fixed: {fixed_gloss} wrong glosses, {fixed_html} HTML leaks, {fixed_dict} dictionary defs, {fixed_period} trailing periods")
print(f"Total: {fixed_gloss + fixed_html + fixed_dict + fixed_period} fixes across {total_w} words")
print(f"Still empty: {still_empty}")
print(f"Remaining HTML: {remaining_html}")
print(f"Remaining dict defs: {remaining_dict}")
