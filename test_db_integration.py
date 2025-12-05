#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify DB saving and JSON export"""

import sys
import os
import json
import asyncio
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from src.scrapers.keibabook import KeibaBookScraper
from src.utils.db_manager import CSVDBManager

async def main():
    print("--- Starting DB Integration Test ---")
    
    # Setup temporary test DB directory
    test_db_dir = "data/test_db"
    test_json_dir = "data/test_json"
    
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir)
    if os.path.exists(test_json_dir):
        shutil.rmtree(test_json_dir)
        
    db_manager = CSVDBManager(db_dir=test_db_dir)
    
    # Mock settings
    settings = {
        'shutuba_url': 'https://example.com',
        'race_type': 'jra',
        'race_id': 'test_race_id'
    }
    
    scraper = KeibaBookScraper(settings, db_manager)
    
    # Read the HTML file
    try:
        with open('debug_files/debug_nouryoku.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Error: debug_files/debug_nouryoku.html not found.")
        return

    # Parse data
    print("Parsing data...")
    horse_table_data = scraper._parse_horse_table_data(html_content)
    
    # Create mock race data
    race_data = {
        'race_name': 'Test Race',
        'race_grade': 'OP',
        'distance': '1600m',
        'horses': []
    }
    
    for horse_num, past_perf in horse_table_data.items():
        race_data['horses'].append({
            'horse_num': str(horse_num),
            'horse_name': f"Test Horse {horse_num}",
            'past_performance': past_perf
        })
        
    # Save to DB
    print("Saving to DB...")
    db_manager.save_race_data(race_data, 'test_race_id', 'test_race_key')
    
    # Verify CSV content
    print("Verifying CSV content...")
    import pandas as pd
    horse_df = pd.read_csv(os.path.join(test_db_dir, 'horses.csv'))
    print(f"Saved {len(horse_df)} horses to CSV")
    
    # Check if past_performance is saved as string
    first_horse = horse_df.iloc[0]
    pp_str = first_horse['past_performance']
    print(f"Past performance type in CSV: {type(pp_str)}")
    print(f"Past performance content (start): {pp_str[:50]}...")
    
    # Export for AI
    print("Exporting for AI...")
    json_path = db_manager.export_for_ai('test_race_id', output_dir=test_json_dir)
    
    if json_path:
        print(f"Exported to {json_path}")
        
        # Verify JSON content
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        print(f"JSON Race Name: {json_data.get('race_name')}")
        
        horses = json_data.get('horses', [])
        if horses:
            first_horse_json = horses[0]
            pp = first_horse_json.get('past_performance')
            print(f"JSON Past Performance type: {type(pp)}")
            print(f"JSON Past Performance length: {len(pp)}")
            
            if isinstance(pp, list) and len(pp) > 0:
                print("Success: Past performance is a list in JSON")
                print(f"First race date: {pp[0].get('date')}")
            else:
                print("FAILURE: Past performance is not a list or is empty")
        else:
            print("FAILURE: No horses in JSON")
            
    else:
        print("FAILURE: Export returned None")

if __name__ == "__main__":
    asyncio.run(main())
