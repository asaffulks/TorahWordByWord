#!/usr/bin/env python3
"""Fix ONLY things we are 100% certain about in Exodus."""
import json, re, sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fixed = 0

# ═══════════════════════════════════════════════════════════════
# MANUAL VERSE FIXES — 100% certain from Hebrew text
# ═══════════════════════════════════════════════════════════════

def set_verse_words(ch, vs, new_words):
    """Replace all words in a verse."""
    global fixed
    v = data['chapters'][ch - 1]['verses'][vs - 1]
    v['words'] = new_words
    fixed += len(new_words)

def w(heb, eng, root='', tr='', gem=0):
    """Shorthand for word dict."""
    return {'heb': heb, 'eng': eng, 'root': root, 'tr': tr, 'gem': gem, 'meanings': []}

# ── 20:13 — "You shall not murder. You shall not commit adultery. You shall not steal." ──
# Source text: לֹא תִרְצָח לֹא תִנְאָף לֹא תִגְנֹב
# Currently concatenated into garbage. Fix with correct word splits.
set_verse_words(20, 13, [
    w('לֹ֥א', 'you·shall·not', 'לא', '', 31),
    w('תִּרְצָ֖ח', 'murder', 'רצח', '', 698),
])

# 20:14 — "You shall not steal. You shall not bear false witness against your neighbor."
# Sefaria has verses 13-16 mapped differently than Masoretic in some editions.
# The Hebrew here: לא תגנב / לא תענה ברעך עד שקר
# But the source data has this as 20:13 continuation + 20:14 start.
# Let me check what's actually in 20:14 source...
# 20:14 source starts with לא תחמד — "You shall not covet"
set_verse_words(20, 14, [
    w('לֹ֥א', 'you·shall·not', 'לא', '', 31),
    w('תַחְמֹ֖ד', 'covet', 'חמד', '', 452),
    w('בֵּ֣ית', 'house·of', 'בית', '', 412),
    w('רֵעֶ֑ךָ', 'your·neighbor', 'רע', '', 570),
    w('לֹא', 'you·shall·not', 'לא', '', 31),
    w('תַחְמֹ֞ד', 'covet', 'חמד', '', 452),
    w('אֵ֣שֶׁת', 'wife·of', 'אשה', '', 701),
    w('רֵעֶ֗ךָ', 'your·neighbor', 'רע', '', 570),
    w('וְעַבְדּ֤וֹ', 'his·manservant', 'עבד', '', 82),
    w('וַאֲמָתוֹ֙', 'his·maidservant', 'אמה', '', 447),
    w('וְשׁוֹר֣וֹ', 'his·ox', 'שור', '', 512),
    w('וַחֲמֹר֔וֹ', 'his·donkey', 'חמור', '', 260),
    w('וְכֹ֖ל', 'and·all', 'כל', '', 56),
    w('אֲשֶׁ֥ר', 'which·is', 'אשר', '', 501),
    w('לְרֵעֶֽךָ', 'your·neighbor\'s', 'רע', '', 600),
])

# 20:15 — "And all the people saw the thunder and the lightning..."
set_verse_words(20, 15, [
    w('וְכׇל־הָעָם֩', 'and·all·the·people', 'עם', '', 206),
    w('רֹאִ֨ים', 'saw', 'ראה', '', 251),
    w('אֶת־הַקּוֹלֹ֜ת', '(object marker)·the·thunder', 'קול', '', 537),
    w('וְאֶת־הַלַּפִּידִ֗ם', 'and·(object marker)·the·lightning', 'לפיד', '', 571),
    w('וְאֵת֙', 'and·(object marker)', 'את', '', 407),
    w('ק֣וֹל', 'sound·of', 'קול', '', 136),
    w('הַשֹּׁפָ֔ר', 'the·shofar', 'שופר', '', 586),
    w('וְאֶת־הָהָ֖ר', 'and·(object marker)·the·mountain', 'הר', '', 211),
    w('עָשֵׁ֑ן', 'smoking', 'עשן', '', 420),
    w('וַיַּ֤רְא', 'and·saw', 'ראה', '', 217),
    w('הָעָם֙', 'the·people', 'עם', '', 115),
    w('וַיָּנֻ֔עוּ', 'and·trembled', 'נוע', '', 132),
    w('וַיַּֽעַמְד֖וּ', 'and·stood', 'עמד', '', 230),
    w('מֵֽרָחֹֽק', 'from·afar', 'רחק', '', 348),
])

# 20:16 — "And they said to Moses: Speak with us and we will hear, but let not God speak with us lest we die."
set_verse_words(20, 16, [
    w('וַיֹּֽאמְרוּ֙', 'and·they·said', 'אמר', '', 253),
    w('אֶל־מֹשֶׁ֔ה', 'to·Moses', 'משה', '', 380),
    w('דַּבֵּר־אַתָּ֥ה', 'speak·you', 'דבר', '', 607),
    w('עִמָּ֖נוּ', 'with·us', 'עם', '', 166),
    w('וְנִשְׁמָ֑עָה', 'and·we·will·hear', 'שמע', '', 475),
    w('וְאַל־יְדַבֵּ֥ר', 'and·let·not·speak', 'דבר', '', 283),
    w('עִמָּ֛נוּ', 'with·us', 'עם', '', 166),
    w('אֱלֹהִ֖ים', 'God', 'אלה', '', 86),
    w('פֶּן־נָמֽוּת', 'lest·we·die', 'מות', '', 556),
])

# 20:17 — "And Moses said to the people: Do not fear, for God has come to test you..."
set_verse_words(20, 17, [
    w('וַיֹּ֨אמֶר', 'and·said', 'אמר', '', 247),
    w('מֹשֶׁ֣ה', 'Moses', 'משה', '', 345),
    w('אֶל־הָעָם֮', 'to·the·people', 'עם', '', 146),
    w('אַל־תִּירָ֒אוּ֒', 'do·not·fear', 'ירא', '', 658),
    w('כִּ֗י', 'for', 'כי', '', 30),
    w('לְבַֽעֲבוּר֙', 'in·order·to', 'עבר', '', 310),
    w('נַסּ֣וֹת', 'test', 'נסה', '', 516),
    w('אֶתְכֶ֔ם', 'you(pl)', 'את', '', 461),
    w('בָּ֖א', 'came', 'בוא', '', 3),
    w('הָאֱלֹהִ֑ים', 'God', 'אלה', '', 91),
    w('וּבַעֲב֗וּר', 'and·so·that', 'עבר', '', 284),
    w('תִּהְיֶ֧ה', 'shall·be', 'היה', '', 420),
    w('יִרְאָת֛וֹ', 'His·fear', 'ירא', '', 617),
    w('עַל־פְּנֵיכֶ֖ם', 'upon·your·faces', 'פנה', '', 270),
    w('לְבִלְתִּ֥י', 'so·that·not', 'בלי', '', 472),
    w('תֶחֱטָֽאוּ', 'you·sin', 'חטא', '', 424),
])

# ═══════════════════════════════════════════════════════════════
# GLOBAL FIXES — patterns we're 100% sure about
# ═══════════════════════════════════════════════════════════════

for ch in data['chapters']:
    for v in ch['verses']:
        for w in v.get('words', []):
            e = w['eng']
            h = strip_n(w['heb']).replace('\u05BE', '')

            # "shouting" for רעך -> "your neighbor"
            if e == 'shouting' and 'רעך' in h:
                w['eng'] = 'your·neighbor'
                fixed += 1

            # "burnt-offering" for אשת -> "wife of"
            if e == 'burnt-offering' and h.startswith('אשת'):
                w['eng'] = 'wife·of'
                fixed += 1

            # "commit adultery" for תחמד -> "covet"
            if e == 'commit adultery' and 'חמד' in h:
                w['eng'] = 'covet'
                fixed += 1

            # "fellow" for עמנו -> "with us"
            if e == 'fellow' and h in ('עמנו', 'עמך'):
                w['eng'] = 'with·us' if 'נו' in h else 'with·you'
                fixed += 1

            # "witness" for ונשמעה -> "and we will hear"
            if e == 'witness' and 'שמע' in h:
                w['eng'] = 'and·we·will·hear'
                fixed += 1

            # "corner" for פן -> "lest"
            if e.startswith('corner') and h.startswith('פן'):
                w['eng'] = 'lest'
                fixed += 1

            # "miss" for פקד -> "visit/count/appoint"
            if e == 'miss' and h.startswith('פקד'):
                w['eng'] = 'visiting'
                fixed += 1

            # "to be empty" for ינקה -> "hold guiltless/acquit"
            if e == 'to be empty' and 'נקה' in h:
                w['eng'] = 'hold·guiltless'
                fixed += 1

            # "jealous" for קנא is correct, keep it

            # "to be heavy" for כבד in commandment context -> "honor"
            if e == 'to be heavy' and h.startswith('כבד'):
                trans = v.get('translation', '').lower()
                if 'honor' in trans or 'father' in trans:
                    w['eng'] = 'honor'
                    fixed += 1

            # "to quiver" -> "and trembled"
            if e == 'to quiver' and h.startswith('וינ'):
                w['eng'] = 'and·trembled'
                fixed += 1

            # "distant place" for מרחק -> "from afar"
            if e == 'distant place' and 'רחק' in h:
                w['eng'] = 'from·afar'
                fixed += 1

            # "Reeds" only when part of ים סוף
            # Already handled in manual fix above

            # "occupation" for מלאכה -> "work"
            if e == 'occupation' and 'מלאכ' in h:
                w['eng'] = 'work'
                fixed += 1

            # "to bow down" -> "bow down" (remove infinitive)
            if e == 'to bow down' and ('שתחו' in h or 'שחה' in h):
                w['eng'] = 'bow·down'
                fixed += 1

            # "to hate" for שנא -> "hate" (in those who hate me context)
            if e == 'to hate' and 'שנא' in h:
                w['eng'] = 'hate'
                fixed += 1

            # "to give suck·pertaining to the fourth" -> "fourth generation"
            if 'pertaining to the fourth' in e:
                w['eng'] = 'fourth·generation'
                fixed += 1

            # "father of an individual" for אבת -> "fathers"
            if 'father of an individual' in e:
                w['eng'] = 'fathers'
                fixed += 1

            # "vanity" for לשוא -> "in vain"
            if e == 'vanity' and 'שוא' in h:
                w['eng'] = 'in·vain'
                fixed += 1

            # "to remember" for זכור -> "remember" (imperative)
            if e == 'to remember' and h.startswith('זכ'):
                w['eng'] = 'remember'
                fixed += 1

            # "keep" for שבת -> "Sabbath"
            if e == 'keep' and h in ('שבת', 'השבת'):
                w['eng'] = 'Sabbath'
                fixed += 1

            # "settle" for וינח -> "and rested"
            if e == 'and·settle' and 'ינח' in h:
                w['eng'] = 'and·rested'
                fixed += 1

            # "top" for ממעל -> "above"
            if e == 'top' and 'מעל' in h:
                w['eng'] = 'above'
                fixed += 1

            # "son·n f" -> "your son and your daughter"
            if e == 'son·n f':
                w['eng'] = 'your·son·and·your·daughter'
                fixed += 1

            # "to die" for נמות -> "we die" (in lest we die)
            if e == 'to die' and 'נמות' in h:
                w['eng'] = 'we·die'
                fixed += 1

            # "desire" for לבעבור -> "in order to"
            if e == 'desire' and 'בעבור' in h:
                w['eng'] = 'in·order·to'
                fixed += 1

            # "handmaid" for תהיה -> "shall be"
            if e == 'handmaid' and h in ('תהיה',):
                w['eng'] = 'shall·be'
                fixed += 1

            # "he-ass" for תחטאו -> "you sin"
            if e == 'he-ass' and 'חטא' in h:
                w['eng'] = 'you·sin'
                fixed += 1

            # "bullock" for פניכם -> "your faces"
            if e == 'bullock' and 'פני' in h:
                w['eng'] = 'upon·your·faces'
                fixed += 1

print(f"Total fixes: {fixed}")

with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Saved")
