import asyncio
from playwright.async_api import async_playwright
import datetime
from bs4 import BeautifulSoup
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeibaGovScheduleFetcher:
    """Fetch schedule from keiba.go.jp monthly convene info as fallback."""
    BASE_URL = "https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"

    @staticmethod
    async def fetch_schedule_for_date(target_date: datetime.date):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context()
            page = await ctx.new_page()
            try:
                url = KeibaGovScheduleFetcher.BASE_URL
                logger.info(f"Keiba.gov schedule: {url} for {target_date}")
                await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # The site contains a table with monthly convene info; search for target date
                venues = []
                # Find elements that include date and venue pairs
                for td in soup.select('td'):
                    if str(target_date.day) in td.get_text():
                        # look for a venue name in nearby siblings
                        possible = td.find_next_siblings()
                        for s in possible:
                            text = s.get_text(strip=True)
                            if text and len(text) < 12:
                                if text not in venues:
                                    venues.append(text)
                                break

                logger.info(f"Keiba.gov venues: {venues}")
                return [{'venue': v} for v in venues]
            except Exception as e:
                logger.error(f"Keiba.gov schedule fetch error: {e}")
                return []
            finally:
                await browser.close()
