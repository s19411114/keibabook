import json
import sys

try:
    with open('data/20251211_kawasaki11R.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"Race Name: {data.get('race_name')}")
        print(f"Distance: {data.get('distance')}")
        
        horses = data.get('horses', [])
        if horses:
            print(f"Horse 1 Pedigree: {json.dumps(horses[0].get('pedigree_data'), ensure_ascii=False)}")
        else:
            print("No horses found")
            
        # Check for marks/odds keys in the first horse
        if horses:
            h = horses[0]
            print(f"Keys in horse object: {list(h.keys())}")
            
except Exception as e:
    print(f"Error: {e}")
