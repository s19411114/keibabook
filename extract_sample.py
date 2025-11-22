#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract sample data from JSON for user review"""

import json

# Read the JSON file
with open('data/20251211_kawasaki11R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract first horse as sample
horse = data['horses'][0]

sample = {
    "馬名": horse['horse_name'],
    "馬番": horse['horse_num'],
    "枠番": horse.get('frame_num'),
    "騎手": horse.get('jockey'),
    "オッズ": horse.get('odds'),
    "人気": horse.get('popularity'),
    "過去走データ（前2走のみ表示）": horse['past_performance'][:2]
}

print(json.dumps(sample, ensure_ascii=False, indent=2))
