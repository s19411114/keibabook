#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to identify available fields in past performance data"""

from bs4 import BeautifulSoup
import re

# Read the HTML file
with open('debug_nouryoku.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Find the table
table = soup.find('table', class_='nouryoku_html_table')
if not table:
    print("Table not found")
    exit(1)

# Find first row
rows = table.find_all('tr', class_=lambda x: x and x.startswith('js-umaban'))
if not rows:
    print("No rows found")
    exit(1)

first_row = rows[0]
print("=== First Horse Row ===")

# Find past performance cells
zensou_tds = first_row.find_all('td', class_=lambda x: x and 'zensou' in x)
print(f"Found {len(zensou_tds)} past performance cells")

if zensou_tds:
    first_zensou = zensou_tds[0]
    print("\n=== First Past Performance Cell ===")
    print(f"Classes: {first_zensou.get('class')}")
    
    # Print all text content
    print("\n--- All Text Content ---")
    print(first_zensou.get_text())
    
    # Find all spans
    print("\n--- All Spans ---")
    for span in first_zensou.find_all('span'):
        print(f"Class: {span.get('class')} | Text: {span.get_text(strip=True)}")
    
    # Find all divs
    print("\n--- All Divs ---")
    for div in first_zensou.find_all('div'):
        print(f"Class: {div.get('class')} | Text: {div.get_text(strip=True)[:50]}")
    
    # Find all lists
    print("\n--- All Lists ---")
    for ul in first_zensou.find_all('ul'):
        print(f"Class: {ul.get('class')}")
        for li in ul.find_all('li'):
            print(f"  - {li.get_text(strip=True)}")
