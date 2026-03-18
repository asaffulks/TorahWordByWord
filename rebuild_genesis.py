#!/usr/bin/env python3
"""
Rebuild Genesis — Per-Verse ETCBC Alignment + Sefaria-First Translation
========================================================================
For each verse:
  1. Align ETCBC words to our words (per-verse, no cascade)
  2. For each word, check if current translation matches ETCBC gloss
  3. If wrong, get replacement from Sefaria (improved), Strong's, or ETCBC
  4. Collect alternative meanings from all 3 sources

Output: genesis_fixed.json
"""

import json, os, re, sys, html as htmlmod
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path('K:/TorahByWord')
SEFARIA_CACHE = BASE / 'sefaria_cache'

def strip_nikud(text):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', text)


# ─── Load ETCBC per-verse data ─────────────────────────────────────────────

def load_etcbc_by_verse():
    print("Loading ETCBC per-verse alignment...")
    with open(BASE / 'references' / 'etcbc_genesis_by_verse.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  {len(data)} verses")
    return data


# ─── Load Strong's/BDB ────────────────────────────────────────────────────

def load_strongs():
    print("Loading Strong's/BDB...")
    tree = ET.parse(str(BASE / 'references' / 'HebrewStrong.xml'))
    root = tree.getroot()
    ns = {'ns': 'http://openscriptures.github.com/morphhb/namespace'}
    ref = defaultdict(list)
    for entry in root.findall('.//ns:entry', ns):
        w = entry.find('ns:w', ns)
        if w is None: continue
        lang = w.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        if lang not in ('heb', 'x-pn'): continue
        hebrew = w.text or ''
        if not hebrew: continue
        defs = []
        me = entry.find('ns:meaning', ns)
        if me is not None:
            de = me.find('ns:def', ns)
            if de is not None and de.text:
                defs.append(de.text.strip().strip('.'))
        ue = entry.find('ns:usage', ns)
        if ue is not None and ue.text:
            for p in ue.text.split(',')[:6]:
                p = re.sub(r'^[+×]\s*', '', p.strip().strip('.'))
                if p and 1 < len(p) < 40 and not p.startswith('Compare'):
                    defs.append(p)
        if defs:
            seen = set()
            unique = [d for d in defs if d.lower() not in seen and not seen.add(d.lower())]
            ref[strip_nikud(hebrew)].append(unique[:8])
    print(f"  {len(ref)} roots")
    return dict(ref)


# ─── Improved Sefaria Lookup ──────────────────────────────────────────────

JUNK = {'adj', 'n m', 'n f', 'v', 'vb', 'prep', 'conj', 'pron', 'adv',
        'subst', 'interj', 'n m/f', 'n pr m', 'n pr', 'n pr f',
        'sign of the definite direct object', '(relative part.)',
        'not translated in English', '—BonkZAW 1891',
        'Commonly transcribed YHWH', 'n pr loc'}

_sef_cache = {}

def sefaria_lookup(hebrew_word):
    """Get all meanings from Sefaria with smart entry selection.
    Returns: (best_definition, [all_meanings])"""
    cons = strip_nikud(hebrew_word).replace('\u05BE', '')
    if cons in _sef_cache:
        return _sef_cache[cons]

    candidates_to_try = [cons]
    # Strip common prefixes
    for pfx in ['ו', 'ה', 'ב', 'ל', 'מ', 'כ', 'שׁ', 'שׂ',
                 'וה', 'וב', 'ול', 'ומ', 'הת']:
        if cons.startswith(pfx) and len(cons) > len(pfx) + 1:
            candidates_to_try.append(cons[len(pfx):])
    # Maqaf parts
    if '\u05BE' in hebrew_word:
        for part in hebrew_word.split('\u05BE'):
            p = strip_nikud(part)
            if p and len(p) >= 2:
                candidates_to_try.append(p)

    best = ''
    all_meanings = []
    seen = set()

    for cand in candidates_to_try:
        safe = re.sub(r'[<>:"/\\|?*()[\]{}]', '', cand)
        cf = SEFARIA_CACHE / f"word_{safe}.json"
        if not cf.exists():
            continue
        try:
            with open(cf, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue
        if not isinstance(data, list):
            continue

        for entry in data:
            if not isinstance(entry, dict): continue
            hw = strip_nikud(entry.get('headword', ''))
            content = entry.get('content', {})
            if not isinstance(content, dict): continue

            for sense in content.get('senses', [])[:6]:
                if not isinstance(sense, dict): continue
                defn = sense.get('definition', '')
                if not isinstance(defn, str): continue
                clean = re.sub(r'<[^>]+>', '', defn)
                clean = htmlmod.unescape(clean).strip()
                for part in clean.split(',')[:3]:
                    part = part.strip().strip('.')
                    if not part or len(part) <= 1 or len(part) >= 50:
                        continue
                    if part.lower() in seen or part.lower() in JUNK:
                        continue
                    # Score: exact headword match is best
                    if not best and hw == cand:
                        best = part
                    all_meanings.append(part)
                    seen.add(part.lower())

                for sub in sense.get('senses', [])[:3]:
                    if isinstance(sub, dict):
                        sd = sub.get('definition', '')
                        if isinstance(sd, str):
                            cs = re.sub(r'<[^>]+>', '', sd)
                            cs = htmlmod.unescape(cs).strip()
                            for part in cs.split(',')[:2]:
                                part = part.strip().strip('.')
                                if part and 1 < len(part) < 50 and part.lower() not in seen and part.lower() not in JUNK:
                                    all_meanings.append(part)
                                    seen.add(part.lower())

    if not best and all_meanings:
        best = all_meanings[0]

    result = (best, all_meanings[:8])
    _sef_cache[cons] = result
    return result


# ─── Per-Verse Word Alignment ─────────────────────────────────────────────

def align_words_in_verse(our_words, etcbc_words):
    """Align ETCBC split-prefix words to our joined words within a single verse.
    Returns: list of lists — etcbc glosses per our-word position."""
    result = []
    ei = 0

    for w in our_words:
        our_cons = strip_nikud(w['heb']).replace('\u05BE', '').replace(' ', '')
        if ei >= len(etcbc_words):
            result.append([])
            continue

        acc = ''
        matched = False
        for count in range(1, min(10, len(etcbc_words) - ei + 1)):
            acc += strip_nikud(etcbc_words[ei + count - 1]['cons']).replace(' ', '')
            if acc == our_cons:
                glosses = []
                for j in range(ei, ei + count):
                    g = etcbc_words[j]['gloss']
                    if g:
                        glosses.append(g)
                result.append(glosses)
                ei += count
                matched = True
                break

        if not matched:
            g = etcbc_words[ei]['gloss'] if ei < len(etcbc_words) else ''
            result.append([g] if g else [])
            ei += 1

    return result


# ─── Translation Matching ─────────────────────────────────────────────────

# Maps ETCBC gloss -> set of acceptable English forms in our translations
EQUIV = {
    'say': {'said', 'say', 'says', 'saying', 'he·said', 'and·said', 'and·he·said'},
    'be': {'was', 'were', 'is', 'are', 'been', 'being', 'become', 'became', 'it·was',
           'let·there·be', 'and·was', 'and·it·was', 'there·was'},
    'create': {'created', 'create', 'and·created'},
    'see': {'saw', 'seen', 'see', 'and·saw', 'look', 'looked', 'appear', 'appeared', 'and·appear'},
    'make': {'made', 'make', 'and·made', 'do', 'did', 'done'},
    'call': {'called', 'call', 'and·called'},
    'separate': {'separated', 'separate', 'divided', 'and·divided', 'and·separated'},
    'give': {'gave', 'give', 'given', 'and·gave'},
    'go': {'went', 'go', 'walk', 'walked', 'and·went'},
    'come': {'came', 'come', 'enter', 'entered', 'advanced'},
    'go out': {'went·out', 'go·out', 'brought·forth', 'and·brought·forth'},
    'take': {'took', 'take', 'taken', 'and·took'},
    'know': {'knew', 'know', 'known', 'and·knew'},
    'hear': {'heard', 'hear', 'and·heard', 'listen', 'listened'},
    'eat': {'ate', 'eat', 'eaten', 'freely·eat', 'you·shall·eat'},
    'die': {'died', 'die', 'dead', 'death', 'surely·die'},
    'live': {'lived', 'live', 'living', 'alive', 'life', 'a·living'},
    'bear': {'bore', 'born', 'bear', 'begot', 'begat', 'gave·birth'},
    'send': {'sent', 'send', 'and·sent'},
    'build': {'built', 'build'},
    'speak': {'spoke', 'speak', 'spoken'},
    'sit': {'sat', 'sit', 'dwell', 'dwelt', 'dwelling', 'settled', 'inhabited'},
    'stand': {'stood', 'stand', 'standing'},
    'rise': {'rose', 'risen', 'rise', 'arose', 'arise'},
    'fall': {'fell', 'fall', 'fallen'},
    'return': {'returned', 'return'},
    'go down': {'went·down', 'descend', 'descended'},
    'go up': {'went·up', 'ascend', 'ascended'},
    'fear': {'feared', 'fear', 'afraid'},
    'love': {'loved', 'love'},
    'bless': {'blessed', 'bless', 'and·blessed'},
    'swear': {'swore', 'swear', 'sworn'},
    'keep': {'kept', 'keep', 'guard', 'guarded'},
    'fill': {'filled', 'fill', 'full', 'and·fill'},
    'gather': {'gathered', 'gather'},
    'grow': {'grew', 'grow', 'grown'},
    'rule': {'ruled', 'rule', 'reign', 'reigned', 'dominion'},
    'set': {'set', 'put', 'place', 'placed', 'and·placed'},
    'plant': {'planted', 'plant'},
    'form': {'formed', 'form', 'and·formed'},
    'breathe': {'breathed', 'breathe', 'and·breathed'},
    'serve': {'served', 'serve', 'work', 'worked', 'till'},
    'touch': {'touched', 'touch'},
    'multiply': {'multiplied', 'multiply', 'and·multiply'},
    'be fertile': {'fruitful', 'be·fruitful'},
    'be many': {'multiply', 'multiplied', 'and·multiply', 'great', 'be·great'},
    'be full': {'fill', 'filled', 'and·fill', 'full'},
    'subdue': {'subdue', 'subdued', 'and·subdue·it'},
    'tread, to rule': {'rule', 'and·rule', 'dominion'},
    'sow': {'bearing', 'sowing', 'sow'},
    'swarm': {'teem', 'swarming', 'swarm'},
    'walk': {'go', 'went', 'walk', 'walked'},
    'sell': {'sold', 'sell'},
    'buy': {'bought', 'buy'},
    'bury': {'buried', 'bury'},
    'find': {'found', 'find'},
    'burn': {'burned', 'burnt', 'burn'},
    'destroy': {'destroyed', 'destroy'},
    'open': {'opened', 'open'},
    'close': {'closed', 'close', 'shut'},
    'leave': {'left', 'leave', 'forsake'},
    'cling': {'clung', 'cling', 'cleave'},
    'weep': {'wept', 'weep', 'cry', 'cried'},
    'laugh': {'laughed', 'laugh'},
    'bow down': {'bowed', 'bow', 'prostrated'},
    'shape': {'formed', 'form', 'and·formed'},

    # Nouns
    'god(s)': {'god', 'gods', 'God'},
    'YHWH': {'lord', 'LORD', 'yhwh', 'YHWH', 'Yahweh'},
    'son': {'son', 'sons', 'child', 'children', 'ben'},
    'daughter': {'daughter', 'daughters'},
    'human, mankind': {'man', 'Adam', 'the·man'},
    'woman': {'woman', 'wife'},
    'earth': {'earth', 'land', 'ground', 'the·earth', 'the·land'},
    'heavens': {'heaven', 'heavens', 'sky', 'the·heavens'},
    'water': {'water', 'waters', 'the·waters'},
    'light': {'light', 'the·light'},
    'darkness': {'darkness', 'dark', 'the·darkness'},
    'day': {'day', 'days'},
    'night': {'night', 'nights'},
    'name': {'name', 'named'},
    'soul': {'soul', 'life', 'person', 'being', 'creature', 'a·living'},
    'face': {'face', 'faces', 'surface', 'presence', 'the·face·of'},
    'seed': {'seed', 'offspring', 'descendants'},
    'serpent': {'serpent', 'snake', 'the·serpent'},
    'shrewd': {'cunning', 'crafty', 'subtle', 'more·cunning'},
    'whole': {'all', 'every', 'each', 'any', 'whole'},
    'wild animal': {'beast', 'creature', 'living·creature', 'beast·of'},
    'open field': {'field', 'the·field'},
    'firmament': {'firmament', 'expanse', 'the·expanse'},
    'wind': {'spirit', 'wind', 'breath', 'the·spirit·of'},
    'male': {'male'},
    'female': {'female'},
    'image': {'image', 'his·image', 'the·image·of', 'in·his·image', 'in·the·image·of'},
    'interval': {'between', 'among'},
    'mother': {'mother', 'mothers'},
    'father': {'father', 'fathers'},
    'brother': {'brother', 'brothers'},
    'silver': {'silver', 'money'},
    'cattle': {'cattle', 'livestock', 'herd', 'herds'},
    'soil': {'ground', 'the·ground'},
    'tree': {'tree', 'trees', 'wood'},
    'garden': {'garden', 'the·garden'},
    'not': {'not', 'no'},
    'alive': {'living', 'alive', 'life'},
    '<object marker>': {'[identifies object]', '[object]', 'object', 'identifies'},
    'saying': {'saying', 'to·say'},
    'herb': {'plant', 'plants', 'herb'},
    'fruit': {'fruit', 'fruits'},
    'fish': {'fish'},
    'bird': {'bird', 'birds', 'fowl'},
    'sea': {'sea', 'seas'},
    'creep': {'creeps', 'creeping', 'crawling', 'moves'},
    'kind': {'kind', 'its·kind', 'after·its·kind', 'their·kind'},
    'morning': {'morning'},
    'evening': {'evening'},
    'dust': {'dust'},
    'rib': {'rib', 'ribs'},
    'side': {'rib', 'side', 'his·ribs'},
    'bone': {'bone', 'bones'},
    'naked': {'naked', 'bare'},
    'clothing': {'garment', 'garments', 'clothing', 'coats'},
    'tent': {'tent', 'tents'},
    'altar': {'altar'},
    'sword': {'sword'},
    'blood': {'blood'},
    'voice': {'voice'},
    'sound': {'voice', 'sound'},
    'covenant': {'covenant'},
    'head': {'head', 'top', 'chief'},
    'foot': {'foot', 'feet'},
    'hand': {'hand', 'hands'},
    'eye': {'eye', 'eyes'},
    'good': {'good'},
    'bad': {'evil', 'bad', 'wicked'},
    'great': {'great', 'big', 'large'},
    'small': {'small', 'little', 'young'},
    'old': {'old', 'elder', 'aged'},
    'new': {'new'},
    'much': {'much', 'many', 'abundant'},
    'there': {'there'},
    'thus': {'so', 'thus'},
}

# Build reverse: acceptable_word -> set of ETCBC glosses
REV = defaultdict(set)
for eg, forms in EQUIV.items():
    for f in forms:
        REV[f.lower()].add(eg)
    REV[eg.lower()].add(eg)


def translation_matches_gloss(our_eng, etcbc_glosses):
    """Check if our translation is correct based on ETCBC glosses."""
    if not etcbc_glosses or not our_eng:
        return False

    our_parts = set(our_eng.lower().replace('·', ' ').split())
    # Remove trivial function words for matching
    content = {p for p in our_parts if p not in ('the', 'and', 'of', 'a', 'an', 'to', 'in', 'for')}

    for gloss in etcbc_glosses:
        g = gloss.lower()
        if g in ('the', 'and', 'to', 'in', 'from'):
            continue

        # Direct match
        if g in content or any(g in p or p in g for p in content if len(p) >= 3):
            return True

        # Synonym match
        if g in EQUIV:
            if content & {f.lower().replace('·', ' ') for f in EQUIV[g]}:
                return True
            # Check if any of our parts appear in the acceptable forms
            for p in content:
                for f in EQUIV[g]:
                    if p in f.lower() or f.lower() in p:
                        return True

        # Reverse: check if any of our words are known forms of this gloss
        for p in content:
            if p in REV:
                if g in REV[p] or any(g.startswith(r[:3]) for r in REV[p]):
                    return True

        # Stem match (last resort)
        for p in content:
            if len(p) >= 4 and len(g) >= 4:
                if p[:4] == g[:4]:
                    return True

    return False


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Genesis Rebuild — Per-Verse Aligned, Sefaria-First")
    print("=" * 60)

    etcbc_by_verse = load_etcbc_by_verse()
    strongs = load_strongs()

    with open(BASE / 'genesis.json', 'r', encoding='utf-8') as f:
        genesis = json.load(f)

    total = 0
    kept = 0
    fixed_sef = 0
    fixed_str = 0
    fixed_etc = 0
    no_etcbc = 0
    log_lines = []

    for ch in genesis['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            ref = f"{ch_num}:{v_num}"
            our_words = v.get('words', [])
            etcbc_verse = etcbc_by_verse.get(ref)

            if not etcbc_verse:
                # No ETCBC alignment for this verse — keep as-is, just add meanings
                for w in our_words:
                    total += 1
                    no_etcbc += 1
                    _, meanings = sefaria_lookup(w['heb'])
                    w['meanings'] = meanings[:6]
                continue

            # Align ETCBC words to our words
            alignment = align_words_in_verse(our_words, etcbc_verse)

            for i, w in enumerate(our_words):
                total += 1
                old_eng = w['eng']
                hebrew = w['heb']
                etcbc_glosses = alignment[i] if i < len(alignment) else []

                # Check if current translation is correct
                if translation_matches_gloss(old_eng, etcbc_glosses):
                    kept += 1
                    new_eng = old_eng
                else:
                    # WRONG — fix it
                    new_eng = None

                    # Try Sefaria first
                    sef_eng, _ = sefaria_lookup(hebrew)
                    if sef_eng and translation_matches_gloss(sef_eng, etcbc_glosses):
                        new_eng = sef_eng
                        fixed_sef += 1
                    else:
                        # Try Strong's
                        cons = strip_nikud(hebrew).replace('\u05BE', '')
                        for pfx_len in range(0, min(4, len(cons))):
                            sub = cons[pfx_len:]
                            if sub in strongs:
                                for defs in strongs[sub]:
                                    for d in defs:
                                        if translation_matches_gloss(d, etcbc_glosses):
                                            new_eng = d
                                            fixed_str += 1
                                            break
                                    if new_eng:
                                        break
                            if new_eng:
                                break

                    # Last resort: use ETCBC gloss directly
                    if not new_eng:
                        content = [g for g in etcbc_glosses
                                   if g not in ('<object marker>', '<relative>')]
                        if content:
                            new_eng = '·'.join(etcbc_glosses)
                            fixed_etc += 1
                        elif etcbc_glosses:
                            new_eng = '·'.join(etcbc_glosses)
                            fixed_etc += 1
                        else:
                            new_eng = old_eng
                            kept += 1

                    if new_eng != old_eng:
                        log_lines.append(f"  {ref}[{i}] {hebrew}: '{old_eng}' -> '{new_eng}'")

                # Collect meanings from all sources
                _, sef_meanings = sefaria_lookup(hebrew)
                all_alt = set(sef_meanings)
                cons = strip_nikud(hebrew).replace('\u05BE', '')
                for pfx_len in range(0, min(4, len(cons))):
                    sub = cons[pfx_len:]
                    if sub in strongs:
                        for defs in strongs[sub]:
                            all_alt.update(defs)
                for g in etcbc_glosses:
                    if g not in ('<object marker>', '<relative>'):
                        all_alt.add(g)

                primary_lower = new_eng.lower().replace('·', ' ') if new_eng else ''
                meanings = [m for m in sorted(all_alt)
                           if m.lower() != primary_lower
                           and m.lower() not in primary_lower
                           and primary_lower not in m.lower()
                           and 1 < len(m) < 50
                           and m.lower() not in JUNK]

                w['eng'] = new_eng
                w['meanings'] = meanings[:6]

        if ch_num % 10 == 0:
            print(f"  Chapter {ch_num} done...")

    # Save
    with open(BASE / 'genesis_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(genesis, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Total words:      {total}")
    print(f"  Kept (correct):   {kept} ({100*kept/total:.1f}%)")
    print(f"  Fixed (Sefaria):  {fixed_sef}")
    print(f"  Fixed (Strong's): {fixed_str}")
    print(f"  Fixed (ETCBC):    {fixed_etc}")
    print(f"  No ETCBC data:    {no_etcbc}")
    print(f"  Output: genesis_fixed.json")
    print(f"{'=' * 60}")

    # Show fixes for key verses
    print(f"\nTotal changes: {len(log_lines)}")
    print("\nKey fixes:")
    key_verses = {'1:27', '1:28', '1:29', '1:30', '3:1', '3:2', '3:3',
                  '3:5', '3:6', '3:20', '49:10'}
    for line in log_lines:
        for kv in key_verses:
            if line.strip().startswith(kv + '['):
                print(line)
                break

    # Spot checks
    print("\nSpot-checks:")
    r = genesis
    checks = [
        (1, 27, 6, 'created/create'),
        (1, 28, 2, 'God'),
        (1, 28, 3, 'said'),
        (3, 1, 7, 'made/make'),
        (3, 1, 8, 'LORD/YHWH'),
        (3, 1, 10, 'said/say'),
        (3, 1, 14, 'God'),
        (3, 20, 2, 'name'),
        (3, 20, 8, 'mother'),
    ]
    for ch, vs, wi, expected in checks:
        word = r['chapters'][ch-1]['verses'][vs-1]['words'][wi]
        eng = word['eng'].lower()
        ok = any(e.lower() in eng for e in expected.split('/'))
        print(f"  {'✓' if ok else '✗'} Gen {ch}:{vs}[{wi}] {word['heb']}: '{word['eng']}' (expect '{expected}')")


if __name__ == '__main__':
    main()
