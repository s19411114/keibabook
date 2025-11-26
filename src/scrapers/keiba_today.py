import asyncio
from playwright.async_api import async_playwright
import datetime
from bs4 import BeautifulSoup
from src.utils.venue_manager import VenueManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeibaTodayFetcher:
    """Fetch today's races and venues from keiba.go.jp TodayRaceInfo page.
    Returns a list of dict items with keys: 'venue', 'races' (list of {race_num, time}).
    """

    BASE_URL = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/TodayRaceInfoTop"

    @staticmethod
    async def fetch_today_schedule(target_date: datetime.date = None):
        if target_date is None:
            target_date = datetime.date.today()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                # The TodayRaceInfoTop uses the current date; we can append date params if needed
                url = KeibaTodayFetcher.BASE_URL
                logger.info(f"Fetching keiba.go.jp today schedule: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                result = []

                # The page contains blocks for different venues with next race info.
                # We'll look for containers that include both a venue name and race list/time.
                # Fallback: Look for '開催' or anchor links that contain venue names.
                possible_venues = soup.select('div.todayConveneArea, div#todayList, div.tomorrow')
                if not possible_venues:
                    # fallback: find anchors with venue names
                    possible_venues = soup.select('a[href*="RaceList"]')

                # Walk through `li` or `div` blocks that likely contain venue section
                containers = soup.select('section.todayInfo, div.todayList') or possible_venues
                if not containers:
                    containers = [soup]

                for c in containers:
                    # Find a venue title
                    title_el = c.find(lambda tag: tag.name in ('h2', 'h3', 'h4') and tag.get_text(strip=True))
                    if title_el:
                        venue = title_el.get_text(strip=True)
                    else:
                        # find first bold/strong text
                        strong = c.find('strong')
                        venue = strong.get_text(strip=True) if strong else ''

                    if not venue:
                        continue

                    # For races: collect items that mention 'R' or race numbers, and times
                    races = []
                    for row in c.select('li, tr, div'):
                        text = row.get_text(separator=' ', strip=True)
                        if 'R' in text and any(ch.isdigit() for ch in text):
                            # extract race num and time
                            # naive parse: find first number followed by 'R'
                            import re
                            m = re.search(r'(\d{1,2})R', text)
                            t = None
                            mtime = re.search(r'(\d{1,2}:\d{2})', text)
                            if m:
                                rnum = int(m.group(1))
                                if mtime:
                                    t = mtime.group(1)
                                races.append({'race_num': rnum, 'time': t})

                    if races:
                        norm = VenueManager.normalize_venue_name(venue) or venue
                        if norm:
                            result.append({'venue': norm, 'races': races})
                        else:
                            result.append({'venue': venue, 'races': races})

                # If no structure matched, try a simplified fallback: find anchors with '開催'
                if not result:
                    anchors = soup.find_all('a', href=True)
                    for a in anchors:
                        text = a.get_text(strip=True)
                        if text and any(k in text for k in ['開催', '場']):
                            # crude: keep unique short labels
                            label = text.split('\n')[0].strip()
                            if label and len(label) < 20:
                                norm = VenueManager.normalize_venue_name(label) or label
                                if not any(r['venue'] == norm for r in result):
                                    result.append({'venue': norm, 'races': []})

                logger.info(f"Keiba Today fetched {len(result)} venues")
                return result
            except Exception as e:
                logger.error(f"Today schedule fetch error: {e}")
                return []
            finally:
                await browser.close()
