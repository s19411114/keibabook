"""実際のレースでログインテスト"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Cookie読み込み
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 阪神11R
        race_url = 'https://s.keibabook.co.jp/cyuou/syutuba/202511305011'
        print(f'Testing: {race_url}')
        await page.goto(race_url, timeout=90000, wait_until='domcontentloaded')
        
        # ページを確認
        title = await page.title()
        print(f'Title: {title}')
        
        # 馬名を取得
        horse_names = await page.query_selector_all('td.Bamei a, a[href*="/uma/"]')
        print(f'Horse links found: {len(horse_names)}')
        
        # 馬名を表示
        for i, link in enumerate(horse_names[:5]):
            name = await link.text_content()
            print(f'  {i+1}: {name.strip()}')
        
        # 全馬の行を確認
        rows = await page.query_selector_all('tr')
        print(f'Total rows: {len(rows)}')
        
        if len(horse_names) >= 10:
            print('\n✅ SUCCESS! All horses visible - LOGGED IN!')
        elif len(horse_names) >= 6:
            print('\n✅ LOGGED IN - Multiple horses visible')
        elif len(horse_names) <= 3:
            print('\n❌ NOT LOGGED IN - Only 3 horses visible')
        else:
            print(f'\n⚠️ Unclear status - {len(horse_names)} horses')
        
        # デバッグ用にHTML保存
        content = await page.content()
        with open('debug_race.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('\nSaved debug_race.html')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_login())
