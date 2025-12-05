import json

# \u30c6\u30b9\u30c8\u7528\u306e\u7c21\u6613\u30b9\u30af\u30ea\u30d7\u30c8: \u73fe\u5728\u306e\u30c7\u30fc\u30bf\u3092\u78ba\u8a8d
with open('data/20251211_kawasaki11R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
print(f"Race Name: {data.get('race_name')}")
print(f"Distance: {data.get('distance')}")
print(f"Number of horses: {len(data.get('horses', []))}")

if data.get('horses'):
    h = data['horses'][0]
    print(f"\nHorse 1 ({h.get('horse_name')}):")
    print(f"  Pedigree keys: {list(h.get('pedigree_data', {}).keys())}")
    print(f"  Has predictions: {'predictions' in h}")
    print(f"  Has odds: {'odds' in h}")
    print(f"  Has past_performance: {'past_performance' in h}")
    
    if h.get('pedigree_data'):
        ped = h['pedigree_data']
        print(f"  Father: {ped.get('father')}")
        print(f"  Fathers Father: {ped.get('fathers_father')}")
        print(f"  Fathers Fathers Father: {ped.get('fathers_fathers_father')}")
