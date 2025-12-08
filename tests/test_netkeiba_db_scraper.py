"""
Netkeiba DB スクレイパーのテストスクリプト
"""
import sys
from pathlib import Path

# Netkeiba DB scraper は keiba-ai に移行されたため、このテストは main では実行しません。
# テストや移行検証は migration/to_keiba_ai 側のテストで管理してください。
print("SKIP: netkeiba_db_scraper tests moved to migration/to_keiba_ai")
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """テスト実行"""
    # テスト用レースID（2024年6月3日 東京8R 11レース）
    race_id_list = ["202406030811"]
    
    logger.info("=== Netkeiba DB スクレイパー テスト開始 ===")
    logger.info(f"対象レース: {race_id_list}")
    
    try:
        print("SKIP: netkeiba_db_scraper has been moved to migration. No action in main tests.")
        return 0
        
        logger.info("\n=== 取得結果サマリ ===")
        for key, df in results.items():
            logger.info(f"{key}: {len(df)} 行 × {len(df.columns)} 列")
            logger.info(f"  列名: {list(df.columns)[:10]}")  # 最初の10列のみ表示
            if len(df) > 0:
                logger.info(f"  サンプル:\n{df.head(3).to_string()}")
        
        scraper.close()
        logger.info("\n✅ テスト完了")
        
    except Exception as e:
        logger.exception(f"❌ テスト失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
