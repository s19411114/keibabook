#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to check track condition and date extraction"""

from bs4 import BeautifulSoup

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

# Find past performance cells
zensou_tds = first_row.find_all('td', class_=lambda x: x and 'zensou' in x)

if zensou_tds:
    first_zensou = zensou_tds[0]
    print("=== First Past Performance Cell ===\n")
    
    # Find date paragraph
    dt = first_zensou.find('dt')
    if dt:
        ichigyo_p = dt.find('p', class_='ichigyo')
        if ichigyo_p:
            print("Raw HTML:")
            print(ichigyo_p)
            print("\nText content:")
            print(repr(ichigyo_p.get_text()))
            print("\nAll children:")
            for child in ichigyo_p.children:
                print(f"  Type: {type(child).__name__}, Content: {repr(str(child)[:100])}")
