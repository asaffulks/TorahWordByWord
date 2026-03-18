#!/usr/bin/env python3
"""
Fix ALL critical and moderate issues found in the audit of genesis_v3.json.
"""
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT  = "K:/TorahByWord/genesis_v3.json"
OUTPUT = "K:/TorahByWord/genesis_v3.json"

# ── Load ──────────────────────────────────────────────────────────────
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

counters = {
    "eng_exact_map": 0,
    "eng_marks_object": 0,
    "eng_hebrew_cleaned": 0,
    "eng_paren_cleaned": 0,
    "eng_verb_form_cleaned": 0,
    "meanings_removed": 0,
    "html_stripped": 0,
    "proper_nouns_fixed": 0,
    "verse_31_55": 0,
}

# ── 1. CRITICAL: Fix corrupted glosses (eng field) ──────────────────

# Exact mapping for known corrupted values
ENG_EXACT_MAP = {
    'foot(-step)':                          'this·time',
    'naked(-ness)':                         'naked',
    'make to) dwell(-er)':                  'dwell',
    'month(-ly)':                           'month',
    "seven-) teen":                         'ten',
    'buy(-er)':                             'purchased',
    'repent(-er':                           'comforted',
    'sea (x -faring man':                   'women',
    '(cause to) burn':                      'burnt·offering',
    '(make) pray(-er':                      'prayed',
    'oil(-ed)':                             'oil',
    '(do) serve(-ant':                      'served',
    'sack(-cloth':                          'sackcloth',
    '(chief) friend':                       'chief',
    '(small) cattle':                       'flock',
    '(that have) escape(-d':                'fugitive',
    'upper(-most)':                         'Most·High',
    '(lest) (peradventure)':                'lest',
    'after (that':                          'after',
    '(ac-) count; declare':                 'count',
    'be (when... were) done':               'finished',
    'be (make) afraid':                     'fear',
    '(BDB) to encounter':                   'to·meet',
    'made) red (ruddy)':                    'red',
    'ten ((eight) -een':                    'multiplied',
    '(make to) approach (nigh)':            'came·near',
    'I (me) beseech (pray) thee':           'please',
    'I beseech (pray) thee (you)':          'give·please',
    'on this (that) side':                  'behold',
    'latter) end (time)':                   'end·of',
    'I (we) pray':                          'please',
    'shew) favour(-able)':                  'graciously·gave',
    '(in) all (manner':                     'eating',
    'he who comes. 1 he who arrives':       'came·to·sojourn',
    'witness. Compare':                     'witness',
    'm.(b. h.; sight':                      'sight',
    'constr. כָּל (b. h.; כָּלַל) all':    'and·all',
    'chief.; שר (של מעלה) guardian angel':  'chief·of',
    'height; (prepos.) upon':               'and·upon',
    '(marks object)':                       '(object marker)',
    '(object)':                             '(object marker)',
    'keep(-er':                             'keeper',
    'Qal)':                                 'be',
}

HEB_CHAR_RE = re.compile(r'[\u05D0-\u05EA]')
PAREN_FRAG_RE = re.compile(r'\(-|^\(.*\)')  # (-  or starts with (...)
VERB_FORM_RE = re.compile(r'\b(Qal|Hif|Nif|Pi|Hith|Hof|Shaf)\b')

def clean_eng(eng):
    """Try to clean a corrupted eng field. Returns (cleaned, category) or None."""
    # Exact match first
    if eng in ENG_EXACT_MAP:
        return ENG_EXACT_MAP[eng], "eng_exact_map"

    # Contains Hebrew characters - extract English parts
    if HEB_CHAR_RE.search(eng):
        # Remove Hebrew chars and BDB artifacts
        cleaned = re.sub(r'[\u05D0-\u05EA\u05B0-\u05BD\u05BF-\u05C7]+', '', eng)
        cleaned = re.sub(r'\b(b\.\s*h\.?|constr\.|Pl\.|Pa\.|Nab\.|abs\.)\b', '', cleaned)
        cleaned = re.sub(r'[;,.()\[\]]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', '·', cleaned.strip()).strip('·')
        if cleaned:
            return cleaned, "eng_hebrew_cleaned"
        return None

    # Contains Strong's/BDB parenthetical fragments like "(-"
    if '(-' in eng:
        cleaned = re.sub(r'\(-[^)]*\)?', '', eng)
        cleaned = re.sub(r'\s+', '·', cleaned.strip()).strip('·')
        if cleaned:
            return cleaned, "eng_paren_cleaned"
        return None

    # Verb form fragments
    if VERB_FORM_RE.search(eng):
        cleaned = VERB_FORM_RE.sub('', eng)
        cleaned = re.sub(r'[()]+', '', cleaned)
        cleaned = re.sub(r'\s+', '·', cleaned.strip()).strip('·')
        if cleaned:
            return cleaned, "eng_verb_form_cleaned"
        return None

    return None


# ── 2. CRITICAL: Fix corrupted meanings ─────────────────────────────

BAD_MEANING_PATTERNS = re.compile(
    r'Pl\.|Qal|Hif\.|Nif\.|Pi\.|Hith\.|Hof\.|see H0|b\. h\.|constr\.|Shaf\.'
)

def is_bad_meaning(m):
    if not isinstance(m, str):
        return True
    if len(m) < 2:
        return True
    if HEB_CHAR_RE.search(m):
        return True
    if BAD_MEANING_PATTERNS.search(m):
        return True
    return False


# ── 3. MODERATE: Strip HTML from commentary ─────────────────────────

HTML_TAG_RE = re.compile(r'</?[a-zA-Zא-ת][^>]*>')

COMMENTARY_FIELDS = [
    'rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
    'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar',
]

# ── 4. MODERATE: Fix proper nouns ───────────────────────────────────

def strip_cantillation(heb):
    return re.sub(r'[\u0591-\u05BD\u05BF-\u05C7\u200D\uFEFF]', '', heb)

def get_base_letters(heb):
    return re.sub(r'[^\u05D0-\u05EA]', '', strip_cantillation(heb))


# ══════════════════════════════════════════════════════════════════════
#  APPLY ALL FIXES
# ══════════════════════════════════════════════════════════════════════

for ch in data["chapters"]:
    for v in ch["verses"]:
        # ── Fix words ──
        for w in v.get("words", []):
            eng = w.get("eng", "")
            heb = w.get("heb", "")
            base = get_base_letters(heb)

            # --- Corrupted glosses ---
            result = clean_eng(eng)
            if result:
                new_eng, category = result
                if new_eng != eng:
                    w["eng"] = new_eng
                    counters[category] += 1

            # --- Corrupted meanings ---
            meanings = w.get("meanings", [])
            if meanings:
                cleaned = [m for m in meanings if not is_bad_meaning(m)]
                removed = len(meanings) - len(cleaned)
                if removed > 0:
                    w["meanings"] = cleaned
                    counters["meanings_removed"] += removed

            # --- Proper noun fixes ---
            eng_now = w.get("eng", "")

            # יצחק glossed as "Abraham" -> "Isaac"
            if eng_now == "Abraham" and "יצחק" in base:
                w["eng"] = "Isaac"
                counters["proper_nouns_fixed"] += 1

            # אברם glossed as "with" -> "Abram" (includes את־אברם)
            if eng_now == "with" and "אברם" in base:
                w["eng"] = "Abram"
                counters["proper_nouns_fixed"] += 1

            # אברהם glossed as "there" -> "Abraham"
            if eng_now == "there" and "אברהם" in base:
                w["eng"] = "Abraham"
                counters["proper_nouns_fixed"] += 1

            # נח glossed as "went·out" -> "Noah"
            if eng_now == "went·out" and base == "נח":
                w["eng"] = "Noah"
                counters["proper_nouns_fixed"] += 1

        # ── Fix commentary HTML ──
        for field in COMMENTARY_FIELDS:
            val = v.get(field, "")
            if val and HTML_TAG_RE.search(val):
                cleaned = HTML_TAG_RE.sub("", val)
                if cleaned != val:
                    v[field] = cleaned
                    counters["html_stripped"] += 1


# ── 5. CRITICAL: Check Genesis 31:55 ────────────────────────────────
# In the Masoretic/Jewish numbering, chapter 31 has 54 verses.
# What Christians call 32:1 is sometimes listed as 31:55 in other numbering.
# Check current state:
ch31 = [c for c in data["chapters"] if c["chapter"] == 31][0]
ch32 = [c for c in data["chapters"] if c["chapter"] == 32][0]
last_v31 = ch31["verses"][-1]["verse"]
first_v32 = ch32["verses"][0]["verse"]

print(f"\nChapter 31: {len(ch31['verses'])} verses, last = {last_v31}")
print(f"Chapter 32: {len(ch32['verses'])} verses, first = {first_v32}")

# In the standard Masoretic text (BHS), Genesis 31 has 54 verses and 32 starts at 1.
# The JPS/Tanakh numbering has 31:55 = 32:1 in Christian Bibles.
# Since this is a Jewish text (Torah), check if we follow Masoretic (54 in ch31)
# or if we need to add 31:55.
# The Masoretic verse count for Gen 31 is indeed 55 (31:1-55),
# and Gen 32 starts at verse 1 (= Christian 32:2).
# Let's check if 32:1 content matches what should be 31:55.

v32_1_text = ch32["verses"][0].get("hebrew_full", "")
v32_1_stripped = strip_cantillation(v32_1_text)
print(f"Gen 32:1 hebrew: {v32_1_text[:100]}")

# In Masoretic numbering, Gen 31:55 is "וַיַּשְׁכֵּם לָבָן בַּבֹּקֶר..."
# (And Laban rose early in the morning...)
# Gen 32:1 (Masoretic) = "וַיֵּלֶךְ יַעֲקֹב לְדַרְכּוֹ..." (And Jacob went on his way...)
# Check what our 32:1 is (strip cantillation for reliable matching):
if "לבן" in get_base_letters(v32_1_text):
    print("32:1 contains Laban - this IS the missing 31:55 content")
    # Move it to 31:55
    verse_to_move = ch32["verses"].pop(0)
    verse_to_move["verse"] = 55
    verse_to_move["ref"] = "Vayetze 31:55"
    ch31["verses"].append(verse_to_move)
    # Renumber remaining ch32 verses (should start at 1 now = former 32:2)
    # Actually, if we moved 32:1 to 31:55, the remaining 32 verses should
    # already be numbered 2,3,4... We need to renumber them to 1,2,3...
    for i, vv in enumerate(ch32["verses"]):
        old_num = vv["verse"]
        new_num = old_num - 1
        vv["verse"] = new_num
        # Update ref if present
        if "ref" in vv:
            vv["ref"] = vv["ref"].replace(f":{old_num}", f":{new_num}")
    counters["verse_31_55"] = 1
    print("Moved 32:1 -> 31:55, renumbered ch32")
elif "יעקב" in get_base_letters(v32_1_text):
    # Check if 31:54 might contain what should be split
    v31_54_text = ch31["verses"][-1].get("hebrew_full", "")
    print(f"Gen 31:54 hebrew: {v31_54_text[:100]}")
    # The numbering may already be consistent (Christian numbering throughout)
    # In that case, 31 has 54 verses and 32:1 = Masoretic 31:55
    # This is a numbering convention choice. If the whole book uses Christian
    # numbering consistently, we should NOT add 31:55.
    print("Numbering appears to follow one consistent convention. No change needed.")

    # But let's verify: check another verse that differs between numbering systems
    # Actually, let's just check if ch32 has 33 verses (Christian) or 32 (Masoretic - since 32:1 moved to 31:55)
    print(f"Ch32 has {len(ch32['verses'])} verses")
else:
    print("Cannot determine 31:55 status from content. Skipping.")


# ── Save ─────────────────────────────────────────────────────────────
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("FIX SUMMARY")
print("=" * 60)
for k, v in counters.items():
    print(f"  {k}: {v}")
total = sum(counters.values())
print(f"  TOTAL fixes applied: {total}")
print(f"\nSaved to {OUTPUT}")
