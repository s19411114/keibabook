#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify past performance data in JSON output"""

import json

# Load JSON
with open('data/json/2025121104111120.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check first horse
horse = data['horses'][0]
print(f"Horse: {horse['horse_name']}")
print(f"Odds: {horse['odds']}")
print(f"Popularity: {horse['popularity']}")

# Parse past_performance
past_perf = json.loads(horse['past_performance'])
print(f"\nPast races: {len(past_perf)}")

if past_perf:
    print("\nFirst race details:")
    for key, value in past_perf[0].items():
        print(f"  {key}: {value}")
else:
    print("No past performance data found!")
