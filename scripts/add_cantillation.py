"""
Add cantillation (taamei hamikra / trope) analysis to thin verses in genesis_v3.json.
Targets verses where total renderable content is under 2000 chars.
Appends analysis to the 'insights' field.
"""

import json
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cantillation mark definitions
DISJUNCTIVE = {
    '\u0591': 'Etnachta',
    '\u0592': 'Segol',
    '\u0593': 'Shalshelet',
    '\u0594': 'Zaqef Qatan',
    '\u0595': 'Zaqef Gadol',
    '\u0596': 'Tipecha',
    '\u0597': 'Revia',
    '\u0598': 'Zarqa',
    '\u0599': 'Pashta',
    '\u059A': 'Yetiv',
    '\u059B': 'Tevir',
    '\u059C': 'Geresh',
    '\u059D': 'Geresh Muqdam',
    '\u059E': 'Gershayim',
    '\u059F': 'Qarney Para',
    '\u05A0': 'Telisha Gedola',
    '\u05A1': 'Pazer',
    '\u05AA': 'Yerah Ben Yomo',
}

CONJUNCTIVE = {
    '\u05A3': 'Munach',
    '\u05A4': 'Mahapakh',
    '\u05A5': 'Merkha',
    '\u05A6': 'Merkha Kefula',
    '\u05A7': 'Darga',
    '\u05A8': 'Qadma',
    '\u05A9': 'Telisha Qetana',
    '\u05AB': 'Ole',
}

SOF_PASUQ = '\u05C3'

COMMENTARY_FIELDS = [
    'rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
    'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar'
]


def get_cantillation_marks(heb_word):
    """Extract cantillation marks from a Hebrew word."""
    marks = []
    for ch in heb_word:
        cp = ord(ch)
        if 0x0591 <= cp <= 0x05AF or cp == 0x05C3:
            marks.append(ch)
    return marks


def classify_marks(marks):
    """Classify marks as disjunctive, conjunctive, or sof pasuq."""
    disj = []
    conj = []
    for m in marks:
        if m in DISJUNCTIVE:
            disj.append(DISJUNCTIVE[m])
        elif m in CONJUNCTIVE:
            conj.append(CONJUNCTIVE[m])
    return disj, conj


def get_total_content(verse):
    """Get total renderable content length."""
    content = ''
    for f in COMMENTARY_FIELDS:
        content += verse.get(f, '') or ''
    content += verse.get('insights', '') or ''
    content += verse.get('gem_note', '') or ''
    content += verse.get('cross_refs', '') or ''
    return content


def analyze_cantillation(verse):
    """Analyze cantillation marks in a verse and return observation text."""
    words = verse.get('words', [])
    if not words:
        return None

    # Collect per-word cantillation info
    word_marks = []
    for w in words:
        heb = w.get('heb', '')
        eng = w.get('eng', '')
        marks = get_cantillation_marks(heb)
        disj, conj = classify_marks(marks)
        word_marks.append({
            'eng': eng,
            'heb': heb,
            'disjunctive': disj,
            'conjunctive': conj,
        })

    # Total counts
    total_disj = sum(len(wm['disjunctive']) for wm in word_marks)
    total_conj = sum(len(wm['conjunctive']) for wm in word_marks)

    if total_disj == 0 and total_conj == 0:
        return None

    observations = []

    # 1. Check for Shalshelet (very rare)
    for wm in word_marks:
        if 'Shalshelet' in wm['disjunctive']:
            observations.append(
                f"This verse contains a shalshelet, one of only four in the entire Torah, "
                f"marking '{wm['eng']}' -- traditionally understood as expressing hesitation "
                f"or internal struggle."
            )
            break

    # 2. Etnachta position
    etnachta_word = None
    etnachta_idx = None
    for i, wm in enumerate(word_marks):
        if 'Etnachta' in wm['disjunctive']:
            etnachta_word = wm['eng']
            etnachta_idx = i
            break

    if etnachta_word is not None:
        total_words = len(word_marks)
        first_half = etnachta_idx + 1
        second_half = total_words - first_half
        if first_half <= second_half:
            balance = "a shorter opening clause and a longer closing clause"
        elif first_half > second_half + 2:
            balance = "a longer opening clause and a shorter closing clause"
        else:
            balance = "two roughly equal halves"
        observations.append(
            f"The etnachta (major mid-verse pause) falls on '{etnachta_word}', "
            f"dividing the verse into {balance} ({first_half} and {second_half} words)."
        )

    # 3. Disjunctive vs conjunctive count and phrase groups
    # Phrase groups = disjunctive count + 1 (each disjunctive ends a phrase)
    if total_disj > 0:
        phrase_groups = total_disj  # each disjunctive accent creates a break
        observations.append(
            f"The verse has {total_disj} disjunctive and {total_conj} conjunctive accents, "
            f"creating {phrase_groups} phrase breaks."
        )

    # 4. Notable patterns
    total_marks = total_disj + total_conj
    if total_marks > 0:
        ratio = total_conj / total_marks if total_marks > 0 else 0
        if ratio >= 0.75 and total_conj >= 3:
            observations.append(
                "The predominance of conjunctive accents gives this verse "
                "a flowing, continuous quality in its cantillation."
            )
        elif ratio <= 0.3 and total_disj >= 3:
            observations.append(
                "The high proportion of disjunctive accents gives this verse "
                "a deliberate, measured cadence with frequent pauses."
            )

    if not observations:
        return None

    # Keep to 2-4 sentences
    result = ' '.join(observations[:4])
    return result


def main():
    input_file = 'genesis_v3.json'

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_verses = 0
    thin_verses = 0
    updated_verses = 0
    shalshelet_count = 0

    for ch in data['chapters']:
        for verse in ch['verses']:
            total_verses += 1

            content = get_total_content(verse)
            if len(content) >= 2000:
                continue

            thin_verses += 1

            analysis = analyze_cantillation(verse)
            if analysis is None:
                continue

            # Check if adding cantillation note would still be reasonable
            # Append to existing insights
            existing = verse.get('insights', '') or ''
            if existing.strip():
                new_insights = existing.rstrip() + ' ' + analysis
            else:
                new_insights = analysis

            verse['insights'] = new_insights
            updated_verses += 1

            # Track shalshelet
            if 'shalshelet' in analysis.lower():
                shalshelet_count += 1
                print(f"  SHALSHELET found: {verse['ref']}")

    print(f"\nSaving {input_file}...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== Cantillation Analysis Stats ===")
    print(f"Total verses:    {total_verses}")
    print(f"Thin verses:     {thin_verses} (under 2000 chars content)")
    print(f"Updated verses:  {updated_verses}")
    print(f"Shalshelet:      {shalshelet_count} verses")
    print(f"Done.")


if __name__ == '__main__':
    main()
