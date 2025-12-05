#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
統合テスト: 過去の有効な日付でテスト
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.schedule_manager import ScheduleManager
from src.scrapers.race_scraper import RaceScraper
from src.utils.db_manager import CSVDBManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_with_specific_race():
    """既知のレースIDで直接テスト"""
    print("=" * 70)
    print("🚀 統合テスト: 既知のレースIDでデータ取得")
    print("=" * 70)
    
    # 既知の有効なレースID（data/json/に存在するもの）
    test_race_id = "202505040611"  # 福島5R
    
    print(f"\n🐎 テスト対象: {test_race_id}")
    print("-" * 70)
    
    # 1. RaceScraperでデータ取得
    scraper = RaceScraper()
    try:
        race_data = await scraper.scrape_race(test_race_id)
        
        if race_data:
            print(f"\n✅ レースデータ取得成功!")
            print(f"  レースID: {race_data.get('race_id', '不明')}")
            print(f"  レース名: {race_data.get('race_name', '不明')}")
            print(f"  出走馬数: {len(race_data.get('horses', []))}")
            print(f"  CPU予想数: {len(race_data.get('cpu_prediction', []))}")
            
            # CPU予想を表示
            cpu_pred = race_data.get('cpu_prediction', [])
            if cpu_pred:
                print(f"\n  💡 CPU予想 TOP 5:")
                for i, pred in enumerate(cpu_pred[:5], 1):
                    print(f"    {i}位: {pred.get('horse_name', '不明')}")
            
            # 出走馬を表示
            horses = race_data.get('horses', [])
            if horses:
                print(f"\n  🐴 出走馬 ({len(horses)}頭):")
                for horse in horses[:5]:
                    print(f"    {horse.get('number', '?')}番: {horse.get('name', '不明')}")
                if len(horses) > 5:
                    print(f"    ... 他{len(horses)-5}頭")
            
            # JSONで保存
            import json
            output_dir = Path("data/json/test")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{test_race_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(race_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 JSONファイル保存: {output_file}")
            
            # 2. データベースに保存テスト
            print(f"\n💾 データベース保存テスト")
            print("-" * 70)
            
            db_manager = CSVDBManager()
            
            # スケジュールデータを作成
            schedule_data = [{
                'venue': '福島',
                'race_type': 'jra',
                'races': [{
                    'race_num': 6,
                    'time': '11:25',
                    'race_id': test_race_id
                }]
            }]
            
            db_manager.save_schedule(schedule_data, "2025-05-04")
            print("✅ スケジュール保存完了")
            
            print("\n" + "=" * 70)
            print("✅ 統合テスト完了!")
            print("=" * 70)
            return True
            
        else:
            print("❌ レースデータ取得失敗")
            return False
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await scraper.close()


if __name__ == '__main__':
    success = asyncio.run(test_with_specific_race())
    sys.exit(0 if success else 1)
