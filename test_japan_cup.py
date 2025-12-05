#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ジャパンカップ データ取得テスト"""

import sys
import asyncio
import yaml
from pathlib import Path
sys.path.insert(0, 'src')

from scrapers.keibabook import KeibaBookScraper

async def test_japan_cup():
    # 設定ファイル読み込み
    config_path = Path('config/settings.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)
    
    # 2024年ジャパンカップ: 11月24日 東京11R
    race_id = '2024112411'
    
    # URLを設定
    shutuba_url = f'https://www.keibabook.co.jp/sp/shutuba.aspx?RaceID={race_id}'
    
    scraper = KeibaBookScraper(settings)
    scraper.shutuba_url = shutuba_url
    
    print(f'🐎 取得開始: {race_id} (2024年ジャパンカップ)')
    print(f'URL: {shutuba_url}')
    print('-' * 50)
    
    try:
        data = await scraper.scrape()
        
        if data:
            print('✅ データ取得成功')
            print(f'レース名: {data.get("race_name", "不明")}')
            print(f'馬数: {len(data.get("horses", []))}')
            
            # 馬名リスト
            if data.get('horses'):
                print('\n出走馬:')
                for i, horse in enumerate(data['horses'][:5], 1):
                    print(f"  {i}. {horse.get('horse_name', '不明')}")
                if len(data['horses']) > 5:
                    print(f"  ... 他 {len(data['horses']) - 5} 頭")
                    
            # JSON保存
            import json
            output_path = Path('data') / 'json' / f'{race_id}.json'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f'\n💾 保存: {output_path}')
        else:
            print('❌ データ取得失敗')
    
    except Exception as e:
        import traceback
        print(f'❌ エラー: {e}')
        traceback.print_exc()
    
    finally:
        # ブラウザクローズ
        if hasattr(scraper, '_playwright') and scraper._playwright:
            await scraper._playwright.__aexit__(None, None, None)

if __name__ == '__main__':
    asyncio.run(test_japan_cup())
