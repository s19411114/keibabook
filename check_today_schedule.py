#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュールマネージャーのテスト: 本日の全レースを確認
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.schedule_manager import ScheduleManager


async def main():
    manager = ScheduleManager()
    schedule = await manager.get_today_schedule("all")
    
    print("\n本日の開催情報")
    print("=" * 70)
    print(f"日付: {datetime.now().strftime('%Y年%m月%d日')}")
    print(f"取得会場数: {len(schedule)}")
    print("=" * 70)
    
    if not schedule:
        print("\n本日は開催がありません")
        return
    
    for venue_data in schedule:
        venue = venue_data.get('venue', '不明')
        races = venue_data.get('races', [])
        
        print(f"\n【{venue}】 {len(races)}レース")
        if races:
            for race in races:
                print(f"  {race.get('race_num')}R: {race.get('time', '時刻不明')}")
        else:
            print("  (レース情報なし)")


if __name__ == '__main__':
    asyncio.run(main())
