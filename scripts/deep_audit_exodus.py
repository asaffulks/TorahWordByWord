#!/usr/bin/env python3
"""Deep audit of Exodus data vs Genesis v7 gold standard."""
import json, re, sys
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/books/torah/exodus_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open('K:/TorahByWord/books/torah/genesis_v3.json', 'r', encoding='utf-8') as f:
    gen = json.load(f)

print("=" * 70)
print("DEEP AUDIT: Exodus vs Genesis v7 Gold Standard")
print("=" * 70)

JARGON = {'adj','adv','subst','n m','n f','n m/f','vb','v','prep','conj','pron',
          'interj','nm','nf','n pr m','n pr','n pr f','n pr loc','pron 3p s'}

# 1. EMPTY/BAD GLOSSES
print("\n=== 1. EMPTY OR BAD GLOSSES ===")
empty = []
jargon = []
too_short = []
hebrew_in_eng = []
for ch in data['chapters']:
    for v in ch['verses']:
        for i, w in enumerate(v.get('words',[])):
            e = w.get('eng','')
            ref = f"{ch['chapter']}:{v['verse']}[{i}]"
            if not e.strip():
                empty.append(f"  {ref} {w['heb']}")
            elif e.lower() in JARGON:
                jargon.append(f"  {ref} {w['heb']} -> '{e}'")
            elif len(e) == 1 and e != 'I':
                too_short.append(f"  {ref} {w['heb']} -> '{e}'")
            if any('\u05D0' <= c <= '\u05EA' for c in e):
                hebrew_in_eng.append(f"  {ref} eng='{e[:60]}'")

print(f"Empty glosses: {len(empty)}")
for x in empty[:5]: print(x)
print(f"Jargon (POS labels): {len(jargon)}")
for x in jargon: print(x)
print(f"Single-char glosses: {len(too_short)}")
for x in too_short[:5]: print(x)
print(f"Hebrew chars in English: {len(hebrew_in_eng)}")
for x in hebrew_in_eng[:5]: print(x)

# 2. MISSING ROOTS
print("\n=== 2. MISSING ROOTS ===")
no_root = sum(1 for ch in data['chapters'] for v in ch['verses'] for w in v.get('words',[]) if not w.get('root',''))
total_w = sum(1 for ch in data['chapters'] for v in ch['verses'] for w in v.get('words',[]))
gen_no = sum(1 for ch in gen['chapters'] for v in ch['verses'] for w in v.get('words',[]) if not w.get('root',''))
gen_t = sum(1 for ch in gen['chapters'] for v in ch['verses'] for w in v.get('words',[]))
print(f"Exodus:  {no_root}/{total_w} missing ({100*no_root/total_w:.1f}%)")
print(f"Genesis: {gen_no}/{gen_t} missing ({100*gen_no/gen_t:.1f}%)")

# 3. SUSPICIOUS TRANSLATIONS
print("\n=== 3. SUSPICIOUS TRANSLATIONS ===")
suspicious = Counter()
sus_examples = {}
for ch in data['chapters']:
    for v in ch['verses']:
        for i, w in enumerate(v.get('words',[])):
            e = w.get('eng','')
            ref = f"{ch['chapter']}:{v['verse']}[{i}]"
            h = strip_n(w['heb']).replace('\u05BE','')

            if 'burning' in e.lower() and 'כי' in h:
                suspicious['burning_for_ki'] += 1
                sus_examples.setdefault('burning_for_ki', []).append(f"  {ref} {w['heb']} -> '{e}'")
            if e == 'ram' and 'אל' in h:
                suspicious['ram_for_el'] += 1
                sus_examples.setdefault('ram_for_el', []).append(f"  {ref} {w['heb']} -> 'ram'")
            if 'Commonly transcribed' in e:
                suspicious['commonly_yhwh'] += 1
                sus_examples.setdefault('commonly_yhwh', []).append(f"  {ref} -> '{e}'")
            if 'relative part' in e:
                suspicious['relative_part'] += 1
            if 'sign of the definite' in e:
                suspicious['sign_of_obj'] += 1
            if h.startswith('וי') and e.startswith('to ') and len(e) < 15 and 'to·' not in e:
                suspicious['vav_consec_unfixed'] += 1
                sus_examples.setdefault('vav_consec_unfixed', []).append(f"  {ref} {w['heb']} -> '{e}'")
            if '=' in e and '"' in e:
                suspicious['dict_def'] += 1
                sus_examples.setdefault('dict_def', []).append(f"  {ref} -> '{e[:60]}'")
            if '<' in e or 'href' in e:
                suspicious['html'] += 1
                sus_examples.setdefault('html', []).append(f"  {ref} -> '{e[:60]}'")
            if e.startswith('(') and 'object' not in e.lower() and len(e) > 20:
                suspicious['parens_junk'] += 1
                sus_examples.setdefault('parens_junk', []).append(f"  {ref} -> '{e[:60]}'")

for kind, count in suspicious.most_common():
    print(f"  {kind}: {count}")
    examples = sus_examples.get(kind, [])
    for ex in examples[:3]:
        print(f"    {ex}")

# 4. REMAINING FRAGMENTS
print("\n=== 4. SINGLE-CONSONANT FRAGMENTS ===")
single = []
for ch in data['chapters']:
    for v in ch['verses']:
        for i, w in enumerate(v.get('words',[])):
            cons = strip_n(w['heb']).replace('\u05BE','')
            if len(cons) <= 1:
                single.append(f"  {ch['chapter']}:{v['verse']}[{i}] '{w['heb']}' -> '{w['eng']}'")
print(f"Found: {len(single)}")
for x in single: print(x)

# 5. COMMENTARY FILL RATES
print("\n=== 5. COMMENTARY FILL RATES ===")
comm_fields = ['rashi','ramban','ibn_ezra','sforno','or_hachaim','chizkuni','rabbeinu_bahya','onkelos','kli_yakar']
total_v = sum(len(ch['verses']) for ch in data['chapters'])
for field in comm_fields:
    filled = sum(1 for ch in data['chapters'] for v in ch['verses'] if v.get(field,'').strip())
    print(f"  {field:20s}: {filled:4d}/{total_v} ({100*filled/total_v:5.1f}%)")

# 6. VERSE FIELD COMPARISON
print("\n=== 6. VERSE FIELD COMPARISON ===")
gen_v = gen['chapters'][0]['verses'][0]
exo_v = data['chapters'][0]['verses'][0]
print(f"Genesis keys: {sorted(gen_v.keys())}")
print(f"Exodus keys:  {sorted(exo_v.keys())}")
print(f"Missing from Exodus: {sorted(set(gen_v.keys()) - set(exo_v.keys()))}")

# 7. WORD FIELD COMPARISON
print("\n=== 7. WORD FIELD COMPARISON ===")
gen_w = gen['chapters'][0]['verses'][0]['words'][0]
exo_w = data['chapters'][0]['verses'][0]['words'][0]
print(f"Genesis: {sorted(gen_w.keys())}")
print(f"Exodus:  {sorted(exo_w.keys())}")

# 8. TOP 30 GLOSSES
print("\n=== 8. TOP 30 GLOSSES (sanity check) ===")
gloss_counts = Counter()
for ch in data['chapters']:
    for v in ch['verses']:
        for w in v.get('words',[]):
            gloss_counts[w.get('eng','')] += 1
for g, c in gloss_counts.most_common(30):
    print(f"  {c:4d}x  '{g}'")

# 9. SPOT CHECK KEY VERSES
print("\n=== 9. SPOT CHECK KEY VERSES ===")
checks = [
    (1, 1, "And these are the names of the sons of Israel"),
    (3, 14, "I Am That I Am"),
    (12, 2, "This month shall be the head of months"),
    (20, 2, "I am the LORD your God"),
    (20, 13, "You shall not murder"),
]
for ch_n, v_n, expected in checks:
    v = data['chapters'][ch_n-1]['verses'][v_n-1]
    words = ' '.join(w['eng'] for w in v['words'])
    print(f"  {ch_n}:{v_n} ({expected}):")
    print(f"    {words[:100]}")
