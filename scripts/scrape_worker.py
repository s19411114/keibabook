"""
================================================================================
スクレイピングワーカー（サブプロセス用）
================================================================================

Playwrightを別プロセスで実行し、Streamlitとの競合を回避します。
JSONファイルでデータをやり取りします。

使用方法:
    python scripts/scrape_worker.py --race_id=2025113005011 --race_type=jra --output=data/result.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.keibabook import KeibaBookScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def run_scraping(race_id: str, race_type: str, output_path: str):
    """
    スクレイピングを実行してJSONに保存
    """
    # URLを構築
    if race_type == 'nar':
        base = "https://s.keibabook.co.jp/chihou"
    else:
        base = "https://s.keibabook.co.jp/cyuou"
    
    shutuba_url = f"{base}/syutuba/{race_id}"
    
    # 設定
    settings = {
        'race_type': race_type,
        'race_id': race_id,
        'race_key': f"{race_id[:8]}_{race_id[8:]}R",
        'shutuba_url': shutuba_url,
        'playwright_headless': True,
        'playwright_timeout': 90000,  # 90秒タイムアウト
        'cookie_file': 'cookies.json',
        'skip_debug_files': True,
    }
    
    logger.info(f"スクレイピング開始: {shutuba_url}")
    
    try:
        scraper = KeibaBookScraper(settings)
        data = await scraper.scrape()
        
        # 結果を保存
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        horse_count = len(data.get('horses', []))
        logger.info(f"スクレイピング完了: {horse_count}頭 -> {output_path}")
        
        # 成功を示す
        return {
            'success': True,
            'horse_count': horse_count,
            'output_path': str(output_file)
        }
        
    except Exception as e:
        logger.error(f"スクレイピングエラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='競馬ブックスクレイピングワーカー')
    parser.add_argument('--race_id', required=True, help='レースID (例: 2025113005011)')
    parser.add_argument('--race_type', default='jra', choices=['jra', 'nar'], help='競馬種別')
    parser.add_argument('--output', required=True, help='出力ファイルパス')
    
    args = parser.parse_args()
    
    # Windows環境でのイベントループポリシー設定
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    result = asyncio.run(run_scraping(args.race_id, args.race_type, args.output))
    
    # 結果をstdoutに出力（JSON形式）
    print(json.dumps(result, ensure_ascii=False))
    
    # 成功/失敗に応じた終了コード
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
