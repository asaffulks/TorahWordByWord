#!/usr/bin/env python3
"""Pull additional commentators from Sefaria to fill gaps."""
import json, os, re, sys, time, html
import urllib.request
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CACHE = Path('K:/TorahByWord/sefaria_cache')
GENESIS = Path('K:/TorahByWord/genesis_fixed.json')

def cached_get(url, cache_key):
    cache_file = CACHE / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    time.sleep(0.4)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        data = {}

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

def extract_text(data):
    en = data.get('text', [])
    if isinstance(en, list):
        en = [t for t in en if t and isinstance(t, str)]
        if not en:
            return ""
        parts = []
        for t in en:
            clean = re.sub(r'<[^>]+>', '', t).strip()
            clean = html.unescape(clean)
            if clean:
                parts.append(clean)
        return ' '.join(parts)
    elif isinstance(en, str):
        return html.unescape(re.sub(r'<[^>]+>', '', en)).strip()
    return ""

# New commentators with their API paths
NEW_COMMENTATORS = [
    ('chizkuni', 'Chizkuni,_Genesis', 'Chizkuni'),
    ('rabbeinu_bahya', 'Rabbeinu_Bahya,_Bereshit', 'Rabbeinu Bahya'),
    ('onkelos', 'Onkelos_Genesis', 'Onkelos'),
    ('kli_yakar', 'Kli_Yakar_on_Genesis', 'Kli Yakar'),
]

with open(GENESIS, 'r', encoding='utf-8') as f:
    genesis = json.load(f)

# Count existing commentary gaps
total_verses = 0
no_commentary = 0
for ch in genesis['chapters']:
    for v in ch['verses']:
        total_verses += 1
        has_any = any(v.get(k, '').strip() for k in ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim'])
        if not has_any:
            no_commentary += 1

print(f"Verses without any commentary: {no_commentary}/{total_verses}")
print(f"Pulling 4 new commentators for all {total_verses} verses...")

for cache_prefix, api_path, display_name in NEW_COMMENTATORS:
    print(f"\n  {display_name}...")
    pulled = 0
    has_content = 0
    already_cached = 0

    for ch in genesis['chapters']:
        ch_num = ch['chapter']
        for v in ch['verses']:
            v_num = v['verse']
            cache_key = f"{cache_prefix}_genesis_{ch_num}_{v_num}"
            cache_file = CACHE / f"{cache_key}.json"

            if cache_file.exists():
                already_cached += 1
                data = json.load(open(cache_file, 'r', encoding='utf-8'))
                text = extract_text(data)
                if text:
                    has_content += 1
                continue

            url = f"https://www.sefaria.org/api/texts/{api_path}.{ch_num}.{v_num}?lang=en&context=0"
            data = cached_get(url, cache_key)
            text = extract_text(data)
            pulled += 1
            if text:
                has_content += 1

            if pulled % 50 == 0:
                print(f"    Ch {ch_num}:{v_num} — {pulled} pulled, {has_content} with content")

    print(f"    Done: {pulled} new + {already_cached} cached, {has_content} with content")

# Now add the new commentary fields to genesis_fixed.json
print("\nAdding new commentary to genesis_fixed.json...")
added = 0

for ch in genesis['chapters']:
    for v in ch['verses']:
        ch_num = ch['chapter']
        v_num = v['verse']

        for cache_prefix, api_path, display_name in NEW_COMMENTATORS:
            field_name = cache_prefix
            cache_key = f"{cache_prefix}_genesis_{ch_num}_{v_num}"
            cache_file = CACHE / f"{cache_key}.json"

            text = ""
            if cache_file.exists():
                try:
                    data = json.load(open(cache_file, 'r', encoding='utf-8'))
                    text = extract_text(data)
                except:
                    pass

            v[field_name] = text
            if text:
                added += 1

# Save
with open(GENESIS, 'w', encoding='utf-8') as f:
    json.dump(genesis, f, ensure_ascii=False, indent=2)

print(f"Added {added} commentary entries")

# Recount gaps
no_commentary_after = 0
all_fields = ['rashi', 'ramban', 'ibn_ezra', 'sforno', 'or_hachaim',
              'chizkuni', 'rabbeinu_bahya', 'onkelos', 'kli_yakar']
for ch in genesis['chapters']:
    for v in ch['verses']:
        has_any = any(v.get(k, '').strip() for k in all_fields)
        if not has_any:
            no_commentary_after += 1

print(f"\nBefore: {no_commentary} verses with no commentary")
print(f"After:  {no_commentary_after} verses with no commentary")
print(f"Filled: {no_commentary - no_commentary_after} gaps")
