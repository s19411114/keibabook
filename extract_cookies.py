"""
Keibabook Cookie Extractor

このスクリプトは、ブラウザからKeibabookのCookieを抽出して保存します。
一度実行すれば、以降はログイン不要でスクレイピングできます。

使い方:
1. Chromeでhttps://s.keibabook.co.jp/ にログイン
2. このスクリプトを実行: python extract_cookies.py
3. cookies.json が生成されます
"""

import json
import browser_cookie3

def extract_keibabook_cookies():
    """ブラウザからKeibabookのCookieを抽出"""
    try:
        # Chromeからクッキーを取得
        cookies = browser_cookie3.chrome(domain_name='keibabook.co.jp')
        
        cookie_list = []
        for cookie in cookies:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'httpOnly': bool(cookie.has_nonstandard_attr('HttpOnly')),
                'secure': cookie.secure,
                'sameSite': 'Lax'  # デフォルト値
            }
            cookie_list.append(cookie_dict)
        
        # JSONファイルに保存
        with open('cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookie_list, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {len(cookie_list)}個のCookieを cookies.json に保存しました")
        print("これで run_scraper.py を実行すると、ログイン状態でスクレイピングできます")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("\n【トラブルシューティング】")
        print("1. Chromeでhttps://s.keibabook.co.jp/ にログインしていますか？")
        print("2. browser-cookie3 がインストールされていますか？")
        print("   インストール: pip install browser-cookie3")

if __name__ == "__main__":
    extract_keibabook_cookies()
