"""
レコメンド機能
過小評価馬の検出など
"""
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HorseRecommender:
    """馬のレコメンド機能"""
    
    def __init__(self, db_manager):
        """
        Args:
            db_manager: CSVDBManagerインスタンス
        """
        self.db_manager = db_manager
    
    def find_undervalued_horses(self, race_data: Dict[str, Any], threshold_rank: float = 0.7, min_odds: float = 50.0) -> List[Dict[str, Any]]:
        """
        過小評価馬を検出
        
        条件:
        - 前走上位7割以内（threshold_rank * 頭数）
        - 現在のオッズが高い（min_odds倍以上）
        
        Args:
            race_data: レースデータ
            threshold_rank: 上位何割以内か（デフォルト0.7 = 7割）
            min_odds: 最低オッズ（デフォルト50倍）
            
        Returns:
            過小評価馬のリスト
        """
        undervalued_horses = []
        
        horses = race_data.get('horses', [])
        if not horses:
            return undervalued_horses
        
        total_horses = len(horses)
        threshold_position = int(total_horses * threshold_rank)
        
        for horse in horses:
            # 前走の着順を取得
            past_results = horse.get('past_results', [])
            if not past_results:
                continue
            
            # 最新の前走を取得
            latest_result = past_results[0]
            finish_position = self._parse_finish_position(latest_result.get('finish_position', ''))
            
            if finish_position is None:
                continue
            
            # 上位7割以内かチェック
            if finish_position > threshold_position:
                continue
            
            # 現在のオッズを取得
            current_odds = self._parse_odds(horse.get('odds', ''))
            if current_odds is None or current_odds < min_odds:
                continue
            
            # 過小評価馬として追加
            undervalued_horses.append({
                'horse_num': horse.get('horse_num'),
                'horse_name': horse.get('horse_name'),
                'previous_rank': finish_position,
                'current_odds': current_odds,
                'reason': f"前走{finish_position}着（上位{threshold_rank*100:.0f}%以内）なのにオッズ{current_odds:.1f}倍"
            })
        
        return undervalued_horses
    
    def _parse_finish_position(self, position_str: str) -> Optional[int]:
        """着順文字列を数値に変換"""
        if not position_str:
            return None
        
        # "1着" -> 1, "3着" -> 3
        try:
            if '着' in position_str:
                return int(position_str.replace('着', ''))
            return int(position_str)
        except Exception as e:
            logger.debug(f"着順解析エラー: {position_str} -> {e}")
            return None
    
    def _parse_odds(self, odds_str: str) -> Optional[float]:
        """オッズ文字列を数値に変換"""
        if not odds_str:
            return None
        
        try:
            # "10.5" -> 10.5, "200.0" -> 200.0
            return float(odds_str.replace(',', ''))
        except Exception as e:
            logger.debug(f"オッズ解析エラー: {odds_str} -> {e}")
            return None
    
    def analyze_horse_performance(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        馬の成績を分析
        
        Args:
            horse_data: 馬データ
            
        Returns:
            分析結果
        """
        analysis = {
            'consistency': 'unknown',  # 一貫性
            'recent_form': 'unknown',  # 近走調子
            'flags': []  # フラグ（要注意など）
        }
        
        past_results = horse_data.get('past_results', [])
        if len(past_results) < 3:
            return analysis
        
        # 直近5走の着順
        recent_ranks = []
        for result in past_results[:5]:
            rank = self._parse_finish_position(result.get('finish_position', ''))
            if rank:
                recent_ranks.append(rank)
        
        if not recent_ranks:
            return analysis
        
        # 一貫性の評価
        rank_variance = self._calculate_variance(recent_ranks)
        if rank_variance > 10:  # ばらつきが大きい
            analysis['consistency'] = 'inconsistent'
            analysis['flags'].append('要注意：成績にばらつきあり')
        else:
            analysis['consistency'] = 'consistent'
        
        # 近走調子
        if len(recent_ranks) >= 3:
            recent_3 = recent_ranks[:3]
            if all(r <= 5 for r in recent_3):  # 直近3走が5着以内
                analysis['recent_form'] = 'good'
            elif all(r >= 10 for r in recent_3):  # 直近3走が10着以下
                analysis['recent_form'] = 'poor'
            else:
                analysis['recent_form'] = 'mixed'
        
        return analysis
    
    def _calculate_variance(self, values: List[int]) -> float:
        """分散を計算"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

