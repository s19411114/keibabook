#!/usr/bin/env python
"""全データ取得テスト + AI用エクスポート"""
import asyncio
import json
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.config import load_settings
from src.utils.exporter import export_for_ai, export_compact

async def main():
    settings = load_settings()
    scraper = KeibaBookScraper(settings)
    race_id = '202544110611'  # 東京11R
    data = await scraper.scrape(race_id)
    
    # AIコピペ用のMarkdown形式でエクスポート
    md_output = export_for_ai(data, format="markdown")
    
    # ファイルに保存
    output_file = f"race_data_{race_id}_for_ai.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_output)
    
    print(f"=== 全データをエクスポート完了: {output_file} ===")
    print(f"ファイルサイズ: {len(md_output):,} 文字")
    print(f"馬数: {len(data.get('horses', []))}頭")
    print("\n--- 出力プレビュー（最初の2000文字）---\n")
    print(md_output[:2000])
    print("\n... (省略)")

if __name__ == "__main__":
    asyncio.run(main())
