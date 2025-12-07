# MIGRATION COPY: debug_schedule.py
# Origin: keibabook

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール取得の詳細デバッグ
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher
from src.scrapers.jra_schedule import JRAScheduleFetcher


async def debug_schedule():
    """各ソースから詳細なスケジュール情報を取得"""
    
    today = datetime.now().date()
    
    print("=" * 70)
    print(f"スケジュール取得詳細デバッグ: {today}")
    print("=" * 70)
    
    # 1. Netkeibaカレンダー
    print("\n【1】Netkeibaカレンダー")
    print("-" * 70)
    try:
        schedule = await NetkeibaCalendarFetcher.fetch_schedule_for_date(today)
        print(f"取得結果: {len(schedule)}会場")
        for venue_data in schedule:
            venue = venue_data.get('venue', '不明')
            races = venue_data.get('races', [])
            print(f"\n  {venue}: {len(races)}レース")
            if races:
                for race in races[:3]:  # 最初の3レースのみ
                    print(f"    {race.get('race_num')}R: {race.get('time', '不明')} - {race.get('race_name', '不明')}")
            else:
                print(f"    データ構造: {venue_data}")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. JRA公式スケジュール
    print("\n\n【2】JRA公式スケジュール")
    print("-" * 70)
    try:
        schedule = await JRAScheduleFetcher.fetch_schedule_for_date(today)
        print(f"取得結果: {len(schedule)}会場")
        for venue_data in schedule:
            venue = venue_data.get('venue', '不明')
            races = venue_data.get('races', [])
            print(f"\n  {venue}: {len(races)}レース")
            if races:
                for race in races[:3]:
                    print(f"    {race.get('race_num')}R: {race.get('time', '不明')} - {race.get('race_name', '不明')}")
            else:
                print(f"    データ構造: {venue_data}")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 生HTMLを保存して確認
    print("\n\n【3】HTML取得テスト")
    print("-" * 70)
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Netkeibaカレンダーページ
        url = "https://race.netkeiba.com/top/calendar.html?rf=sidemenu"
        print(f"URL: {url}")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        content = await page.content()
        
        # HTML保存
        debug_file = Path("debug_files/netkeiba_calendar_debug.html")
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"HTML保存: {debug_file}")
        
        # 本日の日付が含まれているか確認
        today_str = today.strftime("%m/%d")
        if today_str in content:
            print(f"✓ 本日の日付 {today_str} がHTML内に存在")
        else:
            print(f"✗ 本日の日付 {today_str} がHTML内に見つかりません")
        
        # カレンダーセルを確認
        cells = await page.query_selector_all('.RaceCellBox')
        print(f"\nカレンダーセル数: {len(cells)}個")
        
        for i, cell in enumerate(cells[:5], 1):  # 最初の5個のみ
            cell_html = await cell.inner_html()
            print(f"\nセル{i}:")
            print(cell_html[:200])  # 最初の200文字
        
        await browser.close()
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    asyncio.run(debug_schedule())
