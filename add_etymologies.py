#!/usr/bin/env python3
"""Add Hebrew name etymologies to thin-content verses in genesis_v3.json."""

import json
import sys
import re
import unicodedata

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Comprehensive etymology dictionary for Genesis names
# Keys: English name variants -> etymology text (no Hebrew characters)
ETYMOLOGIES = {
    # PEOPLE
    "Adam": 'The name Adam ("man, humanity") derives from the root adamah meaning "earth, ground."',
    "Eve": 'The name Eve/Chavah ("life-giver, living") derives from the root chai meaning "life."',
    "Chavah": 'The name Eve/Chavah ("life-giver, living") derives from the root chai meaning "life."',
    "Cain": 'The name Cain/Kayin ("acquired, possessed") reflects Eve\'s declaration: "I have acquired a man."',
    "Abel": 'The name Abel/Hevel ("breath, vapor, vanity") suggests the fleeting nature of life.',
    "Seth": 'The name Seth/Shet ("appointed, placed") reflects "God appointed another seed."',
    "Enosh": 'The name Enosh ("mortal man, frail humanity") emphasizes human vulnerability.',
    "Kenan": 'The name Kenan/Keinan ("possession" or "smith") suggests acquisition.',
    "Mahalalel": 'The name Mahalalel ("praise of God") combines praise with the divine name.',
    "Jared": 'The name Jared/Yered ("descent") derives from yarad meaning "to descend."',
    "Enoch": 'The name Enoch/Chanoch ("dedicated, initiated") derives from chanakh meaning "to dedicate."',
    "Methuselah": 'The name Methuselah/Metushelach ("man of the dart" or "his death shall send") is notable because he died the year of the Flood.',
    "Lamech": 'The name Lamech is of uncertain meaning, possibly "powerful" or "to make low."',
    "Noah": 'The name Noah/Noach ("rest, comfort") derives from nacham meaning "to comfort."',
    "Shem": 'The name Shem ("name, renown") signifies reputation and legacy.',
    "Ham": 'The name Ham/Cham ("hot, warm") may relate to southern warmth.',
    "Japheth": 'The name Japheth/Yefet ("beauty, expansion") derives from yafah meaning "to be beautiful."',
    "Abram": 'The name Abram/Avram ("exalted father") combines av ("father") with ram ("exalted").',
    "Abraham": 'The name Abraham/Avraham ("father of multitudes") was expanded from Abram to signify his role as patriarch of many nations.',
    "Sarah": 'The name Sarah ("princess") derives from sar meaning "prince, ruler."',
    "Sarai": 'The name Sarai/Sarah ("princess") derives from sar meaning "prince, ruler."',
    "Hagar": 'The name Hagar ("stranger, sojourner") reflects her status as a foreigner.',
    "Ishmael": 'The name Ishmael/Yishmael ("God hears") combines shama ("to hear") with El ("God").',
    "Isaac": 'The name Isaac/Yitzchak ("he will laugh") derives from tzachak meaning "to laugh."',
    "Rebekah": 'The name Rebekah/Rivkah ("to bind, captivating") suggests beauty that ensnares.',
    "Esau": 'The name Esau/Esav ("hairy" or "made, completed") may derive from asah meaning "to make."',
    "Jacob": 'The name Jacob/Yaakov ("heel-grasper, supplanter") derives from akev meaning "heel."',
    "Israel": 'The name Israel/Yisrael ("wrestles with God" or "prince of God") combines sarah ("to strive") with El ("God").',
    "Leah": 'The name Leah ("weary" or "wild cow") may reflect weariness or strength.',
    "Rachel": 'The name Rachel ("ewe, female sheep") evokes pastoral imagery.',
    "Reuben": 'The name Reuben/Reuven ("see, a son!") combines ra\'ah ("to see") with ben ("son").',
    "Simeon": 'The name Simeon/Shimon ("hearing, he heard") derives from shama meaning "to hear."',
    "Levi": 'The name Levi ("attached, joined") derives from lavah meaning "to join."',
    "Judah": 'The name Judah/Yehudah ("praise") derives from yadah meaning "to praise, to thank."',
    "Dan": 'The name Dan ("judge") derives from din meaning "to judge."',
    "Naphtali": 'The name Naphtali ("my wrestling") derives from pathal meaning "to wrestle."',
    "Gad": 'The name Gad ("fortune, luck") signifies good fortune.',
    "Asher": 'The name Asher ("happy, blessed") derives from osher meaning "happiness."',
    "Issachar": 'The name Issachar/Yissachar ("reward, hired") derives from sachar meaning "wages."',
    "Zebulun": 'The name Zebulun/Zevulun ("dwelling, honor") derives from zaval meaning "to dwell."',
    "Dinah": 'The name Dinah ("judgment") derives from din meaning "to judge."',
    "Joseph": 'The name Joseph/Yosef ("he will add") derives from yasaf meaning "to add."',
    "Benjamin": 'The name Benjamin/Binyamin ("son of the right hand") combines ben ("son") with yamin ("right hand").',
    "Ben-oni": 'The name Ben-oni ("son of my sorrow") combines ben ("son") with oni ("sorrow").',
    "Manasseh": 'The name Manasseh/Menasheh ("causing to forget") derives from nashah meaning "to forget."',
    "Ephraim": 'The name Ephraim ("doubly fruitful") derives from parah meaning "to be fruitful."',
    "Tamar": 'The name Tamar ("date palm") evokes beauty and fertility.',
    "Perez": 'The name Perez/Peretz ("breach, breaking through") derives from paratz meaning "to break."',
    "Zerah": 'The name Zerah/Zerach ("rising, dawning") derives from zarach meaning "to shine."',
    "Potiphar": 'The name Potiphar is Egyptian in origin, meaning "he whom Ra gave."',
    "Pharaoh": 'The name Pharaoh is Egyptian, meaning "great house," the title of Egypt\'s ruler.',
    "Lot": 'The name Lot ("covering, veil") suggests concealment.',
    "Melchizedek": 'The name Melchizedek/Malki-Tzedek ("king of righteousness") combines melech ("king") with tzedek ("righteousness").',
    "Nimrod": 'The name Nimrod ("rebel") derives from marad meaning "to rebel."',
    "Peleg": 'The name Peleg ("division") derives from palag meaning "to divide" -- "in his days the earth was divided."',

    # PLACES
    "Eden": 'The name Eden ("delight, pleasure") signifies a place of joy.',
    "Babel": 'The name Babel/Bavel ("confusion") derives from balal meaning "to confuse."',
    "Canaan": 'The name Canaan/Kenaan ("lowland" or "merchant") designates both the land and its people.',
    "Hebron": 'The name Hebron/Chevron ("association, alliance") derives from chaver meaning "friend."',
    "Beer-sheba": 'The name Beer-sheba/Be\'er Sheva ("well of the oath" or "well of seven") combines be\'er ("well") with sheva ("oath/seven").',
    "Bethel": 'The name Bethel/Beit-El ("house of God") combines bayit ("house") with El ("God").',
    "Peniel": 'The name Peniel/Penuel ("face of God") combines panim ("face") with El ("God").',
    "Penuel": 'The name Peniel/Penuel ("face of God") combines panim ("face") with El ("God").',
    "Moriah": 'The name Moriah ("seen by God" or "teaching of God") may relate to God\'s provision.',
    "Sodom": 'The name Sodom possibly means "burning" or "secret council."',
    "Zoar": 'The name Zoar ("small, insignificant") derives from tza\'ir meaning "small."',
    "Gilead": 'The name Gilead ("heap of witness") combines gal ("heap") with ed ("witness").',
    "Mahanaim": 'The name Mahanaim ("two camps") derives from machaneh meaning "camp."',
    "Succoth": 'The name Succoth/Sukkot ("booths, shelters") refers to temporary dwellings.',
    "Goshen": 'The name Goshen possibly means "drawing near."',
    "Pishon": 'The name Pishon ("disperser") derives from push meaning "to spread."',
    "Gihon": 'The name Gihon ("gusher, bursting forth") derives from giach meaning "to gush."',
    "Tigris": 'The name Tigris/Chiddekel ("rapid") reflects the river\'s swift current.',
    "Euphrates": 'The name Euphrates/Perat ("fruitful") derives from parah meaning "to be fruitful."',

    # NATIONS
    "Gomer": 'The name Gomer ("completion") derives from gamar meaning "to complete."',
    "Magog": 'The name Magog ("land of Gog") refers to a northern territory.',
    "Madai": 'The name Madai designates the ancestor of the Medes.',
    "Javan": 'The name Javan/Yavan designates the ancestor of the Greeks (Ionians).',
    "Tubal": 'The name Tubal is associated with metalworking.',
    "Meshech": 'The name Meshech ("to draw out") suggests extension or trade.',
    "Tiras": 'The name Tiras possibly designates the ancestor of the Thracians.',
    "Cush": 'The name Cush/Kush designates the ancestor of Ethiopians and Nubians.',
    "Mizraim": 'The name Mizraim/Mitzrayim ("Egypt") literally means "narrow places" or "double straits."',
    "Put": 'The name Put/Phut designates the ancestor of the Libyans.',
    "Arpachshad": 'The name Arpachshad is of uncertain meaning.',
    "Lud": 'The name Lud designates the ancestor of the Lydians.',
    "Aram": 'The name Aram ("highland") designates the ancestor of the Arameans (Syrians).',
    "Elam": 'The name Elam ("eternity" or "hidden") designates an ancient nation east of Mesopotamia.',
    "Asshur": 'The name Asshur/Ashur ("level plain") designates the ancestor of the Assyrians.',
    "Eber": 'The name Eber/Ever ("one who crosses over") derives from avar meaning "to cross" -- ancestor of the Hebrews.',
    "Seir": 'The name Seir ("hairy, rough") designates the mountainous region of Edom.',
}

# Map English names to consonantal Hebrew forms (without niqqud) for matching
# We'll strip niqqud from verse words and compare
NAME_HEBREW_MAP = {
    "Adam": ["אדם"],
    "Eve": ["חוה"],
    "Chavah": ["חוה"],
    "Cain": ["קין"],
    "Abel": ["הבל"],
    "Seth": ["שת"],
    "Enosh": ["אנוש"],
    "Kenan": ["קינן"],
    "Mahalalel": ["מהללאל"],
    "Jared": ["ירד"],
    "Enoch": ["חנוך"],
    "Methuselah": ["מתושלח"],
    "Lamech": ["למך"],
    "Noah": ["נח"],
    "Shem": ["שם"],
    "Ham": ["חם"],
    "Japheth": ["יפת"],
    "Abram": ["אברם"],
    "Abraham": ["אברהם"],
    "Sarah": ["שרה"],
    "Sarai": ["שרי"],
    "Hagar": ["הגר"],
    "Ishmael": ["ישמעאל"],
    "Isaac": ["יצחק"],
    "Rebekah": ["רבקה"],
    "Esau": ["עשו"],
    "Jacob": ["יעקב"],
    "Israel": ["ישראל"],
    "Leah": ["לאה"],
    "Rachel": ["רחל"],
    "Reuben": ["ראובן"],
    "Simeon": ["שמעון"],
    "Levi": ["לוי"],
    "Judah": ["יהודה"],
    "Dan": ["דן"],
    "Naphtali": ["נפתלי"],
    "Gad": ["גד"],
    "Asher": ["אשר"],
    "Issachar": ["יששכר"],
    "Zebulun": ["זבולון", "זבולן"],
    "Dinah": ["דינה"],
    "Joseph": ["יוסף"],
    "Benjamin": ["בנימין", "בנימן"],
    "Ben-oni": ["בנאוני"],
    "Manasseh": ["מנשה"],
    "Ephraim": ["אפרים"],
    "Tamar": ["תמר"],
    "Perez": ["פרץ"],
    "Zerah": ["זרח"],
    "Potiphar": ["פוטיפר", "פוטיפרע"],
    "Pharaoh": ["פרעה"],
    "Lot": ["לוט"],
    "Melchizedek": ["מלכיצדק", "מלכי־צדק"],
    "Nimrod": ["נמרד"],
    "Peleg": ["פלג"],
    "Eden": ["עדן"],
    "Babel": ["בבל"],
    "Canaan": ["כנען"],
    "Hebron": ["חברון"],
    "Beer-sheba": ["באר שבע", "בארשבע"],
    "Bethel": ["ביתאל", "בית־אל"],
    "Peniel": ["פניאל"],
    "Penuel": ["פנואל"],
    "Moriah": ["מריה", "מוריה"],
    "Sodom": ["סדם", "סדום"],
    "Zoar": ["צוער", "צער"],
    "Gilead": ["גלעד"],
    "Mahanaim": ["מחנים"],
    "Succoth": ["סכות", "סכת"],
    "Goshen": ["גשן"],
    "Pishon": ["פישון"],
    "Gihon": ["גיחון"],
    "Tigris": ["חדקל"],
    "Euphrates": ["פרת"],
    "Gomer": ["גמר"],
    "Magog": ["מגוג"],
    "Madai": ["מדי"],
    "Javan": ["יון"],
    "Tubal": ["תובל", "תבל"],
    "Meshech": ["משך"],
    "Tiras": ["תירס"],
    "Cush": ["כוש"],
    "Mizraim": ["מצרים"],
    "Put": ["פוט"],
    "Arpachshad": ["ארפכשד"],
    "Lud": ["לוד"],
    "Aram": ["ארם"],
    "Elam": ["עילם"],
    "Asshur": ["אשור"],
    "Eber": ["עבר"],
    "Seir": ["שעיר"],
}


def strip_niqqud(text):
    """Remove niqqud (vowel points) and cantillation marks from Hebrew text."""
    result = []
    for ch in text:
        cp = ord(ch)
        # Skip Hebrew niqqud (0x0591-0x05BD, 0x05BF, 0x05C1-0x05C2, 0x05C4-0x05C5, 0x05C7)
        # and cantillation marks
        if 0x0591 <= cp <= 0x05BD:
            continue
        if cp == 0x05BF:
            continue
        if 0x05C1 <= cp <= 0x05C2:
            continue
        if 0x05C4 <= cp <= 0x05C5:
            continue
        if cp == 0x05C7:
            continue
        result.append(ch)
    return ''.join(result)


def get_content_length(verse):
    """Calculate total renderable content length."""
    fields = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'insights', 'gem_note',
              'cross_refs', 'or_hachaim', 'chizkuni', 'rabbeinu_bahya', 'kli_yakar']
    total = 0
    for fld in fields:
        val = verse.get(fld, '')
        if val:
            total += len(str(val))
    return total


# Words that share consonantal forms with names but are common words.
# Map: name -> set of English translations that indicate it's NOT the name.
AMBIGUOUS_NAMES = {
    "Asher": {"which", "who", "that", "whom", "because", "since", "where",
              "as", "what", "whatever", "wherever", "whoever", "happy",
              "which·bear·to", "which·said", "which·made", "in", "so",
              "when", "how", "just·as", "inasmuch"},
    "Shem": {"name", "there", "thence", "fame", "renown", "named"},
    "Adam": {"man", "mankind", "person", "human", "people", "men", "anyone",
             "humankind", "mortal"},
    "Dan": {"judged", "judge", "judges", "judging", "to·judge"},
    "Eber": {"passed", "cross", "crossed", "passing", "beyond", "side",
             "other·side", "ford", "across", "pass·over", "pass", "over",
             "transgressed", "through"},
    "Gad": {"fortune", "troop", "a·troop"},
    "Ham": {"hot", "warm", "father-in-law", "father·in·law"},
    "Lot": {"covering", "veil", "wrap"},
    "Aram": {"highland"},
    "Euphrates": {"cow", "cows", "heifer", "heifers", "kine"},
    "Esau": {"made", "did", "do", "make", "done", "does", "making", "doer"},
    "Levi": {"joined", "attached"},
    "Judah": {"praise", "praised", "praising"},
    "Rachel": {"ewe", "sheep"},
    "Leah": {"weary", "tired"},
    "Jared": {"descended", "descend", "went·down", "went down", "go·down",
              "come·down"},
}


def is_name_usage(name, eng_field):
    """Check if a word with matching Hebrew is actually used as the name (not a common word)."""
    if name not in AMBIGUOUS_NAMES:
        return True  # Not ambiguous, assume it's the name

    # Clean up the English field for comparison
    eng_lower = eng_field.lower().strip()
    # Strip common prefixes like "and·", "the·", "in·", etc.
    for prefix in ["and·", "the·", "of·", "in·", "to·", "from·", "by·",
                   "and ", "the ", "of ", "in ", "to ", "from ", "by "]:
        if eng_lower.startswith(prefix):
            eng_lower = eng_lower[len(prefix):]

    # If eng matches a non-name meaning, it's not the name
    non_name_meanings = AMBIGUOUS_NAMES[name]
    if eng_lower in non_name_meanings:
        return False

    # If the English contains the name itself (case-insensitive), it's the name
    if name.lower() in eng_field.lower():
        return True

    # For remaining cases, if the eng field is capitalized like a proper noun, likely a name
    # But be careful with start-of-verse capitalization
    if eng_field and eng_field[0].isupper() and eng_lower not in non_name_meanings:
        return True

    return True  # Default: assume it's the name


def find_names_in_verse(verse):
    """Find names that appear in a verse's words by matching consonantal Hebrew."""
    words = verse.get('words', [])
    found_names = []
    seen_etymologies = set()  # Track unique etymology texts

    for word in words:
        heb = strip_niqqud(word.get('heb', ''))
        eng = word.get('eng', '')
        # Also strip maqaf (Hebrew hyphen -)
        heb_clean = heb.replace('\u05be', '').replace('-', '')

        for name, hebrew_forms in NAME_HEBREW_MAP.items():
            for form in hebrew_forms:
                form_clean = form.replace('\u05be', '').replace('-', '').replace(' ', '')
                if heb_clean == form_clean:
                    # Disambiguate: is this actually the name or a common word?
                    if not is_name_usage(name, eng):
                        break
                    etym = ETYMOLOGIES.get(name, '')
                    if etym and etym not in seen_etymologies:
                        found_names.append(name)
                        seen_etymologies.add(etym)
                    break

    return found_names


def strip_previous_etymologies(data):
    """Remove any previously-added etymology sentences from insights fields."""
    # Collect all etymology texts we might have added
    all_etyms = set(ETYMOLOGIES.values())
    cleaned = 0
    for ch in data['chapters']:
        for verse in ch['verses']:
            insights = verse.get('insights', '') or ''
            if not insights:
                continue
            original = insights
            for etym in all_etyms:
                insights = insights.replace(' ' + etym, '')
                insights = insights.replace(etym, '')
            insights = insights.rstrip()
            if insights != original:
                verse['insights'] = insights
                cleaned += 1
    print(f"  Cleaned previous etymologies from {cleaned} verses.")


def main():
    input_file = 'K:/TorahByWord/genesis_v3.json'

    print("Loading genesis_v3.json...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # First, strip any previously-added etymologies
    print("Cleaning previous etymology additions...")
    strip_previous_etymologies(data)

    total_verses = 0
    thin_verses = 0
    updated_verses = 0
    total_etymologies_added = 0

    for ch in data['chapters']:
        for verse in ch['verses']:
            total_verses += 1
            content_len = get_content_length(verse)

            if content_len >= 2000:
                continue

            thin_verses += 1
            names = find_names_in_verse(verse)

            if not names:
                continue

            # Check existing insights for already-mentioned etymologies
            existing_insights = verse.get('insights', '') or ''
            new_etymologies = []

            for name in names:
                etym = ETYMOLOGIES[name]
                # Check if this etymology (or name) is already mentioned
                if name in existing_insights and "derives" in existing_insights:
                    continue
                # Also skip if the exact etymology text is already there
                if etym in existing_insights:
                    continue
                new_etymologies.append(etym)

            if not new_etymologies:
                continue

            # Build the etymology addition
            etym_text = ' '.join(new_etymologies)

            if existing_insights:
                verse['insights'] = existing_insights.rstrip() + ' ' + etym_text
            else:
                verse['insights'] = etym_text

            updated_verses += 1
            total_etymologies_added += len(new_etymologies)
            print(f"  {ch['chapter']}:{verse['verse']} - Added {len(new_etymologies)} etymology(ies): {', '.join(names[:5])}")

    print(f"\nSummary:")
    print(f"  Total verses: {total_verses}")
    print(f"  Thin verses (<2000 chars): {thin_verses}")
    print(f"  Verses updated: {updated_verses}")
    print(f"  Total etymologies added: {total_etymologies_added}")

    print("\nSaving genesis_v3.json...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Done.")


if __name__ == '__main__':
    main()
