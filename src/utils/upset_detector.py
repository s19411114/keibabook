"""
穴馬発見機能
数式やメモに基づいた穴馬検出
拡張可能な設計
"""
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UpsetDetector:
    """穴馬発見クラス（拡張可能な設計）"""
    
    def __init__(self):
        """検出ルールのリスト（後から追加可能）"""
        self.detection_rules = [
            self._rule_previous_good_performance_low_odds,
            self._rule_training_improvement,
            self._rule_pedigree_upset_potential,
            self._rule_weight_advantage,
            self._rule_class_drop,
            # 新しいルールはここに追加
        ]
    
    def detect_upset_horses(self, race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        穴馬を検出
        
        Args:
            race_data: レースデータ
            
        Returns:
            穴馬候補のリスト
        """
        horses = race_data.get('horses', [])
        if not horses:
            return []
        
        upset_candidates = []
        
        for horse in horses:
            signals = self._check_all_rules(horse, race_data)
            if signals:
                upset_candidates.append({
                    **horse,
                    'upset_signals': signals,
                    'upset_score': self._calculate_upset_score(signals)
                })
        
        # スコアでソート（高い順）
        upset_candidates.sort(key=lambda x: x['upset_score'], reverse=True)
        
        return upset_candidates
    
    def _check_all_rules(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        すべてのルールをチェック
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            検出されたシグナルのリスト
        """
        signals = []
        
        for rule in self.detection_rules:
            signal = rule(horse, race_data)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _calculate_upset_score(self, signals: List[Dict[str, Any]]) -> float:
        """
        穴馬スコアを計算
        
        Args:
            signals: 検出されたシグナル
            
        Returns:
            穴馬スコア（0-100）
        """
        if not signals:
            return 0.0
        
        # シグナルの重要度に応じてスコアを計算
        total_score = 0.0
        for signal in signals:
            importance = signal.get('importance', 1.0)
            total_score += signal.get('score', 0) * importance
        
        return min(100.0, total_score)
    
    def _rule_previous_good_performance_low_odds(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ルール1: 前走好走なのに低オッズ
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            シグナル（検出された場合）
        """
        past_results = horse.get('past_results', [])
        if not past_results:
            return None
        
        latest_result = past_results[0]
        finish_position = self._parse_finish_position(latest_result.get('finish_position', ''))
        
        if finish_position and finish_position <= 5:
            # 前走5着以内
            current_odds = self._parse_odds(horse.get('odds', ''))
            if current_odds and current_odds >= 20.0:  # 20倍以上
                return {
                    'rule': 'previous_good_performance_low_odds',
                    'reason': f"前走{finish_position}着なのにオッズ{current_odds:.1f}倍",
                    'score': 30.0,
                    'importance': 1.2
                }
        
        return None
    
    def _rule_training_improvement(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ルール2: 調教が向上している
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            シグナル（検出された場合）
        """
        training_data = horse.get('training_data', {})
        if not training_data:
            return None
        
        tanpyo = training_data.get('tanpyo', '')
        if not tanpyo:
            return None
        
        # 調教が良いキーワード
        positive_keywords = ['好調', '順調', '良', '好', '上', '余力', '向上']
        for keyword in positive_keywords:
            if keyword in tanpyo:
                return {
                    'rule': 'training_improvement',
                    'reason': f"調教評価: {tanpyo}",
                    'score': 25.0,
                    'importance': 1.0
                }
        
        return None
    
    def _rule_pedigree_upset_potential(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ルール3: 血統に穴馬の可能性
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            シグナル（検出された場合）
        """
        pedigree_data = horse.get('pedigree_data', {})
        if not pedigree_data:
            return None
        
        # 血統データから穴馬の可能性を評価
        # 将来拡張: 血統データベースと照合
        
        return None
    
    def _rule_weight_advantage(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ルール4: 斤量の有利
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            シグナル（検出された場合）
        """
        weight = horse.get('weight', '')
        horse_weight = horse.get('horse_weight', '')
        
        if not weight or not horse_weight:
            return None
        
        try:
            weight_kg = float(str(weight).replace('kg', '').strip())
            horse_weight_kg = float(str(horse_weight).replace('kg', '').strip())
            
            if horse_weight_kg > 0:
                weight_ratio = (weight_kg / horse_weight_kg) * 100
                
                # 斤量比が軽い（有利）
                if weight_ratio < 3.0:
                    return {
                        'rule': 'weight_advantage',
                        'reason': f"斤量比{weight_ratio:.2f}%で軽い",
                        'score': 20.0,
                        'importance': 0.8
                    }
        except Exception as e:
            logger.debug(f"斤量解析エラー: {e}")
            pass
        
        return None
    
    def _rule_class_drop(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ルール5: クラス降級
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            シグナル（検出された場合）
        """
        # クラス情報が必要
        # 将来拡張: レースのクラスと過去走のクラスを比較
        
        return None
    
    def add_rule(self, rule_func):
        """
        新しい検出ルールを追加（拡張可能）
        
        Args:
            rule_func: ルール関数（horse, race_dataを受け取り、Optional[Dict]を返す）
        """
        self.detection_rules.append(rule_func)
        logger.info(f"新しい検出ルールを追加: {rule_func.__name__}")
    
    def _parse_finish_position(self, position_str: str) -> Optional[int]:
        """着順文字列を数値に変換"""
        if not position_str:
            return None
        
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
            return float(str(odds_str).replace(',', '').replace('倍', ''))
        except Exception as e:
            logger.debug(f"オッズ解析エラー: {odds_str} -> {e}")
            return None

