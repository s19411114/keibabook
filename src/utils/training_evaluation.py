"""
調教評価システム
追い切り方をタイム補正値に変換して評価
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 追い切り方のタイム補正（秒単位）
# 余裕があるほど補正値が大きい（実質タイムがもっと速い）
# 限界まで追うほど補正値が小さい（実質タイムが遅い）
OIKIRI_TIME_ADJUSTMENT = {
    # 馬なり（リラックス）- マイナス補正（実質もっと速い）
    '馬なり余力': -0.5,  # 最も余裕がある（実質0.5秒速い）
    '馬ナリ余力': -0.5,
    '馬なり': -0.4,
    '馬ナリ': -0.4,
    'ナリ': -0.4,
    
    # G前追い系（ゴール前から追う）- やや速い
    'G前強め': -0.2,
    'G前仕掛け': -0.2,
    'G前仕掛': -0.2,
    'G前追う': -0.2,
    'G前追': -0.2,
    'ゴール前強め': -0.2,
    'ゴール前仕掛け': -0.2,
    'ゴール前仕掛': -0.2,
    'ゴール前追う': -0.2,
    'ゴール前追': -0.2,
    
    # 強め - 普通（補正なし）
    '強め': 0.0,
    '直線強め': 0.0,
    '直線追う': 0.0,
    '直線追': 0.0,
    
    # 一杯 - 限界まで追う（プラス補正、実質遅い）
    'G前一杯': 0.3,  # ゴール前からなら少しマシ
    'ゴール前一杯': 0.3,
    '一杯': 0.6,  # 限界（実質0.6秒遅い）
    '一杯に追う': 0.6,
    '直線一杯': 0.6,
    
    # 軽め - 調整段階（要注意、評価対象外）
    '軽め': None,  # 評価対象外
    '軽く': None,
    '軽い': None,
    'ナリ軽め': None,
}

# 追い切り方のパターンマッチング（部分一致用）
OIKIRI_PATTERNS = [
    (r'馬[ナな]リ余力', -0.5),
    (r'馬[ナな]リ', -0.4),
    (r'[Gg]前強め', -0.2),
    (r'[Gg]前仕掛', -0.2),
    (r'[Gg]前追', -0.2),
    (r'[Gg]前一杯', 0.3),
    (r'ゴール前強め', -0.2),
    (r'ゴール前仕掛', -0.2),
    (r'ゴール前追', -0.2),
    (r'ゴール前一杯', 0.3),
    (r'直線強め', 0.0),
    (r'直線追', 0.0),
    (r'直線一杯', 0.6),
    (r'強め', 0.0),
    (r'一杯', 0.6),
    (r'軽め', None),
    (r'軽く', None),
]


def get_oikiri_adjustment(oikiri_text: str) -> Optional[float]:
    """
    追い切り方のテキストからタイム補正値を取得
    
    Args:
        oikiri_text: 追い切り方のテキスト（例: "強め", "G前仕掛け", "馬なり余力"）
        
    Returns:
        タイム補正値（秒）
        - マイナス値: 余裕がある（実質もっと速い）
        - プラス値: 限界まで追う（実質遅い）
        - None: 軽め調整（評価対象外）
        
    例:
        - 馬なり余力: -0.5秒（実質0.5秒速い）
        - 強め: 0.0秒（そのまま）
        - 一杯: +0.6秒（実質0.6秒遅い）
    """
    if not oikiri_text:
        return 0.0  # デフォルト（普通）
    
    # 完全一致チェック
    if oikiri_text in OIKIRI_TIME_ADJUSTMENT:
        return OIKIRI_TIME_ADJUSTMENT[oikiri_text]
    
    # パターンマッチング（部分一致）
    for pattern, adjustment in OIKIRI_PATTERNS:
        if re.search(pattern, oikiri_text):
            logger.debug(f"追い切り補正: '{oikiri_text}' → パターン '{pattern}' マッチ → {adjustment}秒")
            return adjustment
    
    logger.debug(f"追い切り補正: '{oikiri_text}' → 未知のパターン → デフォルト 0.0秒")
    return 0.0  # 未知のパターンはデフォルト


def calculate_adjusted_time(
    last_time: float,
    oikiri_adjustment: Optional[float]
) -> Tuple[float, bool]:
    """
    追い切り方補正を適用した調整後タイムを算出
    
    Args:
        last_time: ラスト1ハロンタイム（秒、変換済み）
        oikiri_adjustment: 追い切り方の補正値（秒）
        
    Returns:
        (adjusted_time, is_light): 調整後タイム、軽め調整かどうか
    """
    # 軽め調整チェック（評価対象外）
    if oikiri_adjustment is None:
        return (last_time, True)
    
    # 補正適用
    # 馬なり（マイナス補正）→ 実質もっと速い → タイムを引く
    # 一杯（プラス補正）→ 実質遅い → タイムを足す
    adjusted_time = last_time + oikiri_adjustment
    
    return (adjusted_time, False)


def calculate_training_score(
    adjusted_time: float,
    time_rank: int,
    total_horses: int,
    oikiri_adjustment: float,
    days_before_race: int
) -> Dict:
    """
    調教の総合評価を算出（5段階相対評価）
    
    Args:
        adjusted_time: 調整後タイム（追い切り方補正済み）
        time_rank: 調整後タイムの順位（1〜出走頭数）
        total_horses: 出走頭数
        oikiri_adjustment: 追い切り方の補正値
        days_before_race: レース何日前の調教か
        
    Returns:
        {
            'score': 総合スコア（1〜5、5が最高）,
            'rank': ランク（S/A/B/C/D）,
            'mark': 印（◎○▲△☆）,
            'time_rank': タイム順位,
            'adjusted_time': 調整後タイム,
            'oikiri_adjustment': 追い切り補正,
            'is_light': False,
            'note': 補足説明
        }
    """
    # 順位パーセンタイルを算出
    percentile = (total_horses - time_rank + 1) / total_horses
    
    # パーセンタイルからスコアを算出（1.0〜5.0）
    # 上位20%: 5.0, 上位40%: 4.0, 上位60%: 3.0, 上位80%: 2.0, それ以下: 1.0
    if percentile >= 0.8:
        base_score = 5.0
    elif percentile >= 0.6:
        base_score = 4.0
    elif percentile >= 0.4:
        base_score = 3.0
    elif percentile >= 0.2:
        base_score = 2.0
    else:
        base_score = 1.0
    
    # 古い調教は減点
    if days_before_race > 14:
        base_score = max(1.0, base_score - 1.0)
    
    # ランク判定
    if base_score >= 4.5:
        rank = 'S'
        mark = '◎'
    elif base_score >= 4.0:
        rank = 'A'
        mark = '○'
    elif base_score >= 3.0:
        rank = 'B'
        mark = '▲'
    elif base_score >= 2.0:
        rank = 'C'
        mark = '△'
    else:
        rank = 'D'
        mark = '☆'
    
    # 補足説明
    notes = []
    
    if oikiri_adjustment is not None:
        if oikiri_adjustment <= -0.4:
            notes.append('余裕のある仕上がり（馬なり）')
        elif oikiri_adjustment >= 0.6:
            notes.append('限界まで追っている（上積み少ない可能性）')
    
    if time_rank <= 3:
        notes.append(f'調整後タイム{time_rank}位')
    
    if days_before_race > 14:
        notes.append('2週間以上前の調教（参考）')
    elif 7 <= days_before_race <= 14:
        notes.append('1〜2週間前の調教（重要）')
    
    note = '、'.join(notes) if notes else ''
    
    return {
        'score': round(base_score, 1),
        'rank': rank,
        'mark': mark,
        'time_rank': time_rank,
        'adjusted_time': round(adjusted_time, 1),
        'oikiri_adjustment': oikiri_adjustment,
        'is_light': False,
        'note': note
    }


def evaluate_all_horses_training(training_data: Dict, race_date: str = None) -> Dict:
    """
    全馬の調教を評価（相対評価 - タイム換算方式）
    
    Args:
        training_data: 調教データ（convert_training_data()の出力）
        race_date: レース日（YYYY-MM-DD形式、省略時は今日から7日後と仮定）
        
    Returns:
        馬番をキーとした評価データ
        {
            'horse_num': {
                'last_training': {最終調教の情報},
                'evaluation': {評価結果},
                'best_recent_training': {直近2週間のベスト調教}
            }
        }
    """
    # レース日を設定（省略時は今日から7日後）
    if race_date:
        try:
            race_date_obj = datetime.strptime(race_date, '%Y-%m-%d')
        except ValueError:
            race_date_obj = datetime.now() + timedelta(days=7)
    else:
        race_date_obj = datetime.now() + timedelta(days=7)
    
    # 全馬の調整後タイムを収集（相対評価用）
    horse_training_info = {}
    
    for horse_num, horse_data in training_data.items():
        details = horse_data.get('details', [])
        if not details:
            continue
        
        # 最新の調教を取得（日付順にソート）
        sorted_details = sorted(
            details,
            key=lambda d: parse_training_date(d.get('date_location', ''), race_date_obj.year),
            reverse=True
        )
        
        if not sorted_details:
            continue
        
        last_training = sorted_details[0]
        
        # ラスト1ハロンタイムを取得
        converted_times = last_training.get('converted_times', [])
        if not converted_times or not converted_times[-1]:
            continue
        
        last_hallon_time = converted_times[-1].get('converted_time', 0)
        if last_hallon_time <= 0:
            continue
        
        # 追い切り方を取得
        oikiri_text = last_training.get('追い切り方', '')
        oikiri_adjustment = get_oikiri_adjustment(oikiri_text)
        
        # 調整後タイムを算出
        adjusted_time, is_light = calculate_adjusted_time(last_hallon_time, oikiri_adjustment)
        
        # レース何日前かを計算
        training_date = parse_training_date(last_training.get('date_location', ''), race_date_obj.year)
        days_before = (race_date_obj - training_date).days
        
        horse_training_info[horse_num] = {
            'training': last_training,
            'original_time': last_hallon_time,
            'adjusted_time': adjusted_time,
            'oikiri_adjustment': oikiri_adjustment,
            'is_light': is_light,
            'days_before': days_before
        }
    
    # 軽め調整を除外して調整後タイムでソート
    valid_horses = [(num, info) for num, info in horse_training_info.items() if not info['is_light']]
    
    if not valid_horses:
        # 全馬が軽め調整の場合
        evaluation_results = {}
        for horse_num, info in horse_training_info.items():
            evaluation_results[horse_num] = {
                'last_training': info['training'],
                'evaluation': {
                    'score': 0,
                    'rank': '⚠️',
                    'mark': '⚠️',
                    'time_rank': None,
                    'adjusted_time': None,
                    'oikiri_adjustment': None,
                    'is_light': True,
                    'note': '調整中（軽め）- 本番が調教代わりの可能性'
                },
                'days_before_race': info['days_before'],
                'race_date': race_date_obj.strftime('%Y-%m-%d')
            }
        return evaluation_results
    
    # 調整後タイムでソート（速い順）
    valid_horses_sorted = sorted(valid_horses, key=lambda x: x[1]['adjusted_time'])
    
    # 各馬を評価
    evaluation_results = {}
    total_horses = len(valid_horses)
    
    for rank, (horse_num, info) in enumerate(valid_horses_sorted, 1):
        # 総合評価を算出
        evaluation = calculate_training_score(
            info['adjusted_time'],
            rank,
            total_horses,
            info['oikiri_adjustment'],
            info['days_before']
        )
        
        evaluation_results[horse_num] = {
            'last_training': info['training'],
            'evaluation': evaluation,
            'days_before_race': info['days_before'],
            'race_date': race_date_obj.strftime('%Y-%m-%d')
        }
    
    # 軽め調整の馬も追加
    for horse_num, info in horse_training_info.items():
        if info['is_light'] and horse_num not in evaluation_results:
            evaluation_results[horse_num] = {
                'last_training': info['training'],
                'evaluation': {
                    'score': 0,
                    'rank': '⚠️',
                    'mark': '⚠️',
                    'time_rank': None,
                    'adjusted_time': None,
                    'oikiri_adjustment': None,
                    'is_light': True,
                    'note': '調整中（軽め）- 本番が調教代わりの可能性'
                },
                'days_before_race': info['days_before'],
                'race_date': race_date_obj.strftime('%Y-%m-%d')
            }
    
    return evaluation_results


def parse_training_date(date_location_str: str, year: int) -> datetime:
    """
    調教の日付文字列からdatetimeオブジェクトを生成
    
    Args:
        date_location_str: "11/28 栗東C" のような文字列
        year: 年（レース年）
        
    Returns:
        datetimeオブジェクト
    """
    # 日付部分を抽出（MM/DD）
    match = re.search(r'(\d{1,2})/(\d{1,2})', date_location_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        
        try:
            return datetime(year, month, day)
        except ValueError:
            # 無効な日付の場合はデフォルト
            return datetime.now()
    
    # パースできない場合は今日
    return datetime.now()


def format_training_evaluation(evaluation_data: Dict) -> str:
    """
    調教評価を見やすいテキストに整形
    
    Args:
        evaluation_data: evaluate_all_horses_training()の出力
        
    Returns:
        整形されたテキスト
    """
    lines = []
    lines.append("=" * 70)
    lines.append("🏇 調教評価早見表（タイム換算方式）")
    lines.append("=" * 70)
    lines.append("")
    lines.append("【評価方法】")
    lines.append("  - 追い切り方をタイム補正に変換（馬なり余力: -0.5秒、一杯: +0.6秒）")
    lines.append("  - 調整後タイム = 実測タイム + 追い切り補正")
    lines.append("  - 調整後タイムで順位をつけて5段階評価")
    lines.append("  - 印: ◎（S）> ○（A）> ▲（B）> △（C）> ☆（D）> ⚠️（軽め）")
    lines.append("")
    
    # ランク別に並び替え
    rank_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, '⚠️': 5}
    sorted_horses = sorted(
        evaluation_data.items(),
        key=lambda x: (
            rank_order.get(x[1]['evaluation']['rank'], 6),
            x[1]['evaluation'].get('adjusted_time', 999)
        )
    )
    
    for horse_num, data in sorted_horses:
        eval_info = data['evaluation']
        training = data['last_training']
        
        rank = eval_info['rank']
        mark = eval_info.get('mark', rank)
        score = eval_info['score']
        is_light = eval_info['is_light']
        
        # ヘッダー
        if is_light:
            lines.append(f"{mark} {horse_num}番 | ⚠️ 調整中（軽め）")
        else:
            adjusted_time = eval_info.get('adjusted_time', 0)
            time_rank = eval_info.get('time_rank', '-')
            lines.append(f"{mark} {horse_num}番 | ランク: {rank} | スコア: {score}/5.0 | 順位: {time_rank}位")
            lines.append(f"   調整後タイム: {adjusted_time:.1f}秒")
        
        # 調教詳細
        date_location = training.get('date_location', '')
        oikiri = training.get('追い切り方', '')
        lines.append(f"   📅 {date_location} | ⚡ {oikiri}")
        
        # タイム
        times_converted = training.get('times_converted', [])
        if times_converted:
            time_strs = [t for t in times_converted if t]
            lines.append(f"   ⏱️  実測: {' - '.join(time_strs)}")
        
        # 補正情報
        if not is_light:
            oikiri_adj = eval_info.get('oikiri_adjustment', 0)
            if oikiri_adj != 0:
                sign = '+' if oikiri_adj > 0 else ''
                lines.append(f"   🔧 追い切り補正: {sign}{oikiri_adj}秒")
        
        # 備考
        note = eval_info.get('note', '')
        if note:
            lines.append(f"   💭 {note}")
        else:
            lines.append(f"   💭 {eval_info.get('note', '')}")
        
        lines.append("")
    
    return "\n".join(lines)
