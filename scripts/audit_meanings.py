#!/usr/bin/env python3
"""
Deep audit and fix of meanings arrays in genesis_v3.json.

Strategy:
1. Build a mapping from ETCBC lexemes to their glosses
2. Build a comprehensive Hebrew-root-to-English-meanings dictionary
3. For every word in genesis_v3.json, match it to an ETCBC lexeme
4. Detect garbage in meanings lists (Hebrew chars, Syriac, BDB artifacts,
   wrong Strong's matches, proper nouns for common words, etc.)
5. Replace with correct meanings from curated root dictionary
6. Also fix eng field if it contains artifacts
"""

import sys
import json
import re
import os
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Curated root-to-meanings dictionary ───────────────────────────────────
# Based on standard Biblical Hebrew lexicons (BDB, HALOT)
# Format: ETCBC lexeme -> list of valid English meanings
ROOT_MEANINGS = {
    # ── Common verbs ──
    'ברא': ['create', 'shape', 'form', 'fashion'],
    'אמר': ['say', 'speak', 'tell', 'declare', 'command', 'promise', 'think'],
    'עשׂה': ['make', 'do', 'accomplish', 'produce', 'act', 'perform', 'prepare', 'work'],
    'עשה': ['make', 'do', 'accomplish', 'produce', 'act', 'perform', 'prepare', 'work'],
    'ראה': ['see', 'look', 'behold', 'perceive', 'observe', 'appear', 'show', 'regard', 'consider', 'provide'],
    'ידע': ['know', 'perceive', 'learn', 'understand', 'recognize', 'acknowledge', 'be acquainted with'],
    'שׁמע': ['hear', 'listen', 'obey', 'heed', 'understand', 'answer', 'pay attention'],
    'שמע': ['hear', 'listen', 'obey', 'heed', 'understand', 'answer', 'pay attention'],
    'הלך': ['walk', 'go', 'come', 'depart', 'proceed', 'travel', 'follow'],
    'בוא': ['come', 'enter', 'go in', 'arrive', 'bring', 'set (of sun)'],
    'נתן': ['give', 'put', 'set', 'place', 'make', 'deliver', 'grant', 'allow', 'yield', 'appoint'],
    'לקח': ['take', 'seize', 'receive', 'accept', 'fetch', 'carry away', 'marry'],
    'שׁוב': ['return', 'turn back', 'come back', 'go back', 'restore', 'repent', 'again'],
    'שוב': ['return', 'turn back', 'come back', 'go back', 'restore', 'repent', 'again'],
    'קרא': ['call', 'name', 'proclaim', 'read', 'cry out', 'summon', 'invite'],
    'דבר': ['speak', 'say', 'talk', 'tell', 'promise', 'command', 'declare', 'warn', 'word', 'thing', 'matter', 'affair'],
    'ישׁב': ['sit', 'dwell', 'live', 'remain', 'stay', 'inhabit', 'settle', 'abide'],
    'ישב': ['sit', 'dwell', 'live', 'remain', 'stay', 'inhabit', 'settle', 'abide'],
    'עלה': ['go up', 'ascend', 'climb', 'rise', 'offer up', 'bring up', 'grow'],
    'ירד': ['go down', 'descend', 'come down', 'sink', 'decline'],
    'אכל': ['eat', 'devour', 'consume', 'feed', 'dine'],
    'שׁלח': ['send', 'stretch out', 'reach out', 'let go', 'release', 'dismiss'],
    'שלח': ['send', 'stretch out', 'reach out', 'let go', 'release', 'dismiss'],
    'מצא': ['find', 'discover', 'encounter', 'meet', 'attain', 'obtain', 'reach'],
    'שׂים': ['put', 'set', 'place', 'lay', 'appoint', 'make', 'establish'],
    'שים': ['put', 'set', 'place', 'lay', 'appoint', 'make', 'establish'],
    'קום': ['rise', 'arise', 'stand', 'stand up', 'get up', 'establish', 'confirm'],
    'פנה': ['turn', 'face', 'look', 'appear', 'clear away', 'presence', 'surface', 'front', 'before'],
    'נשׂא': ['lift', 'carry', 'bear', 'take', 'raise', 'forgive', 'exalt'],
    'נשא': ['lift', 'carry', 'bear', 'take', 'raise', 'forgive', 'exalt'],
    'עבד': ['serve', 'work', 'till', 'labor', 'be a servant', 'worship'],
    'שׁמר': ['keep', 'guard', 'watch', 'observe', 'preserve', 'protect', 'be careful'],
    'שמר': ['keep', 'guard', 'watch', 'observe', 'preserve', 'protect', 'be careful'],
    'זכר': ['remember', 'recall', 'mention', 'be mindful'],
    'כתב': ['write', 'record', 'inscribe'],
    'מות': ['die', 'put to death', 'kill', 'slay'],
    'חיה': ['live', 'be alive', 'revive', 'recover', 'preserve alive'],
    'ילד': ['bear', 'give birth', 'beget', 'bring forth', 'be born'],
    'אהב': ['love', 'be fond of', 'like', 'be a friend'],
    'שׂנא': ['hate', 'be hostile to'],
    'שנא': ['hate', 'be hostile to'],
    'ירא': ['fear', 'be afraid', 'revere', 'be in awe', 'dread'],
    'בנה': ['build', 'construct', 'rebuild', 'establish'],
    'פתח': ['open', 'loosen', 'free', 'engrave'],
    'סגר': ['close', 'shut', 'deliver up'],
    'מלא': ['fill', 'be full', 'fulfill', 'complete', 'overflow'],
    'חזק': ['be strong', 'strengthen', 'harden', 'prevail', 'seize', 'take hold'],
    'גדל': ['grow', 'be great', 'become great', 'magnify', 'bring up', 'nourish'],
    'קטן': ['be small', 'be insignificant', 'be young'],
    'טוב': ['be good', 'be pleasing', 'be well', 'be glad'],
    'רעע': ['be evil', 'be bad', 'do evil', 'be displeasing'],
    'היה': ['be', 'become', 'exist', 'happen', 'come to pass', 'occur'],
    'כלה': ['be complete', 'finish', 'come to an end', 'consume', 'determine', 'cease'],
    'נפל': ['fall', 'lie down', 'be cast down', 'fail', 'attack'],
    'שׁכב': ['lie down', 'sleep', 'rest', 'lie with'],
    'שכב': ['lie down', 'sleep', 'rest', 'lie with'],
    'חלל': ['begin', 'profane', 'defile', 'pollute', 'wound'],
    'מכר': ['sell', 'hand over'],
    'שׁתה': ['drink', 'feast', 'banquet'],
    'שתה': ['drink', 'feast', 'banquet'],
    'צוה': ['command', 'order', 'charge', 'appoint'],
    'ברך': ['bless', 'kneel', 'praise', 'greet'],
    'שׁקה': ['give to drink', 'water', 'irrigate'],
    'שקה': ['give to drink', 'water', 'irrigate'],
    'נכה': ['strike', 'smite', 'hit', 'kill', 'defeat'],
    'שׁאל': ['ask', 'inquire', 'request', 'borrow', 'demand'],
    'שאל': ['ask', 'inquire', 'request', 'borrow', 'demand'],
    'חטא': ['sin', 'miss', 'err', 'offend'],
    'כרת': ['cut', 'cut off', 'make (a covenant)', 'destroy'],
    'צאן': ['flock', 'sheep', 'goats'],
    'צעק': ['cry out', 'call', 'shout'],
    'שׁבע': ['swear', 'take an oath', 'adjure'],
    'שבע': ['swear', 'take an oath', 'adjure'],
    'נצל': ['deliver', 'rescue', 'save', 'strip'],
    'שׁחט': ['slaughter', 'kill', 'slay'],
    'שחט': ['slaughter', 'kill', 'slay'],
    'שׁוב': ['return', 'turn back', 'repent', 'restore'],
    'חנן': ['be gracious', 'show favor', 'pity', 'have mercy'],
    'רבה': ['be many', 'multiply', 'increase', 'be great'],
    'רבב': ['be many', 'multiply', 'increase'],
    'נגד': ['tell', 'declare', 'report', 'announce', 'make known'],
    'נגע': ['touch', 'reach', 'strike', 'arrive'],
    'עזב': ['leave', 'abandon', 'forsake', 'let go'],
    'שׂרף': ['burn', 'consume with fire'],
    'שרף': ['burn', 'consume with fire'],
    'חשׁב': ['think', 'plan', 'devise', 'reckon', 'account', 'consider', 'impute'],
    'חשב': ['think', 'plan', 'devise', 'reckon', 'account', 'consider', 'impute'],
    'כלא': ['restrain', 'shut up', 'withhold', 'confine'],
    'סור': ['turn aside', 'depart', 'remove', 'take away'],
    'נכר': ['recognize', 'acknowledge', 'be strange', 'disguise'],
    'רעה': ['pasture', 'tend', 'graze', 'shepherd', 'feed'],
    'שׁכם': ['rise early', 'start early', 'do early'],
    'שכם': ['rise early', 'start early', 'do early'],
    'נסע': ['set out', 'journey', 'depart', 'march', 'pull up'],
    'גור': ['sojourn', 'dwell as alien', 'be afraid'],
    'צדק': ['be righteous', 'be just', 'be in the right'],
    'נטה': ['stretch out', 'extend', 'spread', 'pitch (tent)', 'turn', 'incline'],
    'סבב': ['go around', 'surround', 'turn', 'encompass'],
    'חפץ': ['delight', 'desire', 'take pleasure'],
    'אסף': ['gather', 'collect', 'remove', 'take away'],
    'ספר': ['count', 'number', 'tell', 'recount', 'declare'],
    'הפך': ['turn', 'overturn', 'overthrow', 'change', 'transform'],
    'אור': ['be light', 'shine', 'give light', 'illuminate'],
    'רפא': ['heal', 'cure', 'restore'],
    'שׁאר': ['remain', 'be left over', 'survive'],
    'שאר': ['remain', 'be left over', 'survive'],
    'עמד': ['stand', 'stand still', 'stop', 'remain', 'endure'],
    'יכל': ['be able', 'prevail', 'endure', 'overcome'],
    'חרה': ['be hot', 'be angry', 'burn', 'be kindled'],
    'שׁוב': ['return', 'turn back', 'repent', 'restore'],
    'נטע': ['plant', 'establish', 'fix'],
    'חלם': ['dream', 'be healthy'],
    'כבד': ['be heavy', 'be honored', 'be rich', 'harden'],
    'פרה': ['be fruitful', 'bear fruit'],
    'פרד': ['separate', 'divide', 'scatter'],
    'משׁל': ['rule', 'have dominion', 'reign', 'govern'],
    'משל': ['rule', 'have dominion', 'reign', 'govern'],
    'נחם': ['comfort', 'console', 'repent', 'be sorry', 'have compassion'],
    'חדל': ['cease', 'stop', 'desist', 'forbear', 'refrain'],
    'שׁחת': ['destroy', 'corrupt', 'ruin', 'spoil'],
    'שחת': ['destroy', 'corrupt', 'ruin', 'spoil'],
    'גלה': ['uncover', 'reveal', 'disclose', 'depart', 'go into exile'],
    'עבר': ['pass over', 'cross', 'pass through', 'go beyond', 'transgress'],
    'יסף': ['add', 'do again', 'continue', 'increase'],
    'שׁבת': ['cease', 'rest', 'stop', 'keep sabbath'],
    'שבת': ['cease', 'rest', 'stop', 'keep sabbath'],
    'רום': ['be high', 'be exalted', 'rise', 'lift up'],
    'יצא': ['go out', 'come out', 'go forth', 'depart', 'proceed'],
    'שׁית': ['put', 'set', 'lay', 'place'],
    'שית': ['put', 'set', 'lay', 'place'],
    'נחל': ['inherit', 'possess', 'get', 'take as property'],
    'כון': ['be firm', 'establish', 'prepare', 'set up', 'be ready'],
    'שׁקר': ['deal falsely', 'deceive', 'lie'],
    'נגשׁ': ['approach', 'draw near', 'come near', 'bring near'],
    'נגש': ['approach', 'draw near', 'come near', 'bring near'],
    'אסר': ['bind', 'tie', 'imprison'],
    'חפר': ['dig', 'search', 'be ashamed'],
    'רכב': ['ride', 'mount'],
    'מלל': ['speak', 'say', 'utter'],
    'צמח': ['sprout', 'grow', 'spring up'],
    'בדל': ['separate', 'divide', 'distinguish', 'set apart'],
    'שׁפט': ['judge', 'govern', 'vindicate', 'decide'],
    'שפט': ['judge', 'govern', 'vindicate', 'decide'],
    'רדה': ['rule', 'have dominion', 'dominate', 'tread'],
    'רמשׂ': ['creep', 'move', 'swarm'],
    'רמש': ['creep', 'move', 'swarm'],
    'כבשׁ': ['subdue', 'bring into bondage', 'conquer'],
    'כבש': ['subdue', 'bring into bondage', 'conquer'],
    'רחף': ['hover', 'move', 'flutter', 'brood'],
    'יבשׁ': ['be dry', 'dry up', 'wither'],
    'יבש': ['be dry', 'dry up', 'wither'],
    'דשׁא': ['sprout', 'bring forth grass'],
    'דשא': ['sprout', 'bring forth grass'],
    'זרע': ['sow', 'scatter seed'],
    'נבט': ['look', 'regard'],
    'בטח': ['trust', 'be confident', 'feel safe'],
    'קוה': ['wait for', 'hope', 'expect', 'collect'],
    'שׁקע': ['sink', 'subside'],
    'רקע': ['spread out', 'stamp', 'beat out'],
    'חשׁך': ['be dark', 'grow dark', 'darken'],
    'חשך': ['be dark', 'grow dark', 'darken'],
    'נחשׁ': ['practice divination', 'divine', 'observe signs'],
    'נחש': ['practice divination', 'divine', 'observe signs'],
    'ערם': ['be shrewd', 'be crafty', 'be cunning'],
    'תפר': ['sew', 'sew together'],
    'חגר': ['gird', 'gird on', 'put on a belt'],
    'חבא': ['hide', 'conceal oneself'],
    'תאן': ['be a fig tree'],
    'שׁוע': ['cry for help'],
    'שוע': ['cry for help'],
    'כסה': ['cover', 'conceal', 'hide', 'clothe', 'overwhelm'],
    'לבשׁ': ['put on', 'wear', 'clothe', 'be clothed'],
    'לבש': ['put on', 'wear', 'clothe', 'be clothed'],
    'גרשׁ': ['drive out', 'expel', 'cast out', 'divorce'],
    'גרש': ['drive out', 'expel', 'cast out', 'divorce'],
    'שׁכן': ['dwell', 'settle', 'abide', 'inhabit', 'tabernacle'],
    'שכן': ['dwell', 'settle', 'abide', 'inhabit', 'tabernacle'],
    'הרג': ['kill', 'slay', 'murder'],
    'נוע': ['wander', 'shake', 'stagger', 'tremble'],
    'נוד': ['wander', 'flutter', 'show grief', 'bemoan'],
    'חנה': ['encamp', 'camp', 'pitch tent'],
    'צער': ['be small', 'be insignificant'],
    'עצם': ['be mighty', 'be numerous', 'be vast'],
    'עצב': ['hurt', 'grieve', 'pain', 'toil'],
    'שׁגה': ['go astray', 'err'],
    'נקם': ['avenge', 'take vengeance'],
    'כנע': ['be subdued', 'humble oneself'],
    'שׁנה': ['change', 'alter', 'repeat'],
    'שנה': ['change', 'alter', 'repeat'],
    'פגע': ['meet', 'encounter', 'reach', 'intercede', 'entreat'],
    'מחה': ['wipe', 'blot out', 'destroy'],
    'צוד': ['hunt', 'chase'],
    'טעם': ['taste', 'perceive'],
    'הרה': ['conceive', 'be pregnant'],
    'שׁפך': ['pour out', 'shed', 'spill'],
    'שפך': ['pour out', 'shed', 'spill'],
    'דרשׁ': ['seek', 'inquire', 'investigate', 'require'],
    'דרש': ['seek', 'inquire', 'investigate', 'require'],
    'מטר': ['rain', 'send rain'],
    'נוח': ['rest', 'settle down', 'be quiet'],
    'יטב': ['be good', 'do well', 'be pleasing', 'deal well'],
    'סתר': ['hide', 'conceal'],
    'פרץ': ['break through', 'burst out', 'spread', 'increase'],
    'נגף': ['strike', 'smite', 'stumble'],
    'חצה': ['divide', 'halve'],
    'אחז': ['seize', 'grasp', 'take hold', 'possess'],
    'חרב': ['be dry', 'be desolate', 'be waste', 'destroy'],
    'פרש': ['spread out', 'stretch out'],
    'פרשׂ': ['spread out', 'stretch out'],
    'רבץ': ['lie down', 'crouch', 'stretch out'],
    'שׁאף': ['gasp', 'pant', 'long for', 'trample'],
    'גער': ['rebuke', 'reprove'],
    'חלף': ['pass on', 'pass away', 'change', 'renew'],
    'עוף': ['fly', 'flutter'],
    'שׁרץ': ['swarm', 'teem'],
    'שרץ': ['swarm', 'teem'],
    'רדף': ['pursue', 'follow', 'chase', 'persecute'],
    'מנה': ['count', 'number', 'reckon', 'assign', 'appoint'],
    'חלק': ['divide', 'share', 'distribute', 'assign'],
    'פלט': ['escape', 'deliver'],
    'שׁבה': ['take captive', 'carry away'],
    'שבה': ['take captive', 'carry away'],
    'רוץ': ['run', 'rush'],
    'ענה': ['answer', 'respond', 'testify', 'afflict', 'humble', 'oppress'],
    'פלל': ['pray', 'intercede', 'judge'],
    'מהר': ['hasten', 'hurry', 'be quick'],
    'לוט': ['wrap', 'envelop'],
    'לוז': ['turn aside', 'depart'],
    'מוט': ['totter', 'shake', 'slip', 'fall'],
    'סכך': ['cover', 'screen', 'hedge'],
    'נצב': ['stand', 'take one\'s stand', 'be stationed', 'be set up'],
    'רגז': ['tremble', 'quake', 'be agitated', 'be excited'],
    'חמם': ['be warm', 'be hot'],
    'צמד': ['bind', 'join'],
    'מושׁ': ['feel', 'touch', 'grope'],
    'מוש': ['feel', 'touch', 'grope'],
    'משׁשׁ': ['feel', 'grope'],
    'משש': ['feel', 'grope'],
    'בכה': ['weep', 'cry', 'mourn'],
    'חבק': ['embrace', 'clasp', 'fold hands'],
    'שׁוה': ['be like', 'resemble', 'be equal', 'set', 'place'],
    'שוה': ['be like', 'resemble', 'be equal', 'set', 'place'],
    'קבר': ['bury', 'inter'],
    'קנה': ['buy', 'acquire', 'purchase', 'possess', 'create'],
    'פקד': ['visit', 'attend to', 'muster', 'appoint', 'number', 'punish'],
    'ספד': ['mourn', 'lament', 'wail'],
    'לחם': ['fight', 'make war', 'do battle'],
    'זנה': ['be a harlot', 'commit fornication', 'be unfaithful'],
    'שׁמח': ['rejoice', 'be glad', 'be joyful'],
    'שמח': ['rejoice', 'be glad', 'be joyful'],
    'נתץ': ['pull down', 'break down', 'tear down'],
    'אבה': ['be willing', 'consent', 'want'],
    'חתת': ['be shattered', 'be dismayed', 'be afraid'],
    'כעס': ['be angry', 'be vexed', 'provoke to anger'],
    'טמא': ['be unclean', 'defile'],
    'רחם': ['have compassion', 'show mercy', 'love'],
    'נבא': ['prophesy'],
    'גנב': ['steal', 'kidnap'],
    'בקשׁ': ['seek', 'search for', 'require', 'desire'],
    'בקש': ['seek', 'search for', 'require', 'desire'],
    'אבל': ['mourn', 'lament'],
    'שׁכח': ['forget', 'neglect'],
    'שכח': ['forget', 'neglect'],
    'שׁלם': ['be complete', 'be sound', 'make peace', 'repay', 'reward'],
    'שלם': ['be complete', 'be sound', 'make peace', 'repay', 'reward'],
    'צלח': ['prosper', 'succeed', 'rush upon'],
    'הרס': ['tear down', 'break through', 'overthrow'],
    'מלט': ['escape', 'deliver', 'save'],
    'חנה': ['encamp', 'camp'],
    'עוד': ['testify', 'bear witness', 'warn'],
    'רחק': ['be far', 'remove', 'be distant'],
    'קרב': ['come near', 'approach', 'draw near', 'bring near', 'offer'],
    'אלה': ['swear', 'curse'],
    'חלה': ['be sick', 'be weak', 'become sick', 'entreat'],
    'מאן': ['refuse'],
    'מאס': ['reject', 'despise', 'refuse'],
    'בער': ['burn', 'consume', 'be brutish'],
    'נסה': ['test', 'try', 'prove', 'tempt'],
    'חלץ': ['draw off', 'withdraw', 'equip', 'deliver'],
    'שׁבר': ['break', 'shatter', 'buy grain'],
    'שבר': ['break', 'shatter', 'buy grain'],
    'עתר': ['pray', 'entreat', 'supplicate'],
    'ארר': ['curse'],
    'מלך': ['reign', 'be king', 'rule'],
    'יסד': ['found', 'establish', 'lay a foundation'],
    'רעב': ['be hungry', 'hunger'],
    'שׁקט': ['be quiet', 'be at rest', 'be undisturbed'],
    'שקט': ['be quiet', 'be at rest', 'be undisturbed'],
    'חרד': ['tremble', 'be terrified', 'be anxious'],
    'אוץ': ['urge', 'press'],
    'שׁקף': ['look down', 'overlook'],
    'שקף': ['look down', 'overlook'],
    'טבח': ['slaughter', 'butcher', 'kill'],
    'רכשׁ': ['acquire', 'get'],
    'רכש': ['acquire', 'get'],
    'עור': ['awake', 'rouse', 'stir up'],
    'שׁחק': ['laugh', 'play', 'sport', 'jest'],
    'שחק': ['laugh', 'play', 'sport', 'jest'],
    'צחק': ['laugh', 'play', 'jest', 'sport'],
    'לין': ['lodge', 'spend the night', 'stay overnight'],
    'לון': ['lodge', 'spend the night', 'murmur', 'grumble'],
    'מול': ['circumcise'],
    'בלל': ['mix', 'confuse', 'confound', 'mingle'],
    'פוץ': ['scatter', 'disperse', 'be spread'],
    'נטל': ['lift', 'lay upon'],
    'רגם': ['stone'],
    'שׁפה': ['set', 'lay upon'],
    'שפה': ['set', 'lay upon'],
    'נסך': ['pour out', 'cast (metal)'],
    'אפה': ['bake'],
    'נכל': ['act treacherously', 'deal craftily'],
    'עקב': ['follow at the heel', 'supplant', 'overreach'],
    'חבל': ['bind', 'pledge', 'act corruptly', 'destroy'],
    'צמת': ['annihilate', 'destroy', 'silence'],
    'כהה': ['grow dim', 'be faint'],
    'תמם': ['be complete', 'be finished', 'be consumed'],
    'רמה': ['deceive', 'beguile', 'deal treacherously'],
    'נכל': ['deceive', 'be crafty'],
    'חמס': ['treat violently', 'wrong'],
    'עטף': ['be feeble', 'languish', 'cover', 'wrap'],
    'רגל': ['spy out', 'slander'],

    # ── Common nouns/substantives ──
    'אדם': ['man', 'mankind', 'human', 'person', 'people'],
    'אישׁ': ['man', 'husband', 'person', 'each', 'everyone'],
    'איש': ['man', 'husband', 'person', 'each', 'everyone'],
    'אשׁה': ['woman', 'wife', 'female'],
    'אשה': ['woman', 'wife', 'female'],
    'בן': ['son', 'child', 'descendant', 'member of a group'],
    'בת': ['daughter', 'girl', 'granddaughter'],
    'אב': ['father', 'ancestor', 'forefather', 'head of household'],
    'אם': ['mother'],
    'אח': ['brother', 'relative', 'kinsman', 'fellow'],
    'אחות': ['sister'],
    'בית': ['house', 'home', 'household', 'family', 'temple', 'dwelling'],
    'עיר': ['city', 'town'],
    'ארץ': ['earth', 'land', 'ground', 'country', 'territory'],
    'שׁמים': ['heaven', 'sky', 'heavens'],
    'שמים': ['heaven', 'sky', 'heavens'],
    'מים': ['water', 'waters'],
    'יום': ['day', 'time', 'today'],
    'לילה': ['night', 'by night'],
    'שׁנה': ['year'],
    'שנה': ['year'],
    'דרך': ['way', 'road', 'path', 'journey', 'manner'],
    # 'דבר' already defined above with both verb and noun senses
    'שׁם': ['name', 'reputation', 'fame', 'memorial'],
    'שם': ['name', 'reputation', 'fame', 'memorial'],
    'עין': ['eye', 'spring', 'fountain', 'appearance'],
    'יד': ['hand', 'power', 'strength', 'side'],
    'פנים': ['face', 'presence', 'before', 'surface', 'front'],
    'לב': ['heart', 'mind', 'inner person', 'will'],
    'לבב': ['heart', 'mind', 'inner person'],
    'נפשׁ': ['soul', 'life', 'person', 'self', 'desire', 'appetite'],
    'נפש': ['soul', 'life', 'person', 'self', 'desire', 'appetite'],
    'רוח': ['spirit', 'wind', 'breath', 'mind'],
    'כל': ['all', 'every', 'whole', 'entire', 'any'],
    'עם': ['people', 'nation', 'folk', 'with'],
    'גוי': ['nation', 'people', 'gentile'],
    'מלך': ['king', 'ruler'],
    'אלהים': ['God', 'gods', 'divine beings', 'judges'],
    'אדון': ['lord', 'master', 'owner'],
    'כהן': ['priest'],
    'נביא': ['prophet'],
    'עבד': ['servant', 'slave', 'worshiper'],
    'מלאך': ['messenger', 'angel'],
    'רע': ['evil', 'bad', 'wicked', 'harmful', 'friend', 'neighbor', 'companion'],
    'טוב': ['good', 'pleasant', 'agreeable', 'beautiful'],
    'גדול': ['great', 'large', 'big', 'important', 'elder'],
    'קטן': ['small', 'little', 'young', 'insignificant'],
    'רב': ['much', 'many', 'great', 'abundant', 'numerous'],
    'חי': ['living', 'alive', 'life'],
    'מת': ['dead', 'death'],
    'חיה': ['living thing', 'animal', 'beast', 'life'],
    'בהמה': ['beast', 'cattle', 'animal', 'livestock'],
    'צאן': ['flock', 'sheep', 'goats', 'sheep and goats'],
    'בקר': ['cattle', 'herd', 'ox'],
    'חמור': ['donkey', 'ass'],
    'גמל': ['camel'],
    'סוס': ['horse'],
    'כסף': ['silver', 'money'],
    'זהב': ['gold'],
    'אבן': ['stone', 'rock'],
    'עץ': ['tree', 'wood', 'timber'],
    'שׂדה': ['field', 'open country', 'land'],
    'שדה': ['field', 'open country', 'land'],
    'הר': ['mountain', 'hill', 'hill country'],
    'נהר': ['river', 'stream'],
    'באר': ['well', 'pit'],
    'מדבר': ['wilderness', 'desert', 'pasture'],
    'גן': ['garden', 'enclosure'],
    'פרי': ['fruit', 'offspring', 'result'],
    'לחם': ['bread', 'food', 'grain'],
    'יין': ['wine'],
    'שׁמן': ['oil', 'fat', 'fatness'],
    'שמן': ['oil', 'fat', 'fatness'],
    'מזבח': ['altar'],
    'ברית': ['covenant', 'alliance', 'pledge', 'agreement', 'treaty'],
    'משׁפט': ['judgment', 'justice', 'ordinance', 'custom', 'manner'],
    'משפט': ['judgment', 'justice', 'ordinance', 'custom', 'manner'],
    'תורה': ['law', 'instruction', 'teaching', 'direction'],
    'חרב': ['sword', 'knife'],
    'מטה': ['staff', 'rod', 'tribe', 'branch'],
    'כתנת': ['tunic', 'coat', 'garment'],
    'בגד': ['garment', 'clothing', 'treachery'],
    'אהל': ['tent'],
    'שׁער': ['gate', 'entrance', 'opening'],
    'שער': ['gate', 'entrance', 'opening'],
    'חומה': ['wall', 'fortification'],
    'ראשׁ': ['head', 'top', 'chief', 'beginning', 'first'],
    'ראש': ['head', 'top', 'chief', 'beginning', 'first'],
    'ראשׁית': ['beginning', 'first', 'chief', 'firstfruits'],
    'מקום': ['place', 'standing place'],
    'אות': ['sign', 'mark', 'token', 'omen', 'miracle'],
    'חטאת': ['sin', 'sin offering', 'punishment'],
    'צדקה': ['righteousness', 'justice'],
    'חסד': ['lovingkindness', 'steadfast love', 'mercy', 'loyalty', 'faithfulness'],
    'אמת': ['truth', 'faithfulness', 'reliability'],
    'שׁלום': ['peace', 'welfare', 'well-being', 'health', 'completeness'],
    'שלום': ['peace', 'welfare', 'well-being', 'health', 'completeness'],
    'כח': ['strength', 'power', 'might', 'force', 'ability'],
    'חכמה': ['wisdom', 'skill'],
    'תהום': ['deep', 'abyss', 'ocean depths'],
    'רקיע': ['expanse', 'firmament', 'sky', 'dome'],
    'מאור': ['light', 'luminary', 'lamp'],
    'כוכב': ['star'],
    'עשׂב': ['herb', 'herbage', 'plant', 'vegetation'],
    'עשב': ['herb', 'herbage', 'plant', 'vegetation'],
    'דשׁא': ['grass', 'vegetation', 'green herbage'],
    'דשא': ['grass', 'vegetation', 'green herbage'],
    'זרע': ['seed', 'offspring', 'descendants', 'sowing'],
    'תנין': ['sea monster', 'serpent', 'dragon'],
    'עוף': ['bird', 'fowl', 'flying creature'],
    'דג': ['fish'],
    'דגה': ['fish'],
    'רמשׂ': ['creeping thing', 'moving creature'],
    'רמש': ['creeping thing', 'moving creature'],
    'נחשׁ': ['serpent', 'snake'],
    'נחש': ['serpent', 'snake'],
    'צלם': ['image', 'likeness', 'form'],
    'דמות': ['likeness', 'form', 'pattern', 'similitude'],
    'עפר': ['dust', 'dry earth', 'ashes'],
    'נשׁמה': ['breath', 'spirit', 'living being'],
    'נשמה': ['breath', 'spirit', 'living being'],
    'צלע': ['rib', 'side'],
    'בשׂר': ['flesh', 'meat', 'body', 'mankind'],
    'בשר': ['flesh', 'meat', 'body', 'mankind'],
    'עצם': ['bone', 'substance', 'self'],
    'עור': ['skin', 'hide', 'leather'],
    'דם': ['blood', 'bloodshed', 'guilt of bloodshed'],
    'קשׁת': ['bow', 'rainbow'],
    'קשת': ['bow', 'rainbow'],
    'ענן': ['cloud'],
    'מבול': ['flood', 'deluge'],
    'תבה': ['ark', 'chest'],
    'גפר': ['gopher wood'],
    'כנף': ['wing', 'extremity', 'edge', 'border'],
    'מזרח': ['east', 'sunrise'],
    'מערב': ['west', 'sunset'],
    'צפון': ['north'],
    'נגב': ['south', 'Negev', 'dry country'],
    'ימין': ['right hand', 'right side', 'south'],
    'שׂמאל': ['left', 'left hand', 'north'],
    'שמאל': ['left', 'left hand', 'north'],
    'מחנה': ['camp', 'army', 'company'],
    'חיל': ['strength', 'wealth', 'army', 'valor', 'virtue'],
    'מנחה': ['offering', 'gift', 'tribute', 'present'],
    'בכור': ['firstborn'],
    'בכירה': ['firstborn (woman)'],
    'צעירה': ['younger', 'small'],
    'אדמה': ['ground', 'land', 'soil', 'earth'],
    'תולדות': ['generations', 'descendants', 'history', 'account'],
    'משׁפחה': ['clan', 'family', 'kind'],
    'משפחה': ['clan', 'family', 'kind'],
    'לשׁון': ['tongue', 'language'],
    'לשון': ['tongue', 'language'],
    'אחזה': ['possession', 'property', 'land property'],
    'מקנה': ['livestock', 'cattle', 'property', 'possession'],
    'רכושׁ': ['property', 'goods', 'possessions'],
    'רכוש': ['property', 'goods', 'possessions'],
    'מגדל': ['tower'],
    'אש': ['fire'],
    'אשׁ': ['fire'],
    'גפרית': ['brimstone', 'sulfur'],
    'מלח': ['salt'],
    'מערה': ['cave'],
    'עקד': ['bind'],
    'איל': ['ram'],
    'סבך': ['thicket'],

    # ── Particles, prepositions, conjunctions ──
    'את': ['(object marker)', 'with', 'together with'],
    'אל': ['to', 'toward', 'into', 'unto'],
    'על': ['on', 'upon', 'over', 'above', 'against', 'concerning', 'about', 'beside'],
    'מן': ['from', 'out of', 'because of', 'more than', 'some of'],
    'ב': ['in', 'at', 'by', 'with', 'among', 'when'],
    'ל': ['to', 'for', 'belonging to', 'in regard to'],
    'כ': ['like', 'as', 'according to', 'about', 'when'],
    'עד': ['until', 'as far as', 'while', 'during', 'forever'],
    'אשׁר': ['who', 'which', 'that', 'because', 'where', 'when'],
    'אשר': ['who', 'which', 'that', 'because', 'where', 'when'],
    'כי': ['for', 'because', 'that', 'when', 'if', 'but', 'indeed', 'surely'],
    'לא': ['not', 'no'],
    'אין': ['there is not', 'nothing', 'without'],
    'גם': ['also', 'even', 'moreover', 'indeed'],
    'הנה': ['behold', 'look', 'here', 'now'],
    'כן': ['so', 'thus', 'right', 'honest', 'true'],
    'עתה': ['now', 'at this time'],
    'פן': ['lest', 'otherwise', 'perhaps'],
    'אם': ['if', 'whether', 'or'],
    'הלא': ['is it not?', 'indeed'],
    'למה': ['why?', 'for what reason?'],
    'מה': ['what?', 'how!', 'whatever'],
    'מי': ['who?', 'whoever'],
    'איפה': ['where?'],
    'אן': ['where?', 'whither?'],
    'אנה': ['where?', 'whither?'],
    'ו': ['and', 'but', 'then', 'or', 'so'],
    'אז': ['then', 'at that time'],
    'טרם': ['before', 'not yet'],
    'עוד': ['still', 'yet', 'again', 'more', 'besides'],
    'אף': ['also', 'indeed', 'even', 'moreover', 'anger', 'nose', 'nostril', 'face'],
    'רק': ['only', 'surely', 'but'],
    'אך': ['only', 'surely', 'but', 'however', 'indeed'],
    'אולי': ['perhaps', 'maybe'],
    'בין': ['between', 'among'],
    'תחת': ['under', 'beneath', 'instead of', 'in place of'],
    'אחר': ['after', 'behind', 'following', 'other', 'another'],
    'לפני': ['before', 'in front of', 'in the presence of'],
    'אצל': ['beside', 'near'],
    'נגד': ['before', 'in front of', 'opposite', 'in the sight of'],
    'סביב': ['around', 'about', 'surrounding'],
    'בעד': ['behind', 'through', 'for', 'on behalf of'],

    # ── Adjectives ──
    'חדשׁ': ['new', 'fresh'],
    'חדש': ['new', 'fresh'],
    'ישׁר': ['straight', 'right', 'upright', 'just'],
    'ישר': ['straight', 'right', 'upright', 'just'],
    'רחב': ['wide', 'broad', 'spacious'],
    'עמק': ['deep', 'valley'],
    'חכם': ['wise', 'skillful'],
    'נער': ['boy', 'youth', 'lad', 'young man', 'servant'],
    'נערה': ['girl', 'maiden', 'young woman', 'female servant'],
    'זקן': ['old', 'elder', 'aged'],
    'צדיק': ['righteous', 'just', 'innocent'],
    'רשׁע': ['wicked', 'guilty', 'criminal'],
    'רשע': ['wicked', 'guilty', 'criminal'],
    'תמים': ['complete', 'blameless', 'whole', 'perfect'],
    'ערום': ['naked', 'bare'],

    # ── Numbers ──
    'אחד': ['one', 'a certain', 'first', 'each', 'single', 'alone'],
    'שׁנים': ['two', 'both', 'second', 'twice', 'double'],
    'שנים': ['two', 'both', 'second', 'twice', 'double'],
    'שׁני': ['second', 'another', 'other', 'again'],
    'שני': ['second', 'another', 'other', 'again'],
    'שׁלשׁ': ['three', 'third'],
    'שלש': ['three', 'third'],
    'שׁלשׁה': ['three'],
    'שלשה': ['three'],
    'ארבע': ['four', 'fourth'],
    'ארבעה': ['four'],
    'חמשׁ': ['five', 'fifth'],
    'חמש': ['five', 'fifth'],
    'חמשׁה': ['five'],
    'חמשה': ['five'],
    'שׁשׁ': ['six', 'sixth'],
    'שש': ['six', 'sixth'],
    'שׁשׁה': ['six'],
    'ששה': ['six'],
    'שׁבע': ['seven', 'seventh'],
    'שבע': ['seven', 'seventh'],
    'שׁבעה': ['seven'],
    'שבעה': ['seven'],
    'שׁמנה': ['eight', 'eighth'],
    'שמנה': ['eight', 'eighth'],
    'תשׁע': ['nine', 'ninth'],
    'תשע': ['nine', 'ninth'],
    'עשׂר': ['ten', 'tenth'],
    'עשר': ['ten', 'tenth'],
    'עשׂרה': ['ten'],
    'עשרה': ['ten'],
    'עשׂרים': ['twenty'],
    'עשרים': ['twenty'],
    'שׁלשׁים': ['thirty'],
    'שלשים': ['thirty'],
    'ארבעים': ['forty'],
    'חמשׁים': ['fifty'],
    'חמשים': ['fifty'],
    'שׁשׁים': ['sixty'],
    'ששים': ['sixty'],
    'שׁבעים': ['seventy'],
    'שבעים': ['seventy'],
    'מאה': ['hundred'],
    'אלף': ['thousand'],
    'רבבה': ['ten thousand', 'myriad'],

    # ── More verbs found in Genesis ──
    'שׁלך': ['throw', 'cast', 'fling', 'hurl'],
    'שלך': ['throw', 'cast', 'fling', 'hurl'],
    'חמד': ['desire', 'covet', 'delight in'],
    'נשׁק': ['kiss', 'arm'],
    'נשק': ['kiss', 'arm'],
    'שׁפל': ['be low', 'be humbled', 'humble'],
    'שפל': ['be low', 'be humbled', 'humble'],
    'רחץ': ['wash', 'bathe'],
    'שׁתל': ['plant', 'transplant'],
    'שתל': ['plant', 'transplant'],
    'פרע': ['let go', 'let alone', 'let loose', 'neglect'],
    'סכל': ['be foolish'],
    'נשׁא': ['deceive', 'beguile'],
    'בלע': ['swallow', 'destroy', 'engulf'],
    'כסל': ['be foolish'],
    'חמל': ['spare', 'have pity', 'compassion'],
    'נאף': ['commit adultery'],
    'שׂטם': ['bear a grudge', 'persecute', 'hate'],
    'שטם': ['bear a grudge', 'persecute', 'hate'],
    'עשׁק': ['oppress', 'wrong', 'extort', 'defraud'],
    'עשק': ['oppress', 'wrong', 'extort', 'defraud'],
    'גדד': ['cut oneself', 'gash'],
    'מדד': ['measure'],
    'צעד': ['step', 'march'],
    'שׂכר': ['hire'],
    'שכר': ['hire'],
    'שׂכל': ['be prudent', 'have insight', 'prosper', 'understand'],
    'שכל': ['be prudent', 'have insight', 'prosper', 'understand'],
    'שׁכל': ['be bereaved of children', 'miscarry'],
    'תעה': ['err', 'wander', 'go astray', 'stagger'],
    'כלם': ['be humiliated', 'be ashamed', 'be disgraced'],
    'שׁען': ['lean', 'support oneself'],
    'פלא': ['be wonderful', 'be extraordinary', 'be too difficult'],
    'עקר': ['uproot', 'hamstring'],
    'שׁחה': ['bow down', 'prostrate oneself', 'worship'],
    'שחה': ['bow down', 'prostrate oneself', 'worship'],
    'לוה': ['join', 'accompany', 'borrow', 'lend'],
    'הלל': ['praise', 'boast', 'be foolish', 'shine'],
    'חלם': ['dream'],
    'חלום': ['dream', 'vision'],
    'מצרי': ['Egyptian'],
    'אנחנו': ['we', 'us'],
    'נחנו': ['we', 'us'],
    'שׁקת': ['watering trough'],
    'שקת': ['watering trough'],
    'מתנה': ['gift', 'present'],
    'תואמם': ['twins'],
    'תאומים': ['twins'],
    'בכות': ['weeping'],
    'אלמה': ['sheaf', 'bundle'],
    'יפה': ['beautiful', 'fair', 'handsome'],
    'כוס': ['cup', 'goblet'],
    'בטנה': ['pistachio', 'pistachio nut'],
    'נעם': ['be pleasant', 'be lovely', 'be delightful'],
    'סכות': ['booths', 'shelters'],
    'חרי': ['cake'],
    'רקיע': ['expanse', 'firmament', 'sky', 'dome'],
    'מאור': ['light', 'luminary', 'lamp'],
    'תנין': ['sea monster', 'serpent', 'dragon', 'great creature'],
    'כרוב': ['cherub', 'angelic being'],
    'עשׂב': ['herb', 'herbage', 'plant', 'vegetation', 'grass'],
    'עשב': ['herb', 'herbage', 'plant', 'vegetation', 'grass'],
    'ירק': ['green', 'greenery', 'vegetation', 'herbs'],
    'קול': ['voice', 'sound', 'noise', 'thunder'],
    'יבל': ['bring', 'carry', 'lead'],
    'פרע': ['let loose', 'let go', 'neglect', 'avenge'],
    'שׁגל': ['violate', 'ravish'],
    'שגל': ['violate', 'ravish'],
    'נאם': ['utterance', 'oracle', 'declaration'],
    'מגן': ['shield', 'protector', 'deliver'],
    'שׂכר': ['wages', 'reward', 'hire'],
    'שכר': ['wages', 'reward', 'hire'],
    'ערב': ['evening', 'sunset'],
    'בקר': ['morning', 'daybreak'],
    'חשׁך': ['darkness', 'obscurity'],
    'חשך': ['darkness', 'obscurity'],
}

# ─── Garbage detection patterns ──────────────────────────────────────────

def has_hebrew(s):
    return bool(re.search(r'[\u0590-\u05FF]', s))

def has_syriac(s):
    return bool(re.search(r'[\u0700-\u074F]', s))

def has_non_latin_script(s):
    """Check for any non-Latin scripts (Hebrew, Syriac, Arabic, etc.)"""
    return bool(re.search(r'[\u0590-\u05FF\u0600-\u06FF\u0700-\u074F\u0710-\u072F]', s))

def is_bdb_artifact(s):
    """BDB dictionary formatting artifacts"""
    patterns = [
        r'^(I+|II+)\.',           # Roman numeral references like "II. מקוה"
        r'esp\.\s',               # "esp. Raḳiʿa"
        r'opp\.\s',               # "opp. day"
        r'fig\.\)',               # "(fig.)"
        r'^\(.*\)$',             # Entire entry is parenthetical
        r'Pl\.\s',               # "Pl. forms"
        r'^cstr\.',              # construct form references
        r'only cstr\.',          # "only cstr."
        r'sf\.\s',               # suffix references
        r'^in ',                  # "in deriv" etc
        r'mostly in',            # "mostly in deriv"
        r'in the time of',       # biographical references
        r'Tam\.\s',              # Talmudic references
        r'Gen\. R\.',            # Genesis Rabbah references
        r'Yalk\.',               # Yalkut references
        r'^v\.\s',               # verse references
        r'^cf\.\s',              # cross-references
        r'^\+\s',                # BDB additions
        r'^=\s',                 # BDB equivalences
        r'deriv\.',              # derivatives
    ]
    for p in patterns:
        if re.search(p, s, re.IGNORECASE):
            return True
    return False

def is_strongs_format_artifact(s):
    """Strong's concordance formatting artifacts"""
    patterns = [
        r'^\(-',                 # "(-er" type fragments
        r'\(-\w+\)',             # "(-ation)" type
        r'^be \(',               # "be (make)" pattern
        r'^\w+\(-',             # "word(-fragment"
        r'chronicals',          # misspelling from Strong's
        r'continually\(-ance\)', # Strong's format
        r'^a particle',          # "a particle of the objective case"
        r'^as cstr\.',          # construct form note
    ]
    for p in patterns:
        if re.search(p, s, re.IGNORECASE):
            return True
    return False

def is_unrelated_proper_noun(s, is_proper_noun_word):
    """Proper nouns appearing in meanings of non-proper-noun words"""
    if is_proper_noun_word:
        return False
    # Common proper noun patterns from wrong Strong's matches
    proper_patterns = [
        r'^[A-Z][a-z]+ite$',    # "Shimathite", "Gadite"
        r'^[A-Z][a-z]+im$',     # "Cherethims"
        r'^[A-Z][a-z]+ael$',    # "Ishmael"
        r'^[A-Z][a-z]+ijah$',   # "Achijah"
        r'^[A-Z][a-z]+mah$',    # "Aholibamah"
        r'= "[^"]+"\s*$',       # 'Joseph = "Jehovah has added"'
    ]
    # Known proper noun garbage values
    proper_nouns = {
        'Immer', 'Jada', 'Jaasau', 'Likchi', 'Abdi', 'Ithai', 'Attai',
        'Shimathite', 'Haroeh', 'Roeh', 'Hashem', 'Hali', 'Jered',
        'Achijah', 'Achio', 'Ahio', 'Shaul', 'Cherez', 'Chedorlaomer',
        'Ishmael', 'Aholibamah', 'Hadoram', 'Akbor', 'Jehu',
        'Ashvath', 'Canan', 'Rabbath', 'Chorite', 'Chori', 'Choronajim',
        'Jachath', 'Miriam', 'Jehudah', 'Cherethims', 'Sem',
        'Ittai', 'Tubal', 'Ruth',
    }
    if s in proper_nouns:
        return True
    for p in proper_patterns:
        if re.search(p, s):
            return True
    return False

def is_garbage_meaning(meaning, is_proper_noun_word=False, word_root=''):
    """Check if a single meaning entry is garbage"""
    if has_non_latin_script(meaning):
        return True
    if is_bdb_artifact(meaning):
        return True
    if is_strongs_format_artifact(meaning):
        return True
    if is_unrelated_proper_noun(meaning, is_proper_noun_word):
        return True
    # Very short meaningless entries
    if len(meaning) <= 1 and meaning not in ('a',):
        return True

    # Known garbage entries from את Strong's that leak into compound words
    AET_GARBAGE = {
        'ploughshare', 'coulter', 'near (of place)', 'Abi',
        'a particle of the objective case',
    }
    if meaning in AET_GARBAGE:
        return True

    # Common leaked garbage from wrong Strong's cross-contamination
    COMMON_GARBAGE = {
        'coupled together',     # From wrong root
        'indef pron',           # BDB notation
        'nothing (subst)',      # BDB notation
        'if only!',             # Wrong root
        'Spanish broom',        # From wrong root for אמר
        'be disobedient',       # Wrong root for אמר
        'draught',              # Wrong root
        'conceit',              # Wrong root for אל
        'bruit',                # Wrong root
        'ease self',            # Wrong root
        'branding',             # Wrong root for כי
        'brand',                # Wrong root for כי
        'moth',                 # Wrong root for עשה
        'vapour',               # Wrong root for היה
        'calamity',             # Wrong root for יהוה
        'as cstr.:—',           # BDB formatting
        'dragon',               # Wrong root for נתן (from תנין)
        'monster',              # Wrong root for נתן
        'ig(-norant)',          # Formatting artifact
        'be hot',               # Common wrong root leak
        'gallows',              # Wrong root for על
        'hades',                # Wrong root for שאול
        'left-hand side',       # Wrong root leak
        'ram (skin dyed red',   # Truncated/wrong
        'Garden of Eden',       # Wrong root leak
        'Tetragrammaton',       # BDB reference
        'pillar',               # Wrong root leak for יהוה
        'mostly in deriv',      # BDB formatting
    }
    if meaning in COMMON_GARBAGE:
        return True

    # Parenthetical fragments
    if re.match(r'^\(.+$', meaning) and meaning.count('(') > meaning.count(')'):
        return True
    # Entries that are just "and" for non-conjunction words
    # (will be handled contextually)

    return False


def strip_niqqud(s):
    """Remove Hebrew vowel points / cantillation marks"""
    return re.sub(r'[\u0591-\u05BD\u05BF-\u05C7]', '', s)


def build_etcbc_lookup(etcbc_data):
    """Build a mapping from (chapter:verse, consonantal Hebrew) -> ETCBC lexeme info"""
    lookup = {}
    lex_to_glosses = defaultdict(set)

    for vref, words in etcbc_data.items():
        for w in words:
            lex = w.get('lex', '')
            gloss = w.get('gloss', '')
            pos = w.get('pos', '')
            heb = w.get('heb', '')
            cons = w.get('cons', '')
            if lex and gloss:
                lex_to_glosses[lex].add(gloss)
            key = (vref, strip_niqqud(heb))
            if key not in lookup:
                lookup[key] = []
            lookup[key].append({
                'lex': lex,
                'gloss': gloss,
                'pos': pos,
                'cons': cons,
            })

    return lookup, lex_to_glosses


def get_etcbc_match(word_heb, chapter, verse, etcbc_lookup):
    """Try to match a genesis_v3 word to its ETCBC lexeme"""
    vref = f"{chapter}:{verse}"
    stripped = strip_niqqud(word_heb)

    # Remove leading ו (vav conjunctive), ה (article), ב/כ/ל/מ (prepositions)
    # from the surface form to try matching
    candidates = etcbc_lookup.get((vref, stripped), [])
    if candidates:
        return candidates

    # Try stripping leading characters
    for prefix_len in range(1, min(4, len(stripped))):
        sub = stripped[prefix_len:]
        candidates = etcbc_lookup.get((vref, sub), [])
        if candidates:
            return candidates

    return []


def build_merged_root_meanings():
    """Build a merged version of ROOT_MEANINGS that handles duplicate keys.
    Python dict only keeps the last value for duplicate keys, so we need
    to explicitly merge entries defined in different sections (verb vs noun)."""
    merged = {}
    # Manually merge polysemous roots that appear as both verb and noun
    POLYSEMOUS = {
        'דבר': ['speak', 'say', 'talk', 'tell', 'declare', 'word', 'thing', 'matter', 'affair'],
        'עבד': ['serve', 'work', 'till', 'labor', 'worship', 'servant', 'slave'],
        'מלך': ['reign', 'be king', 'rule', 'king', 'ruler'],
        'שׁנה': ['change', 'alter', 'repeat', 'year'],
        'שנה': ['change', 'alter', 'repeat', 'year'],
        'טוב': ['be good', 'be pleasing', 'be well', 'good', 'pleasant', 'agreeable', 'beautiful'],
        'קטן': ['be small', 'be insignificant', 'small', 'little', 'young'],
        'חיה': ['live', 'be alive', 'revive', 'living thing', 'animal', 'beast', 'life'],
        'צאן': ['flock', 'sheep', 'goats', 'sheep and goats'],
        'לחם': ['fight', 'make war', 'bread', 'food', 'grain'],
        'חרב': ['be dry', 'be desolate', 'destroy', 'sword', 'knife'],
        'עצם': ['be mighty', 'be numerous', 'bone', 'substance', 'self'],
        'עור': ['awake', 'rouse', 'stir up', 'skin', 'hide', 'leather'],
        'אם': ['if', 'whether', 'or', 'mother'],
        'עוד': ['testify', 'warn', 'still', 'yet', 'again', 'more', 'besides'],
        'נגד': ['tell', 'declare', 'report', 'before', 'in front of', 'opposite'],
        'שׁבע': ['swear', 'take an oath', 'seven', 'seventh'],
        'שבע': ['swear', 'take an oath', 'seven', 'seventh'],
        'חלם': ['dream'],
        'חשׁך': ['be dark', 'grow dark', 'darkness', 'obscurity'],
        'חשך': ['be dark', 'grow dark', 'darkness', 'obscurity'],
        'בקר': ['examine', 'cattle', 'herd', 'ox', 'morning', 'daybreak'],
        'שׂכר': ['hire', 'wages', 'reward'],
        'שכר': ['hire', 'wages', 'reward'],
        'דשׁא': ['sprout', 'bring forth grass', 'grass', 'vegetation', 'green herbage'],
        'דשא': ['sprout', 'bring forth grass', 'grass', 'vegetation', 'green herbage'],
        'זרע': ['sow', 'scatter seed', 'seed', 'offspring', 'descendants'],
        'עוף': ['fly', 'flutter', 'bird', 'fowl', 'flying creature'],
        'רמשׂ': ['creep', 'move', 'swarm', 'creeping thing', 'moving creature'],
        'רמש': ['creep', 'move', 'swarm', 'creeping thing', 'moving creature'],
        'נחשׁ': ['practice divination', 'divine', 'serpent', 'snake'],
        'נחש': ['practice divination', 'divine', 'serpent', 'snake'],
        'עשׂב': ['herb', 'herbage', 'plant', 'vegetation', 'grass'],
        'עשב': ['herb', 'herbage', 'plant', 'vegetation', 'grass'],
        'פרע': ['let loose', 'let go', 'neglect', 'avenge'],
        'חנה': ['encamp', 'camp', 'pitch tent'],
        'נכל': ['act treacherously', 'deal craftily', 'deceive', 'be crafty'],
        'שׁם': ['name', 'reputation', 'fame', 'there', 'thence'],
        'שם': ['name', 'reputation', 'fame', 'there', 'thence'],
        'פנים': ['face', 'presence', 'before', 'surface', 'front'],
        'אלה': ['these', 'those', 'such', 'swear', 'curse', 'big tree'],
        'יהוה': ['YHWH', 'the LORD', 'the Eternal'],
        'אדני': ['Lord', 'my lord', 'master'],
        'מאכל': ['food', 'fruit', 'meat'],
    }
    merged.update(ROOT_MEANINGS)
    merged.update(POLYSEMOUS)
    return merged


MERGED_ROOT_MEANINGS = None  # Will be initialized in main()


def get_correct_meanings(lex, pos, lex_to_glosses):
    """Get correct meanings for a lexeme from our curated dictionary or ETCBC"""
    global MERGED_ROOT_MEANINGS

    # Try exact match
    if lex in MERGED_ROOT_MEANINGS:
        return MERGED_ROOT_MEANINGS[lex]

    # Try without shin/sin distinction
    normalized = lex.replace('שׂ', 'שׁ').replace('שׂ', 'ש')
    if normalized in MERGED_ROOT_MEANINGS:
        return MERGED_ROOT_MEANINGS[normalized]

    normalized2 = lex.replace('שׁ', 'ש')
    if normalized2 in MERGED_ROOT_MEANINGS:
        return MERGED_ROOT_MEANINGS[normalized2]

    # Try stripping final letters for some forms
    for variant in [lex, lex.rstrip('ה'), lex.rstrip('ת'), lex + 'ה']:
        if variant in MERGED_ROOT_MEANINGS:
            return MERGED_ROOT_MEANINGS[variant]

    return None


def main():
    global MERGED_ROOT_MEANINGS
    MERGED_ROOT_MEANINGS = build_merged_root_meanings()

    # Load data
    with open('genesis_v3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open('references/etcbc_genesis_by_verse.json', 'r', encoding='utf-8') as f:
        etcbc_data = json.load(f)

    etcbc_lookup, lex_to_glosses = build_etcbc_lookup(etcbc_data)

    # Stats
    total_words = 0
    words_with_meanings = 0
    meanings_cleaned = 0
    meanings_replaced = 0
    meanings_cleared = 0
    eng_fixed = 0
    individual_garbage_removed = 0

    # Track what we couldn't fix
    unmatched_roots = defaultdict(int)

    for ch in data['chapters']:
        chapter_num = ch['chapter']
        for v in ch['verses']:
            verse_num = v['verse']
            vref = f"{chapter_num}:{verse_num}"

            for w in v['words']:
                total_words += 1
                heb = w.get('heb', '')
                eng = w.get('eng', '')
                root = w.get('root', '')
                meanings = w.get('meanings', [])

                if not meanings:
                    continue

                words_with_meanings += 1

                # Determine if this word is a proper noun
                is_proper = False
                etcbc_matches = get_etcbc_match(heb, chapter_num, verse_num, etcbc_lookup)
                matched_lex = None
                matched_pos = None

                if etcbc_matches:
                    for em in etcbc_matches:
                        if em['pos'] == 'nmpr':
                            is_proper = True
                        matched_lex = em['lex']
                        matched_pos = em['pos']

                # STRATEGY: If we have curated meanings for this lexeme/root,
                # ALWAYS replace - the curated list is better than Strong's/gematria matches.
                # Otherwise, detect and remove garbage entries.

                new_meanings = None

                # Try ETCBC lexeme match first
                if matched_lex:
                    new_meanings = get_correct_meanings(matched_lex, matched_pos, lex_to_glosses)

                # Try root field
                if not new_meanings and root:
                    new_meanings = get_correct_meanings(root, None, lex_to_glosses)

                if new_meanings:
                    # We have curated meanings - always use them
                    if w['meanings'] != list(new_meanings):
                        w['meanings'] = list(new_meanings)
                        meanings_replaced += 1
                else:
                    # No curated meanings - detect and remove garbage
                    garbage_count = 0
                    for m in meanings:
                        if is_garbage_meaning(m, is_proper, root):
                            garbage_count += 1

                    garbage_ratio = garbage_count / len(meanings) if meanings else 0

                    if garbage_ratio > 0.5:
                        # Mostly garbage and no replacement - clear
                        w['meanings'] = []
                        meanings_cleared += 1
                        if matched_lex:
                            unmatched_roots[matched_lex] += 1
                        elif root:
                            unmatched_roots[root] += 1
                    elif garbage_count > 0:
                        # Some garbage - remove individual bad entries
                        cleaned = [m for m in meanings if not is_garbage_meaning(m, is_proper, root)]
                        if cleaned != meanings:
                            individual_garbage_removed += len(meanings) - len(cleaned)
                        w['meanings'] = cleaned
                        meanings_cleaned += 1

                # Fix eng field if it has artifacts
                if eng:
                    orig_eng = eng
                    # Remove Strong's format artifacts from eng
                    if re.search(r'[\u0590-\u05FF]', eng):
                        # Has Hebrew chars in eng - bad
                        if matched_lex and matched_lex in ROOT_MEANINGS:
                            w['eng'] = ROOT_MEANINGS[matched_lex][0]
                            eng_fixed += 1
                    if 'chronicals' in eng:
                        w['eng'] = eng.replace('chronicals', 'chronicles')
                        eng_fixed += 1

    # Save
    with open('genesis_v3.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Report
    print("=" * 60)
    print("GENESIS_V3.JSON MEANINGS AUDIT REPORT")
    print("=" * 60)
    print(f"Total words:                    {total_words}")
    print(f"Words with meanings:            {words_with_meanings}")
    print(f"Meanings fully replaced:        {meanings_replaced}")
    print(f"Meanings cleared (all garbage): {meanings_cleared}")
    print(f"Meanings partially cleaned:     {meanings_cleaned}")
    print(f"Individual garbage removed:     {individual_garbage_removed}")
    print(f"Eng fields fixed:               {eng_fixed}")
    print(f"Total words affected:           {meanings_replaced + meanings_cleared + meanings_cleaned}")
    print()

    if unmatched_roots:
        print(f"Unmatched roots (cleared, top 30):")
        for root, count in sorted(unmatched_roots.items(), key=lambda x: -x[1])[:30]:
            glosses = lex_to_glosses.get(root, set())
            print(f"  {root} ({count}x) ETCBC glosses: {', '.join(glosses) if glosses else 'none'}")


if __name__ == '__main__':
    main()
