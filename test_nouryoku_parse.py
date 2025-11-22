#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to debug nouryoku_html parsing using the actual scraper class"""

import sys
import os
import json
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from src.scrapers.keibabook import KeibaBookScraper

async def main():
    # Mock settings
    settings = {
        'shutuba_url': 'https://example.com',
        'race_type': 'jra'
    }
    
    scraper = KeibaBookScraper(settings)
    
    # Read the HTML file
    try:
        with open('debug_nouryoku.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Error: debug_nouryoku.html not found.")
        return

    print(f"Read {len(html_content)} bytes from debug_nouryoku.html")

    # Test the parser
    print("\n--- Testing _parse_horse_table_data ---")
    try:
        horse_data = scraper._parse_horse_table_data(html_content)
        
        print(f"Extracted data for {len(horse_data)} horses")
        
        if horse_data:
            # Check the first horse
            first_horse_num = list(horse_data.keys())[0]
            first_horse = horse_data[first_horse_num]
            
            print(f"\nHorse {first_horse_num} Past Performance ({len(first_horse)} races):")
            
            for i, race in enumerate(first_horse):
                print(f"\n  Race {i+1}:")
                print(f"    Race Name: {race.get('race_name')}")
                print(f"    Date: {race.get('date')}")
                print(f"    Track Condition: {race.get('track_condition')} (1=良, 2=稍重, 3=重, 4=不良)")
                print(f"    Order: {race.get('order')}")
                print(f"    Popularity: {race.get('popularity')}")
                print(f"    Time: {race.get('time')}")
                print(f"    Distance: {race.get('distance')}")
                print(f"    Passing Order: {race.get('passing_order')}")
                print(f"    Total Horses: {race.get('total_horses')}")
                print(f"    Horse Number: {race.get('horse_number')}")
                
                # Check for missing critical fields
                missing = []
                if not race.get('race_name'): missing.append('race_name')
                if not race.get('date'): missing.append('date')
                if not race.get('order'): missing.append('order')
                if not race.get('total_horses'): missing.append('total_horses')
                if not race.get('horse_number'): missing.append('horse_number')
                if not race.get('track_condition'): missing.append('track_condition')
                
                if missing:
                    print(f"    [WARNING] Missing fields: {', '.join(missing)}")
                else:
                    print(f"    [OK] All fields present")


    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
