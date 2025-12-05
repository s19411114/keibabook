"""
レースデータエクスポーター
- 全データ（血統、出馬表、調教、厩舎の話、ポイント、展開予想、CPU予想、結果）を
  AI分析用に1つのテキストファイルにまとめる

取得項目一覧:
【共通】
- 出馬表: 枠番、馬番、馬名、騎手、斤量、オッズ、人気、予想印、短評/見解
- 血統: 三代血統（父/母/父父/父母/母父/母母/3代前8頭）
- 調教: 短評、タイム、併せ馬
- 厩舎の話
- 前走コメント
- 展開予想: ペース、隊列（逃げ/好位/中位/後方）、展開コメント

【中央競馬専用】
- CPU予想: レーティング、スピード指数、調教印、血統印
- ギリギリ情報（重賞）: 馬体重変動、パドック評価、直前コメント
- 特集ページ（重賞）: 傾向分析、血統傾向、本命・対抗・穴馬
- AI指数

【地方競馬専用】
- ポイント: 大穴馬、激走馬、AI血統予想、パワー馬場向き馬
- 個別馬コメント（穴馬のヒント）

【レース後】
- レース結果: 着順、タイム、着差、通過順位、上がり3F
- ラップタイム（トラックバイアス分析用）
- レース後コメント、次走へのメモ
- 払戻情報
"""
import json
from datetime import datetime

def export_for_ai(race_data: dict, format: str = "markdown") -> str:
    """
    レースデータをAI分析用のテキストに変換
    
    Args:
        race_data: scrape()の結果
        format: "markdown", "plain", "json"のいずれか
    
    Returns:
        AI入力用にフォーマットされたテキスト
    """
    if format == "json":
        return json.dumps(race_data, ensure_ascii=False, indent=2)
    
    lines = []
    
    # ヘッダー
    lines.append("=" * 60)
    lines.append(f"# {race_data.get('race_grade', 'レース情報')}")
    lines.append(f"日時: {race_data.get('race_name', '')}")
    lines.append("=" * 60)
    lines.append("")
    
    # レース条件
    lines.append("## レース条件")
    lines.append(f"- 距離・コース: {race_data.get('full_condition', race_data.get('distance', ''))}")
    lines.append(f"- コース: {race_data.get('course', '')}")
    lines.append(f"- 天候・馬場: {race_data.get('weather_track', '')}")
    if race_data.get('race_class'):
        lines.append(f"- クラス条件: {race_data.get('race_class', '')}")
    if race_data.get('race_base_info'):
        lines.append(f"- 詳細情報: {race_data.get('race_base_info', '')}")
    if race_data.get('start_time'):
        lines.append(f"- 発走時刻: {race_data.get('start_time', '')}")
    lines.append("")
    
    # 展開予想
    lines.append("## 展開予想")
    lines.append(f"- ペース: {race_data.get('pace', '不明')}")
    formation = race_data.get('formation', {})
    if formation:
        lines.append("- 隊列予想:")
        for pos, horses in formation.items():
            lines.append(f"  - {pos}: {horses}")
    if race_data.get('formation_comment'):
        lines.append(f"- 展開コメント: {race_data.get('formation_comment')}")
    if race_data.get('race_comment'):
        lines.append(f"- 全体分析: {race_data.get('race_comment')}")
    lines.append("")
    
    # ===== 中央競馬専用: CPU予想 =====
    cpu_data = race_data.get('cpu_prediction', {})
    if cpu_data and cpu_data.get('horses'):
        lines.append("## CPU予想（最重要）")
        lines.append("| 馬番 | 馬名 | レーティング | スピード指数 | 調教印 | 血統印 | CPU指数 |")
        lines.append("|------|------|--------------|--------------|--------|--------|---------|")
        for h in cpu_data.get('horses', []):
            lines.append(f"| {h.get('horse_num', '')} | {h.get('horse_name', '')} | {h.get('rating', '')} | {h.get('speed_index', '')} | {h.get('training_mark', '')} | {h.get('pedigree_mark', '')} | {h.get('cpu_index', '')} |")
        if cpu_data.get('summary', {}).get('comment'):
            lines.append(f"\n**サマリー**: {cpu_data['summary']['comment']}")
        lines.append("")
    
    # ===== 中央競馬専用: ギリギリ情報（重賞） =====
    girigiri_data = race_data.get('girigiri_info', {})
    if girigiri_data:
        lines.append("## ギリギリ情報（直前情報）")
        if girigiri_data.get('overall_comment'):
            lines.append(f"- 全体コメント: {girigiri_data['overall_comment']}")
        if girigiri_data.get('paddock_comment'):
            lines.append(f"- パドック: {girigiri_data['paddock_comment']}")
        if girigiri_data.get('last_update'):
            lines.append(f"- 最終更新: {girigiri_data['last_update']}")
        for h in girigiri_data.get('horses', []):
            lines.append(f"- {h.get('horse_num', '')}番 {h.get('horse_name', '')}: 体重{h.get('weight_change', '')} パドック{h.get('paddock_eval', '')} {h.get('girigiri_comment', '')}")
        lines.append("")
    
    # ===== 中央競馬専用: 特集ページ（重賞） =====
    feature_data = race_data.get('special_feature', {})
    if feature_data and feature_data.get('title'):
        lines.append(f"## 特集: {feature_data.get('title', '')}")
        for analysis in feature_data.get('analysis', []):
            lines.append(f"### {analysis.get('title', '')}")
            lines.append(f"{analysis.get('content', '')}")
            lines.append("")
        if feature_data.get('trends'):
            lines.append("### 傾向データ")
            for k, v in feature_data['trends'].items():
                lines.append(f"- {k}: {v}")
        picks = feature_data.get('picks', {})
        if any(picks.values()):
            lines.append("### 注目馬")
            if picks.get('honmei'):
                lines.append(f"- **本命**: {', '.join(picks['honmei'])}")
            if picks.get('taikou'):
                lines.append(f"- **対抗**: {', '.join(picks['taikou'])}")
            if picks.get('anaba'):
                lines.append(f"- **穴馬**: {', '.join(picks['anaba'])}")
        if feature_data.get('pedigree_trends'):
            lines.append("### 血統傾向")
            for trend in feature_data['pedigree_trends']:
                lines.append(f"- {trend}")
        if feature_data.get('course_analysis'):
            lines.append(f"### コース分析\n{feature_data['course_analysis']}")
        lines.append("")
    
    # ===== 地方競馬専用: ポイント情報 =====
    point_data = race_data.get('point_info', {})
    if point_data:
        lines.append("## ポイント情報（地方競馬）")
        if point_data.get('big_upset_horses'):
            lines.append("### 今日大穴空けた馬たち")
            for h in point_data['big_upset_horses']:
                lines.append(f"- {h.get('horse_num', '')}番 {h.get('horse_name', '')}: {h.get('reason', '')} (オッズ{h.get('odds', '')})")
        if point_data.get('strong_run_hints'):
            lines.append("### 激走した馬たちのヒント")
            for h in point_data['strong_run_hints']:
                lines.append(f"- {h.get('horse_num', '')}番 {h.get('horse_name', '')}: {h.get('reason', '')}")
        if point_data.get('ai_pedigree_picks'):
            lines.append("### 血統からAIが予想した馬")
            for h in point_data['ai_pedigree_picks']:
                lines.append(f"- {h.get('horse_num', '')}番 {h.get('horse_name', '')}: {h.get('reason', '')}")
        if point_data.get('power_track_horses'):
            lines.append("### パワー馬場向きの馬")
            for h in point_data['power_track_horses']:
                lines.append(f"- {h.get('horse_num', '')}番 {h.get('horse_name', '')}: {h.get('reason', '')} (オッズ{h.get('odds', '')})")
        lines.append("")
    
    # 出馬表（詳細）
    lines.append("## 出馬表")
    lines.append("")
    
    horses = race_data.get('horses', [])
    for h in horses:
        waku = h.get('waku', '')
        num = h.get('horse_num', '')
        name = h.get('horse_name', '')
        mark = h.get('prediction_mark', '')
        
        lines.append(f"### {num}番 {name} ({waku}枠) {mark}")
        lines.append("")
        
        # 基本情報
        sex = h.get('sex', '')
        age = h.get('age', '')
        weight = h.get('weight', '')
        jockey = h.get('jockey', '')
        odds = h.get('odds')
        pop = h.get('popularity')
        
        lines.append(f"- 性齢: {sex}{age}")
        lines.append(f"- 斤量: {weight}kg")
        lines.append(f"- 騎手: {jockey}")
        if odds is not None:
            lines.append(f"- オッズ: {odds}倍 ({pop}人気)" if pop else f"- オッズ: {odds}倍")
        
        # 個別予想家印（広瀬、吉田、安中、CPU穴など）
        individual_marks = h.get('individual_marks', {})
        if individual_marks:
            mark_strs = [f"{name}:{m}" for name, m in individual_marks.items() if m]
            if mark_strs:
                lines.append(f"- **予想家印**: {', '.join(mark_strs)}")
        
        # 短評/見解
        comment = h.get('comment', '')
        if comment:
            lines.append(f"- **短評**: {comment}")
        
        # 血統
        pedigree = h.get('pedigree_data', {})
        if pedigree:
            lines.append("")
            lines.append("#### 血統")
            father = pedigree.get('father', '')
            mother = pedigree.get('mother', '')
            mothers_father = pedigree.get('mothers_father', '')
            if father:
                lines.append(f"- 父: {father}")
            if mother:
                lines.append(f"- 母: {mother}")
            if mothers_father:
                lines.append(f"- 母父: {mothers_father}")
            # 3代血統詳細
            ff = pedigree.get('father_father', '')
            fm = pedigree.get('father_mother', '')
            mf = pedigree.get('mothers_father', '')
            mm = pedigree.get('mothers_mother', '')
            if ff or fm or mf or mm:
                lines.append(f"- 父父: {ff} / 父母: {fm}")
                lines.append(f"- 母父: {mf} / 母母: {mm}")
        
        # 調教データ
        training = h.get('training_data', {})
        if training:
            lines.append("")
            lines.append("#### 調教")
            tanpyo = training.get('tanpyo', '')
            if tanpyo:
                lines.append(f"- 短評: {tanpyo}")
            details = training.get('details', [])
            for d in details[-3:]:  # 直近3本のみ表示
                date_loc = d.get('date_location', '')
                oikiri = d.get('追い切り方', '')
                center = d.get('training_center', '')
                course = d.get('course', '')
                
                # 換算後タイムを優先表示（元タイムも括弧内に表示）
                converted_times = d.get('converted_times', [])
                positions = d.get('positions', [])
                
                if converted_times:
                    time_parts = []
                    for idx, conv in enumerate(converted_times):
                        conv_str = conv.get('converted_str', '')
                        orig_str = conv.get('original_str', '')
                        pos = positions[idx] if idx < len(positions) else ''
                        
                        # 換算タイムと元タイムが異なる場合のみ元タイムを表示
                        if conv_str and conv_str != orig_str:
                            time_parts.append(f"{conv_str}{pos}({orig_str})")
                        else:
                            time_parts.append(f"{orig_str}{pos}")
                    time_str = '-'.join(time_parts)
                else:
                    # フォールバック: 元タイムのみ
                    times = d.get('times', [])
                    time_str = '-'.join([f"{t}{positions[i] if i < len(positions) else ''}" for i, t in enumerate(times)]) if times else ''
                
                awase = d.get('awase', '')
                comment = d.get('comment', '')
                
                lines.append(f"  - {date_loc} {oikiri} {time_str}")
                if center and course:
                    lines.append(f"    ({center}{course})")
                if awase:
                    lines.append(f"    併せ: {awase}")
                if comment:
                    lines.append(f"    コメント: {comment}")
        
        # 厩舎の話
        stable = h.get('stable_comment', '')
        if stable:
            lines.append("")
            lines.append("#### 厩舎の話")
            lines.append(f"{stable}")
        
        # 前走コメント
        prev_comment = h.get('previous_race_comment', '')
        if prev_comment:
            lines.append("")
            lines.append("#### 前走レース回顧")
            lines.append(f"{prev_comment}")
        
        # 個別コメント
        ind_comment = h.get('individual_comment', '')
        if ind_comment:
            lines.append("")
            lines.append("#### 馬個別コメント")
            lines.append(f"{ind_comment}")
        
        # 過去成績
        past = h.get('past_results', [])
        if past:
            lines.append("")
            lines.append("#### 過去成績")
            for result in past[:5]:  # 直近5走
                lines.append(f"  - {result}")
        
        # CPU予想データ（中央競馬）
        if h.get('rating') or h.get('speed_index') or h.get('cpu_index'):
            lines.append("")
            lines.append("#### CPU予想")
            if h.get('rating'):
                lines.append(f"- レーティング: {h['rating']}")
            if h.get('speed_index'):
                lines.append(f"- スピード指数: {h['speed_index']}")
            if h.get('cpu_training_mark'):
                lines.append(f"- 調教印: {h['cpu_training_mark']}")
            if h.get('cpu_pedigree_mark'):
                lines.append(f"- 血統印: {h['cpu_pedigree_mark']}")
            if h.get('cpu_index'):
                lines.append(f"- CPU指数: {h['cpu_index']}")
        
        # レース結果（レース後のみ）
        if h.get('result_rank'):
            lines.append("")
            lines.append("#### レース結果")
            lines.append(f"- 着順: {h['result_rank']}")
            if h.get('result_time'):
                lines.append(f"- タイム: {h['result_time']}")
            if h.get('result_margin'):
                lines.append(f"- 着差: {h['result_margin']}")
            if h.get('result_passing'):
                lines.append(f"- 通過順位: {h['result_passing']}")
            if h.get('result_last_3f'):
                lines.append(f"- 上がり3F: {h['result_last_3f']}")
            if h.get('result_comment'):
                lines.append(f"- レース後コメント: {h['result_comment']}")
            if h.get('next_race_memo'):
                lines.append(f"- **次走メモ**: {h['next_race_memo']}")
        
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    
    # ===== レース結果セクション（レース後のみ） =====
    result_data = race_data.get('result', {})
    if result_data:
        lines.append("## レース結果")
        
        # ラップタイム（トラックバイアス分析用）
        lap_times = race_data.get('lap_times', [])
        if lap_times:
            lines.append("### ラップタイム")
            lines.append(f"- {' - '.join(lap_times)}")
        
        # コーナー通過順位
        corner_positions = race_data.get('corner_positions', {})
        if corner_positions:
            lines.append("### コーナー通過順位")
            for corner, positions in corner_positions.items():
                lines.append(f"- {corner}: {positions}")
        
        # レース回顧
        if race_data.get('race_review'):
            lines.append("### レース回顧")
            lines.append(f"{race_data['race_review']}")
        
        # 払戻
        payouts = race_data.get('payouts', {})
        if payouts:
            lines.append("### 払戻")
            for payout_type, value in payouts.items():
                if isinstance(value, dict):
                    lines.append(f"- {payout_type}: {value.get('value', '')} ({value.get('horse', '')})")
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, dict):
                            lines.append(f"- {payout_type}: {v.get('value', '')} ({v.get('horse', '')})")
                        else:
                            lines.append(f"- {payout_type}: {v}")
                else:
                    lines.append(f"- {payout_type}: {value}")
        lines.append("")
    
    # フッター
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"エクスポート日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def export_compact(race_data: dict) -> str:
    """
    コンパクトなJSON形式でエクスポート（キー名を短縮）
    """
    compact = {
        "race": {
            "name": race_data.get('race_grade', ''),
            "date": race_data.get('race_name', ''),
            "condition": race_data.get('full_condition', ''),
            "pace": race_data.get('pace', ''),
            "formation": race_data.get('formation', {}),
        },
        "horses": []
    }
    
    for h in race_data.get('horses', []):
        horse = {
            "n": h.get('horse_num'),
            "w": h.get('waku'),
            "name": h.get('horse_name'),
            "mark": h.get('prediction_mark'),
            "jockey": h.get('jockey'),
            "age": f"{h.get('sex', '')}{h.get('age', '')}",
            "wt": h.get('weight'),
            "odds": h.get('odds'),
            "pop": h.get('popularity'),
            "comment": h.get('comment'),
        }
        
        # 血統
        ped = h.get('pedigree_data', {})
        if ped:
            horse["ped"] = {
                "f": ped.get('father'),
                "m": ped.get('mother'),
                "mf": ped.get('mothers_father'),
            }
        
        # 調教
        tr = h.get('training_data', {})
        if tr:
            horse["tr"] = {
                "comment": tr.get('tanpyo'),
                "count": len(tr.get('details', [])),
            }
        
        # 厩舎
        if h.get('stable_comment'):
            horse["stable"] = h.get('stable_comment')
        
        compact["horses"].append(horse)
    
    return json.dumps(compact, ensure_ascii=False, indent=2)


# 直接実行時のテスト
if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample = {
        "race_name": "2025年11月24日 5回東京6日目",
        "race_grade": "11R 東京スポーツ杯2歳S(GII)",
        "full_condition": "1800m (芝C・左) 晴・良",
        "pace": "S",
        "formation": {"逃げ": "②", "好位": "⑥⑨④"},
        "horses": [
            {
                "horse_num": "1",
                "waku": "1",
                "horse_name": "ラストスマイル",
                "prediction_mark": "★-",
                "sex": "牡",
                "age": "2",
                "weight": "56",
                "jockey": "杉原誠",
                "odds": 39.6,
                "popularity": 10,
                "comment": "一挙相手強化",
                "pedigree_data": {"father": "ポエティックフレア", "mother": "Hymn of the Dawn"},
                "training_data": {"tanpyo": "１ハロンの伸び目立つ"},
                "stable_comment": "",
            }
        ]
    }
    
    print(export_for_ai(sample))
