#!/usr/bin/env python3
"""
Cross-check our word-level glosses (genesis_v3.json) against ETCBC morpheme data
(references/etcbc_genesis_by_verse.json) to find discrepancies.

Aligns Hebrew text from both sources, builds expected glosses from ETCBC morphemes,
and flags meaningful differences.
"""

import json
import sys
import re
import unicodedata
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Paths ──────────────────────────────────────────────────────────────────────
OUR_DATA   = "K:/TorahByWord/genesis_v3.json"
ETCBC_DATA = "K:/TorahByWord/references/etcbc_genesis_by_verse.json"
OUTPUT     = "K:/TorahByWord/gloss_discrepancies.json"

# ── Synonym sets: pairs that should NOT be flagged ─────────────────────────────
# Each set contains words considered equivalent for comparison purposes.
SYNONYM_SETS = [
    # ── Object marker ──
    {"d.o.", "object marker", "<object marker>", "[d.o.]", "dom"},

    # ── Verbs: ETCBC gives lexical form, we use inflected forms ──
    {"said", "say", "says", "saying"},
    {"called", "call", "calls", "calling"},
    {"made", "make", "makes", "making", "did", "do", "does", "done", "doing"},
    {"saw", "see", "sees", "seen", "seeing"},
    {"gave", "give", "gives", "given", "giving"},
    {"went", "go", "goes", "gone", "going", "walk", "walked", "walking", "walks"},
    {"came", "come", "comes", "coming"},
    {"took", "take", "takes", "taken", "taking"},
    {"knew", "know", "knows", "known", "knowing"},
    {"bore", "bear", "bears", "born", "borne", "bearing", "bring forth", "brought forth"},
    {"set", "put", "place", "placed", "placing", "putting", "setting"},
    {"created", "create", "creates", "creating"},
    {"was", "be", "is", "were", "been", "being", "became", "become", "becomes"},
    {"lived", "live", "lives", "living"},
    {"died", "die", "dies", "dying"},
    {"begot", "beget", "begets", "begetting", "fathered", "fathering"},
    {"blessed", "bless", "blesses", "blessing"},
    {"sent", "send", "sends", "sending"},
    {"returned", "return", "returns", "returning", "turn back", "turned back"},
    {"stood", "stand", "stands", "standing"},
    {"sat", "sit", "sits", "sitting", "dwell", "dwelt", "dwelling", "dwells", "settled", "settle"},
    {"ate", "eat", "eats", "eaten", "eating"},
    {"drank", "drink", "drinks", "drinking"},
    {"slept", "sleep", "sleeps", "sleeping"},
    {"heard", "hear", "hears", "hearing"},
    {"loved", "love", "loves", "loving"},
    {"hated", "hate", "hates", "hating"},
    {"feared", "fear", "fears", "fearing"},
    {"lifted", "lift", "lifts", "lifting", "raise", "raised", "raising"},
    {"opened", "open", "opens", "opening"},
    {"closed", "close", "closes", "closing", "shut", "shutting"},
    {"built", "build", "builds", "building"},
    {"brought", "bring", "brings", "bringing"},
    {"kept", "keep", "keeps", "keeping", "guard", "guarded", "guarding"},
    {"fell", "fall", "falls", "falling"},
    {"rose", "rise", "rises", "rising"},
    {"filled", "fill", "fills", "filling", "full"},
    {"turned", "turn", "turns", "turning"},
    {"spoken", "speak", "speaks", "speaking", "spoke"},
    {"written", "write", "writes", "writing", "wrote"},
    {"gathered", "gather", "gathers", "gathering", "collect", "collected"},
    {"swore", "swear", "swears", "sworn", "swearing"},
    {"ceased", "cease", "ceases", "ceasing", "rested", "rest", "rests", "resting"},
    {"commanded", "command", "commands", "commanding"},
    {"touched", "touch", "touches", "touching"},
    {"formed", "form", "forms", "forming", "shape", "shaped", "shaping"},
    {"sprouted", "sprout", "sprouts", "sprouting"},
    {"desired", "desire", "desires", "desiring", "desirable"},
    {"cursed", "curse", "curses", "cursing"},
    {"added", "add", "adds", "adding", "again"},
    {"pastured", "pasture", "pastures", "pasturing"},
    {"worked", "work", "works", "working", "serve", "served", "serving", "work, serve"},
    {"sowed", "sow", "sows", "sowing", "bearing"},
    {"separated", "separate", "separates", "separating"},
    {"teemed", "teem", "teems", "teeming", "swarm", "swarmed", "swarming"},
    {"fertile", "be fertile", "fruitful", "be fruitful"},
    {"rained", "rain", "rains", "raining", "had rained"},
    {"cried", "cry", "cries", "crying"},
    {"struck", "strike", "strikes", "striking", "struck down", "hit"},
    {"found", "find", "finds", "finding"},
    {"left", "leave", "leaves", "leaving"},
    {"clung", "cling", "clings", "clinging", "cling, cleave to", "cleave", "cleaved"},
    {"let bring forth", "go out", "bring forth", "brought forth"},
    {"many", "be many", "became great", "multiplied", "multiply", "increase", "increased"},
    {"crept", "creep", "creeps", "creeping"},
    {"planted", "plant", "plants", "planting"},
    {"completed", "complete", "completes", "finish", "finished", "finishing"},
    {"divided", "divide", "divides", "dividing"},
    {"named", "name", "names", "naming"},
    {"answered", "answer", "answers", "answering"},
    {"asked", "ask", "asks", "asking"},
    {"bought", "buy", "buys", "buying"},
    {"sold", "sell", "sells", "selling"},
    {"counted", "count", "counts", "counting"},
    {"covered", "cover", "covers", "covering"},
    {"crossed", "cross", "crosses", "crossing"},
    {"cried out", "cry out", "crying out"},
    {"deceived", "deceive", "deceives", "deceiving"},
    {"destroyed", "destroy", "destroys", "destroying"},
    {"killed", "kill", "kills", "killing", "slay", "slew", "slaying"},
    {"moved", "move", "moves", "moving"},
    {"passed", "pass", "passes", "passing"},
    {"remembered", "remember", "remembers", "remembering"},
    {"ruled", "rule", "rules", "ruling"},
    {"saved", "save", "saves", "saving"},
    {"served", "serve", "serves", "serving"},
    {"stretched", "stretch", "stretches", "stretching"},
    {"tested", "test", "tests", "testing", "tried", "try"},
    {"wept", "weep", "weeps", "weeping"},
    {"bowed", "bow", "bows", "bowing"},
    {"burned", "burn", "burns", "burning"},
    {"changed", "change", "changes", "changing"},
    {"circumcised", "circumcise", "circumcises", "circumcising"},
    {"conceived", "conceive", "conceives", "conceiving"},
    {"established", "establish", "establishes", "establishing"},
    {"fed", "feed", "feeds", "feeding"},
    {"forgot", "forget", "forgets", "forgetting", "forgotten"},
    {"grieved", "grieve", "grieves", "grieving"},
    {"hid", "hide", "hides", "hiding", "hidden"},
    {"inherited", "inherit", "inherits", "inheriting"},
    {"journeyed", "journey", "journeys", "journeying", "pulled up", "travel", "traveled"},
    {"judged", "judge", "judges", "judging"},
    {"kissed", "kiss", "kisses", "kissing"},
    {"laughed", "laugh", "laughs", "laughing"},
    {"looked", "look", "looks", "looking"},
    {"mourned", "mourn", "mourns", "mourning"},
    {"pitched", "pitch", "pitches", "pitching"},
    {"prayed", "pray", "prays", "praying"},
    {"pursued", "pursue", "pursues", "pursuing"},
    {"reached", "reach", "reaches", "reaching"},
    {"reigned", "reign", "reigns", "reigning"},
    {"remained", "remain", "remains", "remaining"},
    {"seized", "seize", "seizes", "seizing"},
    {"waited", "wait", "waits", "waiting"},
    {"washed", "wash", "washes", "washing"},
    {"ran", "run", "runs", "running"},
    {"fought", "fight", "fights", "fighting"},
    {"grew", "grow", "grows", "growing"},
    {"hung", "hang", "hangs", "hanging"},
    {"dreamed", "dream", "dreams", "dreaming"},
    {"interpreted", "interpret", "interprets", "interpreting"},
    {"stole", "steal", "steals", "stealing", "stolen"},
    {"swallowed", "swallow", "swallows", "swallowing"},
    {"overthrew", "overthrow", "overthrows", "overthrowing"},
    {"possessed", "possess", "possesses", "possessing"},
    {"prospered", "prosper", "prospers", "prospering"},
    {"refused", "refuse", "refuses", "refusing"},
    {"assembled", "assemble", "assembles", "assembling"},
    {"buried", "bury", "buries", "burying"},
    {"dwelt", "dwell", "dwells", "dwelling"},
    {"embalmed", "embalm", "embalms", "embalming"},
    {"fasted", "fast", "fasts", "fasting"},
    {"hastened", "hasten", "hastens", "hastening", "hurry", "hurried"},
    {"healed", "heal", "heals", "healing"},
    {"instructed", "instruct", "instructs", "instructing"},
    {"obeyed", "obey", "obeys", "obeying"},
    {"offered", "offer", "offers", "offering"},
    {"prevailed", "prevail", "prevails", "prevailing"},
    {"redeemed", "redeem", "redeems", "redeeming"},
    {"rejected", "reject", "rejects", "rejecting"},
    {"rescued", "rescue", "rescues", "rescuing"},
    {"rested", "rest", "rests", "resting"},
    {"scattered", "scatter", "scatters", "scattering"},
    {"swam", "swim", "swims", "swimming"},
    {"taught", "teach", "teaches", "teaching"},
    {"wandered", "wander", "wanders", "wandering"},
    {"worshipped", "worship", "worships", "worshipping"},
    {"arose", "arise", "arises", "arising"},
    {"fled", "flee", "flees", "fleeing"},
    {"dug", "dig", "digs", "digging"},
    {"tore", "tear", "tears", "tearing", "torn"},
    {"threw", "throw", "throws", "throwing", "thrown", "cast"},
    {"awoke", "awake", "awaken", "awakened", "awakening"},
    {"reigned", "reign", "reigns", "reigning", "be king", "king"},
    {"entered", "enter", "enters", "entering", "come", "came", "come in"},
    {"settled", "settle", "settles", "settling", "sit", "sat", "sitting"},
    {"advanced", "advance", "advances", "advancing"},
    {"met", "meet", "meets", "meeting", "encounter", "encountered"},
    {"angry", "be hot", "be angry", "burn with anger"},
    {"repent", "repented", "repenting", "console", "consoled", "repent, console"},
    {"strove", "strive", "striving", "contend", "contended"},
    {"prevail", "prevailed", "prevailing", "be able", "able"},
    {"appear", "appeared", "appearing", "see", "show", "showed", "shown", "provide", "provided"},
    {"report", "reported", "reporting", "tell", "told", "telling", "declare", "declared"},
    {"gather", "gathered", "add", "added", "again", "continue", "continued"},
    {"buy", "bought", "buyer", "buying"},
    {"do well", "be good", "do good"},
    {"bring forth", "go out", "went out", "brought forth", "come out", "came out"},
    {"fertile", "be fertile", "fruitful", "be fruitful", "bear fruit"},
    {"destroy", "destroyed", "destroying", "destruction", "destructive"},
    {"catch", "caught", "catching", "seize", "seized", "seizing"},
    {"distance", "far", "be far", "distant"},
    {"bound", "bind", "binds", "binding"},
    {"willing", "be willing", "want", "wanted", "wanting"},
    {"separated", "separate", "divide", "divided", "dividing", "division"},
    {"runner", "run", "ran", "running"},
    {"saw", "see", "sees", "seen", "seeing", "i saw", "you saw", "they saw", "we saw", "he saw", "were seen", "will be seen", "be seen", "when seeing"},
    {"dwelt", "dwell", "sit", "sat", "sitting", "dwelling", "to dwell", "to sit"},

    # ── Nouns and other parts of speech ──
    {"earth", "land", "ground"},
    {"god", "god(s)", "gods"},
    {"man", "human", "adam", "mankind", "humankind"},
    {"woman", "wife"},
    {"upon", "on", "over", "above"},
    {"to", "for", "toward", "towards"},
    {"in", "at", "within"},
    {"from", "out of", "away from"},
    {"with", "together with"},
    {"good", "be good"},
    {"great", "be great", "big"},
    {"small", "be small", "little"},
    {"much", "many", "abundant", "be much"},
    {"son", "sons", "children", "child"},
    {"daughter", "daughters"},
    {"brother", "brothers"},
    {"father", "fathers"},
    {"water", "waters"},
    {"day", "days"},
    {"year", "years"},
    {"night", "nights"},
    {"morning", "mornings"},
    {"evening", "evenings"},
    {"hand", "hands"},
    {"eye", "eyes"},
    {"face", "faces", "before", "presence"},
    {"heavens", "heaven", "sky"},
    {"sea", "seas"},
    {"name", "names"},
    {"word", "words", "thing", "things", "matter"},
    {"king", "kings"},
    {"servant", "servants", "slave", "slaves"},
    {"people", "nation", "nations"},
    {"seed", "offspring", "descendant", "descendants"},
    {"soul", "life", "self", "being", "person", "living"},
    {"spirit", "wind", "breath"},
    {"tree", "trees", "wood"},
    {"field", "fields"},
    {"city", "cities"},
    {"house", "houses"},
    {"midst", "middle", "among"},
    {"that", "which", "who", "whom", "because"},
    {"not", "no"},
    {"all", "every", "each", "whole"},
    {"also", "even", "moreover"},
    {"very", "exceedingly", "greatly"},
    {"plants", "herb", "herbage", "vegetation"},
    {"livestock", "cattle", "beast", "animal"},
    {"expanse", "firmament"},
    {"between", "interval"},
    {"sign", "signs"},
    {"appointment", "appointed place", "appointed time", "season"},
    {"light", "lamp", "luminary"},
    {"soil", "ground", "earth", "land", "dust"},
    {"empty place", "emptiness", "formless", "void", "chaos"},
    {"darkness", "darken", "dark"},
    {"beast", "wild animal", "living creature"},
    {"birds", "bird", "fowl"},
    {"green", "greens", "vegetation", "herb"},
    {"creeping thing", "creeper", "crawling thing"},
    {"likeness", "image", "resemblance"},
    {"kind", "type", "species"},
    {"fruit", "fruits"},
    {"freely", "surely"},
    {"surely", "certainly", "indeed"},
]

# Build a lookup: word -> canonical representative
def build_synonym_map():
    smap = {}
    for group in SYNONYM_SETS:
        canonical = sorted(group)[0]  # pick alphabetically first as canonical
        for w in group:
            smap[w.lower()] = canonical
    return smap

SYNONYM_MAP = build_synonym_map()

# ── Hebrew text utilities ──────────────────────────────────────────────────────

MAQEF = '\u05BE'  # ־

def strip_niqqud(text):
    """Remove vowel points, cantillation marks, and other diacritics from Hebrew."""
    result = []
    for ch in text:
        cat = unicodedata.category(ch)
        # Keep letters and the maqef; drop marks (Mn = nonspacing mark, etc.)
        if cat.startswith('M'):
            continue
        result.append(ch)
    return ''.join(result)

def normalize_hebrew(text):
    """Strip niqqud + remove maqef + strip whitespace."""
    t = strip_niqqud(text)
    t = t.replace(MAQEF, '')
    t = t.replace('\u200d', '')  # zero-width joiner
    t = t.replace('\u200c', '')  # zero-width non-joiner
    t = t.strip()
    return t

# ── Gloss normalization ───────────────────────────────────────────────────────

def normalize_gloss(g):
    """Normalize a gloss for comparison: lowercase, strip separators, sort parts."""
    g = g.lower().strip()
    # Remove bracketed markers like [d.o.]
    g = re.sub(r'\[.*?\]', 'dom', g)
    # Replace separators with space
    g = g.replace('·', ' ').replace('‧', ' ').replace('-', ' ').replace('_', ' ')
    # Remove angle brackets
    g = re.sub(r'[<>]', '', g)
    # Collapse whitespace
    g = re.sub(r'\s+', ' ', g).strip()
    return g

def gloss_parts(g):
    """Split a normalized gloss into individual meaning-bearing parts."""
    g = normalize_gloss(g)
    parts = g.split()
    # Map through synonyms
    mapped = []
    for p in parts:
        mapped.append(SYNONYM_MAP.get(p, p))
    return mapped

def crude_stem(word):
    """Very crude English stemming: strip common suffixes."""
    w = word.lower()
    for suffix in ['ing', 'tion', 'ed', 'es', 'er', 'ly', 'ness', 'ment', 's']:
        if len(w) > len(suffix) + 2 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w

def words_similar(a, b):
    """Check if two English words are similar (same stem or synonym)."""
    a, b = a.lower(), b.lower()
    if a == b:
        return True
    # Check synonym map
    if SYNONYM_MAP.get(a) == SYNONYM_MAP.get(b) and SYNONYM_MAP.get(a) is not None:
        return True
    # Crude stem comparison
    sa, sb = crude_stem(a), crude_stem(b)
    if sa == sb and len(sa) >= 3:
        return True
    # Check if one contains the other (for compound ETCBC glosses like "work, serve")
    if a in b or b in a:
        return True
    return False

def glosses_match(our, etcbc):
    """Check if two glosses are semantically equivalent."""
    our_parts = gloss_parts(our)
    etc_parts = gloss_parts(etcbc)

    # Remove trivially functional words for comparison
    skip = {'the', 'a', 'an', 'of', 'to'}
    our_content = [p for p in our_parts if p not in skip]
    etc_content = [p for p in etc_parts if p not in skip]

    if not our_content and not etc_content:
        return True
    if not our_content or not etc_content:
        return set(our_parts) == set(etc_parts)

    # Check if any content word from ours matches any from ETCBC
    for ow in our_content:
        for ew in etc_content:
            if words_similar(ow, ew):
                return True

    return False

def compute_severity(our_gloss, etcbc_gloss, pos):
    """Determine severity of a gloss discrepancy."""
    our_n = normalize_gloss(our_gloss)
    etc_n = normalize_gloss(etcbc_gloss)

    # If after normalization they're the same string, no issue
    if our_n == etc_n:
        return None

    # Use the full glosses_match check (includes synonyms + stemming)
    if glosses_match(our_gloss, etcbc_gloss):
        return None

    our_p = [p for p in gloss_parts(our_gloss) if p not in {'the', 'a', 'an', 'of', 'to'}]
    etc_p = [p for p in gloss_parts(etcbc_gloss) if p not in {'the', 'a', 'an', 'of', 'to'}]

    # Both empty after filtering
    if not our_p and not etc_p:
        return None

    # Check pairwise word similarity (catches stem matches)
    for ow in our_p:
        for ew in etc_p:
            if words_similar(ow, ew):
                return None

    # Check if one set is subset of other (partial match)
    if set(our_p) and set(etc_p):
        if set(our_p) <= set(etc_p) or set(etc_p) <= set(our_p):
            return "low"

    # Verbs are most important to get right
    if pos == "verb":
        return "high"

    # Nouns/substantives with different meaning
    if pos in ("subs", "nmpr"):
        if pos == "nmpr":
            return "low"
        return "medium"

    # Other POS
    return "low"


# ── Core alignment logic ──────────────────────────────────────────────────────

PREFIX_CONSONANTS = {'ב', 'ה', 'ו', 'כ', 'ל', 'מ', 'ש'}
PREFIX_POS = {'prep', 'art', 'conj'}

def align_and_compare(our_words, etcbc_morphemes, ref):
    """
    Align our words to ETCBC morphemes and compare glosses.
    Returns list of discrepancy dicts.
    """
    discrepancies = []

    # Strategy: walk through ETCBC morphemes, grouping them to match our words.
    # Our words may include maqef-joined pairs (e.g., "עַל־פְּנֵי") which span
    # multiple ETCBC words.

    # First, split our maqef words into sub-words for alignment
    our_expanded = []
    for idx, w in enumerate(our_words):
        heb = w['heb']
        eng = w['eng']
        sub_hebs = heb.split(MAQEF)
        sub_engs = eng.split('·') if '·' in eng else [eng]

        # Handle case where eng parts don't match sub_hebs count
        # Just keep them together in that case
        if len(sub_hebs) > 1 and len(sub_engs) >= len(sub_hebs):
            # Distribute eng parts across sub hebs
            # Prefixes in first sub-word get allocated from eng parts
            parts_per_sub = []
            eng_idx = 0
            for sh in sub_hebs:
                # Count how many prefix morphemes this sub-word has
                stripped = normalize_hebrew(sh)
                # Estimate: each sub-word gets at least 1 eng part
                parts_per_sub.append([])

            # Simple: distribute evenly, first sub gets more if uneven
            per = len(sub_engs) // len(sub_hebs)
            extra = len(sub_engs) % len(sub_hebs)
            ei = 0
            for si in range(len(sub_hebs)):
                n = per + (1 if si < extra else 0)
                parts_per_sub[si] = sub_engs[ei:ei+n]
                ei += n

            for si, sh in enumerate(sub_hebs):
                our_expanded.append({
                    'heb': sh,
                    'eng': '·'.join(parts_per_sub[si]) if parts_per_sub[si] else '',
                    'orig_idx': idx,
                    'orig_heb': heb,
                    'orig_eng': eng
                })
        else:
            our_expanded.append({
                'heb': heb,
                'eng': eng,
                'orig_idx': idx,
                'orig_heb': heb,
                'orig_eng': eng
            })

    # Now align our_expanded words with ETCBC morphemes
    # ETCBC splits prefixes, so multiple morphemes -> one of our words

    # Build ETCBC "words" by grouping: a word starts with a non-prefix morpheme
    # or after a prefix sequence followed by a non-prefix.
    # Actually, let's group by concatenating Hebrew until we match our word.

    etcbc_idx = 0

    for ow in our_expanded:
        our_heb_norm = normalize_hebrew(ow['heb'])
        if not our_heb_norm:
            continue

        # Try to consume ETCBC morphemes until their concatenated consonants match
        best_group = []
        concat = ''
        search_idx = etcbc_idx
        found = False

        # Try up to 8 morphemes (generous for prefix + word combos)
        while search_idx < len(etcbc_morphemes) and len(best_group) < 8:
            m = etcbc_morphemes[search_idx]
            m_cons = m.get('cons', '')
            m_heb_norm = normalize_hebrew(m.get('heb', ''))

            # Use consonantal form if available, else normalized heb
            addition = m_cons if m_cons else m_heb_norm
            # Normalize consonantal: remove shin/sin dots if present
            addition = strip_niqqud(addition)

            best_group.append(m)
            concat += addition
            search_idx += 1

            # Compare
            # Need to also strip shin/sin dots from our word
            our_compare = our_heb_norm.replace('שׁ', 'ש').replace('שׂ', 'ש')
            concat_compare = concat.replace('שׁ', 'ש').replace('שׂ', 'ש')

            if our_compare == concat_compare:
                found = True
                break

        if not found:
            # Try skipping ahead - maybe alignment is off
            # Don't advance etcbc_idx, just skip this word
            continue

        # We matched! Build ETCBC gloss from the group
        etcbc_idx = search_idx  # advance past consumed morphemes

        etcbc_gloss_parts = []
        primary_pos = None
        for m in best_group:
            g = m.get('gloss', '')
            p = m.get('pos', '')
            if g and g not in ('<object marker>',):
                etcbc_gloss_parts.append(g)
            elif g == '<object marker>':
                etcbc_gloss_parts.append('[d.o.]')
            if p in ('verb', 'subs', 'nmpr', 'adjv', 'advb') and not primary_pos:
                primary_pos = p

        etcbc_combined = '·'.join(etcbc_gloss_parts)

        if not etcbc_combined or not ow['eng']:
            continue

        # Compare
        severity = compute_severity(ow['eng'], etcbc_combined, primary_pos or '')

        if severity:
            discrepancies.append({
                'ref': ref,
                'word_idx': ow['orig_idx'],
                'heb': ow['orig_heb'],
                'our_gloss': ow['orig_eng'],
                'etcbc_gloss': etcbc_combined,
                'etcbc_pos': primary_pos or '',
                'severity': severity,
            })

    return discrepancies


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    with open(OUR_DATA, 'r', encoding='utf-8') as f:
        our = json.load(f)
    with open(ETCBC_DATA, 'r', encoding='utf-8') as f:
        etcbc = json.load(f)

    all_discrepancies = []
    verses_checked = 0
    verses_skipped = 0
    words_checked = 0

    for ch in our['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            ref = f"{ch_num}:{v_num}"

            if ref not in etcbc:
                verses_skipped += 1
                continue

            our_words = v['words']
            etcbc_morphemes = etcbc[ref]

            words_checked += len(our_words)
            verses_checked += 1

            discs = align_and_compare(our_words, etcbc_morphemes, ref)
            all_discrepancies.extend(discs)

    # Deduplicate: same orig word can appear multiple times if maqef-split
    seen = set()
    unique_discrepancies = []
    for d in all_discrepancies:
        key = (d['ref'], d['word_idx'], d['our_gloss'])
        if key not in seen:
            seen.add(key)
            unique_discrepancies.append(d)

    # Sort by severity (high first), then by reference
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    unique_discrepancies.sort(key=lambda d: (severity_order[d['severity']],
                                              d['ref'].split(':')[0].zfill(3),
                                              d['ref']))

    # Save report
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(unique_discrepancies, f, ensure_ascii=False, indent=2)

    # Print summary
    sev_counts = Counter(d['severity'] for d in unique_discrepancies)
    pos_counts = Counter(d['etcbc_pos'] for d in unique_discrepancies if d['severity'] == 'high')

    print(f"\n{'='*70}")
    print(f"GLOSS CROSS-CHECK REPORT")
    print(f"{'='*70}")
    print(f"Verses checked:  {verses_checked}")
    print(f"Verses skipped:  {verses_skipped} (not in ETCBC)")
    print(f"Words checked:   {words_checked}")
    print(f"Total discrepancies: {len(unique_discrepancies)}")
    print(f"  HIGH:   {sev_counts.get('high', 0)}")
    print(f"  MEDIUM: {sev_counts.get('medium', 0)}")
    print(f"  LOW:    {sev_counts.get('low', 0)}")
    print()

    if pos_counts:
        print("HIGH severity by POS:")
        for pos, cnt in pos_counts.most_common():
            print(f"  {pos:8s}: {cnt}")
        print()

    # Show top HIGH severity examples
    highs = [d for d in unique_discrepancies if d['severity'] == 'high']
    print(f"── Top HIGH-severity discrepancies (showing up to 50) ──")
    for d in highs[:50]:
        print(f"  {d['ref']:>8s} [{d['word_idx']:2d}] {d['heb']}")
        print(f"           ours:  {d['our_gloss']}")
        print(f"           etcbc: {d['etcbc_gloss']}  ({d['etcbc_pos']})")
        print()

    # Show some MEDIUM examples
    meds = [d for d in unique_discrepancies if d['severity'] == 'medium']
    print(f"── Sample MEDIUM-severity discrepancies (showing up to 30) ──")
    for d in meds[:30]:
        print(f"  {d['ref']:>8s} [{d['word_idx']:2d}] {d['heb']}")
        print(f"           ours:  {d['our_gloss']}")
        print(f"           etcbc: {d['etcbc_gloss']}  ({d['etcbc_pos']})")
        print()

    print(f"Full report saved to: {OUTPUT}")

if __name__ == '__main__':
    main()
