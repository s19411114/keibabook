#!/usr/bin/env python3
"""
最新のJSONファイルを探すスクリプト
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# 15分以内に作成されたJSONファイルを探す
cutoff_time = datetime.now() - timedelta(minutes=15)

data_dir = Path('/mnt/c/GeminiCLI/TEST/keibabook/data')

print(f"Searching for JSON files created after {cutoff_time}")
print(f"In directory: {data_dir}")
print()

for json_file in data_dir.rglob('*.json'):
    mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
    if mtime > cutoff_time:
        print(f"Found: {json_file}")
        print(f"  Modified: {mtime}")
        print(f"  Size: {json_file.stat().st_size} bytes")
        
        # 内容の一部を表示
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  Keys: {list(data.keys())}")
                if 'horses' in data:
                    print(f"  Horses count: {len(data['horses'])}")
                    if len(data['horses']) > 0:
                        first_horse = data['horses'][0]
                        print(f"  First horse keys: {list(first_horse.keys())}")
                        if 'pedigree_data' in first_horse:
                            print(f"  ✅ pedigree_data found!")
                        if 'training_data' in first_horse:
                            print(f"  ✅ training_data found!")
        except Exception as e:
            print(f"  Error reading file: {e}")
        print()
