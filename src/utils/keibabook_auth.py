"""
================================================================================
⚠️ 重要: このファイルを削除しないでください ⚠️
================================================================================

競馬ブックログイン管理モジュール (keibabook_auth.py)

このファイルはログイン問題の解決に不可欠です。
数日間かけて解決したログイン問題のコアロジックが含まれています。

【ログイン仕組み】
1. cookies.json からセッションCookieを読み込み
2. Playwrightコンテキストにcookieを適用
3. 出馬表ページにアクセスして馬の数で認証状態を確認
4. 3頭以下 = 未ログイン、6頭以上 = ログイン成功

【重要なポイント】
- tkクッキーが認証トークン（約30日間有効）
- ログインページでは「ログインしたままにする」チェックが重要
- Streamlit内ではPlaywrightが動かないため、別プロセスで実行

【関連ファイル】
- src/utils/login.py: 基本ログインクラス
- scripts/login_helper.py: Streamlit用ログインヘルパー
- scripts/test_login.py: ログイン診断ツール
 - scripts/login_diag.py: ログイン診断ツール
- cookies.json: セッションCookie保存先

================================================================================
"""

import asyncio
import json
import os
import time
from typing import Optional, Tuple
from pathlib import Path

from playwright.async_api import Page, BrowserContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeibaBookAuth:
    """
    競馬ブック認証管理クラス
    
    ⚠️ このクラスのメソッドを変更する際は十分注意してください
    """
    
    LOGIN_URL = "https://s.keibabook.co.jp/login/login"
    TOP_URL = "https://s.keibabook.co.jp/"
    
    # 認証確認用のテストURL（今日のレースがない場合でも使える）
    TEST_URLS = [
        "https://s.keibabook.co.jp/cyuou/nittei/top",  # 日程ページ
        "https://s.keibabook.co.jp/",  # トップページ
    ]
    
    @staticmethod
    def get_cookie_file_path(cookie_file: str = 'cookies.json') -> Path:
        """Cookieファイルのパスを取得"""
        return Path(cookie_file)
    
    @staticmethod
    def is_cookie_valid(cookie_file: str = 'cookies.json') -> Tuple[bool, str]:
        """
        Cookieファイルの有効性を確認
        
        Returns:
            (is_valid, message): 有効かどうかとメッセージ
        """
        path = KeibaBookAuth.get_cookie_file_path(cookie_file)
        
        if not path.exists():
            return False, "Cookieファイルが存在しません"
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if not cookies:
                return False, "Cookieが空です"
            
            # tkクッキーを確認（認証トークン）
            tk_cookie = None
            now = int(time.time())
            
            for c in cookies:
                if c.get('name') == 'tk':
                    tk_cookie = c
                    break
            
            if not tk_cookie:
                return False, "tkクッキーが見つかりません（再ログインが必要）"
            
            exp = tk_cookie.get('expires', 0)
            if exp and exp < now:
                return False, "tkクッキーの期限切れです"
            
            remaining_days = (exp - now) / 86400 if exp else 0
            return True, f"Cookie有効（残り{remaining_days:.1f}日）"
            
        except Exception as e:
            return False, f"Cookieファイル読み込みエラー: {e}"
    
    @staticmethod
    async def load_cookies(context: BrowserContext, cookie_file: str = 'cookies.json') -> bool:
        """
        CookieをPlaywrightコンテキストに読み込み
        
        ⚠️ これがログイン状態維持の核心部分
        """
        path = KeibaBookAuth.get_cookie_file_path(cookie_file)
        
        try:
            if not path.exists():
                logger.warning(f"Cookieファイルが存在しません: {path}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if not cookies:
                logger.warning("Cookieが空です")
                return False
            
            # Cookieをコンテキストに追加
            await context.add_cookies(cookies)
            logger.info(f"Cookieを読み込みました: {len(cookies)}個")
            return True
            
        except Exception as e:
            logger.error(f"Cookie読み込みエラー: {e}")
            return False
    
    @staticmethod
    async def save_cookies(context: BrowserContext, cookie_file: str = 'cookies.json') -> bool:
        """現在のCookieを保存"""
        try:
            cookies = await context.cookies()
            
            path = KeibaBookAuth.get_cookie_file_path(cookie_file)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cookieを保存しました: {len(cookies)}個 -> {path}")
            return True
            
        except Exception as e:
            logger.error(f"Cookie保存エラー: {e}")
            return False
    
    @staticmethod
    async def verify_login_by_horse_count(page: Page, test_url: str = None) -> Tuple[bool, int]:
        """
        馬の数でログイン状態を確認
        
        【重要】
        - 3頭以下 = 未ログイン（無料ユーザー制限）
        - 6頭以上 = ログイン済み
        
        Returns:
            (is_logged_in, horse_count)
        """
        if not test_url:
            # 今日のレースで確認（日付は動的に生成）
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            # 中山12R を試す (06=中山)
            test_url = f"https://s.keibabook.co.jp/cyuou/syutuba/{today}0612"
        
        try:
            logger.debug(f"馬の数でログイン確認: {test_url}")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)
            
            # 複数のパターンで馬の行を検出
            horse_count = 0
            
            # パターン1: HorseListテーブル
            rows = await page.query_selector_all('table.HorseList tbody tr')
            if rows:
                horse_count = len(rows)
            
            # パターン2: syutubaテーブルの行
            if horse_count == 0:
                rows = await page.query_selector_all('table.syutuba tbody tr')
                if rows:
                    horse_count = len(rows)
            
            # パターン2b: syutuba_spテーブルの行（実際のHTML構造で使用）
            if horse_count == 0:
                rows = await page.query_selector_all('table.syutuba_sp tbody tr')
                if rows:
                    horse_count = len(rows)
            
            # パターン3: 馬名リンク
            if horse_count == 0:
                links = await page.query_selector_all('a[href*="/uma/"]')
                if links:
                    # 重複を除去（馬名リンクが複数ある場合）
                    horse_count = len(links)
            
            # パターン4: 馬番セル
            if horse_count == 0:
                cells = await page.query_selector_all('td.Umaban, td.umaban')
                if cells:
                    horse_count = len(cells)
            
            logger.info(f"検出された馬の数: {horse_count}")
            
            # 補助チェック: ログアウトリンクや「ログアウト」文言があるかどうか
            logout_found = False
            try:
                logout_nodes = await page.query_selector_all('a[href*="logout"], a[class*="logout"], a[href*="/logout"]')
                if logout_nodes and len(logout_nodes) > 0:
                    logout_found = True
                else:
                    # ページ内のテキストに「ログアウト」があるかをチェック
                    page_html = await page.content()
                    if 'ログアウト' in page_html:
                        logout_found = True
            except Exception as e:
                logger.debug(f"ログアウト検出中にエラー: {e}")

            # 3頭以下は未ログイン。ただしログアウトリンクがあればログイン済みと判断
            is_logged_in = (horse_count >= 6) or logout_found
            
            return is_logged_in, horse_count
            
        except Exception as e:
            logger.error(f"馬の数確認エラー: {e}")
            return False, 0
    
    @staticmethod
    async def perform_login(
        page: Page,
        login_id: str,
        password: str,
        cookie_file: str = 'cookies.json'
    ) -> bool:
        """
        ログイン実行
        
        【重要なポイント】
        - 「ログインしたままにする」チェックボックスをON
        - ログイン成功後は「ログインしました」ページに遷移
        - Cookieを保存して次回から自動ログイン
        """
        try:
            logger.info(f"ログイン開始: {login_id[:3]}***")
            
            await page.goto(KeibaBookAuth.LOGIN_URL, wait_until='networkidle', timeout=60000)

            # Wait for input fields to appear and fill
            try:
                await page.wait_for_selector("input[name='login_id']", timeout=60000)
                await page.wait_for_selector("input[name='pswd']", timeout=60000)
            except Exception as e:
                logger.error(f"ログインフォーム要素の待機中にエラー: {e}")
                # デバッグHTMLを保存
                try:
                    debug_dir = Path('debug_files')
                    debug_dir.mkdir(exist_ok=True)
                    html = await page.content()
                    debug_file = debug_dir / 'debug_login_missing_inputs.html'
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    logger.info(f"ログインフォームが見つからないHTMLを保存しました: {debug_file}")
                except Exception as e:
                    logger.debug(f"デバッグHTML保存中の例外: {e}")
                raise

            # 認証情報を入力
            await page.fill("input[name='login_id']", login_id)
            await page.fill("input[name='pswd']", password)
            
            # 「ログインしたままにする」チェック（重要！）
            try:
                checkbox = await page.query_selector("input[name='autologin']")
                if checkbox:
                    await checkbox.check()
                    logger.debug("「ログインしたままにする」をチェック")
            except Exception as e:
                logger.warning(f"チェックボックス操作エラー: {e}")
            
            # ログインボタンをクリック
            await page.click("input[name='submitbutton']")
            
            # ページ遷移を待機
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            current_url = page.url
            logger.debug(f"ログイン後のURL: {current_url}")
            
            # ログインページから離れていれば成功
            if 'login' not in current_url.lower():
                logger.info("✅ ログイン成功！")
                
                # Cookieを保存
                await KeibaBookAuth.save_cookies(page.context, cookie_file)
                return True
            else:
                # 失敗時にデバッグ情報を保存
                logger.error("❌ ログイン失敗（まだログインページ） - デバッグ情報を保存します")
                try:
                    debug_dir = Path('debug_files')
                    debug_dir.mkdir(exist_ok=True)
                    html = await page.content()
                    debug_file = debug_dir / 'debug_login_failed.html'
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    logger.info(f"ログイン失敗時のHTMLを保存しました: {debug_file}")
                    # 検出可能な要素をログに記録
                    selectors_found = []
                    for sel in ["input[name='login_id']", "input[name='pswd']", "input[name='autologin']", "input[name='submitbutton']", "form"]:
                        try:
                            node = await page.query_selector(sel)
                            if node:
                                selectors_found.append(sel)
                        except Exception as e:
                            logger.debug(f"Selector検出中に例外が発生しました: {e}")
                    logger.info(f"検出されたセレクタ: {selectors_found}")
                except Exception as e:
                    logger.error(f"ログイン失敗デバッグの保存中にエラー: {e}")
                return False
                
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            return False
    
    @staticmethod
    async def ensure_authenticated(
        context: BrowserContext,
        page: Page = None,
            login_id: str = None,
            password: str = None,
        cookie_file: str = 'cookies.json',
        target_url: str = None
    ) -> Tuple[bool, Page]:
        """
        認証を確保（Cookieまたはログインで）
        
        ⚠️ スクレイパーから呼び出されるメインメソッド
        
        Args:
            context: Playwrightブラウザコンテキスト
            page: 使用するページ（Noneなら新規作成）
            login_id: ログインID（Cookie無効時に使用）
            password: パスワード（Cookie無効時に使用）
            cookie_file: Cookieファイルパス
            target_url: 最終的にアクセスするURL
        
        Returns:
            (is_authenticated, page): 認証成功かどうかとページオブジェクト
        """
        # ページが提供されていなければ作成
        created_page = False
        if page is None:
            page = await context.new_page()
            created_page = True
        
        try:
            # Step 1: Cookieを読み込み
            cookie_loaded = await KeibaBookAuth.load_cookies(context, cookie_file)
            
            if cookie_loaded:
                logger.info("Cookieを読み込みました。認証状態を確認...")
                
                # Step 2: 馬の数でログイン確認
                is_logged_in, horse_count = await KeibaBookAuth.verify_login_by_horse_count(
                    page, target_url
                )
                
                if is_logged_in:
                    logger.info(f"✅ Cookie認証成功（{horse_count}頭確認）")
                    return True, page
                else:
                    logger.warning(f"⚠️ Cookie認証失敗（{horse_count}頭のみ）")
            
            # Step 3: Cookieが無効な場合、ログインを試みる
            # If login_id/password not provided, fallback to environment variables
            if not login_id:
                login_id = os.getenv('LOGIN_ID') or os.getenv('KEIBABOOK_LOGIN_ID')
            if not password:
                password = os.getenv('LOGIN_PASSWORD') or os.getenv('KEIBABOOK_LOGIN_PASSWORD')
            if login_id and password:
                logger.info("認証情報でログインを試みます...")
                success = await KeibaBookAuth.perform_login(page, login_id, password, cookie_file)
                
                if success:
                    # 再度確認
                    is_logged_in, horse_count = await KeibaBookAuth.verify_login_by_horse_count(
                        page, target_url
                    )
                    if is_logged_in:
                        logger.info(f"✅ ログイン認証成功（{horse_count}頭確認）")
                        return True, page
            
            # Step 4: 認証失敗
            logger.error("❌ 認証失敗。無料範囲のデータのみ取得されます。")
            
            # ターゲットURLに遷移しておく
            if target_url:
                try:
                    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
                except Exception as e:
                    logger.debug(f"ターゲット遷移中にエラー: {e}")
            
            return False, page
            
        except Exception as e:
            logger.error(f"認証エラー: {e}")
            if created_page:
                try:
                    await page.close()
                except Exception as e:
                    logger.debug(f"ページクローズエラー: {e}")
                    pass
                return False, None
            return False, page


# 互換性のためのエイリアス
async def ensure_logged_in_with_verification(
    context: BrowserContext,
    page: Page = None,
    login_id: str = None,
    password: str = None,
    cookie_file: str = 'cookies.json',
    target_url: str = None
) -> Tuple[bool, Page]:
    """
    ensure_authenticated のエイリアス（互換性維持用）
    """
    return await KeibaBookAuth.ensure_authenticated(
        context, page, login_id, password, cookie_file, target_url
    )
