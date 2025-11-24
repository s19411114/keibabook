#!/usr/bin/env python3
"""
重複チェック無効化機能を追加するスクリプト
"""
import re

# ファイルを読み込む
with open('/mnt/c/GeminiCLI/TEST/keibabook/src/scrapers/keibabook.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. __init__メソッドに skip_duplicate_check を追加
content = content.replace(
    "        self.race_type = settings.get('race_type', 'jra')  # 'jra' or 'nar'\n        self.db_manager = db_manager",
    "        self.race_type = settings.get('race_type', 'jra')  # 'jra' or 'nar'\n        self.skip_duplicate_check = settings.get('skip_duplicate_check', False)  # 重複チェックをスキップするか\n        self.db_manager = db_manager"
)

# 2. 全ての重複チェックを条件付きに変更
# パターン1: if self.db_manager and self.db_manager.is_url_fetched(
content = re.sub(
    r'if self\.db_manager and self\.db_manager\.is_url_fetched\(',
    r'if not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(',
    content
)

# パターン2: if not (self.db_manager and self.db_manager.is_url_fetched(
content = re.sub(
    r'if not \(self\.db_manager and self\.db_manager\.is_url_fetched\(',
    r'if not (not self.skip_duplicate_check and self.db_manager and self.db_manager.is_url_fetched(',
    content
)

# ファイルに書き込む
with open('/mnt/c/GeminiCLI/TEST/keibabook/src/scrapers/keibabook.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 重複チェック無効化機能を追加しました")
