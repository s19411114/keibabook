"""
ログインテストスクリプト
⚠️ このファイルは削除しないでください - ログイン問題のデバッグに重要 ⚠️

競馬ブックのログイン状態を確認し、全頭データが取得できるかテストします。
3頭しか見れない = 未ログイン状態
全頭見れる = ログイン済み
"""
import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def test_login_with_cookies():
    """Cookieを使ってログイン状態をテスト"""
    cookie_file = project_root / 'cookies.json'
    
    print("=" * 60)
    print("競馬ブック ログインテスト")
    print("=" * 60)
    
    # Cookie確認
    if not cookie_file.exists():
        print("❌ cookies.json が見つかりません")
        return False
    
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"✅ Cookieファイル読み込み: {len(cookies)}個のCookie")
    
    # tkクッキーを確認
    tk_cookie = None
    for c in cookies:
        if c.get('name') == 'tk':
            tk_cookie = c
            import time
            exp = c.get('expires', 0)
            now = time.time()
            remaining_days = (exp - now) / 86400
            print(f"✅ tkクッキー発見: 残り {remaining_days:.1f}日")
            break
    
    if not tk_cookie:
        print("❌ tkクッキーが見つかりません - 再ログインが必要です")
        return False
    
    async with async_playwright() as p:
        print("\n🌐 ブラウザを起動中...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Cookieを読み込み
        print("🍪 Cookieを読み込み中...")
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # テスト1: トップページにアクセス
        print("\n📍 テスト1: トップページにアクセス...")
        await page.goto('https://s.keibabook.co.jp/', wait_until='domcontentloaded', timeout=60000)
        
        current_url = page.url
        print(f"   URL: {current_url}")
        
        if 'login' in current_url:
            print("   ❌ ログインページにリダイレクトされました")
        else:
            print("   ✅ ログインページにリダイレクトされていません")
        
        # テスト2: 出馬表ページにアクセスして馬の数を確認
        print("\n📍 テスト2: 出馬表ページで馬の数を確認...")
        
        # 今日のレースで確認（中山・阪神）
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        test_urls = [
            f'https://s.keibabook.co.jp/cyuou/syutuba/{today}0612',  # 中山12R
            f'https://s.keibabook.co.jp/cyuou/syutuba/{today}0512',  # 阪神12R
            f'https://s.keibabook.co.jp/cyuou/syutuba/{today}0611',  # 中山11R
            f'https://s.keibabook.co.jp/cyuou/syutuba/{today}0511',  # 阪神11R
        ]
        
        for test_url in test_urls:
            print(f"\n   試行: {test_url}")
            try:
                await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
                
                # ページ内容を確認
                content = await page.content()
                
                # HTMLをデバッグ保存
                with open('debug_files/debug_login_test.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                print(f"   📄 HTMLを debug_files/debug_login_test.html に保存")
                
                # 馬の行を数える（複数のパターン）
                horse_count = 0
                
                # パターン1: ShutubaTable の行（より正確）
                horse_rows = await page.query_selector_all('table.ShutubaTable tbody tr')
                if horse_rows:
                    horse_count = len(horse_rows)
                    print(f"   🐴 ShutubaTable形式: {horse_count}頭")
                
                # パターン2: syutubaテーブルの行
                if horse_count == 0:
                    horse_rows = await page.query_selector_all('table.syutuba tbody tr')
                    if horse_rows:
                        horse_count = len(horse_rows)
                        print(f"   🐴 syutuba形式: {horse_count}頭")
                
                # パターン3: 馬名リンクを数える
                if horse_count == 0:
                    horse_links = await page.query_selector_all('a[href*="/uma/"]')
                    if horse_links:
                        horse_count = len(horse_links)
                        print(f"   🐴 リンク形式: {horse_count}頭")
                
                if horse_count >= 6:
                    print(f"   ✅ 全頭データ取得可能！ ({horse_count}頭)")
                    await browser.close()
                    return True
                elif horse_count > 0 and horse_count <= 3:
                    print(f"   ❌ 3頭以下のみ = 未ログイン状態 ({horse_count}頭)")
                elif horse_count == 0:
                    print(f"   ⚠️ レースが見つからない、または開催なし")
                    
            except Exception as e:
                print(f"   ⚠️ エラー: {e}")
                continue
        
        await browser.close()
    
    print("\n" + "=" * 60)
    print("❌ ログイン状態の確認に失敗しました")
    print("   再ログインが必要かもしれません")
    print("=" * 60)
    return False


async def test_fresh_login():
    """新規ログインをテスト（設定ファイルから認証情報を取得）"""
    from src.utils.config import load_settings
    from src.utils.login import KeibaBookLogin
    
    settings = load_settings()
    login_id = settings.get('login_id')
    login_password = settings.get('login_password')
    
    if not login_id or not login_password:
        print("\n⚠️ 設定ファイルにログイン情報がありません")
        print("   config/settings.yml に login_id と login_password を設定してください")
        print("   または環境変数 LOGIN_ID, LOGIN_PASSWORD を設定してください")
        return False
    
    print(f"\n🔐 ログインを実行: {login_id[:3]}***")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 確認用にヘッドあり
        context = await browser.new_context()
        
        success = await KeibaBookLogin.ensure_logged_in(
            context, login_id, login_password,
            cookie_file='cookies.json', save_cookies=True
        )
        
        await browser.close()
        
        if success:
            print("✅ ログイン成功！Cookieを保存しました")
            return True
        else:
            print("❌ ログイン失敗")
            return False


async def main():
    print("\n" + "=" * 60)
    print("  競馬ブック ログイン診断ツール")
    print("=" * 60)
    
    # まずCookieでログイン状態を確認
    success = await test_login_with_cookies()
    
    if success:
        print("\n✅ ログイン状態OK！全頭データを取得できます")
        return 0
    
    # Cookieでダメな場合、新規ログインを試みる
    print("\n🔄 Cookieでのログインに失敗。新規ログインを試みます...")
    success = await test_fresh_login()
    
    if success:
        # 再度Cookie確認
        success = await test_login_with_cookies()
        if success:
            print("\n✅ 新規ログイン成功！全頭データを取得できます")
            return 0
    
    print("\n❌ ログインに失敗しました")
    print("   手動でブラウザからログインし、Cookieをエクスポートしてください")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
