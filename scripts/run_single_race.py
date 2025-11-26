#!/usr/bin/env python3
"""
Utility to directly run a single race scrape and save summary — avoids CLI parsing/selection complexity.
"""
import argparse
import asyncio
import datetime
from pathlib import Path

from src.utils.config import load_settings
from src.scrapers.keibabook import KeibaBookScraper
from src.utils.output import save_per_race_json, save_race_summary_json
from src.utils.venue_manager import VenueManager
from src.utils.db_manager import CSVDBManager


def build_race_id(date_str, venue_name, race_num):
    # Normalize venue name and prefer numeric code if available
    norm_name = VenueManager.normalize_venue_name(venue_name) or venue_name
    numeric = VenueManager.get_venue_numeric_code(norm_name)
    if numeric:
        code = numeric
    else:
        code = VenueManager.get_venue_code(norm_name) or '00'
    return f"{date_str}{code}{int(race_num):02d}"


async def main(venue, race_num, rate_limit=1.5, full=False, headful=False, perf=False, skip_dup=False, skip_debug_files=False, race_id=None, shutuba_url=None):
    settings = load_settings()
    if rate_limit:
        settings['rate_limit_base'] = float(rate_limit)
    # perf flags
    settings['perf'] = bool(perf)
    if full:
        settings['skip_training'] = False
        settings['skip_pedigree'] = False
        settings['skip_past_results'] = False
        settings['skip_stable_comment'] = False
        settings['skip_previous_race_comment'] = False
    else:
        settings['skip_pedigree'] = True
        settings['skip_past_results'] = True

    # Allow explicit race_id override (useful for testing specific past/future races)
    date_str = datetime.date.today().strftime('%Y%m%d')
    if race_id is None:
        race_id = build_race_id(date_str, venue, race_num)
    norm = VenueManager.normalize_venue_name(venue) or venue
    race_key = f"{date_str}_{VenueManager.get_venue_code(norm) or 'unknown'}{race_num}R"

    out_dir = Path(settings.get('output_dir', 'data'))
    out_dir.mkdir(parents=True, exist_ok=True)
    dbm = CSVDBManager()

    # Set race_type based on venue (NAR vs JRA)
    race_type = 'nar' if VenueManager.is_minami_kanto(norm) else 'jra'
    base = 'chihou' if race_type == 'nar' else 'cyuou'
    if skip_dup:
        settings['skip_duplicate_check'] = True
    settings['skip_debug_files'] = bool(skip_debug_files)
    # Respect explicit shutuba_url override
    if shutuba_url:
        url = shutuba_url
    else:
        url = f'https://s.keibabook.co.jp/{base}/syutuba/{race_id}'
    scraper = KeibaBookScraper({**settings, 'race_id': race_id, 'race_key': race_key, 'race_type': race_type, 'shutuba_url': url, 'output_dir': str(out_dir)}, db_manager=dbm)

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headful)
        context = await browser.new_context()
        page = await context.new_page()
        scraped = await scraper.scrape(context=context, page=page)

    if not scraped:
        print('No data scraped')
        return

    per_file = save_per_race_json(out_dir, race_id, race_key, scraped)
    summary_file = save_race_summary_json(out_dir, race_id, race_key, scraped)
    print('Saved:', per_file)
    print('Saved summary:', summary_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--venue', required=True)
    parser.add_argument('--race', required=True, type=int)
    parser.add_argument('--rate', default=1.5, type=float)
    parser.add_argument('--race-id', default=None, help='Explicit race_id (YYYYMMDDVVNN) to use')
    parser.add_argument('--shutuba-url', default=None, help='Explicit shutuba URL to use')
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--headful', action='store_true')
    parser.add_argument('--perf', action='store_true', help='Enable per-step perf logs')
    parser.add_argument('--skip-dup', action='store_true', help='Skip duplicate check and always fetch')
    parser.add_argument('--skip-debug-files', action='store_true', help='Skip writing debug HTML and JSON files')
    args = parser.parse_args()
    # enable perf logging if requested
    asyncio.run(main(args.venue, args.race, rate_limit=args.rate, full=args.full, headful=args.headful, perf=args.perf if hasattr(args, 'perf') else False, skip_dup=args.skip_dup, skip_debug_files=args.skip_debug_files, race_id=args.race_id, shutuba_url=args.shutuba_url))
