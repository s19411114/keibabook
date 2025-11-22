"""
地方競馬専用パーサー
ポイント情報、個別馬コメントなどを取得
"""
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LocalRacingParser:
    """地方競馬専用パーサー"""
    
    def parse_point_page(self, html_content: str) -> Dict[str, Any]:
        """
        ポイントページから情報を取得
        
        取得する情報:
        - 今日大穴空けた馬たち
        - 激走した馬たちのヒント
        - 血統からAIが予想した馬たち
        - パワー要る馬場があるみたいなオッズ百倍二百倍で掲示板や3着来た馬など
        
        Args:
            html_content: ポイントページのHTML
            
        Returns:
            ポイント情報データ
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        point_data = {
            'big_upset_horses': [],  # 今日大穴空けた馬たち
            'strong_run_hints': [],  # 激走した馬たちのヒント
            'ai_pedigree_picks': [],  # 血統からAIが予想した馬たち
            'power_track_horses': [],  # パワー要る馬場の馬（高オッズで3着など）
            'board_horses': []  # 掲示板の馬
        }
        
        # ポイント情報を探す（実際のHTML構造に応じて調整が必要）
        # セレクタは実際のHTML構造に合わせて調整
        
        # 大穴空けた馬たち
        upset_section = soup.select_one(".big_upset, .BigUpset, [class*='upset']")
        if upset_section:
            for item in upset_section.find_all(['div', 'li', 'tr'], class_=['horse', 'Horse']):
                horse_info = self._parse_horse_info(item)
                if horse_info:
                    point_data['big_upset_horses'].append(horse_info)
        
        # 激走した馬たちのヒント
        strong_run_section = soup.select_one(".strong_run, .StrongRun, [class*='strong']")
        if strong_run_section:
            for item in strong_run_section.find_all(['div', 'li', 'tr'], class_=['horse', 'Horse']):
                horse_info = self._parse_horse_info(item)
                if horse_info:
                    point_data['strong_run_hints'].append(horse_info)
        
        # 血統からAIが予想した馬たち
        ai_section = soup.select_one(".ai_pedigree, .AIPedigree, [class*='ai']")
        if ai_section:
            for item in ai_section.find_all(['div', 'li', 'tr'], class_=['horse', 'Horse']):
                horse_info = self._parse_horse_info(item)
                if horse_info:
                    point_data['ai_pedigree_picks'].append(horse_info)
        
        # パワー要る馬場の馬（高オッズで3着など）
        power_track_section = soup.select_one(".power_track, .PowerTrack, [class*='power']")
        if power_track_section:
            for item in power_track_section.find_all(['div', 'li', 'tr'], class_=['horse', 'Horse']):
                horse_info = self._parse_horse_info(item)
                if horse_info:
                    point_data['power_track_horses'].append(horse_info)
        
        # 掲示板の馬
        board_section = soup.select_one(".board, .Board, [class*='board']")
        if board_section:
            for item in board_section.find_all(['div', 'li', 'tr'], class_=['horse', 'Horse']):
                horse_info = self._parse_horse_info(item)
                if horse_info:
                    point_data['board_horses'].append(horse_info)
        
        logger.info(f"ポイント情報取得: 大穴{len(point_data['big_upset_horses'])}頭, "
                   f"激走{len(point_data['strong_run_hints'])}頭, "
                   f"AI予想{len(point_data['ai_pedigree_picks'])}頭")
        
        return point_data
    
    def parse_horse_comment(self, html_content: str, horse_num: str) -> Optional[str]:
        """
        個別馬のコメントを取得（穴馬のヒント）
        
        Args:
            html_content: 馬の詳細ページのHTML
            horse_num: 馬番
            
        Returns:
            コメント文字列（見つからない場合はNone）
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # コメントを探す（複数のセレクタパターンを試す）
        comment_selectors = [
            ".horse_comment", ".HorseComment", ".comment", ".Comment",
            "[class*='comment']", "[class*='Comment']"
        ]
        
        for selector in comment_selectors:
            comment_elem = soup.select_one(selector)
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                if comment_text:
                    logger.debug(f"馬{horse_num}のコメント取得: {comment_text[:50]}...")
                    return comment_text
        
        logger.debug(f"馬{horse_num}のコメントが見つかりませんでした")
        return None
    
    def _parse_horse_info(self, item) -> Optional[Dict[str, Any]]:
        """馬情報をパース"""
        horse_info = {}
        
        # 馬番
        horse_num_elem = item.select_one(".horse_num, .HorseNum, .umaban")
        if horse_num_elem:
            horse_info['horse_num'] = horse_num_elem.get_text(strip=True)
        
        # 馬名
        horse_name_elem = item.select_one(".horse_name, .HorseName, .kbamei a")
        if horse_name_elem:
            horse_info['horse_name'] = horse_name_elem.get_text(strip=True)
        
        # 理由・ヒント
        reason_elem = item.select_one(".reason, .Reason, .hint, .Hint")
        if reason_elem:
            horse_info['reason'] = reason_elem.get_text(strip=True)
        
        # オッズ（該当する場合）
        odds_elem = item.select_one(".odds, .Odds")
        if odds_elem:
            horse_info['odds'] = odds_elem.get_text(strip=True)
        
        return horse_info if horse_info else None

