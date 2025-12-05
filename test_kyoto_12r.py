#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本日の京都12Rをテスト
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.race_scraper import RaceScraper
from src.utils.db_manager import CSVDBManager


async def test_kyoto_12r():
    """本日の京都12Rでテスト"""
    
    # 本日の日付から京都12RのレースIDを生成
    # フォーマット: YYYYMMDDVVRR (京都=08, 12R=12)
    today = datetime.now()
    race_id = f"{today.year:04d}{today.month:02d}{today.day:02d}0812"
    
    print("=" * 70)
    print(f"本日の京都12R データ取得テスト")
    print("=" * 70)
    print(f"日付: {today.year}年{today.month}月{today.day}日")
    print(f"レースID: {race_id}")
    print("-" * 70)
    
    scraper = RaceScraper()
    try:
        race_data = await scraper.scrape_race(race_id)
        
        if race_data:
            print(f"\nデータ取得成功!")
            print(f"  レース名: {race_data.get('race_name', '不明')}")
            print(f"  グレード: {race_data.get('grade', '不明')}")
            print(f"  距離: {race_data.get('distance', '不明')}")
            print(f"  出走馬数: {len(race_data.get('horses', []))}")
            print(f"  CPU予想数: {len(race_data.get('cpu_prediction', []))}")
            print(f"  元URL: {race_data.get('url', '')}")
            print(f"  最終URL: {race_data.get('final_url', '')}")
            
            # 出走馬一覧
            horses = race_data.get('horses', [])
            if horses:
                print(f"\n出走馬 ({len(horses)}頭):")
                for horse in horses:
                    print(f"  {horse.get('number', '?')}番: {horse.get('name', '不明')}")
            
            # CPU予想
            cpu_pred = race_data.get('cpu_prediction', [])
            if cpu_pred:
                print(f"\nCPU予想 TOP {min(5, len(cpu_pred))}:")
                for i, pred in enumerate(cpu_pred[:5], 1):
                    print(f"  {i}位: {pred.get('horse_name', '不明')}")
            
            # JSONで保存
            output_dir = Path("data/json")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{race_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(race_data, f, ensure_ascii=False, indent=2)
            
            print(f"\nJSONファイル保存: {output_file}")
            
            # データベースに保存
            db_manager = CSVDBManager()
            schedule_data = [{
                'venue': '京都',
                'race_type': 'jra',
                'races': [{
                    'race_num': 12,
                    'time': '',
                    'race_id': race_id
                }]
            }]
            
            today_str = today.strftime("%Y-%m-%d")
            db_manager.save_schedule(schedule_data, today_str)
            print(f"スケジュール保存: data/db/schedules.csv")
            
            print("\n" + "=" * 70)
            print("テスト完了!")
            print("=" * 70)
            return True
            
        else:
            print("\nデータ取得失敗")
            print("レースが存在しないか、Cookieが無効です。")
            return False
            
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await scraper.close()


if __name__ == '__main__':
    success = asyncio.run(test_kyoto_12r())
    sys.exit(0 if success else 1)
