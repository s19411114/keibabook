"""クイックログインテスト"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Cookie読み込み
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 阪神12Rにアクセス
        race_url = 'https://s.keibabook.co.jp/cyuou/syutuba/2025113005012'
        print(f'Accessing: {race_url}')
        await page.goto(race_url, timeout=60000, wait_until='domcontentloaded')
        
        # 馬の行を数える
        rows = await page.query_selector_all('table tbody tr')
        print(f'Table rows: {len(rows)}')
        
        # 馬名リンクを数える
        horse_links = await page.query_selector_all('a[href*="/uma/"]')
        print(f'Horse links: {len(horse_links)}')
        
        # 馬番を数える
        umaban = await page.query_selector_all('td.Umaban')
        print(f'Umaban cells: {len(umaban)}')
        
        if len(horse_links) >= 6:
            print('✅ LOGIN SUCCESS - All horses visible!')
        elif len(horse_links) > 0 and len(horse_links) <= 3:
            print('❌ NOT LOGGED IN - Only 3 horses')
        else:
            # コンテンツを確認
            content = await page.content()
            with open('debug_files/debug_test.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print('Saved debug_files/debug_test.html for inspection')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test())
