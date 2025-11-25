#!/usr/bin/env python3
import asyncio
import json
import datetime
from src.scrapers.keiba_today import KeibaTodayFetcher
from src.scrapers.netkeiba_calendar import NetkeibaCalendarFetcher


async def main():
    today = datetime.date.today()
    s = await KeibaTodayFetcher.fetch_today_schedule(today)
    print('Keiba Today:')
    print(json.dumps(s, ensure_ascii=False, indent=2))
    s2 = await NetkeibaCalendarFetcher.fetch_schedule_for_date(today)
    print('Netkeiba:')
    print(json.dumps(s2, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
