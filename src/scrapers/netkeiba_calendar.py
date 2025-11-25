import asyncio
from playwright.async_api import async_playwright
import datetime
from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NetkeibaCalendarFetcher:
    """Netkeiba のカレンダーページから開催会場を取得するフェッチャ。
    対象日（`target_date`）に開催のある会場を返す。
    返却形式は JRAScheduleFetcher と合わせて `[{ 'venue': '東京', 'races': [] }, ...]` のようにする。
    """

    BASE_URL = "https://race.netkeiba.com/top/calendar.html?rf=sidemenu"

    @staticmethod
    async def fetch_schedule_for_date(target_date: datetime.date):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                logger.info(f"Netkeiba カレンダー取得開始: {NetkeibaCalendarFetcher.BASE_URL} (Target: {target_date})")
                await page.goto(NetkeibaCalendarFetcher.BASE_URL, wait_until='domcontentloaded', timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # カレンダーのセルから target_date のセルを探す
                # Netkeiba のカレンダーは <td> に日付があり、開催情報は a 要素などで表現されることが多い
                target_day_str = str(target_date.day)
                found_venues = set()
                occurrences = {}

                # 日付セルを検索
                tds = soup.select('td')
                for td in tds:
                    # match day at start of cell text (Netkeiba often lists day as a number)
                    cell_text = td.get_text(strip=True)
                    if cell_text.startswith(target_day_str) or cell_text.startswith(f"{int(target_day_str)}日"):
                        # このセルに含まれるリンクやテキストから会場名を抽出
                        # リンクのテキストや imgのaltなどをチェック
                        links = td.find_all('a')
                        for a in links:
                            text = a.get_text(strip=True)
                            # 長いテキストをカット
                            if not text:
                                # imgのalt -> 例: '東京'
                                img = a.find('img')
                                if img and img.get('alt'):
                                    text = img.get('alt')
                            # 会場名の候補をフィルタリング
                            if text:
                                # Extract race number and time if present. Example: '1R 10:00' or '1R(10:00)'
                                import re
                                # Extract venue names
                                for v in ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]:
                                    if v in text:
                                        # initialize races list if first time
                                        if v not in occurrences:
                                            occurrences[v] = []
                                        found_venues.add(v)
                                        # find all race entries within the anchor's text
                                        # e.g., '1R 10:00' or '1R(10:00)'
                                        r_matches = re.findall(r"(\d{1,2})R", text)
                                        times = re.findall(r"(\d{1,2}:\d{2})", text)
                                        # If both found and lengths match, pair them; else, pair sequentially
                                        if r_matches and times and len(r_matches) == len(times):
                                            for rn, tm in zip(r_matches, times):
                                                occurrences[v].append({'race_num': int(rn), 'time': tm})
                                        elif r_matches and times:
                                            # try pairing closest times
                                            for i, rn in enumerate(r_matches):
                                                tm = times[min(i, len(times)-1)]
                                                occurrences[v].append({'race_num': int(rn), 'time': tm})
                                        elif r_matches:
                                            for rn in r_matches:
                                                occurrences[v].append({'race_num': int(rn), 'time': None})
                                        else:
                                            # If no explicit race number, but venue found, keep empty races
                                            occurrences[v] = occurrences.get(v, [])
                        # ここの td に venue が含まれる場合は処理を終える
                        break

                # Compose result with races if available
                result = []
                for v in sorted(found_venues):
                    result.append({'venue': v, 'races': occurrences.get(v, [])})
                logger.info(f"Netkeiba 取得結果: {result}")
                return result
            except Exception as e:
                logger.error(f"Netkeiba カレンダー取得エラー: {e}")
                return []
            finally:
                await browser.close()


if __name__ == '__main__':
    today = datetime.date.today()
    schedule = asyncio.run(NetkeibaCalendarFetcher.fetch_schedule_for_date(today))
    print(schedule)
