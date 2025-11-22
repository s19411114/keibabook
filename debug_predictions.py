#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to check prediction marks in HTML"""

from bs4 import BeautifulSoup

# Read the HTML file
with open('debug_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Find the shutuba table
shutuba_table = soup.select_one(".syutuba_sp")
if not shutuba_table:
    print("出馬表テーブルが見つかりません")
    exit(1)

print("=== 出馬表テーブル発見 ===\n")

# Check header
thead = shutuba_table.select_one("thead")
if thead:
    headers = thead.find_all("th")
    print(f"ヘッダー数: {len(headers)}")
    print("\nヘッダー一覧:")
    for i, th in enumerate(headers):
        print(f"  [{i}] {th.get_text(strip=True)}")

# Check first horse row
tbody = shutuba_table.select_one("tbody")
if tbody:
    first_row = tbody.find('tr')
    if first_row:
        print("\n=== 1頭目のデータ ===")
        tds = first_row.find_all('td')
        print(f"列数: {len(tds)}")
        
        for i, td in enumerate(tds):
            text = td.get_text(strip=True)
            classes = td.get('class', [])
            print(f"\n[{i}] class={classes}")
            print(f"    Text: {text[:50] if text else '(empty)'}")
            
            # Check for images/SVG
            if td.find('svg'):
                print(f"    Contains: SVG")
            if td.find('img'):
                img = td.find('img')
                print(f"    Contains: IMG src={img.get('src', '')}")
