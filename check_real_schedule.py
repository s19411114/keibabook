#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡易スケジュール確認: 本日のレース有無を確認
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path


async def check_today_races():
    """本日のレース有無を直接確認"""
    
    print("=" * 70)
    print("本日のレース確認")
    print("=" * 70)
    
    today = datetime.now()
    print(f"日付: {today.year}年{today.month}月{today.day}日 ({['月','火','水','木','金','土','日'][today.weekday()]}曜日)")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. JRA公式カレンダー
        print("\n【1】JRA公式サイト確認")
        print("-" * 70)
        
        url = f"https://www.jra.go.jp/keiba/calendar/{today.year}/{today.month:02d}/"
        print(f"URL: {url}")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            content = await page.content()
            
            # HTML保存
            debug_file = Path(f"debug_files/jra_calendar_{today.year}{today.month:02d}.html")
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"HTML保存: {debug_file}")
            
            # 本日の日付を検索
            day_str = f"{today.day}日"
            if day_str in content:
                print(f"✓ 「{day_str}」がページに存在")
                
                # 会場名を検索
                venues = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]
                found_venues = []
                for venue in venues:
                    if venue in content:
                        # 会場の前後200文字を抽出
                        idx = content.find(venue)
                        context = content[max(0, idx-100):min(len(content), idx+300)]
                        
                        # 30日との関連性をチェック
                        if "30" in context or day_str in context:
                            found_venues.append(venue)
                
                if found_venues:
                    print(f"✓ 本日開催の可能性がある会場: {', '.join(found_venues)}")
                else:
                    print("✗ 本日開催の会場が見つかりません")
            else:
                print(f"✗ 「{day_str}」がページに見つかりません")
                
        except Exception as e:
            print(f"エラー: {e}")
        
        # 2. Netkeiba Today
        print("\n\n【2】Netkeiba 本日のレース")
        print("-" * 70)
        
        url = "https://race.netkeiba.com/top/"
        print(f"URL: {url}")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            content = await page.content()
            
            # HTML保存
            debug_file = Path("debug_files/netkeiba_today.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"HTML保存: {debug_file}")
            
            # 「本日のレース」「開催なし」などを検索
            if "開催なし" in content or "レースはありません" in content:
                print("✗ 本日は開催なし")
            elif "レース" in content:
                print("✓ レース情報がページに存在")
                
                # 会場名を検索
                venues = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]
                found_venues = [v for v in venues if v in content]
                
                if found_venues:
                    print(f"✓ 開催会場: {', '.join(found_venues)}")
                else:
                    print("? 会場名が見つかりません（地方競馬の可能性）")
            else:
                print("? レース情報の有無が不明")
                
        except Exception as e:
            print(f"エラー: {e}")
        
        await browser.close()
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    asyncio.run(check_today_races())
