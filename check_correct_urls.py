#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
正しいURLでスケジュール確認
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


async def check_correct_urls():
    """正しいURLでスケジュールを確認"""
    
    print("=" * 70)
    print("正しいURLでスケジュール確認")
    print("=" * 70)
    
    today = datetime.now()
    print(f"日付: {today.year}年{today.month}月{today.day}日")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. JRA公式カレンダー（正しいURL）
        print("\n【1】JRA公式カレンダー")
        print("-" * 70)
        
        url = "https://www.jra.go.jp/keiba/calendar/"
        print(f"URL: {url}")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            content = await page.content()
            
            # HTML保存
            debug_file = Path("debug_files/jra_calendar_top.html")
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"HTML保存: {debug_file}")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 本日の開催情報を探す
            # 「30日」「11/30」「11月30日」などを検索
            day_patterns = [
                f"{today.day}日",
                f"{today.month}/{today.day}",
                f"{today.month}月{today.day}日"
            ]
            
            found = False
            for pattern in day_patterns:
                if pattern in content:
                    print(f"✓ 「{pattern}」がページに存在")
                    found = True
                    break
            
            if not found:
                print("✗ 本日の日付が見つかりません")
            
            # 会場名を検索
            venues = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]
            found_venues = []
            
            for venue in venues:
                if venue in content:
                    found_venues.append(venue)
            
            if found_venues:
                print(f"✓ ページ内の会場: {', '.join(found_venues)}")
            
            # テーブル構造を確認
            tables = soup.find_all('table')
            print(f"\nテーブル数: {len(tables)}")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. KeibaBook日程（正しいURL）
        print("\n\n【2】KeibaBook日程")
        print("-" * 70)
        
        url = "https://s.keibabook.co.jp/cyuou/nittei/top"
        print(f"URL: {url}")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            content = await page.content()
            
            # HTML保存
            debug_file = Path("debug_files/keibabook_nittei.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"HTML保存: {debug_file}")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 本日の日付を検索
            day_patterns = [
                f"{today.day}",
                f"{today.month}/{today.day}",
                "本日",
                "今日"
            ]
            
            found = False
            for pattern in day_patterns:
                if pattern in content:
                    print(f"✓ 「{pattern}」がページに存在")
                    found = True
            
            if not found:
                print("✗ 本日の日付が見つかりません")
            
            # 会場名を検索
            venues = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]
            found_venues = []
            
            for venue in venues:
                # 会場の周辺200文字を確認
                if venue in content:
                    idx = content.find(venue)
                    context_text = content[max(0, idx-100):min(len(content), idx+200)]
                    
                    # レース番号を検索（1R〜12R）
                    import re
                    races = re.findall(r'(\d{1,2})R', context_text)
                    
                    if races:
                        found_venues.append(f"{venue}({len(set(races))}R)")
                    else:
                        found_venues.append(venue)
            
            if found_venues:
                print(f"✓ 開催会場: {', '.join(found_venues)}")
            else:
                print("✗ 会場が見つかりません")
            
            # リンクを探す
            links = soup.find_all('a')
            race_links = []
            for link in links[:50]:  # 最初の50個のリンクを確認
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # レース番号を含むリンク
                if 'R' in text or '/cyuou/' in href:
                    race_links.append(f"{text} -> {href[:50]}")
            
            if race_links:
                print(f"\nレース関連リンク ({len(race_links)}個):")
                for rl in race_links[:10]:
                    print(f"  {rl}")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        
        await browser.close()
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    asyncio.run(check_correct_urls())
