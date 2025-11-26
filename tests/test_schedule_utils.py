import datetime
from src.utils.schedule_utils import get_next_race_number


def test_get_next_race_number_with_venue_variants():
    today = datetime.datetime.now()
    schedule = [
        {
            'venue': '浦和競馬場浦和記念',
            'races': [{'race_num': 8, 'time': (today + datetime.timedelta(minutes=20)).strftime('%H:%M')}, {'race_num': 9, 'time': (today + datetime.timedelta(minutes=40)).strftime('%H:%M')}]
        }
    ]
    # Looking for '浦和' should match the normalized venue
    next_race = get_next_race_number(schedule, '浦和', now=today, buffer_minutes=15)
    assert next_race == 8
import datetime
from src.utils.schedule_utils import get_next_race_number


def test_get_next_race_number_simple():
    today = datetime.datetime(2025, 11, 25, 10, 15)
    schedule = [
        {'venue': '東京', 'races': [{'race_num': 1, 'time': '10:00'}, {'race_num': 2, 'time': '10:40'}, {'race_num': 3, 'time': '11:20'}]},
        {'venue': '京都', 'races': [{'race_num': 1, 'time': '09:50'}]}
    ]

    # When now=10:15 with default buffer=10m, 10:00 >= 10:05? No, so next is 2 at 10:40
    r = get_next_race_number(schedule, '東京', now=today)
    assert r == 2

def test_get_next_race_number_buffer_included():
    today = datetime.datetime(2025, 11, 25, 9, 55)
    schedule = [
        {'venue': '東京', 'races': [{'race_num': 1, 'time': '10:00'}, {'race_num': 2, 'time': '10:40'}]}
    ]
    # With buffer 10 minutes, onset at now=9:55 should include 1R at 10:00
    r = get_next_race_number(schedule, '東京', now=today, buffer_minutes=10)
    assert r == 1


def test_get_next_race_number_buffer_one_minute():
    today = datetime.datetime(2025, 11, 25, 10, 15)
    schedule = [
        {'venue': '東京', 'races': [{'race_num': 1, 'time': '10:00'}, {'race_num': 2, 'time': '10:20'}]}
    ]
    # With buffer=1 minute, we expect the next race at 10:20 when now=10:15
    r = get_next_race_number(schedule, '東京', now=today, buffer_minutes=1)
    assert r == 2
