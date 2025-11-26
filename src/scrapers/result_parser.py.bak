"""
結果ページパーサー
結果ページから詳細なレース情報を取得

取得項目（トラックバイアス分析用）:
- 着順、タイム、上がり、通過順位
- ラップタイム
- レース後コメント
- 次走へのメモ
- 払戻情報
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResultPageParser:
    """結果ページのパーサー"""
    
    def parse_result_page(self, html_content: str) -> Dict[str, Any]:
        """
        結果ページから詳細情報を取得
        
        取得項目（トラックバイアス分析用）:
        - レース基本情報
        - 着順、タイム、上がり、通過順位
        - ラップタイム
        - レース後コメント、次走メモ
        - 払戻情報
        
        Args:
            html_content: 結果ページのHTML
            
        Returns:
            レース結果データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result_data = {
            'race_info': {},
            'horses': [],
            'lap_times': [],
            'payouts': {},
            'race_comment': '',  # レース全体のコメント
            'corner_positions': {}  # コーナー通過順位
        }
        
        # レース基本情報
        result_data['race_info'] = self._parse_race_info(soup)
        
        # 着順・結果情報
        result_data['horses'] = self._parse_horse_results(soup)
        
        # ラップタイム（トラックバイアス分析用）
        result_data['lap_times'] = self._parse_lap_times(soup)
        
        # コーナー通過順位
        result_data['corner_positions'] = self._parse_corner_positions(soup)
        
        # 払戻情報
        result_data['payouts'] = self._parse_payouts(soup)
        
        # レース後コメント・回顧
        result_data['race_comment'] = self._parse_race_comment(soup)
        
        return result_data
    
    def _parse_race_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """レース基本情報を取得"""
        race_info = {}
        
        # レース名
        race_name_elem = soup.select_one(".race_name, .RaceName, .racemei")
        if race_name_elem:
            race_info['race_name'] = race_name_elem.get_text(strip=True)
        
        # 開催日、開催場所
        date_venue_elem = soup.select_one(".date_venue, .DateVenue, .racetitle_sub")
        if date_venue_elem:
            race_info['date_venue'] = date_venue_elem.get_text(strip=True)
        
        # 距離、コース、馬場状態
        course_info_elem = soup.select_one(".course_info, .CourseInfo, .racetitle_sub p")
        if course_info_elem:
            course_text = course_info_elem.get_text(strip=True)
            race_info['course_info'] = course_text
            
            # 距離を抽出
            distance_match = re.search(r'(\d+m)', course_text)
            if distance_match:
                race_info['distance'] = distance_match.group(1)
            
            # コース条件を抽出（ダート/芝、左右）
            course_match = re.search(r'\((.*?)\)', course_text)
            if course_match:
                race_info['course'] = course_match.group(1)
        
        # 天候、馬場状態
        weather_elem = soup.select_one(".weather, .Weather")
        if weather_elem:
            race_info['weather'] = weather_elem.get_text(strip=True)
        
        # 馬場状態を別途取得（良、稍重、重、不良）
        track_condition_elem = soup.select_one(".track_condition, .baba")
        if track_condition_elem:
            race_info['track_condition'] = track_condition_elem.get_text(strip=True)
        
        return race_info
    
    def _parse_horse_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """着順・結果情報を取得"""
        horses = []
        
        # 結果テーブルを探す
        results_table = soup.select_one(
            ".result_table tbody, .ResultTable tbody, table.result tbody, "
            "table.seiseki tbody, table[class*='result'], table[class*='seiseki']"
        )
        
        if not results_table:
            # keibabook形式を試す
            results_table = soup.select_one("table.default tbody")
        
        if results_table:
            for row in results_table.find_all('tr'):
                horse_data = self._parse_horse_result_row(row)
                if horse_data and (horse_data.get('horse_num') or horse_data.get('rank')):
                    horses.append(horse_data)
        
        return horses
    
    def _parse_horse_result_row(self, row) -> Optional[Dict[str, Any]]:
        """結果テーブルの1行をパース"""
        horse_data = {}
        
        # 着順
        rank_elem = row.select_one(".rank, .Rank, td.rank, .chakujun, td:first-child")
        if rank_elem:
            rank_text = rank_elem.get_text(strip=True)
            horse_data['rank'] = rank_text
            # 着順を数値化（1着、2着...）
            rank_num = re.search(r'(\d+)', rank_text)
            if rank_num:
                horse_data['rank_num'] = int(rank_num.group(1))
        
        # 枠番
        waku_elem = row.select_one(".waku, td.waku")
        if waku_elem:
            horse_data['waku'] = waku_elem.get_text(strip=True)
        
        # 馬番
        horse_num_elem = row.select_one(".horse_num, .HorseNum, td.horse_num, .umaban")
        if horse_num_elem:
            horse_data['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = row.select_one(".horse_name a, .HorseName a, td.horse_name a, .kbamei a")
        if horse_name_elem:
            horse_data['horse_name'] = horse_name_elem.get_text(strip=True)
            if horse_name_elem.has_attr('href'):
                horse_data['horse_link'] = horse_name_elem['href']
        
        # 騎手
        jockey_elem = row.select_one(".jockey, .Jockey, td.jockey, .kisyu a")
        if jockey_elem:
            horse_data['jockey'] = jockey_elem.get_text(strip=True)
        
        # タイム
        time_elem = row.select_one(".time, .Time, td.time")
        if time_elem:
            horse_data['time'] = time_elem.get_text(strip=True)
        
        # 着差
        margin_elem = row.select_one(".margin, .Margin, td.margin, .chakusa")
        if margin_elem:
            horse_data['margin'] = margin_elem.get_text(strip=True)
        
        # 通過順位
        passing_elem = row.select_one(".passing, .Passing, td.passing, .tuuka")
        if passing_elem:
            horse_data['passing'] = passing_elem.get_text(strip=True)
        
        # 上がり3F
        last_3f_elem = row.select_one(".last_3f, .Last3F, td.last_3f, .agari")
        if last_3f_elem:
            horse_data['last_3f'] = last_3f_elem.get_text(strip=True)
        
        # オッズ
        odds_elem = row.select_one(".odds, .Odds, td.odds")
        if odds_elem:
            odds_text = odds_elem.get_text(strip=True)
            horse_data['odds'] = odds_text
            try:
                horse_data['odds_num'] = float(re.search(r'[\d.]+', odds_text).group())
            except (AttributeError, ValueError):
                pass
        
        # 人気
        popularity_elem = row.select_one(".popularity, .Popularity, td.popularity, .ninki")
        if popularity_elem:
            pop_text = popularity_elem.get_text(strip=True)
            horse_data['popularity'] = pop_text
            try:
                horse_data['popularity_num'] = int(re.search(r'\d+', pop_text).group())
            except (AttributeError, ValueError):
                pass
        
        # 斤量
        weight_elem = row.select_one(".weight, .Weight, td.weight, .kinryo")
        if weight_elem:
            horse_data['weight'] = weight_elem.get_text(strip=True)
        
        # 馬体重
        horse_weight_elem = row.select_one(".horse_weight, .HorseWeight, .batai")
        if horse_weight_elem:
            horse_data['horse_weight'] = horse_weight_elem.get_text(strip=True)
        
        # レース後コメント
        race_comment_elem = row.select_one(".race_comment, .RaceComment, .comment")
        if race_comment_elem:
            horse_data['race_comment'] = race_comment_elem.get_text(strip=True)
        
        # 次走へのメモ
        next_memo_elem = row.select_one(".next_memo, .NextMemo, .jisou_memo")
        if next_memo_elem:
            horse_data['next_race_memo'] = next_memo_elem.get_text(strip=True)
        
        return horse_data if horse_data else None
    
    def _parse_lap_times(self, soup: BeautifulSoup) -> List[str]:
        """
        ラップタイムを取得（トラックバイアス分析用）
        
        Returns:
            ラップタイムのリスト（例: ["12.3", "11.5", "12.0", ...]）
        """
        lap_times = []
        
        # ラップタイムセクションを探す
        lap_section = soup.select_one(
            ".lap_times, .LapTimes, .lap, .Lap, "
            "table.lap tbody, [class*='lap']"
        )
        
        if lap_section:
            # テーブル形式の場合
            for td in lap_section.select("td"):
                lap_text = td.get_text(strip=True)
                if re.match(r'^\d+\.\d+$', lap_text):
                    lap_times.append(lap_text)
            
            # リスト形式の場合
            if not lap_times:
                lap_text = lap_section.get_text(strip=True)
                lap_times = re.findall(r'\d+\.\d+', lap_text)
        
        # 別のセレクタパターン
        if not lap_times:
            lap_row = soup.select_one("tr.lap, .lap_row")
            if lap_row:
                for td in lap_row.find_all("td"):
                    lap_text = td.get_text(strip=True)
                    if re.match(r'^\d+\.\d+$', lap_text):
                        lap_times.append(lap_text)
        
        logger.debug(f"ラップタイム取得: {lap_times}")
        return lap_times
    
    def _parse_corner_positions(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        コーナー通過順位を取得
        
        Returns:
            {"1コーナー": "1-2-3-4", "2コーナー": "1-2-3-4", ...}
        """
        corner_positions = {}
        
        # コーナー通過セクション
        corner_section = soup.select_one(
            ".corner_positions, .CornerPositions, "
            "[class*='corner'], .tuukajun"
        )
        
        if corner_section:
            for row in corner_section.select("tr, .item"):
                corner_name_elem = row.select_one("th, .corner_name")
                corner_value_elem = row.select_one("td, .corner_value")
                if corner_name_elem and corner_value_elem:
                    corner_positions[corner_name_elem.get_text(strip=True)] = corner_value_elem.get_text(strip=True)
        
        return corner_positions
    
    def _parse_race_comment(self, soup: BeautifulSoup) -> str:
        """
        レース全体のコメント・回顧を取得
        """
        comment = ""
        
        # レース回顧セクション
        comment_selectors = [
            ".race_comment", ".RaceComment", ".race_review",
            ".kaiko", ".review", "[class*='comment']"
        ]
        
        for selector in comment_selectors:
            comment_elem = soup.select_one(selector)
            if comment_elem:
                comment = comment_elem.get_text(strip=True)
                if comment and len(comment) > 20:  # 十分な長さがあれば採用
                    break
        
        return comment
    
    def _parse_payouts(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """払戻情報を取得"""
        payouts = {}
        
        # 払戻テーブルを探す
        payout_table = soup.select_one(
            ".payout_table, .PayoutTable, table.haraimodoshi, "
            "[class*='payout'], [class*='haraimodoshi']"
        )
        
        if payout_table:
            for row in payout_table.select("tr"):
                type_elem = row.select_one("th, .type, td:first-child")
                value_elem = row.select_one("td.value, td:nth-child(2)")
                horse_elem = row.select_one("td.horse, td:nth-child(3)")
                
                if type_elem:
                    payout_type = type_elem.get_text(strip=True)
                    payout_value = value_elem.get_text(strip=True) if value_elem else ""
                    payout_horse = horse_elem.get_text(strip=True) if horse_elem else ""
                    
                    # 種類ごとに整理
                    if "単勝" in payout_type:
                        payouts['win'] = {'value': payout_value, 'horse': payout_horse}
                    elif "複勝" in payout_type:
                        if 'place' not in payouts:
                            payouts['place'] = []
                        payouts['place'].append({'value': payout_value, 'horse': payout_horse})
                    elif "枠連" in payout_type:
                        payouts['bracket_quinella'] = {'value': payout_value, 'horse': payout_horse}
                    elif "馬連" in payout_type:
                        payouts['quinella'] = {'value': payout_value, 'horse': payout_horse}
                    elif "ワイド" in payout_type:
                        if 'wide' not in payouts:
                            payouts['wide'] = []
                        payouts['wide'].append({'value': payout_value, 'horse': payout_horse})
                    elif "馬単" in payout_type:
                        payouts['exacta'] = {'value': payout_value, 'horse': payout_horse}
                    elif "三連複" in payout_type:
                        payouts['trio'] = {'value': payout_value, 'horse': payout_horse}
                    elif "三連単" in payout_type:
                        payouts['trifecta'] = {'value': payout_value, 'horse': payout_horse}
        
        # 別のパターン（単純なセレクタ）
        if not payouts:
            win_elem = soup.select_one(".win_payout, .WinPayout")
            if win_elem:
                payouts['win'] = win_elem.get_text(strip=True)
            
            place_elem = soup.select_one(".place_payout, .PlacePayout")
            if place_elem:
                payouts['place'] = place_elem.get_text(strip=True)
        
        return payouts

