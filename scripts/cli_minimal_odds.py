#!/usr/bin/env python3
"""
Minimal odds fetch script
- Target tracks only (e.g. 浦和), limited races
- Fetches odds at two times: 10 and 4 minutes before race start
- Saves snapshots to `data/odds/<race_id>/<timestamp>.json` and logs simple percentage change
"""
import argparse
import asyncio
import datetime
import json
from pathlib import Path
from typing import List, Dict

from src.utils.config import load_settings
from src.scrapers.keiba_today import KeibaTodayFetcher
from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher
from src.utils.venue_manager import VenueManager
from src.scrapers.jra_odds import JRAOddsFetcher
from src.scrapers.odds_fetcher import OddsFetcher
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_race_id(date_str: str, venue_name: str, race_num: int) -> str:
    code = VenueManager.get_venue_code(venue_name) or '00'
    return f"{date_str}{code}{int(race_num):02d}"


def _now():
    return datetime.datetime.now()


async def fetch_schedule_for_today():
    today = datetime.date.today()
    # try today source first
    schedule = await KeibaTodayFetcher.fetch_today_schedule(today)
    if not schedule:
        schedule = await NetkeibaCalendarFetcher.fetch_schedule_for_date(today)
    return schedule


def parse_time_to_datetime(time_str: str) -> datetime.datetime:
    now = _now()
    if not time_str:
        return None
    hh, mm = map(int, time_str.split(':'))
    return datetime.datetime(now.year, now.month, now.day, hh, mm)


def save_snapshot(out_dir: Path, race_id: str, data: Dict):
    od_dir = out_dir / 'odds' / race_id
    od_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    fpath = od_dir / f"{ts}.json"
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fpath


def compare_snapshots(prev: Dict, current: Dict) -> Dict:
    # Simple percent change per horse_num for win odds only (if present)
    changes = {}
    prev_h = {str(h.get('horse_num')): float(h.get('win_odds')) if h.get('win_odds') else None for h in prev.get('horses', [])}
    cur_h = {str(h.get('horse_num')): float(h.get('win_odds')) if h.get('win_odds') else None for h in current.get('horses', [])}
    for k, v in cur_h.items():
        if k in prev_h and prev_h[k] and v:
            try:
                pct = (v - prev_h[k]) / prev_h[k] * 100.0
                changes[k] = round(pct, 2)
            except Exception:
                changes[k] = None
    return changes


async def do_fetch(browser, page, race_id: str, race_type: str, settings: Dict):
    # Choose odds fetcher
    if race_type == 'nar':
        fetcher = OddsFetcher({**settings, 'race_id': race_id, 'race_type': 'nar'})
        data = await fetcher.fetch_odds(page)
    else:
        # parse venue/race_id to get venue and number: last 2 digits are race num
        # JRAOddsFetcher.fetch_realtime_odds expects venue_name and race_num
        # Minimal approach: we'll return dummy if JRAOddsFetcher is not implemented
        data = await JRAOddsFetcher.fetch_realtime_odds('JRA', int(race_id[-2:]))
    return data


async def main(tracks: List[str], offsets: List[int], headful: bool = False, dry_run: bool = False):
    settings = load_settings()
    out_dir = Path(settings.get('output_dir', 'data'))
    schedule = await fetch_schedule_for_today()
    if not schedule:
        logger.warning('No schedule found for today')
        return

    # Filter schedule for given tracks
    selected = []
    for s in schedule:
        for t in tracks:
            if t in s.get('venue') or s.get('venue').startswith(t):
                selected.append(s)
                break

    if not selected:
        logger.warning(f'No venues match {tracks}')
        return

    # Build a list of (race_id, time, race_type)
    tasks = []
    date_str = datetime.date.today().strftime('%Y%m%d')
    for v in selected:
        venue = v.get('venue')
        races = v.get('races', [])
        # treat all races found in schedule
        for r in races:
            race_num = r.get('race_num')
            t = r.get('time')
            if not race_num or not t:
                continue
            race_dt = parse_time_to_datetime(t)
            race_id = build_race_id(date_str, venue, race_num)
            # For now: treat JRA vs NAR by venue manager
            race_type = 'nar' if VenueManager.is_minami_kanto(venue) else 'jra'
            # For each offset, compute scheduled time and append
            for off in offsets:
                sched_at = race_dt - datetime.timedelta(minutes=off)
                if sched_at > _now():
                    tasks.append({'race_id': race_id, 'venue': venue, 'race_num': race_num, 'sched_at': sched_at, 'race_type': race_type, 'offset': off})

    if not tasks:
        logger.info('No upcoming tasks scheduled for provided offsets')
        return

    # Sort tasks by time
    tasks = sorted(tasks, key=lambda x: x['sched_at'])
    logger.info(f"Scheduled {len(tasks)} tasks: {tasks}")

    if dry_run:
        logger.info('Dry run: not executing tasks')
        return

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headful)
        context = await browser.new_context()
        page = await context.new_page()
        prev_snapshot_map = {}
        for task in tasks:
            now = _now()
            wait_seconds = (task['sched_at'] - now).total_seconds()
            if wait_seconds > 0:
                logger.info(f"Waiting {round(wait_seconds)}s until {task['venue']} {task['race_num']}R (-{task['offset']}m)")
                await asyncio.sleep(wait_seconds)
            logger.info(f"Fetching odds for {task['race_id']} ({task['venue']} {task['race_num']}R) at -{task['offset']}m")
            data = await do_fetch(browser, page, task['race_id'], task['race_type'], settings)
            if not data:
                logger.warning('No odds data returned')
                continue
            path = save_snapshot(out_dir, task['race_id'], data)
            logger.info(f"Saved snapshot: {path}")
            # compute diff
            prev = prev_snapshot_map.get(task['race_id'])
            if not prev:
                # find last snapshot on disk to compare
                od_dir = out_dir / 'odds' / task['race_id']
                if od_dir.exists():
                    files = sorted(od_dir.glob('*.json'))
                    if files:
                        with open(files[-1], 'r', encoding='utf-8') as f:
                            prev = json.load(f)
            if prev:
                changes = compare_snapshots(prev, data)
                if changes:
                    logger.info(f"Odds changes: {changes}")
            prev_snapshot_map[task['race_id']] = data

        await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Minimal odds fetcher (10 and 4 min updates)')
    parser.add_argument('--tracks', default='浦和', help='Comma-separated venue names to monitor (default: 浦和)')
    parser.add_argument('--offsets', default='10,4', help='Comma-separated minute offsets before race to fetch (default: 10,4)')
    parser.add_argument('--headful', action='store_true', help='Launch browser headful instead of headless')
    parser.add_argument('--dry-run', action='store_true', help='Do not perform HTTP requests; just show schedule')
    args = parser.parse_args()
    tracks = [t.strip() for t in args.tracks.split(',') if t.strip()]
    offsets = [int(x.strip()) for x in args.offsets.split(',') if x.strip()]
    asyncio.run(main(tracks, offsets, headful=args.headful, dry_run=args.dry_run))
