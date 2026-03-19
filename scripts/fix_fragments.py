#!/usr/bin/env python3
"""
Fix broken word fragments in genesis.json.
Fragments are pieces of words split by cantillation marks.
Merges them with the correct adjacent word.
"""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

def calc_gematria(word):
    GEMATRIA = {
        '\u05D0':1,'\u05D1':2,'\u05D2':3,'\u05D3':4,'\u05D4':5,
        '\u05D5':6,'\u05D6':7,'\u05D7':8,'\u05D8':9,'\u05D9':10,
        '\u05DB':20,'\u05DA':20,'\u05DC':30,'\u05DE':40,'\u05DD':40,
        '\u05E0':50,'\u05DF':50,'\u05E1':60,'\u05E2':70,'\u05E4':80,
        '\u05E3':80,'\u05E6':90,'\u05E5':90,'\u05E7':100,'\u05E8':200,
        '\u05E9':300,'\u05EA':400,
    }
    clean = strip_n(word)
    return sum(GEMATRIA.get(c, 0) for c in clean)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Words that are legitimate short Hebrew words — don't merge these
LEGIT = {
    'את','לא','כי','על','אל','עד','גם','אם','בן','אב','אח','אף',
    'עץ','לו','לי','לך','בו','בה','כל','שם','דם','חי','רע','יד','פה',
    'הם','הן','מי','מה','אי','נא','רק','אך','עם','בי','חם','דן','גד',
    'זה','אז','כן','לה','בא','אש','רב','טל','פר','אד','הו',
}

merged = 0
for c in d['chapters']:
    for v in c['verses']:
        words = v['words']
        new_words = []
        i = 0
        while i < len(words):
            w = words[i]
            cons = strip_n(w['heb']).replace('\u05BE', '')

            # Is this a fragment?
            is_frag = len(cons) <= 2 and cons not in LEGIT

            if is_frag:
                # Decide: merge with previous or next?
                prev_cons = strip_n(new_words[-1]['heb']).replace('\u05BE', '') if new_words else ''
                next_cons = strip_n(words[i+1]['heb']).replace('\u05BE', '') if i+1 < len(words) else ''

                # Check if previous word ends with the start of this fragment
                # e.g., prev=ל, frag=וט -> merge to form לוט (Lot)
                # Or prev=וַיְכֻלּ, frag=וּ -> merge to form ויכלו

                # Heuristic: if fragment starts with וֹ or וּ (vav with vowel),
                # it's likely a suffix that belongs to the PREVIOUS word
                first_char = w['heb'][0] if w['heb'] else ''
                has_vav_vowel = first_char == '\u05D5' or (len(w['heb']) > 1 and w['heb'][0] == '\u05D5')

                # If previous word looks incomplete (ends abruptly)
                # or fragment is a vav-suffix, merge with previous
                if new_words and (has_vav_vowel or len(prev_cons) >= 2):
                    prev = new_words[-1]
                    merged_heb = prev['heb'] + w['heb']
                    merged_cons = strip_n(merged_heb).replace('\u05BE', '')

                    # Verify the merged form is reasonable (3+ consonants)
                    if len(merged_cons) >= 3:
                        new_words[-1] = {
                            'heb': merged_heb,
                            'eng': prev['eng'],  # keep previous word's gloss
                            'root': prev['root'] or w['root'],
                            'tr': prev['tr'] + w['tr'],
                            'gem': calc_gematria(merged_heb.replace('\u05BE', '')),
                        }
                        merged += 1
                        i += 1
                        continue

                # Otherwise try merging with next word
                if i + 1 < len(words):
                    nxt = words[i + 1]
                    merged_heb = w['heb'] + nxt['heb']
                    merged_cons = strip_n(merged_heb).replace('\u05BE', '')

                    if len(merged_cons) >= 3:
                        new_words.append({
                            'heb': merged_heb,
                            'eng': nxt['eng'],
                            'root': nxt['root'] or w['root'],
                            'tr': w['tr'] + nxt['tr'],
                            'gem': calc_gematria(merged_heb.replace('\u05BE', '')),
                        })
                        merged += 1
                        i += 2
                        continue

            new_words.append(w)
            i += 1

        if len(new_words) != len(words):
            v['words'] = new_words
            v['total_gematria'] = sum(ww['gem'] for ww in new_words)

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

total = sum(len(v['words']) for c in d['chapters'] for v in c['verses'])
print(f"Merged {merged} fragments. Total words: {total}")

# Verify Lot section
for vn in [1, 5]:
    v = d['chapters'][18]['verses'][vn - 1]
    print(f'\n{v["ref"]}:')
    for w in v['words']:
        print(f'  {w["heb"]:20s}  {w["eng"]}')
