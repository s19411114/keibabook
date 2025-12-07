#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check what data is currently being collected"""

import json

# Read the JSON file
with open('data/20251211_kawasaki11R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== レース情報 ===")
print(f"レース名: {data.get('race_name')}")
print(f"レースID: {data.get('race_id')}")
print(f"距離: {data.get('distance')}")
print(f"馬場: {data.get('track_condition')}")

print("\n=== 馬情報（1頭目のサンプル） ===")
horse = data['horses'][0]

print(f"\n【基本情報】")
print(f"馬名: {horse.get('horse_name')}")
print(f"馬番: {horse.get('horse_num')}")
print(f"枠番: {horse.get('frame_num')}")
print(f"騎手: {horse.get('jockey')}")
print(f"オッズ: {horse.get('odds')}")
print(f"人気: {horse.get('popularity')}")

print(f"\n【予想印】")
predictions = horse.get('predictions')
if predictions:
    if isinstance(predictions, str):
        import json as json_module
        try:
            predictions = json_module.loads(predictions)
        except Exception as e:
            print('predictions JSON parse error:', e)
            pass
    print(f"予想印: {predictions}")
else:
    print("予想印: なし")

print(f"\n【指数・レーティング】")
# Check all keys to find rating/index fields
for key in horse.keys():
    if any(keyword in key.lower() for keyword in ['rating', 'index', '指数', 'レーティング', 'ai', 'speed']):
        print(f"{key}: {horse.get(key)}")

print(f"\n【血統データ】")
pedigree = horse.get('pedigree_data', {})
if pedigree:
    print(f"父: {pedigree.get('father')}")
    print(f"母: {pedigree.get('mother')}")
    print(f"父父: {pedigree.get('fathers_father')}")
else:
    print("血統データ: なし")

print(f"\n【その他のフィールド】")
print("全フィールド一覧:")
for key in sorted(horse.keys()):
    if key not in ['horse_name', 'horse_num', 'frame_num', 'jockey', 'odds', 'popularity', 'predictions', 'pedigree_data', 'past_performance']:
        value = horse.get(key)
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"  {key}: {value}")
