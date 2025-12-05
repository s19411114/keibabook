#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KeibaBookスケジュールフェッチャーのテスト
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.keibabook_schedule import KeibaBookScheduleFetcher


async def test():
    today = datetime.now().date()
    schedule = await KeibaBookScheduleFetcher.fetch_schedule_for_date(today)
    
    print(f"\n本日のスケジュール ({today}):")
    print("=" * 60)
    
    for venue_data in schedule:
        venue = venue_data['venue']
        races = venue_data['races']
        print(f"\n{venue} ({len(races)}レース):")
        for race in races:
            print(f"  {race['race_num']}R: {race['race_name']} (ID: {race['race_id']})")


if __name__ == '__main__':
    asyncio.run(test())
