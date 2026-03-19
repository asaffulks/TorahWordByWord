#!/usr/bin/env python3
"""Fix clearly broken/corrupted word glosses identified by cross-check."""
import json, sys, re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('K:/TorahByWord/genesis_v3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def strip_n(t):
    return re.sub(r'[\u0591-\u05C7\u05F3\u05F4]', '', t).replace('\u05BE', '')

fixes = 0

def fix(ch, v, word_idx, new_gloss):
    global fixes
    verse = data['chapters'][ch-1]['verses'][v-1]
    w = verse['words'][word_idx]
    old = w['eng']
    if old != new_gloss:
        print(f"  {ch}:{v}[{word_idx}] {w['heb']}: \"{old}\" -> \"{new_gloss}\"")
        w['eng'] = new_gloss
        fixes += 1

def find_and_fix(ch, v, heb_pattern, new_gloss):
    """Find word by Hebrew pattern and fix."""
    global fixes
    verse = data['chapters'][ch-1]['verses'][v-1]
    for i, w in enumerate(verse['words']):
        if strip_n(w['heb']) == strip_n(heb_pattern) or heb_pattern in w['heb']:
            old = w['eng']
            if old != new_gloss:
                print(f"  {ch}:{v}[{i}] {w['heb']}: \"{old}\" -> \"{new_gloss}\"")
                w['eng'] = new_gloss
                fixes += 1
                return True
    return False

print("=== Fixing corrupted/truncated glosses ===")

# "repent(-er" -> proper forms of נחם
find_and_fix(6, 6, 'וַיִּנָּחֶם', 'and·He·regretted')
find_and_fix(24, 67, 'וַיִּנָּחֵם', 'and·was·comforted')
find_and_fix(27, 42, 'מִתְנַחֵם', 'consoling·himself')
find_and_fix(37, 35, 'לְהִתְנַחֵם', 'to·be·comforted')
find_and_fix(38, 12, 'וַיִּנָּחֶם', 'and·was·comforted')
find_and_fix(50, 21, 'וַיְנַחֵם', 'and·he·comforted')

# "buy(-er)" -> proper forms of קנה
find_and_fix(25, 10, 'קָנָה', 'purchased')
find_and_fix(47, 22, 'קָנָה', 'purchased')
find_and_fix(49, 30, 'קָנָה', 'purchased')
find_and_fix(50, 13, 'קָנָה', 'purchased')

# "he who comes. 1 he who arrives" -> proper forms of בוא
find_and_fix(19, 9, 'בָּא', 'came·to·sojourn')
find_and_fix(43, 23, 'בָּא', 'has·come')

# "(in) all (manner" -> eating
find_and_fix(39, 6, 'אוֹכֵל', 'eating')

# "all·v" and "not·v" -> truncated
find_and_fix(21, 6, 'כׇּל', 'all·who·hear')
find_and_fix(32, 13, 'לֹא', 'not·be·counted')
find_and_fix(39, 10, 'וְלֹא', 'and·not·listened')

# "and·do·adv" -> and·did·so
find_and_fix(42, 29, 'וַיַּעֲשׂוּ', 'and·they·did·so')
find_and_fix(45, 21, 'וַיַּעֲשׂוּ', 'and·they·did·so')

# "I (we) pray" / "I beseech..." -> please
find_and_fix(37, 6, 'שִׁמְעוּ', 'hear·please')
find_and_fix(30, 14, 'תְּנִי', 'give·please')

print("\n=== Fixing wrong meanings ===")

# "not·to·be" for הגדת -> not·told
find_and_fix(12, 18, 'לֹא', 'not·told')
find_and_fix(21, 26, 'לֹא', 'not·told')
find_and_fix(31, 27, 'וְלֹא', 'and·not·told')

# "not·to gather" -> not·be·withheld
find_and_fix(11, 6, 'לֹא', 'not·be·withheld')

# "to·his·wife" for והיו -> and·they·became
fix(2, 24, 6, 'and·became')

# "all·cold" -> all·that·befell
find_and_fix(42, 29, 'כׇּל', 'all·that·befell')

# "not·to prevail" -> not·withhold
find_and_fix(23, 6, 'לֹא', 'not·withhold')

# "not·to brought" -> not·brought
find_and_fix(31, 39, 'לֹא', 'not·brought')

# "not·to support" -> not·believed
find_and_fix(45, 26, 'לֹא', 'not·believed')

# "not·to go down" -> not·go·down
find_and_fix(42, 38, 'לֹא', 'not·go·down')

# "all·to go up" -> all·who·went·up
find_and_fix(50, 14, 'וְכׇל', 'and·all·who·went·up')

print("\n=== Fixing alignment-shifted glosses ===")

# הָיְתָה-לִּי / תִּהְיֶה-לִּי / וַיְהִי-לִי patterns
# These are "was/became to me" = "I had" or "she became my"
fix(18, 12, 6, 'there·was·for·me')
fix(20, 12, 7, 'and·she·became·my')
fix(21, 30, 7, 'it·will·be·for·me')
fix(26, 14, 0, 'and·he·had')
fix(32, 6, 0, 'and·I·have')
fix(44, 10, 7, 'shall·be·my')
fix(44, 17, 11, 'shall·be·my')
fix(48, 5, 3, 'shall·be·mine')

# 18:11 "advanced" is fine contextually but let's check
# 1:22 "and·fill" for פרו should be "be·fruitful"
find_and_fix(1, 22, 'פְּרוּ', 'be·fruitful')

# 1:3 "and·be·to be" for ויהי-אור -> "and·there·was·light"
find_and_fix(1, 3, 'וַֽיְהִי', 'and·there·was·light')

# 2:16 "freely" for אכל is part of infinitive absolute - ok contextually but let's improve
fix(2, 16, 2, 'you·may·freely·eat')

# 2:17 "surely" for מות - same pattern
fix(2, 17, 4, 'you·shall·surely·die')

# "let·not·be·angry" for אל-תותר -> do·not·excel (or: do·not·be·reckless)
find_and_fix(49, 4, 'אַל', 'do·not·have·preeminence')

# "place where...stood" -> standing
find_and_fix(28, 12, 'מֻצָּב', 'set·up')

# 34:15/22/23 "which" for נאות -> consent
find_and_fix(34, 15, 'נֵאוֹת', 'consent')
find_and_fix(34, 22, 'יֵאֹתוּ', 'consent')
find_and_fix(34, 23, 'נֵאוֹתָה', 'let·us·consent')

# "committed·fornication" -> should·she·be·treated·as·a·harlot
find_and_fix(34, 31, 'הַכְזוֹנָה', 'as·a·harlot')

# "witness. Compare" -> as·a·witness
find_and_fix(21, 30, 'לְעֵדָה', 'as·a·witness')

# 2:24 [2] "[d.o.]" missing "his·father"
fix(2, 24, 2, '[d.o.]·his·father')
# 2:24 [5] "in·woman" -> to·his·wife
fix(2, 24, 5, 'to·his·wife')

# 26:14 [2] "purchase" -> herds·of
fix(26, 14, 2, 'and·herds·of')

# 32:6 [4] "worked" -> and·servant
fix(32, 6, 4, 'and·servant')

# 44:17 [3] "did" -> from·doing
fix(44, 17, 3, 'from·doing')

# 44:10 [10] "was" -> shall·be
fix(44, 10, 10, 'shall·be')

print(f"\n=== Total fixes: {fixes} ===")

with open('K:/TorahByWord/genesis_v3.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved genesis_v3.json")
