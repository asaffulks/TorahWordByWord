#!/usr/bin/env python3
"""
Rebuild Book — Per-Verse ETCBC Alignment + Sefaria-First Translation
=====================================================================
For each verse in a given book:
  1. Align ETCBC words to our words (per-verse, no cascade)
  2. For each word, check if current translation matches ETCBC gloss
  3. If wrong, get replacement from Sefaria (improved), Strong's, or ETCBC
  4. Collect alternative meanings from all 3 sources

Usage:
  python rebuild_book.py exodus
  python rebuild_book.py leviticus numbers deuteronomy
  python rebuild_book.py all          # all Torah books except Genesis

Output: books/torah/{book}_fixed.json
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

# Map CLI names to file paths
BOOK_CONFIG = {
    'exodus': {
        'json': BASE / 'books' / 'torah' / 'exodus.json',
        'etcbc': BASE / 'references' / 'etcbc_exodus_by_verse.json',
        'output': BASE / 'books' / 'torah' / 'exodus_fixed.json',
        'display': 'Exodus',
    },
    'leviticus': {
        'json': BASE / 'books' / 'torah' / 'leviticus.json',
        'etcbc': BASE / 'references' / 'etcbc_leviticus_by_verse.json',
        'output': BASE / 'books' / 'torah' / 'leviticus_fixed.json',
        'display': 'Leviticus',
    },
    'numbers': {
        'json': BASE / 'books' / 'torah' / 'numbers.json',
        'etcbc': BASE / 'references' / 'etcbc_numbers_by_verse.json',
        'output': BASE / 'books' / 'torah' / 'numbers_fixed.json',
        'display': 'Numbers',
    },
    'deuteronomy': {
        'json': BASE / 'books' / 'torah' / 'deuteronomy.json',
        'etcbc': BASE / 'references' / 'etcbc_deuteronomy_by_verse.json',
        'output': BASE / 'books' / 'torah' / 'deuteronomy_fixed.json',
        'display': 'Deuteronomy',
    },
}


def strip_nikud(text):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', text)


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
        'not translated in English', '\u2014BonkZAW 1891',
        'Commonly transcribed YHWH', 'n pr loc'}

_sef_cache = {}

def sefaria_lookup(hebrew_word):
    """Get all meanings from Sefaria with smart entry selection."""
    cons = strip_nikud(hebrew_word).replace('\u05BE', '')
    if cons in _sef_cache:
        return _sef_cache[cons]

    candidates_to_try = [cons]
    for pfx in ['\u05D5', '\u05D4', '\u05D1', '\u05DC', '\u05DE', '\u05DB',
                '\u05E9\u05C1', '\u05E9\u05C2',
                '\u05D5\u05D4', '\u05D5\u05D1', '\u05D5\u05DC', '\u05D5\u05DE', '\u05D4\u05EA']:
        if cons.startswith(pfx) and len(cons) > len(pfx) + 1:
            candidates_to_try.append(cons[len(pfx):])
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
    """Align ETCBC split-prefix words to our joined words within a single verse."""
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

EQUIV = {
    'say': {'said', 'say', 'says', 'saying', 'he\u00B7said', 'and\u00B7said', 'and\u00B7he\u00B7said'},
    'be': {'was', 'were', 'is', 'are', 'been', 'being', 'become', 'became', 'it\u00B7was',
           'let\u00B7there\u00B7be', 'and\u00B7was', 'and\u00B7it\u00B7was', 'there\u00B7was'},
    'create': {'created', 'create', 'and\u00B7created'},
    'see': {'saw', 'seen', 'see', 'and\u00B7saw', 'look', 'looked', 'appear', 'appeared', 'and\u00B7appear'},
    'make': {'made', 'make', 'and\u00B7made', 'do', 'did', 'done'},
    'call': {'called', 'call', 'and\u00B7called'},
    'separate': {'separated', 'separate', 'divided', 'and\u00B7divided', 'and\u00B7separated'},
    'give': {'gave', 'give', 'given', 'and\u00B7gave'},
    'go': {'went', 'go', 'walk', 'walked', 'and\u00B7went'},
    'come': {'came', 'come', 'enter', 'entered', 'advanced'},
    'go out': {'went\u00B7out', 'go\u00B7out', 'brought\u00B7forth', 'and\u00B7brought\u00B7forth'},
    'take': {'took', 'take', 'taken', 'and\u00B7took'},
    'know': {'knew', 'know', 'known', 'and\u00B7knew'},
    'hear': {'heard', 'hear', 'and\u00B7heard', 'listen', 'listened'},
    'eat': {'ate', 'eat', 'eaten', 'freely\u00B7eat', 'you\u00B7shall\u00B7eat'},
    'die': {'died', 'die', 'dead', 'death', 'surely\u00B7die'},
    'live': {'lived', 'live', 'living', 'alive', 'life', 'a\u00B7living'},
    'bear': {'bore', 'born', 'bear', 'begot', 'begat', 'gave\u00B7birth'},
    'send': {'sent', 'send', 'and\u00B7sent'},
    'build': {'built', 'build'},
    'speak': {'spoke', 'speak', 'spoken'},
    'sit': {'sat', 'sit', 'dwell', 'dwelt', 'dwelling', 'settled', 'inhabited'},
    'stand': {'stood', 'stand', 'standing'},
    'rise': {'rose', 'risen', 'rise', 'arose', 'arise'},
    'fall': {'fell', 'fall', 'fallen'},
    'return': {'returned', 'return'},
    'go down': {'went\u00B7down', 'descend', 'descended'},
    'go up': {'went\u00B7up', 'ascend', 'ascended'},
    'fear': {'feared', 'fear', 'afraid'},
    'love': {'loved', 'love'},
    'bless': {'blessed', 'bless', 'and\u00B7blessed'},
    'swear': {'swore', 'swear', 'sworn'},
    'keep': {'kept', 'keep', 'guard', 'guarded'},
    'fill': {'filled', 'fill', 'full', 'and\u00B7fill'},
    'gather': {'gathered', 'gather'},
    'grow': {'grew', 'grow', 'grown'},
    'rule': {'ruled', 'rule', 'reign', 'reigned', 'dominion'},
    'set': {'set', 'put', 'place', 'placed', 'and\u00B7placed'},
    'plant': {'planted', 'plant'},
    'form': {'formed', 'form', 'and\u00B7formed'},
    'breathe': {'breathed', 'breathe', 'and\u00B7breathed'},
    'serve': {'served', 'serve', 'work', 'worked', 'till'},
    'touch': {'touched', 'touch'},
    'multiply': {'multiplied', 'multiply', 'and\u00B7multiply'},
    'be fertile': {'fruitful', 'be\u00B7fruitful'},
    'be many': {'multiply', 'multiplied', 'and\u00B7multiply', 'great', 'be\u00B7great'},
    'be full': {'fill', 'filled', 'and\u00B7fill', 'full'},
    'subdue': {'subdue', 'subdued', 'and\u00B7subdue\u00B7it'},
    'tread, to rule': {'rule', 'and\u00B7rule', 'dominion'},
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
    'shape': {'formed', 'form', 'and\u00B7formed'},
    # Exodus-relevant additions
    'smite': {'smote', 'struck', 'strike', 'hit'},
    'stretch out': {'stretched', 'stretch'},
    'harden': {'hardened', 'harden', 'heavy', 'stubborn'},
    'redeem': {'redeemed', 'redeem', 'ransom'},
    'command': {'commanded', 'command'},
    'sanctify': {'sanctified', 'sanctify', 'holy', 'consecrate', 'consecrated'},
    'sacrifice': {'sacrificed', 'sacrifice', 'offer', 'offered'},
    'camp': {'camped', 'encamp', 'encamped'},
    'cry': {'cried', 'cry', 'shout', 'shouted'},
    'deliver': {'delivered', 'deliver', 'save', 'saved'},
    'judge': {'judged', 'judge'},
    'praise': {'praised', 'praise'},
    'sing': {'sang', 'sing', 'sung'},
    'turn': {'turned', 'turn'},
    'pass over': {'passed', 'pass'},
    'write': {'wrote', 'write', 'written'},
    'count': {'counted', 'count', 'number', 'numbered'},
    'dwell': {'dwelt', 'dwell', 'sit', 'sat', 'inhabit', 'inhabited'},
    'wage war': {'fight', 'fought', 'war', 'battle'},
    'inherit': {'inherited', 'inherit', 'possess', 'possessed'},
    'remember': {'remembered', 'remember'},
    'forget': {'forgot', 'forget', 'forgotten'},
    'cover': {'covered', 'cover'},
    'atone': {'atoned', 'atone', 'atonement'},
    'sprinkle': {'sprinkled', 'sprinkle'},
    'slaughter': {'slaughtered', 'slaughter', 'kill', 'killed'},
    'wash': {'washed', 'wash'},
    'anoint': {'anointed', 'anoint'},
    'swallow': {'swallowed', 'swallow'},
    'plague': {'plagued', 'plague', 'strike', 'struck'},

    # Nouns
    'god(s)': {'god', 'gods', 'God'},
    'YHWH': {'lord', 'LORD', 'yhwh', 'YHWH', 'Yahweh'},
    'son': {'son', 'sons', 'child', 'children', 'ben'},
    'daughter': {'daughter', 'daughters'},
    'human, mankind': {'man', 'Adam', 'the\u00B7man'},
    'woman': {'woman', 'wife'},
    'earth': {'earth', 'land', 'ground', 'the\u00B7earth', 'the\u00B7land'},
    'heavens': {'heaven', 'heavens', 'sky', 'the\u00B7heavens'},
    'water': {'water', 'waters', 'the\u00B7waters'},
    'light': {'light', 'the\u00B7light'},
    'darkness': {'darkness', 'dark', 'the\u00B7darkness'},
    'day': {'day', 'days'},
    'night': {'night', 'nights'},
    'name': {'name', 'named'},
    'soul': {'soul', 'life', 'person', 'being', 'creature', 'a\u00B7living'},
    'face': {'face', 'faces', 'surface', 'presence', 'the\u00B7face\u00B7of'},
    'seed': {'seed', 'offspring', 'descendants'},
    'serpent': {'serpent', 'snake', 'the\u00B7serpent'},
    'shrewd': {'cunning', 'crafty', 'subtle', 'more\u00B7cunning'},
    'whole': {'all', 'every', 'each', 'any', 'whole'},
    'wild animal': {'beast', 'creature', 'living\u00B7creature', 'beast\u00B7of'},
    'open field': {'field', 'the\u00B7field'},
    'firmament': {'firmament', 'expanse', 'the\u00B7expanse'},
    'wind': {'spirit', 'wind', 'breath', 'the\u00B7spirit\u00B7of'},
    'male': {'male'},
    'female': {'female'},
    'image': {'image', 'his\u00B7image'},
    'interval': {'between', 'among'},
    'mother': {'mother', 'mothers'},
    'father': {'father', 'fathers'},
    'brother': {'brother', 'brothers'},
    'silver': {'silver', 'money'},
    'cattle': {'cattle', 'livestock', 'herd', 'herds'},
    'soil': {'ground', 'the\u00B7ground'},
    'tree': {'tree', 'trees', 'wood'},
    'garden': {'garden', 'the\u00B7garden'},
    'not': {'not', 'no'},
    'alive': {'living', 'alive', 'life'},
    '<object marker>': {'[identifies object]', '[object]', 'object', 'identifies', '(object marker)'},
    'saying': {'saying', 'to\u00B7say'},
    'herb': {'plant', 'plants', 'herb'},
    'fruit': {'fruit', 'fruits'},
    'fish': {'fish'},
    'bird': {'bird', 'birds', 'fowl'},
    'sea': {'sea', 'seas'},
    'creep': {'creeps', 'creeping', 'crawling', 'moves'},
    'kind': {'kind', 'its\u00B7kind', 'after\u00B7its\u00B7kind', 'their\u00B7kind'},
    'morning': {'morning'},
    'evening': {'evening'},
    'dust': {'dust'},
    'rib': {'rib', 'ribs'},
    'side': {'rib', 'side', 'his\u00B7ribs'},
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
    # Exodus/Torah-wide additions
    'Moses': {'Moses'},
    'Aaron': {'Aaron'},
    'Pharaoh': {'Pharaoh'},
    'Egypt': {'Egypt', 'Egyptian'},
    'Israel': {'Israel', 'Israelite', 'Israelites'},
    'priest': {'priest', 'priests'},
    'offering': {'offering', 'offerings', 'sacrifice'},
    'tabernacle': {'tabernacle', 'dwelling', 'mishkan'},
    'ark': {'ark'},
    'statute': {'statute', 'statutes', 'law', 'decree'},
    'judgment': {'judgment', 'judgments', 'ordinance', 'justice'},
    'testimony': {'testimony', 'testimonies', 'witness'},
    'congregation': {'congregation', 'assembly'},
    'wilderness': {'wilderness', 'desert'},
    'mountain': {'mountain', 'mount', 'hill'},
    'river': {'river', 'rivers', 'Nile'},
    'plague': {'plague', 'plagues', 'blow', 'strike'},
    'sign': {'sign', 'signs'},
    'wonder': {'wonder', 'wonders', 'miracle', 'miracles'},
    'cloud': {'cloud', 'clouds'},
    'fire': {'fire'},
    'glory': {'glory', 'honor', 'honour'},
    'holiness': {'holy', 'holiness', 'sacred'},
    'sin': {'sin', 'sins', 'transgression'},
    'iniquity': {'iniquity', 'guilt', 'punishment'},
    'atonement': {'atonement', 'covering'},
    'tribe': {'tribe', 'tribes', 'staff', 'rod'},
    'firstborn': {'firstborn', 'first-born'},
    'passover': {'passover', 'Passover'},
    'unleavened bread': {'unleavened', 'matzah', 'matzot'},
    'lamp': {'lamp', 'lamps', 'lampstand', 'menorah'},
    'gold': {'gold', 'golden'},
    'copper': {'copper', 'bronze', 'brass'},
    'linen': {'linen', 'fine linen'},
}

REV = defaultdict(set)
for eg, forms in EQUIV.items():
    for f in forms:
        REV[f.lower()].add(eg)
    REV[eg.lower()].add(eg)


def translation_matches_gloss(our_eng, etcbc_glosses):
    """Check if our translation is correct based on ETCBC glosses."""
    if not etcbc_glosses or not our_eng:
        return False

    our_parts = set(our_eng.lower().replace('\u00B7', ' ').split())
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
            if content & {f.lower().replace('\u00B7', ' ') for f in EQUIV[g]}:
                return True
            for p in content:
                for f in EQUIV[g]:
                    if p in f.lower() or f.lower() in p:
                        return True

        # Reverse lookup
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

def rebuild_book(book_key, strongs):
    """Run the rebuild pipeline for one book."""
    cfg = BOOK_CONFIG[book_key]
    display = cfg['display']

    print(f"\n{'=' * 60}")
    print(f"  {display} Rebuild — Per-Verse Aligned, Sefaria-First")
    print(f"{'=' * 60}")

    # Load ETCBC
    print(f"Loading ETCBC for {display}...")
    with open(cfg['etcbc'], 'r', encoding='utf-8') as f:
        etcbc_by_verse = json.load(f)
    print(f"  {len(etcbc_by_verse)} verses")

    # Load book data
    with open(cfg['json'], 'r', encoding='utf-8') as f:
        book_data = json.load(f)

    total = 0
    kept = 0
    fixed_sef = 0
    fixed_str = 0
    fixed_etc = 0
    no_etcbc = 0
    log_lines = []

    for ch in book_data['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            ref = f"{ch_num}:{v_num}"
            our_words = v.get('words', [])
            etcbc_verse = etcbc_by_verse.get(ref)

            if not etcbc_verse:
                for w in our_words:
                    total += 1
                    no_etcbc += 1
                    _, meanings = sefaria_lookup(w['heb'])
                    w['meanings'] = meanings[:6]
                continue

            alignment = align_words_in_verse(our_words, etcbc_verse)

            for i, w in enumerate(our_words):
                total += 1
                old_eng = w['eng']
                hebrew = w['heb']
                etcbc_glosses = alignment[i] if i < len(alignment) else []

                if translation_matches_gloss(old_eng, etcbc_glosses):
                    kept += 1
                    new_eng = old_eng
                else:
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
                            new_eng = '\u00B7'.join(etcbc_glosses)
                            fixed_etc += 1
                        elif etcbc_glosses:
                            new_eng = '\u00B7'.join(etcbc_glosses)
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

                primary_lower = new_eng.lower().replace('\u00B7', ' ') if new_eng else ''
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
    with open(cfg['output'], 'w', encoding='utf-8') as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)

    pct = 100 * kept / total if total else 0
    print(f"\n{'=' * 60}")
    print(f"  {display} DONE!")
    print(f"  Total words:      {total}")
    print(f"  Kept (correct):   {kept} ({pct:.1f}%)")
    print(f"  Fixed (Sefaria):  {fixed_sef}")
    print(f"  Fixed (Strong's): {fixed_str}")
    print(f"  Fixed (ETCBC):    {fixed_etc}")
    print(f"  No ETCBC data:    {no_etcbc}")
    print(f"  Changes:          {len(log_lines)}")
    print(f"  Output: {cfg['output'].name}")
    print(f"{'=' * 60}")

    # Show sample fixes
    if log_lines:
        print(f"\nSample fixes (first 20):")
        for line in log_lines[:20]:
            print(line)

    return {
        'book': display,
        'total': total,
        'kept': kept,
        'fixed_sef': fixed_sef,
        'fixed_str': fixed_str,
        'fixed_etc': fixed_etc,
        'no_etcbc': no_etcbc,
        'changes': len(log_lines),
    }


def main():
    args = [a.lower() for a in sys.argv[1:]]

    if not args or 'all' in args:
        books = ['exodus', 'leviticus', 'numbers', 'deuteronomy']
    else:
        books = [a for a in args if a in BOOK_CONFIG]
        if not books:
            print(f"Usage: python rebuild_book.py [exodus|leviticus|numbers|deuteronomy|all]")
            sys.exit(1)

    # Load Strong's once
    strongs = load_strongs()

    results = []
    for book_key in books:
        cfg = BOOK_CONFIG[book_key]
        if not cfg['etcbc'].exists():
            print(f"ERROR: ETCBC data not found: {cfg['etcbc']}")
            print(f"  Run: python build_etcbc_by_verse.py {book_key.title()}")
            continue
        if not cfg['json'].exists():
            print(f"ERROR: Book data not found: {cfg['json']}")
            continue
        results.append(rebuild_book(book_key, strongs))

    if len(results) > 1:
        print(f"\n{'=' * 60}")
        print(f"  SUMMARY")
        print(f"{'=' * 60}")
        for r in results:
            pct = 100 * r['kept'] / r['total'] if r['total'] else 0
            print(f"  {r['book']:15s}  {r['total']:6d} words  {pct:5.1f}% correct  {r['changes']:5d} fixed")


if __name__ == '__main__':
    main()
