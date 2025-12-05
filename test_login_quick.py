"""クイックログインテスト"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        print('Testing login...')
        await page.goto('https://s.keibabook.co.jp/cyuou/syutuba/202511305011', 
                       timeout=90000, wait_until='domcontentloaded')
        
        # 馬を数える
        horse_links = await page.query_selector_all('a[href*="/uma/"]')
        print(f'Horses: {len(horse_links)}')
        
        if len(horse_links) >= 6:
            print('✅ SUCCESS! Logged in!')
        elif len(horse_links) <= 3 and len(horse_links) > 0:
            print('❌ NOT LOGGED IN - only 3 horses')
        else:
            print('⚠️ No data found')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test())
