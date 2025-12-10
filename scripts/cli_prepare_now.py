#!/usr/bin/env python3
import asyncio
import datetime
import json
from pathlib import Path

from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
from src.scrapers.jra_odds import JRAOddsFetcher
from src.utils.db_manager import CSVDBManager
from src.utils.recommender import HorseRecommender
from src.utils.horse_ranker import HorseRanker
from src.utils.schedule_utils import get_next_race_number
from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher
from src.scrapers.keiba_today import KeibaTodayFetcher
from src.scrapers.jra_schedule import JRAScheduleFetcher
from src.utils.output import save_per_race_json, save_race_summary_json
from src.utils.venue_manager import VenueManager


async def fetch_schedule_for_today(settings):
    today = datetime.date.today()
    # try today source first
    schedule = await KeibaTodayFetcher.fetch_today_schedule(today)
    if not schedule:
        schedule = await NetkeibaCalendarFetcher.fetch_schedule_for_date(today)
    if not schedule:
        schedule = await JRAScheduleFetcher.fetch_schedule_for_date(today)
    return schedule


def build_race_id(date_str, venue_name, race_num):
    code = VenueManager.get_venue_code(venue_name) or '00'
    return f"{date_str}{code}{int(race_num):02d}"


async def main(target_venue: str = None, fast: bool = False, headful: bool = False, race_num: int = None, rate_limit: float = None, full: bool = False, no_summary: bool = False, perf: bool = False):
    settings = load_settings()
    print('Loaded settings')
    schedule = await fetch_schedule_for_today(settings)
    print('target_venue:', target_venue)
    print('Schedule:', schedule)

    # pick first active venue if any; if target_venue provided, try to match it
    if not schedule:
        print('No schedule found for today')
        return
    venue = None
    if target_venue:
        for s in schedule:
            print('Checking schedule venue:', s.get('venue'))
            if target_venue in s.get('venue') or s.get('venue').startswith(target_venue):
                venue = s.get('venue')
                races = s.get('races', [])
                break
    if not venue:
        # default to first active venue
        venue = schedule[0]['venue']
        races = schedule[0].get('races', [])
    now = datetime.datetime.now()
    # If race_num provided, use it; otherwise use next race heuristic
    if race_num:
        print('Provided race_num argument:', race_num)
        next_r = race_num
    else:
        next_r = get_next_race_number(schedule, venue, now, buffer_minutes=settings.get('next_race_buffer_minutes', 1))
    if not next_r:
        # fallback to 1R
        next_r = 1

    date_str = datetime.date.today().strftime('%Y%m%d')
    race_id = build_race_id(date_str, venue, next_r)
    race_key = f"{date_str}_{VenueManager.get_venue_code(venue) or 'unknown'}{next_r}R"
    print(f"Preparing next race: {venue} {next_r}R -> {race_id}")

    out_dir = Path(settings.get('output_dir', 'data'))
    out_dir.mkdir(parents=True, exist_ok=True)
    dbm = CSVDBManager()
    # Apply fast mode settings: reduce wait times and skip optional heavy fetches
    if rate_limit is not None:
        settings['rate_limit_base'] = float(rate_limit)
    settings['perf'] = bool(perf)

    if full:
        # Full means do not skip any content
        settings['skip_training'] = False
        settings['skip_pedigree'] = False
        settings['skip_past_results'] = False
        settings['skip_stable_comment'] = False
        settings['skip_previous_race_comment'] = False
    if fast:
        settings['rate_limit_base'] = 0.5
        settings['skip_pedigree'] = True
        settings['skip_past_results'] = True
        settings['skip_stable_comment'] = False  # keep comments
        settings['skip_training'] = False  # keep training
        # keep playwright headless by default in fast mode
        settings['playwright_headless'] = True
        # shorten Playwright timeout in fast mode
        settings['playwright_timeout'] = 15000
        settings['skip_debug_files'] = True

    scraper = KeibaBookScraper({**settings, 'race_id': race_id, 'race_key': race_key, 'shutuba_url': f'https://s.keibabook.co.jp/cyuou/syutuba/{race_id}', 'output_dir': str(out_dir)}, db_manager=dbm)

    print('Scraping... (reusing browser if possible)')
    # Launch a Playwright browser once and reuse the page for speed
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headful)
        context = await browser.new_context()
        page = await context.new_page()
        scraped = await scraper.scrape(context=context, page=page)
    if not scraped:
        print('No data scraped')
        return
    print('Scraped horses:', len(scraped.get('horses', [])))

    # odds for JRA
    if settings.get('race_type', 'jra') == 'jra':
        print('Fetching JRA odds...')
        odds = await JRAOddsFetcher.fetch_realtime_odds(venue, next_r)
        if odds:
            for h in scraped.get('horses', []):
                hn = h.get('horse_num')
                if hn in odds:
                    h['current_odds'] = odds[hn]

    per_file = save_per_race_json(out_dir, race_id, race_key, scraped)
    print('Saved:', per_file)
    if not no_summary:
        summary_file = save_race_summary_json(out_dir, race_id, race_key, scraped)
        print('Saved summary:', summary_file)

    # quick analysis
    recommender = HorseRecommender(dbm)
    ranker = HorseRanker()
    ranked = ranker.rank_horses(scraped)
    print('Top ranked horses:')
    for r in ranked[:5]:
        print(f"{r.get('predicted_rank')} - {r.get('horse_name')} {r.get('horse_num')} (score: {r.get('rank_score')})")

    print('Done')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Prepare Now CLI')
    parser.add_argument('--venue', default=None, help='Venue name to target (e.g., 浦和)')
    parser.add_argument('--fast', action='store_true', help='Fast mode: limited fetching, reuse browser and reduce waits')
    parser.add_argument('--headful', action='store_true', help='Launch browser UI for debugging')
    parser.add_argument('--race', type=int, default=None, help='Specific race number to target (e.g., 9)')
    parser.add_argument('--rate', type=float, default=None, help='Rate limit base seconds (e.g., 1.5)')
    parser.add_argument('--full', action='store_true', help='Full fetch mode: retrieve all fields (training, comments, pedigree, points)')
    parser.add_argument('--no-summary', action='store_true', help='Do not write summary JSON')
    parser.add_argument('--perf', action='store_true', help='Enable per-step perf logs')
    args = parser.parse_args()
    print('Parsed args:', args)
    asyncio.run(main(target_venue=args.venue, fast=args.fast, headful=args.headful, race_num=args.race, rate_limit=args.rate, full=args.full, no_summary=args.no_summary, perf=args.perf))
