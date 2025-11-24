import json
import os

file_path = 'data/20251124_tokyo11R.json'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Race Name: {data.get('race_name')}")
print(f"Race Grade: {data.get('race_grade')}")

horses = data.get('horses', [])
print(f"Total Horses: {len(horses)}")

if horses:
    # Check first few horses for marks
    print("\n--- First 3 Horses ---")
    for i, horse in enumerate(horses[:3]):
        print(f"Horse {horse.get('horse_num')} {horse.get('horse_name')}:")
        print(f"  Mark: {horse.get('prediction_mark')}")
        print(f"  Odds: {horse.get('odds_text')}")
        
    # Check premium keys presence
    first_horse = horses[0]
    premium_keys = [k for k in first_horse.keys() if 'mark' in k or 'prediction' in k]
    print(f"\nPremium Keys found: {premium_keys}")
else:
    print("No horses found!")
