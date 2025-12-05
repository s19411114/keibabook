"""
調教評価システムのテスト
"""
import json
from src.utils.training_evaluation import (
    evaluate_oikiri,
    evaluate_all_horses_training,
    format_training_evaluation
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_oikiri_evaluation():
    """追い切り方の評価をテスト"""
    
    test_cases = [
        ('馬なり余力', 5.5),
        ('馬なり', 5.0),
        ('馬ナリ', 5.0),
        ('G前強め', 4.5),
        ('G前仕掛け', 4.5),
        ('ゴール前強め', 4.5),
        ('強め', 4.0),
        ('直線強め', 4.0),
        ('一杯', 2.5),
        ('一杯に追う', 2.5),
        ('G前一杯', 3.0),
        ('軽め', 0.0),
    ]
    
    logger.info("=== 追い切り評価テスト ===")
    for text, expected_score in test_cases:
        score = evaluate_oikiri(text)
        status = "✅" if score == expected_score else "❌"
        logger.info(f"{status} '{text}' → スコア: {score} (期待値: {expected_score})")


def test_training_evaluation():
    """調教評価システム全体をテスト"""
    
    # テスト用調教データ（test_training_offline.pyで生成したJSONを使用）
    json_file = "training_data_20251124_tokyo11R.json"
    
    logger.info(f"\n=== 調教評価システムテスト: {json_file} ===")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        # 評価実行
        evaluation_results = evaluate_all_horses_training(
            training_data,
            race_date='2025-11-24'
        )
        
        # 結果を表示
        logger.info(f"\n評価結果: {len(evaluation_results)}頭")
        
        for horse_num, data in evaluation_results.items():
            eval_info = data['evaluation']
            training = data['last_training']
            
            logger.info(f"\n🐴 {horse_num}番")
            logger.info(f"  ランク: {eval_info['rank']}")
            logger.info(f"  スコア: {eval_info['score']}/5.0")
            logger.info(f"  調教: {training.get('date_location', '')} {training.get('追い切り方', '')}")
            logger.info(f"  タイム順位: {eval_info.get('time_rank', '-')}位")
            logger.info(f"  備考: {eval_info.get('note', '')}")
        
        # テキスト形式で出力
        logger.info("\n" + "=" * 60)
        text_output = format_training_evaluation(evaluation_results)
        logger.info("\n" + text_output)
        
        # ファイルに保存
        output_file = "training_evaluation_test.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_output)
        logger.info(f"\n✅ 評価結果を保存: {output_file}")
        
    except FileNotFoundError:
        logger.error(f"❌ ファイルが見つかりません: {json_file}")
        logger.info("先に test_training_offline.py を実行してください")
    except Exception as e:
        logger.error(f"❌ エラー: {e}", exc_info=True)


if __name__ == "__main__":
    # 追い切り評価テスト
    test_oikiri_evaluation()
    
    # 調教評価システムテスト
    test_training_evaluation()
