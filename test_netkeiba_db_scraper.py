"""
Netkeiba DB スクレイパーのテストスクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.scrapers.netkeiba_db_scraper import NetkeibaDBScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """テスト実行"""
    # テスト用レースID（2024年6月3日 東京8R 11レース）
    race_id_list = ["202406030811"]
    
    logger.info("=== Netkeiba DB スクレイパー テスト開始 ===")
    logger.info(f"対象レース: {race_id_list}")
    
    try:
        scraper = NetkeibaDBScraper(output_dir="data/netkeiba_archive")
        results = scraper.scrape_all(race_id_list)
        
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
