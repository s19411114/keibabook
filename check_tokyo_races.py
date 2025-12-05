#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""今日の東京競馬場のレースID一覧を取得"""

import sys
import asyncio
from datetime import datetime
sys.path.insert(0, 'src')

from scrapers.jra_schedule import JRAScheduleFetcher

async def get_tokyo_races():
    today = datetime(2025, 11, 30).date()
    schedule = await JRAScheduleFetcher.fetch_schedule_for_date(today)
    
    print(f"📅 {today} 東京競馬場のレース:")
    print("-" * 60)
    
    for race in schedule:
        if '東京' in race.get('venue', ''):
            print(f"{race['race_number']:2d}R: {race['race_id']:20s} - {race.get('race_name', '不明')}")

if __name__ == '__main__':
    asyncio.run(get_tokyo_races())
