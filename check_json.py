import json
import os

file_path = 'data/20250306_fukushima1R.json'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Race ID: {data.get('race_id')}")
print(f"Race Name: {data.get('race_name')}")

horses = data.get('horses', [])
print(f"Total Horses: {len(horses)}")

if horses:
    first_horse = horses[0]
    print(f"First Horse: {first_horse.get('horse_name')}")
    print("Keys in first horse:", list(first_horse.keys()))
    
    # Check for premium content
    premium_keys = [k for k in first_horse.keys() if 'mark' in k or 'prediction' in k]
    print(f"Premium Keys found: {premium_keys}")
    
    # Check pedigree
    pedigree = first_horse.get('pedigree_data', {})
    print(f"Pedigree Data: {pedigree}")
else:
    print("No horses found!")
