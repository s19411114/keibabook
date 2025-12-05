#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KeibaBook日程ページからスケジュールを取得する新しいフェッチャー
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, date
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeibaBookScheduleFetcher:
    """KeibaBook日程ページから本日のスケジュールを取得"""
    
    BASE_URL = "https://s.keibabook.co.jp/cyuou/nittei/top"
    
    @staticmethod
    async def fetch_schedule_for_date(target_date: date) -> List[Dict[str, Any]]:
        """
        指定日のスケジュールを取得
        
        Args:
            target_date: 対象日付
            
        Returns:
            スケジュールリスト [{'venue': '東京', 'races': [{race_num: 11, ...}]}, ...]
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                logger.info(f"KeibaBook日程取得: {KeibaBookScheduleFetcher.BASE_URL} (Target: {target_date})")
                
                await page.goto(KeibaBookScheduleFetcher.BASE_URL, wait_until='domcontentloaded', timeout=15000)
                content = await page.content()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # 対象日付のセクションを探す (例: "11/30")
                target_date_str = f"{target_date.month}/{target_date.day}"
                
                venues_data = {}
                
                # 日付ごとのdlブロックを検索
                date_sections = soup.find_all('dt', class_='tukihi')
                
                for dt in date_sections:
                    date_text = dt.get_text(strip=True)
                    
                    # 対象日付か確認
                    if date_text == target_date_str:
                        # 次のddタグ内のレース情報を取得
                        dd = dt.find_next_sibling('dd')
                        
                        if dd:
                            # 会場ごとのliを検索
                            venue_items = dd.find_all('li', class_='negahikeibajyo')
                            
                            for li in venue_items:
                                # 会場名を取得
                                venue_elem = li.select_one('p.keibajyo')
                                if not venue_elem:
                                    # テキストから直接会場名を取得する場合
                                    venue_text = li.get_text(strip=True)
                                    venue_name = None
                                    for v in ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]:
                                        if v in venue_text:
                                            venue_name = v
                                            break
                                else:
                                    venue_name = venue_elem.get_text(strip=True)
                                
                                if not venue_name:
                                    continue
                                
                                # レースIDを取得
                                link = li.find('a')
                                if link and link.get('href'):
                                    href = link.get('href')
                                    # 例: /cyuou/nittei/2025113004 から 2025113004 を抽出
                                    race_id = href.split('/')[-1]
                                    
                                    # race_idから会場コードとレース番号を抽出
                                    # フォーマット: YYYYMMDDVVRR または YYYYMMDDVV
                                    if len(race_id) >= 10:
                                        # YYYYMMDDVV の場合は重賞レースのメインレース
                                        # YYYYMMDDVVRR の場合は通常レース
                                        if len(race_id) == 10:
                                            # 重賞レースは通常11Rか12R
                                            race_num = 11  # デフォルト
                                        elif len(race_id) == 12:
                                            race_num_str = race_id[10:12]
                                            race_num = int(race_num_str)
                                        else:
                                            race_num = 0
                                        
                                        # レース名を取得
                                        race_name_elem = li.select_one('p.jusyo')
                                        race_name = race_name_elem.get_text(strip=True) if race_name_elem else ''
                                        
                                        # 会場データに追加
                                        if venue_name not in venues_data:
                                            venues_data[venue_name] = []
                                        
                                        venues_data[venue_name].append({
                                            'race_num': race_num,
                                            'race_name': race_name,
                                            'race_id': race_id,
                                            'time': ''  # KeibaBook日程ページには時刻情報なし
                                        })
                        
                        break  # 対象日付を見つけたらループ終了
                
                # 結果を整形
                result = []
                for venue, races in sorted(venues_data.items()):
                    result.append({
                        'venue': venue,
                        'races': sorted(races, key=lambda r: r['race_num'])
                    })
                
                logger.info(f"KeibaBook日程取得結果: {len(result)}会場")
                for v_data in result:
                    logger.info(f"  {v_data['venue']}: {len(v_data['races'])}レース")
                
                return result
                
            except Exception as e:
                logger.error(f"KeibaBook日程取得エラー: {e}", exc_info=True)
                return []
                
            finally:
                await browser.close()


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    async def test():
        today = datetime.now().date()
        schedule = await KeibaBookScheduleFetcher.fetch_schedule_for_date(today)
        
        print(f"\n本日のスケジュール ({today}):")
        print("=" * 60)
        
        for venue_data in schedule:
            venue = venue_data['venue']
            races = venue_data['races']
            print(f"\n{venue} ({len(races)}レース):")
            for race in races:
                print(f"  {race['race_num']}R: {race['race_name']} (ID: {race['race_id']})")
    
    asyncio.run(test())
