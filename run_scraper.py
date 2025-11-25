import argparse
import asyncio
import os
import json
from pathlib import Path
from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.db_manager import CSVDBManager
from src.utils.output import save_per_race_json

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--race-id', help='Race ID to override config')
    parser.add_argument('--output-dir', help='Output directory to override config')
    args, _ = parser.parse_known_args()

    settings = load_settings()
    if args.race_id:
        settings['race_id'] = args.race_id
    if args.output_dir:
        settings['output_dir'] = args.output_dir
    
    # CSV DBマネージャーを初期化
    db_manager = CSVDBManager(db_dir=os.path.join(settings.get('output_dir', 'data'), 'db'))
    
    # スクレイパーを作成（DBマネージャーを渡す）
    scraper = KeibaBookScraper(settings, db_manager=db_manager)
    
    print("スクレイピング開始...")
    scraped_data = await scraper.scrape()

    if not scraped_data:
        print("データが取得できませんでした（重複チェックでスキップされた可能性があります）")
        return

    # CSV DBに保存
    race_id = settings.get('race_id')
    race_key = settings.get('race_key', race_id)
    db_manager.save_race_data(scraped_data, race_id, race_key)

    # JSONファイルにも保存
    output_dir = Path(settings.get('output_dir', os.path.join(os.getcwd(), 'data')))
    output_dir.mkdir(parents=True, exist_ok=True)
    # legacy file
    output_path = output_dir / f"{race_key}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
    # per-race file
    per_race_path = save_per_race_json(output_dir, race_id, race_key, scraped_data)

    print(f"✅ 保存完了: {output_path}")
    print(f"✅ per-race 保存完了: {per_race_path}")
    
    # AI用JSONもエクスポート
    json_path = db_manager.export_for_ai(race_id, str(output_dir / "json"))
    if json_path:
        print(f"✅ AI用JSONエクスポート: {json_path}")

if __name__ == '__main__':
    asyncio.run(main())
