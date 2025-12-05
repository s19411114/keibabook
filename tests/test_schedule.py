"""日程からレースIDを取得"""
import asyncio
from playwright.async_api import async_playwright
import json
import re

async def get_race_schedule():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 日程ページ
        print('Accessing schedule page...')
        await page.goto('https://s.keibabook.co.jp/cyuou/nittei/top', timeout=60000, wait_until='networkidle')
        
        content = await page.content()
        
        # 11/30 の開催を探す
        # 2025113005 = 2025年11月30日 05=阪神
        # 2025113006 = 2025年11月30日 06=中山
        
        # syutuba リンクを全部探す
        race_ids = re.findall(r'syutuba/(\d+)', content)
        unique_ids = sorted(set(race_ids))
        
        print(f'Found {len(unique_ids)} unique race IDs')
        print('11/30 races:')
        for rid in unique_ids:
            if rid.startswith('2025113'):
                print(f'  {rid}')
        
        # HTMLを保存
        with open('debug_files/debug_schedule.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Saved debug_files/debug_schedule.html')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(get_race_schedule())
