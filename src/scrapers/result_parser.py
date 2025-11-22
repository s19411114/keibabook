"""
結果ページパーサー
結果ページから詳細なレース情報を取得
"""
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResultPageParser:
    """結果ページのパーサー"""
    
    def parse_result_page(self, html_content: str) -> Dict[str, Any]:
        """
        結果ページから詳細情報を取得
        
        Args:
            html_content: 結果ページのHTML
            
        Returns:
            レース結果データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result_data = {
            'race_info': {},
            'horses': [],
            'payouts': {}
        }
        
        # レース基本情報
        result_data['race_info'] = self._parse_race_info(soup)
        
        # 着順・結果情報
        result_data['horses'] = self._parse_horse_results(soup)
        
        # 払戻情報
        result_data['payouts'] = self._parse_payouts(soup)
        
        return result_data
    
    def _parse_race_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """レース基本情報を取得"""
        race_info = {}
        
        # レース名
        race_name_elem = soup.select_one(".race_name, .RaceName")
        if race_name_elem:
            race_info['race_name'] = race_name_elem.get_text(strip=True)
        
        # 開催日、開催場所
        date_venue_elem = soup.select_one(".date_venue, .DateVenue")
        if date_venue_elem:
            race_info['date_venue'] = date_venue_elem.get_text(strip=True)
        
        # 距離、コース、馬場状態
        course_info_elem = soup.select_one(".course_info, .CourseInfo")
        if course_info_elem:
            race_info['course_info'] = course_info_elem.get_text(strip=True)
        
        # 天候、馬場状態
        weather_elem = soup.select_one(".weather, .Weather")
        if weather_elem:
            race_info['weather'] = weather_elem.get_text(strip=True)
        
        return race_info
    
    def _parse_horse_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """着順・結果情報を取得"""
        horses = []
        
        # 結果テーブルを探す（実際のHTML構造に応じて調整が必要）
        results_table = soup.select_one(".result_table tbody, .ResultTable tbody, table.result tbody")
        
        if not results_table:
            # 別のセレクタを試す
            results_table = soup.select_one("table[class*='result'], table[class*='Result']")
            if results_table:
                results_table = results_table.find('tbody')
        
        if results_table:
            for row in results_table.find_all('tr'):
                horse_data = self._parse_horse_result_row(row)
                if horse_data:
                    horses.append(horse_data)
        
        return horses
    
    def _parse_horse_result_row(self, row) -> Dict[str, Any]:
        """結果テーブルの1行をパース"""
        horse_data = {}
        
        # 着順
        rank_elem = row.select_one(".rank, .Rank, td.rank")
        if rank_elem:
            horse_data['rank'] = rank_elem.get_text(strip=True)
        
        # 馬番
        horse_num_elem = row.select_one(".horse_num, .HorseNum, td.horse_num")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = row.select_one(".horse_name a, .HorseName a, td.horse_name a")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
            if horse_name_elem.has_attr('href'):
                horse_data['horse_link'] = horse_name_elem['href']
        
        # 騎手
        jockey_elem = row.select_one(".jockey, .Jockey, td.jockey")
        if jockey_elem:
            horse_data['jockey'] = jockey_elem.get_text(strip=True)
        
        # タイム
        time_elem = row.select_one(".time, .Time, td.time")
        if time_elem:
            horse_data['time'] = time_elem.get_text(strip=True)
        
        # 着差
        margin_elem = row.select_one(".margin, .Margin, td.margin")
        if margin_elem:
            horse_data['margin'] = margin_elem.get_text(strip=True)
        
        # 通過順位
        passing_elem = row.select_one(".passing, .Passing, td.passing")
        if passing_elem:
            horse_data['passing'] = passing_elem.get_text(strip=True)
        
        # 上がり
        last_3f_elem = row.select_one(".last_3f, .Last3F, td.last_3f")
        if last_3f_elem:
            horse_data['last_3f'] = last_3f_elem.get_text(strip=True)
        
        # オッズ
        odds_elem = row.select_one(".odds, .Odds, td.odds")
        if odds_elem:
            horse_data['odds'] = odds_elem.get_text(strip=True)
        
        # 人気
        popularity_elem = row.select_one(".popularity, .Popularity, td.popularity")
        if popularity_elem:
            horse_data['popularity'] = popularity_elem.get_text(strip=True)
        
        # 斤量
        weight_elem = row.select_one(".weight, .Weight, td.weight")
        if weight_elem:
            horse_data['weight'] = weight_elem.get_text(strip=True)
        
        return horse_data if horse_data else None
    
    def _parse_payouts(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """払戻情報を取得"""
        payouts = {}
        
        # 単勝
        win_elem = soup.select_one(".win_payout, .WinPayout")
        if win_elem:
            payouts['win'] = win_elem.get_text(strip=True)
        
        # 複勝
        place_elem = soup.select_one(".place_payout, .PlacePayout")
        if place_elem:
            payouts['place'] = place_elem.get_text(strip=True)
        
        # 馬連
        exacta_elem = soup.select_one(".exacta_payout, .ExactaPayout")
        if exacta_elem:
            payouts['exacta'] = exacta_elem.get_text(strip=True)
        
        # ワイド
        wide_elem = soup.select_one(".wide_payout, .WidePayout")
        if wide_elem:
            payouts['wide'] = wide_elem.get_text(strip=True)
        
        # 三連複
        trifecta_elem = soup.select_one(".trifecta_payout, .TrifectaPayout")
        if trifecta_elem:
            payouts['trifecta'] = trifecta_elem.get_text(strip=True)
        
        # 三連単
        trio_elem = soup.select_one(".trio_payout, .TrioPayout")
        if trio_elem:
            payouts['trio'] = trio_elem.get_text(strip=True)
        
        return payouts

