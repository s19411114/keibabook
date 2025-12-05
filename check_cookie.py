import json
from pathlib import Path
from datetime import datetime

cookie_file = Path('cookies.json')

if cookie_file.exists():
    cookies = json.loads(cookie_file.read_text())
    print(f"✅ Cookie存在: {len(cookies)}個")
    
    if cookies and 'expires' in cookies[0]:
        exp_time = datetime.fromtimestamp(cookies[0]['expires'])
        now = datetime.now()
        print(f"📅 有効期限: {exp_time.strftime('%Y-%m-%d %H:%M')}")
        
        if exp_time > now:
            print(f"✅ 有効 (残り {(exp_time - now).days}日)")
        else:
            print(f"❌ 期限切れ ({(now - exp_time).days}日前に失効)")
    else:
        print("⚠️ 期限情報なし")
else:
    print("❌ cookies.json が見つかりません")
