import asyncio
from playwright.async_api import async_playwright
import datetime

async def fetch_jra_schedule():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Get current month
        today = datetime.date.today()
        url = f"https://www.jra.go.jp/keiba/calendar/{today.year}/{today.month}/"
        print(f"Fetching {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            
            with open("debug_jra_schedule.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved to debug_jra_schedule.html")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_jra_schedule())
