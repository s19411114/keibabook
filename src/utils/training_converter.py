"""
調教タイム換算モジュール
栗東・美浦の調教施設間のタイム差を補正して共通基準に統一

参考データ:
- ラスト1ハロン（200m）: 栗東が約0.5秒遅く出る傾向
- 坂路調教: 栗東Cコース vs 美浦南W（勾配差により補正必要）
- ウッドチップ: 栗東Dコース vs 美浦南Wなど

補正係数は継続的に更新が必要（馬場状態、季節変動を考慮）
"""
from typing import Dict, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 調教施設間の補正係数（秒単位）
# 形式: (調教場所, コース) -> ラスト1ハロン補正値（秒）
# 正の値 = その施設が速く出る傾向 → 減算して統一
# 負の値 = その施設が遅く出る傾向 → 加算して統一
# 
# データソース: 競馬業界の一般的な定説
# - 坂路: 栗東が約0.5〜0.7秒遅い（勾配差）
# - CW/ポリ: 栗東が約0.3〜0.4秒遅い（クッション性）
# - ダート: 栗東が約0.2〜0.3秒遅い
# - 芝: ほぼ同等（0.1〜0.2秒差）
TIME_CORRECTION = {
    # 栗東トレセン
    ('栗東', 'C'): -0.6,  # 栗東Cコース（坂路）は美浦より0.6秒遅い（保守的な値）
    ('栗東', 'D'): -0.35, # 栗東Dコース（ウッドチップ）は美浦より0.35秒遅い
    ('栗東', 'E'): -0.15, # 栗東Eコース（芝）は美浦より0.15秒遅い
    ('栗東', 'B'): -0.25, # 栗東Bコース（ダート）は美浦より0.25秒遅い
    ('栗東', 'A'): -0.4,  # 栗東Aコース（複合）は美浦より0.4秒遅い
    
    # 美浦トレセン（基準）
    ('美浦', '南W'): 0.0,   # 美浦南W（坂路）を基準とする
    ('美浦', '南P'): 0.1,   # 美浦南P（ポリトラック）は南Wより0.1秒速い
    ('美浦', '南B'): 0.0,   # 美浦南B（芝）は基準と同等
    ('美浦', '北C'): -0.1,  # 美浦北Cは南Wより0.1秒遅い
    ('美浦', '芝'): 0.0,    # 美浦芝コース（一般）
    ('美浦', 'ダート'): -0.05, # 美浦ダートコース
    
    # 地方競馬場（参考値・データ不足のため保守的）
    ('栗東', '栗東'): -0.6,  # 栗東と表記される場合（坂路想定）
    ('美浦', '美浦'): 0.0,   # 美浦と表記される場合
}

# 距離別補正係数（200mあたりの補正を他の距離にスケール）
# 例: 400mの場合は200mの2倍、600mの場合は3倍
DISTANCE_SCALE = {
    200: 1.0,   # ラスト1ハロン
    400: 2.0,   # ラスト2ハロン
    600: 3.0,   # ラスト3ハロン
    800: 4.0,   # ラスト4ハロン
    1000: 5.0,  # ラスト5ハロン
}


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """
    タイム文字列を秒数に変換
    
    Args:
        time_str: タイム文字列（例: "12.5", "1:12.5", "52.3"）
        
    Returns:
        秒数（floatまたはNone）
    """
    if not time_str or time_str == '-':
        return None
    
    try:
        time_str = time_str.strip()
        
        # 分:秒.小数 形式（例: "1:12.5"）
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            # 秒.小数 形式（例: "12.5"）
            return float(time_str)
    except (ValueError, IndexError) as e:
        logger.warning(f"タイム変換エラー: {time_str} - {e}")
        return None


def seconds_to_time_str(seconds: float) -> str:
    """
    秒数をタイム文字列に変換
    
    Args:
        seconds: 秒数
        
    Returns:
        タイム文字列（例: "12.5", "1:12.5"）
    """
    if seconds >= 60:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:.1f}"
    else:
        return f"{seconds:.1f}"


def convert_training_time(
    time_str: str,
    training_center: str,
    course: str,
    distance: int = 200
) -> Dict[str, any]:
    """
    調教タイムを共通基準（美浦南W）に換算
    
    Args:
        time_str: 元のタイム文字列（例: "12.5"）
        training_center: 調教場所（"栗東" or "美浦"）
        course: コース（"C", "D", "E", "南W" など）
        distance: 距離（m）デフォルトは200m（ラスト1ハロン）
        
    Returns:
        {
            'original_time': 元のタイム（秒）,
            'converted_time': 換算後タイム（秒）,
            'correction': 補正値（秒）,
            'original_str': 元のタイム文字列,
            'converted_str': 換算後タイム文字列,
            'center': 調教場所,
            'course': コース
        }
    """
    original_seconds = parse_time_to_seconds(time_str)
    
    if original_seconds is None:
        return {
            'original_time': None,
            'converted_time': None,
            'correction': 0.0,
            'original_str': time_str,
            'converted_str': time_str,
            'center': training_center,
            'course': course
        }
    
    # 補正係数を取得
    key = (training_center, course)
    base_correction = TIME_CORRECTION.get(key, 0.0)
    
    # 距離に応じてスケール
    distance_scale = DISTANCE_SCALE.get(distance, distance / 200.0)
    correction = base_correction * distance_scale
    
    # 換算（栗東が遅い場合は負の値なので、引くことで速くなる）
    converted_seconds = original_seconds - correction
    
    logger.debug(f"調教タイム換算: {training_center}{course} {time_str} → {seconds_to_time_str(converted_seconds)} (補正: {correction:.1f}秒)")
    
    return {
        'original_time': original_seconds,
        'converted_time': converted_seconds,
        'correction': correction,
        'original_str': time_str,
        'converted_str': seconds_to_time_str(converted_seconds),
        'center': training_center,
        'course': course
    }


def extract_training_center_and_course(location_str: str) -> tuple:
    """
    日付・場所文字列から調教場所とコースを抽出
    
    Args:
        location_str: 日付・場所文字列（例: "11/28 栗東C", "11/5 美浦南Ｗ"）
        
    Returns:
        (training_center, course) タプル
    """
    location_str = location_str.strip()
    
    # 栗東の判定
    if '栗東' in location_str:
        training_center = '栗東'
        # コースを抽出（C, D, E, B など）
        for char in location_str:
            if char in ['C', 'D', 'E', 'B', 'A', 'Ｃ', 'Ｄ', 'Ｅ', 'Ｂ', 'Ａ']:
                # 全角を半角に変換
                course_map = {'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｂ': 'B', 'Ａ': 'A'}
                return (training_center, course_map.get(char, char))
        return (training_center, '栗東')  # コース不明
    
    # 美浦の判定
    elif '美浦' in location_str:
        training_center = '美浦'
        # コースを抽出（南W, 南P, 南B, 北C など）- 全角・半角両対応
        if '南W' in location_str or '南w' in location_str or '南Ｗ' in location_str or '南ｗ' in location_str:
            return (training_center, '南W')
        elif '南P' in location_str or '南p' in location_str or '南Ｐ' in location_str or '南ｐ' in location_str:
            return (training_center, '南P')
        elif '南B' in location_str or '南b' in location_str or '南Ｂ' in location_str or '南ｂ' in location_str:
            return (training_center, '南B')
        elif '北C' in location_str or '北c' in location_str or '北Ｃ' in location_str or '北ｃ' in location_str:
            return (training_center, '北C')
        else:
            return (training_center, '美浦')  # コース不明
    
    # その他（地方競馬場など）
    else:
        return ('不明', '不明')


def convert_training_data(training_data: Dict) -> Dict:
    """
    調教データ全体を換算（馬ごとの4回分のタイムを一括処理）
    
    Args:
        training_data: _parse_training_data() の出力
        
    Returns:
        換算済み調教データ（元データ + converted_times 追加）
    """
    converted_data = {}
    
    for horse_num, data in training_data.items():
        converted_horse_data = data.copy()
        converted_details = []
        
        for detail in data.get('details', []):
            converted_detail = detail.copy()
            
            # 日付・場所から調教場所とコースを抽出
            location_str = detail.get('date_location', '')
            training_center, course = extract_training_center_and_course(location_str)
            
            # 4回分のタイムを換算
            converted_times = []
            times_converted_list = []  # 文字列リスト（HTMLレポート用）
            for time_str in detail.get('times', []):
                result = convert_training_time(time_str, training_center, course, distance=200)
                converted_times.append(result)
                times_converted_list.append(result['converted_str'])
            
            converted_detail['converted_times'] = converted_times
            converted_detail['times_converted'] = times_converted_list  # 互換性のため追加
            converted_detail['training_center'] = training_center
            converted_detail['course'] = course
            converted_details.append(converted_detail)
        
        converted_horse_data['details'] = converted_details
        converted_data[horse_num] = converted_horse_data
    
    return converted_data


def get_best_last_half(training_data: Dict, horse_num: str) -> Optional[Dict]:
    """
    指定馬の最も速いラスト1ハロンタイムを取得（換算後）
    
    Args:
        training_data: convert_training_data() の出力
        horse_num: 馬番
        
    Returns:
        {
            'time': 最速タイム（秒）,
            'time_str': タイム文字列,
            'date_location': 日付・場所,
            'center': 調教場所,
            'course': コース
        }
    """
    if horse_num not in training_data:
        return None
    
    best_time = None
    best_info = None
    
    for detail in training_data[horse_num].get('details', []):
        for conv_time in detail.get('converted_times', []):
            if conv_time['converted_time'] is not None:
                if best_time is None or conv_time['converted_time'] < best_time:
                    best_time = conv_time['converted_time']
                    best_info = {
                        'time': best_time,
                        'time_str': conv_time['converted_str'],
                        'date_location': detail.get('date_location', ''),
                        'center': detail.get('training_center', ''),
                        'course': detail.get('course', '')
                    }
    
    return best_info
