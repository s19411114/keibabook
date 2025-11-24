from bs4 import BeautifulSoup

with open('debug_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
table = soup.select_one(".syutuba_sp tbody")

if table:
    # Print headers if possible (though tbody usually doesn't have th)
    # Check first row
    rows = table.find_all('tr')
    print(f"Total rows: {len(rows)}")
    
    if rows:
        first_row = rows[0]
        print("First row classes:", first_row.get('class'))
        print("First row content:")
        for i, td in enumerate(first_row.find_all(['td', 'th'])):
            print(f"  Col {i}: Class={td.get('class')}, Text={td.get_text(strip=True)[:20]}")
            
        # Check for specific classes related to marks
        print("\nSearching for 'yoso' or 'mark' classes:")
        yoso_elems = soup.select("[class*='yoso'], [class*='mark']")
        print(f"Found {len(yoso_elems)} elements with 'yoso' or 'mark'")
        if yoso_elems:
            print("Sample:", yoso_elems[0])

else:
    print("Table .syutuba_sp tbody not found")
