#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
統合テストスクリプト

スケジュール取得 → データベース保存 → レースデータ取得の一連の流れをテスト
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.schedule_manager import ScheduleManager
from src.scrapers.race_scraper import RaceScraper
from src.utils.db_manager import CSVDBManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_full_workflow():
    """
    完全なワークフローをテスト
    
    1. 本日のスケジュールを取得
    2. スケジュールをデータベースに保存
    3. 最初のレースデータを取得
    4. レースデータをJSONで保存
    """
    print("=" * 70)
    print("🚀 統合テスト開始: スケジュール取得 → DB保存 → レースデータ取得")
    print("=" * 70)
    
    # 1. スケジュール取得
    print("\n📅 STEP 1: 本日のスケジュール取得")
    print("-" * 70)
    
    schedule_manager = ScheduleManager()
    schedule = await schedule_manager.get_today_schedule("all")
    
    if not schedule:
        print("❌ スケジュール取得失敗。開催がない可能性があります。")
        return False
    
    print(f"✅ スケジュール取得成功: {len(schedule)} 会場")
    for venue_data in schedule:
        venue = venue_data.get('venue', '不明')
        races = venue_data.get('races', [])
        print(f"  🏇 {venue}: {len(races)} レース")
    
    # 2. データベースに保存
    print("\n💾 STEP 2: スケジュールをデータベースに保存")
    print("-" * 70)
    
    db_manager = CSVDBManager()
    today_str = datetime.now().strftime("%Y-%m-%d")
    db_manager.save_schedule(schedule, today_str)
    
    print(f"✅ スケジュール保存完了: {today_str}")
    
    # 3. レースID生成
    print("\n🆔 STEP 3: レースID生成")
    print("-" * 70)
    
    today_date = datetime.now().date()
    race_ids = schedule_manager.generate_race_ids(schedule, today_date)
    
    if not race_ids:
        print("❌ レースIDが生成できませんでした")
        return False
    
    print(f"✅ レースID生成完了: {len(race_ids)} 件")
    print(f"  サンプル: {race_ids[:5]}")
    
    # 4. 最初のレースデータを取得
    print("\n🐎 STEP 4: 最初のレースデータを取得")
    print("-" * 70)
    
    first_race_id = race_ids[0]
    print(f"対象レースID: {first_race_id}")
    
    scraper = RaceScraper()
    try:
        race_data = await scraper.scrape_race(first_race_id)
        
        if race_data:
            print(f"\n✅ レースデータ取得成功!")
            print(f"  レース名: {race_data.get('race_name', '不明')}")
            print(f"  出走馬数: {len(race_data.get('horses', []))}")
            print(f"  CPU予想数: {len(race_data.get('cpu_prediction', []))}")
            print(f"  URL: {race_data.get('url', '')}")
            print(f"  最終URL: {race_data.get('final_url', '')}")
            
            # CPU予想上位3頭を表示
            cpu_pred = race_data.get('cpu_prediction', [])
            if cpu_pred:
                print(f"\n  💡 CPU予想 TOP 3:")
                for i, pred in enumerate(cpu_pred[:3], 1):
                    print(f"    {i}位: {pred.get('horse_name', '不明')}")
            
            # JSONで保存
            import json
            output_dir = Path("data/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{first_race_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(race_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 JSONファイル保存: {output_file}")
            
        else:
            print("❌ レースデータ取得失敗")
            return False
            
    finally:
        await scraper.close()
    
    # 5. まとめ
    print("\n" + "=" * 70)
    print("✅ 統合テスト完了!")
    print("=" * 70)
    print(f"\n📊 結果サマリー:")
    print(f"  ・取得会場数: {len(schedule)}")
    print(f"  ・生成レースID数: {len(race_ids)}")
    print(f"  ・データベース: data/db/schedules.csv")
    print(f"  ・JSONファイル: data/json/{first_race_id}.json")
    print()
    
    return True


if __name__ == '__main__':
    success = asyncio.run(test_full_workflow())
    sys.exit(0 if success else 1)
