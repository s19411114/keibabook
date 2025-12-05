from bs4 import BeautifulSoup
import re

def analyze():
    try:
        with open("debug_files/debug_schedule.html", "r", encoding="utf-8") as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all links to 'syutuba'
        links = soup.find_all('a', href=re.compile(r'syutuba'))
        
        print(f"Found {len(links)} links to 'syutuba':")
        for link in links:
            print(f"Text: {link.get_text(strip=True)}")
            print(f"URL: {link['href']}")
            print("-" * 20)
            
        # Also look for venue names
        venues = ["中山", "阪神", "中京", "小倉", "東京", "京都", "新潟", "福島", "札幌", "函館"]
        print("\nSearching for venue names:")
        for venue in venues:
            if venue in content:
                print(f"Found venue: {venue}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
