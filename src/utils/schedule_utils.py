import datetime
from typing import List, Dict, Optional
from src.utils.venue_manager import VenueManager


def get_next_race_number(schedule: List[Dict], venue_name: str, now: datetime.datetime = None, buffer_minutes: int = 10) -> Optional[int]:
    """Given a schedule list of {venue, races: [{race_num, time}]}, find the next race number for given venue_name.
    - schedule: list of venues with races
    - venue_name: name to match
    - now: current datetime; if None, use datetime.datetime.now()
    - buffer_minutes: treat any race starting within buffer as 'upcoming' — select it

    Returns: next race number or None if not found
    """
    if now is None:
        now = datetime.datetime.now()

    # find venue; attempt to normalize source-provided venue labels
    normalized_target = VenueManager.normalize_venue_name(venue_name) or venue_name
    for v in schedule:
        sched_name = v.get('venue')
        normalized_sched = VenueManager.normalize_venue_name(sched_name) or sched_name
        # Allow for flexible matching: exact match or substring match
        if normalized_sched == normalized_target or (normalized_sched and normalized_target and (normalized_sched in normalized_target or normalized_target in normalized_sched)):
            races = v.get('races', [])
            # parse time string HH:MM into today datetime; compare
            for r in sorted(races, key=lambda x: x.get('race_num', 0)):
                t = r.get('time')
                if not t:
                    continue
                try:
                    hh, mm = map(int, t.split(':'))
                    # Construct candidate datetime for race; handle potential next-day races
                    race_dt = datetime.datetime(now.year, now.month, now.day, hh, mm)
                    # If race time appears to be for the next day (e.g., now 23:50 and race at 00:10),
                    # treat times more than 12 hours in the past as next-day races.
                    if race_dt < (now - datetime.timedelta(hours=12)):
                        race_dt = race_dt + datetime.timedelta(days=1)
                    # If race time is after now - buffer, it's a candidate
                    if race_dt >= (now - datetime.timedelta(minutes=buffer_minutes)):
                        return r.get('race_num')
                except Exception:
                    continue
            # If no times found, fallback None
            return None
    return None
