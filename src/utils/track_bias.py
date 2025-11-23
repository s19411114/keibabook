"""
トラックバイアス指数計算モジュール
上位6頭の成績から馬場の傾向を分析
"""
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TrackBiasAnalyzer:
    """トラックバイアス分析クラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def calculate_bias_index(self, race_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        トラックバイアス指数を計算
        
        Args:
            race_result: レース結果データ（上位6頭の情報を含む）
            
        Returns:
            トラックバイアス指数データ
        """
        horses = race_result.get('horses', [])
        
        if len(horses) < 6:
            logger.warning(f"データ不足: {len(horses)}頭のみ（6頭必要）")
            return self._empty_bias_index()
        
        # 上位6頭を抽出
        top_6 = horses[:6]
        
        # 各指標を計算
        bias_data = {
            'inner_outer_bias': self._calculate_inner_outer_bias(top_6),
            'pace_bias': self._calculate_pace_bias(top_6),
            'last_3f_bias': self._calculate_last_3f_bias(top_6),
            'overall_bias_score': 0.0,
            'bias_type': 'unknown',
            'confidence': 0.0
        }
        
        # 総合バイアススコアを計算
        bias_data['overall_bias_score'] = self._calculate_overall_score(bias_data)
        
        # バイアスタイプを判定
        bias_data['bias_type'] = self._determine_bias_type(bias_data)
        
        # 信頼度を計算
        bias_data['confidence'] = self._calculate_confidence(top_6)
        
        logger.info(f"トラックバイアス指数: {bias_data['bias_type']} (スコア: {bias_data['overall_bias_score']:.2f}, 信頼度: {bias_data['confidence']:.2f})")
        
        return bias_data
    
    def _calculate_inner_outer_bias(self, horses: List[Dict[str, Any]]) -> float:
        """
        内外バイアスを計算（着順重み付け + 人気段階評価）
        
        Args:
            horses: 上位6頭のデータ
            
        Returns:
            内外バイアススコア（-100〜100、マイナスが内有利、プラスが外有利）
        """
        inner_score = 0.0
        outer_score = 0.0
        middle_score = 0.0  # 中枠（5-8番）
        
        # 着順による重み（1着が最重要）
        rank_weights = {
            1: 1.0,   # 1着: 100%
            2: 0.8,   # 2着: 80%
            3: 0.7,   # 3着: 70%
            4: 0.5,   # 4着: 50%
            5: 0.4,   # 5着: 40%
            6: 0.3    # 6着: 30%
        }
        
        for horse in horses:
            horse_num = self._parse_horse_num(horse.get('horse_num', ''))
            rank = self._parse_rank(horse.get('rank', ''))
            
            if not horse_num or not rank or rank > 6:
                continue
            
            # 人気とオッズを取得
            popularity = self._parse_popularity(horse.get('popularity', ''))
            
            # 人気段階を判定（5段階）
            popularity_tier = self._get_popularity_tier(popularity)
            
            # 着順から期待される人気段階を計算
            expected_tier = self._get_expected_tier_for_rank(rank)
            
            # 何段階裏切ったか（マイナス = 人気より好走、プラス = 人気より凡走）
            tier_upset = expected_tier - popularity_tier
            
            # 基本スコア（着順による）
            base_score = 100 * rank_weights.get(rank, 0.2)
            
            # 裏切り度によるボーナス（着順が下がるほど緩やかに）
            if tier_upset < 0:  # 人気より好走（穴馬）
                # 着順による緩和係数（1-2着は敏感、3-4着は普通、5-6着は緩やか）
                if rank <= 2:
                    multiplier = 40  # 1段階につき+40点（敏感）
                elif rank <= 4:
                    multiplier = 25  # 1段階につき+25点（普通）
                else:
                    multiplier = 15  # 1段階につき+15点（緩やか、団栗の背比べ）
                
                upset_bonus = abs(tier_upset) * multiplier
            elif tier_upset > 0:  # 人気より凡走
                # ペナルティは控えめ（着順関係なく一律）
                upset_bonus = -tier_upset * 10  # 1段階につき-10点
            else:  # 妥当な順位
                upset_bonus = 0
            
            # 総合スコア（過学習防止: ボーナスは基本スコアの60%まで）
            total_score = base_score + min(upset_bonus, base_score * 0.6)
            total_score = max(total_score, base_score * 0.4)  # 最低でも基本スコアの40%
            
            # 枠位置による分類（内・中・外）
            if horse_num <= 4:  # 内枠（1-4番）
                inner_score += total_score
                position_label = "内"
            elif horse_num <= 8:  # 中枠（5-8番）
                middle_score += total_score
                position_label = "中"
            else:  # 外枠（9番以降）
                outer_score += total_score
                position_label = "外"
            
            # ログ出力
            tier_label = self._get_tier_label(popularity_tier)
            expected_label = self._get_tier_label(expected_tier)
            logger.debug(
                f"{rank}着 {horse_num}番({position_label}枠): "
                f"人気{tier_label} vs 期待{expected_label} → "
                f"裏切り度{tier_upset:+d}段階, "
                f"基本{base_score:.0f} + ボーナス{upset_bonus:.0f} = {total_score:.0f}"
            )
        
        # 中枠飛ばし現象の検出
        total_score_sum = inner_score + middle_score + outer_score
        if total_score_sum > 0:
            middle_ratio = middle_score / total_score_sum
            if middle_ratio < 0.15:  # 中枠が15%未満
                logger.info("⚠️ 中枠飛ばし現象を検出！")
        
        # バイアススコア計算（内 vs 外、中枠は中立として扱う）
        if inner_score + outer_score == 0:
            return 0.0
        
        # 内外の差を計算（-100〜100）
        score = ((outer_score - inner_score) / (inner_score + outer_score)) * 100
        
        logger.info(
            f"内外バイアス: 内{inner_score:.1f} vs 中{middle_score:.1f} vs 外{outer_score:.1f} "
            f"→ スコア{score:.1f}"
        )
        
        return score
    
    def _get_popularity_tier(self, popularity: Optional[int]) -> int:
        """
        人気を段階に変換（3段階にシンプル化）
        
        Args:
            popularity: 人気順位
            
        Returns:
            段階（1-3）
        """
        if not popularity:
            return 2  # デフォルト: 中間
        
        if popularity <= 5:
            return 1  # 上位人気（1-5番人気）
        elif popularity <= 10:
            return 2  # 中位人気（6-10番人気）
        else:
            return 3  # 下位人気（11番人気以降）
    
    def _get_expected_tier_for_rank(self, rank: int) -> int:
        """
        着順から期待される人気段階を計算（緩やかに）
        
        Args:
            rank: 着順
            
        Returns:
            期待される段階（1-3）
        """
        # 1-2着は上位人気を期待（敏感）
        # 3-4着は中位人気を期待（やや緩やか）
        # 5-6着は下位人気を期待（かなり緩やか）
        if rank <= 2:
            return 1  # 上位人気を期待
        elif rank <= 4:
            return 2  # 中位人気を期待
        else:
            return 3  # 下位人気を期待（団栗の背比べ）
    
    def _get_tier_label(self, tier: int) -> str:
        """段階のラベルを取得"""
        labels = {
            1: "上位(1-5)",
            2: "中位(6-10)",
            3: "下位(11-)"
        }
        return labels.get(tier, "不明")
    
    def _calculate_pace_bias(self, horses: List[Dict[str, Any]]) -> float:
        """
        ペースバイアスを計算（逃げ・先行有利 vs 差し・追込有利）
        
        Args:
            horses: 上位6頭のデータ
            
        Returns:
            ペースバイアススコア（-100〜100、マイナスが前有利、プラスが後有利）
        """
        front_runner_count = 0
        closer_count = 0
        
        for horse in horses:
            passing = horse.get('passing', '')
            if passing:
                # 通過順位から脚質を推定
                # 例: "1-1-1" → 逃げ・先行, "10-10-5" → 差し・追込
                positions = self._parse_passing_positions(passing)
                if positions:
                    avg_position = sum(positions) / len(positions)
                    if avg_position <= 4:  # 前半4番手以内
                        front_runner_count += 1
                    else:  # 後方
                        closer_count += 1
        
        total = front_runner_count + closer_count
        if total == 0:
            return 0.0
        
        # スコア計算（-100〜100）
        score = ((closer_count - front_runner_count) / total) * 100
        
        logger.debug(f"ペースバイアス: 前{front_runner_count}頭 vs 後{closer_count}頭 → スコア{score:.1f}")
        
        return score
    
    def _calculate_last_3f_bias(self, horses: List[Dict[str, Any]]) -> float:
        """
        上がり3Fバイアスを計算
        
        Args:
            horses: 上位6頭のデータ
            
        Returns:
            上がり3Fバイアススコア（0〜100、高いほど上がりが速い馬が有利）
        """
        last_3f_times = []
        
        for horse in horses:
            last_3f = self._parse_last_3f(horse.get('last_3f', ''))
            if last_3f:
                last_3f_times.append(last_3f)
        
        if not last_3f_times:
            return 50.0  # デフォルト
        
        # 平均上がりタイムを計算
        avg_last_3f = sum(last_3f_times) / len(last_3f_times)
        
        # 基準値（35.0秒）からの差でスコア化
        # 速いほど高スコア
        score = max(0, min(100, (36.0 - avg_last_3f) * 20 + 50))
        
        logger.debug(f"上がり3Fバイアス: 平均{avg_last_3f:.1f}秒 → スコア{score:.1f}")
        
        return score
    
    def _calculate_overall_score(self, bias_data: Dict[str, Any]) -> float:
        """
        総合バイアススコアを計算
        
        Args:
            bias_data: バイアスデータ
            
        Returns:
            総合スコア（0〜100）
        """
        # 各指標を正規化して合算
        inner_outer = abs(bias_data['inner_outer_bias']) / 2  # 0〜50
        pace = abs(bias_data['pace_bias']) / 2  # 0〜50
        last_3f = bias_data['last_3f_bias']  # 0〜100
        
        # 重み付け平均
        overall = (inner_outer * 0.3 + pace * 0.3 + last_3f * 0.4)
        
        return overall
    
    def _determine_bias_type(self, bias_data: Dict[str, Any]) -> str:
        """
        バイアスタイプを判定
        
        Args:
            bias_data: バイアスデータ
            
        Returns:
            バイアスタイプ（文字列）
        """
        inner_outer = bias_data['inner_outer_bias']
        pace = bias_data['pace_bias']
        
        # 内外バイアス判定
        if inner_outer < -30:
            position_bias = "内有利"
        elif inner_outer > 30:
            position_bias = "外有利"
        else:
            position_bias = "フラット"
        
        # ペースバイアス判定
        if pace < -30:
            pace_bias = "前有利"
        elif pace > 30:
            pace_bias = "後有利"
        else:
            pace_bias = "平均"
        
        return f"{position_bias}・{pace_bias}"
    
    def _calculate_confidence(self, horses: List[Dict[str, Any]]) -> float:
        """
        信頼度を計算
        
        Args:
            horses: 上位6頭のデータ
            
        Returns:
            信頼度（0.0〜1.0）
        """
        # データの完全性をチェック
        complete_data_count = 0
        
        for horse in horses:
            if all([
                horse.get('horse_num'),
                horse.get('passing'),
                horse.get('last_3f')
            ]):
                complete_data_count += 1
        
        confidence = complete_data_count / len(horses)
        
        return confidence
    
    def _parse_horse_num(self, horse_num_str: str) -> Optional[int]:
        """馬番をパース"""
        try:
            return int(horse_num_str)
        except (ValueError, TypeError):
            return None
    
    def _parse_passing_positions(self, passing_str: str) -> List[int]:
        """通過順位をパース（例: "1-1-1" → [1, 1, 1]）"""
        try:
            return [int(p) for p in passing_str.split('-') if p.strip()]
        except (ValueError, AttributeError):
            return []
    
    def _parse_last_3f(self, last_3f_str: str) -> Optional[float]:
        """上がり3Fをパース（例: "35.2" → 35.2）"""
        try:
            return float(last_3f_str)
        except (ValueError, TypeError):
            return None
    
    def _parse_rank(self, rank_str: str) -> Optional[int]:
        """着順をパース（例: "1" → 1）"""
        try:
            return int(rank_str)
        except (ValueError, TypeError):
            return None
    
    def _parse_popularity(self, popularity_str: str) -> Optional[int]:
        """人気をパース（例: "10" → 10）"""
        try:
            # "10番人気" のような形式にも対応
            import re
            match = re.search(r'(\d+)', popularity_str)
            if match:
                return int(match.group(1))
            return None
        except (ValueError, TypeError, AttributeError):
            return None
    
    def _parse_odds(self, odds_str: str) -> Optional[float]:
        """オッズをパース（例: "125.3" → 125.3）"""
        try:
            return float(odds_str)
        except (ValueError, TypeError):
            return None
    
    def _empty_bias_index(self) -> Dict[str, Any]:
        """空のバイアス指数を返す"""
        return {
            'inner_outer_bias': 0.0,
            'pace_bias': 0.0,
            'last_3f_bias': 50.0,
            'overall_bias_score': 0.0,
            'bias_type': 'データ不足',
            'confidence': 0.0
        }
