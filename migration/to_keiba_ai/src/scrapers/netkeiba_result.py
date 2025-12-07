# MIGRATION COPY: src/scrapers/netkeiba_result.py
# Origin: keibabook

"""
Netkeiba結果ページスクレイパー
レース結果とトラックバイアス分析用データを取得
"""
import asyncio
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger
from src.scrapers.result_parser import ResultPageParser
from src.utils.track_bias import TrackBiasAnalyzer

logger = get_logger(__name__)


class NetkeibaResultScraper:
    """Netkeiba結果ページスクレイパー"""
    
    BASE_URL = "https://race.netkeiba.com/race/result.html"
    
    def __init__(self, headless: bool = True):
        """
        初期化
        
        Args:
            headless: ヘッドレスモードで実行するか
        """
        self.headless = headless
        self.parser = ResultPageParser()
        self.bias_analyzer = TrackBiasAnalyzer()
    
    async def fetch_result(self, race_id: str) -> Dict[str, Any]:
        """
        レース結果を取得
        
        Args:
            race_id: レースID（例: "202508040611"）
            
        Returns:
            レース結果データ（トラックバイアス指数含む）
        """
        url = f"{self.BASE_URL}?race_id={race_id}"
        logger.info(f"Netkeiba結果取得開始: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # ページ取得
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # レンダリング待機
                
                # HTMLを取得
                html_content = await page.content()
                
                # パース
                result_data = self._parse_result_page(html_content)
                
                # トラックバイアス指数を計算
                if result_data and result_data.get('horses'):
                    bias_index = self.bias_analyzer.calculate_bias_index(result_data)
                    result_data['track_bias'] = bias_index
                    logger.info(f"トラックバイアス: {bias_index['bias_type']}")
                
                return result_data
                
            except Exception as e:
                logger.error(f"Netkeiba結果取得エラー: {e}")
                return {}
            finally:
                await browser.close()
    
    def _parse_result_page(self, html_content: str) -> Dict[str, Any]:
        """
        結果ページをパース
        
        Args:
            html_content: HTML
            
        Returns:
            パース済みデータ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result_data = {
            'race_info': {},
            'horses': [],
            'payouts': {},
            'track_bias': {}
        }
        
        # レース情報
        result_data['race_info'] = self._parse_race_info(soup)
        
        # 着順結果（上位6頭を優先的に取得）
        result_data['horses'] = self._parse_horses(soup)
        
        # 払戻情報
        result_data['payouts'] = self._parse_payouts(soup)
        
        logger.info(f"結果パース完了: {len(result_data['horses'])}頭")
        
        return result_data
    
    def _parse_race_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """レース情報をパース"""
        race_info = {}
        
        # レース名
        race_name = soup.select_one(".RaceName, .racedata .RaceName")
        if race_name:
            race_info['race_name'] = race_name.get_text(strip=True)
        
        # 開催情報
        race_data1 = soup.select_one(".RaceData01, .racedata .RaceData01")
        if race_data1:
            race_info['race_data'] = race_data1.get_text(strip=True)
        
        # 馬場状態・天候
        race_data2 = soup.select_one(".RaceData02, .racedata .RaceData02")
        if race_data2:
            race_info['conditions'] = race_data2.get_text(strip=True)
        
        return race_info
    
    def _parse_horses(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """着順結果をパース"""
        horses = []
        
        # 結果テーブルを探す
        result_table = soup.select_one("table.race_table_01, table.ResultTable")
        
        if not result_table:
            logger.warning("結果テーブルが見つかりません")
            return horses
        
        tbody = result_table.find('tbody')
        if not tbody:
            logger.warning("tbody が見つかりません")
            return horses
        
        # 各行をパース
        for row in tbody.find_all('tr'):
            horse_data = self._parse_horse_row(row)
            if horse_data:
                horses.append(horse_data)
        
        logger.debug(f"パース完了: {len(horses)}頭")
        
        return horses
    
    def _parse_horse_row(self, row) -> Optional[Dict[str, Any]]:
        """1行の馬データをパース"""
        horse_data = {}
        
        tds = row.find_all('td')
        if len(tds) < 10:
            return None
        
        try:
            # 着順（0列目）
            rank_elem = tds[0]
            horse_data['rank'] = rank_elem.get_text(strip=True)
            
            # 枠番（1列目）
            frame_elem = tds[1]
            horse_data['frame_num'] = frame_elem.get_text(strip=True)
            
            # 馬番（2列目）
            horse_num_elem = tds[2]
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
            
            # 馬名（3列目）
            horse_name_elem = tds[3].find('a')
            if horse_name_elem:
                horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
            
            # 性齢（4列目）
            sex_age_elem = tds[4]
            horse_data['sex_age'] = sex_age_elem.get_text(strip=True)
            
            # 斤量（5列目）
            weight_elem = tds[5]
            horse_data['weight'] = weight_elem.get_text(strip=True)
            
            # 騎手（6列目）
            jockey_elem = tds[6].find('a')
            if jockey_elem:
                horse_data['jockey'] = jockey_elem.get_text(strip=True)
            
            # タイム（7列目）
            time_elem = tds[7]
            horse_data['time'] = time_elem.get_text(strip=True)
            
            # 着差（8列目）
            margin_elem = tds[8]
            horse_data['margin'] = margin_elem.get_text(strip=True)
            
            # 通過順位（10列目）
            if len(tds) > 10:
                passing_elem = tds[10]
                horse_data['passing'] = passing_elem.get_text(strip=True)
            
            # 上がり3F（11列目）
            if len(tds) > 11:
                last_3f_elem = tds[11]
                horse_data['last_3f'] = last_3f_elem.get_text(strip=True)
            
            # 単勝オッズ（12列目）
            if len(tds) > 12:
                odds_elem = tds[12]
                horse_data['odds'] = odds_elem.get_text(strip=True)
            
            # 人気（13列目）
            if len(tds) > 13:
                popularity_elem = tds[13]
                horse_data['popularity'] = popularity_elem.get_text(strip=True)
            
            return horse_data
            
        except Exception as e:
            logger.error(f"馬データパースエラー: {e}")
            return None
    
    def _parse_payouts(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """払戻情報をパース"""
        payouts = {}
        
        # 払戻テーブルを探す
        payout_table = soup.select_one("table.pay_table_01, table.PayoutTable")
        
        if not payout_table:
            return payouts
        
        # 各払戻タイプをパース
        for row in payout_table.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            
            if th and td:
                payout_type = th.get_text(strip=True)
                payout_value = td.get_text(strip=True)
                payouts[payout_type] = payout_value
        
        return payouts
