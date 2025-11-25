import asyncio
from playwright.async_api import async_playwright
import datetime
from bs4 import BeautifulSoup
from src.utils.venue_manager import VenueManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NARScheduleFetcher:
    """NAR (地方競馬) の開催スケジュールを netkeiba から取得するクラス"""
    BASE_URL = "https://nar.netkeiba.com/top/"

    @staticmethod
    async def fetch_schedule_for_date(target_date: datetime.date):
        date_str = target_date.strftime('%Y%m%d')
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                # Access netkeiba NAR top page with date param
                url = f"{NARScheduleFetcher.BASE_URL}?kaisai_date={date_str}"
                logger.info(f"NAR schedule fetch for {target_date} -> {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # On the page, look for kaisai (開催) list; find anchors with kaisai_id
                venues = []
                for a in soup.select('div#kaisai_list a'):
                    text = a.get_text(strip=True)
                    # The anchor text usually contains the venue name
                    if text and text not in venues:
                        venues.append(text)

                # Fallback: look for links with kaisai_id in href
                if not venues:
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if 'kaisai_id=' in href:
                            text = a.get_text(strip=True)
                            if text and text not in venues:
                                venues.append(text)

                # Normalize venue labels (strip whitespace) and canonicalize
                venues = [v.strip() for v in venues if v.strip()]
                normed = []
                for v in venues:
                    norm = VenueManager.normalize_venue_name(v) or v
                    if norm and norm not in normed:
                        normed.append(norm)
                logger.info(f"NAR venues: {normed}")
                return [{'venue': v} for v in normed]
            except Exception as e:
                logger.error(f"NAR schedule fetch error: {e}")
                return []
            finally:
                await browser.close()
