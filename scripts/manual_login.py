"""
================================================================================
競馬ブックスマート 手動ログインヘルパー
================================================================================

ブラウザを開いて手動でログインし、Cookieを保存します。
⚠️ 競馬ブックスマート (s.keibabook.co.jp) 専用

【Cookieについて】
- 「ログインしたままにする」をチェックすると、tkクッキーが約30日間有効
- 30日以内に再ログインすれば、IDとパスワードは不要
- セッションCookie（keibabook_session）は毎回更新されますが、tkがあれば大丈夫

使い方:
    python scripts/manual_login.py
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 競馬ブックスマートのURL（s.がつく）
LOGIN_URL = "https://s.keibabook.co.jp/login/login"
TOP_URL = "https://s.keibabook.co.jp/"


async def manual_login():
    print("=" * 60)
    print("競馬ブックスマート 手動ログインヘルパー")
    print("=" * 60)
    print()
    print("📌 対象サイト: https://s.keibabook.co.jp/")
    print("   (競馬ブックスマート - スマホ版)")
    print()
    
    async with async_playwright() as p:
        # ヘッドありでブラウザを起動
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # ログインページに移動
        print("🌐 ログインページを開いています...")
        print(f"   URL: {LOGIN_URL}")
        await page.goto(LOGIN_URL, timeout=60000)
        
        print()
        print("=" * 60)
        print("📝 ブラウザでログインしてください")
        print()
        print("   1. ユーザーID/メールアドレスを入力")
        print("   2. パスワードを入力")
        print("   3. 「ログインしたままにする」にチェック ★重要★")
        print("   4. ログインボタンをクリック")
        print()
        print("   ⏳ ログインを検知したら自動的にCookieを保存します...")
        print("=" * 60)
        print()
        
        # ログイン完了を自動検知（URLがloginから離れるまで待機）
        max_wait = 180  # 3分待機
        start_time = time.time()
        logged_in = False
        
        while time.time() - start_time < max_wait:
            await asyncio.sleep(2)
            current_url = page.url
            
            # ログインページから離れた = ログイン完了
            if 'login' not in current_url.lower():
                print(f"✅ ログイン検知！ URL: {current_url}")
                logged_in = True
                break
            # または、tk クッキーが設定された場合もログイン完了とみなす
            try:
                cookies = await context.cookies()
                for c in cookies:
                    if c.get('name') == 'tk':
                        print("✅ tkクッキー検出: ログイン完了とみなします")
                        logged_in = True
                        break
                if logged_in:
                    break
            except Exception:
                pass
            
            # 残り時間を表示
            elapsed = int(time.time() - start_time)
            remaining = max_wait - elapsed
            if elapsed % 10 == 0:
                print(f"   ⏳ 待機中... (残り{remaining}秒)")
        
        if not logged_in:
            print("❌ タイムアウト: ログインが検知されませんでした")
            await browser.close()
            return False
        
        # 少し待ってからCookieを取得
        await asyncio.sleep(2)
        
        # Cookieを取得
        cookies = await context.cookies()
        
        # tkクッキーを確認
        tk_cookie = None
        for c in cookies:
            if c.get('name') == 'tk':
                tk_cookie = c
                break
        
        if tk_cookie:
            exp = tk_cookie.get('expires', 0)
            now = time.time()
            remaining_days = (exp - now) / 86400
            print(f"\n✅ tkクッキー取得成功！")
            print(f"   有効期限: 約{remaining_days:.0f}日間")
            print(f"   （{remaining_days:.0f}日以内に再ログインすればID/パスワード不要）")
        else:
            print("\n⚠️ tkクッキーが見つかりません")
            print("   「ログインしたままにする」にチェックしましたか？")
        
        # Cookieを保存
        cookie_file = project_root / 'cookies.json'
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Cookieを保存しました: {cookie_file}")
        print(f"   保存されたCookie数: {len(cookies)}")
        
        # ログイン確認（馬の数で判定）
        print("\n🔍 ログイン状態を確認中...")
        
        # 今日のレースにアクセス
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        test_url = f"https://s.keibabook.co.jp/cyuou/syutuba/{today}0511"  # 阪神11R
        
        try:
            await page.goto(test_url, timeout=60000, wait_until='domcontentloaded')
            
            # 馬名リンクを数える
            horse_links = await page.query_selector_all('a[href*="/uma/"]')
            horse_count = len(horse_links)
            
            print(f"   検出された馬: {horse_count}頭")
            
            if horse_count >= 6:
                print("\n🎉 ログイン成功！全頭のデータを取得できます")
            elif 0 < horse_count <= 3:
                print("\n⚠️ 3頭のみ表示（ログインに問題がある可能性）")
            else:
                print("\n⚠️ レースデータが見つかりませんでした（開催日を確認してください）")
        except Exception as e:
            print(f"\n⚠️ 確認中にエラー: {e}")
        
        await browser.close()
    
    print("\n" + "=" * 60)
    print("完了！Streamlitアプリを再起動してスクレイピングを試してください")
    print("=" * 60)
    return True


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(manual_login())
