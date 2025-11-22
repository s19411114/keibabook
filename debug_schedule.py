import asyncio
from playwright.async_api import async_playwright
import os
import json

async def fetch_schedule():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Try to load cookies if available
        cookie_file = 'cookies.json'
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            await page.context.add_cookies(cookies)
            
        url = "https://s.keibabook.co.jp/"
        print(f"Fetching {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            
            with open("schedule.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved to schedule.txt")
            
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_schedule())
