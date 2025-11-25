import asyncio
from playwright.async_api import async_playwright
import datetime
import re
from bs4 import BeautifulSoup
from src.utils.venue_manager import VenueManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class JRAScheduleFetcher:
    """JRA公式サイトから開催スケジュールを取得するクラス"""
    
    BASE_URL = "https://www.jra.go.jp/keiba/calendar/"
    
    @staticmethod
    async def fetch_schedule_for_date(target_date: datetime.date):
        """
        指定された日付の開催スケジュールを取得
        
        Args:
            target_date (datetime.date): 対象日
            
        Returns:
            list: [{ "venue": "東京", "race_num": 12, "time": "..." }, ...]
            開催がない場合は空リスト
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # User-Agentを設定してブロック回避を試みる
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # JRAのカレンダーページ（月別）にアクセス
                # URL: https://www.jra.go.jp/keiba/calendar/{year}/{month}/
                url = f"{JRAScheduleFetcher.BASE_URL}{target_date.year}/{target_date.month}/"
                logger.info(f"JRAスケジュール取得開始: {url} (Target: {target_date})")
                
                # タイムアウトを短く設定 (5秒)
                await page.goto(url, wait_until="domcontentloaded", timeout=5000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                active_venues = []
                
                # td要素をすべて取得
                tds = soup.select("td")
                target_day_str = str(target_date.day)
                
                found_venues = []
                
                for td in tds:
                    # 日付チェック
                    date_div = td.select_one(".date")
                    if date_div and date_div.get_text(strip=True) == target_day_str:
                        # このセルが対象日
                        # 会場名を探す
                        race_divs = td.select(".race a") # リンクになっていることが多い
                        for link in race_divs:
                            venue_name = link.get_text(strip=True)
                            # "東京" や "1回東京3日" のような形式
                            # 会場名だけ抽出
                            for v in ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]:
                                if v in venue_name:
                                    found_venues.append(v)
                        break
                
                # 重複排除
                found_venues = list(set(found_venues))
                
                # 結果形式に変換 (normalize venue names)
                normed = []
                for v in found_venues:
                    norm = VenueManager.normalize_venue_name(v) or v
                    if norm and norm not in normed:
                        normed.append(norm)
                result = [{"venue": v} for v in normed]
                logger.info(f"取得された開催会場: {found_venues}")
                
                return result
                
            except Exception as e:
                logger.error(f"JRAスケジュール取得エラー: {e}")
                return []
            finally:
                await browser.close()

if __name__ == "__main__":
    # テスト実行
    today = datetime.date.today()
    schedule = asyncio.run(JRAScheduleFetcher.fetch_schedule_for_date(today))
    print(f"Schedule for {today}: {schedule}")
