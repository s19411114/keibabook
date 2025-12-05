#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RaceScraperクラス - KeibaBookからレースデータを取得する統一インターフェース

設計方針:
1. シンプルな公開API: scrape_race() メソッド1つで全データ取得
2. 内部実装の隠蔽: _parse_* メソッドで責務を分離
3. エラー処理の一元化: 各処理段階でのエラーをログに記録
4. Cookie認証の自動化: cookies.json を自動で読み込み

使用例:
    scraper = RaceScraper()
    data = await scraper.scrape_race("202505040611")
    await scraper.close()
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RaceScraper:
    """KeibaBookからレースデータを取得するスクレイパー"""
    
    BASE_URL = "https://s.keibabook.co.jp/cyuou/cyokyo/0"  # 正しいKeibaBook URL
    
    def __init__(self, cookies_path: str = "cookies.json"):
        """
        初期化
        
        Args:
            cookies_path: Cookie JSONファイルのパス
        """
        self.cookies_path = Path(cookies_path)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def _init_browser(self):
        """ブラウザを初期化"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            
            # Cookie読み込み
            if self.cookies_path.exists():
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.page.context.add_cookies(cookies)
                logger.info(f"Loaded cookies from {self.cookies_path}")
            else:
                logger.warning(f"Cookie file not found: {self.cookies_path}")
    
    async def scrape_race(self, race_id: str) -> Dict[str, Any]:
        """
        レースIDからレースデータを取得
        
        Args:
            race_id: レースID (例: "202505040611")
            
        Returns:
            レースデータの辞書
        """
        await self._init_browser()
        
        # KeibaBookの正しいURL形式
        url = f"https://s.keibabook.co.jp/cyuou/cyokyo/0/{race_id}"
        logger.info(f"Fetching race data: {url}")
        
        try:
            # ページ取得
            response = await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response or not response.ok:
                logger.error(f"Failed to load page: {url} (status: {response.status if response else 'N/A'})")
                return {}
            
            # ログイン確認
            content = await self.page.content()
            if "プレミアム会員" in content or "ログイン" in content:
                logger.info("ログイン確認成功。プレミアムデータを取得します。")
            
            # 最終URLを記録（リダイレクト検出）
            final_url = self.page.url
            if race_id not in final_url:
                logger.warning(f"URL redirected: {url} -> {final_url}")
            
            # データ解析
            race_data = {
                'race_id': race_id,
                'url': url,
                'final_url': final_url,
                'race_name': await self._parse_race_name(content),
                'horses': await self._parse_horses(content),
                'cpu_prediction': await self._parse_cpu_prediction(content),
                'grade': await self._parse_grade(content),
                'distance': await self._parse_distance(content),
            }
            
            logger.info(f"Data retrieved: {race_data.get('race_name', 'Unknown')} ({len(race_data.get('horses', []))} horses)")
            return race_data
            
        except Exception as e:
            logger.error(f"Error scraping race {race_id}: {e}", exc_info=True)
            return {}
    
    async def _parse_race_name(self, html: str) -> str:
        """レース名を抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        race_title = soup.select_one('.racetitle')
        if race_title:
            return race_title.get_text(strip=True)
        return "不明"
    
    async def _parse_horses(self, html: str) -> list:
        """出走馬リストを抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        horses = []
        
        table = soup.select_one('table.syutuba_sp')
        if not table:
            logger.warning("出馬表テーブルが見つかりません")
            return horses
        
        rows = table.select('tr')
        for row in rows:
            umaban = row.select_one('.umaban')
            horse_name = row.select_one('.kbamei a')
            
            if umaban and horse_name:
                horses.append({
                    'number': umaban.get_text(strip=True),
                    'name': horse_name.get_text(strip=True),
                })
        
        return horses
    
    async def _parse_cpu_prediction(self, html: str) -> list:
        """CPU予想を抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        predictions = []
        
        # CPU予想セクションを探索
        cpu_section = soup.select_one('.cpu_prediction, .cpuyoso, [class*="cpu"]')
        if not cpu_section:
            # 別のセレクタを試す
            all_tables = soup.select('table')
            for table in all_tables:
                if 'CPU' in table.get_text():
                    cpu_section = table
                    break
        
        if cpu_section:
            rows = cpu_section.select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    rank = cells[0].get_text(strip=True)
                    horse_name = cells[1].get_text(strip=True)
                    
                    if rank and horse_name:
                        predictions.append({
                            'rank': rank,
                            'horse_name': horse_name,
                        })
        
        logger.info(f"CPU予想取得成功: {len(predictions)}頭")
        return predictions
    
    async def _parse_grade(self, html: str) -> str:
        """レースグレードを抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        grade_elem = soup.select_one('.grade, .race_grade')
        if grade_elem:
            return grade_elem.get_text(strip=True)
        return ""
    
    async def _parse_distance(self, html: str) -> str:
        """距離情報を抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        distance_elem = soup.select_one('.distance, .race_distance')
        if distance_elem:
            return distance_elem.get_text(strip=True)
        return ""
    
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
        if self.playwright:
            await self.playwright.stop()


# CLIテスト用
if __name__ == '__main__':
    async def test():
        scraper = RaceScraper()
        data = await scraper.scrape_race("202505040611")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        await scraper.close()
    
    asyncio.run(test())
