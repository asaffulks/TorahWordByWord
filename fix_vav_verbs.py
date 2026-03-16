"""Fix all vav-consecutive verbs: 'to X' -> 'and·X-ed'"""
import json, re, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def strip_n(t):
    return re.sub(r'[\u0591-\u05AF\u05B0-\u05C7]', '', t)

TO_PAST = {
    'to go out': 'and\u00B7went\u00B7out', 'to rise': 'and\u00B7rose',
    'to add': 'and\u00B7added', 'to hasten': 'and\u00B7hurried',
    'to give to drink': 'and\u00B7gave\u00B7drink', 'to go down': 'and\u00B7went\u00B7down',
    'to cover': 'and\u00B7covered', 'to lie down': 'and\u00B7lay\u00B7down',
    'to put': 'and\u00B7put', 'to flee': 'and\u00B7fled',
    'to answer': 'and\u00B7answered', 'to love': 'and\u00B7loved',
    'to recognise': 'and\u00B7recognized', 'to rest': 'and\u00B7rested',
    'to do': 'and\u00B7did', 'to dress': 'and\u00B7dressed',
    'to awake': 'and\u00B7awoke', 'to bow down': 'and\u00B7bowed\u00B7down',
    'to lodge': 'and\u00B7lodged', 'to dig': 'and\u00B7dug',
    'to steal': 'and\u00B7stole', 'to pass over or by or through': 'and\u00B7passed\u00B7over',
    'to leave': 'and\u00B7left', 'to rule': 'and\u00B7ruled',
    'to cease': 'and\u00B7ceased', 'to settle down': 'and\u00B7settled',
    'to prevail': 'and\u00B7prevailed', 'to strike': 'and\u00B7struck',
    'to be behind': 'and\u00B7remained', 'to circumcise': 'and\u00B7circumcised',
    'to overlook': 'and\u00B7looked\u00B7down', 'to turn': 'and\u00B7turned',
    'to strengthen': 'and\u00B7strengthened', 'to be bad': 'and\u00B7was\u00B7displeased',
    'to tie': 'and\u00B7tied', 'to seize': 'and\u00B7seized',
    'to weigh': 'and\u00B7weighed', 'to draw': 'and\u00B7drew',
    'to strive': 'and\u00B7strove', 'to hate': 'and\u00B7hated',
    'to snatch away': 'and\u00B7snatched', 'to put together': 'and\u00B7gathered',
    'to get': 'and\u00B7acquired', 'to be good': 'and\u00B7was\u00B7good',
    'to tear': 'and\u00B7tore', 'to refuse': 'and\u00B7refused',
    'to create': 'and\u00B7created', 'to sleep': 'and\u00B7slept',
    'to shut': 'and\u00B7shut', 'to kill': 'and\u00B7killed',
    'to hurt': 'and\u00B7hurt', 'to wipe': 'and\u00B7wiped',
    'to smell': 'and\u00B7smelled', 'to be or become drunk or drunken': 'and\u00B7became\u00B7drunk',
    'to uncover': 'and\u00B7uncovered', 'to mourn': 'and\u00B7mourned',
    'to complete': 'and\u00B7completed', 'to call': 'and\u00B7called',
    'to be fruitful': 'and\u00B7was\u00B7fruitful', 'to multiply': 'and\u00B7multiplied',
    'to curse': 'and\u00B7cursed', 'to form': 'and\u00B7formed',
    'to breathe': 'and\u00B7breathed', 'to set': 'and\u00B7set',
    'to cause to grow': 'and\u00B7caused\u00B7to\u00B7grow', 'to keep': 'and\u00B7kept',
    'to sew': 'and\u00B7sewed', 'to make': 'and\u00B7made',
    'to drive out': 'and\u00B7drove\u00B7out', 'to get to know': 'and\u00B7knew',
    'to name': 'and\u00B7named', 'to cry out': 'and\u00B7cried\u00B7out',
    'to separate': 'and\u00B7separated', 'to pitch a tent': 'and\u00B7pitched\u00B7tent',
    'to move': 'and\u00B7moved', 'to save': 'and\u00B7saved',
    'to be willing': 'and\u00B7was\u00B7willing', 'to scatter': 'and\u00B7scattered',
    'to confuse': 'and\u00B7confused', 'to conceive': 'and\u00B7conceived',
    'to bear': 'and\u00B7bore', 'to see': 'and\u00B7saw',
    'to take': 'and\u00B7took', 'to give': 'and\u00B7gave',
    'to be': 'and\u00B7was', 'to say': 'and\u00B7said',
    'to lift': 'and\u00B7lifted', 'to go': 'and\u00B7went',
    'to return': 'and\u00B7returned', 'to sit': 'and\u00B7sat',
    'to send': 'and\u00B7sent', 'to come': 'and\u00B7came',
    'to build': 'and\u00B7built', 'to dwell': 'and\u00B7dwelt',
    'to command': 'and\u00B7commanded', 'to bring': 'and\u00B7brought',
    'to eat': 'and\u00B7ate', 'to be afraid': 'and\u00B7was\u00B7afraid',
    'to change': 'and\u00B7changed', 'to console': 'and\u00B7consoled',
    'to visit': 'and\u00B7visited', 'to embalm': 'and\u00B7embalmed',
    'to adjure': 'and\u00B7made\u00B7swear', 'to sprout': 'and\u00B7sprouted',
    'to reach': 'and\u00B7reached', 'to mix': 'and\u00B7mixed',
    'to hide': 'and\u00B7hid', 'to lean': 'and\u00B7leaned',
    'to warn': 'and\u00B7warned', 'to slaughter': 'and\u00B7slaughtered',
    'to graze': 'and\u00B7grazed', 'to envy': 'and\u00B7envied',
    'to inherit': 'and\u00B7inherited', 'to set up': 'and\u00B7set\u00B7up',
    'to pour': 'and\u00B7poured', 'to join': 'and\u00B7joined',
    'to hire': 'and\u00B7hired', 'to prosper': 'and\u00B7prospered',
    'to increase': 'and\u00B7increased', 'to strip': 'and\u00B7stripped',
    'to peel': 'and\u00B7peeled', 'to be wroth': 'and\u00B7was\u00B7angry',
    'to search': 'and\u00B7searched', 'to wrestle': 'and\u00B7wrestled',
    'to limp': 'and\u00B7limped', 'to embrace': 'and\u00B7embraced',
    'to offer': 'and\u00B7offered', 'to trouble': 'and\u00B7troubled',
    'to go up': 'and\u00B7went\u00B7up', 'to be able': 'and\u00B7was\u00B7able',
    'to load': 'and\u00B7loaded', 'to interpret': 'and\u00B7interpreted',
    'to shave': 'and\u00B7shaved', 'to gather together': 'and\u00B7gathered',
    'to open': 'and\u00B7opened', 'to fear': 'and\u00B7feared',
    'to be conspicuous': 'and\u00B7told', 'to be hot': 'and\u00B7was\u00B7angry',
    'to be sorry': 'and\u00B7was\u00B7grieved', 'to remember': 'and\u00B7remembered',
    'to drink': 'and\u00B7drank', 'to run': 'and\u00B7ran',
    'to go in': 'and\u00B7brought', 'to grow': 'and\u00B7grew\u00B7great',
    'to swear': 'and\u00B7swore', 'to stretch out': 'and\u00B7stretched\u00B7out',
    'to ask': 'and\u00B7asked', 'to laugh': 'and\u00B7laughed',
    'to rise or start early': 'and\u00B7rose\u00B7early',
    'to accomplish': 'and\u00B7finished', 'to know': 'and\u00B7knew',
    'to expire': 'and\u00B7expired',
    'to be or become king or queen': 'and\u00B7reigned',
    'to gather': 'and\u00B7was\u00B7gathered', 'to fall': 'and\u00B7fell',
    'to weep': 'and\u00B7wept', 'to pass over': 'and\u00B7crossed',
    'to begin': 'and\u00B7began', 'to sell': 'and\u00B7sold',
    'to find': 'and\u00B7found', 'to plant': 'and\u00B7planted',
    'to count': 'and\u00B7counted', 'to bury': 'and\u00B7buried',
    'to bless': 'and\u00B7blessed', 'to touch': 'and\u00B7touched',
    'to speak': 'and\u00B7spoke', 'to serve': 'and\u00B7served',
    'to dream': 'and\u00B7dreamed', 'to turn aside': 'and\u00B7turned',
    'to wash': 'and\u00B7washed', 'to place': 'and\u00B7placed',
    'to bind': 'and\u00B7bound', 'to kiss': 'and\u00B7kissed',
    'to meet': 'and\u00B7met', 'to pursue': 'and\u00B7pursued',
    'to stand': 'and\u00B7stood', 'to throw': 'and\u00B7threw',
    'to fill': 'and\u00B7filled', 'to divide': 'and\u00B7divided',
    'to make a covenant': 'and\u00B7made\u00B7a\u00B7covenant',
    'to die': 'and\u00B7died', 'to hear': 'and\u00B7heard',
    'to give, put, set': 'and\u00B7gave', 'to smite': 'and\u00B7struck',
    'to write': 'and\u00B7wrote', 'to draw near': 'and\u00B7drew\u00B7near',
}

# Compound junk fixes
COMPOUND_CLEAN = {
    "to give\u00B7inflected pers. pron. meaning 'to me'": 'and\u00B7gave\u00B7to\u00B7me',
    'to take\u00B7Lamed': 'and\u00B7took\u00B7to',
    'to be\u00B7Lamed': 'and\u00B7was\u00B7to',
    'to be\u00B7evening': 'and\u00B7was\u00B7evening',
    'to be\u00B7cattle': 'and\u00B7was\u00B7morning',
    'to be\u00B7adv': 'and\u00B7was\u00B7so',
    'to give\u00B7Lamed': 'and\u00B7gave\u00B7to',
    'to be\u00B7thus': 'and\u00B7was\u00B7so',
}

with open('K:/TorahByWord/genesis.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

fixed = 0
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            key = strip_n(w['heb']).replace('\u05BE', '')
            eng = w['eng']

            # Compound fixes first
            if eng in COMPOUND_CLEAN:
                w['eng'] = COMPOUND_CLEAN[eng]
                fixed += 1
                continue

            # Vav-consecutive: any word starting with וי/ות with 'to ' gloss
            has_vav = key.startswith('וי') or key.startswith('ות') or key.startswith('ונ')
            if has_vav and eng.startswith('to '):
                if eng in TO_PAST:
                    w['eng'] = TO_PAST[eng]
                    fixed += 1
                else:
                    # Generic fallback: strip 'to ' and prefix 'and·'
                    verb = eng[3:].strip()
                    w['eng'] = 'and\u00B7' + verb
                    fixed += 1
                continue

            # Fix compound vav-consecutive glosses like 'to be·something'
            if has_vav and '\u00B7' in eng:
                parts = eng.split('\u00B7')
                if parts[0].startswith('to '):
                    if parts[0] in TO_PAST:
                        parts[0] = TO_PAST[parts[0]]
                    else:
                        parts[0] = 'and\u00B7' + parts[0][3:]
                    w['eng'] = '\u00B7'.join(parts)
                    fixed += 1

# Also fix remaining 'Lamed' fragments
for c in d['chapters']:
    for v in c['verses']:
        for w in v['words']:
            if w['eng'] == 'Lamed' or w['eng'] == 'to\u00B7Lamed':
                w['eng'] = 'to'
                fixed += 1
            elif w['eng'].endswith('\u00B7Lamed'):
                w['eng'] = w['eng'].replace('\u00B7Lamed', '\u00B7to')
                fixed += 1
            # Fix 'cattle' -> 'morning' (בקר)
            if 'cattle' in w['eng']:
                key = strip_n(w['heb']).replace('\u05BE', '')
                if 'בקר' in key:
                    w['eng'] = w['eng'].replace('cattle', 'morning')
                    fixed += 1

remaining = sum(1 for c in d['chapters'] for v in c['verses'] for w in v['words']
                if (strip_n(w['heb']).replace('\u05BE', '').startswith(('וי', 'ות'))
                    and w['eng'].startswith('to ')))

with open('K:/TorahByWord/genesis.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed}. Remaining vav-consecutive "to verb": {remaining}')
