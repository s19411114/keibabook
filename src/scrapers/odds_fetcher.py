"""
オッズ取得機能
南関東競馬公式サイトからオッズを取得
"""
import asyncio
import random
from datetime import datetime, time
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OddsFetcher:
    """オッズ取得クラス（南関東競馬公式サイト連携）"""
    
    # アクセスが少ない時間帯（深夜〜早朝）
    LOW_TRAFFIC_HOURS = list(range(0, 6)) + list(range(23, 24))
    
    def __init__(self, settings: Dict[str, Any]):
        """
        Args:
            settings: 設定辞書
        """
        self.settings = settings
        self.race_id = settings.get('race_id', '')
        self.race_type = settings.get('race_type', 'jra')
    
    async def fetch_odds(self, page: Page) -> Dict[str, Any]:
        """
        南関東競馬公式サイトからオッズを取得
        
        Args:
            page: Playwrightのページオブジェクト
            
        Returns:
            オッズデータ
        """
        try:
            # 南関東競馬公式サイトのURL（実際のURLに置き換えが必要）
            # 例: https://www.nankankeiba.com/odds/race/{race_id}
            if self.race_type == 'nar':
                odds_url = f"https://www.nankankeiba.com/odds/race/{self.race_id}"
            else:
                # 中央競馬の場合はJRA公式サイトなど
                odds_url = f"https://www.jra.go.jp/odds/race/{self.race_id}"
            
            # レート制御: ランダム待機
            await self._rate_limit_delay()
            
            await page.goto(odds_url, wait_until="domcontentloaded", timeout=30000)
            html_content = await page.content()
            
            # オッズをパース
            odds_data = self._parse_odds(html_content)
            odds_data['fetched_at'] = datetime.now().isoformat()
            odds_data['race_id'] = self.race_id
            
            logger.info(f"オッズ取得成功: {len(odds_data.get('horses', []))}頭")
            return odds_data
            
        except Exception as e:
            logger.error(f"オッズ取得エラー: {e}")
            return {}
    
    def _parse_odds(self, html_content: str) -> Dict[str, Any]:
        """
        HTMLからオッズをパース
        
        Args:
            html_content: HTMLコンテンツ
            
        Returns:
            オッズデータ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        odds_data = {
            'horses': []
        }
        
        # オッズテーブルを探す（実際のHTML構造に応じて調整が必要）
        odds_table = soup.select_one(".odds_table, .OddsTable, table.odds")
        
        if odds_table:
            for row in odds_table.find_all('tr'):
                horse_odds = self._parse_odds_row(row)
                if horse_odds:
                    odds_data['horses'].append(horse_odds)
        
        return odds_data
    
    def _parse_odds_row(self, row) -> Optional[Dict[str, Any]]:
        """オッズテーブルの1行をパース"""
        horse_odds = {}
        
        # 馬番
        horse_num_elem = row.select_one(".horse_num, .HorseNum, td.horse_num")
        if horse_num_elem:
            horse_odds['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 単勝オッズ
        win_odds_elem = row.select_one(".win_odds, .WinOdds, td.win_odds")
        if win_odds_elem:
            horse_odds['win_odds'] = win_odds_elem.get_text(strip=True)
        
        # 複勝オッズ
        place_odds_elem = row.select_one(".place_odds, .PlaceOdds, td.place_odds")
        if place_odds_elem:
            horse_odds['place_odds'] = place_odds_elem.get_text(strip=True)
        
        # 人気
        popularity_elem = row.select_one(".popularity, .Popularity, td.popularity")
        if popularity_elem:
            horse_odds['popularity'] = popularity_elem.get_text(strip=True)
        
        return horse_odds if horse_odds else None
    
    async def _rate_limit_delay(self):
        """
        レート制御: ランダム待機とアクセス少ない時間帯の考慮
        
        見えない心遣い: サイト負担を軽減
        """
        current_hour = datetime.now().hour
        
        # アクセスが少ない時間帯の場合は短めの待機
        if current_hour in self.LOW_TRAFFIC_HOURS:
            base_delay = 3  # 3秒
        else:
            base_delay = 10  # 10秒
        
        # ランダムな待機時間（±50%のばらつき）
        random_factor = random.uniform(0.5, 1.5)
        delay = base_delay * random_factor
        
        logger.debug(f"レート制御: {delay:.1f}秒待機")
        await asyncio.sleep(delay)
    
    @staticmethod
    def is_low_traffic_time() -> bool:
        """現在がアクセスが少ない時間帯かチェック"""
        current_hour = datetime.now().hour
        return current_hour in OddsFetcher.LOW_TRAFFIC_HOURS

