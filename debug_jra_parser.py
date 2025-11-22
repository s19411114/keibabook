import asyncio
from playwright.async_api import async_playwright
import datetime
from bs4 import BeautifulSoup

async def debug_calendar():
    target_date = datetime.date.today()
    print(f"Target Date: {target_date}")
    
    url = f"https://www.jra.go.jp/keiba/calendar/{target_date.year}/{target_date.month}/"
    print(f"URL: {url}")
    
    async with async_playwright() as p:
        # Use a standard User-Agent
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            print(f"Response Status: {response.status}")
            
            title = await page.title()
            print(f"Page Title: {title}")
            
            content = await page.content()
            print(f"Content Length: {len(content)}")
            
            soup = BeautifulSoup(content, 'html.parser')
            tds = soup.select("td")
            print(f"Found {len(tds)} tds")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_calendar())
