"""
================================================================================
⚠️ 重要: このファイルを削除しないでください ⚠️
================================================================================

ログインヘルパースクリプト
Streamlitから別プロセスでログイン処理を実行

【使用方法】
python scripts/login_helper.py

【関連ファイル】
- src/utils/keibabook_auth.py: 認証モジュール（コア）
- src/utils/login.py: 基本ログインクラス
- scripts/test_login.py: ログイン診断ツール
- cookies.json: セッションCookie保存先

================================================================================
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.keibabook_auth import KeibaBookAuth
from src.utils.config import load_settings
from playwright.async_api import async_playwright


async def main():
    """ログイン処理を実行"""
    try:
        # 設定を読み込み
        settings = load_settings()
        login_id = settings.get('login_id')
        login_password = settings.get('login_password')
        cookie_file = settings.get('cookie_file', 'cookies.json')
        
        print("=" * 60)
        print("競馬ブック ログインヘルパー")
        print("=" * 60)
        
        # まずCookieの有効性を確認
        is_valid, status_msg = KeibaBookAuth.is_cookie_valid(cookie_file)
        print(f"\n📋 Cookie状態: {status_msg}")
        
        if is_valid:
            print("✅ Cookieは有効です。認証確認を行います...")
        
        async with async_playwright() as p:
            # ブラウザを起動
            print("\n🌐 ブラウザを起動中...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 認証を確保
            success, page = await KeibaBookAuth.ensure_authenticated(
                context=context,
                page=page,
                login_id=login_id,
                password=login_password,
                cookie_file=cookie_file,
                target_url=None  # 認証確認のみ
            )
            
            await browser.close()
            
            if success:
                print("\n" + "=" * 60)
                print("✅ ログイン成功！全頭データを取得できます")
                print("=" * 60)
                return 0
            else:
                print("\n" + "=" * 60)
                print("❌ ログイン失敗")
                if not login_id or not login_password:
                    print("\n⚠️ ログイン情報が設定されていません")
                    print("   config/settings.yml に以下を設定してください:")
                    print("   login_id: あなたのID")
                    print("   login_password: あなたのパスワード")
                print("=" * 60)
                return 1
    
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
