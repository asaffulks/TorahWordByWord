#!/usr/bin/env python3
"""
Word-by-word audit: cross-check every Exodus word against
ETCBC glosses AND the verse's full English translation.
Flag anything that doesn't match either source.
"""
import json, re, sys
from collections import Counter
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

# Load data
with open(BASE / 'books' / 'torah' / 'exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(BASE / 'references' / 'etcbc_exodus_by_verse.json', 'r', encoding='utf-8') as f:
    etcbc = json.load(f)

# ── Synonym sets for matching ──
SYNONYMS = {}
GROUPS = [
    {'say','said','says','saying','spoke','speak','spoken','tell','told','declare','declared'},
    {'be','was','were','is','are','been','being','become','became','shall be'},
    {'make','made','do','did','done','does'},
    {'see','saw','seen','look','looked','appear','appeared','show','showed'},
    {'go','went','walk','walked','walking'},
    {'come','came','enter','entered','advance','advanced'},
    {'take','took','taken'},
    {'give','gave','given'},
    {'know','knew','known'},
    {'hear','heard','listen','listened'},
    {'eat','ate','eaten'},
    {'die','died','dead','death'},
    {'live','lived','living','alive','life'},
    {'bear','bore','born','begot','begat','give birth','gave birth'},
    {'send','sent'},
    {'build','built'},
    {'sit','sat','dwell','dwelt','dwelling','settled','inhabit','inhabited'},
    {'stand','stood','standing'},
    {'rise','rose','arose','arise','risen'},
    {'fall','fell','fallen'},
    {'return','returned'},
    {'fear','feared','afraid'},
    {'love','loved'},
    {'keep','kept','guard','guarded'},
    {'call','called'},
    {'kill','killed','slay','slew','slain','murder','murdered'},
    {'burn','burned','burnt'},
    {'open','opened'},
    {'close','closed','shut'},
    {'gather','gathered'},
    {'fill','filled','full'},
    {'turn','turned'},
    {'leave','left'},
    {'find','found'},
    {'bless','blessed'},
    {'serve','served','work','worked'},
    {'command','commanded'},
    {'god','gods','God'},
    {'lord','LORD','YHWH','Yahweh'},
    {'son','sons','child','children'},
    {'daughter','daughters'},
    {'man','men','person','human','mankind'},
    {'woman','wife','women','wives'},
    {'earth','land','ground'},
    {'heaven','heavens','sky'},
    {'water','waters'},
    {'day','days'},
    {'night','nights'},
    {'year','years'},
    {'house','houses'},
    {'king','kings'},
    {'hand','hands'},
    {'eye','eyes'},
    {'face','faces','presence','before'},
    {'name','names','named'},
    {'soul','life','person','being','creature'},
    {'spirit','wind','breath'},
    {'voice','sound'},
    {'word','words','thing','things','matter'},
    {'servant','servants','slave','slaves'},
    {'people','nation','nations'},
    {'seed','offspring','descendants'},
    {'blood','bloods'},
    {'all','every','each','whole'},
    {'not','no'},
    {'upon','on','over','above'},
    {'to','toward','towards','unto'},
    {'in','at','within'},
    {'from','out of','away from'},
    {'with','together with'},
    {'between','among'},
    {'because','that','for','since','when','if'},
    {'which','who','whom','whose','where','what','whoever'},
    {'priest','priests'},
    {'offering','offerings','sacrifice','sacrifices'},
    {'holy','holiness','sacred','sanctify','consecrate'},
    {'altar','altars'},
    {'tent','tents'},
    {'tabernacle','dwelling','mishkan'},
    {'mountain','mount','hill'},
    {'wilderness','desert'},
    {'plague','plagues','blow','strike','struck'},
    {'sign','signs'},
    {'wonder','wonders','miracle','miracles'},
    {'firstborn','first-born'},
    {'Egypt','Egyptian','Egyptians'},
    {'Israel','Israelite','Israelites'},
    {'Moses'},
    {'Aaron'},
    {'Pharaoh'},
]

for group in GROUPS:
    for word in group:
        SYNONYMS[word.lower()] = group


def words_match(our_eng, reference):
    """Check if our English gloss matches a reference gloss (ETCBC or translation word)."""
    if not our_eng or not reference:
        return False

    our = our_eng.lower().replace('·', ' ').replace('-', ' ').strip()
    ref = reference.lower().replace('·', ' ').replace('-', ' ').strip()

    # Direct match
    if our == ref:
        return True

    # One contains the other
    if our in ref or ref in our:
        return True

    # Any word overlap
    our_words = set(our.split())
    ref_words = set(ref.split())

    # Remove function words
    skip = {'the','a','an','of','to','in','for','and','or','is','was','with','from','by','on','at','it','he','she','they','his','her','their','its','my','your','our','not','no','this','that','these','those'}
    our_content = our_words - skip
    ref_content = ref_words - skip

    if our_content & ref_content:
        return True

    # Synonym match
    for ow in our_content:
        for rw in ref_content:
            ow_group = SYNONYMS.get(ow, {ow})
            if rw in ow_group:
                return True
            rw_group = SYNONYMS.get(rw, {rw})
            if ow in rw_group:
                return True

    # Stem match (first 4 chars)
    for ow in our_content:
        for rw in ref_content:
            if len(ow) >= 4 and len(rw) >= 4 and ow[:4] == rw[:4]:
                return True

    return False


def check_against_translation(verse_words, translation):
    """Check which words are plausibly in the verse translation."""
    if not translation:
        return [True] * len(verse_words)  # Can't check, assume ok

    trans_lower = translation.lower()
    trans_words = set(re.findall(r'[a-zA-Z]+', trans_lower))

    results = []
    for w in verse_words:
        eng = w.get('eng', '')
        if not eng:
            results.append(False)
            continue

        eng_clean = eng.lower().replace('·', ' ').replace('(object marker)', '').strip()
        eng_parts = set(eng_clean.split())
        eng_parts -= {'the','a','an','of','to','in','for','and','or'}

        # Check if any content word appears in translation
        found = False
        for part in eng_parts:
            if part in trans_words:
                found = True
                break
            # Check synonyms
            group = SYNONYMS.get(part, set())
            if group & trans_words:
                found = True
                break
            # Stem match
            for tw in trans_words:
                if len(part) >= 4 and len(tw) >= 4 and part[:4] == tw[:4]:
                    found = True
                    break
            if found:
                break

        results.append(found)
    return results


def align_etcbc(our_words, etcbc_morphemes):
    """Align our words to ETCBC and return glosses per word."""
    result = []
    ei = 0

    for w in our_words:
        our_cons = strip_n(w['heb']).replace('\u05BE', '').replace(' ', '')
        if ei >= len(etcbc_morphemes):
            result.append([])
            continue

        acc = ''
        matched = False
        for count in range(1, min(10, len(etcbc_morphemes) - ei + 1)):
            acc += etcbc_morphemes[ei + count - 1]['cons'].replace(' ', '')
            if acc == our_cons:
                glosses = []
                for j in range(ei, ei + count):
                    g = etcbc_morphemes[j]['gloss']
                    if g:
                        glosses.append(g)
                result.append(glosses)
                ei += count
                matched = True
                break

        if not matched:
            if ei < len(etcbc_morphemes):
                g = etcbc_morphemes[ei].get('gloss', '')
                result.append([g] if g else [])
                ei += 1
            else:
                result.append([])

    return result


# ── Run audit ──

flagged = []
total_words = 0
total_ok = 0

for ch in data['chapters']:
    for v in ch['verses']:
        ref = f"{ch['chapter']}:{v['verse']}"
        words = v.get('words', [])
        translation = v.get('translation', '')
        etcbc_verse = etcbc.get(ref, [])

        # Check against translation
        trans_ok = check_against_translation(words, translation)

        # Check against ETCBC
        etcbc_alignment = align_etcbc(words, etcbc_verse)

        for i, w in enumerate(words):
            total_words += 1
            eng = w.get('eng', '')

            # Skip common function words / object markers - these are fine
            if eng in ('(object marker)', 'and', 'the', 'to', 'in', 'from', 'not', 'which', 'upon', 'with', 'all', 'because', 'if', 'also', 'so', 'yet', 'now', 'this', 'that', 'these', 'behold', 'and·behold', 'I', 'he', 'she', 'they', 'you', 'we', 'before', 'between', 'until', 'but', 'LORD', 'God', 'Moses', 'Aaron', 'Pharaoh', 'Israel', 'Egypt'):
                total_ok += 1
                continue
            if eng.startswith('(object marker)'):
                total_ok += 1
                continue
            if eng.startswith('and·') and len(eng) < 20:
                total_ok += 1
                continue

            # Check ETCBC
            etcbc_glosses = etcbc_alignment[i] if i < len(etcbc_alignment) else []
            etcbc_match = any(words_match(eng, g) for g in etcbc_glosses)

            # Check translation
            trans_match = trans_ok[i] if i < len(trans_ok) else True

            if etcbc_match or trans_match:
                total_ok += 1
                continue

            # FLAGGED: doesn't match either source
            etcbc_str = '|'.join(etcbc_glosses) if etcbc_glosses else '(no ETCBC)'
            flagged.append({
                'ref': ref,
                'idx': i,
                'heb': w['heb'],
                'our': eng,
                'etcbc': etcbc_str,
                'translation': translation[:80] if translation else '(none)',
            })

print(f"Total words: {total_words}")
print(f"OK (matched source): {total_ok}")
print(f"Flagged (no match): {len(flagged)}")
print(f"Match rate: {100*total_ok/total_words:.1f}%")
print()

# Categorize flagged items
categories = Counter()
for f in flagged:
    eng = f['our']
    if 'to ' in eng.lower() and eng.lower().startswith('to '):
        categories['infinitive (to X)'] += 1
    elif any(c.isupper() for c in eng) and '·' not in eng:
        categories['proper noun'] += 1
    elif len(eng) > 25:
        categories['too long'] += 1
    elif eng.startswith('(') or eng.endswith(')'):
        categories['parenthetical'] += 1
    else:
        categories['other'] += 1

print("=== FLAGGED BY CATEGORY ===")
for cat, count in categories.most_common():
    print(f"  {cat}: {count}")

print()
print("=== SAMPLE FLAGGED WORDS (first 60) ===")
for f in flagged[:60]:
    print(f"  {f['ref']:>8s}[{f['idx']:2d}] {f['heb']}")
    print(f"           ours:  {f['our']}")
    print(f"           etcbc: {f['etcbc']}")
    print()

# Save full report
report_path = BASE / 'exodus_audit_report.json'
with open(report_path, 'w', encoding='utf-8') as fp:
    json.dump(flagged, fp, ensure_ascii=False, indent=2)
print(f"Full report: {report_path} ({len(flagged)} items)")
