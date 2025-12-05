#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ScheduleManagerクラス - 競馬スケジュールを複数ソースから取得

設計方針:
1. フォールバック機能: 複数のデータソースを優先順位付きで試行
2. 統一インターフェース: get_today_schedule() 1つで全ソースを試行
3. エラー耐性: 1つのソースが失敗しても次のソースを試す
4. ログ記録: どのソースが成功/失敗したかを記録

データソース優先順位:
- JRA (中央競馬):
  1. Netkeiba Calendar (負荷分散)
  2. JRA Official Calendar (公式)
  3. keiba.go.jp Today (最終手段)
  
- NAR (地方競馬):
  1. NAR Netkeiba Schedule
  2. keiba.go.jp Monthly Convene

使用例:
    manager = ScheduleManager()
    schedule = await manager.get_today_schedule()
    # -> [{'venue': '東京', 'races': [{'race_num': 1, 'time': '10:00'}, ...]}, ...]
"""

import asyncio
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher
from src.scrapers.jra_schedule import JRAScheduleFetcher
from src.scrapers.keiba_today import KeibaTodayFetcher
from src.scrapers.nar_schedule import NARScheduleFetcher
from src.scrapers.keiba_schedule import KeibaGovScheduleFetcher
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScheduleManager:
    """競馬スケジュールを複数ソースから取得するマネージャー"""
    
    def __init__(self):
        """初期化"""
        self.jra_sources = [
            ("Netkeiba Calendar", NetkeibaCalendarFetcher.fetch_schedule_for_date),
            ("JRA Official", JRAScheduleFetcher.fetch_schedule_for_date),
        ]
        
        self.nar_sources = [
            ("NAR Netkeiba", NARScheduleFetcher.fetch_schedule_for_date),
            ("keiba.go.jp", KeibaGovScheduleFetcher.fetch_schedule_for_date),
        ]
        
        self.today_sources = [
            ("keiba.go.jp Today", KeibaTodayFetcher.fetch_today_schedule),
        ]
    
    async def get_today_schedule(self, race_type: str = "all") -> List[Dict[str, Any]]:
        """
        本日のスケジュールを取得
        
        Args:
            race_type: "jra", "nar", or "all"
            
        Returns:
            スケジュールリスト [{'venue': '東京', 'races': [...]}, ...]
        """
        today = datetime.now().date()
        return await self.get_schedule_for_date(today, race_type)
    
    async def get_schedule_for_date(
        self, 
        target_date: date, 
        race_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        指定日のスケジュールを取得
        
        Args:
            target_date: 対象日付
            race_type: "jra", "nar", or "all"
            
        Returns:
            スケジュールリスト
        """
        logger.info(f"📅 スケジュール取得開始: {target_date} (type: {race_type})")
        
        schedule = []
        
        # JRAスケジュール取得
        if race_type in ["jra", "all"]:
            jra_schedule = await self._fetch_with_fallback(
                self.jra_sources, 
                target_date,
                "JRA"
            )
            if jra_schedule:
                schedule.extend(jra_schedule)
        
        # NARスケジュール取得
        if race_type in ["nar", "all"]:
            nar_schedule = await self._fetch_with_fallback(
                self.nar_sources, 
                target_date,
                "NAR"
            )
            if nar_schedule:
                schedule.extend(nar_schedule)
        
        # スケジュールが空なら本日情報APIを試す
        if not schedule:
            logger.warning("日付指定APIで取得失敗。本日情報APIを試行します。")
            for source_name, fetcher in self.today_sources:
                try:
                    logger.info(f"  🔄 {source_name} を試行中...")
                    today_schedule = await fetcher()
                    if today_schedule:
                        logger.info(f"  ✅ {source_name} 成功: {len(today_schedule)} 会場")
                        schedule = today_schedule
                        break
                except Exception as e:
                    logger.error(f"  ❌ {source_name} 失敗: {e}")
        
        logger.info(f"✅ スケジュール取得完了: {len(schedule)} 会場")
        return schedule
    
    async def _fetch_with_fallback(
        self, 
        sources: List[tuple], 
        target_date: date,
        source_type: str
    ) -> List[Dict[str, Any]]:
        """
        フォールバック付きでデータソースを試行
        
        Args:
            sources: [(name, fetcher_func), ...] のリスト
            target_date: 対象日付
            source_type: ソースタイプ（ログ用）
            
        Returns:
            スケジュールリスト
        """
        for source_name, fetcher in sources:
            try:
                logger.info(f"  🔄 {source_type} - {source_name} を試行中...")
                schedule = await fetcher(target_date)
                
                if schedule:
                    logger.info(f"  ✅ {source_type} - {source_name} 成功: {len(schedule)} 会場")
                    return schedule
                else:
                    logger.warning(f"  ⚠️ {source_type} - {source_name} データなし")
                    
            except Exception as e:
                logger.error(f"  ❌ {source_type} - {source_name} 失敗: {e}")
        
        logger.warning(f"❌ {source_type} 全ソース失敗")
        return []
    
    def generate_race_ids(
        self, 
        schedule: List[Dict[str, Any]], 
        target_date: date
    ) -> List[str]:
        """
        スケジュールからレースIDリストを生成
        
        Args:
            schedule: スケジュールリスト
            target_date: 対象日付
            
        Returns:
            レースIDリスト ["YYYYMMDDVVNN", ...]
        """
        race_ids = []
        
        for venue_data in schedule:
            venue = venue_data.get('venue', '不明')
            venue_code = self._get_venue_code(venue)
            races = venue_data.get('races', [])
            
            for race in races:
                race_num = race.get('race_num', 0)
                if race_num > 0:
                    # フォーマット: YYYYMMDDVVRR
                    race_id = (
                        f"{target_date.year:04d}{target_date.month:02d}{target_date.day:02d}"
                        f"{venue_code:02d}{race_num:02d}"
                    )
                    race_ids.append(race_id)
        
        logger.info(f"生成されたレースID: {len(race_ids)}件")
        return race_ids
    
    def _get_venue_code(self, venue_name: str) -> int:
        """
        会場名からコードを取得
        
        Args:
            venue_name: 会場名
            
        Returns:
            会場コード (数値)
        """
        # 簡易的な会場コードマッピング
        venue_codes = {
            '札幌': 1, '函館': 2, '福島': 3, '新潟': 4,
            '東京': 5, '中山': 6, '中京': 7, '京都': 8,
            '阪神': 9, '小倉': 10,
            # 地方競馬
            '門別': 30, '盛岡': 31, '水沢': 32, '浦和': 33,
            '船橋': 34, '大井': 35, '川崎': 36, '金沢': 37,
            '笠松': 38, '名古屋': 39, '園田': 40, '姫路': 41,
            '高知': 42, '佐賀': 43,
        }
        
        for key in venue_codes:
            if key in venue_name:
                return venue_codes[key]
        
        logger.warning(f"未知の会場: {venue_name} (コード0を割り当て)")
        return 0


# CLIテスト用
if __name__ == '__main__':
    async def test():
        manager = ScheduleManager()
        schedule = await manager.get_today_schedule("all")
        
        print(f"\n📅 本日のスケジュール ({len(schedule)} 会場):")
        print("-" * 60)
        for venue_data in schedule:
            venue = venue_data.get('venue', '不明')
            races = venue_data.get('races', [])
            print(f"\n🏇 {venue} ({len(races)} レース)")
            for race in races[:3]:  # 最初の3レースのみ表示
                print(f"  {race.get('race_num')}R: {race.get('time', '時刻不明')}")
        
        # レースID生成テスト
        race_ids = manager.generate_race_ids(schedule, datetime.now().date())
        print(f"\n🆔 生成されたレースID ({len(race_ids)}件):")
        print(race_ids[:5])  # 最初の5件のみ表示
    
    asyncio.run(test())
