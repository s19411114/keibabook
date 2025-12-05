"""詳細ログインテスト"""
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
        
        # Cookie情報を表示
        print('Cookies:')
        for c in cookies:
            if c['name'] in ['tk', 'keibabook_session', 'XSRF-TOKEN']:
                print(f"  {c['name']}: {c['domain']} (expires: {c.get('expires', 'session')})")
        
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # まずトップページでCookieが有効か確認
        print('\n1. Checking top page...')
        await page.goto('https://s.keibabook.co.jp/', timeout=60000, wait_until='domcontentloaded')
        
        current_url = page.url
        print(f'   Current URL: {current_url}')
        
        if 'login' in current_url:
            print('   ❌ Redirected to login - cookies not working')
            await browser.close()
            return
        
        # ログインボタンがあるか確認
        login_btn = await page.query_selector('a[href*="login"]')
        logout_btn = await page.query_selector('a[href*="logout"]')
        
        if login_btn:
            text = await login_btn.text_content()
            print(f'   Found login link: {text}')
        if logout_btn:
            text = await logout_btn.text_content()
            print(f'   Found logout link: {text}')
        
        # 出馬表ページに移動
        print('\n2. Navigating to race page...')
        race_url = 'https://s.keibabook.co.jp/cyuou/syutuba/202511305011'
        await page.goto(race_url, timeout=60000, wait_until='networkidle')
        
        current_url = page.url
        print(f'   Current URL: {current_url}')
        
        # ページ内容を確認
        content = await page.content()
        
        # 存在しないページエラー
        if '存在しません' in content:
            print('   ❌ Page does not exist')
            with open('debug_files/debug_race2.html', 'w', encoding='utf-8') as f:
                f.write(content)
            await browser.close()
            return
        
        # 馬データを探す
        print('\n3. Looking for horse data...')
        
        # パターン1: テーブル行
        tables = await page.query_selector_all('table')
        print(f'   Tables found: {len(tables)}')
        
        for i, table in enumerate(tables[:3]):
            rows = await table.query_selector_all('tr')
            class_name = await table.get_attribute('class')
            print(f'   Table {i+1} ({class_name}): {len(rows)} rows')
        
        # パターン2: 馬名リンク
        horse_links = await page.query_selector_all('a[href*="/uma/"]')
        print(f'   Horse links (/uma/): {len(horse_links)}')
        
        # パターン3: td要素
        waku_tds = await page.query_selector_all('td[class*="Waku"]')
        print(f'   Waku TDs: {len(waku_tds)}')
        
        # HTMLを保存
        with open('debug_files/debug_race2.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('\n   Saved debug_files/debug_race2.html')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_login())
