#!/usr/bin/env python3
"""
Fix glosses by matching Hebrew text within specific verses.
Safer than index-based fixes — won't misalign.
Format: (chapter, verse, hebrew_text, correct_gloss)
"""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# === GLOBAL fixes: these Hebrew words are ALWAYS wrong, fix everywhere ===
# (hebrew_consonants, wrong_gloss, correct_gloss)
# If wrong_gloss is None, fix regardless of current gloss
GLOBAL = [
    # Verbs consistently wrong
    ('נשים', 'offering', 'wives'),
    ('אשתך', 'offering', 'your·wife'),
    ('אשתו', 'offering', 'his·wife'),
    ('לאשה', 'offering', 'as·a·wife'),
    ('נשיבניך', 'burnt-offering·son', 'the·wives·of·your·sons'),
    ('מביא', 'go in', 'bringing'),
    ('תביא', 'go in', 'you·shall·bring'),
    ('יבאו', 'go in', 'shall·come'),
    ('ובאת', 'go in', 'and·you·shall·enter'),
    ('באו', 'go in', 'came'),
    ('הביא', 'go in', 'brought'),
    ('והקמתי', 'rise', 'and·I·will·establish'),
    ('תעשה', 'do', 'you·shall·make'),
    ('תעשה', 'to do', 'you·shall·make'),
    ('תעשה', 'to·do', 'you·shall·make'),
    ('עשה', 'to do', 'make'),
    ('צוה', 'command', 'commanded'),
    ('צוה', 'to command', 'commanded'),
    ('ראיתי', 'see', 'I·have·seen'),
    ('ראיתי', 'to see', 'I·have·seen'),
    ('שנים', 'years', None),  # context-dependent, skip global
    ('שניים', 'years', None),
    ('זכר', 'remember', None),  # context-dependent
    ('זכר', 'to remember', None),

    # Nouns consistently wrong
    ('רוחי', 'smell', 'My·spirit'),
    ('רוחי', 'to smell', 'My·spirit'),
    ('חיים', 'adj', 'life'),
    ('חיים', 'living', None),  # this one is fine, skip
    ('חי', 'adj', 'living'),
    ('בריתי', '[d.o.]', 'My·covenant'),
    ('אתך', '[d.o.]·you', 'with·you'),
    ('בניך', 'son', 'your·sons'),
    ('ולהם', 'abundance', 'and·for·them'),
    ('מלמעלה', 'unfaithful', 'from·above'),
    ('תשים', 'put', 'you·shall·set'),
    ('תשים', 'to put', 'you·shall·set'),
    ('שניים', 'years', 'two'),
    ('שנים', None, None),  # too context-dependent
    ('ככל', 'all', 'according·to·all'),
    ('אתו', '[d.o.]·him', 'him'),  # simplify
    ('בדור', 'period', 'in·the·generation'),
    ('צדיק', 'just', 'righteous'),
    ('ביתך', 'nm', 'your·household'),
    ('התבה', 'ark', 'the·ark'),
    ('אלהתבה', 'to·ark', 'into·the·ark'),
    ('צהר', None, 'window'),
    ('תחתיים', 'low', 'lower'),
    ('שלשים', 'thirty', None),  # could be correct

    # [d.o.] cleanup — old format
    ('[d.o.]', None, '[identifies object]'),
]

gfixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            for heb_cons, wrong, correct in GLOBAL:
                if correct is None:
                    continue  # skip context-dependent
                if key == heb_cons:
                    if wrong is None or w['eng'] == wrong:
                        if w['eng'] != correct:
                            w['eng'] = correct
                            gfixed += 1
                    break

print(f"Global fixes: {gfixed}")

# === Fix שנים/שניים = "two" vs "years" based on context ===
for c in d['chapters']:
    for v in c['verses']:
        trans = v.get('translation', '').lower()
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if key in ('שנים', 'שניים') and w['eng'] == 'years':
                if 'two' in trans and 'year' not in trans:
                    w['eng'] = 'two'
                    gfixed += 1
                elif 'two' in trans:
                    # Check if this specific word is "two" by position
                    # If followed by a non-number word, likely "two"
                    idx = v['words'].index(w)
                    if idx + 1 < len(v['words']):
                        next_eng = v['words'][idx + 1]['eng']
                        if next_eng not in ('year', 'years', 'hundred', 'hundreds'):
                            w['eng'] = 'two'
                            gfixed += 1

# === Fix זכר = "male" vs "remember" based on context ===
for c in d['chapters']:
    for v in c['verses']:
        trans = v.get('translation', '').lower()
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            if key == 'זכר' and w['eng'] in ('remember', 'to remember'):
                if 'male' in trans or 'man' in trans:
                    w['eng'] = 'male'
                    gfixed += 1

print(f"Global + context fixes: {gfixed}")

# (chapter, verse, hebrew_consonants, correct_english)
# Hebrew consonants = stripped of nikud/cantillation but keeping maqaf
FIXES = [
    # Gen 5 remaining fixes
    (5, 1, 'אדם', 'Adam'),  # first occurrence in verse
    (5, 29, 'נח', 'Noah'),

    # Gen 6
    (6, 1, 'כיהחל', 'when·began'),
    (6, 1, 'לרב', 'to·multiply'),
    (6, 1, 'עלפני', 'upon·the·face·of'),
    (6, 1, 'האדמה', 'the·ground'),
    (6, 1, 'ובנות', 'and·daughters'),
    (6, 1, 'ילדו', 'were·born'),
    (6, 2, 'ויראו', 'and·saw'),
    (6, 2, 'בניהאלהים', 'the·sons·of·God'),
    (6, 2, 'אתבנות', 'the·daughters·of'),
    (6, 2, 'טבת', 'beautiful'),
    (6, 2, 'הנה', 'they·were'),
    (6, 2, 'נשים', 'wives'),
    (6, 2, 'בחרו', 'they·chose'),
    (6, 3, 'לאידון', 'not·shall·strive'),
    (6, 3, 'רוחי', 'My·spirit'),
    (6, 3, 'באדם', 'in·man'),
    (6, 3, 'לעלם', 'forever'),
    (6, 3, 'בשגם', 'since·also'),
    (6, 3, 'והיו', 'and·shall·be'),
    (6, 3, 'ימיו', 'his·days'),
    (6, 4, 'הנפלים', 'the·Nephilim'),
    (6, 4, 'היו', 'were'),
    (6, 4, 'בימים', 'in·the·days'),
    (6, 4, 'ההם', 'those'),
    (6, 4, 'וגם', 'and·also'),
    (6, 4, 'אחריכן', 'after·that'),
    (6, 4, 'יבאו', 'came'),
    (6, 4, 'בני', 'the·sons·of'),
    (6, 4, 'אלבנות', 'to·the·daughters·of'),
    (6, 4, 'וילדו', 'and·they·bore'),
    (6, 4, 'המה', 'they·were'),
    (6, 4, 'הגברים', 'the·mighty·ones'),
    (6, 4, 'מעולם', 'from·of·old'),
    (6, 4, 'אנשי', 'men·of'),
    (6, 4, 'השם', 'renown'),
    (6, 5, 'וירא', 'and·YHWH·saw'),
    (6, 5, 'רבה', 'great'),
    (6, 5, 'רעת', 'the·wickedness·of'),
    (6, 5, 'וכליצר', 'and·every·intent·of'),
    (6, 5, 'מחשבת', 'the·thoughts·of'),
    (6, 5, 'לבו', 'his·heart'),
    (6, 5, 'רק', 'only'),
    (6, 5, 'רע', 'evil'),
    (6, 5, 'כלהיום', 'all·the·day'),
    (6, 6, 'וינחם', 'and·regretted'),
    (6, 6, 'עשה', 'He·had·made'),
    (6, 6, 'ויתעצב', 'and·it·grieved'),
    (6, 6, 'אללבו', 'to·His·heart'),
    (6, 7, 'אמחה', 'I·will·blot·out'),
    (6, 7, 'בראתי', 'I·created'),
    (6, 7, 'מעלפני', 'from·the·face·of'),
    (6, 7, 'מאדם', 'from·man'),
    (6, 7, 'עדבהמה', 'to·beast'),
    (6, 7, 'עדרמש', 'to·creeping·thing'),
    (6, 7, 'ועדעוף', 'and·to·birds·of'),
    (6, 7, 'נחמתי', 'I·regret'),
    (6, 7, 'עשיתם', 'I·made·them'),
    (6, 8, 'ונח', 'but·Noah'),
    (6, 8, 'מצא', 'found'),
    (6, 8, 'חן', 'favor'),
    (6, 8, 'בעיני', 'in·the·eyes·of'),
    (6, 9, 'תולדת', 'the·generations·of'),
    (6, 9, 'צדיק', 'righteous'),
    (6, 9, 'תמים', 'blameless'),
    (6, 9, 'בדרתיו', 'in·his·generations'),
    (6, 9, 'האלהים', 'God'),
    (6, 9, 'התהלך', 'walked'),
    (6, 10, 'ויולד', 'and·begot'),
    (6, 10, 'שלשה', 'three'),
    (6, 10, 'בנים', 'sons'),
    (6, 11, 'ותשחת', 'and·was·corrupt'),
    (6, 11, 'לפני', 'before'),
    (6, 11, 'ותמלא', 'and·was·filled'),
    (6, 11, 'חמס', 'with·violence'),
    (6, 12, 'וירא', 'and·saw'),
    (6, 12, 'נשחתה', 'it·was·corrupt'),
    (6, 12, 'כיהשחית', 'for·had·corrupted'),
    (6, 12, 'כלבשר', 'all·flesh'),
    (6, 12, 'דרכו', 'its·way'),
    (6, 13, 'קץ', 'the·end·of'),
    (6, 13, 'כלבשר', 'all·flesh'),
    (6, 13, 'בא', 'has·come'),
    (6, 13, 'לפני', 'before·Me'),
    (6, 13, 'כימלאה', 'for·is·filled'),
    (6, 13, 'חמס', 'with·violence'),
    (6, 13, 'מפניהם', 'because·of·them'),
    (6, 13, 'והנני', 'and·behold·I'),
    (6, 13, 'משחיתם', 'will·destroy·them'),
    (6, 13, 'אתהארץ', 'with·the·earth'),
    (6, 14, 'עשה', 'make'),
    (6, 14, 'לך', 'for·yourself'),
    (6, 14, 'תבת', 'an·ark·of'),
    (6, 14, 'עציגפר', 'gopher·wood'),
    (6, 14, 'קנים', 'rooms'),
    (6, 14, 'תעשה', 'you·shall·make'),
    (6, 14, 'התבה', 'the·ark'),
    (6, 14, 'וכפרת', 'and·cover·it'),
    (6, 14, 'מבית', 'inside'),
    (6, 14, 'ומחוץ', 'and·outside'),
    (6, 14, 'בכפר', 'with·pitch'),
]

# Apply fixes — match by chapter, verse, and Hebrew consonants
fixed = 0
for ch_num, v_num, heb_cons, correct in FIXES:
    ch = d['chapters'][ch_num - 1]
    if v_num - 1 >= len(ch['verses']):
        continue
    v = ch['verses'][v_num - 1]
    for w in v['words']:
        key = strip_n(w['heb']).replace('\u05BE', '')
        if key == heb_cons:
            if w['eng'] != correct:
                w['eng'] = correct
                fixed += 1
            break  # only fix first match in verse

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Verify Gen 6:1-4
print(f"Fixed {fixed} entries\n")
for v in d['chapters'][5]['verses'][:4]:
    print(f'{v["ref"]}:  {v["translation"][:60]}')
    for w in v['words']:
        print(f'  {w["heb"]:20s}  {w["eng"]}')
    print()
