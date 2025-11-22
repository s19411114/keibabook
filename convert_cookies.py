"""
Cookie形式変換スクリプト

EditThisCookie形式のCookieをPlaywright形式に変換します。
"""

import json

# EditThisCookie形式のCookieを読み込み
with open('cookies.json', 'r', encoding='utf-8') as f:
    edit_this_cookie_format = json.load(f)

# Playwright形式に変換
playwright_cookies = []
for cookie in edit_this_cookie_format:
    playwright_cookie = {
        'name': cookie['name'],
        'value': cookie['value'],
        'domain': cookie['domain'],
        'path': cookie['path'],
        'httpOnly': cookie.get('httpOnly', False),
        'secure': cookie.get('secure', False),
        'sameSite': cookie.get('sameSite', 'Lax')
    }
    
    # expirationDate を expires に変換（Unix timestamp）
    if 'expirationDate' in cookie:
        playwright_cookie['expires'] = int(cookie['expirationDate'])
    
    playwright_cookies.append(playwright_cookie)

# Playwright形式で保存
with open('cookies.json', 'w', encoding='utf-8') as f:
    json.dump(playwright_cookies, f, indent=2, ensure_ascii=False)

print(f"✅ {len(playwright_cookies)}個のCookieをPlaywright形式に変換しました")
