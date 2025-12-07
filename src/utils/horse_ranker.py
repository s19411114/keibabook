"""
馬の順位付け機能
血統、トラックバイアス、斤量比、クラス成績、脚質などで評価
"""
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HorseRanker:
    """馬の順位付けクラス（拡張可能な設計）"""
    
    def __init__(self):
        """評価項目の重みを設定（後から調整可能）"""
        self.weights = {
            'pedigree': 0.25,  # 血統
            'track_bias': 0.20,  # トラックバイアス
            'weight_ratio': 0.15,  # 斤量比・馬体重
            'class_performance': 0.20,  # クラスごとの成績
            'running_style': 0.10,  # 脚質
            'training': 0.10  # 調教
        }
    
    def rank_horses(self, race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        馬を順位付け
        
        Args:
            race_data: レースデータ
            
        Returns:
            順位付けされた馬のリスト（スコア付き）
        """
        horses = race_data.get('horses', [])
        if not horses:
            return []
        
        ranked_horses = []
        
        for horse in horses:
            score = self._calculate_score(horse, race_data)
            ranked_horses.append({
                **horse,
                'rank_score': score,
                'rank_breakdown': self._get_score_breakdown(horse, race_data)
            })
        
        # スコアでソート（高い順）
        ranked_horses.sort(key=lambda x: x['rank_score'], reverse=True)
        
        # 順位を追加
        for i, horse in enumerate(ranked_horses, 1):
            horse['predicted_rank'] = i
        
        return ranked_horses
    
    def _calculate_score(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> float:
        """
        馬の総合スコアを計算
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            総合スコア（0-100）
        """
        score = 0.0
        
        # 血統スコア
        pedigree_score = self._evaluate_pedigree(horse)
        score += pedigree_score * self.weights['pedigree']
        
        # トラックバイアススコア（2レースくらい前のデータが必要）
        track_bias_score = self._evaluate_track_bias(horse, race_data)
        score += track_bias_score * self.weights['track_bias']
        
        # 斤量比・馬体重スコア
        weight_score = self._evaluate_weight(horse)
        score += weight_score * self.weights['weight_ratio']
        
        # クラスごとの成績スコア
        class_score = self._evaluate_class_performance(horse)
        score += class_score * self.weights['class_performance']
        
        # 脚質スコア
        running_style_score = self._evaluate_running_style(horse)
        score += running_style_score * self.weights['running_style']
        
        # 調教スコア
        training_score = self._evaluate_training(horse)
        score += training_score * self.weights['training']
        
        return min(100.0, max(0.0, score))
    
    def _evaluate_pedigree(self, horse: Dict[str, Any]) -> float:
        """
        血統を評価
        
        Args:
            horse: 馬データ
            
        Returns:
            血統スコア（0-100）
        """
        pedigree_data = horse.get('pedigree_data', {})
        if not pedigree_data:
            return 50.0  # データがない場合は中間値
        
        score = 50.0  # ベーススコア
        
        # 父の評価（将来拡張: 血統データベースと照合）
        father = pedigree_data.get('father', '')
        if father:
            # 有名な父の場合は加点（実際の血統データベースと照合が必要）
            # ここでは基本的な評価のみ
            score += 10.0
        
        # 母父の評価
        mothers_father = pedigree_data.get('mothers_father', '')
        if mothers_father:
            score += 10.0
        
        return min(100.0, score)
    
    def _evaluate_track_bias(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> float:
        """
        トラックバイアスを評価（2レースくらい前のデータが必要）
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            トラックバイアススコア（0-100）
        """
        # 現時点ではデータが不足しているため、中間値を返す
        # 過去走結果を集めてから実装
        
        past_results = horse.get('past_results', [])
        if len(past_results) < 2:
            return 50.0  # データ不足
        
        # 2レース前のデータを確認
        # 実際のトラックバイアス分析は過去データ蓄積後に実装
        
        return 50.0
    
    def _evaluate_weight(self, horse: Dict[str, Any]) -> float:
        """
        斤量比・馬体重を評価
        
        Args:
            horse: 馬データ
            
        Returns:
            斤量比スコア（0-100）
        """
        # 斤量と馬体重のデータが必要
        # 現時点では基本的な評価のみ
        
        weight = horse.get('weight', '')  # 斤量
        horse_weight = horse.get('horse_weight', '')  # 馬体重
        
        if not weight or not horse_weight:
            return 50.0  # データ不足
        
        try:
            weight_kg = float(str(weight).replace('kg', '').strip())
            horse_weight_kg = float(str(horse_weight).replace('kg', '').strip())
            
            if horse_weight_kg > 0:
                weight_ratio = (weight_kg / horse_weight_kg) * 100
                
                # 斤量比が適切な範囲（3-5%）の場合は高評価
                if 3.0 <= weight_ratio <= 5.0:
                    return 80.0
                elif 2.5 <= weight_ratio < 3.0 or 5.0 < weight_ratio <= 5.5:
                    return 60.0
                else:
                    return 40.0
        except Exception as e:
            logger.debug(f"斤量解析エラー: {e}")
            pass
        
        return 50.0
    
    def _evaluate_class_performance(self, horse: Dict[str, Any]) -> float:
        """
        クラスごとの成績を評価
        
        Args:
            horse: 馬データ
            
        Returns:
            クラス成績スコア（0-100）
        """
        past_results = horse.get('past_results', [])
        if not past_results:
            return 50.0
        
        # 直近3走の成績を評価
        recent_results = past_results[:3]
        total_score = 0.0
        
        for result in recent_results:
            finish_position = self._parse_finish_position(result.get('finish_position', ''))
            if finish_position:
                # 着順が良いほど高スコア
                if finish_position <= 3:
                    total_score += 30.0
                elif finish_position <= 5:
                    total_score += 20.0
                elif finish_position <= 8:
                    total_score += 10.0
        
        # 平均スコア
        if recent_results:
            avg_score = total_score / len(recent_results)
            return min(100.0, avg_score)
        
        return 50.0
    
    def _evaluate_running_style(self, horse: Dict[str, Any]) -> float:
        """
        脚質を評価
        
        Args:
            horse: 馬データ
            
        Returns:
            脚質スコア（0-100）
        """
        # 脚質データが必要（通過順位など）
        # 現時点では基本的な評価のみ
        
        past_results = horse.get('past_results', [])
        if not past_results:
            return 50.0
        
        # 通過順位のデータがあれば評価
        # 現時点では中間値を返す
        
        return 50.0
    
    def _evaluate_training(self, horse: Dict[str, Any]) -> float:
        """
        調教を評価
        
        Args:
            horse: 馬データ
            
        Returns:
            調教スコア（0-100）
        """
        training_data = horse.get('training_data', {})
        if not training_data:
            return 50.0
        
        score = 50.0  # ベーススコア
        
        # 調教評価の短評があれば評価
        tanpyo = training_data.get('tanpyo', '')
        if tanpyo:
            # 良い評価のキーワードがあれば加点
            positive_keywords = ['好調', '順調', '良', '好', '上', '余力']
            negative_keywords = ['不調', '悪', '下', '不足']
            
            for keyword in positive_keywords:
                if keyword in tanpyo:
                    score += 10.0
                    break
            
            for keyword in negative_keywords:
                if keyword in tanpyo:
                    score -= 10.0
                    break
        
        return min(100.0, max(0.0, score))
    
    def _get_score_breakdown(self, horse: Dict[str, Any], race_data: Dict[str, Any]) -> Dict[str, float]:
        """
        スコアの内訳を取得
        
        Args:
            horse: 馬データ
            race_data: レースデータ
            
        Returns:
            各項目のスコア
        """
        return {
            'pedigree': self._evaluate_pedigree(horse),
            'track_bias': self._evaluate_track_bias(horse, race_data),
            'weight_ratio': self._evaluate_weight(horse),
            'class_performance': self._evaluate_class_performance(horse),
            'running_style': self._evaluate_running_style(horse),
            'training': self._evaluate_training(horse)
        }
    
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
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        重みを更新（後から調整可能）
        
        Args:
            new_weights: 新しい重みの辞書
        """
        self.weights.update(new_weights)
        logger.info(f"重みを更新: {new_weights}")

