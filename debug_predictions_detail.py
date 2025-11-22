#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to check prediction mark HTML structure"""

from bs4 import BeautifulSoup

# Read the HTML file
with open('debug_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Find the shutuba table
shutuba_table = soup.select_one(".syutuba_sp")
tbody = shutuba_table.select_one("tbody")
first_row = tbody.find('tr')
tds = first_row.find_all('td')

print("=== 予想家の印セル（詳細） ===\n")

# Check prediction columns (indices 3, 4, 5)
for i in [3, 4, 5]:
    td = tds[i]
    print(f"\n[列{i}] HTML:")
    print(td.prettify()[:500])
    print(f"\nText: '{td.get_text(strip=True)}'")
    print(f"Has SVG: {td.find('svg') is not None}")
    print(f"Has IMG: {td.find('img') is not None}")
    print(f"Has SPAN: {td.find('span') is not None}")
    
    # Check for specific classes or attributes
    if td.find('span'):
        span = td.find('span')
        print(f"SPAN class: {span.get('class')}")
        print(f"SPAN text: '{span.get_text(strip=True)}'")
