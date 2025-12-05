#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本日の東京12RのレースIDをKeibaBookから直接取得"""

import sys
import asyncio
from datetime import datetime
sys.path.insert(0, 'src')

from scrapers.race_scraper import RaceScraper

async def find_race():
    # 本日の日付から考えられるレースID形式を試行
    today = datetime.now()
    
    # KeibaBookの形式: YYYYMMDD + 会場コード + レース番号
    # 東京: 05, 12R: 12
    race_id_pattern = f"{today.year}{today.month:02d}{today.day:02d}0512"
    
    print(f"🔍 試行するレースID: {race_id_pattern}")
    print(f"📅 日付: {today.year}年{today.month}月{today.day}日")
    print(f"🏇 会場: 東京 (コード: 05)")
    print(f"🏁 レース: 12R")
    print("-" * 60)
    
    scraper = RaceScraper()
    try:
        url = f"https://www.keibabook.co.jp/sp/shutuba.aspx?RaceID={race_id_pattern}"
        print(f"📍 URL: {url}")
        
        data = await scraper.scrape_race(race_id_pattern)
        
        if data:
            print(f"\n✅ レース発見!")
            print(f"レース名: {data.get('race_name', '不明')}")
            print(f"馬数: {len(data.get('horses', []))}")
            if data.get('cpu_prediction'):
                print(f"CPU予想馬数: {len(data['cpu_prediction'])}")
                print("\n🐎 CPU予想上位3頭:")
                for i, horse in enumerate(data['cpu_prediction'][:3], 1):
                    print(f"  {i}位: {horse.get('horse_name', '不明')}")
        else:
            print("❌ データ取得失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        await scraper.close()

if __name__ == '__main__':
    asyncio.run(find_race())
