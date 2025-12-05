"""Cookie確認スクリプト"""
import json
import time
from datetime import datetime

with open('cookies.json', 'r') as f:
    cookies = json.load(f)

print('=== Cookie一覧 ===')
for c in cookies:
    name = c.get('name')
    domain = c.get('domain')
    exp = c.get('expires', -1)
    
    if exp > 0:
        exp_date = datetime.fromtimestamp(exp)
        remaining = (exp - time.time()) / 86400
        if remaining > 0:
            status = f'{exp_date.strftime("%Y/%m/%d")} (残り{remaining:.0f}日)'
        else:
            status = 'EXPIRED'
    else:
        status = 'Session'
    
    print(f'  {name}: {status}')

# tk確認
tk = [c for c in cookies if c['name'] == 'tk']
if tk:
    exp = tk[0].get('expires', 0)
    remaining = (exp - time.time()) / 86400
    print(f'\n✅ tkクッキー: 残り約{remaining:.0f}日')
else:
    print('\n❌ tkクッキーがありません')
