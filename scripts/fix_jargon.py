#!/usr/bin/env python3
"""Fix all remaining jargon, academic language, and unclear glosses."""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            changed = False

            # [obj.mark] -> [direct object]
            if '[obj.mark]' in e:
                e = e.replace('[obj.mark]', '[d.o.]')
                changed = True

            # "sign of the definite direct object" variants
            if 'sign of the definite' in e.lower() or 'sign of the direct' in e.lower():
                e = '[d.o.]'
                changed = True

            # (relative part.) -> which
            if '(relative part.)' in e:
                e = e.replace('(relative part.)', 'which')
                changed = True

            # "subst" -> contextual fix based on the Hebrew word
            if e == 'subst' or e.startswith('subst\u00B7') or '\u00B7subst' in e:
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'על' in key or 'מעל' in key:
                    e = e.replace('subst', 'above')
                elif 'עוד' in key:
                    e = e.replace('subst', 'still')
                elif 'נגד' in key:
                    e = e.replace('subst', 'before')
                elif 'תחת' in key:
                    e = e.replace('subst', 'beneath')
                elif 'סביב' in key:
                    e = e.replace('subst', 'around')
                elif 'אחר' in key:
                    e = e.replace('subst', 'after')
                elif 'בין' in key:
                    e = e.replace('subst', 'between')
                elif 'פנ' in key:
                    e = e.replace('subst', 'before')
                else:
                    e = e.replace('subst', 'there')
                changed = True

            # "adv" -> contextual
            if e == 'adv':
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'כן' in key:
                    e = 'so'
                elif 'שם' in key:
                    e = 'there'
                elif 'מאד' in key:
                    e = 'very'
                else:
                    e = 'thus'
                changed = True

            # "pron 3p s" and similar
            if e.startswith('pron ') or e == 'pron':
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'הוא' in key:
                    e = 'he'
                elif 'היא' in key:
                    e = 'she'
                elif 'הם' in key:
                    e = 'they'
                else:
                    e = 'he'
                changed = True

            # "inflected pers. pron..." -> clean pronoun
            if 'inflected' in e:
                if 'to me' in e or 'li' in e.lower():
                    e = 'to\u00B7me'
                elif 'to you' in e:
                    e = 'to\u00B7you'
                elif 'to us' in e:
                    e = 'to\u00B7us'
                elif 'to him' in e:
                    e = 'to\u00B7him'
                elif 'to her' in e:
                    e = 'to\u00B7her'
                elif 'to them' in e:
                    e = 'to\u00B7them'
                elif 'in him' in e or 'in it' in e:
                    e = 'in\u00B7him'
                else:
                    # Try to extract meaning
                    m = re.search(r"meaning '([^']+)'", e)
                    if m:
                        e = m.group(1).replace(' ', '\u00B7')
                    else:
                        e = 'him'
                changed = True

            # "Lamed" (letter name used as gloss) -> "to"
            if e == 'Lamed':
                e = 'to'
                changed = True
            if '\u00B7Lamed' in e:
                e = e.replace('\u00B7Lamed', '\u00B7to')
                changed = True
            if 'Lamed\u00B7' in e:
                e = e.replace('Lamed\u00B7', 'to\u00B7')
                changed = True

            # Placeholder "this" that was used for empty slots
            if e == 'this':
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'הזה' in key or 'הזאת' in key:
                    pass  # actually correct
                elif 'זה' in key or 'זאת' in key:
                    pass  # correct
                else:
                    # It's a placeholder — try root
                    if w.get('root'):
                        e = w['root']
                    changed = True

            # Generic "and" for words longer than 2 consonants
            if e == 'and':
                key = strip_n(w['heb']).replace('\u05BE', '')
                if len(key) > 3:
                    if w.get('root'):
                        e = 'and\u00B7' + w['root']
                    changed = True

            # Clean up double dots
            e = e.replace('\u00B7\u00B7', '\u00B7')
            e = e.strip('\u00B7').strip()

            if changed:
                w['eng'] = e
                fixed += 1

# Verify
remaining = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            e = w['eng']
            if '[obj.mark]' in e or 'subst' in e or '(relative' in e or 'inflected' in e or 'sign of the' in e:
                remaining += 1

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed} jargon entries. Remaining jargon: {remaining}')
