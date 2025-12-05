#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡易テスト: Cookie認証とレースページ取得を確認
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def test_login_and_fetch():
    """Cookie認証とページ取得をテスト"""
    
    print("🔐 Cookie認証テスト")
    print("=" * 60)
    
    # Cookieを読み込み
    cookies_path = Path("cookies.json")
    if not cookies_path.exists():
        print("❌ cookies.json が見つかりません")
        return
    
    with open(cookies_path, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"✅ Cookie読み込み成功: {len(cookies)}個")
    
    # ブラウザ起動
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Cookie設定
        await page.context.add_cookies(cookies)
        print("✅ Cookie設定完了")
        
        # トップページにアクセス
        test_urls = [
            "https://www.keibabook.co.jp/",
            "https://s.keibabook.co.jp/",
            "https://www.keibabook.co.jp/sp/",
        ]
        
        for test_url in test_urls:
            print(f"\n📍 テストURL: {test_url}")
            
            response = await page.goto(test_url, wait_until='networkidle', timeout=30000)
            
            if response and response.ok:
                print(f"✅ ページ読み込み成功 (status: {response.status})")
                
                # ログイン状態確認
                content = await page.content()
                
                if "ログイン" in content and "プレミアム" not in content:
                    print("⚠️ ログインしていません")
                elif "プレミアム" in content or "会員" in content:
                    print("✅ ログイン成功（プレミアム会員）")
                else:
                    print("ℹ️ ログイン状態不明")
                
                # ページタイトル取得
                title = await page.title()
                print(f"📄 ページタイトル: {title}")
                
                # 最終URL
                print(f"🔗 最終URL: {page.url}")
                
                break  # 成功したらループ終了
                
            else:
                print(f"❌ ページ読み込み失敗 (status: {response.status if response else 'None'})")
        
        await browser.close()
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    asyncio.run(test_login_and_fetch())
