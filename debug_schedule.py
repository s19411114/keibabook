import asyncio
from playwright.async_api import async_playwright
import os
import json

async def fetch_schedule():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Ensure login: try load cookies or perform login if needed
        cookie_file = 'cookies.json'
        from src.utils.login import KeibaBookLogin
        # Attempt to ensure login using default test URL
        await KeibaBookLogin.ensure_logged_in(page.context, os.environ.get('LOGIN_ID'), os.environ.get('LOGIN_PASSWORD'), cookie_file=cookie_file, save_cookies=True)
            
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
